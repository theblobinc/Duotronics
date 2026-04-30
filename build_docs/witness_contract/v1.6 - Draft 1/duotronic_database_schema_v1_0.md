# Duotronic Database Schema v1.0

**Status:** normative implementation contract  
**Version:** database-schema@v1.0  
**Document kind:** PostgreSQL schema plan and storage authority contract  
**Primary purpose:** Define the durable storage model for v1.6 prototypes.

## 1. Storage authority rule

PostgreSQL-compatible relational storage is the canonical transactional store. Milvus-compatible vector stores and Redis-compatible coordination stores may accelerate retrieval and scheduling, but they do not own durable truth.

## 2. Required PostgreSQL schemas

```text
core        versioned DBP envelopes, principals, registry rows
evidence    evidence bundles and source records
witness     candidate and canonical witness facts
math        canonical mathematical objects, claims, domains, status transitions
langlands   Langlands-domain object extensions and bridge witnesses
runtime     interpreter runs, proof-checker runs, runtime artifacts
policy      policy snapshots, decisions, overrides, vetoes
srnn        tasks, oracle jobs, temporal meta objects, witness event links
replay      replay packages, replay attempts, deterministic verification results
audit       append-only audit events, tamper-evidence chain
ops         health snapshots, deployment records, migration runs
```

## 3. Core tables

```sql
CREATE TABLE core.dbp_envelopes (
  envelope_id TEXT PRIMARY KEY,
  dbp_version TEXT NOT NULL,
  object_kind TEXT NOT NULL,
  schema_id TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  canonical_identity_hash TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  payload_json JSONB NOT NULL,
  authority_scope TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  policy_decision_id TEXT,
  replay_identity_ref TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by_principal TEXT NOT NULL,
  UNIQUE(schema_id, schema_version, canonical_identity_hash)
);

CREATE INDEX dbp_envelopes_kind_idx ON core.dbp_envelopes(object_kind);
CREATE INDEX dbp_envelopes_payload_hash_idx ON core.dbp_envelopes(payload_hash);
```

```sql
CREATE TABLE core.principals (
  principal_id TEXT PRIMARY KEY,
  principal_kind TEXT NOT NULL,
  display_name TEXT,
  public_key_ref TEXT,
  scopes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 4. Evidence and witness tables

```sql
CREATE TABLE evidence.evidence_bundles (
  evidence_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_system TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  raw_payload_hash TEXT NOT NULL,
  payload_mime_type TEXT,
  privacy_class TEXT NOT NULL DEFAULT 'unknown',
  transport_status TEXT NOT NULL,
  trust_status TEXT NOT NULL DEFAULT 'raw',
  captured_at TIMESTAMPTZ NOT NULL,
  payload_ref TEXT,
  metadata_json JSONB NOT NULL DEFAULT '{}'::JSONB
);
```

```sql
CREATE TABLE witness.candidate_witnesses (
  witness_id TEXT PRIMARY KEY,
  candidate_kind TEXT NOT NULL,
  source_evidence_ids TEXT[] NOT NULL,
  model_witness_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  proposed_object_json JSONB NOT NULL,
  proposed_canonicalization_json JSONB,
  confidence_json JSONB NOT NULL DEFAULT '{}'::JSONB,
  status TEXT NOT NULL DEFAULT 'candidate',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE witness.canonical_witness_facts (
  canonical_witness_fact_id TEXT PRIMARY KEY,
  source_candidate_witness_ids TEXT[] NOT NULL,
  evidence_bundle_ids TEXT[] NOT NULL,
  profile_id TEXT NOT NULL,
  schema_id TEXT NOT NULL,
  normalizer_id TEXT NOT NULL,
  canonical_identity_hash TEXT NOT NULL,
  canonical_payload_ref TEXT NOT NULL,
  replay_identity_ref TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  truth_status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 5. Mathematical canon tables

```sql
CREATE TABLE math.canonical_math_objects (
  canonical_math_object_id TEXT PRIMARY KEY,
  domain_id TEXT NOT NULL,
  object_kind TEXT NOT NULL,
  object_schema_id TEXT NOT NULL,
  canonical_identity_hash TEXT NOT NULL,
  canonical_payload_json JSONB NOT NULL,
  notation_json JSONB NOT NULL DEFAULT '[]'::JSONB,
  source_witness_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  policy_decision_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(domain_id, object_kind, canonical_identity_hash)
);

CREATE TABLE math.math_claims (
  claim_id TEXT PRIMARY KEY,
  claim_kind TEXT NOT NULL,
  domain_ids TEXT[] NOT NULL,
  object_ids TEXT[] NOT NULL,
  normalized_statement_json JSONB NOT NULL,
  current_status TEXT NOT NULL,
  status_reason TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE math.claim_status_transitions (
  transition_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES math.math_claims(claim_id),
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  evidence_witness_ids TEXT[] NOT NULL,
  policy_decision_id TEXT NOT NULL,
  reviewer_principal_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 6. Langlands tables

```sql
CREATE TABLE langlands.objects (
  langlands_object_id TEXT PRIMARY KEY,
  canonical_math_object_id TEXT NOT NULL REFERENCES math.canonical_math_objects(canonical_math_object_id),
  langlands_kind TEXT NOT NULL,
  base_field_ref TEXT,
  local_global_scope TEXT NOT NULL,
  payload_json JSONB NOT NULL
);

CREATE TABLE langlands.bridge_witnesses (
  bridge_witness_id TEXT PRIMARY KEY,
  source_object_id TEXT NOT NULL,
  target_object_id TEXT NOT NULL,
  bridge_kind TEXT NOT NULL,
  preservation_claims_json JSONB NOT NULL,
  local_factor_checks_json JSONB NOT NULL DEFAULT '[]'::JSONB,
  status TEXT NOT NULL,
  evidence_witness_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  policy_decision_id TEXT NOT NULL
);
```

## 7. Runtime and proof tables

```sql
CREATE TABLE runtime.interpreter_runs (
  interpreter_run_id TEXT PRIMARY KEY,
  language TEXT NOT NULL,
  runtime_profile_id TEXT NOT NULL,
  code_hash TEXT NOT NULL,
  input_artifact_refs TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  output_artifact_refs TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  stdout_hash TEXT,
  stderr_hash TEXT,
  exit_code INTEGER,
  resource_usage_json JSONB NOT NULL DEFAULT '{}'::JSONB,
  sandbox_profile_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  replay_identity_ref TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE runtime.proof_checker_runs (
  checker_run_id TEXT PRIMARY KEY,
  proof_system TEXT NOT NULL,
  proof_authority_profile_id TEXT NOT NULL,
  claim_id TEXT,
  input_hash TEXT NOT NULL,
  result TEXT NOT NULL,
  checker_version TEXT NOT NULL,
  proof_artifact_ref TEXT,
  policy_decision_id TEXT NOT NULL,
  replay_identity_ref TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 8. Policy and SRNN tables

```sql
CREATE TABLE policy.decisions (
  policy_decision_id TEXT PRIMARY KEY,
  policy_snapshot_id TEXT NOT NULL,
  request_json JSONB NOT NULL,
  decision TEXT NOT NULL,
  runtime_mode TEXT NOT NULL,
  rationale TEXT NOT NULL,
  obligations_json JSONB NOT NULL DEFAULT '[]'::JSONB,
  decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE srnn.oracle_jobs (
  job_id TEXT PRIMARY KEY,
  loop_id TEXT NOT NULL DEFAULT 'chrono-main',
  node_id TEXT NOT NULL DEFAULT 'main',
  oracle_id TEXT NOT NULL,
  input_payload_json JSONB NOT NULL,
  input_artifact_ref TEXT,
  replay_identity_ref TEXT,
  status TEXT NOT NULL,
  output_payload_json JSONB,
  output_artifact_ref TEXT,
  witness_event_id TEXT,
  confidence DOUBLE PRECISION,
  latency_ms DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX oracle_jobs_witness_event_idx ON srnn.oracle_jobs(witness_event_id);
```

## 9. Audit chain

Every mutating API call must append an audit row:

```sql
CREATE TABLE audit.events (
  audit_event_id TEXT PRIMARY KEY,
  previous_audit_hash TEXT,
  audit_hash TEXT NOT NULL,
  principal_id TEXT NOT NULL,
  action TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  response_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 10. Milvus and Redis projections

Milvus collections must store only derived embeddings or semantic keys with back references to PostgreSQL IDs. Redis keys must be TTL-bounded unless explicitly marked coordination state. Neither may be the only copy of canonical data.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
