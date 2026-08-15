from __future__ import annotations

import asyncio

from duotronic_runtime.wgrnn_worker_loop import WGRNNWorkerLoop


class _Autonomy:
    def __init__(self):
        self.events = []

    def record_event(self, **kwargs):
        self.events.append(kwargs)
        return kwargs


class _Kernel:
    def __init__(self):
        self.autonomy = _Autonomy()


class _Service:
    def __init__(self, kernel, state):
        self.kernel = kernel
        self.state = state

    async def wgrnn_tick(self, args):
        self.state["calls"] += 1
        if self.state.get("raise_once") and self.state["calls"] == 1:
            raise RuntimeError("synthetic tick failure")
        result = self.state.get("result")
        if result is not None:
            return result
        return {"worker_id": "worker:wgrnn-main", "processed": [], "count": 0}


def _factory(state):
    return lambda kernel: _Service(kernel, state)


def test_run_once_preserves_delegation_learning_metadata():
    kernel = _Kernel()
    state = {
        "calls": 0,
        "result": {
            "worker_id": "worker:wgrnn-main",
            "count": 1,
            "processed": [
                {
                    "delegation_id": "delegation-1",
                    "run_id": "run-1",
                    "tool_name": "runtime.health",
                    "status": "completed",
                    "result_digest": "sha256:result",
                    "learning": {
                        "witnessed": True,
                        "trajectory_id": "trajectory-1",
                        "experience_digest": "sha256:experience",
                    },
                }
            ],
        },
    }
    loop = WGRNNWorkerLoop(
        kernel,
        interval_seconds=0.25,
        max_tasks_per_tick=1,
        service_factory=_factory(state),
    )

    result = asyncio.run(loop.run_once())

    assert result["count"] == 1
    assert state["calls"] == 1
    events = [row for row in kernel.autonomy.events if row["event_type"] == "wgrnn_worker_tick"]
    assert len(events) == 1
    processed = events[0]["content"]["processed"][0]
    assert processed["delegation_id"] == "delegation-1"
    assert processed["learning"]["witnessed"] is True
    assert processed["learning"]["trajectory_id"] == "trajectory-1"


def test_background_loop_runs_without_chat_turn_and_stops_cleanly():
    async def scenario():
        kernel = _Kernel()
        state = {"calls": 0}
        loop = WGRNNWorkerLoop(
            kernel,
            interval_seconds=0.25,
            max_tasks_per_tick=2,
            service_factory=_factory(state),
        )
        await loop.start()
        assert loop.running is True
        await asyncio.sleep(0.34)
        await loop.stop()
        assert loop.running is False
        assert state["calls"] >= 1
        kinds = [row["event_type"] for row in kernel.autonomy.events]
        assert "wgrnn_worker_loop_started" in kinds
        assert "wgrnn_worker_loop_stopped" in kinds

    asyncio.run(scenario())


def test_background_loop_records_tick_errors_and_continues():
    async def scenario():
        kernel = _Kernel()
        state = {"calls": 0, "raise_once": True}
        loop = WGRNNWorkerLoop(
            kernel,
            interval_seconds=0.25,
            max_tasks_per_tick=1,
            service_factory=_factory(state),
        )
        await loop.start()
        await asyncio.sleep(0.58)
        await loop.stop()
        assert state["calls"] >= 2
        errors = [row for row in kernel.autonomy.events if row["event_type"] == "wgrnn_worker_loop_error"]
        assert len(errors) == 1
        assert errors[0]["content"]["error"] == "RuntimeError"

    asyncio.run(scenario())
