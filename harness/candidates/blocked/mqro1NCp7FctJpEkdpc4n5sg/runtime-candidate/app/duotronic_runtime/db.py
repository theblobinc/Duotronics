from __future__ import annotations

import json
import re
from typing import Any, Iterable

import psycopg
from psycopg.rows import dict_row

from .config import Settings

SCHEMA_SQL = r"""
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS model_registry (
  model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  provider TEXT NOT NULL,
  model TEXT,
  base_url TEXT,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS runtime_runs (
  run_id TEXT PRIMARY KEY,
  loop_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  prompt TEXT NOT NULL,
  response_text TEXT NOT NULL,
  requested_action TEXT NOT NULL,
  model JSONB NOT NULL,
  policy_decision JSONB NOT NULL,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS wgrnn_memory_updates (
  update_id TEXT PRIMARY KEY,
  run_id TEXT REFERENCES runtime_runs(run_id) ON DELETE SET NULL,
  loop_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  slot_id INTEGER NOT NULL,
  update_kind TEXT NOT NULL CHECK (update_kind IN ('candidate_write','quarantine_write','promote','noop')),
  trust_status TEXT NOT NULL CHECK (trust_status IN ('candidate','quarantine','promoted','rejected')),
  authority_t DOUBLE PRECISION NOT NULL CHECK (authority_t >= 0 AND authority_t <= 1),
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  contradiction DOUBLE PRECISION NOT NULL CHECK (contradiction >= 0 AND contradiction <= 1),
  affected_slot_ids JSONB NOT NULL,
  replay_identity_ref TEXT NOT NULL,
  state_digest TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS nla_activation_witnesses (
  witness_id TEXT PRIMARY KEY,
  run_id TEXT REFERENCES runtime_runs(run_id) ON DELETE SET NULL,
  loop_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  wg_rnn_update_id TEXT REFERENCES wgrnn_memory_updates(update_id) ON DELETE SET NULL,
  source_model JSONB NOT NULL,
  activation JSONB NOT NULL,
  verbalizer JSONB NOT NULL,
  reconstructor JSONB NOT NULL,
  fidelity JSONB NOT NULL,
  lifecycle JSONB NOT NULL,
  policy JSONB NOT NULL,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memory_cells (
  cell_id TEXT PRIMARY KEY,
  loop_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  slot_id INTEGER NOT NULL,
  state_digest TEXT NOT NULL,
  trust_status TEXT NOT NULL,
  authority_t DOUBLE PRECISION NOT NULL,
  latest_update_id TEXT REFERENCES wgrnn_memory_updates(update_id) ON DELETE SET NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(loop_id, node_id, slot_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'info',
  run_id TEXT,
  witness_id TEXT,
  update_id TEXT,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corpus_documents (
  doc_id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  title TEXT NOT NULL,
  digest TEXT NOT NULL,
  headings JSONB NOT NULL DEFAULT '[]'::jsonb,
  excerpt TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corpus_versions (
  corpus_id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  digest TEXT NOT NULL,
  manifest_ref TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','active','retired','rejected')),
  manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
  validation JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  activated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS evidence_claims (
  claim_id TEXT PRIMARY KEY,
  claim_digest TEXT NOT NULL,
  claim_kind TEXT NOT NULL,
  claim_status TEXT NOT NULL,
  epistemic_status TEXT NOT NULL,
  force TEXT NOT NULL,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object JSONB NOT NULL,
  support JSONB NOT NULL DEFAULT '[]'::jsonb,
  corpus JSONB NOT NULL DEFAULT '{}'::jsonb,
  payload JSONB NOT NULL,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_witnesses (
  witness_id TEXT PRIMARY KEY,
  witness_type TEXT NOT NULL,
  force TEXT NOT NULL,
  observer_id TEXT NOT NULL,
  status TEXT NOT NULL,
  corpus JSONB NOT NULL DEFAULT '{}'::jsonb,
  payload_digest TEXT NOT NULL,
  payload JSONB NOT NULL,
  run_id TEXT REFERENCES runtime_runs(run_id) ON DELETE SET NULL,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS module_invocations (
  invocation_id TEXT PRIMARY KEY,
  module_id TEXT NOT NULL,
  module_kind TEXT NOT NULL,
  status TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  output_digest TEXT,
  witness_id TEXT REFERENCES evidence_witnesses(witness_id) ON DELETE SET NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evidence_claims_subject_idx ON evidence_claims(subject);
CREATE INDEX IF NOT EXISTS evidence_witnesses_type_idx ON evidence_witnesses(witness_type);
CREATE INDEX IF NOT EXISTS evidence_witnesses_run_idx ON evidence_witnesses(run_id);

CREATE TABLE IF NOT EXISTS observer_claim_observations (
  observation_id TEXT PRIMARY KEY,
  claim_key TEXT NOT NULL,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object JSONB NOT NULL,
  observer_id TEXT NOT NULL,
  observer_kind TEXT NOT NULL,
  independence_group TEXT NOT NULL,
  stance TEXT NOT NULL CHECK (stance IN ('support','contradict','uncertain')),
  confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  source_ref TEXT,
  evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS observer_claim_key_idx ON observer_claim_observations(claim_key, created_at_ms DESC);
CREATE INDEX IF NOT EXISTS observer_claim_observer_idx ON observer_claim_observations(observer_id, created_at_ms DESC);
CREATE INDEX IF NOT EXISTS observer_claim_group_idx ON observer_claim_observations(independence_group, created_at_ms DESC);

CREATE TABLE IF NOT EXISTS claim_consensus (
  claim_key TEXT PRIMARY KEY,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object JSONB NOT NULL,
  support_weight DOUBLE PRECISION NOT NULL DEFAULT 0,
  contradiction_weight DOUBLE PRECISION NOT NULL DEFAULT 0,
  uncertain_weight DOUBLE PRECISION NOT NULL DEFAULT 0,
  support_ratio DOUBLE PRECISION NOT NULL DEFAULT 0,
  contradiction_ratio DOUBLE PRECISION NOT NULL DEFAULT 0,
  independent_observers INTEGER NOT NULL DEFAULT 0,
  independent_groups INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'insufficient_observers',
  promotion_recommended BOOLEAN NOT NULL DEFAULT FALSE,
  observer_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  evaluated_at_ms BIGINT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS claim_consensus_status_idx ON claim_consensus(status, promotion_recommended);


CREATE TABLE IF NOT EXISTS session_transcript_events (
  session_id TEXT NOT NULL,
  sequence BIGINT NOT NULL,
  event_digest TEXT NOT NULL UNIQUE,
  previous_event_digest TEXT,
  content_digest TEXT NOT NULL,
  event_type TEXT NOT NULL,
  actor TEXT NOT NULL,
  created_at_ms BIGINT NOT NULL,
  witness_id TEXT,
  supersedes JSONB NOT NULL DEFAULT '[]'::jsonb,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  content JSONB NOT NULL DEFAULT '{}'::jsonb,
  training_eligible BOOLEAN NOT NULL DEFAULT TRUE,
  redaction JSONB NOT NULL DEFAULT '{}'::jsonb,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (session_id, sequence)
);

CREATE INDEX IF NOT EXISTS session_transcript_created_idx ON session_transcript_events(created_at_ms DESC);
CREATE INDEX IF NOT EXISTS session_transcript_type_idx ON session_transcript_events(event_type);
CREATE INDEX IF NOT EXISTS session_transcript_actor_idx ON session_transcript_events(actor);
CREATE INDEX IF NOT EXISTS session_transcript_tags_gin ON session_transcript_events USING GIN(tags);
CREATE INDEX IF NOT EXISTS session_transcript_content_gin ON session_transcript_events USING GIN(content);

CREATE TABLE IF NOT EXISTS source_index_generations (
  generation_id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  root_path TEXT,
  commit_id TEXT,
  status TEXT NOT NULL CHECK (status IN ('staging','completed','failed','superseded')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  document_count BIGINT NOT NULL DEFAULT 0,
  byte_count BIGINT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS source_documents (
  repository_id TEXT NOT NULL,
  generation_id TEXT NOT NULL REFERENCES source_index_generations(generation_id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  language TEXT,
  content_digest TEXT NOT NULL,
  source_digest TEXT,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  training_eligible BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(repository_id,'') || ' ' || coalesce(path,'') || ' ' || coalesce(content,''))
  ) STORED,
  PRIMARY KEY (repository_id, generation_id, path, chunk_index)
);

CREATE INDEX IF NOT EXISTS source_generations_repo_status_idx ON source_index_generations(repository_id, status, completed_at DESC);
CREATE INDEX IF NOT EXISTS source_documents_search_gin ON source_documents USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS source_documents_path_idx ON source_documents(repository_id, path);
"""


class Store:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pool: psycopg.ConnectionPool | None = None

    def _get_pool(self) -> psycopg.ConnectionPool:
        if self._pool is None:
            from psycopg_pool import ConnectionPool
            self._pool = ConnectionPool(self.settings.database_url, kwargs={"row_factory": dict_row}, min_size=1, max_size=10, open=True)
        return self._pool

    def connect(self):
        try:
            return self._get_pool().connection()
        except Exception:
            return psycopg.connect(self.settings.database_url, row_factory=dict_row)

    def migrate(self) -> None:
        from .coordination import COORDINATION_SCHEMA_SQL
        from .session_delegation import SESSION_DELEGATION_SCHEMA_SQL
        from .project_tasks import PROJECT_TASK_SCHEMA_SQL
        from .corpus_index import CORPUS_INDEX_SCHEMA_SQL

        with self.connect() as conn:
            conn.execute(SCHEMA_SQL)
            conn.execute(COORDINATION_SCHEMA_SQL)
            conn.execute(SESSION_DELEGATION_SCHEMA_SQL)
            conn.execute(PROJECT_TASK_SCHEMA_SQL)
            conn.execute(CORPUS_INDEX_SCHEMA_SQL)
            conn.commit()

    def insert_run_bundle(self, result: dict[str, Any], extra_witnesses: list[dict[str, Any]] | None = None) -> None:
        run_id = result["run_id"]
        wg_update = result["wg_rnn"]["memory_update"]
        nla = result["nla_witness"]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_runs (run_id, loop_id, node_id, prompt, response_text, requested_action, model, policy_decision, created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (run_id) DO NOTHING
                """,
                (run_id, result["loop_id"], result["node_id"], result["prompt"], result["response_text"], result["requested_action"], json.dumps(result["model"]), json.dumps(result["policy_decision"]), result["created_at_ms"]),
            )
            conn.execute(
                """
                INSERT INTO wgrnn_memory_updates
                (update_id, run_id, loop_id, node_id, slot_id, update_kind, trust_status, authority_t, confidence, contradiction, affected_slot_ids, replay_identity_ref, state_digest, payload, created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (update_id) DO NOTHING
                """,
                (
                    wg_update["update_id"], run_id, wg_update["loop_id"], wg_update["node_id"], wg_update["slot_id"], wg_update["update_kind"], wg_update["trust_status"], wg_update["authority_t"], wg_update["confidence"], wg_update["contradiction"], json.dumps(wg_update["affected_slot_ids"]), wg_update["replay_identity_ref"], wg_update["state_digest"], json.dumps(wg_update), wg_update["created_at_ms"],
                ),
            )
            cell_id = f"cell_{wg_update['loop_id']}_{wg_update['node_id']}_{wg_update['slot_id']}"
            conn.execute(
                """
                INSERT INTO memory_cells (cell_id, loop_id, node_id, slot_id, state_digest, trust_status, authority_t, latest_update_id, payload)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (loop_id, node_id, slot_id) DO UPDATE SET
                  state_digest=EXCLUDED.state_digest,
                  trust_status=EXCLUDED.trust_status,
                  authority_t=EXCLUDED.authority_t,
                  latest_update_id=EXCLUDED.latest_update_id,
                  payload=EXCLUDED.payload,
                  updated_at=now()
                """,
                (cell_id, wg_update["loop_id"], wg_update["node_id"], wg_update["slot_id"], wg_update["state_digest"], wg_update["trust_status"], wg_update["authority_t"], wg_update["update_id"], json.dumps(result["memory"])),
            )
            conn.execute(
                """
                INSERT INTO nla_activation_witnesses
                (witness_id, run_id, loop_id, node_id, wg_rnn_update_id, source_model, activation, verbalizer, reconstructor, fidelity, lifecycle, policy, created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (witness_id) DO NOTHING
                """,
                (nla["witness_id"], run_id, nla["loop_id"], nla["node_id"], nla.get("wg_rnn_update_id"), json.dumps(nla["source_model"]), json.dumps(nla["activation"]), json.dumps(nla["verbalizer"]), json.dumps(nla["reconstructor"]), json.dumps(nla["fidelity"]), json.dumps(nla["lifecycle"]), json.dumps(nla["policy"]), nla["created_at_ms"]),
            )
            conn.execute(
                "INSERT INTO audit_events (event_type, severity, run_id, witness_id, update_id, payload) VALUES (%s,%s,%s,%s,%s,%s)",
                ("runtime.run", "info", run_id, nla["witness_id"], wg_update["update_id"], json.dumps(result)),
            )
            for w in (extra_witnesses or []):
                conn.execute(
                    """
                    INSERT INTO evidence_witnesses
                    (witness_id, witness_type, force, observer_id, status, corpus, payload_digest, payload, run_id, created_at_ms)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (witness_id) DO UPDATE SET
                      status=EXCLUDED.status, payload=EXCLUDED.payload, run_id=COALESCE(EXCLUDED.run_id, evidence_witnesses.run_id)
                    """,
                    (
                        w["witness_id"], w["witness_type"], w.get("force", "observe"),
                        w.get("observer_id", "unknown"), w.get("status", "recorded"),
                        json.dumps(w.get("corpus", {})), w.get("payload_digest", ""),
                        json.dumps(w.get("payload", {})), run_id, w.get("created_at_ms", 0),
                    ),
                )
            conn.commit()

    def insert_wgrnn_event(self, *, event: dict[str, Any], witness: dict[str, Any] | None = None) -> None:
        """Persist standalone WG-RNN events outside full run bundles."""
        update = None
        if isinstance(event, dict):
            update = event.get("memory_update") or event.get("update")
            if not update and isinstance(event.get("ledger_entry"), dict):
                update = event["ledger_entry"].get("update")
        with self.connect() as conn:
            if isinstance(update, dict) and update.get("update_id"):
                conn.execute(
                    """
                    INSERT INTO wgrnn_memory_updates
                    (update_id, run_id, loop_id, node_id, slot_id, update_kind, trust_status, authority_t, confidence, contradiction, affected_slot_ids, replay_identity_ref, state_digest, payload, created_at_ms)
                    VALUES (%s,NULL,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (update_id) DO UPDATE SET
                      trust_status=EXCLUDED.trust_status,
                      authority_t=EXCLUDED.authority_t,
                      confidence=EXCLUDED.confidence,
                      contradiction=EXCLUDED.contradiction,
                      state_digest=EXCLUDED.state_digest,
                      payload=EXCLUDED.payload
                    """,
                    (
                        update["update_id"], update["loop_id"], update["node_id"], update["slot_id"],
                        update["update_kind"], update["trust_status"], update["authority_t"],
                        update["confidence"], update["contradiction"], json.dumps(update["affected_slot_ids"]),
                        update["replay_identity_ref"], update["state_digest"], json.dumps(update), update["created_at_ms"],
                    ),
                )
                cell_id = f"cell_{update['loop_id']}_{update['node_id']}_{update['slot_id']}"
                conn.execute(
                    """
                    INSERT INTO memory_cells (cell_id, loop_id, node_id, slot_id, state_digest, trust_status, authority_t, latest_update_id, payload)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (loop_id, node_id, slot_id) DO UPDATE SET
                      state_digest=EXCLUDED.state_digest,
                      trust_status=EXCLUDED.trust_status,
                      authority_t=EXCLUDED.authority_t,
                      latest_update_id=EXCLUDED.latest_update_id,
                      payload=EXCLUDED.payload,
                      updated_at=now()
                    """,
                    (cell_id, update["loop_id"], update["node_id"], update["slot_id"], update["state_digest"], update["trust_status"], update["authority_t"], update["update_id"], json.dumps(event)),
                )
            conn.execute(
                "INSERT INTO audit_events (event_type, severity, run_id, witness_id, update_id, payload) VALUES (%s,%s,NULL,%s,%s,%s)",
                (
                    str(event.get("event", "wgrnn.event")),
                    "info",
                    (witness or {}).get("witness_id"),
                    update.get("update_id") if isinstance(update, dict) else None,
                    json.dumps(event),
                ),
            )
            if witness:
                conn.execute(
                    """
                    INSERT INTO evidence_witnesses
                    (witness_id, witness_type, force, observer_id, status, corpus, payload_digest, payload, run_id, created_at_ms)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s)
                    ON CONFLICT (witness_id) DO UPDATE SET
                      status=EXCLUDED.status,
                      payload=EXCLUDED.payload
                    """,
                    (
                        witness["witness_id"], witness["witness_type"], witness.get("force", "observe"),
                        witness.get("observer_id", "unknown"), witness.get("status", "recorded"),
                        json.dumps(witness.get("corpus", {})), witness.get("payload_digest", ""),
                        json.dumps(witness.get("payload", {})), witness.get("created_at_ms", 0),
                    ),
                )
            conn.commit()

    def insert_witness(self, witness: dict[str, Any], run_id: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_witnesses
                (witness_id, witness_type, force, observer_id, status, corpus, payload_digest, payload, run_id, created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (witness_id) DO UPDATE SET
                  status=EXCLUDED.status, payload=EXCLUDED.payload, run_id=COALESCE(EXCLUDED.run_id, evidence_witnesses.run_id)
                """,
                (
                    witness["witness_id"], witness["witness_type"], witness.get("force", "observe"),
                    witness.get("observer_id", "unknown"), witness.get("status", "recorded"),
                    json.dumps(witness.get("corpus", {})), witness.get("payload_digest", ""),
                    json.dumps(witness.get("payload", {})), run_id, witness.get("created_at_ms", 0),
                ),
            )
            conn.commit()

    def insert_evidence_claim(self, claim: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_claims
                (claim_id, claim_digest, claim_kind, claim_status, epistemic_status, force, subject, predicate, object, support, corpus, payload, created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (claim_id) DO NOTHING
                """,
                (
                    claim["claim_id"], claim["claim_digest"], claim.get("claim_kind", "observation"),
                    claim.get("claim_status", "observed"), claim.get("epistemic_status", "observed"),
                    claim.get("force", "observe"), claim.get("subject", ""), claim.get("predicate", ""),
                    json.dumps(claim.get("object")), json.dumps(claim.get("support", [])),
                    json.dumps(claim.get("corpus", {})), json.dumps(claim), claim.get("created_at_ms", 0),
                ),
            )
            conn.commit()

    def upsert_corpus_version(self, corpus: dict[str, Any], validation: dict[str, Any], status: str = "candidate") -> None:
        corpus_id = "corpus_" + str(corpus.get("digest", "sha256:unknown")).split(":")[-1][:24]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO corpus_versions (corpus_id, version, digest, manifest_ref, status, manifest, validation)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (corpus_id) DO UPDATE SET
                  version=EXCLUDED.version, digest=EXCLUDED.digest, manifest_ref=EXCLUDED.manifest_ref,
                  status=EXCLUDED.status, manifest=EXCLUDED.manifest, validation=EXCLUDED.validation
                """,
                (corpus_id, corpus.get("version", "unversioned"), corpus.get("digest", "sha256:unknown"), corpus.get("manifest_ref", "unknown"), status, json.dumps(corpus), json.dumps(validation)),
            )
            conn.commit()

    def fetch_recent(self, table: str, limit: int = 20, *, timeout: float | None = None) -> list[dict[str, Any]]:
        order_columns = {
            "runtime_runs": "created_at",
            "wgrnn_memory_updates": "created_at",
            "nla_activation_witnesses": "created_at",
            "memory_cells": "updated_at",
            "audit_events": "created_at",
            "corpus_documents": "created_at",
            "corpus_versions": "created_at",
            "evidence_claims": "created_at",
            "evidence_witnesses": "created_at",
            "module_invocations": "created_at",
            "source_documents": "created_at",
            "source_index_generations": "started_at",
            "session_transcript_events": "ingested_at",
            "observer_claim_observations": "created_at",
            "claim_consensus": "updated_at",
        }
        order_col = order_columns.get(table)
        if order_col is None:
            raise ValueError("unsupported table")
        connection = self.connect() if timeout is None else self._get_pool().connection(timeout=max(0.05, float(timeout)))
        with connection as conn:
            rows = conn.execute(
                f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT %s",
                (min(max(int(limit), 1), 100),),
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert_corpus_docs(self, docs: Iterable[dict[str, Any]]) -> int:
        count = 0
        with self.connect() as conn:
            for d in docs:
                conn.execute(
                    """
                    INSERT INTO corpus_documents (doc_id, path, title, digest, headings, excerpt)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (doc_id) DO UPDATE SET
                      path=EXCLUDED.path, title=EXCLUDED.title, digest=EXCLUDED.digest,
                      headings=EXCLUDED.headings, excerpt=EXCLUDED.excerpt
                    """,
                    (d["doc_id"], d["path"], d["title"], d["digest"], json.dumps(d["headings"]), d["excerpt"]),
                )
                count += 1
            conn.commit()
        return count

    def insert_session_event(
        self,
        record: dict[str, Any],
        *,
        training_eligible: bool = True,
        redaction: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO session_transcript_events
                (session_id, sequence, event_digest, previous_event_digest, content_digest,
                 event_type, actor, created_at_ms, witness_id, supersedes, tags, content,
                 training_eligible, redaction)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_digest) DO NOTHING
                """,
                (
                    record["session_id"], record["sequence"], record["event_digest"],
                    record.get("previous_event_digest"), record["content_digest"],
                    record["event_type"], record["actor"], record["created_at_ms"],
                    record.get("witness_id"), json.dumps(record.get("supersedes", [])),
                    json.dumps(record.get("tags", [])), json.dumps(record.get("content", {})),
                    bool(training_eligible), json.dumps(redaction or {}),
                ),
            )
            conn.commit()
        return {"inserted": True, "event_digest": record["event_digest"]}

    def search_session_events(
        self,
        *,
        query: str | None = None,
        session_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
        tag: str | None = None,
        training_eligible: bool | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        clauses: list[str] = []
        params: list[Any] = []
        if query:
            clauses.append("(content::text ILIKE %s OR event_type ILIKE %s OR actor ILIKE %s)")
            term = f"%{query}%"
            params.extend([term, term, term])
        if session_id:
            clauses.append("session_id = %s")
            params.append(session_id)
        if event_type:
            clauses.append("event_type = %s")
            params.append(event_type)
        if actor:
            clauses.append("actor = %s")
            params.append(actor)
        if tag:
            clauses.append("tags ? %s")
            params.append(tag)
        if training_eligible is not None:
            clauses.append("training_eligible = %s")
            params.append(bool(training_eligible))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(min(max(int(limit), 1), 200))
        sql = (
            "SELECT session_id,sequence,event_digest,previous_event_digest,content_digest,event_type,actor,"
            "created_at_ms,witness_id,supersedes,tags,content,training_eligible,redaction,ingested_at "
            f"FROM session_transcript_events{where} ORDER BY created_at_ms DESC, sequence DESC LIMIT %s"
        )
        with self.connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return {"schema_version": "postgres-transcript-search-v1", "count": len(rows), "events": [dict(r) for r in rows]}

    def begin_source_generation(
        self,
        *,
        generation_id: str,
        repository_id: str,
        root_path: str | None = None,
        commit_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO source_index_generations
                (generation_id, repository_id, root_path, commit_id, status, metadata)
                VALUES (%s,%s,%s,%s,'staging',%s)
                ON CONFLICT (generation_id) DO UPDATE SET
                  repository_id=EXCLUDED.repository_id,
                  root_path=EXCLUDED.root_path,
                  commit_id=EXCLUDED.commit_id,
                  status='staging',
                  metadata=EXCLUDED.metadata,
                  document_count=0,
                  byte_count=0,
                  completed_at=NULL
                """,
                (generation_id, repository_id, root_path, commit_id, json.dumps(metadata or {})),
            )
            conn.execute("DELETE FROM source_documents WHERE generation_id=%s", (generation_id,))
            conn.commit()
        return {"generation_id": generation_id, "repository_id": repository_id, "status": "staging"}

    def upsert_source_documents(self, docs: Iterable[dict[str, Any]]) -> dict[str, Any]:
        count = 0
        byte_count = 0
        generations: set[str] = set()
        with self.connect() as conn:
            for doc in docs:
                content = str(doc.get("content") or "")
                generation_id = str(doc["generation_id"])
                repository_id = str(doc["repository_id"])
                conn.execute(
                    """
                    INSERT INTO source_documents
                    (repository_id,generation_id,path,chunk_index,language,content_digest,source_digest,content,metadata,training_eligible)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (repository_id,generation_id,path,chunk_index) DO UPDATE SET
                      language=EXCLUDED.language,
                      content_digest=EXCLUDED.content_digest,
                      source_digest=EXCLUDED.source_digest,
                      content=EXCLUDED.content,
                      metadata=EXCLUDED.metadata,
                      training_eligible=EXCLUDED.training_eligible,
                      created_at=now()
                    """,
                    (
                        repository_id, generation_id, str(doc["path"]), int(doc.get("chunk_index", 0)),
                        doc.get("language"), str(doc["content_digest"]), doc.get("source_digest"), content,
                        json.dumps(doc.get("metadata") or {}), bool(doc.get("training_eligible", True)),
                    ),
                )
                count += 1
                byte_count += len(content.encode("utf-8"))
                generations.add(generation_id)
            for generation_id in generations:
                conn.execute(
                    """
                    UPDATE source_index_generations SET
                      document_count=(SELECT count(*) FROM source_documents WHERE generation_id=%s),
                      byte_count=(SELECT coalesce(sum(octet_length(content)),0) FROM source_documents WHERE generation_id=%s)
                    WHERE generation_id=%s
                    """,
                    (generation_id, generation_id, generation_id),
                )
            conn.commit()
        return {"upserted": count, "bytes": byte_count, "generations": sorted(generations)}

    def finalize_source_generation(self, *, generation_id: str, status: str = "completed", keep_generations: int = 2) -> dict[str, Any]:
        if status not in {"completed", "failed"}:
            raise ValueError("status must be completed or failed")
        with self.connect() as conn:
            row = conn.execute(
                "UPDATE source_index_generations SET status=%s, completed_at=now() WHERE generation_id=%s RETURNING repository_id,document_count,byte_count",
                (status, generation_id),
            ).fetchone()
            if row is None:
                raise ValueError("unknown source generation")
            repository_id = row["repository_id"]
            if status == "completed":
                conn.execute(
                    """
                    UPDATE source_index_generations SET status='superseded'
                    WHERE repository_id=%s AND generation_id<>%s AND status='completed'
                    """,
                    (repository_id, generation_id),
                )
                old = conn.execute(
                    """
                    SELECT generation_id FROM source_index_generations
                    WHERE repository_id=%s AND status='superseded'
                    ORDER BY completed_at DESC NULLS LAST OFFSET %s
                    """,
                    (repository_id, max(int(keep_generations) - 1, 0)),
                ).fetchall()
                for item in old:
                    conn.execute("DELETE FROM source_index_generations WHERE generation_id=%s", (item["generation_id"],))
            conn.commit()
        return {"generation_id": generation_id, "repository_id": repository_id, "status": status, "document_count": row["document_count"], "byte_count": row["byte_count"]}

    def search_source_documents(
        self,
        *,
        query: str,
        repository_id: str | None = None,
        path_prefix: str | None = None,
        training_eligible: bool | None = None,
        limit: int = 20,
        preview_chars: int = 500,
    ) -> dict[str, Any]:
        raw_query = str(query or "").strip()
        if not raw_query:
            raise ValueError("query is required")
        terms = []
        seen = set()
        for token in re.findall(r"[A-Za-z0-9_]+", raw_query.lower()):
            if token and token not in seen:
                terms.append(token)
                seen.add(token)
            if len(terms) >= 32:
                break
        if not terms:
            raise ValueError("query contains no searchable terms")
        ts_query = " | ".join(terms)
        phrase_pattern = f"%{raw_query}%"
        clauses = [
            "g.status='completed'",
            "(d.search_vector @@ q.tsq OR d.content ILIKE q.phrase OR d.path ILIKE q.phrase)",
        ]
        params: list[Any] = [ts_query, phrase_pattern]
        if repository_id:
            clauses.append("d.repository_id=%s")
            params.append(repository_id)
        if path_prefix:
            clauses.append("d.path LIKE %s")
            params.append(path_prefix.rstrip("/") + "%")
        if training_eligible is not None:
            clauses.append("d.training_eligible=%s")
            params.append(bool(training_eligible))
        params.append(min(max(int(limit), 1), 100))
        with self.connect() as conn:
            rows = conn.execute(
                """
                WITH q AS (
                  SELECT to_tsquery('simple', %s) AS tsq, %s::text AS phrase
                )
                SELECT d.repository_id,d.generation_id,d.path,d.chunk_index,d.language,d.content_digest,
                       d.content,
                       ts_rank(d.search_vector, q.tsq)
                         + CASE WHEN d.content ILIKE q.phrase THEN 2.0 ELSE 0.0 END
                         + CASE WHEN d.path ILIKE q.phrase THEN 3.0 ELSE 0.0 END AS rank
                FROM source_documents d
                JOIN source_index_generations g ON g.generation_id=d.generation_id
                CROSS JOIN q
                WHERE """ + " AND ".join(clauses) + " ORDER BY rank DESC, d.path, d.chunk_index LIMIT %s",
                tuple(params),
            ).fetchall()
        requested_preview = min(max(int(preview_chars), 120), 1000)
        preview_limit = min(requested_preview, max(120, 5000 // max(len(rows), 1)))
        documents: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            content = str(item.pop("content", ""))
            lower = content.lower()
            positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
            center = min(positions) if positions else 0
            start = max(0, center - preview_limit // 4)
            end = min(len(content), start + preview_limit)
            if end - start < preview_limit and start > 0:
                start = max(0, end - preview_limit)
            item.update({
                "content_preview": content[start:end],
                "preview_start": start,
                "preview_end": end,
                "content_chars": len(content),
                "preview_truncated": start > 0 or end < len(content),
            })
            documents.append(item)
        return {
            "schema_version": "source-search-v3.1",
            "query": raw_query,
            "query_terms": terms,
            "match_mode": "ranked_any_term_with_exact_phrase_boost",
            "count": len(documents),
            "documents": documents,
        }

    def get_source_document(
        self,
        *,
        repository_id: str,
        path: str,
        chunk_index: int = 0,
        generation_id: str | None = None,
        offset: int = 0,
        max_chars: int = 8000,
    ) -> dict[str, Any]:
        clauses = ["d.repository_id=%s", "d.path=%s", "d.chunk_index=%s"]
        params: list[Any] = [repository_id, path, int(chunk_index)]
        if generation_id:
            clauses.append("d.generation_id=%s")
            params.append(generation_id)
        else:
            clauses.append("g.status='completed'")
        sql = """
            SELECT d.repository_id,d.generation_id,d.path,d.chunk_index,d.language,d.content_digest,
                   d.source_digest,d.content,d.metadata,d.training_eligible,g.commit_id,g.completed_at
            FROM source_documents d
            JOIN source_index_generations g ON g.generation_id=d.generation_id
            WHERE """ + " AND ".join(clauses) + " ORDER BY g.completed_at DESC NULLS LAST LIMIT 1"
        with self.connect() as conn:
            row = conn.execute(sql, tuple(params)).fetchone()
        if row is None:
            return {
                "schema_version": "source-get-v1",
                "found": False,
                "repository_id": repository_id,
                "path": path,
                "chunk_index": int(chunk_index),
                "generation_id": generation_id,
            }
        item = dict(row)
        content = str(item.pop("content", ""))
        start = min(max(int(offset), 0), len(content))
        size = min(max(int(max_chars), 256), 10000)
        end = min(len(content), start + size)
        item.update({
            "schema_version": "source-get-v1",
            "found": True,
            "content": content[start:end],
            "content_chars": len(content),
            "offset": start,
            "next_offset": end if end < len(content) else None,
            "eof": end >= len(content),
        })
        return item

    def source_index_status(self) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT ON (repository_id)
                  repository_id,generation_id,root_path,commit_id,status,metadata,document_count,byte_count,started_at,completed_at
                FROM source_index_generations
                ORDER BY repository_id, completed_at DESC NULLS LAST, started_at DESC
                """
            ).fetchall()
        return {"schema_version": "source-index-status-v1", "repositories": [dict(r) for r in rows]}

