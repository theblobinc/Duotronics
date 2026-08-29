from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from duotronic_runtime.autonomy_stack import AutonomyStack, sanitize_training_value
from duotronic_runtime.session_delegation import SessionDelegationService, session_delegation_tool_manifest


class _LedgerStub:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append(self, **kwargs):
        sequence = len(self.events) + 1
        event = dict(kwargs)
        event["sequence"] = sequence
        event["event_digest"] = f"shake256-512:event-{sequence}"
        event.setdefault("content", {})
        self.events.append(event)
        return event

    def _read_events(self, session_id: str):
        return [event for event in self.events if event.get("session_id") == session_id]

    def index(self):
        return {"sessions": {}}

    def search(self, **kwargs):
        return {"matches": [], "count": 0}

    def tail(self, **kwargs):
        rows = self._read_events(str(kwargs.get("session_id") or ""))
        return {"events": rows[-int(kwargs.get("limit", 50)):], "count": len(rows)}


class _EvidenceStub:
    def __init__(self) -> None:
        self.witnesses: list[dict] = []

    def witness(self, witness_type, payload, **kwargs):
        row = {
            "witness_id": f"witness-{len(self.witnesses)+1}",
            "witness_type": witness_type,
            "payload_digest": f"shake256-512:witness-{len(self.witnesses)+1}",
            **kwargs,
        }
        self.witnesses.append({"payload": payload, **row})
        return row


class _WGRNNStub:
    def __init__(self) -> None:
        self.steps: list[dict] = []

    def snapshot(self, **kwargs):
        return {"ledger_entries": len(self.steps), "candidate_slots": list(range(len(self.steps)))}


class _StoreStub:
    def begin_source_generation(self, **kwargs):
        return kwargs

    def upsert_source_documents(self, docs):
        rows = list(docs)
        return {"upserted": len(rows), "bytes": sum(len(str(r.get("content", "")).encode()) for r in rows)}

    def finalize_source_generation(self, **kwargs):
        return kwargs


class _KernelStub:
    def __init__(self, tmp_path: Path) -> None:
        self.store = _StoreStub()
        self.session_ledger = _LedgerStub()
        self.evidence = _EvidenceStub()
        self.wgrnn = _WGRNNStub()
        self.settings = SimpleNamespace(runtime_data_dir=str(tmp_path))
        self.wgrnn_steps: list[dict] = []

    def wgrnn_step_witnessed(self, **kwargs):
        self.wgrnn_steps.append(dict(kwargs))
        return {
            "memory_update": {
                "trust_status": "candidate",
                "authority_t": kwargs.get("evidence_quality", 0.72),
                "slot_id": len(self.wgrnn_steps) - 1,
            }
        }


def test_session_delegation_manifest_exposes_addressable_collaboration_and_worker():
    names = {item["name"] for item in session_delegation_tool_manifest()}
    assert {
        "session.list",
        "session.send_message",
        "session.inbox",
        "session.acknowledge",
        "delegation.assign",
        "delegation.inbox",
        "delegation.update",
        "worker.register_wgrnn",
        "worker.wgrnn_tick",
    } <= names


def test_wgrnn_worker_identity_is_stable_and_addressable():
    assert SessionDelegationService.WGRNN_WORKER_ID == "worker:wgrnn-main"
    assert SessionDelegationService.WGRNN_SESSION_ID == "wgrnn:worker:main"


def test_wgrnn_safe_tool_policy_allows_observation_and_blocks_mutating_surfaces():
    safe = SessionDelegationService._safe_wgrnn_tool

    assert safe("runtime.health")
    assert safe("runtime.autonomy_status")
    assert safe("runtime.session_search")
    assert safe("runtime.reference_search")
    assert safe("runtime.transcript_search")
    assert safe("coordination.status")
    assert safe("coordination.search")

    assert not safe("runtime.session_append")
    assert not safe("runtime.transcript_ingest")
    assert not safe("coordination.claim")
    assert not safe("coordination.release")
    assert not safe("coordination.preflight")
    assert not safe("repo.patch")
    assert not safe("ops.exec")


def test_default_worker_tools_are_subset_of_safe_policy():
    unsafe = [name for name in SessionDelegationService.DEFAULT_WGRNN_TOOLS if not SessionDelegationService._safe_wgrnn_tool(name)]
    assert unsafe == []


def _append_delegated_run_events(stack: AutonomyStack, *, session_id: str, success: bool) -> tuple[int, int]:
    start = stack.record_event(
        session_id=session_id,
        event_type="mcp_call_start",
        actor="agent:wgrnn",
        content={
            "delegation_id": "dlg-example" if success else "dlg-fail",
            "work_id": "work-example",
            "worker_id": SessionDelegationService.WGRNN_WORKER_ID,
            "tool_name": "runtime.health",
            "arguments_digest": "shake256-512:args",
        },
        tags=["delegation", "wgrnn-worker", "tool-start"],
    )
    end = stack.record_event(
        session_id=session_id,
        event_type="mcp_call_result" if success else "mcp_call_error",
        actor="agent:wgrnn",
        content={
            "delegation_id": "dlg-example" if success else "dlg-fail",
            "work_id": "work-example",
            "worker_id": SessionDelegationService.WGRNN_WORKER_ID,
            "tool_name": "runtime.health",
            "result_digest": "shake256-512:result" if success else None,
            "error": None if success else "TimeoutError",
        },
        tags=["delegation", "wgrnn-worker", "tool-result" if success else "tool-error"],
    )
    return int(start["sequence"]), int(end["sequence"])


def test_delegated_result_becomes_witnessed_training_trajectory(tmp_path):
    kernel = _KernelStub(tmp_path)
    stack = AutonomyStack(kernel, root=tmp_path / "autonomy")
    session_id = SessionDelegationService.WGRNN_SESSION_ID
    start, end = _append_delegated_run_events(stack, session_id=session_id, success=True)

    result = stack.build_trajectory(
        session_id=session_id,
        start_sequence=start,
        end_sequence=end,
        outcome={"success": True, "score": 1.0, "delegation_status": "completed"},
        evaluator="wgrnn-delegation-integration",
        learn=True,
    )
    trajectory = result["trajectory"]

    assert trajectory["schema_version"] == "experience-trajectory/v1"
    assert trajectory["session_id"] == "wgrnn:worker:main"
    assert trajectory["outcome"]["success"] is True
    assert trajectory["outcome"]["score"] == 1.0
    assert trajectory["start_ordinal"]["ordinal"] >= 1
    assert trajectory["end_ordinal"]["ordinal"] >= trajectory["start_ordinal"]["ordinal"]
    assert trajectory["start_ordinal"]["bijective"]
    assert trajectory["end_ordinal"]["bijective"]
    assert trajectory["actions"]
    assert trajectory["observations"]
    assert trajectory["witness"]["witness_type"] == "ExperienceTrajectoryWitness"
    assert kernel.wgrnn_steps, "trajectory should immediately become WG-RNN candidate experience"
    assert kernel.wgrnn_steps[-1]["requested_action"] == "observe"


def test_failed_delegated_result_is_still_learning_evidence(tmp_path):
    kernel = _KernelStub(tmp_path)
    stack = AutonomyStack(kernel, root=tmp_path / "autonomy")
    session_id = SessionDelegationService.WGRNN_SESSION_ID
    start, end = _append_delegated_run_events(stack, session_id=session_id, success=False)

    result = stack.build_trajectory(
        session_id=session_id,
        start_sequence=start,
        end_sequence=end,
        outcome={"success": False, "score": 0.0, "delegation_status": "failed"},
        evaluator="wgrnn-delegation-integration",
        learn=True,
    )

    assert result["trajectory"]["outcome"]["success"] is False
    assert result["trajectory"]["outcome"]["score"] == 0.0
    assert kernel.wgrnn_steps, "failed executions should also become candidate experience"
    assert kernel.wgrnn_steps[-1]["requested_action"] == "observe"


def test_secret_fields_are_replaced_by_capability_references_for_training():
    sanitized = sanitize_training_value(
        {
            "password": "plaintext-secret",
            "authorization": "Bearer top-secret",
            "api_key": "abc123",
            "credential_ref": "secret://router/admin",
            "normal": "retain me",
        }
    )

    rendered = json.dumps(sanitized, sort_keys=True)
    assert "plaintext-secret" not in rendered
    assert "Bearer top-secret" not in rendered
    assert "abc123" not in rendered
    assert sanitized["normal"] == "retain me"
    assert "secret_ref_only" in rendered
