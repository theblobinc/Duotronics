from __future__ import annotations

import pytest

from duotronic_runtime.autonomy_stack import ACTION_EVENT_TYPES, OBSERVATION_EVENT_TYPES
from duotronic_runtime.delegation_learning import (
    SCHEMA_VERSION,
    WORKER_ID,
    WORKER_SESSION_ID,
    events_for_delegated_run,
    expand_worker_tick_result,
    normalize_delegated_run,
)


def test_normalize_completed_delegated_run_is_deterministic_and_bijective():
    run = {
        "delegation_id": "11111111-1111-1111-1111-111111111111",
        "run_id": "22222222-2222-2222-2222-222222222222",
        "work_id": "33333333-3333-3333-3333-333333333333",
        "project_key": "xavi.app-backend",
        "objective": "Inspect runtime health",
        "tool_name": "runtime.health",
        "status": "completed",
        "result_digest": "sha256:abc",
    }
    first = normalize_delegated_run(run, ordinal=1)
    second = normalize_delegated_run(run, ordinal=1)

    assert first == second
    assert first["schema_version"] == SCHEMA_VERSION
    assert first["worker_id"] == WORKER_ID
    assert first["worker_session_id"] == WORKER_SESSION_ID
    assert first["success"] is True
    assert first["ordinal"]["ordinal"] == 1
    assert first["ordinal"]["bijective"] == "1"
    assert first["experience_digest"].startswith("sha256:")


def test_failed_run_remains_training_evidence_not_success():
    row = normalize_delegated_run(
        {
            "delegation_id": "11111111-1111-1111-1111-111111111111",
            "run_id": "22222222-2222-2222-2222-222222222222",
            "tool_name": "runtime.health",
            "status": "failed",
            "error": "TimeoutError",
        },
        ordinal=10,
    )
    assert row["success"] is False
    assert row["error"] == "TimeoutError"
    assert row["ordinal"]["bijective"] == "A"


def test_event_specs_are_classified_by_autonomy_stack():
    action, observation = events_for_delegated_run(
        {
            "delegation_id": "11111111-1111-1111-1111-111111111111",
            "run_id": "22222222-2222-2222-2222-222222222222",
            "tool_name": "runtime.health",
            "status": "completed",
            "result_digest": "sha256:abc",
        },
        ordinal=11,
    )
    assert action["event_type"] == "delegated_tool_action"
    assert observation["event_type"] == "delegated_tool_result"
    assert action["event_type"] in ACTION_EVENT_TYPES
    assert observation["event_type"] in OBSERVATION_EVENT_TYPES
    assert action["content"]["ordinal"]["bijective"] == "11"


def test_expand_worker_tick_result_normalizes_each_processed_run():
    rows = expand_worker_tick_result(
        {
            "worker_id": "worker:wgrnn-main",
            "processed": [
                {
                    "delegation_id": "11111111-1111-1111-1111-111111111111",
                    "run_id": "22222222-2222-2222-2222-222222222222",
                    "tool_name": "runtime.health",
                    "status": "completed",
                    "result_digest": "sha256:one",
                },
                {
                    "delegation_id": "33333333-3333-3333-3333-333333333333",
                    "run_id": "44444444-4444-4444-4444-444444444444",
                    "tool_name": "coordination.status",
                    "status": "failed",
                    "error": "RuntimeError",
                },
            ],
        },
        starting_ordinal=9,
    )
    assert len(rows) == 2
    assert rows[0]["ordinal"]["bijective"] == "9"
    assert rows[1]["ordinal"]["bijective"] == "A"
    assert rows[0]["success"] is True
    assert rows[1]["success"] is False


def test_invalid_run_is_rejected():
    with pytest.raises(ValueError):
        normalize_delegated_run({"run_id": "r", "tool_name": "runtime.health", "status": "completed"}, ordinal=1)
    with pytest.raises(ValueError):
        normalize_delegated_run({"delegation_id": "d", "run_id": "r", "tool_name": "runtime.health", "status": "made-up"}, ordinal=1)
