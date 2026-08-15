from __future__ import annotations

import json
import re
import time
from contextlib import nullcontext
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
  signature_suite TEXT,
  signing_key_id TEXT,
  signed_envelope JSONB,
  signature_verified BOOLEAN NOT NULL DEFAULT FALSE,
  run_id TEXT REFERENCES runtime_runs(run_id) ON DELETE SET NULL,
  created_at_ms BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE evidence_witnesses ADD COLUMN IF NOT EXISTS signature_suite TEXT;
ALTER TABLE evidence_witnesses ADD COLUMN IF NOT EXISTS signing_key_id TEXT;
ALTER TABLE evidence_witnesses ADD COLUMN IF NOT EXISTS signed_envelope JSONB;
ALTER TABLE evidence_witnesses ADD COLUMN IF NOT EXISTS signature_verified BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS evidence_witnesses_signing_key_idx ON evidence_witnesses(signing_key_id);

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

-- Witness Contract v1.6 Draft 5.3.18 meta-object candidate graph.
-- These tables preserve canonical semantic/edge identities while observation
-- support remains non-authoritative until a separate evidence/policy gate acts.
CREATE TABLE IF NOT EXISTS semantic_contents (
  semantic_content_id TEXT PRIMARY KEY,
  contract_version TEXT NOT NULL,
  content_type TEXT NOT NULL,
  canonical_body BYTEA NOT NULL,
  schema_id TEXT NOT NULL,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meta_object_edges (
  edge_content_id TEXT PRIMARY KEY,
  source_content_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id),
  relation_type TEXT NOT NULL,
  target_content_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id),
  context_content_id TEXT REFERENCES semantic_contents(semantic_content_id),
  assumption_manifest_id TEXT,
  policy_id TEXT NOT NULL,
  valid_from TIMESTAMPTZ,
  valid_until TIMESTAMPTZ,
  supersedes_edge_id TEXT REFERENCES meta_object_edges(edge_content_id),
  canonical_edge BYTEA NOT NULL,
  CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
);
CREATE INDEX IF NOT EXISTS meta_edges_source_relation_idx ON meta_object_edges(source_content_id, relation_type);
CREATE INDEX IF NOT EXISTS meta_edges_target_relation_idx ON meta_object_edges(target_content_id, relation_type);

CREATE TABLE IF NOT EXISTS meta_graph_observations (
  observation_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  source_update_id TEXT,
  root_content_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id),
  content_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  edge_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  trust_status TEXT NOT NULL DEFAULT 'candidate',
  observed_at_ms BIGINT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS meta_graph_observations_namespace_idx ON meta_graph_observations(namespace, observed_at_ms DESC);
CREATE INDEX IF NOT EXISTS meta_graph_observations_content_gin ON meta_graph_observations USING GIN(content_ids);

CREATE TABLE IF NOT EXISTS meta_edge_recurrence (
  namespace TEXT NOT NULL,
  edge_content_id TEXT NOT NULL REFERENCES meta_object_edges(edge_content_id),
  occurrence_count BIGINT NOT NULL DEFAULT 1,
  first_observed_at_ms BIGINT NOT NULL,
  last_observed_at_ms BIGINT NOT NULL,
  last_update_id TEXT,
  PRIMARY KEY(namespace, edge_content_id)
);
CREATE INDEX IF NOT EXISTS meta_edge_recurrence_count_idx ON meta_edge_recurrence(namespace, occurrence_count DESC);
CREATE INDEX IF NOT EXISTS meta_edge_recurrence_edge_namespace_idx ON meta_edge_recurrence(edge_content_id, namespace);

-- Reconstructible meta-object composition v3. Pair-edge recurrence is retained
-- only for backwards compatibility with older candidate observations; active
-- ranking is based on witnessed meta-object participation/occurrence structure.
ALTER TABLE meta_graph_observations ADD COLUMN IF NOT EXISTS composition_content_id TEXT;
ALTER TABLE meta_graph_observations ADD COLUMN IF NOT EXISTS meta_object_ids JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE meta_graph_observations ADD COLUMN IF NOT EXISTS occurrence_ids JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS meta_object_occurrences (
  occurrence_id TEXT PRIMARY KEY REFERENCES semantic_contents(semantic_content_id) ON DELETE CASCADE,
  information_content_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id) ON DELETE CASCADE,
  meta_object_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id) ON DELETE CASCADE,
  descendant_meta_object_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  locator JSONB NOT NULL DEFAULT '{}'::jsonb,
  ordinal BIGINT NOT NULL,
  channel TEXT,
  confidence JSONB,
  sum_contribution JSONB NOT NULL DEFAULT '{}'::jsonb,
  canonical_occurrence BYTEA NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE meta_object_occurrences ADD COLUMN IF NOT EXISTS sum_contribution JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS meta_object_occurrences_information_idx ON meta_object_occurrences(information_content_id, ordinal);
CREATE INDEX IF NOT EXISTS meta_object_occurrences_meta_idx ON meta_object_occurrences(meta_object_id);
CREATE INDEX IF NOT EXISTS meta_object_occurrences_descendants_gin ON meta_object_occurrences USING GIN(descendant_meta_object_ids);

CREATE TABLE IF NOT EXISTS media_profile_nodes (
  node_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  left_node_id TEXT,
  right_node_id TEXT,
  occurrence_id TEXT,
  canonical_node BYTEA NOT NULL,
  sum_vector JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE media_profile_nodes ADD COLUMN IF NOT EXISTS left_node_id TEXT;
ALTER TABLE media_profile_nodes ADD COLUMN IF NOT EXISTS right_node_id TEXT;
ALTER TABLE media_profile_nodes ADD COLUMN IF NOT EXISTS occurrence_id TEXT;
CREATE INDEX IF NOT EXISTS media_profile_nodes_left_idx ON media_profile_nodes(left_node_id) WHERE left_node_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS media_profile_nodes_right_idx ON media_profile_nodes(right_node_id) WHERE right_node_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS media_profile_nodes_occurrence_idx ON media_profile_nodes(occurrence_id) WHERE occurrence_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS media_profiles (
  profile_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  observation_id TEXT REFERENCES meta_graph_observations(observation_id) ON DELETE SET NULL,
  information_ref TEXT NOT NULL,
  root_content_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id) ON DELETE RESTRICT,
  composition_content_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id) ON DELETE RESTRICT,
  merkle_sum_root_node_id TEXT NOT NULL REFERENCES media_profile_nodes(node_id) ON DELETE RESTRICT,
  aggregate_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
  sum_vector JSONB NOT NULL DEFAULT '{}'::jsonb,
  profile_body BYTEA NOT NULL,
  signed_manifest JSONB,
  signature_suite TEXT,
  signing_key_id TEXT,
  signature_verified BOOLEAN NOT NULL DEFAULT FALSE,
  trust_status TEXT NOT NULL DEFAULT 'candidate',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS media_profiles_namespace_created_idx ON media_profiles(namespace, created_at DESC);
CREATE INDEX IF NOT EXISTS media_profiles_information_ref_idx ON media_profiles(information_ref);

CREATE TABLE IF NOT EXISTS information_chains (
  chain_id TEXT PRIMARY KEY,
  chain_ref TEXT,
  profile_ids JSONB NOT NULL,
  chain_body BYTEA NOT NULL,
  signed_manifest JSONB,
  signature_suite TEXT,
  signing_key_id TEXT,
  signature_verified BOOLEAN NOT NULL DEFAULT FALSE,
  trust_status TEXT NOT NULL DEFAULT 'candidate',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS information_chains_created_idx ON information_chains(created_at DESC);
CREATE INDEX IF NOT EXISTS information_chains_profile_ids_gin ON information_chains USING GIN(profile_ids);

CREATE TABLE IF NOT EXISTS meta_object_recurrence (
  namespace TEXT NOT NULL,
  meta_object_id TEXT NOT NULL REFERENCES semantic_contents(semantic_content_id) ON DELETE CASCADE,
  observation_count BIGINT NOT NULL DEFAULT 1,
  occurrence_count BIGINT NOT NULL DEFAULT 1,
  first_observed_at_ms BIGINT NOT NULL,
  last_observed_at_ms BIGINT NOT NULL,
  last_update_id TEXT,
  PRIMARY KEY(namespace, meta_object_id)
);
CREATE INDEX IF NOT EXISTS meta_object_recurrence_count_idx ON meta_object_recurrence(namespace, observation_count DESC, occurrence_count DESC);
CREATE INDEX IF NOT EXISTS meta_object_recurrence_meta_namespace_idx ON meta_object_recurrence(meta_object_id, namespace);
"""


def _witness_signature_storage(witness: dict[str, Any]) -> tuple[str | None, str | None, dict[str, Any] | None, bool]:
    envelope = witness.get("pq_signed_envelope") or witness.get("signed_envelope")
    if not isinstance(envelope, dict):
        return None, None, None, False
    summary = witness.get("pq_signature") if isinstance(witness.get("pq_signature"), dict) else {}
    suite = str(envelope.get("signature_suite") or summary.get("signature_suite") or "").strip() or None
    key_id = str(envelope.get("key_id") or summary.get("key_id") or "").strip() or None
    verified = bool(summary.get("verified") or witness.get("signature_verified"))
    return suite, key_id, envelope, verified


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
                signature_suite, signing_key_id, signed_envelope, signature_verified = _witness_signature_storage(w)
                conn.execute(
                    """
                    INSERT INTO evidence_witnesses
                    (witness_id, witness_type, force, observer_id, status, corpus, payload_digest, payload, signature_suite, signing_key_id, signed_envelope, signature_verified, run_id, created_at_ms)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (witness_id) DO UPDATE SET
                      status=EXCLUDED.status,
                      payload=EXCLUDED.payload,
                      signature_suite=COALESCE(EXCLUDED.signature_suite, evidence_witnesses.signature_suite),
                      signing_key_id=COALESCE(EXCLUDED.signing_key_id, evidence_witnesses.signing_key_id),
                      signed_envelope=COALESCE(EXCLUDED.signed_envelope, evidence_witnesses.signed_envelope),
                      signature_verified=EXCLUDED.signature_verified OR evidence_witnesses.signature_verified,
                      run_id=COALESCE(EXCLUDED.run_id, evidence_witnesses.run_id)
                    """,
                    (
                        w["witness_id"], w["witness_type"], w.get("force", "observe"),
                        w.get("observer_id", "unknown"), w.get("status", "recorded"),
                        json.dumps(w.get("corpus", {})), w.get("payload_digest", ""),
                        json.dumps(w.get("payload", {})), signature_suite, signing_key_id,
                        json.dumps(signed_envelope) if signed_envelope is not None else None, signature_verified,
                        run_id, w.get("created_at_ms", 0),
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
                signature_suite, signing_key_id, signed_envelope, signature_verified = _witness_signature_storage(witness)
                conn.execute(
                    """
                    INSERT INTO evidence_witnesses
                    (witness_id, witness_type, force, observer_id, status, corpus, payload_digest, payload, signature_suite, signing_key_id, signed_envelope, signature_verified, run_id, created_at_ms)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s)
                    ON CONFLICT (witness_id) DO UPDATE SET
                      status=EXCLUDED.status,
                      payload=EXCLUDED.payload,
                      signature_suite=COALESCE(EXCLUDED.signature_suite, evidence_witnesses.signature_suite),
                      signing_key_id=COALESCE(EXCLUDED.signing_key_id, evidence_witnesses.signing_key_id),
                      signed_envelope=COALESCE(EXCLUDED.signed_envelope, evidence_witnesses.signed_envelope),
                      signature_verified=EXCLUDED.signature_verified OR evidence_witnesses.signature_verified
                    """,
                    (
                        witness["witness_id"], witness["witness_type"], witness.get("force", "observe"),
                        witness.get("observer_id", "unknown"), witness.get("status", "recorded"),
                        json.dumps(witness.get("corpus", {})), witness.get("payload_digest", ""),
                        json.dumps(witness.get("payload", {})), signature_suite, signing_key_id,
                        json.dumps(signed_envelope) if signed_envelope is not None else None, signature_verified,
                        witness.get("created_at_ms", 0),
                    ),
                )
            conn.commit()

    def insert_witness(self, witness: dict[str, Any], run_id: str | None = None) -> None:
        signature_suite, signing_key_id, signed_envelope, signature_verified = _witness_signature_storage(witness)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_witnesses
                (witness_id, witness_type, force, observer_id, status, corpus, payload_digest, payload, signature_suite, signing_key_id, signed_envelope, signature_verified, run_id, created_at_ms)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (witness_id) DO UPDATE SET
                  status=EXCLUDED.status,
                  payload=EXCLUDED.payload,
                  signature_suite=COALESCE(EXCLUDED.signature_suite, evidence_witnesses.signature_suite),
                  signing_key_id=COALESCE(EXCLUDED.signing_key_id, evidence_witnesses.signing_key_id),
                  signed_envelope=COALESCE(EXCLUDED.signed_envelope, evidence_witnesses.signed_envelope),
                  signature_verified=EXCLUDED.signature_verified OR evidence_witnesses.signature_verified,
                  run_id=COALESCE(EXCLUDED.run_id, evidence_witnesses.run_id)
                """,
                (
                    witness["witness_id"], witness["witness_type"], witness.get("force", "observe"),
                    witness.get("observer_id", "unknown"), witness.get("status", "recorded"),
                    json.dumps(witness.get("corpus", {})), witness.get("payload_digest", ""),
                    json.dumps(witness.get("payload", {})), signature_suite, signing_key_id,
                    json.dumps(signed_envelope) if signed_envelope is not None else None, signature_verified,
                    run_id, witness.get("created_at_ms", 0),
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
        corpus_id = "corpus_" + str(corpus.get("digest", "shake256-512:unknown")).split(":")[-1][:24]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO corpus_versions (corpus_id, version, digest, manifest_ref, status, manifest, validation)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (corpus_id) DO UPDATE SET
                  version=EXCLUDED.version, digest=EXCLUDED.digest, manifest_ref=EXCLUDED.manifest_ref,
                  status=EXCLUDED.status, manifest=EXCLUDED.manifest, validation=EXCLUDED.validation
                """,
                (corpus_id, corpus.get("version", "unversioned"), corpus.get("digest", "shake256-512:unknown"), corpus.get("manifest_ref", "unknown"), status, json.dumps(corpus), json.dumps(validation)),
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
        from .meta_graph import build_information_graph

        count = 0
        byte_count = 0
        graph_count = 0
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
                content_bytes = len(content.encode("utf-8"))
                graph_window = content[:16000]
                graph = build_information_graph(
                    information_kind="source_document_chunk",
                    text_fields={"content": graph_window},
                    facets={
                        "repository_id": repository_id,
                        "generation_id": generation_id,
                        "path": str(doc["path"]),
                        "chunk_index": int(doc.get("chunk_index", 0)),
                        "language": doc.get("language"),
                        "training_eligible": bool(doc.get("training_eligible", True)),
                        "metadata": doc.get("metadata") or {},
                    },
                    metadata={
                        "content_digest": str(doc["content_digest"]),
                        "source_digest": doc.get("source_digest"),
                        "content_chars": len(content),
                        "content_bytes": content_bytes,
                        "graph_window_chars": len(graph_window),
                        "graph_window_truncated": len(graph_window) < len(content),
                    },
                )
                self.insert_meta_graph_observation(
                    graph=graph,
                    namespace=f"source-document/{repository_id}",
                    source_update_id=None,
                    trust_status="candidate",
                    observed_at_ms=int(time.time() * 1000),
                    metadata={
                        "repository_id": repository_id,
                        "generation_id": generation_id,
                        "path": str(doc["path"]),
                        "chunk_index": int(doc.get("chunk_index", 0)),
                        "content_digest": str(doc["content_digest"]),
                        "authority": "candidate_observation_only",
                    },
                    connection=conn,
                    commit=False,
                )
                graph_count += 1
                count += 1
                byte_count += content_bytes
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
        return {
            "upserted": count,
            "bytes": byte_count,
            "generations": sorted(generations),
            "meta_graph_observations": graph_count,
            "meta_graph_authority": "candidate_observation_only",
        }

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



    def insert_meta_graph_observation(
        self,
        *,
        graph: dict[str, Any],
        namespace: str,
        source_update_id: str | None,
        trust_status: str = "candidate",
        observed_at_ms: int,
        metadata: dict[str, Any] | None = None,
        connection: Any | None = None,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Persist one non-authoritative reconstructible meta-object composition."""
        from .crypto_primitives import contract_canonical_bytes, semantic_content_id

        contents = list(graph.get("contents") or [])
        edges = list(graph.get("edges") or [])
        occurrences = [row for row in (graph.get("occurrences") or []) if isinstance(row, dict)]
        content_ids = [str(row.get("semantic_content_id") or "") for row in contents if row.get("semantic_content_id")]
        edge_ids = [str(row.get("edge_content_id") or "") for row in edges if row.get("edge_content_id")]
        root_content_id = str(graph.get("root_content_id") or "")
        composition_content_id = str(graph.get("composition_content_id") or "") or None
        meta_object_ids = sorted({str(value) for value in (graph.get("meta_object_ids") or []) if str(value)})
        occurrence_ids = [str(row.get("occurrence_id") or "") for row in occurrences if row.get("occurrence_id")]
        if not root_content_id or root_content_id not in content_ids:
            raise ValueError("meta graph root_content_id is missing from contents")
        if composition_content_id and composition_content_id not in content_ids:
            raise ValueError("meta graph composition_content_id is missing from contents")

        observation_body = {
            "schema_version": "meta_graph_observation/v3",
            "namespace": str(namespace),
            "source_update_id": str(source_update_id or ""),
            "root_content_id": root_content_id,
            "composition_content_id": composition_content_id,
            "meta_object_ids": meta_object_ids,
            "occurrence_ids": occurrence_ids,
            "trust_status": str(trust_status),
        }
        observation_id = semantic_content_id("meta_graph_observation/v3", observation_body)

        # Count participation once per top-level occurrence. Nested descriptor IDs
        # inherit the occurrence, but observation_count is incremented only once
        # per media/information observation regardless of repetition inside it.
        participation: dict[str, int] = {}
        for occurrence in occurrences:
            descendants = {
                str(value) for value in (occurrence.get("descendant_meta_object_ids") or []) if str(value)
            }
            if occurrence.get("meta_object_id"):
                descendants.add(str(occurrence["meta_object_id"]))
            for meta_id in descendants:
                participation[meta_id] = participation.get(meta_id, 0) + 1
        if not participation:
            participation = {meta_id: 1 for meta_id in meta_object_ids}

        with (self.connect() if connection is None else nullcontext(connection)) as conn:
            for row in contents:
                conn.execute(
                    """
                    INSERT INTO semantic_contents(
                      semantic_content_id,contract_version,content_type,canonical_body,schema_id
                    ) VALUES(%s,%s,%s,%s,%s)
                    ON CONFLICT (semantic_content_id) DO NOTHING
                    """,
                    (
                        row["semantic_content_id"],
                        row.get("contract_version") or graph.get("contract_version") or "v1.6-draft-5.3.18",
                        row["content_type"],
                        bytes(row["canonical_body"]),
                        row.get("schema_id") or f"runtime://semantic/{row['content_type']}",
                    ),
                )
            # Preserve contract edge support for explicit relations supplied by a
            # future adapter, but v3 never manufactures within-object pair edges.
            for edge in edges:
                conn.execute(
                    """
                    INSERT INTO meta_object_edges(
                      edge_content_id,source_content_id,relation_type,target_content_id,
                      context_content_id,assumption_manifest_id,policy_id,valid_from,valid_until,
                      supersedes_edge_id,canonical_edge
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (edge_content_id) DO NOTHING
                    """,
                    (
                        edge["edge_content_id"], edge["source_content_id"], edge["relation_type"], edge["target_content_id"],
                        edge.get("context_content_id"), edge.get("assumption_manifest_id"),
                        edge.get("policy_id") or "policy:wg-rnn-candidate-meta-observation-v3",
                        edge.get("valid_from"), edge.get("valid_until"), edge.get("supersedes_edge_id"),
                        contract_canonical_bytes(edge),
                    ),
                )
            for occurrence in occurrences:
                conn.execute(
                    """
                    INSERT INTO meta_object_occurrences(
                      occurrence_id,information_content_id,meta_object_id,descendant_meta_object_ids,
                      locator,ordinal,channel,confidence,sum_contribution,canonical_occurrence
                    ) VALUES(%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s::jsonb,%s::jsonb,%s)
                    ON CONFLICT (occurrence_id) DO NOTHING
                    """,
                    (
                        occurrence["occurrence_id"], occurrence["information_content_id"], occurrence["meta_object_id"],
                        json.dumps(sorted({str(v) for v in (occurrence.get("descendant_meta_object_ids") or []) if str(v)})),
                        json.dumps(occurrence.get("locator") or {}, sort_keys=True), int(occurrence.get("ordinal") or 0),
                        occurrence.get("channel"), json.dumps(occurrence.get("confidence")),
                        json.dumps(occurrence.get("sum_contribution") or {}, sort_keys=True),
                        bytes(occurrence.get("canonical_occurrence") or b""),
                    ),
                )

            inserted_observation = conn.execute(
                """
                INSERT INTO meta_graph_observations(
                  observation_id,namespace,source_update_id,root_content_id,composition_content_id,
                  content_ids,edge_ids,meta_object_ids,occurrence_ids,trust_status,observed_at_ms,metadata
                ) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s::jsonb)
                ON CONFLICT (observation_id) DO NOTHING
                RETURNING observation_id
                """,
                (
                    observation_id, str(namespace), source_update_id, root_content_id, composition_content_id,
                    json.dumps(sorted(content_ids)), json.dumps(sorted(edge_ids)), json.dumps(meta_object_ids),
                    json.dumps(occurrence_ids), str(trust_status), int(observed_at_ms),
                    json.dumps(dict(metadata or {}), sort_keys=True),
                ),
            ).fetchone()

            if inserted_observation is not None:
                for meta_id, occurrence_count in sorted(participation.items()):
                    conn.execute(
                        """
                        INSERT INTO meta_object_recurrence(
                          namespace,meta_object_id,observation_count,occurrence_count,
                          first_observed_at_ms,last_observed_at_ms,last_update_id
                        ) VALUES(%s,%s,1,%s,%s,%s,%s)
                        ON CONFLICT(namespace,meta_object_id) DO UPDATE SET
                          observation_count=meta_object_recurrence.observation_count+1,
                          occurrence_count=meta_object_recurrence.occurrence_count+EXCLUDED.occurrence_count,
                          last_observed_at_ms=GREATEST(meta_object_recurrence.last_observed_at_ms, EXCLUDED.last_observed_at_ms),
                          last_update_id=EXCLUDED.last_update_id
                        """,
                        (str(namespace), meta_id, int(occurrence_count), int(observed_at_ms), int(observed_at_ms), source_update_id),
                    )
            if commit:
                conn.commit()
        return {
            "schema_version": "meta_graph_persist_result/v3",
            "observation_id": observation_id,
            "namespace": str(namespace),
            "source_update_id": source_update_id,
            "root_content_id": root_content_id,
            "composition_content_id": composition_content_id,
            "content_count": len(content_ids),
            "meta_object_count": len(meta_object_ids),
            "occurrence_count": len(occurrence_ids),
            "edge_count": len(edge_ids),
            "trust_status": str(trust_status),
            "authority": "candidate_observation_only",
        }

    def search_meta_graph(
        self,
        *,
        namespace: str,
        query_content_ids: Iterable[str],
        limit: int = 256,
        require_source_update_id: bool = True,
    ) -> dict[str, Any]:
        """Rank candidates by witnessed nested meta-object overlap and recurrence."""
        query_ids = sorted({str(value) for value in query_content_ids if str(value)})
        if not query_ids:
            return {"schema_version": "meta_graph_search/v3", "namespace": namespace, "matches": []}
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT observation_id,source_update_id,root_content_id,composition_content_id,
                       meta_object_ids,occurrence_ids,trust_status,observed_at_ms
                FROM meta_graph_observations
                WHERE namespace=%s
                ORDER BY observed_at_ms DESC
                LIMIT %s
                """,
                (str(namespace), min(max(int(limit), 1), 2048)),
            ).fetchall()
            recurrence_rows = conn.execute(
                """
                SELECT meta_object_id,observation_count,occurrence_count
                FROM meta_object_recurrence
                WHERE namespace=%s AND meta_object_id=ANY(%s)
                """,
                (str(namespace), query_ids),
            ).fetchall()
            shared_source_rows = conn.execute(
                """
                SELECT meta_object_id,coalesce(sum(observation_count),0)::bigint AS observation_count,
                       coalesce(sum(occurrence_count),0)::bigint AS occurrence_count
                FROM meta_object_recurrence
                WHERE namespace LIKE 'source-document/%%' AND namespace<>%s AND meta_object_id=ANY(%s)
                GROUP BY meta_object_id
                """,
                (str(namespace), query_ids),
            ).fetchall()
            shared_adapter_rows = conn.execute(
                """
                SELECT meta_object_id,coalesce(sum(observation_count),0)::bigint AS observation_count,
                       coalesce(sum(occurrence_count),0)::bigint AS occurrence_count
                FROM meta_object_recurrence
                WHERE namespace LIKE 'adapter-observation/%%' AND namespace<>%s AND meta_object_id=ANY(%s)
                GROUP BY meta_object_id
                """,
                (str(namespace), query_ids),
            ).fetchall()
        recurrence = {str(r["meta_object_id"]): (int(r["observation_count"]), int(r["occurrence_count"])) for r in recurrence_rows}
        shared_source = {str(r["meta_object_id"]): (int(r["observation_count"]), int(r["occurrence_count"])) for r in shared_source_rows}
        shared_adapter = {str(r["meta_object_id"]): (int(r["observation_count"]), int(r["occurrence_count"])) for r in shared_adapter_rows}
        query_set = set(query_ids)
        matches: list[dict[str, Any]] = []
        for row in rows:
            source_update_id = str(row.get("source_update_id") or "")
            if not source_update_id and require_source_update_id:
                continue
            observed_meta_ids = {str(value) for value in (row.get("meta_object_ids") or []) if str(value)}
            overlap = sorted(query_set & observed_meta_ids)
            if not overlap:
                continue
            local_observation_support = sum(max(recurrence.get(mid, (1, 1))[0] - 1, 0) for mid in overlap)
            local_occurrence_support = sum(max(recurrence.get(mid, (1, 1))[1] - 1, 0) for mid in overlap)
            shared_source_support = sum(shared_source.get(mid, (0, 0))[0] for mid in overlap)
            shared_source_occurrences = sum(shared_source.get(mid, (0, 0))[1] for mid in overlap)
            shared_adapter_support = sum(shared_adapter.get(mid, (0, 0))[0] for mid in overlap)
            shared_adapter_occurrences = sum(shared_adapter.get(mid, (0, 0))[1] for mid in overlap)
            overlap_ratio = len(overlap) / max(len(query_set), 1)
            local_recurrence_score = min(local_observation_support / max(len(overlap) * 4, 1), 1.0)
            shared_source_score = min(shared_source_support / max(len(overlap) * 8, 1), 1.0)
            shared_adapter_score = min(shared_adapter_support / max(len(overlap) * 8, 1), 1.0)
            local_graph_score = min(1.0, 0.82 * overlap_ratio + 0.18 * local_recurrence_score)
            graph_score = min(1.0, local_graph_score + 0.09 * shared_source_score + 0.09 * shared_adapter_score)
            matches.append({
                "source_update_id": source_update_id,
                "observation_id": row["observation_id"],
                "root_content_id": row["root_content_id"],
                "composition_content_id": row.get("composition_content_id"),
                "trust_status": row["trust_status"],
                "overlap_count": len(overlap),
                "query_feature_count": len(query_set),
                "overlap_content_ids": overlap[:32],
                "overlap_meta_object_ids": overlap[:32],
                "recurrence_support": local_observation_support,
                "local_occurrence_support": local_occurrence_support,
                "local_recurrence_score": round(local_recurrence_score, 6),
                "shared_source_recurrence_support": shared_source_support,
                "shared_source_occurrence_support": shared_source_occurrences,
                "shared_source_recurrence_score": round(shared_source_score, 6),
                "shared_adapter_recurrence_support": shared_adapter_support,
                "shared_adapter_occurrence_support": shared_adapter_occurrences,
                "shared_adapter_recurrence_score": round(shared_adapter_score, 6),
                "local_graph_score": round(local_graph_score, 6),
                "graph_score": round(graph_score, 6),
                "observed_at_ms": int(row["observed_at_ms"]),
            })
        best: dict[str, dict[str, Any]] = {}
        for row in matches:
            key = row["source_update_id"] or f"observation:{row['observation_id']}"
            current = best.get(key)
            if current is None or (row["graph_score"], row["observed_at_ms"]) > (current["graph_score"], current["observed_at_ms"]):
                best[key] = row
        ranked = sorted(best.values(), key=lambda row: (row["graph_score"], row["recurrence_support"], row["observed_at_ms"]), reverse=True)
        return {
            "schema_version": "meta_graph_search/v3",
            "namespace": str(namespace),
            "query_content_ids": query_ids,
            "matches": ranked,
            "authority": "candidate_ranking_signal_only",
        }


    def search_meta_compositions(
        self,
        *,
        namespace: str,
        query_graph: dict[str, Any],
        limit: int = 128,
        minimum_similarity: float = 0.35,
    ) -> dict[str, Any]:
        """Compare reconstructible candidate compositions, including near quantities.

        SHAKE identities remain exact content references. This path dereferences
        their canonical measured structures and computes similarity over those
        structures; it never uses digest bit distance as a semantic metric.
        """
        from .meta_graph import compare_information_compositions

        row_limit = min(max(int(limit), 1), 512)
        with self.connect() as conn:
            observations = conn.execute(
                """
                SELECT observation_id,source_update_id,root_content_id,composition_content_id,
                       content_ids,meta_object_ids,occurrence_ids,trust_status,observed_at_ms,metadata
                FROM meta_graph_observations
                WHERE namespace=%s AND composition_content_id IS NOT NULL
                  AND jsonb_array_length(occurrence_ids) > 0
                ORDER BY observed_at_ms DESC
                LIMIT %s
                """,
                (str(namespace), row_limit),
            ).fetchall()
            all_content_ids = sorted({
                str(cid)
                for row in observations
                for cid in (row.get("content_ids") or [])
                if str(cid)
            })
            all_occurrence_ids = sorted({
                str(oid)
                for row in observations
                for oid in (row.get("occurrence_ids") or [])
                if str(oid)
            })
            if all_content_ids:
                content_rows = conn.execute(
                    """
                    SELECT semantic_content_id,contract_version,content_type,canonical_body,schema_id
                    FROM semantic_contents WHERE semantic_content_id=ANY(%s)
                    """,
                    (all_content_ids,),
                ).fetchall()
            else:
                content_rows = []
            if all_occurrence_ids:
                occurrence_rows = conn.execute(
                    """
                    SELECT occurrence_id,information_content_id,meta_object_id,descendant_meta_object_ids,
                           locator,ordinal,channel,confidence,sum_contribution,canonical_occurrence
                    FROM meta_object_occurrences WHERE occurrence_id=ANY(%s)
                    """,
                    (all_occurrence_ids,),
                ).fetchall()
            else:
                occurrence_rows = []

        contents_by_id: dict[str, dict[str, Any]] = {}
        for row in content_rows:
            canonical = bytes(row["canonical_body"])
            try:
                body = json.loads(canonical.decode("utf-8"))
            except Exception:
                continue
            contents_by_id[str(row["semantic_content_id"])] = {
                "semantic_content_id": str(row["semantic_content_id"]),
                "contract_version": str(row["contract_version"]),
                "content_type": str(row["content_type"]),
                "body": body,
                "canonical_body": canonical,
                "schema_id": str(row["schema_id"]),
            }
        occurrence_by_id = {str(row["occurrence_id"]): dict(row) for row in occurrence_rows}

        matches: list[dict[str, Any]] = []
        for observation in observations:
            content_ids = [str(v) for v in (observation.get("content_ids") or []) if str(v)]
            occurrence_ids = [str(v) for v in (observation.get("occurrence_ids") or []) if str(v)]
            contents = [contents_by_id[cid] for cid in content_ids if cid in contents_by_id]
            occurrences: list[dict[str, Any]] = []
            for oid in occurrence_ids:
                row = occurrence_by_id.get(oid)
                if not row:
                    continue
                occurrences.append({
                    "occurrence_id": oid,
                    "information_content_id": str(row["information_content_id"]),
                    "meta_object_id": str(row["meta_object_id"]),
                    "descendant_meta_object_ids": [str(v) for v in (row.get("descendant_meta_object_ids") or [])],
                    "locator": row.get("locator") or {},
                    "ordinal": int(row.get("ordinal") or 0),
                    "channel": row.get("channel"),
                    "confidence": row.get("confidence"),
                    "sum_contribution": row.get("sum_contribution") or {},
                    "canonical_occurrence": bytes(row.get("canonical_occurrence") or b""),
                })
            if not occurrences:
                continue
            candidate_graph = {
                "schema_version": "wgrnn_meta_object_composition_observation/v3",
                "contract_version": "v1.6-draft-5.3.18",
                "root_content_id": str(observation["root_content_id"]),
                "composition_content_id": str(observation.get("composition_content_id") or ""),
                "contents": contents,
                "meta_object_ids": [str(v) for v in (observation.get("meta_object_ids") or [])],
                "occurrence_ids": occurrence_ids,
                "occurrences": occurrences,
            }
            comparison = compare_information_compositions(
                query_graph,
                candidate_graph,
                minimum_similarity=float(minimum_similarity),
            )
            similarity = float(comparison.get("similarity") or 0.0)
            if similarity < float(minimum_similarity):
                continue
            matches.append({
                "observation_id": str(observation["observation_id"]),
                "source_update_id": str(observation.get("source_update_id") or ""),
                "root_content_id": str(observation["root_content_id"]),
                "composition_content_id": str(observation.get("composition_content_id") or ""),
                "trust_status": str(observation.get("trust_status") or "candidate"),
                "observed_at_ms": int(observation.get("observed_at_ms") or 0),
                "composition_similarity": round(similarity, 6),
                "matched_occurrence_count": int(comparison.get("matched_occurrence_count") or 0),
                "comparison_matches": list(comparison.get("matches") or [])[:64],
            })
        matches.sort(
            key=lambda row: (row["composition_similarity"], row["matched_occurrence_count"], row["observed_at_ms"]),
            reverse=True,
        )
        return {
            "schema_version": "meta_composition_search/v1",
            "namespace": str(namespace),
            "query_composition_content_id": query_graph.get("composition_content_id"),
            "matches": matches,
            "authority": "candidate_similarity_signal_only",
        }


    def insert_media_profile_bundle(
        self,
        *,
        bundle: dict[str, Any],
        namespace: str,
        observation_id: str | None,
        trust_status: str = "candidate",
        connection: Any | None = None,
        commit: bool = True,
    ) -> dict[str, Any]:
        """Persist a deterministic Merkle-sum media profile and optional PQ signature."""
        from .crypto_primitives import contract_canonical_bytes

        profile_id = str(bundle.get("profile_id") or "")
        profile = dict(bundle.get("profile") or {})
        dag = dict(bundle.get("dag") or {})
        nodes = [dict(row) for row in (dag.get("nodes") or []) if isinstance(row, dict)]
        if not profile_id or not profile or not nodes:
            raise ValueError("media profile bundle is incomplete")
        root_node_id = str(profile.get("merkle_sum_root_node_id") or "")
        if root_node_id != str(dag.get("root_node_id") or ""):
            raise ValueError("media profile root mismatch")
        signed = bundle.get("signed_manifest") if isinstance(bundle.get("signed_manifest"), dict) else None
        suite = str((signed or {}).get("signature_suite") or "") or None
        key_id = str((signed or {}).get("key_id") or "") or None
        verified = bool(bundle.get("signature_verified")) if signed is not None else False

        with (self.connect() if connection is None else nullcontext(connection)) as conn:
            for node in nodes:
                node_id = str(node.get("node_id") or "")
                if not node_id:
                    raise ValueError("media profile node missing node_id")
                conn.execute(
                    """
                    INSERT INTO media_profile_nodes(
                      node_id,schema_version,left_node_id,right_node_id,occurrence_id,canonical_node,sum_vector
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb)
                    ON CONFLICT (node_id) DO NOTHING
                    """,
                    (
                        node_id,
                        str(node.get("schema_version") or "unknown"),
                        str(node.get("left_node_id") or "") or None,
                        str(node.get("right_node_id") or "") or None,
                        str(node.get("occurrence_id") or "") or None,
                        contract_canonical_bytes(node),
                        json.dumps(node.get("sum_vector") or {}, sort_keys=True),
                    ),
                )
            conn.execute(
                """
                INSERT INTO media_profiles(
                  profile_id,namespace,observation_id,information_ref,root_content_id,
                  composition_content_id,merkle_sum_root_node_id,aggregate_schema,sum_vector,
                  profile_body,signed_manifest,signature_suite,signing_key_id,signature_verified,trust_status
                ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s,%s,%s,%s)
                ON CONFLICT (profile_id) DO UPDATE SET
                  signed_manifest=COALESCE(EXCLUDED.signed_manifest, media_profiles.signed_manifest),
                  signature_suite=COALESCE(EXCLUDED.signature_suite, media_profiles.signature_suite),
                  signing_key_id=COALESCE(EXCLUDED.signing_key_id, media_profiles.signing_key_id),
                  signature_verified=media_profiles.signature_verified OR EXCLUDED.signature_verified
                """,
                (
                    profile_id, str(namespace), observation_id, str(profile.get("information_ref") or ""),
                    str(profile.get("root_content_id") or ""), str(profile.get("composition_content_id") or ""),
                    root_node_id, json.dumps(profile.get("aggregate_schema") or {}, sort_keys=True),
                    json.dumps(profile.get("sum_vector") or {}, sort_keys=True), contract_canonical_bytes(profile),
                    json.dumps(signed, sort_keys=True) if signed is not None else None,
                    suite, key_id, verified, str(trust_status),
                ),
            )
            if commit:
                conn.commit()
        return {
            "schema_version": "media_profile_persist_result/v1",
            "profile_id": profile_id,
            "namespace": str(namespace),
            "observation_id": observation_id,
            "root_node_id": root_node_id,
            "node_count": len(nodes),
            "signature_suite": suite,
            "signing_key_id": key_id,
            "signature_verified": verified,
            "trust_status": str(trust_status),
        }

    def get_media_profile_bundle(self, profile_id: str) -> dict[str, Any] | None:
        """Materialize a stored media profile bundle for independent verification."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM media_profiles WHERE profile_id=%s",
                (str(profile_id),),
            ).fetchone()
            if row is None:
                return None
            root_id = str(row["merkle_sum_root_node_id"])
            node_rows = conn.execute(
                """
                WITH RECURSIVE reachable AS (
                  SELECT node_id,left_node_id,right_node_id,canonical_node
                  FROM media_profile_nodes
                  WHERE node_id=%s
                  UNION
                  SELECT child.node_id,child.left_node_id,child.right_node_id,child.canonical_node
                  FROM media_profile_nodes child
                  JOIN reachable parent
                    ON child.node_id=parent.left_node_id OR child.node_id=parent.right_node_id
                )
                SELECT node_id,canonical_node FROM reachable
                """,
                (root_id,),
            ).fetchall()
        profile = json.loads(bytes(row["profile_body"]).decode("utf-8"))
        reachable: dict[str, dict[str, Any]] = {}
        for nrow in node_rows:
            try:
                node = json.loads(bytes(nrow["canonical_node"]).decode("utf-8"))
            except Exception as exc:
                raise ValueError(f"invalid media profile node: {nrow['node_id']}") from exc
            reachable[str(nrow["node_id"])] = node
        if root_id not in reachable:
            raise ValueError(f"missing media profile root node: {root_id}")
        dag = {
            "schema_version": "duotronic_merkle_sum_dag/v1",
            "aggregate_schema": row.get("aggregate_schema") or {},
            "root_node_id": root_id,
            "sum_vector": row.get("sum_vector") or {},
            "leaf_count": sum(1 for node in reachable.values() if node.get("schema_version") == "duotronic_media_profile_leaf/v1"),
            "node_count": len(reachable),
            "nodes": [reachable[key] for key in sorted(reachable)],
        }
        bundle = {
            "schema_version": "duotronic_media_profile_bundle/v1",
            "profile_id": str(row["profile_id"]),
            "namespace": str(row.get("namespace") or ""),
            "observation_id": str(row.get("observation_id") or ""),
            "information_ref": str(row.get("information_ref") or ""),
            "trust_status": str(row.get("trust_status") or "candidate"),
            "profile": profile,
            "dag": dag,
            "signature_verified": bool(row.get("signature_verified")),
        }
        if row.get("signed_manifest"):
            bundle["signed_manifest"] = row["signed_manifest"]
        return bundle


    def get_meta_graph_observation(self, observation_id: str) -> dict[str, Any] | None:
        """Materialize one reconstructible meta-object observation from canonical storage."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM meta_graph_observations WHERE observation_id=%s",
                (str(observation_id),),
            ).fetchone()
            if row is None:
                return None
            content_ids = [str(v) for v in (row.get("content_ids") or []) if str(v)]
            occurrence_ids = [str(v) for v in (row.get("occurrence_ids") or []) if str(v)]
            content_rows = conn.execute(
                """
                SELECT semantic_content_id,contract_version,content_type,canonical_body,schema_id
                FROM semantic_contents WHERE semantic_content_id=ANY(%s)
                """,
                (content_ids,),
            ).fetchall() if content_ids else []
            occurrence_rows = conn.execute(
                """
                SELECT occurrence_id,information_content_id,meta_object_id,descendant_meta_object_ids,
                       locator,ordinal,channel,confidence,sum_contribution,canonical_occurrence
                FROM meta_object_occurrences WHERE occurrence_id=ANY(%s)
                """,
                (occurrence_ids,),
            ).fetchall() if occurrence_ids else []
        contents: list[dict[str, Any]] = []
        root_body: dict[str, Any] = {}
        for crow in content_rows:
            canonical = bytes(crow["canonical_body"])
            body = json.loads(canonical.decode("utf-8"))
            item = {
                "semantic_content_id": str(crow["semantic_content_id"]),
                "contract_version": str(crow["contract_version"]),
                "content_type": str(crow["content_type"]),
                "body": body,
                "canonical_body": canonical,
                "schema_id": str(crow["schema_id"]),
            }
            contents.append(item)
            if str(crow["semantic_content_id"]) == str(row["root_content_id"]):
                root_body = body
        occurrences = [
            {
                "occurrence_id": str(orow["occurrence_id"]),
                "information_content_id": str(orow["information_content_id"]),
                "meta_object_id": str(orow["meta_object_id"]),
                "descendant_meta_object_ids": [str(v) for v in (orow.get("descendant_meta_object_ids") or [])],
                "locator": orow.get("locator") or {},
                "ordinal": int(orow.get("ordinal") or 0),
                "channel": orow.get("channel"),
                "confidence": orow.get("confidence"),
                "sum_contribution": orow.get("sum_contribution") or {},
                "canonical_occurrence": bytes(orow.get("canonical_occurrence") or b""),
            }
            for orow in occurrence_rows
        ]
        occurrences.sort(key=lambda value: (int(value.get("ordinal") or 0), str(value.get("occurrence_id") or "")))
        return {
            "schema_version": "wgrnn_meta_object_composition_observation/v3",
            "contract_version": "v1.6-draft-5.3.18",
            "authority": "candidate_observation_only",
            "observation_id": str(row["observation_id"]),
            "namespace": str(row["namespace"]),
            "source_update_id": str(row.get("source_update_id") or ""),
            "root_content_id": str(row["root_content_id"]),
            "information_ref": str(root_body.get("information_ref") or ""),
            "composition_content_id": str(row.get("composition_content_id") or ""),
            "contents": contents,
            "edges": [],
            "content_ids": content_ids,
            "edge_ids": [str(v) for v in (row.get("edge_ids") or []) if str(v)],
            "meta_object_ids": [str(v) for v in (row.get("meta_object_ids") or []) if str(v)],
            "top_level_meta_object_ids": list(dict.fromkeys(str(v["meta_object_id"]) for v in occurrences)),
            "occurrence_ids": occurrence_ids,
            "occurrences": occurrences,
            "measurement_count": len(occurrences),
            "trust_status": str(row.get("trust_status") or "candidate"),
            "observed_at_ms": int(row.get("observed_at_ms") or 0),
            "metadata": row.get("metadata") or {},
        }

    def insert_information_chain(
        self,
        *,
        chain_id: str,
        chain_body: dict[str, Any],
        profile_ids: list[str],
        chain_ref: str | None = None,
        signed_manifest: dict[str, Any] | None = None,
        signature_verified: bool = False,
        trust_status: str = "candidate",
    ) -> dict[str, Any]:
        """Persist an ordered cross-media pattern witness."""
        from .crypto_primitives import contract_canonical_bytes
        suite = str((signed_manifest or {}).get("signature_suite") or "") or None
        key_id = str((signed_manifest or {}).get("key_id") or "") or None
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO information_chains(
                  chain_id,chain_ref,profile_ids,chain_body,signed_manifest,signature_suite,
                  signing_key_id,signature_verified,trust_status
                ) VALUES(%s,%s,%s::jsonb,%s,%s::jsonb,%s,%s,%s,%s)
                ON CONFLICT (chain_id) DO UPDATE SET
                  chain_ref=COALESCE(EXCLUDED.chain_ref, information_chains.chain_ref),
                  signed_manifest=COALESCE(EXCLUDED.signed_manifest, information_chains.signed_manifest),
                  signature_suite=COALESCE(EXCLUDED.signature_suite, information_chains.signature_suite),
                  signing_key_id=COALESCE(EXCLUDED.signing_key_id, information_chains.signing_key_id),
                  signature_verified=information_chains.signature_verified OR EXCLUDED.signature_verified
                """,
                (
                    str(chain_id), str(chain_ref or "") or None, json.dumps([str(v) for v in profile_ids]),
                    contract_canonical_bytes(chain_body),
                    json.dumps(signed_manifest, sort_keys=True) if signed_manifest is not None else None,
                    suite, key_id, bool(signature_verified), str(trust_status),
                ),
            )
            conn.commit()
        return {
            "schema_version": "information_chain_persist_result/v1",
            "chain_id": str(chain_id),
            "chain_ref": str(chain_ref or "") or None,
            "profile_count": len(profile_ids),
            "signature_suite": suite,
            "signing_key_id": key_id,
            "signature_verified": bool(signature_verified),
            "trust_status": str(trust_status),
        }

    def get_information_chain(self, chain_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM information_chains WHERE chain_id=%s", (str(chain_id),)).fetchone()
        if row is None:
            return None
        return {
            "schema_version": "duotronic_information_chain_bundle/v1",
            "chain_id": str(row["chain_id"]),
            "chain_ref": row.get("chain_ref"),
            "profile_ids": [str(v) for v in (row.get("profile_ids") or [])],
            "chain": json.loads(bytes(row["chain_body"]).decode("utf-8")),
            "signed_manifest": row.get("signed_manifest"),
            "signature_suite": row.get("signature_suite"),
            "signing_key_id": row.get("signing_key_id"),
            "signature_verified": bool(row.get("signature_verified")),
            "trust_status": str(row.get("trust_status") or "candidate"),
        }
