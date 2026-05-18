from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "session-ledger-event-v1"
SUMMARY_SCHEMA_VERSION = "session-ledger-summary-v1"
DEFAULT_LEDGER_ROOT = Path(os.environ.get("XAVI_SESSION_LEDGER_DIR", "/runtime/data/session_ledger"))
_SAFE_SESSION = re.compile(r"[^A-Za-z0-9_.-]+")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _safe_session_id(session_id: str) -> str:
    raw = str(session_id or "default").strip() or "default"
    safe = _SAFE_SESSION.sub("_", raw).strip("._-")
    if not safe:
        safe = "session_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return safe[:120]


class SessionLedger:
    """Append-only session ledger with per-session hash chaining."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_LEDGER_ROOT

    def _events_dir(self) -> Path:
        return self.root / "events"

    def _events_path(self, session_id: str) -> Path:
        return self._events_dir() / f"{_safe_session_id(session_id)}.jsonl"

    def _read_events(self, session_id: str) -> list[dict[str, Any]]:
        path = self._events_path(session_id)
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def append(
        self,
        *,
        session_id: str,
        event_type: str,
        actor: str,
        content: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        witness_id: str | None = None,
        supersedes: list[str] | None = None,
        created_at_ms: int | None = None,
    ) -> dict[str, Any]:
        if not str(event_type or "").strip():
            raise ValueError("event_type is required")
        if not str(actor or "").strip():
            raise ValueError("actor is required")

        sid = str(session_id or "default").strip() or "default"
        existing = self._read_events(sid)
        previous = existing[-1] if existing else None
        sequence = int(previous.get("sequence", 0)) + 1 if previous else 1
        previous_digest = previous.get("event_digest") if previous else None
        payload = dict(content or {})

        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "session_id": sid,
            "sequence": sequence,
            "event_type": str(event_type).strip(),
            "actor": str(actor).strip(),
            "created_at_ms": int(created_at_ms if created_at_ms is not None else _now_ms()),
            "content": payload,
            "content_digest": _digest(payload),
            "previous_event_digest": previous_digest,
            "witness_id": witness_id,
            "supersedes": list(supersedes or []),
            "tags": sorted({str(tag) for tag in (tags or []) if str(tag).strip()}),
        }
        record["event_digest"] = _digest(record)

        path = self._events_path(sid)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(_canonical_json(record) + "\n")
        self._write_index(sid, record)
        return record

    def tail(self, *, session_id: str, limit: int = 20) -> dict[str, Any]:
        limit = max(1, min(int(limit), 200))
        events = self._read_events(session_id)
        return {
            "schema_version": "session-ledger-tail-v1",
            "session_id": str(session_id or "default").strip() or "default",
            "count": len(events),
            "events": events[-limit:],
        }

    def index(self) -> dict[str, Any]:
        path = self.root / "index.json"
        if not path.exists():
            return {"schema_version": "session-ledger-index-v1", "sessions": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"schema_version": "session-ledger-index-v1", "sessions": {}, "corrupt": True}
        if not isinstance(data, dict):
            return {"schema_version": "session-ledger-index-v1", "sessions": {}, "corrupt": True}
        data.setdefault("schema_version", "session-ledger-index-v1")
        data.setdefault("sessions", {})
        return data

    def summary(self, *, session_id: str) -> dict[str, Any]:
        events = self._read_events(session_id)
        event_types = Counter(event.get("event_type") for event in events)
        actors = Counter(event.get("actor") for event in events)
        tags = Counter(tag for event in events for tag in event.get("tags", []))
        latest = events[-1] if events else None
        return {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "session_id": str(session_id or "default").strip() or "default",
            "event_count": len(events),
            "latest_event_digest": latest.get("event_digest") if latest else None,
            "latest_sequence": latest.get("sequence") if latest else 0,
            "event_types": dict(sorted(event_types.items())),
            "actors": dict(sorted(actors.items())),
            "tags": dict(sorted(tags.items())),
        }

    def verify(self, *, session_id: str) -> dict[str, Any]:
        events = self._read_events(session_id)
        previous_digest: str | None = None
        for expected_sequence, event in enumerate(events, start=1):
            if event.get("sequence") != expected_sequence:
                return {"ok": False, "error": "sequence_gap", "sequence": expected_sequence}
            if event.get("previous_event_digest") != previous_digest:
                return {"ok": False, "error": "previous_digest_mismatch", "sequence": expected_sequence}
            event_copy = dict(event)
            digest = event_copy.pop("event_digest", None)
            if _digest(event_copy) != digest:
                return {"ok": False, "error": "event_digest_mismatch", "sequence": expected_sequence}
            previous_digest = digest
        return {"ok": True, "session_id": session_id, "event_count": len(events), "latest_event_digest": previous_digest}

    def _write_index(self, session_id: str, latest: dict[str, Any]) -> None:
        path = self.root / "index.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {"schema_version": "session-ledger-index-v1", "sessions": {}}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = {"schema_version": "session-ledger-index-v1", "sessions": {}}
        sessions = data.setdefault("sessions", {})
        sessions[str(session_id)] = {
            "latest_sequence": latest["sequence"],
            "latest_event_digest": latest["event_digest"],
            "updated_at_ms": latest["created_at_ms"],
        }
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
