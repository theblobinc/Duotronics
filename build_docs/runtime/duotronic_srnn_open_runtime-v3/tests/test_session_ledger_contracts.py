from __future__ import annotations

import json

import pytest

from duotronic_runtime.session_ledger import SessionLedger


def test_session_ledger_appends_hash_chained_events(tmp_path):
    ledger = SessionLedger(tmp_path)

    first = ledger.append(
        session_id="runtime-v3-buildout",
        event_type="user_prompt",
        actor="tbi",
        content={"text": "continue the runtime buildout"},
        tags=["runtime-v3", "mcp"],
        created_at_ms=1000,
    )
    second = ledger.append(
        session_id="runtime-v3-buildout",
        event_type="assistant_response",
        actor="chatgpt",
        content={"text": "added a plan"},
        tags=["runtime-v3"],
        created_at_ms=1001,
    )

    assert first["schema_version"] == "session-ledger-event-v1"
    assert first["sequence"] == 1
    assert first["previous_event_digest"] is None
    assert second["sequence"] == 2
    assert second["previous_event_digest"] == first["event_digest"]
    assert second["event_digest"] != first["event_digest"]

    assert ledger.verify(session_id="runtime-v3-buildout")["ok"] is True


def test_session_ledger_tail_and_summary(tmp_path):
    ledger = SessionLedger(tmp_path)
    for i in range(3):
        ledger.append(
            session_id="s1",
            event_type="plan",
            actor="agent",
            content={"i": i},
            tags=["planning"],
            created_at_ms=2000 + i,
        )

    tail = ledger.tail(session_id="s1", limit=2)
    summary = ledger.summary(session_id="s1")

    assert tail["schema_version"] == "session-ledger-tail-v1"
    assert tail["count"] == 3
    assert [event["sequence"] for event in tail["events"]] == [2, 3]
    assert summary["schema_version"] == "session-ledger-summary-v1"
    assert summary["event_count"] == 3
    assert summary["event_types"] == {"plan": 3}
    assert summary["actors"] == {"agent": 3}
    assert summary["tags"] == {"planning": 3}


def test_session_ledger_rejects_missing_required_fields(tmp_path):
    ledger = SessionLedger(tmp_path)

    with pytest.raises(ValueError):
        ledger.append(session_id="s1", event_type="", actor="agent", content={})
    with pytest.raises(ValueError):
        ledger.append(session_id="s1", event_type="plan", actor="", content={})


def test_session_ledger_detects_tampering(tmp_path):
    ledger = SessionLedger(tmp_path)
    ledger.append(session_id="s1", event_type="plan", actor="agent", content={"ok": True})

    path = tmp_path / "events" / "s1.jsonl"
    event = json.loads(path.read_text().splitlines()[0])
    event["content"] = {"ok": False}
    path.write_text(json.dumps(event) + "\n")

    result = ledger.verify(session_id="s1")
    assert result["ok"] is False
    assert result["error"] == "event_digest_mismatch"


def test_session_ledger_writes_index(tmp_path):
    ledger = SessionLedger(tmp_path)
    event = ledger.append(session_id="s1", event_type="plan", actor="agent", content={})

    index = json.loads((tmp_path / "index.json").read_text())
    assert index["schema_version"] == "session-ledger-index-v1"
    assert index["sessions"]["s1"]["latest_sequence"] == 1
    assert index["sessions"]["s1"]["latest_event_digest"] == event["event_digest"]
