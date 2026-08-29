from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .crypto_primitives import shake256_ref


SESSION_DELEGATION_SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS mcp_session_messages (
  message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_session_id TEXT NOT NULL,
  recipient_session_id TEXT NOT NULL,
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  work_id UUID,
  delegation_id UUID,
  message_type TEXT NOT NULL DEFAULT 'message'
    CHECK (message_type IN ('message','suggestion','handoff','request','result','system')),
  subject TEXT NOT NULL DEFAULT '',
  body TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','delivered','read','acknowledged','expired','cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  delivered_at TIMESTAMPTZ,
  read_at TIMESTAMPTZ,
  acknowledged_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS mcp_session_messages_recipient_idx
  ON mcp_session_messages(recipient_session_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS mcp_session_messages_sender_idx
  ON mcp_session_messages(sender_session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS mcp_session_messages_work_idx
  ON mcp_session_messages(work_id, created_at DESC);

CREATE TABLE IF NOT EXISTS mcp_delegations (
  delegation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_id UUID NOT NULL,
  parent_work_id UUID,
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  delegator_session_id TEXT NOT NULL,
  delegate_session_id TEXT,
  delegate_kind TEXT NOT NULL DEFAULT 'session'
    CHECK (delegate_kind IN ('session','wgrnn','worker')),
  objective TEXT NOT NULL,
  required_capabilities TEXT[] NOT NULL DEFAULT '{}'::text[],
  resource_hints JSONB NOT NULL DEFAULT '{}'::jsonb,
  acceptance JSONB NOT NULL DEFAULT '{}'::jsonb,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','offered','accepted','running','blocked','completed','failed','cancelled','declined')),
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  accepted_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS mcp_delegations_delegate_idx
  ON mcp_delegations(delegate_session_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS mcp_delegations_kind_idx
  ON mcp_delegations(delegate_kind, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS mcp_delegations_work_idx
  ON mcp_delegations(work_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS mcp_worker_registry (
  worker_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL UNIQUE,
  worker_kind TEXT NOT NULL
    CHECK (worker_kind IN ('wgrnn','agent','service')),
  status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','idle','busy','disabled','error')),
  capabilities TEXT[] NOT NULL DEFAULT '{}'::text[],
  allowed_tools TEXT[] NOT NULL DEFAULT '{}'::text[],
  resource_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS mcp_worker_registry_kind_idx
  ON mcp_worker_registry(worker_kind, status, last_seen_at DESC);

CREATE TABLE IF NOT EXISTS mcp_delegated_tool_runs (
  run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  delegation_id UUID NOT NULL REFERENCES mcp_delegations(delegation_id) ON DELETE CASCADE,
  worker_id TEXT NOT NULL REFERENCES mcp_worker_registry(worker_id),
  tool_name TEXT NOT NULL,
  tool_args JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','running','completed','failed','cancelled')),
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS mcp_delegated_tool_runs_worker_idx
  ON mcp_delegated_tool_runs(worker_id, status, created_at ASC);
"""


def _safe_text(value: Any, default: str = "", maximum: int = 20000) -> str:
    text = str(value if value is not None else default).strip()
    return (text or default)[:maximum]


def _project(value: Any) -> str:
    text = _safe_text(value, "xavi.app-backend", 160)
    if not text:
        raise HTTPException(422, "project_key is required")
    return text


def _uuid(value: Any, *, required: bool = False) -> str | None:
    text = _safe_text(value, "", 80)
    if not text:
        if required:
            raise HTTPException(422, "UUID value is required")
        return None
    try:
        return str(uuid.UUID(text))
    except Exception as exc:
        raise HTTPException(422, f"Invalid UUID: {text}") from exc


def _clean_array(value: Any, maximum: int = 64) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple, set)):
        raise HTTPException(422, "Expected an array")
    out: list[str] = []
    for item in list(value)[:maximum]:
        text = _safe_text(item, "", 160)
        if text and text not in out:
            out.append(text)
    return out


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return shake256_ref(raw)


def session_delegation_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "session.list",
            "description": "List addressable MCP sessions and registered workers, including current activity metadata.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {"project_key": {"type": "string"}, "active_within_seconds": {"type": "integer", "minimum": 1, "maximum": 604800, "default": 86400}, "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}}, "additionalProperties": True},
        },
        {
            "name": "session.send_message",
            "description": "Send a durable addressed message to another MCP session. The recipient sees it through session.inbox on its next MCP turn.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["recipient_session_id", "body"], "properties": {"recipient_session_id": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}, "message_type": {"type": "string", "enum": ["message","suggestion","handoff","request","result","system"], "default": "message"}, "project_key": {"type": "string"}, "work_id": {"type": ["string","null"]}, "delegation_id": {"type": ["string","null"]}, "payload": {"type": "object"}, "expires_seconds": {"type": ["integer","null"], "minimum": 60, "maximum": 604800}}, "additionalProperties": True},
        },
        {
            "name": "session.inbox",
            "description": "Read messages addressed to the current MCP session and mark queued messages delivered.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {"status": {"type": ["string","null"], "enum": ["queued","delivered","read","acknowledged",None]}, "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}, "mark_read": {"type": "boolean", "default": False}}, "additionalProperties": True},
        },
        {
            "name": "session.acknowledge",
            "description": "Acknowledge one addressed session message.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["message_id"], "properties": {"message_id": {"type": "string"}, "read": {"type": "boolean", "default": True}}, "additionalProperties": True},
        },
        {
            "name": "delegation.assign",
            "description": "Create an explicit work delegation to a session or to the governed WG-RNN worker.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["objective"], "properties": {"objective": {"type": "string"}, "delegate_session_id": {"type": ["string","null"]}, "delegate_kind": {"type": "string", "enum": ["session","wgrnn","worker"], "default": "session"}, "work_id": {"type": ["string","null"]}, "parent_work_id": {"type": ["string","null"]}, "project_key": {"type": "string"}, "required_capabilities": {"type": "array", "items": {"type": "string"}}, "resource_hints": {"type": "object"}, "acceptance": {"type": "object"}, "payload": {"type": "object"}, "tool_name": {"type": ["string","null"]}, "tool_args": {"type": "object"}}, "additionalProperties": True},
        },
        {
            "name": "delegation.inbox",
            "description": "List work delegated to the current session or, when requested, to the WG-RNN worker.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {"delegate_kind": {"type": "string", "enum": ["session","wgrnn","worker"], "default": "session"}, "status": {"type": ["string","null"]}, "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}}, "additionalProperties": True},
        },
        {
            "name": "delegation.update",
            "description": "Accept, start, block, complete, fail, decline, or cancel a delegated work item.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["delegation_id", "status"], "properties": {"delegation_id": {"type": "string"}, "status": {"type": "string", "enum": ["accepted","running","blocked","completed","failed","cancelled","declined"]}, "result": {"type": "object"}}, "additionalProperties": True},
        },
        {
            "name": "worker.register_wgrnn",
            "description": "Register or refresh the governed WG-RNN MCP worker identity and its allowlisted capabilities/tools.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {"capabilities": {"type": "array", "items": {"type": "string"}}, "allowed_tools": {"type": "array", "items": {"type": "string"}}, "resource_profile": {"type": "object"}, "metadata": {"type": "object"}}, "additionalProperties": True},
        },
        {
            "name": "worker.wgrnn_tick",
            "description": "Process one queued WG-RNN delegation. Tool execution is restricted to an explicit read-only/safe allowlist and is witnessed through the normal MCP boundary.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {"max_tasks": {"type": "integer", "minimum": 1, "maximum": 8, "default": 1}}, "additionalProperties": True},
        },
    ]


class SessionDelegationService:
    WGRNN_WORKER_ID = "worker:wgrnn-main"
    WGRNN_SESSION_ID = "wgrnn:worker:main"
    DEFAULT_WGRNN_TOOLS = (
        "runtime.health",
        "runtime.models",
        "runtime.service_registry",
        "runtime.service_health",
        "runtime.node_pressure",
        "runtime.service_candidates",
        "runtime.capabilities",
        "runtime.autonomy_status",
        "runtime.autonomy_continuation",
        "runtime.autonomy_schedule",
        "runtime.autonomy_research",
        "runtime.session_search",
        "runtime.reference_search",
        "runtime.session_find",
        "runtime.session_tail",
        "runtime.transcript_search",
        "coordination.status",
        "coordination.search",
    )

    def __init__(self, kernel: Any) -> None:
        self.kernel = kernel
        self.store = kernel.store
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with self.store.connect() as conn:
            conn.execute(SESSION_DELEGATION_SCHEMA_SQL)
            conn.commit()

    def _ensure_session(self, session_id: str, agent_id: str, *, client_name: str = "mcp-client", metadata: dict[str, Any] | None = None) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT INTO coordination_agent_sessions(session_id,agent_id,client_name,status,metadata,last_seen_at)
                VALUES (%s,%s,%s,'active',%s,now())
                ON CONFLICT(session_id) DO UPDATE SET
                  agent_id=EXCLUDED.agent_id,
                  client_name=EXCLUDED.client_name,
                  status='active',
                  metadata=coordination_agent_sessions.metadata || EXCLUDED.metadata,
                  last_seen_at=now(),
                  ended_at=NULL
                """,
                (session_id, agent_id, client_name, Jsonb(metadata or {})),
            )
            conn.commit()

    def register_wgrnn(self, args: dict[str, Any]) -> dict[str, Any]:
        capabilities = _clean_array(args.get("capabilities") or ["wgrnn", "retrieval", "coordination", "scheduling", "analysis"])
        requested_tools = _clean_array(args.get("allowed_tools") or list(self.DEFAULT_WGRNN_TOOLS), 128)
        runtime_tools = {str(item.get("name")) for item in self.kernel_tool_manifest()}
        allowed = [name for name in requested_tools if name in runtime_tools and self._safe_wgrnn_tool(name)]
        self._ensure_session(self.WGRNN_SESSION_ID, "agent:wgrnn", client_name="WG-RNN", metadata={"worker": True, "worker_kind": "wgrnn"})
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT INTO mcp_worker_registry(worker_id,session_id,worker_kind,status,capabilities,allowed_tools,resource_profile,metadata,last_seen_at)
                VALUES (%s,%s,'wgrnn','idle',%s,%s,%s,%s,now())
                ON CONFLICT(worker_id) DO UPDATE SET
                  status=CASE WHEN mcp_worker_registry.status='disabled' THEN 'disabled' ELSE 'idle' END,
                  capabilities=EXCLUDED.capabilities,
                  allowed_tools=EXCLUDED.allowed_tools,
                  resource_profile=EXCLUDED.resource_profile,
                  metadata=mcp_worker_registry.metadata || EXCLUDED.metadata,
                  last_seen_at=now()
                """,
                (self.WGRNN_WORKER_ID, self.WGRNN_SESSION_ID, capabilities, allowed, Jsonb(args.get("resource_profile") or {}), Jsonb(args.get("metadata") or {})),
            )
            conn.commit()
        return {"worker_id": self.WGRNN_WORKER_ID, "session_id": self.WGRNN_SESSION_ID, "capabilities": capabilities, "allowed_tools": allowed, "status": "idle"}

    def kernel_tool_manifest(self) -> list[dict[str, Any]]:
        from .http_mcp import _tool_manifest
        return _tool_manifest()

    @staticmethod
    def _safe_wgrnn_tool(name: str) -> bool:
        prefixes = ("runtime.session_", "runtime.transcript_", "coordination.")
        exact = {
            "runtime.health", "runtime.models", "runtime.service_registry", "runtime.service_health", "runtime.node_pressure", "runtime.service_candidates", "runtime.capabilities",
            "runtime.autonomy_status", "runtime.autonomy_continuation", "runtime.autonomy_schedule", "runtime.autonomy_research",
            "runtime.reference_search",
        }
        if name in exact:
            return True
        if name.startswith(prefixes):
            destructive = ("append", "ingest", "build", "finish", "claim", "release", "event", "plan", "begin", "heartbeat", "preflight")
            return not any(part in name for part in destructive)
        return False

    def list_sessions(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _project(args.get("project_key"))
        seconds = max(1, min(int(args.get("active_within_seconds", 86400)), 604800))
        limit = max(1, min(int(args.get("limit", 50)), 200))
        with self.store.connect() as conn:
            sessions = conn.execute(
                """
                SELECT s.session_id,s.agent_id,s.client_name,s.status,s.metadata,s.started_at,s.last_seen_at,
                       (SELECT count(*) FROM coordination_work_items w WHERE w.owner_session_id=s.session_id AND w.status IN ('planned','active','blocked')) AS open_work,
                       (SELECT count(*) FROM mcp_session_messages m WHERE m.recipient_session_id=s.session_id AND m.status IN ('queued','delivered')) AS unread_messages
                FROM coordination_agent_sessions s
                WHERE s.last_seen_at >= now() - make_interval(secs => %s)
                ORDER BY s.last_seen_at DESC LIMIT %s
                """,
                (seconds, limit),
            ).fetchall()
            workers = conn.execute("SELECT worker_id,session_id,worker_kind,status,capabilities,allowed_tools,resource_profile,metadata,last_seen_at FROM mcp_worker_registry ORDER BY last_seen_at DESC").fetchall()
        return {"project_key": project_key, "sessions": [dict(row) for row in sessions], "workers": [dict(row) for row in workers]}

    def send_message(self, args: dict[str, Any]) -> dict[str, Any]:
        sender = _safe_text(args.get("session_id"), "", 200)
        recipient = _safe_text(args.get("recipient_session_id"), "", 200)
        if not sender or not recipient:
            raise HTTPException(422, "sender and recipient session IDs are required")
        body = _safe_text(args.get("body"), "", 100000)
        if not body:
            raise HTTPException(422, "message body is required")
        message_type = _safe_text(args.get("message_type"), "message", 20)
        if message_type not in {"message","suggestion","handoff","request","result","system"}:
            raise HTTPException(422, "invalid message_type")
        work_id = _uuid(args.get("work_id"))
        delegation_id = _uuid(args.get("delegation_id"))
        expires_seconds = args.get("expires_seconds")
        expires_at = None
        if expires_seconds is not None:
            seconds = max(60, min(int(expires_seconds), 604800))
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        with self.store.connect() as conn:
            target = conn.execute("SELECT session_id FROM coordination_agent_sessions WHERE session_id=%s", (recipient,)).fetchone()
            if target is None:
                raise HTTPException(404, "recipient MCP session is not registered")
            row = conn.execute(
                """
                INSERT INTO mcp_session_messages(sender_session_id,recipient_session_id,project_key,work_id,delegation_id,message_type,subject,body,payload,expires_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (sender, recipient, _project(args.get("project_key")), work_id, delegation_id, message_type, _safe_text(args.get("subject"), "", 500), body, Jsonb(args.get("payload") or {}), expires_at),
            ).fetchone()
            conn.commit()
        return dict(row) | {"delivery": "durable-inbox"}

    def inbox(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id = _safe_text(args.get("session_id"), "", 200)
        if not session_id:
            raise HTTPException(422, "session_id is required")
        limit = max(1, min(int(args.get("limit", 50)), 200))
        requested_status = args.get("status")
        mark_read = bool(args.get("mark_read", False))
        with self.store.connect() as conn:
            conn.execute("UPDATE mcp_session_messages SET status='expired' WHERE status IN ('queued','delivered') AND expires_at IS NOT NULL AND expires_at < now()")
            if requested_status:
                rows = conn.execute("SELECT * FROM mcp_session_messages WHERE recipient_session_id=%s AND status=%s ORDER BY created_at ASC LIMIT %s", (session_id, requested_status, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM mcp_session_messages WHERE recipient_session_id=%s AND status IN ('queued','delivered','read') ORDER BY created_at ASC LIMIT %s", (session_id, limit)).fetchall()
            ids = [str(row["message_id"]) for row in rows]
            if ids:
                if mark_read:
                    conn.execute("UPDATE mcp_session_messages SET status='read',delivered_at=COALESCE(delivered_at,now()),read_at=COALESCE(read_at,now()) WHERE message_id = ANY(%s::uuid[])", (ids,))
                else:
                    conn.execute("UPDATE mcp_session_messages SET status='delivered',delivered_at=COALESCE(delivered_at,now()) WHERE message_id = ANY(%s::uuid[]) AND status='queued'", (ids,))
            conn.commit()
        return {"session_id": session_id, "messages": [dict(row) for row in rows], "count": len(rows)}

    def acknowledge(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id = _safe_text(args.get("session_id"), "", 200)
        message_id = _uuid(args.get("message_id"), required=True)
        with self.store.connect() as conn:
            row = conn.execute(
                """
                UPDATE mcp_session_messages SET
                  status='acknowledged',
                  delivered_at=COALESCE(delivered_at,now()),
                  read_at=CASE WHEN %s THEN COALESCE(read_at,now()) ELSE read_at END,
                  acknowledged_at=now()
                WHERE message_id=%s AND recipient_session_id=%s
                RETURNING *
                """,
                (bool(args.get("read", True)), message_id, session_id),
            ).fetchone()
            conn.commit()
        if row is None:
            raise HTTPException(404, "message not found for this session")
        return dict(row)

    def _resolve_resource_hints(self, value: Any) -> dict[str, Any]:
        hints = dict(value) if isinstance(value, dict) else {}
        scheduler_keys = {
            "node_id", "backend_node", "role", "backend_role", "service", "backend_service",
            "prefer_gpu", "minimum_memory_gib", "min_memory_gib", "require_backend", "require_live", "live_timeout_seconds", "candidate_limit",
        }
        if not any(key in hints for key in scheduler_keys):
            return hints

        def _truthy(raw: Any) -> bool:
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return bool(raw)

        node_id = _safe_text(hints.get("node_id") or hints.get("backend_node"), "", 200) or None
        role = _safe_text(hints.get("role") or hints.get("backend_role"), "", 200) or None
        service = _safe_text(hints.get("service") or hints.get("backend_service"), "", 200) or None
        prefer_gpu = _truthy(hints.get("prefer_gpu", False))
        require_backend = _truthy(hints.get("require_backend", False))
        require_live = _truthy(hints.get("require_live", False))
        try:
            live_timeout_seconds = max(0.2, min(float(hints.get("live_timeout_seconds") or 2.0), 10.0))
        except (TypeError, ValueError):
            raise HTTPException(422, "resource_hints live_timeout_seconds must be numeric")
        try:
            minimum_memory_gib = max(
                float(hints.get("minimum_memory_gib") or 0.0),
                float(hints.get("min_memory_gib") or 0.0),
                0.0,
            )
        except (TypeError, ValueError):
            raise HTTPException(422, "resource_hints memory floor must be numeric")
        try:
            candidate_limit = max(1, min(int(hints.get("candidate_limit") or 4), 16))
        except (TypeError, ValueError):
            raise HTTPException(422, "resource_hints candidate_limit must be an integer")

        resolved = self.kernel.service_registry.scheduler_candidates(
            node_id=node_id,
            role=role,
            service=service,
            prefer_gpu=prefer_gpu,
            minimum_memory_gib=minimum_memory_gib,
            require_live=require_live,
            live_timeout_seconds=live_timeout_seconds,
            observe_pressure=True,
            pressure_timeout_seconds=min(live_timeout_seconds, 1.5),
            limit=candidate_limit,
        )
        candidates = list(resolved.get("candidates") or [])
        selected = candidates[0] if candidates else None
        registry_report = self.kernel.service_registry.report()
        hints["scheduler"] = {
            "schema_version": "wgrnn-delegation-scheduler-v1",
            "offline_only": True,
            "registry_digest": registry_report.get("registry_digest"),
            "filters": resolved.get("filters") or {},
            "selected": selected,
            "candidate_count": int(resolved.get("count") or 0),
            "excluded": list(resolved.get("excluded") or []),
            "require_backend": require_backend,
            "require_live": require_live,
            "live_observation_digest": ((resolved.get("live_observation") or {}).get("observation_digest") if isinstance(resolved.get("live_observation"), dict) else None),
            "pressure_observation_digest": ((resolved.get("pressure_observation") or {}).get("observation_digest") if isinstance(resolved.get("pressure_observation"), dict) else None),
            "pressure_observed_count": int((resolved.get("pressure_observation") or {}).get("observed_count") or 0) if isinstance(resolved.get("pressure_observation"), dict) else 0,
            "status": "selected" if selected else "no-match",
        }
        if require_backend and selected is None:
            raise HTTPException(422, "no commissioned backend LAN node satisfies required resource_hints")
        return hints

    def assign(self, args: dict[str, Any]) -> dict[str, Any]:
        delegator = _safe_text(args.get("session_id"), "", 200)
        objective = _safe_text(args.get("objective"), "", 20000)
        if not delegator or not objective:
            raise HTTPException(422, "delegator session and objective are required")
        kind = _safe_text(args.get("delegate_kind"), "session", 20)
        if kind not in {"session","wgrnn","worker"}:
            raise HTTPException(422, "invalid delegate_kind")
        delegate_session = _safe_text(args.get("delegate_session_id"), "", 200) or None
        if kind == "wgrnn":
            self.register_wgrnn({})
            delegate_session = self.WGRNN_SESSION_ID
        elif not delegate_session:
            raise HTTPException(422, "delegate_session_id is required for session/worker delegation")
        work_id = _uuid(args.get("work_id")) or str(uuid.uuid4())
        parent_work_id = _uuid(args.get("parent_work_id"))
        capabilities = _clean_array(args.get("required_capabilities"))
        project_key = _project(args.get("project_key"))
        resource_hints = self._resolve_resource_hints(args.get("resource_hints") or {})
        self._ensure_session(delegator, _safe_text(args.get("agent_id"), "agent:mcp", 200), client_name=_safe_text(args.get("client_name"), "mcp-client", 120))
        with self.store.connect() as conn:
            target = conn.execute("SELECT session_id FROM coordination_agent_sessions WHERE session_id=%s", (delegate_session,)).fetchone()
            if target is None:
                raise HTTPException(404, "delegate session is not registered")
            work = conn.execute("SELECT work_id FROM coordination_work_items WHERE work_id=%s", (work_id,)).fetchone()
            if work is None:
                conn.execute(
                    "INSERT INTO coordination_work_items(work_id,project_key,title,objective,status,owner_session_id,parent_work_id,metadata) VALUES (%s,%s,%s,%s,'planned',%s,%s,%s)",
                    (work_id, project_key, _safe_text(args.get("title"), objective[:160], 500), objective, delegate_session, parent_work_id, Jsonb({"delegated": True, "delegate_kind": kind})),
                )
            row = conn.execute(
                """
                INSERT INTO mcp_delegations(work_id,parent_work_id,project_key,delegator_session_id,delegate_session_id,delegate_kind,objective,required_capabilities,resource_hints,acceptance,payload,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'offered') RETURNING *
                """,
                (work_id, parent_work_id, project_key, delegator, delegate_session, kind, objective, capabilities, Jsonb(resource_hints), Jsonb(args.get("acceptance") or {}), Jsonb(args.get("payload") or {})),
            ).fetchone()
            delegation_id = str(row["delegation_id"])
            tool_name = _safe_text(args.get("tool_name"), "", 200)
            if kind == "wgrnn" and tool_name:
                worker = conn.execute("SELECT allowed_tools FROM mcp_worker_registry WHERE worker_id=%s", (self.WGRNN_WORKER_ID,)).fetchone()
                if worker is None or tool_name not in list(worker["allowed_tools"] or []):
                    raise HTTPException(422, f"WG-RNN worker is not allowed to run tool {tool_name}")
                conn.execute("INSERT INTO mcp_delegated_tool_runs(delegation_id,worker_id,tool_name,tool_args,status) VALUES (%s,%s,%s,%s,'queued')", (delegation_id, self.WGRNN_WORKER_ID, tool_name, Jsonb(args.get("tool_args") or {})))
            conn.commit()
        if kind == "session":
            try:
                self.send_message({"session_id": delegator, "recipient_session_id": delegate_session, "project_key": project_key, "work_id": work_id, "delegation_id": delegation_id, "message_type": "request", "subject": "Delegated work", "body": objective, "payload": {"required_capabilities": capabilities, "resource_hints": resource_hints, "acceptance": args.get("acceptance") or {}}})
            except Exception:
                pass
        return dict(row) | {"work_id": work_id}

    def delegation_inbox(self, args: dict[str, Any]) -> dict[str, Any]:
        kind = _safe_text(args.get("delegate_kind"), "session", 20)
        session_id = self.WGRNN_SESSION_ID if kind == "wgrnn" else _safe_text(args.get("session_id"), "", 200)
        if not session_id:
            raise HTTPException(422, "session_id is required")
        limit = max(1, min(int(args.get("limit", 50)), 200))
        status = _safe_text(args.get("status"), "", 20)
        with self.store.connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM mcp_delegations WHERE delegate_session_id=%s AND status=%s ORDER BY updated_at DESC LIMIT %s", (session_id, status, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM mcp_delegations WHERE delegate_session_id=%s AND status IN ('queued','offered','accepted','running','blocked') ORDER BY updated_at DESC LIMIT %s", (session_id, limit)).fetchall()
        return {"session_id": session_id, "delegate_kind": kind, "delegations": [dict(row) for row in rows], "count": len(rows)}

    def update_delegation(self, args: dict[str, Any]) -> dict[str, Any]:
        delegation_id = _uuid(args.get("delegation_id"), required=True)
        status = _safe_text(args.get("status"), "", 20)
        if status not in {"accepted","running","blocked","completed","failed","cancelled","declined"}:
            raise HTTPException(422, "invalid delegation status")
        session_id = _safe_text(args.get("session_id"), "", 200)
        with self.store.connect() as conn:
            existing = conn.execute("SELECT * FROM mcp_delegations WHERE delegation_id=%s", (delegation_id,)).fetchone()
            if existing is None:
                raise HTTPException(404, "delegation not found")
            allowed_actor = session_id in {str(existing["delegator_session_id"]), str(existing["delegate_session_id"])} or session_id == self.WGRNN_SESSION_ID
            if not allowed_actor:
                raise HTTPException(403, "session is not allowed to update this delegation")
            row = conn.execute(
                """
                UPDATE mcp_delegations SET status=%s,result=%s,updated_at=now(),
                  accepted_at=CASE WHEN %s='accepted' THEN COALESCE(accepted_at,now()) ELSE accepted_at END,
                  started_at=CASE WHEN %s='running' THEN COALESCE(started_at,now()) ELSE started_at END,
                  completed_at=CASE WHEN %s IN ('completed','failed','cancelled','declined') THEN COALESCE(completed_at,now()) ELSE completed_at END
                WHERE delegation_id=%s RETURNING *
                """,
                (status, Jsonb(args.get("result") or {}), status, status, status, delegation_id),
            ).fetchone()
            if status in {"completed","failed","cancelled"}:
                work_status = "completed" if status == "completed" else ("cancelled" if status == "cancelled" else "blocked")
                conn.execute("UPDATE coordination_work_items SET status=%s,updated_at=now(),completed_at=CASE WHEN %s='completed' THEN now() ELSE completed_at END WHERE work_id=%s", (work_status, work_status, existing["work_id"]))
            conn.commit()
        return dict(row)

    async def wgrnn_tick(self, args: dict[str, Any]) -> dict[str, Any]:
        self.register_wgrnn({})
        max_tasks = max(1, min(int(args.get("max_tasks", 1)), 8))
        processed: list[dict[str, Any]] = []
        from .http_mcp import _call_tool
        from .delegation_learning import events_for_delegated_run

        def _record_delegated_learning(run_payload: dict[str, Any], ordinal: int) -> dict[str, Any]:
            try:
                specs = events_for_delegated_run(run_payload, ordinal=ordinal)
                recorded = [
                    self.kernel.autonomy.record_event(
                        session_id=self.WGRNN_SESSION_ID,
                        event_type=spec["event_type"],
                        actor=spec["actor"],
                        content=spec["content"],
                        tags=spec["tags"],
                    )
                    for spec in specs
                ]
                built = self.kernel.autonomy.build_trajectory(
                    session_id=self.WGRNN_SESSION_ID,
                    start_sequence=int(recorded[0]["sequence"]),
                    end_sequence=int(recorded[-1]["sequence"]),
                    outcome={
                        "success": run_payload.get("status") == "completed",
                        "score": 1.0 if run_payload.get("status") == "completed" else 0.0,
                        "delegation_status": run_payload.get("status"),
                    },
                    evaluator="wgrnn-delegated-tool",
                    learn=True,
                )
                trajectory = built.get("trajectory", {}) if isinstance(built, dict) else {}
                return {
                    "witnessed": True,
                    "trajectory_id": trajectory.get("trajectory_id"),
                    "experience_digest": specs[-1]["content"].get("experience_digest"),
                }
            except Exception as exc:
                return {"witnessed": False, "error": exc.__class__.__name__}

        def _handoff_delegated_result(run_payload: dict[str, Any], learning: dict[str, Any]) -> dict[str, Any]:
            recipient = _safe_text(run_payload.get("delegator_session_id"), "", 200)
            if not recipient:
                return {"delivery": "missing-delegator"}
            status = _safe_text(run_payload.get("status"), "failed", 20)
            tool_name = _safe_text(run_payload.get("tool_name"), "delegated tool", 200)
            try:
                message = self.send_message({
                    "session_id": self.WGRNN_SESSION_ID,
                    "recipient_session_id": recipient,
                    "project_key": run_payload.get("project_key"),
                    "work_id": run_payload.get("work_id"),
                    "delegation_id": run_payload.get("delegation_id"),
                    "message_type": "result",
                    "subject": f"WG-RNN delegation {status}",
                    "body": f"WG-RNN {status} delegated tool {tool_name}. The complete result remains bound to the delegation/run record.",
                    "payload": {
                        "status": status,
                        "tool_name": tool_name,
                        "run_id": str(run_payload.get("run_id") or ""),
                        "result_digest": run_payload.get("result_digest"),
                        "learning": learning,
                        "scheduler": (run_payload.get("resource_hints") or {}).get("scheduler"),
                    },
                })
                return {"delivery": "durable-inbox", "message_id": str(message.get("message_id") or "")}
            except Exception as exc:
                return {"delivery": "failed", "error": exc.__class__.__name__}

        for _ in range(max_tasks):
            with self.store.connect() as conn:
                run = conn.execute(
                    """
                    SELECT r.*,d.work_id,d.objective,d.project_key,d.delegator_session_id,d.resource_hints
                    FROM mcp_delegated_tool_runs r
                    JOIN mcp_delegations d ON d.delegation_id=r.delegation_id
                    WHERE r.worker_id=%s AND r.status='queued' AND d.status IN ('offered','accepted','running')
                    ORDER BY r.created_at ASC
                    FOR UPDATE SKIP LOCKED LIMIT 1
                    """,
                    (self.WGRNN_WORKER_ID,),
                ).fetchone()
                if run is None:
                    conn.commit()
                    break
                tool_name = str(run["tool_name"])
                if not self._safe_wgrnn_tool(tool_name):
                    conn.execute("UPDATE mcp_delegated_tool_runs SET status='failed',error='tool not allowed',completed_at=now() WHERE run_id=%s", (run["run_id"],))
                    conn.execute("UPDATE mcp_delegations SET status='failed',result=%s,updated_at=now(),completed_at=now() WHERE delegation_id=%s", (Jsonb({"error": "tool not allowed", "tool_name": tool_name}), run["delegation_id"]))
                    conn.commit()
                    continue
                conn.execute("UPDATE mcp_delegated_tool_runs SET status='running',started_at=now() WHERE run_id=%s", (run["run_id"],))
                conn.execute("UPDATE mcp_delegations SET status='running',started_at=COALESCE(started_at,now()),updated_at=now() WHERE delegation_id=%s", (run["delegation_id"],))
                conn.execute("UPDATE mcp_worker_registry SET status='busy',last_seen_at=now() WHERE worker_id=%s", (self.WGRNN_WORKER_ID,))
                conn.commit()
            tool_args = dict(run["tool_args"] or {})
            tool_args["session_id"] = self.WGRNN_SESSION_ID
            tool_args["agent_id"] = "agent:wgrnn"
            tool_args["client_name"] = "WG-RNN"
            try:
                result = await _call_tool(self.kernel, tool_name, tool_args)
                safe_result = json.loads(json.dumps(result, default=str))
                with self.store.connect() as conn:
                    conn.execute("UPDATE mcp_delegated_tool_runs SET status='completed',result=%s,completed_at=now() WHERE run_id=%s", (Jsonb(safe_result), run["run_id"]))
                    conn.execute("UPDATE mcp_delegations SET status='completed',result=%s,updated_at=now(),completed_at=now() WHERE delegation_id=%s", (Jsonb({"tool_name": tool_name, "result": safe_result, "result_digest": _digest(safe_result)}), run["delegation_id"]))
                    conn.execute("UPDATE coordination_work_items SET status='completed',updated_at=now(),completed_at=now() WHERE work_id=%s", (run["work_id"],))
                    conn.execute("UPDATE mcp_worker_registry SET status='idle',last_seen_at=now() WHERE worker_id=%s", (self.WGRNN_WORKER_ID,))
                    conn.commit()
                result_digest = _digest(safe_result)
                completed_payload = {
                    "delegation_id": str(run["delegation_id"]),
                    "run_id": str(run["run_id"]),
                    "work_id": str(run["work_id"]),
                    "project_key": str(run["project_key"]),
                    "objective": str(run["objective"]),
                    "delegator_session_id": str(run["delegator_session_id"]),
                    "resource_hints": dict(run["resource_hints"] or {}),
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "status": "completed",
                    "result": safe_result,
                    "result_digest": result_digest,
                }
                learning = _record_delegated_learning(completed_payload, len(processed) + 1)
                handoff = _handoff_delegated_result(completed_payload, learning)
                processed.append({
                    "delegation_id": str(run["delegation_id"]),
                    "run_id": str(run["run_id"]),
                    "tool_name": tool_name,
                    "status": "completed",
                    "result_digest": result_digest,
                    "learning": learning,
                    "scheduler": (completed_payload.get("resource_hints") or {}).get("scheduler"),
                    "handoff": handoff,
                })
            except Exception as exc:
                with self.store.connect() as conn:
                    conn.execute("UPDATE mcp_delegated_tool_runs SET status='failed',error=%s,completed_at=now() WHERE run_id=%s", (_safe_text(str(exc), "error", 4000), run["run_id"]))
                    conn.execute("UPDATE mcp_delegations SET status='failed',result=%s,updated_at=now(),completed_at=now() WHERE delegation_id=%s", (Jsonb({"error": exc.__class__.__name__, "message": _safe_text(str(exc), "error", 4000)}), run["delegation_id"]))
                    conn.execute("UPDATE mcp_worker_registry SET status='error',last_seen_at=now() WHERE worker_id=%s", (self.WGRNN_WORKER_ID,))
                    conn.commit()
                failed_payload = {
                    "delegation_id": str(run["delegation_id"]),
                    "run_id": str(run["run_id"]),
                    "work_id": str(run["work_id"]),
                    "project_key": str(run["project_key"]),
                    "objective": str(run["objective"]),
                    "delegator_session_id": str(run["delegator_session_id"]),
                    "resource_hints": dict(run["resource_hints"] or {}),
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "status": "failed",
                    "error": f"{exc.__class__.__name__}: {_safe_text(str(exc), 'error', 4000)}",
                }
                learning = _record_delegated_learning(failed_payload, len(processed) + 1)
                handoff = _handoff_delegated_result(failed_payload, learning)
                processed.append({
                    "delegation_id": str(run["delegation_id"]),
                    "run_id": str(run["run_id"]),
                    "tool_name": tool_name,
                    "status": "failed",
                    "error": exc.__class__.__name__,
                    "learning": learning,
                    "scheduler": (failed_payload.get("resource_hints") or {}).get("scheduler"),
                    "handoff": handoff,
                })
        return {"worker_id": self.WGRNN_WORKER_ID, "processed": processed, "count": len(processed)}

    async def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == "session.list":
            return self.list_sessions(args)
        if name == "session.send_message":
            return self.send_message(args)
        if name == "session.inbox":
            return self.inbox(args)
        if name == "session.acknowledge":
            return self.acknowledge(args)
        if name == "delegation.assign":
            return self.assign(args)
        if name == "delegation.inbox":
            return self.delegation_inbox(args)
        if name == "delegation.update":
            return self.update_delegation(args)
        if name == "worker.register_wgrnn":
            return self.register_wgrnn(args)
        if name == "worker.wgrnn_tick":
            return await self.wgrnn_tick(args)
        raise HTTPException(404, f"Unknown session/delegation tool: {name}")
