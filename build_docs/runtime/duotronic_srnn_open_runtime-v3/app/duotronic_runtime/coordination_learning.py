from __future__ import annotations

from .crypto_primitives import shake256_ref

import json
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from psycopg.types.json import Jsonb

COORDINATION_LEARNING_SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS coordination_learning_links (
  event_id BIGINT PRIMARY KEY REFERENCES coordination_events(event_id) ON DELETE CASCADE,
  event_digest TEXT NOT NULL,
  project_key TEXT NOT NULL,
  wgrnn_namespace TEXT NOT NULL,
  slot_id INTEGER NOT NULL,
  update_id TEXT NOT NULL,
  trust_status TEXT NOT NULL,
  authority_t DOUBLE PRECISION NOT NULL DEFAULT 0,
  confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
  contradiction DOUBLE PRECISION NOT NULL DEFAULT 0,
  requested_action TEXT NOT NULL,
  replay_verified BOOLEAN NOT NULL DEFAULT FALSE,
  replay_checked_at TIMESTAMPTZ,
  promoted_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS coordination_learning_project_idx
  ON coordination_learning_links(project_key, event_id DESC);
CREATE INDEX IF NOT EXISTS coordination_learning_slot_idx
  ON coordination_learning_links(project_key, wgrnn_namespace, slot_id, event_id DESC);
CREATE INDEX IF NOT EXISTS coordination_learning_update_idx
  ON coordination_learning_links(project_key, update_id);
"""

_EVENT_TOKEN = re.compile(r"[^a-z0-9._:-]+")
_HIGH_VALUE_PARTS = (
    "succeeded", "failed", "passed", "blocked", "completed", "decision",
    "deployment", "change", "conflict", "repaired", "fixed", "rollback",
)
_SKIP_EVENTS = {"session_begin", "claim_acquired", "claim_released"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def _sha(value: Any) -> str:
    return shake256_ref(value)


def _project(value: Any) -> str:
    text = str(value or "xavi.app-backend").strip()[:160]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}", text):
        raise HTTPException(422, "Invalid coordination learning project key")
    return text


def _limit(value: Any, default: int = 20, maximum: int = 100) -> int:
    try:
        number = int(value)
    except Exception:
        number = default
    return max(1, min(maximum, number))


def _namespace_parts(project_key: str) -> dict[str, str]:
    return {
        "user_id": "system",
        "agent_id": "xavi-mcp-coordinator",
        "thread_id": project_key,
    }


def _namespace(project_key: str) -> str:
    return f"system/xavi-mcp-coordinator/{project_key}"


def _event_quality(event_type: str) -> float:
    if any(part in event_type for part in ("test_passed", "tool_succeeded", "work_completed", "deployment_succeeded", "repaired", "fixed")):
        return 0.97
    if any(part in event_type for part in ("failed", "blocked", "conflict", "rollback", "quarantine")):
        return 0.92
    if any(part in event_type for part in ("decision", "plan_updated", "change", "progress")):
        return 0.84
    return 0.72


def coordination_learning_tool_manifest(context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": "coordination.learning_status",
            "description": "Inspect the MCP coordination WG-RNN namespace, linked source events, candidate/quarantine/promoted slots, and replay state.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
                "include_slots": {"type": "boolean", "default": False},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.learning_context",
            "description": "Retrieve recurrent MCP lessons for an objective, tool, or resource and resolve WG-RNN slots back to human-readable plans, failures, and successful fixes.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
                "query": {"type": "string"},
                "objective": {"type": "string"},
                "resources": context["resources"],
                "top_k": {"type": "integer", "minimum": 1, "maximum": 20, "default": 8},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.learning_replay_verify",
            "description": "Witness and verify both the WG-RNN ledger and the linked coordination event hash chain before any learned MCP behavior is promoted.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.learning_promote",
            "description": "Explicitly promote one replay-verified coordination WG-RNN slot. Automatic event ingestion never promotes itself.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["slot_id", "reason", "approved_by"], "properties": {
                "project_key": context["project_key"],
                "slot_id": {"type": "integer", "minimum": 0},
                "reason": {"type": "string"},
                "approved_by": {"type": "string"},
            }, "additionalProperties": True},
        },
    ]


class CoordinationLearning:
    def __init__(self, store: Any, kernel: Any | None) -> None:
        self.store = store
        self.kernel = kernel

    def available(self) -> bool:
        return self.kernel is not None and getattr(self.kernel, "wgrnn", None) is not None

    def ingest(self, conn: Any, event: dict[str, Any]) -> dict[str, Any]:
        event_type = str(event.get("event_type") or "event").lower()
        if not self.available():
            return {"ingested": False, "reason": "wgrnn_unavailable"}
        if event_type.startswith("learning_") or event_type in _SKIP_EVENTS:
            return {"ingested": False, "reason": "event_not_selected"}
        project_key = _project(event.get("project_key"))
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        resources = list(event.get("resource_keys") or [])[:12]
        tool_name = str(payload.get("tool_name") or payload.get("command_name") or "")[:160]
        feature = {
            "project_key": project_key,
            "event_type": event_type,
            "tool_name": tool_name or None,
            "resources": resources,
            "status": payload.get("status"),
        }
        prompt = "MCP coordination operational pattern\n" + _canonical(feature)
        response_text = str(event.get("summary") or event_type)[:4000] + "\n" + _canonical(payload)[:6000]
        requested_action = "memory_write" if any(part in event_type for part in _HIGH_VALUE_PARTS) else "observe"
        evidence_quality = _event_quality(event_type)
        tags = [
            "mcp-coordination",
            _EVENT_TOKEN.sub("-", project_key.lower())[:80],
            _EVENT_TOKEN.sub("-", event_type)[:80],
        ]
        if tool_name:
            tags.append("tool:" + _EVENT_TOKEN.sub("-", tool_name.lower())[:72])
        try:
            result = self.kernel.wgrnn_step_witnessed(
                prompt=prompt,
                response_text=response_text,
                requested_action=requested_action,
                evidence_quality=evidence_quality,
                tags=tags,
                **_namespace_parts(project_key),
            )
            update = result.get("memory_update") or {}
            namespace = str(result.get("namespace") or _namespace(project_key))
            conn.execute(
                """
                INSERT INTO coordination_learning_links
                  (event_id,event_digest,project_key,wgrnn_namespace,slot_id,update_id,trust_status,
                   authority_t,confidence,contradiction,requested_action,metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_id) DO UPDATE SET
                  event_digest=EXCLUDED.event_digest,project_key=EXCLUDED.project_key,
                  wgrnn_namespace=EXCLUDED.wgrnn_namespace,slot_id=EXCLUDED.slot_id,
                  update_id=EXCLUDED.update_id,trust_status=EXCLUDED.trust_status,
                  authority_t=EXCLUDED.authority_t,confidence=EXCLUDED.confidence,
                  contradiction=EXCLUDED.contradiction,requested_action=EXCLUDED.requested_action,
                  metadata=coordination_learning_links.metadata||EXCLUDED.metadata
                """,
                (
                    event["event_id"], event["event_digest"], project_key, namespace,
                    int(update.get("slot_id")), str(update.get("update_id")), str(update.get("trust_status")),
                    float(update.get("authority_t") or 0.0), float(update.get("confidence") or 0.0),
                    float(update.get("contradiction") or 0.0), requested_action,
                    Jsonb({"feature_digest": _sha(feature), "witness_id": (result.get("witness") or {}).get("witness_id")}),
                ),
            )
            return {
                "ingested": True,
                "namespace": namespace,
                "slot_id": update.get("slot_id"),
                "update_id": update.get("update_id"),
                "trust_status": update.get("trust_status"),
                "authority_t": update.get("authority_t"),
                "requested_action": requested_action,
            }
        except Exception as exc:
            return {"ingested": False, "reason": "wgrnn_ingest_failed", "error_digest": _sha(str(exc))}

    def status(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        limit = _limit(args.get("limit"), 30)
        if not self.available():
            return {"available": False, "project_key": project_key, "reason": "wgrnn_unavailable"}
        snapshot = self.kernel.wgrnn.snapshot(include_slots=bool(args.get("include_slots")), **_namespace_parts(project_key))
        with self.store.connect() as conn:
            counts = conn.execute(
                "SELECT trust_status,count(*) AS count FROM coordination_learning_links WHERE project_key=%s GROUP BY trust_status ORDER BY trust_status",
                (project_key,),
            ).fetchall()
            rows = conn.execute(
                """
                SELECT l.*,e.event_type,e.summary,e.resource_keys,e.payload,e.created_at AS event_created_at
                  FROM coordination_learning_links l
                  JOIN coordination_events e ON e.event_id=l.event_id
                 WHERE l.project_key=%s ORDER BY l.event_id DESC LIMIT %s
                """,
                (project_key, limit),
            ).fetchall()
        return {
            "available": True,
            "project_key": project_key,
            "namespace": _namespace(project_key),
            "snapshot": snapshot,
            "link_counts": [dict(row) for row in counts],
            "recent_links": [dict(row) for row in rows],
        }

    def context(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        resources = [str(value) for value in (args.get("resources") or []) if str(value).strip()][:20]
        query = str(args.get("query") or args.get("objective") or "").strip()
        if resources:
            query = (query + "\nresources=" + " ".join(resources)).strip()
        if not query:
            query = "MCP backend coordination plans changes failures tests and successful fixes"
        if not self.available():
            return {"available": False, "project_key": project_key, "query": query, "lessons": []}
        retrieval = self.kernel.wgrnn.retrieve(query, top_k=_limit(args.get("top_k"), 8, 20), **_namespace_parts(project_key))
        lessons: list[dict[str, Any]] = []
        with self.store.connect() as conn:
            for result in retrieval.get("results", []):
                row = conn.execute(
                    """
                    SELECT l.*,e.event_type,e.summary,e.resource_keys,e.payload,e.created_at AS event_created_at
                      FROM coordination_learning_links l
                      JOIN coordination_events e ON e.event_id=l.event_id
                     WHERE l.project_key=%s AND l.update_id=%s
                     ORDER BY l.event_id DESC LIMIT 1
                    """,
                    (project_key, result.get("update_id")),
                ).fetchone()
                if row is None:
                    continue
                source = dict(row)
                event_type = str(source.get("event_type") or "")
                if "failed" in event_type:
                    suggestion = "Review this prior failure and its resource state before repeating the operation."
                elif "conflict" in event_type:
                    suggestion = "Coordinate with the active owner or narrow the resource claim before editing."
                elif any(part in event_type for part in ("passed", "succeeded", "completed", "fixed", "repaired")):
                    suggestion = "A prior successful operational pattern exists; reuse its tested sequence where applicable."
                elif source.get("trust_status") == "promoted":
                    suggestion = "This is promoted recurrent operational memory and should be treated as established guidance."
                else:
                    suggestion = "Candidate recurrent memory; inspect its source event before relying on it."
                lessons.append({"retrieval": result, "source_event": source, "suggestion": suggestion})
        return {
            "available": True,
            "project_key": project_key,
            "namespace": _namespace(project_key),
            "query": query,
            "query_digest": _sha(query),
            "lessons": lessons,
            "count": len(lessons),
        }

    def _verify_coordination_chain(self, project_key: str) -> dict[str, Any]:
        with self.store.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM coordination_events WHERE project_key=%s ORDER BY event_id",
                (project_key,),
            ).fetchall()
        previous = None
        failures = []
        for row in rows:
            item = dict(row)
            created_at = item["created_at"]
            if isinstance(created_at, datetime):
                created_at = created_at.astimezone(timezone.utc).isoformat()
            material = {
                "project_key": item["project_key"],
                "work_id": str(item["work_id"]) if item.get("work_id") else None,
                "session_id": item.get("session_id"),
                "agent_id": item["agent_id"],
                "event_type": item["event_type"],
                "summary": item["summary"],
                "resource_keys": list(item.get("resource_keys") or []),
                "payload": item.get("payload") or {},
                "previous_event_digest": item.get("previous_event_digest"),
                "created_at": created_at,
            }
            if item.get("previous_event_digest") != previous:
                failures.append({"event_id": item["event_id"], "reason": "previous_event_digest_mismatch"})
            recalculated = _sha(material)
            if recalculated != item.get("event_digest"):
                failures.append({"event_id": item["event_id"], "reason": "event_digest_mismatch"})
            previous = item.get("event_digest")
        return {"verified": not failures, "events": len(rows), "failures": failures[:20]}

    def replay_verify(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        if not self.available():
            raise HTTPException(503, "WG-RNN coordination learning is unavailable")
        wgrnn = self.kernel.wgrnn_replay_verify_witnessed(**_namespace_parts(project_key))
        coordination = self._verify_coordination_chain(project_key)
        verified = bool(wgrnn.get("verified")) and bool(coordination.get("verified"))
        with self.store.connect() as conn:
            conn.execute(
                "UPDATE coordination_learning_links SET replay_verified=%s,replay_checked_at=now() WHERE project_key=%s",
                (verified, project_key),
            )
        return {
            "project_key": project_key,
            "namespace": _namespace(project_key),
            "verified": verified,
            "wgrnn": wgrnn,
            "coordination_chain": coordination,
        }

    def promote(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        approved_by = str(args.get("approved_by") or "").strip()[:240]
        reason = str(args.get("reason") or "").strip()[:1000]
        if not approved_by or not reason:
            raise HTTPException(422, "approved_by and reason are required for learned MCP promotion")
        verification = self.replay_verify(args)
        if not verification.get("verified"):
            raise HTTPException(409, "Cannot promote WG-RNN coordination memory before successful replay verification")
        slot_id = int(args.get("slot_id"))
        snapshot = self.kernel.wgrnn.snapshot(include_slots=True, **_namespace_parts(project_key))
        slot = next((row for row in snapshot.get("slots", []) if int(row.get("slot_id")) == slot_id), None)
        if slot is None:
            raise HTTPException(404, "WG-RNN slot not found")
        if slot.get("trust_status") not in {"candidate", "quarantine"}:
            raise HTTPException(409, "WG-RNN slot is not a promotable candidate or quarantine slot")
        update_id = str(slot.get("update_id") or "")
        with self.store.connect() as conn:
            link = conn.execute(
                "SELECT * FROM coordination_learning_links WHERE project_key=%s AND update_id=%s ORDER BY event_id DESC LIMIT 1",
                (project_key, update_id),
            ).fetchone()
        if link is None:
            raise HTTPException(409, "WG-RNN slot is not linked to a coordination event")
        result = self.kernel.wgrnn_promote_witnessed(
            slot_id=slot_id,
            reason=f"{reason}; approved_by={approved_by}",
            **_namespace_parts(project_key),
        )
        with self.store.connect() as conn:
            conn.execute(
                """
                UPDATE coordination_learning_links SET trust_status='promoted',promoted_at=now(),
                  metadata=metadata||%s WHERE project_key=%s AND update_id=%s
                """,
                (Jsonb({"approved_by": approved_by, "promotion_reason": reason}), project_key, update_id),
            )
        return {
            "project_key": project_key,
            "namespace": _namespace(project_key),
            "slot_id": slot_id,
            "update_id": update_id,
            "approved_by": approved_by,
            "reason": reason,
            "verification": verification,
            "promotion": result,
            "source_link": dict(link),
        }
