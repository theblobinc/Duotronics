PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

INSERT OR IGNORE INTO wc_schema_generations(generation, applied_at, source_generation, migration_sha256)
VALUES ('v1.6-draft-5.3.5', '2026-07-31T00:00:00-07:00', 'v1.6-draft-5.3.4', NULL);

-- Draft 5.3.5: immutable policy-resolution and compiler-witness bindings.
CREATE TABLE wc_proof_policy_registries_v1 (
  registry_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'proof_policy_registry/v1'),
  governance_key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64),
  signature TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (governance_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_proof_policy_registry_v1_insert_guard BEFORE INSERT ON wc_proof_policy_registries_v1 BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    OR NOT EXISTS (
      SELECT 1 FROM wc_governance_authorities_v1 g
      WHERE g.governance_key_id = NEW.governance_key_id
        AND julianday(NEW.created_at) >= julianday(g.valid_from)
        AND (g.valid_until IS NULL OR julianday(NEW.created_at) < julianday(g.valid_until))
        AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
    ) THEN RAISE(ABORT, 'proof policy registry signature or canonical binding invalid') END;
END;

CREATE TABLE wc_proof_policy_decisions_v1 (
  policy_decision_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'proof_policy_decision/v1'),
  registry_id TEXT NOT NULL,
  canonical_record_json TEXT NOT NULL CHECK (json_valid(canonical_record_json) = 1),
  canonical_record_sha256 TEXT NOT NULL CHECK (length(canonical_record_sha256) = 64),
  status TEXT NOT NULL CHECK (status IN ('active','revoked','expired','superseded')),
  subject_id TEXT NOT NULL,
  operation TEXT NOT NULL CHECK (operation = 'proof_check'),
  compiler_profile_ids_json TEXT NOT NULL CHECK (json_valid(compiler_profile_ids_json) = 1 AND json_type(compiler_profile_ids_json) = 'array'),
  source_bundle_ids_json TEXT NOT NULL CHECK (json_valid(source_bundle_ids_json) = 1 AND json_type(source_bundle_ids_json) = 'array'),
  valid_from TEXT NOT NULL CHECK (julianday(valid_from) IS NOT NULL),
  valid_until TEXT CHECK (valid_until IS NULL OR julianday(valid_until) IS NOT NULL),
  supersedes_policy_decision_id TEXT,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (registry_id) REFERENCES wc_proof_policy_registries_v1(registry_id),
  FOREIGN KEY (supersedes_policy_decision_id) REFERENCES wc_proof_policy_decisions_v1(policy_decision_id)
);

CREATE TRIGGER wc_proof_policy_decision_v1_insert_guard BEFORE INSERT ON wc_proof_policy_decisions_v1 BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.canonical_record_json) <> 1
    OR wc_sha256(NEW.canonical_record_json) <> NEW.canonical_record_sha256
    OR NOT EXISTS (
      SELECT 1 FROM wc_proof_policy_registries_v1 r, json_each(json_extract(r.signed_payload_canonical_json, '$.decisions')) d
      WHERE r.registry_id = NEW.registry_id
        AND json_extract(d.value, '$.policy_decision_id') = NEW.policy_decision_id
        AND json_extract(d.value, '$.canonical_record_sha256') = NEW.canonical_record_sha256
    )
    OR json_extract(NEW.canonical_record_json, '$.policy_decision_id') <> NEW.policy_decision_id
    OR json_extract(NEW.canonical_record_json, '$.status') <> NEW.status
    OR json_extract(NEW.canonical_record_json, '$.subject_id') <> NEW.subject_id
    OR json_extract(NEW.canonical_record_json, '$.operation') <> NEW.operation
    OR json(json_extract(NEW.canonical_record_json, '$.compiler_profile_ids')) <> json(NEW.compiler_profile_ids_json)
    OR json(json_extract(NEW.canonical_record_json, '$.source_bundle_ids')) <> json(NEW.source_bundle_ids_json)
    OR json_extract(NEW.canonical_record_json, '$.valid_from') <> NEW.valid_from
    OR json_extract(NEW.canonical_record_json, '$.valid_until') IS NOT NEW.valid_until
    OR json_extract(NEW.canonical_record_json, '$.supersedes_policy_decision_id') IS NOT NEW.supersedes_policy_decision_id
    THEN RAISE(ABORT, 'proof policy decision fields are not canonically bound') END;
END;

CREATE TABLE wc_lean_compiler_witnesses_v4 (
  lean_compiler_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'lean_compiler_witness/v4'),
  claim_id TEXT NOT NULL,
  compiler_profile_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  policy_decision_sha256 TEXT NOT NULL CHECK (length(policy_decision_sha256) = 64),
  authority_snapshot_id TEXT NOT NULL,
  authority_ledger_high_water_sequence INTEGER NOT NULL CHECK (authority_ledger_high_water_sequence >= 0),
  result TEXT NOT NULL CHECK (result IN ('passed','failed','toolchain_unavailable')),
  statement_binding_confirmed INTEGER NOT NULL CHECK (statement_binding_confirmed IN (0,1)),
  snapshot_verified_immutable INTEGER NOT NULL CHECK (snapshot_verified_immutable IN (0,1)),
  result_channel_isolated INTEGER NOT NULL CHECK (result_channel_isolated IN (0,1)),
  output_limit_exceeded INTEGER NOT NULL CHECK (output_limit_exceeded IN (0,1)),
  requested_controls_json TEXT NOT NULL CHECK (json_valid(requested_controls_json) = 1),
  applied_controls_json TEXT NOT NULL CHECK (json_valid(applied_controls_json) = 1),
  verified_controls_json TEXT NOT NULL CHECK (json_valid(verified_controls_json) = 1),
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64),
  signature TEXT NOT NULL,
  key_id TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (compiler_profile_id) REFERENCES wc_compiler_profiles_v2(compiler_profile_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_proof_policy_decisions_v1(policy_decision_id),
  FOREIGN KEY (authority_snapshot_id) REFERENCES wc_authority_snapshots_v2(snapshot_id),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id)
);

CREATE TRIGGER wc_compiler_witness_v4_insert_guard BEFORE INSERT ON wc_lean_compiler_witnesses_v4 BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    OR NEW.policy_decision_sha256 <> (SELECT canonical_record_sha256 FROM wc_proof_policy_decisions_v1 WHERE policy_decision_id = NEW.policy_decision_id)
    OR NEW.requested_controls_json <> NEW.applied_controls_json
    OR EXISTS (SELECT value FROM json_each(NEW.applied_controls_json) EXCEPT SELECT value FROM json_each(NEW.verified_controls_json))
    OR (NEW.result = 'passed' AND (NEW.statement_binding_confirmed <> 1 OR NEW.snapshot_verified_immutable <> 1 OR NEW.result_channel_isolated <> 1 OR NEW.output_limit_exceeded <> 0))
    OR json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') <> NEW.policy_decision_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_sha256') <> NEW.policy_decision_sha256
    THEN RAISE(ABORT, 'Draft 5.3.5 compiler witness lacks policy or effective-control closure') END;
END;

CREATE TABLE wc_theorem_promotion_gates_v4 (
  promotion_gate_id TEXT PRIMARY KEY,
  compiler_witness_id TEXT NOT NULL,
  authority_snapshot_id TEXT NOT NULL,
  approval_event_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  policy_decision_sha256 TEXT NOT NULL CHECK (length(policy_decision_sha256) = 64),
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (compiler_witness_id) REFERENCES wc_lean_compiler_witnesses_v4(lean_compiler_witness_id),
  FOREIGN KEY (authority_snapshot_id) REFERENCES wc_authority_snapshots_v2(snapshot_id),
  FOREIGN KEY (approval_event_id) REFERENCES wc_authority_events_v1(event_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_proof_policy_decisions_v1(policy_decision_id)
);

CREATE TRIGGER wc_theorem_gate_v4_insert_guard BEFORE INSERT ON wc_theorem_promotion_gates_v4 BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_lean_compiler_witnesses_v4 c
    JOIN wc_proof_policy_decisions_v1 p ON p.policy_decision_id = c.policy_decision_id
    WHERE c.lean_compiler_witness_id = NEW.compiler_witness_id AND c.result = 'passed'
      AND c.policy_decision_id = NEW.policy_decision_id AND c.policy_decision_sha256 = NEW.policy_decision_sha256
      AND p.canonical_record_sha256 = NEW.policy_decision_sha256 AND p.status = 'active'
      AND julianday(NEW.created_at) >= julianday(p.valid_from)
      AND (p.valid_until IS NULL OR julianday(NEW.created_at) < julianday(p.valid_until))
      AND c.authority_snapshot_id = NEW.authority_snapshot_id
  ) THEN RAISE(ABORT, 'theorem gate lacks exact active policy-bound witness') END;
  SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM wc_release_activation_evidence_v1 WHERE package_version = 'v1.6-draft-5.3.5')
    THEN RAISE(ABORT, 'theorem authority remains disabled until every 5.3.5 activation gate passes') END;
END;

CREATE VIEW wc_authoritative_theorems_v4 AS
SELECT g.* FROM wc_theorem_promotion_gates_v4 g
JOIN wc_release_activation_evidence_v1 a ON a.package_version = 'v1.6-draft-5.3.5';

CREATE TRIGGER wc_proof_policy_registry_v1_no_update BEFORE UPDATE ON wc_proof_policy_registries_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_proof_policy_registry_v1_no_delete BEFORE DELETE ON wc_proof_policy_registries_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_proof_policy_decision_v1_no_update BEFORE UPDATE ON wc_proof_policy_decisions_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_proof_policy_decision_v1_no_delete BEFORE DELETE ON wc_proof_policy_decisions_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_witness_v4_no_update BEFORE UPDATE ON wc_lean_compiler_witnesses_v4 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_witness_v4_no_delete BEFORE DELETE ON wc_lean_compiler_witnesses_v4 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_theorem_gate_v4_no_update BEFORE UPDATE ON wc_theorem_promotion_gates_v4 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_theorem_gate_v4_no_delete BEFORE DELETE ON wc_theorem_promotion_gates_v4 BEGIN SELECT RAISE(ABORT, 'append-only'); END;

COMMIT;
