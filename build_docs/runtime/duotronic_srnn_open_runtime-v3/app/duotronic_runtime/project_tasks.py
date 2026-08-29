from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import HTTPException
from psycopg.types.json import Jsonb


PROJECT_TASK_SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS coordination_tasks (
  task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_key TEXT NOT NULL DEFAULT 'xavi.app-backend',
  task_kind TEXT NOT NULL
    CHECK (task_kind IN ('coding','functionality','ui','context')),
  title TEXT NOT NULL,
  objective TEXT NOT NULL DEFAULT '',
  context JSONB NOT NULL DEFAULT '{}'::jsonb,
  resources TEXT[] NOT NULL DEFAULT '{}'::text[],
  depends_on UUID[] NOT NULL DEFAULT '{}'::uuid[],
  required_capabilities TEXT[] NOT NULL DEFAULT '{}'::text[],
  priority SMALLINT NOT NULL DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),
  status TEXT NOT NULL DEFAULT 'ready'
    CHECK (status IN ('planned','ready','claimed','blocked','completed','cancelled')),
  work_id UUID,
  created_by_session_id TEXT NOT NULL,
  created_by_agent_id TEXT NOT NULL,
  claimed_by_session_id TEXT,
  claimed_by_agent_id TEXT,
  claim_token UUID,
  claimed_at TIMESTAMPTZ,
  lease_expires_at TIMESTAMPTZ,
  blocked_reason TEXT NOT NULL DEFAULT '',
  result JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS coordination_tasks_project_queue_idx
  ON coordination_tasks(project_key, status, priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS coordination_tasks_kind_queue_idx
  ON coordination_tasks(project_key, task_kind, status, priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS coordination_tasks_claim_idx
  ON coordination_tasks(claimed_by_session_id, status, lease_expires_at);
CREATE INDEX IF NOT EXISTS coordination_tasks_work_idx
  ON coordination_tasks(work_id, updated_at DESC);
"""

TASK_KINDS = ('coding', 'functionality', 'ui', 'context')
TASK_STATUSES = ('planned', 'ready', 'claimed', 'blocked', 'completed', 'cancelled')


def _safe_text(value: Any, default: str = '', maximum: int = 20000) -> str:
    text = str(value if value is not None else default).strip()
    return (text or default)[:maximum]


def _clean_array(value: Any, *, maximum: int = 100, item_maximum: int = 1200) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple, set)):
        raise HTTPException(422, 'Expected an array')
    out: list[str] = []
    for item in list(value)[:maximum]:
        text = _safe_text(item, '', item_maximum)
        if text and text not in out:
            out.append(text)
    return out


def _uuid(value: Any, *, required: bool = False) -> str | None:
    text = _safe_text(value, '', 80)
    if not text:
        if required:
            raise HTTPException(422, 'UUID value is required')
        return None
    try:
        return str(uuid.UUID(text))
    except Exception as exc:
        raise HTTPException(422, f'Invalid UUID: {text}') from exc


def _identity(args: dict[str, Any]) -> tuple[str, str]:
    session_id = _safe_text(args.get('session_id'), '', 240)
    agent_id = _safe_text(args.get('agent_id'), '', 240)
    if not session_id or not agent_id:
        raise HTTPException(401, 'Task mutation requires server-injected MCP session identity')
    return session_id, agent_id


def project_task_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            'name': 'task.list',
            'description': 'Read the shared project task backlog, including coding, functionality, UI, and context tasks plus current claims and dependencies.',
            'read_only': True,
            'input_schema': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'default': 'xavi.app-backend'},
                    'status': {'type': ['string', 'null'], 'enum': [*TASK_STATUSES, None]},
                    'task_kind': {'type': ['string', 'null'], 'enum': [*TASK_KINDS, None]},
                    'include_completed': {'type': 'boolean', 'default': True},
                    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 500, 'default': 100},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.create',
            'description': 'Add one structured task to the shared backlog with category, implementation context, resources, dependencies, and acceptance metadata.',
            'read_only': False,
            'input_schema': {
                'type': 'object',
                'required': ['title', 'task_kind'],
                'properties': {
                    'project_key': {'type': 'string', 'default': 'xavi.app-backend'},
                    'title': {'type': 'string'},
                    'task_kind': {'type': 'string', 'enum': list(TASK_KINDS)},
                    'objective': {'type': 'string'},
                    'context': {'type': 'object'},
                    'resources': {'type': 'array', 'items': {'type': 'string'}},
                    'depends_on': {'type': 'array', 'items': {'type': 'string'}},
                    'required_capabilities': {'type': 'array', 'items': {'type': 'string'}},
                    'priority': {'type': 'integer', 'minimum': 0, 'maximum': 100, 'default': 50},
                    'status': {'type': 'string', 'enum': ['planned', 'ready'], 'default': 'ready'},
                    'metadata': {'type': 'object'},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.claim_next',
            'description': 'Atomically claim the highest-priority dependency-ready task no other MCP session owns. Optional WG-RNN selection requires an explicit context.wgrnn_delegation tool contract inside the supplied allowlist. Uses FOR UPDATE SKIP LOCKED and an expiring lease.',
            'read_only': False,
            'input_schema': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'default': 'xavi.app-backend'},
                    'task_kinds': {'type': 'array', 'items': {'type': 'string', 'enum': list(TASK_KINDS)}},
                    'capabilities': {'type': 'array', 'items': {'type': 'string'}},
                    'allowed_tools': {'type': 'array', 'items': {'type': 'string'}},
                    'require_wgrnn_contract': {'type': 'boolean', 'default': False},
                    'lease_seconds': {'type': 'integer', 'minimum': 60, 'maximum': 86400, 'default': 1800},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.renew',
            'description': 'Renew an active task lease owned by the current MCP session.',
            'read_only': False,
            'input_schema': {
                'type': 'object',
                'required': ['task_id', 'claim_token'],
                'properties': {
                    'task_id': {'type': 'string'},
                    'claim_token': {'type': 'string'},
                    'lease_seconds': {'type': 'integer', 'minimum': 60, 'maximum': 86400, 'default': 1800},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.update',
            'description': 'Update a claimed task: block, complete, release back to ready, cancel, or attach its coordination work_id/result.',
            'read_only': False,
            'input_schema': {
                'type': 'object',
                'required': ['task_id', 'claim_token', 'status'],
                'properties': {
                    'task_id': {'type': 'string'},
                    'claim_token': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['ready', 'blocked', 'completed', 'cancelled']},
                    'blocked_reason': {'type': 'string'},
                    'result': {'type': 'object'},
                    'work_id': {'type': ['string', 'null']},
                    'context_patch': {'type': 'object'},
                    'metadata_patch': {'type': 'object'},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.reopen',
            'description': 'Move a planned or blocked task back to ready after its dependency, blocker, or context has changed.',
            'read_only': False,
            'input_schema': {
                'type': 'object',
                'required': ['task_id'],
                'properties': {
                    'task_id': {'type': 'string'},
                    'context_patch': {'type': 'object'},
                    'metadata_patch': {'type': 'object'},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.awareness',
            'description': 'Return a compact live collaboration snapshot so every MCP AI knows active peer sessions, objectives, work, leases, delegations, workers, available tasks, blockers, and where it can help or work independently.',
            'read_only': True,
            'input_schema': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'default': 'xavi.app-backend'},
                    'active_within_seconds': {'type': 'integer', 'minimum': 60, 'maximum': 604800, 'default': 7200},
                    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 200, 'default': 50},
                },
                'additionalProperties': True,
            },
        },
        {
            'name': 'task.recurrent_context',
            'description': 'Return compact structured task documents suitable for coordination-learning/WG-RNN recurrent retrieval on every MCP session.',
            'read_only': True,
            'input_schema': {
                'type': 'object',
                'properties': {
                    'project_key': {'type': 'string', 'default': 'xavi.app-backend'},
                    'include_completed': {'type': 'boolean', 'default': False},
                    'limit': {'type': 'integer', 'minimum': 1, 'maximum': 200, 'default': 50},
                },
                'additionalProperties': True,
            },
        },
    ]


class ProjectTaskService:
    """PostgreSQL-backed collaborative task queue for MCP sessions.

    Task ownership is intentionally separate from resource ownership.  Claiming a
    task stops duplicate effort; the returned `resources` are then fed through the
    normal coordination.preflight/claim lease system before files/services mutate.
    """

    def __init__(self, store: Any) -> None:
        self.store = store

    def migrate(self) -> None:
        with self.store.connect() as conn:
            conn.execute(PROJECT_TASK_SCHEMA_SQL)
            conn.commit()

    def _expire_claims(self, conn: Any, project_key: str) -> int:
        row = conn.execute(
            """
            UPDATE coordination_tasks
               SET status='ready',
                   claimed_by_session_id=NULL,
                   claimed_by_agent_id=NULL,
                   claim_token=NULL,
                   claimed_at=NULL,
                   lease_expires_at=NULL,
                   updated_at=now()
             WHERE project_key=%s
               AND status='claimed'
               AND lease_expires_at IS NOT NULL
               AND lease_expires_at <= now()
            RETURNING task_id
            """,
            (project_key,),
        ).fetchall()
        return len(row)

    def list(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _safe_text(args.get('project_key'), 'xavi.app-backend', 160)
        limit = max(1, min(int(args.get('limit', 100)), 500))
        status = _safe_text(args.get('status'), '', 32) or None
        task_kind = _safe_text(args.get('task_kind'), '', 32) or None
        include_completed = bool(args.get('include_completed', True))
        clauses = ['project_key=%s']
        params: list[Any] = [project_key]
        if status:
            if status not in TASK_STATUSES:
                raise HTTPException(422, 'Invalid task status')
            clauses.append('status=%s')
            params.append(status)
        elif not include_completed:
            clauses.append("status NOT IN ('completed','cancelled')")
        if task_kind:
            if task_kind not in TASK_KINDS:
                raise HTTPException(422, 'Invalid task kind')
            clauses.append('task_kind=%s')
            params.append(task_kind)
        params.append(limit)
        with self.store.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM coordination_tasks
                 WHERE {' AND '.join(clauses)}
                 ORDER BY
                   CASE status WHEN 'claimed' THEN 0 WHEN 'ready' THEN 1 WHEN 'blocked' THEN 2 WHEN 'planned' THEN 3 ELSE 4 END,
                   priority DESC,
                   created_at ASC
                 LIMIT %s
                """,
                tuple(params),
            ).fetchall()
            conn.commit()
        return {'project_key': project_key, 'tasks': rows, 'count': len(rows)}

    def create(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id, agent_id = _identity(args)
        project_key = _safe_text(args.get('project_key'), 'xavi.app-backend', 160)
        title = _safe_text(args.get('title'), '', 300)
        objective = _safe_text(args.get('objective'), '', 20000)
        task_kind = _safe_text(args.get('task_kind'), '', 32).lower()
        status = _safe_text(args.get('status'), 'ready', 32).lower()
        if not title:
            raise HTTPException(422, 'Task title is required')
        if task_kind not in TASK_KINDS:
            raise HTTPException(422, 'Invalid task kind')
        if status not in {'planned', 'ready'}:
            raise HTTPException(422, 'New tasks must be planned or ready')
        depends_on = [_uuid(value, required=True) for value in _clean_array(args.get('depends_on'), maximum=100, item_maximum=80)]
        priority = max(0, min(int(args.get('priority', 50)), 100))
        with self.store.connect() as conn:
            if depends_on:
                found = conn.execute(
                    'SELECT task_id::text FROM coordination_tasks WHERE project_key=%s AND task_id = ANY(%s::uuid[])',
                    (project_key, depends_on),
                ).fetchall()
                found_ids = {str(row['task_id']) for row in found}
                missing = [value for value in depends_on if value not in found_ids]
                if missing:
                    raise HTTPException(409, {'message': 'Task dependencies do not exist in this project', 'missing': missing})
            row = conn.execute(
                """
                INSERT INTO coordination_tasks
                  (project_key, task_kind, title, objective, context, resources, depends_on,
                   required_capabilities, priority, status, created_by_session_id,
                   created_by_agent_id, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s::uuid[],%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    project_key,
                    task_kind,
                    title,
                    objective,
                    Jsonb(dict(args.get('context') or {})),
                    _clean_array(args.get('resources')),
                    depends_on,
                    _clean_array(args.get('required_capabilities'), maximum=64, item_maximum=160),
                    priority,
                    status,
                    session_id,
                    agent_id,
                    Jsonb(dict(args.get('metadata') or {})),
                ),
            ).fetchone()
            conn.commit()
        return {'task': row, 'event': self.event_document('created', row)}

    def claim_next(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id, agent_id = _identity(args)
        project_key = _safe_text(args.get('project_key'), 'xavi.app-backend', 160)
        requested_kinds = _clean_array(args.get('task_kinds'), maximum=4, item_maximum=32) or list(TASK_KINDS)
        invalid_kinds = [value for value in requested_kinds if value not in TASK_KINDS]
        if invalid_kinds:
            raise HTTPException(422, {'message': 'Invalid task kinds', 'values': invalid_kinds})
        capabilities = _clean_array(args.get('capabilities'), maximum=64, item_maximum=160)
        allowed_tools = _clean_array(args.get('allowed_tools'), maximum=128, item_maximum=200)
        require_wgrnn_contract = bool(args.get('require_wgrnn_contract', False))
        lease_seconds = max(60, min(int(args.get('lease_seconds', 1800)), 86400))
        token = str(uuid.uuid4())
        with self.store.connect() as conn:
            expired = self._expire_claims(conn, project_key)
            if require_wgrnn_contract and not allowed_tools:
                conn.commit()
                return {
                    'task': None,
                    'expired_claims_requeued': expired,
                    'reason': 'wgrnn_allowlist_empty',
                    'selector': {'require_wgrnn_contract': True, 'allowed_tool_count': 0},
                }
            row = conn.execute(
                """
                SELECT t.*
                  FROM coordination_tasks t
                 WHERE t.project_key=%s
                   AND t.status='ready'
                   AND t.task_kind = ANY(%s::text[])
                   AND (cardinality(t.required_capabilities)=0 OR t.required_capabilities <@ %s::text[])
                   AND (
                     %s = false OR (
                       jsonb_typeof(t.context->'wgrnn_delegation')='object'
                       AND COALESCE(t.context->'wgrnn_delegation'->>'tool_name','') <> ''
                       AND (t.context->'wgrnn_delegation'->>'tool_name') = ANY(%s::text[])
                     )
                   )
                   AND NOT EXISTS (
                     SELECT 1
                       FROM unnest(t.depends_on) AS dep(task_id)
                       LEFT JOIN coordination_tasks d ON d.task_id=dep.task_id
                      WHERE d.task_id IS NULL OR d.status <> 'completed'
                   )
                 ORDER BY t.priority DESC, t.created_at ASC
                 FOR UPDATE SKIP LOCKED
                 LIMIT 1
                """,
                (project_key, requested_kinds, capabilities, require_wgrnn_contract, allowed_tools),
            ).fetchone()
            if row is None:
                conn.commit()
                return {'task': None, 'expired_claims_requeued': expired}
            claimed = conn.execute(
                """
                UPDATE coordination_tasks
                   SET status='claimed',
                       claimed_by_session_id=%s,
                       claimed_by_agent_id=%s,
                       claim_token=%s::uuid,
                       claimed_at=now(),
                       lease_expires_at=now() + (%s * interval '1 second'),
                       blocked_reason='',
                       updated_at=now()
                 WHERE task_id=%s
                RETURNING *
                """,
                (session_id, agent_id, token, lease_seconds, row['task_id']),
            ).fetchone()
            conn.commit()
        return {
            'task': claimed,
            'claim_token': token,
            'expired_claims_requeued': expired,
            'next_step': 'Run normal coordination.preflight/claim for the returned resources before mutating them.',
            'selector': {
                'require_wgrnn_contract': require_wgrnn_contract,
                'allowed_tool_count': len(allowed_tools),
            },
            'event': self.event_document('claimed', claimed),
        }

    def renew(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id, agent_id = _identity(args)
        task_id = _uuid(args.get('task_id'), required=True)
        claim_token = _uuid(args.get('claim_token'), required=True)
        lease_seconds = max(60, min(int(args.get('lease_seconds', 1800)), 86400))
        with self.store.connect() as conn:
            row = conn.execute(
                """
                UPDATE coordination_tasks
                   SET lease_expires_at=now() + (%s * interval '1 second'), updated_at=now()
                 WHERE task_id=%s::uuid
                   AND status='claimed'
                   AND claimed_by_session_id=%s
                   AND claimed_by_agent_id=%s
                   AND claim_token=%s::uuid
                   AND lease_expires_at > now()
                RETURNING *
                """,
                (lease_seconds, task_id, session_id, agent_id, claim_token),
            ).fetchone()
            if row is None:
                raise HTTPException(409, 'Task lease is missing, expired, or owned by another MCP session')
            conn.commit()
        return {'task': row, 'event': self.event_document('renewed', row)}

    def update(self, args: dict[str, Any]) -> dict[str, Any]:
        session_id, agent_id = _identity(args)
        task_id = _uuid(args.get('task_id'), required=True)
        claim_token = _uuid(args.get('claim_token'), required=True)
        new_status = _safe_text(args.get('status'), '', 32).lower()
        if new_status not in {'ready', 'blocked', 'completed', 'cancelled'}:
            raise HTTPException(422, 'Invalid task transition')
        work_id = _uuid(args.get('work_id'))
        blocked_reason = _safe_text(args.get('blocked_reason'), '', 12000)
        context_patch = dict(args.get('context_patch') or {})
        metadata_patch = dict(args.get('metadata_patch') or {})
        result = dict(args.get('result') or {})
        with self.store.connect() as conn:
            current = conn.execute(
                """
                SELECT * FROM coordination_tasks
                 WHERE task_id=%s::uuid
                   AND status='claimed'
                   AND claimed_by_session_id=%s
                   AND claimed_by_agent_id=%s
                   AND claim_token=%s::uuid
                   AND lease_expires_at > now()
                 FOR UPDATE
                """,
                (task_id, session_id, agent_id, claim_token),
            ).fetchone()
            if current is None:
                raise HTTPException(409, 'Task lease is missing, expired, or owned by another MCP session')
            row = conn.execute(
                """
                UPDATE coordination_tasks
                   SET status=%s,
                       work_id=COALESCE(%s::uuid, work_id),
                       context=context || %s::jsonb,
                       metadata=metadata || %s::jsonb,
                       blocked_reason=%s,
                       result=%s,
                       claimed_by_session_id=NULL,
                       claimed_by_agent_id=NULL,
                       claim_token=NULL,
                       claimed_at=NULL,
                       lease_expires_at=NULL,
                       completed_at=CASE WHEN %s='completed' THEN now() ELSE completed_at END,
                       updated_at=now()
                 WHERE task_id=%s::uuid
                RETURNING *
                """,
                (
                    new_status,
                    work_id,
                    json.dumps(context_patch),
                    json.dumps(metadata_patch),
                    blocked_reason if new_status == 'blocked' else '',
                    Jsonb(result),
                    new_status,
                    task_id,
                ),
            ).fetchone()
            conn.commit()
        return {'task': row, 'event': self.event_document(new_status, row)}

    def reopen(self, args: dict[str, Any]) -> dict[str, Any]:
        _identity(args)
        task_id = _uuid(args.get('task_id'), required=True)
        context_patch = dict(args.get('context_patch') or {})
        metadata_patch = dict(args.get('metadata_patch') or {})
        with self.store.connect() as conn:
            row = conn.execute(
                """
                UPDATE coordination_tasks
                   SET status='ready',
                       context=context || %s::jsonb,
                       metadata=metadata || %s::jsonb,
                       blocked_reason='',
                       claimed_by_session_id=NULL,
                       claimed_by_agent_id=NULL,
                       claim_token=NULL,
                       claimed_at=NULL,
                       lease_expires_at=NULL,
                       updated_at=now()
                 WHERE task_id=%s::uuid
                   AND status IN ('planned','blocked')
                RETURNING *
                """,
                (json.dumps(context_patch), json.dumps(metadata_patch), task_id),
            ).fetchone()
            if row is None:
                raise HTTPException(409, 'Only planned or blocked tasks can be reopened')
            conn.commit()
        return {'task': row, 'event': self.event_document('reopened', row)}

    def awareness(self, args: dict[str, Any]) -> dict[str, Any]:
        project_key = _safe_text(args.get('project_key'), 'xavi.app-backend', 160)
        active_within = max(60, min(int(args.get('active_within_seconds', 7200)), 604800))
        limit = max(1, min(int(args.get('limit', 50)), 200))
        current_session = _safe_text(args.get('session_id'), '', 240) or None
        with self.store.connect() as conn:
            sessions = conn.execute(
                """
                SELECT session_id, agent_id, client_name, status, metadata, last_seen_at
                  FROM coordination_agent_sessions
                 WHERE status IN ('active','idle')
                   AND last_seen_at >= now() - (%s * interval '1 second')
                 ORDER BY last_seen_at DESC
                 LIMIT %s
                """,
                (active_within, limit),
            ).fetchall()
            observed_sessions = conn.execute(
                """
                SELECT session_id,
                       max(created_at_ms) AS last_seen_ms,
                       count(*) AS event_count,
                       (array_agg(actor ORDER BY sequence DESC))[1] AS latest_actor,
                       (array_agg(event_type ORDER BY sequence DESC))[1] AS latest_event_type
                  FROM session_transcript_events
                 WHERE created_at_ms >= ((EXTRACT(EPOCH FROM now()) * 1000)::bigint - (%s * 1000))
                 GROUP BY session_id
                 ORDER BY last_seen_ms DESC
                 LIMIT %s
                """,
                (active_within, limit),
            ).fetchall()
            work = conn.execute(
                """
                SELECT w.work_id, w.project_key, w.title, w.objective, w.plan, w.status, w.priority,
                       w.owner_session_id, w.parent_work_id, w.metadata, w.updated_at,
                       s.last_seen_at AS owner_last_seen_at
                  FROM coordination_work_items w
                  JOIN coordination_agent_sessions s ON s.session_id=w.owner_session_id
                 WHERE w.status IN ('planned','active','blocked')
                   AND s.status IN ('active','idle')
                   AND s.last_seen_at >= now() - (%s * interval '1 second')
                 ORDER BY CASE WHEN w.project_key=%s THEN 0 ELSE 1 END,
                          w.priority DESC, w.updated_at DESC
                 LIMIT %s
                """,
                (active_within, project_key, limit),
            ).fetchall()
            claims = conn.execute(
                """
                SELECT claim_id, work_id, project_key, session_id, agent_id, resource_key,
                       resource_kind, mode, purpose, expires_at
                  FROM coordination_resource_claims
                 WHERE status='active' AND expires_at > now()
                 ORDER BY CASE WHEN project_key=%s THEN 0 ELSE 1 END, expires_at ASC
                 LIMIT %s
                """,
                (project_key, limit * 2),
            ).fetchall()
            tasks = conn.execute(
                """
                SELECT t.task_id, t.project_key, t.task_kind, t.title, t.objective, t.context, t.resources,
                       t.depends_on, t.required_capabilities, t.priority, t.status, t.work_id,
                       t.created_by_session_id, t.claimed_by_session_id, t.claimed_by_agent_id,
                       t.lease_expires_at, t.blocked_reason, t.result, t.metadata, t.updated_at,
                       NOT EXISTS (
                         SELECT 1
                           FROM unnest(t.depends_on) AS dep(task_id)
                           LEFT JOIN coordination_tasks d ON d.task_id=dep.task_id
                          WHERE d.task_id IS NULL OR d.status <> 'completed'
                       ) AS dependencies_ready
                  FROM coordination_tasks t
                 WHERE t.status NOT IN ('completed','cancelled')
                 ORDER BY CASE WHEN t.project_key=%s THEN 0 ELSE 1 END,
                          CASE t.status WHEN 'claimed' THEN 0 WHEN 'ready' THEN 1 WHEN 'blocked' THEN 2 ELSE 3 END,
                          t.priority DESC, t.updated_at DESC
                 LIMIT %s
                """,
                (project_key, limit * 2),
            ).fetchall()
            delegations = conn.execute(
                """
                SELECT delegation_id, work_id, parent_work_id, project_key, delegator_session_id,
                       delegate_session_id, delegate_kind, objective, required_capabilities,
                       resource_hints, acceptance, status, result, updated_at
                  FROM mcp_delegations
                 WHERE status IN ('queued','offered','accepted','running','blocked')
                 ORDER BY CASE WHEN project_key=%s THEN 0 ELSE 1 END, updated_at DESC
                 LIMIT %s
                """,
                (project_key, limit),
            ).fetchall()
            messages = conn.execute(
                """
                SELECT message_id, sender_session_id, recipient_session_id, project_key, work_id,
                       delegation_id, message_type, subject, left(body, 4000) AS body,
                       status, created_at, delivered_at, read_at, acknowledged_at
                  FROM mcp_session_messages
                 WHERE project_key=%s
                   AND created_at >= now() - (%s * interval '1 second')
                 ORDER BY created_at DESC
                 LIMIT %s
                """,
                (project_key, active_within, limit),
            ).fetchall()
            workers = conn.execute(
                """
                SELECT worker_id, session_id, worker_kind, status, capabilities, allowed_tools,
                       resource_profile, metadata, last_seen_at
                  FROM mcp_worker_registry
                 WHERE status IN ('active','idle','busy')
                   AND last_seen_at >= now() - (%s * interval '1 second')
                 ORDER BY last_seen_at DESC
                 LIMIT %s
                """,
                (active_within, limit),
            ).fetchall()
            events = conn.execute(
                """
                SELECT event_id, project_key, work_id, session_id, agent_id, event_type,
                       summary, resource_keys, payload, created_at
                  FROM coordination_events
                 ORDER BY created_at DESC
                 LIMIT %s
                """,
                (limit,),
            ).fetchall()

        my_work = [row for row in work if current_session and row.get('owner_session_id') == current_session]
        peer_work = [row for row in work if not current_session or row.get('owner_session_id') != current_session]
        my_claims = [row for row in claims if current_session and row.get('session_id') == current_session]
        peer_claims = [row for row in claims if not current_session or row.get('session_id') != current_session]
        available_tasks = [row for row in tasks if row.get('status') == 'ready' and bool(row.get('dependencies_ready'))]
        addressed_delegations = [
            row for row in delegations
            if current_session
            and row.get('delegate_session_id') == current_session
            and row.get('status') in {'offered', 'accepted', 'running'}
        ]
        help_candidates = [row for row in peer_work if row.get('status') == 'blocked']
        if not help_candidates:
            help_candidates = [row for row in peer_work if row.get('status') == 'active'][:5]

        action_hints: list[dict[str, Any]] = []
        for row in addressed_delegations[:5]:
            action_hints.append({
                'action': 'handle_delegation',
                'delegation_id': str(row.get('delegation_id')),
                'work_id': str(row.get('work_id')) if row.get('work_id') else None,
                'delegator_session_id': row.get('delegator_session_id'),
                'objective': row.get('objective'),
                'resource_hints': dict(row.get('resource_hints') or {}),
                'acceptance': dict(row.get('acceptance') or {}),
                'reason': 'This delegation is addressed to the current MCP session; continue or report it before seeking unrelated work.',
            })
        if help_candidates:
            for row in help_candidates[:3]:
                action_hints.append({
                    'action': 'coordinate_or_help',
                    'work_id': str(row.get('work_id')),
                    'owner_session_id': row.get('owner_session_id'),
                    'title': row.get('title'),
                    'reason': 'Peer work is blocked or active; inspect context, send the owner any useful hint, and avoid only the exact file/service they are actively mutating. Parallel work on adjacent resources is encouraged.',
                })
        for row in available_tasks[:5]:
            action_hints.append({
                'action': 'claim_task',
                'task_id': str(row.get('task_id')),
                'project_key': row.get('project_key'),
                'task_kind': row.get('task_kind'),
                'title': row.get('title'),
                'resources': list(row.get('resources') or []),
                'reason': 'Task is ready, dependency-complete, and currently unclaimed.',
            })
        if not available_tasks and not addressed_delegations:
            action_hints.append({
                'action': 'create_or_discover_task',
                'reason': 'No dependency-ready unclaimed task or addressed delegation is currently visible; inspect peer context, another project, or create a backlog item before implementation.',
            })

        peer_lines = [
            f"{row.get('agent_id')} session={row.get('session_id')} status={row.get('status')} last_seen={row.get('last_seen_at')}"
            for row in sessions
            if not current_session or row.get('session_id') != current_session
        ][:10]
        known_session_ids = {str(row.get('session_id')) for row in sessions}
        observed_lines = [
            f"{row.get('latest_actor')} session={row.get('session_id')} event={row.get('latest_event_type')} events={row.get('event_count')} last_seen_ms={row.get('last_seen_ms')}"
            for row in observed_sessions
            if str(row.get('session_id')) not in known_session_ids
            and (not current_session or row.get('session_id') != current_session)
        ][:10]
        work_lines = [
            f"{row.get('status')} work={row.get('work_id')} owner={row.get('owner_session_id')} title={row.get('title')} objective={row.get('objective')}"
            for row in peer_work[:10]
        ]
        task_lines = [
            f"{row.get('status')} task={row.get('task_id')} kind={row.get('task_kind')} priority={row.get('priority')} title={row.get('title')}"
            for row in tasks[:12]
        ]
        awareness_text = '\n'.join([
            f"Shared MCP awareness for {project_key}",
            'Active coordination peers:',
            *(peer_lines or ['none visible']),
            'Other recently observed MCP sessions:',
            *(observed_lines or ['none visible']),
            'Peer work:',
            *(work_lines or ['none visible']),
            'Task backlog:',
            *(task_lines or ['none visible']),
        ])
        return {
            'schema': 'xavi-mcp-peer-awareness/v1',
            'project_key': project_key,
            'current_session_id': current_session,
            'active_sessions': sessions,
            'observed_session_activity': observed_sessions,
            'my_work': my_work,
            'peer_work': peer_work,
            'my_resource_claims': my_claims,
            'peer_resource_claims': peer_claims,
            'tasks': tasks,
            'available_tasks': available_tasks,
            'delegations': delegations,
            'recent_session_messages': messages,
            'workers': workers,
            'recent_events': events,
            'action_hints': action_hints,
            'awareness_text': awareness_text,
            'integration_hint': 'Inject this compact snapshot into coordination.begin/preflight and MCP result context so every AI sees peer activity before choosing work.',
        }

    def compact_awareness(self, args: dict[str, Any]) -> dict[str, Any]:
        payload = self.awareness({**dict(args or {}), 'limit': min(int((args or {}).get('limit', 12)), 20)})
        current_session = payload.get('current_session_id')
        return {
            'schema': 'xavi-mcp-peer-awareness-compact/v1',
            'project_key': payload.get('project_key'),
            'current_session_id': current_session,
            'active_peers': [
                row for row in payload.get('active_sessions', [])
                if not current_session or row.get('session_id') != current_session
            ][:8],
            'observed_sessions': [
                row for row in payload.get('observed_session_activity', [])
                if not current_session or row.get('session_id') != current_session
            ][:8],
            'peer_work': payload.get('peer_work', [])[:8],
            'peer_resource_claims': payload.get('peer_resource_claims', [])[:12],
            'available_tasks': payload.get('available_tasks', [])[:8],
            'delegations': payload.get('delegations', [])[:8],
            'workers': payload.get('workers', [])[:8],
            'recent_session_messages': payload.get('recent_session_messages', [])[:6],
            'action_hints': payload.get('action_hints', [])[:8],
            'awareness_text': payload.get('awareness_text', ''),
        }

    def recurrent_context(self, args: dict[str, Any]) -> dict[str, Any]:
        listing = self.list({
            'project_key': args.get('project_key'),
            'include_completed': bool(args.get('include_completed', False)),
            'limit': args.get('limit', 50),
        })
        docs = [self.recurrent_document(task) for task in listing['tasks']]
        return {
            'schema': 'xavi-shared-task-context/v1',
            'project_key': listing['project_key'],
            'documents': docs,
            'count': len(docs),
        }

    @staticmethod
    def recurrent_document(task: dict[str, Any]) -> dict[str, Any]:
        context = task.get('context') or {}
        result = task.get('result') or {}
        resources = list(task.get('resources') or [])
        dependencies = [str(value) for value in task.get('depends_on') or []]
        text = '\n'.join([
            f"Task: {task.get('title')}",
            f"Task ID: {task.get('task_id')}",
            f"Project: {task.get('project_key')}",
            f"Kind: {task.get('task_kind')} | Status: {task.get('status')} | Priority: {task.get('priority')}",
            f"Objective: {task.get('objective') or ''}",
            f"Resources: {', '.join(resources)}",
            f"Dependencies: {', '.join(dependencies)}",
            f"Claimed by: {task.get('claimed_by_agent_id') or ''}/{task.get('claimed_by_session_id') or ''}",
            f"Context: {json.dumps(context, sort_keys=True, default=str)}",
            f"Result: {json.dumps(result, sort_keys=True, default=str)}",
        ])
        return {
            'task_id': str(task.get('task_id')),
            'project_key': task.get('project_key'),
            'task_kind': task.get('task_kind'),
            'status': task.get('status'),
            'priority': task.get('priority'),
            'tags': [
                'shared-task-board',
                f"task-kind:{task.get('task_kind')}",
                f"task-status:{task.get('status')}",
            ],
            'resources': resources,
            'text': text,
        }

    @classmethod
    def event_document(cls, action: str, task: dict[str, Any]) -> dict[str, Any]:
        doc = cls.recurrent_document(task)
        return {
            'event_type': f"task.{action}",
            'summary': f"{action}: {task.get('title')}",
            'project_key': task.get('project_key'),
            'work_id': str(task.get('work_id')) if task.get('work_id') else None,
            'resources': doc['resources'],
            'payload': {
                'task_id': doc['task_id'],
                'task_kind': doc['task_kind'],
                'task_status': doc['status'],
                'priority': doc['priority'],
                'recurrent_document': doc,
            },
        }

    def dispatch(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if name == 'task.list':
            return self.list(args)
        if name == 'task.create':
            return self.create(args)
        if name == 'task.claim_next':
            return self.claim_next(args)
        if name == 'task.renew':
            return self.renew(args)
        if name == 'task.update':
            return self.update(args)
        if name == 'task.reopen':
            return self.reopen(args)
        if name == 'task.awareness':
            return self.awareness(args)
        if name == 'task.recurrent_context':
            return self.recurrent_context(args)
        raise HTTPException(404, f'Unknown project task tool: {name}')
