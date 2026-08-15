-- Additive production schema for the SRNN Runtime Host.
-- The Python Store bootstraps the same tables through app/duotronic_runtime/db.py.
-- Operators who want SQL-first migrations can extract SCHEMA_SQL from db.py or
-- translate it into their migration framework of choice.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

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
  run_id TEXT,
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
  witness_id TEXT,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS evidence_claims_subject_idx ON evidence_claims(subject);
CREATE INDEX IF NOT EXISTS evidence_witnesses_type_idx ON evidence_witnesses(witness_type);
CREATE INDEX IF NOT EXISTS evidence_witnesses_run_idx ON evidence_witnesses(run_id);
