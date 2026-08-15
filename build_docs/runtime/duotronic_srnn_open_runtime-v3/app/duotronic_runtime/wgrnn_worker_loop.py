from __future__ import annotations

"""Autonomous bounded WG-RNN delegation worker loop.

The loop deliberately lives outside ``session_delegation.py`` so the durable
mailbox/delegation state machine remains independent from runtime lifecycle
management.  It executes only work already admitted by
``SessionDelegationService`` and therefore cannot expand the WG-RNN worker's
MCP tool allowlist.

Each delegated run is witnessed/learned by the delegation service and native
runtime autonomy stack.  Loop lifecycle/error observations are additional
operational evidence, not authority promotion.
"""

import asyncio
import os
from typing import Any, Callable

from .session_delegation import SessionDelegationService


class WGRNNWorkerLoop:
    """Periodically process bounded WG-RNN delegations without a chat turn."""

    def __init__(
        self,
        kernel: Any,
        *,
        interval_seconds: float | None = None,
        max_tasks_per_tick: int | None = None,
        service_factory: Callable[[Any], Any] = SessionDelegationService,
    ) -> None:
        self.kernel = kernel
        self.interval_seconds = max(
            0.25,
            float(
                interval_seconds
                if interval_seconds is not None
                else os.environ.get("WGRNN_WORKER_TICK_SECONDS", "5")
            ),
        )
        self.max_tasks_per_tick = max(
            1,
            min(
                8,
                int(
                    max_tasks_per_tick
                    if max_tasks_per_tick is not None
                    else os.environ.get("WGRNN_WORKER_MAX_TASKS_PER_TICK", "2")
                ),
            ),
        )
        self.service_factory = service_factory
        self._stop = asyncio.Event()
        self._task: asyncio.Task[Any] | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def _record(self, event_type: str, content: dict[str, Any], *, training_eligible: bool = True) -> None:
        autonomy = getattr(self.kernel, "autonomy", None)
        if autonomy is None:
            return
        try:
            autonomy.record_event(
                session_id=SessionDelegationService.WGRNN_SESSION_ID,
                event_type=event_type,
                actor="wgrnn-worker-loop",
                content=content,
                tags=["wgrnn", "delegation-worker", "autonomous-loop"],
                training_eligible=training_eligible,
            )
        except Exception:
            # Observability must never make the worker loop itself unavailable.
            pass

    async def run_once(self) -> dict[str, Any]:
        service = self.service_factory(self.kernel)
        result = await service.wgrnn_tick({"max_tasks": self.max_tasks_per_tick})
        count = int((result or {}).get("count", 0))
        if count:
            self._record(
                "wgrnn_worker_tick",
                {
                    "count": count,
                    "worker_id": (result or {}).get("worker_id"),
                    "processed": [
                        {
                            "delegation_id": row.get("delegation_id"),
                            "run_id": row.get("run_id"),
                            "tool_name": row.get("tool_name"),
                            "status": row.get("status"),
                            "result_digest": row.get("result_digest"),
                            "learning": row.get("learning"),
                        }
                        for row in ((result or {}).get("processed") or [])
                    ],
                },
            )
        return result

    async def run(self) -> None:
        self._record(
            "wgrnn_worker_loop_started",
            {
                "interval_seconds": self.interval_seconds,
                "max_tasks_per_tick": self.max_tasks_per_tick,
            },
            training_eligible=False,
        )
        try:
            while not self._stop.is_set():
                try:
                    await self.run_once()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self._record(
                        "wgrnn_worker_loop_error",
                        {
                            "error": exc.__class__.__name__,
                            "message": str(exc)[:4000],
                        },
                    )

                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self.interval_seconds)
                except asyncio.TimeoutError:
                    pass
        finally:
            self._record(
                "wgrnn_worker_loop_stopped",
                {},
                training_eligible=False,
            )

    async def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._task = asyncio.create_task(self.run(), name="xavi-wgrnn-worker-loop")

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        if task is None:
            return
        if task is asyncio.current_task():
            return
        try:
            await asyncio.wait_for(task, timeout=max(2.0, self.interval_seconds + 1.0))
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        finally:
            self._task = None
