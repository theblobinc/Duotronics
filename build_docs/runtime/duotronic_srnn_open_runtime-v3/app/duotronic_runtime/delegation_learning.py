from __future__ import annotations

"""Witness/training normalization for delegated MCP work.

This module deliberately does not own session messaging, delegation state, worker
registration, or execution. Those remain in session_delegation.py. It provides a
small side-effect-free normalization layer that converts completed/failed worker
runs into the same witnessed experience vocabulary used by AutonomyStack.

That separation lets multiple MCP-connected developers evolve coordination and
learning independently without competing for the same implementation file.
"""

import json
from typing import Any

from .crypto_primitives import shake256_ref
from .duotronic_bijective import positive_ordinal_payload

SCHEMA_VERSION = "delegated-experience/v1"
WORKER_ID = "worker:wgrnn-main"
WORKER_SESSION_ID = "wgrnn:worker:main"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return shake256_ref(value)


def _text(value: Any, maximum: int = 4000) -> str:
    return str(value or "")[:maximum]


def normalize_delegated_run(
    run: dict[str, Any],
    *,
    ordinal: int,
    worker_id: str = WORKER_ID,
    worker_session_id: str = WORKER_SESSION_ID,
) -> dict[str, Any]:
    """Convert one delegated tool-run row/result into deterministic experience.

    Raw credentials are not expected in this record. The caller should pass the
    already-sanitized tool args/result used by the runtime witness path. The
    record binds digests even when the full result is deliberately omitted.
    """

    if not isinstance(run, dict):
        raise TypeError("run must be a dict")
    delegation_id = _text(run.get("delegation_id"), 120)
    run_id = _text(run.get("run_id"), 120)
    tool_name = _text(run.get("tool_name"), 240)
    status = _text(run.get("status"), 40).lower()
    if not delegation_id:
        raise ValueError("delegation_id is required")
    if not run_id:
        raise ValueError("run_id is required")
    if not tool_name:
        raise ValueError("tool_name is required")
    if status not in {"queued", "running", "completed", "failed", "cancelled"}:
        raise ValueError("invalid delegated run status")

    success = status == "completed"
    result = run.get("result")
    result_digest = _text(run.get("result_digest"), 160) or (_digest(result) if result is not None else None)
    error = _text(run.get("error"), 4000) or None
    body = {
        "schema_version": SCHEMA_VERSION,
        "worker_id": worker_id,
        "worker_session_id": worker_session_id,
        "delegation_id": delegation_id,
        "run_id": run_id,
        "work_id": _text(run.get("work_id"), 120) or None,
        "project_key": _text(run.get("project_key"), 160) or None,
        "objective": _text(run.get("objective"), 4000) or None,
        "tool_name": tool_name,
        "tool_args_digest": _text(run.get("tool_args_digest"), 160) or (_digest(run.get("tool_args")) if run.get("tool_args") is not None else None),
        "result_digest": result_digest,
        "status": status,
        "success": success,
        "error": error,
        "ordinal": positive_ordinal_payload(int(ordinal)),
    }
    body["experience_digest"] = _digest(body)
    return body


def events_for_delegated_run(run: dict[str, Any], *, ordinal: int) -> list[dict[str, Any]]:
    """Return normalized action/observation event specifications for AutonomyStack."""

    experience = normalize_delegated_run(run, ordinal=ordinal)
    common_tags = ["delegation", "wgrnn-worker", experience["tool_name"]]
    action = {
        "event_type": "delegated_tool_action",
        "actor": "agent:wgrnn",
        "content": {
            "delegation_id": experience["delegation_id"],
            "run_id": experience["run_id"],
            "work_id": experience["work_id"],
            "worker_id": experience["worker_id"],
            "tool_name": experience["tool_name"],
            "tool_args_digest": experience["tool_args_digest"],
            "experience_digest": experience["experience_digest"],
            "ordinal": experience["ordinal"],
        },
        "tags": common_tags + ["action"],
    }
    observation = {
        "event_type": "delegated_tool_result" if experience["success"] else "delegated_tool_error",
        "actor": "xavi-runtime",
        "content": {
            "delegation_id": experience["delegation_id"],
            "run_id": experience["run_id"],
            "work_id": experience["work_id"],
            "worker_id": experience["worker_id"],
            "tool_name": experience["tool_name"],
            "status": experience["status"],
            "success": experience["success"],
            "result_digest": experience["result_digest"],
            "error": experience["error"],
            "experience_digest": experience["experience_digest"],
            "ordinal": experience["ordinal"],
        },
        "tags": common_tags + (["observation", "success"] if experience["success"] else ["observation", "failure"]),
    }
    return [action, observation]


def expand_worker_tick_result(result: dict[str, Any], *, starting_ordinal: int = 1) -> list[dict[str, Any]]:
    """Normalize every run summarized by worker.wgrnn_tick.

    The tick endpoint returns compact processed rows. This function is useful
    immediately at the MCP boundary; richer DB rows can later be supplied by the
    worker implementation without changing the schema.
    """

    if not isinstance(result, dict):
        return []
    processed = result.get("processed")
    if not isinstance(processed, list):
        return []
    rows: list[dict[str, Any]] = []
    ordinal = max(1, int(starting_ordinal))
    for item in processed:
        if not isinstance(item, dict):
            continue
        try:
            rows.append(normalize_delegated_run(item, ordinal=ordinal))
            ordinal += 1
        except (TypeError, ValueError):
            continue
    return rows
