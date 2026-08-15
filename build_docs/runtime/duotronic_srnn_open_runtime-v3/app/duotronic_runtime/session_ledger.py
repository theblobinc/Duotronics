from __future__ import annotations

import fcntl
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .crypto_primitives import shake256_hex, shake256_ref
from .duotronic_bijective import positive_ordinal_payload


SCHEMA_VERSION = "session-ledger-event-v2"
SUMMARY_SCHEMA_VERSION = "session-ledger-summary-v1"
DEFAULT_LEDGER_ROOT = Path(os.environ.get("XAVI_SESSION_LEDGER_DIR", "/runtime/data/session_ledger"))
_SAFE_SESSION = re.compile(r"[^A-Za-z0-9_.-]+")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return shake256_ref(value)


def _experience_witness_id(*, session_id: str, sequence: int, event_type: str, actor: str, content_digest: str, previous_event_digest: str | None) -> str:
    seed = {
        "schema": "experience-event-witness-id-v1",
        "session_id": session_id,
        "sequence": sequence,
        "event_type": event_type,
        "actor": actor,
        "content_digest": content_digest,
        "previous_event_digest": previous_event_digest,
    }
    return "xevw_" + shake256_hex(_canonical_json(seed))[:40]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _safe_session_id(session_id: str) -> str:
    raw = str(session_id or "default").strip() or "default"
    safe = _SAFE_SESSION.sub("_", raw).strip("._-")
    if not safe:
        safe = "session_" + shake256_hex(raw)[:16]
    return safe[:120]


class SessionLedger:
    """Append-only session ledger with per-session hash chaining."""

    def __init__(self, root: str | Path | None = None, store: Any | None = None) -> None:
        self.root = Path(root) if root is not None else DEFAULT_LEDGER_ROOT
        self._store = store

    def _postgres_store(self):
        if self._store is None:
            from .config import get_settings
            from .db import Store
            self._store = Store(get_settings())
        return self._store

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
        training_eligible: bool = True,
        redaction: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not str(event_type or "").strip():
            raise ValueError("event_type is required")
        if not str(actor or "").strip():
            raise ValueError("actor is required")

        sid = str(session_id or "default").strip() or "default"
        lock_path = self.root / "locks" / f"{_safe_session_id(sid)}.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            existing = self._read_events(sid)
            previous = existing[-1] if existing else None
            sequence = int(previous.get("sequence", 0)) + 1 if previous else 1
            previous_digest = previous.get("event_digest") if previous else None
            payload = dict(content or {})
            event_type_name = str(event_type).strip()
            actor_name = str(actor).strip()
            content_digest = _digest(payload)
            auto_witness = witness_id is None
            effective_witness_id = witness_id or _experience_witness_id(
                session_id=sid,
                sequence=sequence,
                event_type=event_type_name,
                actor=actor_name,
                content_digest=content_digest,
                previous_event_digest=previous_digest,
            )
            record: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "session_id": sid,
                "sequence": sequence,
                "sequence_bijective": positive_ordinal_payload(sequence),
                "event_type": event_type_name,
                "actor": actor_name,
                "created_at_ms": int(created_at_ms if created_at_ms is not None else _now_ms()),
                "content": payload,
                "content_digest": content_digest,
                "previous_event_digest": previous_digest,
                "witness_id": effective_witness_id,
                "supersedes": list(supersedes or []),
                "tags": sorted({str(tag) for tag in (tags or []) if str(tag).strip()}),
                "training_eligible": bool(training_eligible),
                "redaction": dict(redaction or {}),
            }
            record["event_digest"] = _digest(record)
            path = self._events_path(sid)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as events_file:
                events_file.write(_canonical_json(record) + "\n")
                events_file.flush()
                os.fsync(events_file.fileno())
            self._write_index(sid, record)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

        persistence = {
            "jsonl": True,
            "postgres": False,
            "postgres_error": None,
            "witness": not auto_witness,
            "witness_error": None,
        }
        store = self._postgres_store()
        try:
            store.insert_session_event(
                record,
                training_eligible=training_eligible,
                redaction=redaction or {},
            )
            persistence["postgres"] = True
        except Exception as exc:
            persistence["postgres_error"] = f"{type(exc).__name__}: {exc}"[:500]

        if auto_witness:
            witness = {
                "witness_id": record["witness_id"],
                "witness_type": "experience_event",
                "force": "observe",
                "observer_id": "session-ledger",
                "status": "recorded",
                "corpus": {
                    "contract": "duotronic-witness-contract-v1.6-draft-5.3.18",
                    "ledger_schema": SCHEMA_VERSION,
                },
                "payload_digest": record["event_digest"],
                "payload": {
                    "schema_version": "experience-event-witness-v1",
                    "session_id": record["session_id"],
                    "sequence": record["sequence"],
                    "event_type": record["event_type"],
                    "actor": record["actor"],
                    "event_digest": record["event_digest"],
                    "content_digest": record["content_digest"],
                    "previous_event_digest": record.get("previous_event_digest"),
                    "tags": record.get("tags", []),
                    "training_eligible": record["training_eligible"],
                    "redaction": record["redaction"],
                },
                "created_at_ms": record["created_at_ms"],
            }
            try:
                store.insert_witness(witness)
                persistence["witness"] = True
            except Exception as exc:
                persistence["witness_error"] = f"{type(exc).__name__}: {exc}"[:500]

        return {**record, "_persistence": persistence}

    def postgres_search(self, **kwargs: Any) -> dict[str, Any]:
        return self._postgres_store().search_session_events(**kwargs)

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

    def search(
        self,
        *,
        session_id: str | None = None,
        query: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
        tag: str | None = None,
        tool_name: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit), 100))
        q = str(query or "").strip().lower()
        wanted_event_type = str(event_type or "").strip()
        wanted_actor = str(actor or "").strip()
        wanted_tag = str(tag or "").strip()
        wanted_tool = str(tool_name or "").strip()

        if session_id:
            session_ids = [str(session_id).strip() or "default"]
        else:
            session_ids = sorted((self.index().get("sessions") or {}).keys())

        matches: list[dict[str, Any]] = []
        for sid in session_ids:
            for event in reversed(self._read_events(sid)):
                content = event.get("content") if isinstance(event.get("content"), dict) else {}
                tags = event.get("tags") if isinstance(event.get("tags"), list) else []
                if wanted_event_type and event.get("event_type") != wanted_event_type:
                    continue
                if wanted_actor and event.get("actor") != wanted_actor:
                    continue
                if wanted_tag and wanted_tag not in tags:
                    continue
                if wanted_tool and content.get("tool_name") != wanted_tool and wanted_tool not in tags:
                    continue
                haystack = _canonical_json({
                    "event_type": event.get("event_type"),
                    "actor": event.get("actor"),
                    "tags": tags,
                    "content": content,
                }).lower()
                if q and q not in haystack:
                    continue

                preview = content.get("summary") or content.get("result_preview") or content.get("args_preview") or _canonical_json(content)[:240]
                matches.append({
                    "session_id": event.get("session_id"),
                    "sequence": event.get("sequence"),
                    "event_type": event.get("event_type"),
                    "actor": event.get("actor"),
                    "created_at_ms": event.get("created_at_ms"),
                    "event_digest": event.get("event_digest"),
                    "previous_event_digest": event.get("previous_event_digest"),
                    "content_digest": event.get("content_digest"),
                    "tags": tags,
                    "tool_name": content.get("tool_name"),
                    "preview": str(preview)[:320],
                })
                if len(matches) >= limit:
                    return {
                        "schema_version": "session-ledger-search-v1",
                        "query": query,
                        "session_id": session_id,
                        "count": len(matches),
                        "matches": matches,
                    }

        return {
            "schema_version": "session-ledger-search-v1",
            "query": query,
            "session_id": session_id,
            "count": len(matches),
            "matches": matches,
        }

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
