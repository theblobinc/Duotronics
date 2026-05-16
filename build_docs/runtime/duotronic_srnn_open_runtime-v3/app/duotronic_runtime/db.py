from __future__ import annotations

import json
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
        with self.connect() as conn:
            conn.execute(SCHEMA_SQL)
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

    def fetch_recent(self, table: str, limit: int = 20) -> list[dict[str, Any]]:
        if table not in {"runtime_runs", "wgrnn_memory_updates", "nla_activation_witnesses", "memory_cells", "audit_events", "corpus_documents", "corpus_versions", "evidence_claims", "evidence_witnesses", "module_invocations"}:
            raise ValueError("unsupported table")
        with self.connect() as conn:
            order_col = "updated_at" if table == "memory_cells" else "created_at"
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT %s", (min(max(int(limit), 1), 100),)).fetchall()
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
