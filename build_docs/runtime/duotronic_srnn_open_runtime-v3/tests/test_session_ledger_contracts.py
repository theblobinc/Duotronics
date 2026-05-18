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


def test_session_ledger_mcp_surface_is_wired():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()

    assert '"name": "runtime.session_append"' in mcp
    assert '"name": "runtime.session_tail"' in mcp
    assert '"name": "runtime.session_summary"' in mcp
    assert '"name": "runtime.session_verify"' in mcp
    assert 'if tool == "runtime.session_append"' in mcp
    assert 'if tool == "runtime.session_tail"' in mcp
    assert 'if tool == "runtime.session_summary"' in mcp
    assert 'if tool == "runtime.session_verify"' in mcp
    assert 'from .session_ledger import SessionLedger' in mcp


def test_session_ledger_index_contract(tmp_path):
    ledger = SessionLedger(tmp_path)
    event = ledger.append(session_id="s1", event_type="plan", actor="agent", content={})

    index = ledger.index()

    assert index["schema_version"] == "session-ledger-index-v1"
    assert index["sessions"]["s1"]["latest_sequence"] == 1
    assert index["sessions"]["s1"]["latest_event_digest"] == event["event_digest"]


def test_session_ledger_mcp_index_surface_is_wired():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()

    assert '"name": "runtime.session_index"' in mcp
    assert 'if tool == "runtime.session_index"' in mcp
    assert "return SessionLedger().index()" in mcp


def test_session_ledger_search_filters_by_tag_tool_and_text(tmp_path):
    ledger = SessionLedger(tmp_path)
    ledger.append(
        session_id="s1",
        event_type="mcp_call_result",
        actor="adapter",
        content={"tool_name": "runtime.session_tail", "result_preview": "found buildout checkpoint"},
        tags=["mcp-auto-capture", "tool-result"],
        created_at_ms=3000,
    )
    ledger.append(
        session_id="s1",
        event_type="plan",
        actor="agent",
        content={"summary": "unrelated planning note"},
        tags=["planning"],
        created_at_ms=3001,
    )

    by_tool = ledger.search(session_id="s1", tool_name="runtime.session_tail")
    by_tag = ledger.search(session_id="s1", tag="planning")
    by_text = ledger.search(session_id="s1", query="checkpoint")

    assert by_tool["schema_version"] == "session-ledger-search-v1"
    assert by_tool["count"] == 1
    assert by_tool["matches"][0]["tool_name"] == "runtime.session_tail"
    assert by_tag["count"] == 1
    assert by_tag["matches"][0]["event_type"] == "plan"
    assert by_text["count"] == 1
    assert "checkpoint" in by_text["matches"][0]["preview"]


def test_session_ledger_search_across_indexed_sessions(tmp_path):
    ledger = SessionLedger(tmp_path)
    ledger.append(session_id="a", event_type="plan", actor="agent", content={"summary": "alpha"})
    ledger.append(session_id="b", event_type="plan", actor="agent", content={"summary": "beta"})

    result = ledger.search(query="beta")

    assert result["count"] == 1
    assert result["matches"][0]["session_id"] == "b"


def test_session_ledger_mcp_search_surface_is_wired():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()

    assert '"name": "runtime.session_search"' in mcp
    assert '"name": "runtime.session_find"' in mcp
    assert 'if tool in {"runtime.session_search", "runtime.session_find"}' in mcp
    assert "return SessionLedger().search(" in mcp
