from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .crypto_primitives import shake256_ref
from .coordination_learning import (
    COORDINATION_LEARNING_SCHEMA_SQL,
    CoordinationLearning,
    coordination_learning_tool_manifest,
)


COORDINATION_SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS coordination_agent_sessions (
  session_id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  device_id_digest TEXT,
  client_name TEXT,
  user_agent TEXT,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','idle','completed','abandoned')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS coordination_agent_last_seen_idx
  ON coordination_agent_sessions(last_seen_at DESC);
CREATE INDEX IF NOT EXISTS coordination_agent_status_idx
  ON coordination_agent_sessions(status, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS coordination_work_items (
  work_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  title TEXT NOT NULL,
  objective TEXT NOT NULL DEFAULT '',
  plan JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('planned','active','blocked','completed','cancelled')),
  priority SMALLINT NOT NULL DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),
  owner_session_id TEXT NOT NULL REFERENCES coordination_agent_sessions(session_id),
  parent_work_id UUID REFERENCES coordination_work_items(work_id) ON DELETE SET NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS coordination_work_project_status_idx
  ON coordination_work_items(project_key, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS coordination_work_owner_idx
  ON coordination_work_items(owner_session_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS coordination_resource_claims (
  claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id UUID REFERENCES coordination_work_items(work_id) ON DELETE SET NULL,
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  session_id TEXT NOT NULL REFERENCES coordination_agent_sessions(session_id),
  agent_id TEXT NOT NULL,
  resource_key TEXT NOT NULL,
  resource_kind TEXT NOT NULL DEFAULT 'path',
  mode TEXT NOT NULL DEFAULT 'exclusive'
    CHECK (mode IN ('exclusive','shared')),
  purpose TEXT NOT NULL DEFAULT '',
  base_digest TEXT,
  lease_token UUID NOT NULL DEFAULT gen_random_uuid(),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','released','expired','cancelled')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  renewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS coordination_claim_active_resource_idx
  ON coordination_resource_claims(project_key, resource_key, expires_at)
  WHERE status = 'active';
CREATE INDEX IF NOT EXISTS coordination_claim_session_idx
  ON coordination_resource_claims(session_id, status, expires_at DESC);
CREATE INDEX IF NOT EXISTS coordination_claim_work_idx
  ON coordination_resource_claims(work_id, status, expires_at DESC);

CREATE TABLE IF NOT EXISTS coordination_events (
  event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_uuid UUID NOT NULL DEFAULT gen_random_uuid(),
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  work_id UUID REFERENCES coordination_work_items(work_id) ON DELETE SET NULL,
  session_id TEXT,
  agent_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  resource_keys TEXT[] NOT NULL DEFAULT '{}'::text[],
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  search_document TEXT NOT NULL DEFAULT '',
  previous_event_digest TEXT,
  event_digest TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS coordination_event_uuid_idx
  ON coordination_events(event_uuid);
CREATE INDEX IF NOT EXISTS coordination_event_project_idx
  ON coordination_events(project_key, event_id DESC);
CREATE INDEX IF NOT EXISTS coordination_event_work_idx
  ON coordination_events(work_id, event_id DESC);
CREATE INDEX IF NOT EXISTS coordination_event_session_idx
  ON coordination_events(session_id, event_id DESC);
CREATE INDEX IF NOT EXISTS coordination_event_resources_idx
  ON coordination_events USING GIN(resource_keys);
CREATE INDEX IF NOT EXISTS coordination_event_search_idx
  ON coordination_events USING GIN(to_tsvector('simple', search_document));

CREATE TABLE IF NOT EXISTS coordination_resource_state (
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  resource_key TEXT NOT NULL,
  last_event_id BIGINT REFERENCES coordination_events(event_id) ON DELETE SET NULL,
  last_work_id UUID REFERENCES coordination_work_items(work_id) ON DELETE SET NULL,
  last_session_id TEXT,
  last_agent_id TEXT,
  last_event_type TEXT,
  last_summary TEXT NOT NULL DEFAULT '',
  last_event_digest TEXT,
  state JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(project_key, resource_key)
);
CREATE INDEX IF NOT EXISTS coordination_resource_state_updated_idx
  ON coordination_resource_state(project_key, updated_at DESC);
"""

COORDINATION_SCHEMA_SQL += COORDINATION_LEARNING_SCHEMA_SQL

_PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
_EVENT_RE = re.compile(r"^[a-z][a-z0-9._:-]{0,79}$")
_STATUS_RE = re.compile(r"^(planned|active|blocked|completed|cancelled)$")

_SECRET_KEY_RE = re.compile(r"(?:password|passwd|secret|token|cookie|authorization|api[_-]?key|private[_-]?key)", re.IGNORECASE)


def _redact_sensitive(value: Any, key: str | None = None) -> Any:
    if key and _SECRET_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact_sensitive(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_sensitive(item) for item in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def _sha(value: Any) -> str:
    return shake256_ref(value)


def _bounded_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except Exception:
        number = default
    return max(low, min(high, number))


def _safe_text(value: Any, default: str, maximum: int) -> str:
    text = str(value if value is not None else default).strip()
    return (text or default)[:maximum]


def _project(value: Any) -> str:
    text = _safe_text(value, "xavi.app-backend", 160)
    if not _PROJECT_RE.fullmatch(text):
        raise HTTPException(422, "Invalid coordination project key")
    return text


def _normalize_resource(value: Any) -> str:
    raw = str(value or "").strip().replace("\\", "/")
    if not raw:
        raise HTTPException(422, "Coordination resource is empty")
    if len(raw) > 1200:
        raise HTTPException(422, "Coordination resource is too long")
    if "://" in raw:
        scheme, rest = raw.split("://", 1)
        return f"{scheme.lower()}://{rest.rstrip('/')}"
    prefix = ""
    body = raw
    if ":" in raw and not raw.startswith("/"):
        candidate, remainder = raw.split(":", 1)
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{0,31}", candidate):
            prefix = candidate.lower() + ":"
            body = remainder
    if body.startswith("/"):
        normalized = PurePosixPath(body).as_posix()
    else:
        normalized = re.sub(r"/{2,}", "/", body)
    normalized = normalized.rstrip("/") or "/"
    return prefix + normalized


def _resources(values: Any) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise HTTPException(422, "resources must be an array")
    output: list[str] = []
    for value in values[:100]:
        resource = _normalize_resource(value)
        if resource not in output:
            output.append(resource)
    return output


def coordination_tool_manifest() -> list[dict[str, Any]]:
    context = {
        "project_key": {"type": "string", "default": "xavi.app-backend"},
        "title": {"type": "string"},
        "objective": {"type": "string"},
        "plan": {"type": "object"},
        "resources": {"type": "array", "items": {"type": "string"}},
        "lease_seconds": {"type": "integer", "minimum": 60, "maximum": 86400, "default": 1800},
    }
    return [
        {
            "name": "coordination.begin",
            "description": "FIRST STEP for backend work: register this MCP agent session, open or resume a shared work item, and return active plans, claims, recent changes, and conflicts.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": context, "additionalProperties": True},
        },
        {
            "name": "coordination.status",
            "description": "Read the shared multi-agent work board: active sessions, plans, resource leases, recent changes, and current resource state.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
                "resources": context["resources"],
                "work_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 30},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.plan",
            "description": "Create or update a shared implementation plan so every MCP agent can see the objective, steps, decisions, blockers, and ownership.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {
                **context,
                "work_id": {"type": "string"},
                "status": {"type": "string", "enum": ["planned","active","blocked","completed","cancelled"]},
                "priority": {"type": "integer", "minimum": 0, "maximum": 100},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.claim",
            "description": "Publish or renew resource activity. Exact-resource exclusive mutations held by another session are conflicts; parent directories and sibling paths remain visible but do not block parallel work.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["resources"], "properties": {
                "project_key": context["project_key"],
                "work_id": {"type": "string"},
                "resources": context["resources"],
                "mode": {"type": "string", "enum": ["exclusive","shared"], "default": "exclusive"},
                "purpose": {"type": "string"},
                "base_digest": {"type": "string"},
                "lease_seconds": context["lease_seconds"],
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.preflight",
            "description": "Check and automatically claim inferred resources immediately before a mutating MCP tool call. The adapter invokes this automatically.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {
                **context,
                "work_id": {"type": "string"},
                "tool_name": {"type": "string"},
                "args_digest": {"type": "string"},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.heartbeat",
            "description": "Refresh this agent session and renew its active resource leases while work continues.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
                "work_id": {"type": "string"},
                "lease_seconds": context["lease_seconds"],
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.event",
            "description": "Append a durable hashed progress, decision, blocker, change, test, deployment, or failure event to shared MCP memory.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["event_type"], "properties": {
                "project_key": context["project_key"],
                "work_id": {"type": "string"},
                "event_type": {"type": "string"},
                "summary": {"type": "string"},
                "resources": context["resources"],
                "payload": {"type": "object"},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.search",
            "description": "Fast full-text search across prior plans and hashed change events, including completed work from earlier MCP sessions.",
            "read_only": True,
            "input_schema": {"type": "object", "required": ["query"], "properties": {
                "project_key": context["project_key"],
                "query": {"type": "string"},
                "resources": context["resources"],
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.release",
            "description": "Release selected or all resource leases owned by this MCP agent session.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
                "work_id": {"type": "string"},
                "resources": context["resources"],
            }, "additionalProperties": True},
        },
        {
            "name": "coordination.finish",
            "description": "Complete, block, cancel, or otherwise close a shared work item; release leases and record the final outcome.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {
                "project_key": context["project_key"],
                "work_id": {"type": "string"},
                "status": {"type": "string", "enum": ["completed","blocked","cancelled"], "default": "completed"},
                "summary": {"type": "string"},
                "payload": {"type": "object"},
                "close_session": {"type": "boolean", "default": False},
            }, "additionalProperties": True},
        },
        *coordination_learning_tool_manifest(context),
    ]


class CoordinationService:
    def __init__(self, store: Any, kernel: Any | None = None) -> None:
        self.store = store
        self.kernel = kernel
        self.learning = CoordinationLearning(store, kernel)

    def _identity(self, args: dict[str, Any]) -> tuple[str, str, str]:
        session_id = _safe_text(args.get("session_id"), "direct-runtime", 220)
        agent_id = _safe_text(args.get("agent_id"), "mcp-client", 160)
        project_key = _project(args.get("project_key"))
        return session_id, agent_id, project_key

    def _cleanup(self, conn: Any) -> None:
        conn.execute("UPDATE coordination_resource_claims SET status='expired' WHERE status='active' AND expires_at<=now()")
        conn.execute(
            """
            UPDATE coordination_resource_claims c
               SET status='released',renewed_at=now(),expires_at=now()
              FROM coordination_work_items w
             WHERE c.work_id=w.work_id
               AND c.status='active'
               AND w.status IN ('completed','cancelled')
            """
        )
        conn.execute("UPDATE coordination_agent_sessions SET status='idle' WHERE status='active' AND last_seen_at<now()-interval '2 hours'")

    def _touch_session(self, conn: Any, args: dict[str, Any]) -> dict[str, Any]:
        session_id, agent_id, _ = self._identity(args)
        metadata = args.get("session_metadata") if isinstance(args.get("session_metadata"), dict) else {}
        row = conn.execute(
            """
            INSERT INTO coordination_agent_sessions
              (session_id,agent_id,device_id_digest,client_name,user_agent,status,metadata,last_seen_at)
            VALUES (%s,%s,%s,%s,%s,'active',%s,now())
            ON CONFLICT (session_id) DO UPDATE SET
              agent_id=EXCLUDED.agent_id,
              device_id_digest=COALESCE(EXCLUDED.device_id_digest,coordination_agent_sessions.device_id_digest),
              client_name=COALESCE(EXCLUDED.client_name,coordination_agent_sessions.client_name),
              user_agent=COALESCE(EXCLUDED.user_agent,coordination_agent_sessions.user_agent),
              status='active', metadata=coordination_agent_sessions.metadata||EXCLUDED.metadata,
              last_seen_at=now(), ended_at=NULL
            RETURNING *
            """,
            (
                session_id, agent_id, args.get("device_id_digest"), args.get("client_name"),
                args.get("user_agent"), Jsonb(metadata),
            ),
        ).fetchone()
        return dict(row)

    def _ensure_work(self, conn: Any, args: dict[str, Any], *, create: bool = True) -> dict[str, Any] | None:
        session_id, _, project_key = self._identity(args)
        supplied = str(args.get("work_id") or "").strip()
        if supplied:
            row = conn.execute("SELECT * FROM coordination_work_items WHERE work_id=%s::uuid AND project_key=%s", (supplied, project_key)).fetchone()
            if row is None:
                raise HTTPException(404, "Coordination work item not found")
            return dict(row)
        row = conn.execute(
            """
            SELECT * FROM coordination_work_items
             WHERE project_key=%s AND owner_session_id=%s AND status IN ('planned','active','blocked')
             ORDER BY updated_at DESC LIMIT 1
            """,
            (project_key, session_id),
        ).fetchone()
        if row is not None or not create:
            return dict(row) if row is not None else None
        title = _safe_text(args.get("title"), f"MCP work by {args.get('agent_id') or 'agent'}", 240)
        objective = _safe_text(args.get("objective"), "Coordinate backend changes safely.", 4000)
        plan = args.get("plan") if isinstance(args.get("plan"), dict) else {}
        metadata = args.get("work_metadata") if isinstance(args.get("work_metadata"), dict) else {"automatic": True}
        row = conn.execute(
            """
            INSERT INTO coordination_work_items
              (project_key,title,objective,plan,status,priority,owner_session_id,metadata)
            VALUES (%s,%s,%s,%s,'active',%s,%s,%s)
            RETURNING *
            """,
            (project_key, title, objective, Jsonb(plan), _bounded_int(args.get("priority"), 50, 0, 100), session_id, Jsonb(metadata)),
        ).fetchone()
        return dict(row)

    def _append_event(
        self,
        conn: Any,
        *,
        project_key: str,
        work_id: Any,
        session_id: str | None,
        agent_id: str,
        event_type: str,
        summary: str,
        resources: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event_type = _safe_text(event_type, "event", 80).lower()
        if not _EVENT_RE.fullmatch(event_type):
            raise HTTPException(422, "Invalid coordination event type")
        summary = _safe_text(summary, event_type.replace("_", " "), 4000)
        payload = json.loads(_canonical(_redact_sensitive(payload)))
        created_at = datetime.now(timezone.utc).isoformat()
        conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"coordination-events:{project_key}",))
        previous = conn.execute(
            "SELECT event_digest FROM coordination_events WHERE project_key=%s ORDER BY event_id DESC LIMIT 1",
            (project_key,),
        ).fetchone()
        previous_digest = previous["event_digest"] if previous else None
        material = {
            "project_key": project_key,
            "work_id": str(work_id) if work_id else None,
            "session_id": session_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "summary": summary,
            "resource_keys": resources,
            "payload": payload,
            "previous_event_digest": previous_digest,
            "created_at": created_at,
        }
        digest = _sha(material)
        search_document = f"{summary}\n{event_type}\n{' '.join(resources)}\n{_canonical(payload)}"
        row = conn.execute(
            """
            INSERT INTO coordination_events
              (project_key,work_id,session_id,agent_id,event_type,summary,resource_keys,payload,
               search_document,previous_event_digest,event_digest,created_at)
            VALUES (%s,%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::timestamptz)
            RETURNING *
            """,
            (project_key, str(work_id) if work_id else None, session_id, agent_id, event_type, summary,
             resources, Jsonb(payload), search_document, previous_digest, digest, created_at),
        ).fetchone()
        event = dict(row)
        for resource in resources:
            state = payload.get("resource_state") if isinstance(payload.get("resource_state"), dict) else {}
            conn.execute(
                """
                INSERT INTO coordination_resource_state
                  (project_key,resource_key,last_event_id,last_work_id,last_session_id,last_agent_id,
                   last_event_type,last_summary,last_event_digest,state,updated_at)
                VALUES (%s,%s,%s,%s::uuid,%s,%s,%s,%s,%s,%s,now())
                ON CONFLICT (project_key,resource_key) DO UPDATE SET
                  last_event_id=EXCLUDED.last_event_id,last_work_id=EXCLUDED.last_work_id,
                  last_session_id=EXCLUDED.last_session_id,last_agent_id=EXCLUDED.last_agent_id,
                  last_event_type=EXCLUDED.last_event_type,last_summary=EXCLUDED.last_summary,
                  last_event_digest=EXCLUDED.last_event_digest,
                  state=coordination_resource_state.state||EXCLUDED.state,updated_at=now()
                """,
                (project_key, resource, event["event_id"], str(work_id) if work_id else None,
                 session_id, agent_id, event_type, summary, digest, Jsonb(state)),
            )
        event["learning"] = self.learning.ingest(conn, event)
        return event

    @staticmethod
    def _overlap_sql() -> str:
        # Coordination claims are presence/activity records. Only the exact same
        # resource can block a conflicting exclusive mutation; parent/child path
        # relationships remain visible on the board but never fence a directory.
        return "resource_key=%s"

    def begin(self, args: dict[str, Any]) -> dict[str, Any]:
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=True)
            if args.get("plan") or args.get("objective") or args.get("title"):
                work = self._update_work(conn, args, work)
            self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"],
                session_id=session["session_id"], agent_id=session["agent_id"], event_type="session_begin",
                summary=_safe_text(args.get("objective"), f"{session['agent_id']} began or resumed work", 4000),
                resources=_resources(args.get("resources")),
                payload={"client_name": session.get("client_name"), "automatic": bool((work.get("metadata") or {}).get("automatic"))},
            )
        if args.get("resources"):
            claim = self.claim({**args, "work_id": str(work["work_id"])})
        else:
            claim = {"allowed": True, "claims": [], "conflicts": []}
        learning = self.learning.context({
            "project_key": work["project_key"],
            "objective": work.get("objective") or args.get("objective"),
            "resources": _resources(args.get("resources")),
            "top_k": 8,
        })
        return {"session": session, "work": work, "claim": claim, "board": self.status({**args, "work_id": str(work["work_id"])}), "learning": learning}

    def _update_work(self, conn: Any, args: dict[str, Any], work: dict[str, Any]) -> dict[str, Any]:
        status = _safe_text(args.get("status"), str(work.get("status") or "active"), 20)
        if not _STATUS_RE.fullmatch(status):
            raise HTTPException(422, "Invalid coordination work status")
        title = _safe_text(args.get("title"), str(work.get("title") or "MCP work"), 240)
        objective = _safe_text(args.get("objective"), str(work.get("objective") or ""), 4000)
        plan = args.get("plan") if isinstance(args.get("plan"), dict) else (work.get("plan") or {})
        priority = _bounded_int(args.get("priority"), int(work.get("priority") or 50), 0, 100)
        row = conn.execute(
            """
            UPDATE coordination_work_items SET title=%s,objective=%s,plan=%s,status=%s,priority=%s,
              updated_at=now(),completed_at=CASE WHEN %s IN ('completed','cancelled') THEN now() ELSE NULL END
             WHERE work_id=%s RETURNING *
            """,
            (title, objective, Jsonb(plan), status, priority, status, work["work_id"]),
        ).fetchone()
        return dict(row)

    def plan(self, args: dict[str, Any]) -> dict[str, Any]:
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=True)
            work = self._update_work(conn, args, work)
            event = self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"],
                session_id=session["session_id"], agent_id=session["agent_id"], event_type="plan_updated",
                summary=f"Plan updated: {work['title']}", resources=_resources(args.get("resources")),
                payload={"objective": work["objective"], "plan": work["plan"], "status": work["status"], "priority": work["priority"]},
            )
            return {"session": session, "work": work, "event": event}

    def _conflicts(self, conn: Any, *, project_key: str, session_id: str, resources: list[str], mode: str) -> list[dict[str, Any]]:
        conflicts: dict[str, dict[str, Any]] = {}
        for resource in resources:
            rows = conn.execute(
                f"""
                SELECT c.*,w.title AS work_title,w.objective AS work_objective,
                       s.client_name,s.last_seen_at
                  FROM coordination_resource_claims c
                  LEFT JOIN coordination_work_items w ON w.work_id=c.work_id
                  LEFT JOIN coordination_agent_sessions s ON s.session_id=c.session_id
                 WHERE c.project_key=%s AND c.status='active' AND c.expires_at>now()
                   AND c.session_id<>%s AND {self._overlap_sql()}
                   AND (%s='exclusive' OR c.mode='exclusive')
                 ORDER BY c.expires_at DESC
                """,
                (project_key, session_id, resource, mode),
            ).fetchall()
            for row in rows:
                conflicts[str(row["claim_id"])] = dict(row) | {"requested_resource": resource}
        return list(conflicts.values())

    def claim(self, args: dict[str, Any]) -> dict[str, Any]:
        resources = _resources(args.get("resources"))
        if not resources:
            raise HTTPException(422, "At least one coordination resource is required")
        mode = _safe_text(args.get("mode"), "exclusive", 16)
        if mode not in {"exclusive", "shared"}:
            raise HTTPException(422, "Invalid coordination claim mode")
        lease_seconds = _bounded_int(args.get("lease_seconds"), 1800, 60, 86400)
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=True)
            conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"coordination-claims:{work['project_key']}",))
            conflicts = self._conflicts(conn, project_key=work["project_key"], session_id=session["session_id"], resources=resources, mode=mode)
            if conflicts:
                self._append_event(
                    conn, project_key=work["project_key"], work_id=work["work_id"], session_id=session["session_id"],
                    agent_id=session["agent_id"], event_type="claim_conflict",
                    summary=f"Resource claim blocked by {len(conflicts)} active overlapping lease(s)", resources=resources,
                    payload={"mode": mode, "conflicts": [{k: v for k, v in row.items() if k not in {"metadata"}} for row in conflicts]},
                )
                return {"allowed": False, "work": work, "claims": [], "conflicts": conflicts}
            claims: list[dict[str, Any]] = []
            for resource in resources:
                existing = conn.execute(
                    """
                    SELECT * FROM coordination_resource_claims
                     WHERE project_key=%s AND session_id=%s AND resource_key=%s AND status='active'
                     ORDER BY acquired_at DESC LIMIT 1
                    """,
                    (work["project_key"], session["session_id"], resource),
                ).fetchone()
                if existing:
                    row = conn.execute(
                        """
                        UPDATE coordination_resource_claims SET work_id=%s,agent_id=%s,mode=%s,purpose=%s,
                          base_digest=COALESCE(%s,base_digest),renewed_at=now(),
                          expires_at=now()+(%s||' seconds')::interval,metadata=metadata||%s
                         WHERE claim_id=%s RETURNING *
                        """,
                        (work["work_id"], session["agent_id"], mode, _safe_text(args.get("purpose"), "MCP backend change", 1000),
                         args.get("base_digest"), lease_seconds, Jsonb(args.get("claim_metadata") if isinstance(args.get("claim_metadata"), dict) else {}), existing["claim_id"]),
                    ).fetchone()
                else:
                    kind = resource.split(":", 1)[0] if ":" in resource else "path"
                    row = conn.execute(
                        """
                        INSERT INTO coordination_resource_claims
                          (work_id,project_key,session_id,agent_id,resource_key,resource_kind,mode,purpose,
                           base_digest,metadata,expires_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now()+(%s||' seconds')::interval)
                        RETURNING *
                        """,
                        (work["work_id"], work["project_key"], session["session_id"], session["agent_id"], resource, kind, mode,
                         _safe_text(args.get("purpose"), "MCP backend change", 1000), args.get("base_digest"),
                         Jsonb(args.get("claim_metadata") if isinstance(args.get("claim_metadata"), dict) else {}), lease_seconds),
                    ).fetchone()
                claims.append(dict(row))
            event = self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"], session_id=session["session_id"],
                agent_id=session["agent_id"], event_type="claim_acquired",
                summary=f"Acquired {len(claims)} {mode} resource lease(s)", resources=resources,
                payload={"mode": mode, "lease_seconds": lease_seconds, "claim_ids": [str(row["claim_id"]) for row in claims]},
            )
            return {"allowed": True, "work": work, "claims": claims, "conflicts": [], "event": event}

    def preflight(self, args: dict[str, Any]) -> dict[str, Any]:
        begin = self.begin({**args, "resources": []})
        resources = _resources(args.get("resources"))
        if not resources:
            return {"allowed": True, "work": begin["work"], "claims": [], "conflicts": [], "warning": "No resources were inferred for this mutating tool call", "board": begin["board"]}
        claim = self.claim({**args, "work_id": str(begin["work"]["work_id"]), "resources": resources,
                            "purpose": args.get("purpose") or f"Automatic preflight for {args.get('tool_name') or 'MCP tool'}"})
        relevant = self.status({**args, "work_id": str(begin["work"]["work_id"]), "resources": resources, "limit": 20})
        learning = self.learning.context({
            "project_key": begin["work"]["project_key"],
            "query": f"tool={args.get('tool_name') or 'unknown'} resources={' '.join(resources)}",
            "resources": resources,
            "top_k": 8,
        })
        return {**claim, "board": relevant, "learning": learning, "tool_name": args.get("tool_name"), "args_digest": args.get("args_digest")}

    def heartbeat(self, args: dict[str, Any]) -> dict[str, Any]:
        lease_seconds = _bounded_int(args.get("lease_seconds"), 1800, 60, 86400)
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=False)
            params: list[Any] = [lease_seconds, session["session_id"]]
            where = "session_id=%s AND status='active'"
            if work:
                where += " AND work_id=%s"
                params.append(work["work_id"])
            rows = conn.execute(
                f"UPDATE coordination_resource_claims SET renewed_at=now(),expires_at=now()+(%s||' seconds')::interval WHERE {where} RETURNING *",
                tuple(params),
            ).fetchall()
            return {"session": session, "work": work, "renewed": [dict(row) for row in rows], "lease_seconds": lease_seconds}

    def event(self, args: dict[str, Any]) -> dict[str, Any]:
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=True)
            payload = args.get("payload") if isinstance(args.get("payload"), dict) else {}
            event = self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"], session_id=session["session_id"],
                agent_id=session["agent_id"], event_type=str(args.get("event_type") or "progress"),
                summary=_safe_text(args.get("summary"), str(args.get("event_type") or "progress"), 4000),
                resources=_resources(args.get("resources")), payload=payload,
            )
            conn.execute("UPDATE coordination_work_items SET updated_at=now() WHERE work_id=%s", (work["work_id"],))
            return {"session": session, "work": work, "event": event}

    def release(self, args: dict[str, Any]) -> dict[str, Any]:
        resources = _resources(args.get("resources"))
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=False)
            params: list[Any] = [session["session_id"]]
            where = "session_id=%s AND status='active'"
            if work:
                where += " AND work_id=%s"
                params.append(work["work_id"])
            if resources:
                where += " AND resource_key=ANY(%s)"
                params.append(resources)
            rows = conn.execute(
                f"UPDATE coordination_resource_claims SET status='released',renewed_at=now(),expires_at=now() WHERE {where} RETURNING *",
                tuple(params),
            ).fetchall()
            if work and rows:
                self._append_event(
                    conn, project_key=work["project_key"], work_id=work["work_id"], session_id=session["session_id"],
                    agent_id=session["agent_id"], event_type="claim_released", summary=f"Released {len(rows)} resource lease(s)",
                    resources=[row["resource_key"] for row in rows], payload={"claim_ids": [str(row["claim_id"]) for row in rows]},
                )
            return {"released": [dict(row) for row in rows], "count": len(rows), "work": work}

    def finish(self, args: dict[str, Any]) -> dict[str, Any]:
        status = _safe_text(args.get("status"), "completed", 20)
        if status not in {"completed", "blocked", "cancelled"}:
            raise HTTPException(422, "finish status must be completed, blocked, or cancelled")
        with self.store.connect() as conn:
            self._cleanup(conn)
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=False)
            if work is None:
                raise HTTPException(404, "No active coordination work item")
            work = self._update_work(conn, {**args, "status": status}, work)
            # Finishing a work item closes the work, not merely this transport's
            # participation in it. A refreshed MCP transport can legitimately finish
            # work created by the prior transport for the same witnessed conversation.
            # Release every active claim bound to the closed work item or those stale
            # leases can deadlock the handoff until their original TTL expires.
            rows = conn.execute(
                "UPDATE coordination_resource_claims SET status='released',expires_at=now(),renewed_at=now() WHERE work_id=%s AND status='active' RETURNING resource_key",
                (work["work_id"],),
            ).fetchall()
            event = self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"], session_id=session["session_id"],
                agent_id=session["agent_id"], event_type=f"work_{status}",
                summary=_safe_text(args.get("summary"), f"Work {status}: {work['title']}", 4000),
                resources=[row["resource_key"] for row in rows],
                payload=args.get("payload") if isinstance(args.get("payload"), dict) else {},
            )
            if bool(args.get("close_session")):
                conn.execute("UPDATE coordination_agent_sessions SET status='completed',ended_at=now(),last_seen_at=now() WHERE session_id=%s", (session["session_id"],))
            return {"work": work, "event": event, "released_resources": [row["resource_key"] for row in rows]}

    def status(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        limit = _bounded_int(args.get("limit"), 30, 1, 200)
        resources = _resources(args.get("resources"))
        with self.store.connect() as conn:
            self._cleanup(conn)
            if args.get("session_id"):
                self._touch_session(conn, args)
            sessions = conn.execute(
                "SELECT * FROM coordination_agent_sessions WHERE status IN ('active','idle') ORDER BY last_seen_at DESC LIMIT %s",
                (limit,),
            ).fetchall()
            works = conn.execute(
                "SELECT * FROM coordination_work_items WHERE project_key=%s AND status IN ('planned','active','blocked') ORDER BY priority DESC,updated_at DESC LIMIT %s",
                (project_key, limit),
            ).fetchall()
            claims = conn.execute(
                """
                SELECT c.*,w.title AS work_title,w.objective AS work_objective,s.client_name,s.last_seen_at
                  FROM coordination_resource_claims c
                  LEFT JOIN coordination_work_items w ON w.work_id=c.work_id
                  LEFT JOIN coordination_agent_sessions s ON s.session_id=c.session_id
                 WHERE c.project_key=%s AND c.status='active' AND c.expires_at>now()
                 ORDER BY c.expires_at DESC LIMIT %s
                """,
                (project_key, max(limit, 100)),
            ).fetchall()
            events = conn.execute(
                "SELECT * FROM coordination_events WHERE project_key=%s ORDER BY event_id DESC LIMIT %s",
                (project_key, limit),
            ).fetchall()
            states = []
            if resources:
                states = conn.execute(
                    "SELECT * FROM coordination_resource_state WHERE project_key=%s AND resource_key=ANY(%s) ORDER BY updated_at DESC",
                    (project_key, resources),
                ).fetchall()
                filtered_claims = []
                for row in claims:
                    if any(row["resource_key"] == r or row["resource_key"].startswith(r + "/") or r.startswith(row["resource_key"] + "/") for r in resources):
                        filtered_claims.append(row)
                claims = filtered_claims
            return {
                "schema_version": "xavi-mcp-coordination-board-v1",
                "project_key": project_key,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "active_sessions": [dict(row) for row in sessions],
                "active_work": [dict(row) for row in works],
                "active_claims": [dict(row) for row in claims],
                "recent_events": [dict(row) for row in events],
                "resource_state": [dict(row) for row in states],
            }

    def search(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        query = _safe_text(args.get("query"), "", 1000)
        if not query:
            raise HTTPException(422, "Coordination search query is required")
        limit = _bounded_int(args.get("limit"), 20, 1, 100)
        resources = _resources(args.get("resources"))
        with self.store.connect() as conn:
            work_rows = conn.execute(
                """
                SELECT *,ts_rank(to_tsvector('simple',title||' '||objective||' '||plan::text),plainto_tsquery('simple',%s)) AS rank
                  FROM coordination_work_items
                 WHERE project_key=%s AND (
                   to_tsvector('simple',title||' '||objective||' '||plan::text) @@ plainto_tsquery('simple',%s)
                   OR title ILIKE %s OR objective ILIKE %s OR plan::text ILIKE %s)
                 ORDER BY rank DESC,updated_at DESC LIMIT %s
                """,
                (query, project_key, query, f"%{query}%", f"%{query}%", f"%{query}%", limit),
            ).fetchall()
            event_rows = conn.execute(
                """
                SELECT *,ts_rank(to_tsvector('simple',search_document),plainto_tsquery('simple',%s)) AS rank
                  FROM coordination_events
                 WHERE project_key=%s AND (
                   to_tsvector('simple',search_document) @@ plainto_tsquery('simple',%s)
                   OR search_document ILIKE %s)
                 ORDER BY rank DESC,event_id DESC LIMIT %s
                """,
                (query, project_key, query, f"%{query}%", limit),
            ).fetchall()
            events = [dict(row) for row in event_rows]
            if resources:
                events = [row for row in events if any(any(r == e or r.startswith(e + "/") or e.startswith(r + "/") for e in row.get("resource_keys", [])) for r in resources)]
            return {"query": query, "project_key": project_key, "work_items": [dict(row) for row in work_rows], "events": events, "count": len(work_rows) + len(events)}

    def learning_replay_verify(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self.learning.replay_verify(args)
        with self.store.connect() as conn:
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=True)
            event = self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"],
                session_id=session["session_id"], agent_id=session["agent_id"],
                event_type="learning_replay_verified" if result.get("verified") else "learning_replay_failed",
                summary="Coordination and WG-RNN replay verification passed" if result.get("verified") else "Coordination or WG-RNN replay verification failed",
                resources=["runtime:wgrnn-memory"], payload={"verification": result},
            )
        return {**result, "coordination_event": event}

    def learning_promote(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self.learning.promote(args)
        with self.store.connect() as conn:
            session = self._touch_session(conn, args)
            work = self._ensure_work(conn, args, create=True)
            event = self._append_event(
                conn, project_key=work["project_key"], work_id=work["work_id"],
                session_id=session["session_id"], agent_id=session["agent_id"],
                event_type="learning_promoted",
                summary=f"Promoted replay-verified WG-RNN coordination slot {result['slot_id']}",
                resources=["runtime:wgrnn-memory"],
                payload={"slot_id": result["slot_id"], "update_id": result["update_id"], "approved_by": result["approved_by"], "reason": result["reason"]},
            )
        return {**result, "coordination_event": event}

    def dispatch(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        handlers = {
            "coordination.begin": self.begin,
            "coordination.status": self.status,
            "coordination.plan": self.plan,
            "coordination.claim": self.claim,
            "coordination.preflight": self.preflight,
            "coordination.heartbeat": self.heartbeat,
            "coordination.event": self.event,
            "coordination.search": self.search,
            "coordination.release": self.release,
            "coordination.finish": self.finish,
            "coordination.learning_status": self.learning.status,
            "coordination.learning_context": self.learning.context,
            "coordination.learning_replay_verify": self.learning_replay_verify,
            "coordination.learning_promote": self.learning_promote,
        }
        handler = handlers.get(tool)
        if handler is None:
            raise HTTPException(404, f"Unknown coordination tool: {tool}")
        return handler(args)
