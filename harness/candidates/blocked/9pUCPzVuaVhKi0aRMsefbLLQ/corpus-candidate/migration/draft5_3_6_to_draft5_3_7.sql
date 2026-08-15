PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

INSERT OR IGNORE INTO wc_schema_generations(generation, applied_at, source_generation, migration_shake256_512)
VALUES ('v1.6-draft-5.3.7', '2026-08-01T00:00:00-07:00', 'v1.6-draft-5.3.6', NULL);

-- v6 is a new-write boundary. v5 records remain replayable under their
-- original semantics and are never silently reclassified.
CREATE TABLE wc_lean_compiler_witnesses_v6 (
  lean_compiler_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'lean_compiler_witness/v6'),
  claim_id TEXT NOT NULL,
  compiler_profile_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  policy_decision_shake256_512 TEXT NOT NULL CHECK (length(policy_decision_shake256_512) = 128),
  authority_snapshot_id TEXT NOT NULL,
  authority_ledger_high_water_sequence INTEGER NOT NULL CHECK (authority_ledger_high_water_sequence >= 0),
  result TEXT NOT NULL CHECK (result IN ('passed','failed','toolchain_unavailable')),
  recursive_dependency_policy_result TEXT NOT NULL CHECK (recursive_dependency_policy_result IN ('passed','failed','not_evaluated')),
  statement_binding_confirmed INTEGER NOT NULL CHECK (statement_binding_confirmed IN (0,1)),
  exact_executed_argv_shake256_512 TEXT NOT NULL CHECK (length(exact_executed_argv_shake256_512) = 128),
  effective_resource_limits_shake256_512 TEXT NOT NULL CHECK (length(effective_resource_limits_shake256_512) = 128),
  domain_file_size_limit INTEGER NOT NULL CHECK (domain_file_size_limit > 0 AND domain_file_size_limit <= 134217728),
  compile_handoff_manifest_shake256_512 TEXT NOT NULL CHECK (length(compile_handoff_manifest_shake256_512) = 128),
  trust_root_attestation_registry_shake256_512 TEXT NOT NULL CHECK (length(trust_root_attestation_registry_shake256_512) = 128),
  requested_controls_json TEXT NOT NULL CHECK (json_valid(requested_controls_json) = 1),
  emitted_controls_json TEXT NOT NULL CHECK (json_valid(emitted_controls_json) = 1),
  accepted_controls_json TEXT NOT NULL CHECK (json_valid(accepted_controls_json) = 1),
  applied_controls_json TEXT NOT NULL CHECK (json_valid(applied_controls_json) = 1),
  measured_controls_json TEXT NOT NULL CHECK (json_valid(measured_controls_json) = 1),
  derived_controls_json TEXT NOT NULL CHECK (json_valid(derived_controls_json) = 1),
  control_evidence_json TEXT NOT NULL CHECK (json_valid(control_evidence_json) = 1),
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_shake256_512 TEXT NOT NULL CHECK (length(signed_payload_shake256_512) = 128),
  signature TEXT NOT NULL,
  key_id TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (compiler_profile_id) REFERENCES wc_compiler_profiles_v2(compiler_profile_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_proof_policy_decisions_v1(policy_decision_id),
  FOREIGN KEY (authority_snapshot_id) REFERENCES wc_authority_snapshots_v2(snapshot_id),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id)
);

CREATE TRIGGER wc_compiler_witness_v6_insert_guard BEFORE INSERT ON wc_lean_compiler_witnesses_v6 BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_shake256_512(NEW.signed_payload_canonical_json) <> NEW.signed_payload_shake256_512
    OR NEW.policy_decision_shake256_512 <> (SELECT canonical_record_shake256_512 FROM wc_proof_policy_decisions_v1 WHERE policy_decision_id = NEW.policy_decision_id)
    OR NEW.requested_controls_json <> NEW.emitted_controls_json
    OR NEW.emitted_controls_json <> NEW.accepted_controls_json
    OR EXISTS (SELECT value FROM json_each(NEW.applied_controls_json) EXCEPT SELECT value FROM json_each(NEW.measured_controls_json))
    OR (NEW.result = 'passed' AND (NEW.statement_binding_confirmed <> 1 OR NEW.recursive_dependency_policy_result <> 'passed'))
    OR json_extract(NEW.signed_payload_canonical_json, '$.schema_version') <> NEW.schema_version
    OR json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') <> NEW.policy_decision_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_shake256_512') <> NEW.policy_decision_shake256_512
    OR json_extract(NEW.signed_payload_canonical_json, '$.normalized_executed_argv_shake256_512') <> NEW.exact_executed_argv_shake256_512
    OR json_extract(NEW.signed_payload_canonical_json, '$.effective_resource_limits_shake256_512') <> NEW.effective_resource_limits_shake256_512
    OR json_extract(NEW.signed_payload_canonical_json, '$.domain_file_size_limit') <> NEW.domain_file_size_limit
    OR json_extract(NEW.signed_payload_canonical_json, '$.handoff_manifest_shake256_512') <> NEW.compile_handoff_manifest_shake256_512
    OR json_extract(NEW.signed_payload_canonical_json, '$.trust_root_attestation_registry_shake256_512') <> NEW.trust_root_attestation_registry_shake256_512
    THEN RAISE(ABORT, 'Draft 5.3.7 compiler witness lacks domain-limit or evidence-state closure') END;
END;

CREATE TABLE wc_theorem_promotion_gates_v6 (
  promotion_gate_id TEXT PRIMARY KEY,
  compiler_witness_id TEXT NOT NULL,
  authority_snapshot_id TEXT NOT NULL,
  approval_event_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  policy_decision_shake256_512 TEXT NOT NULL CHECK (length(policy_decision_shake256_512) = 128),
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (compiler_witness_id) REFERENCES wc_lean_compiler_witnesses_v6(lean_compiler_witness_id),
  FOREIGN KEY (authority_snapshot_id) REFERENCES wc_authority_snapshots_v2(snapshot_id),
  FOREIGN KEY (approval_event_id) REFERENCES wc_authority_events_v1(event_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_proof_policy_decisions_v1(policy_decision_id)
);

CREATE TRIGGER wc_theorem_gate_v6_insert_guard BEFORE INSERT ON wc_theorem_promotion_gates_v6 BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_lean_compiler_witnesses_v6 c
    JOIN wc_proof_policy_decisions_v1 p ON p.policy_decision_id = c.policy_decision_id
    WHERE c.lean_compiler_witness_id = NEW.compiler_witness_id
      AND c.result = 'passed'
      AND c.recursive_dependency_policy_result = 'passed'
      AND c.statement_binding_confirmed = 1
      AND c.policy_decision_id = NEW.policy_decision_id
      AND c.policy_decision_shake256_512 = NEW.policy_decision_shake256_512
      AND p.canonical_record_shake256_512 = NEW.policy_decision_shake256_512
      AND p.status = 'active'
      AND c.authority_snapshot_id = NEW.authority_snapshot_id
  ) THEN RAISE(ABORT, 'theorem gate lacks the exact Draft 5.3.7 authority closure') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_release_activation_evidence_v1
    WHERE package_version = 'v1.6-draft-5.3.7'
  ) THEN RAISE(ABORT, 'theorem authority remains disabled until all eight Draft 5.3.7 external gates pass') END;
END;

CREATE VIEW wc_authoritative_theorems_v6 AS
SELECT g.* FROM wc_theorem_promotion_gates_v6 g
JOIN wc_release_activation_evidence_v1 a
  ON a.package_version = 'v1.6-draft-5.3.7';

CREATE TRIGGER wc_compiler_witness_v6_no_update BEFORE UPDATE ON wc_lean_compiler_witnesses_v6 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_witness_v6_no_delete BEFORE DELETE ON wc_lean_compiler_witnesses_v6 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_theorem_gate_v6_no_update BEFORE UPDATE ON wc_theorem_promotion_gates_v6 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_theorem_gate_v6_no_delete BEFORE DELETE ON wc_theorem_promotion_gates_v6 BEGIN SELECT RAISE(ABORT, 'append-only'); END;

COMMIT;
