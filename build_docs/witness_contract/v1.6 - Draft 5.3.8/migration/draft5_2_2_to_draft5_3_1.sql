PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS wc_schema_generations (
  generation TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL,
  source_generation TEXT NOT NULL,
  migration_sha256 TEXT
);

INSERT OR IGNORE INTO wc_schema_generations(generation, applied_at, source_generation, migration_sha256)
VALUES ('v1.6-draft-5.3.1', '2026-07-31T00:00:00-07:00', 'v1.6-draft-5.2.2', NULL);

CREATE TABLE IF NOT EXISTS wc_claims_v2 (
  claim_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'evidence_claim/v2'),
  claim_kind TEXT NOT NULL CHECK (claim_kind IN ('atomic','measurement','observation','policy_decision','proof_claim','replay_claim','human_attestation')),
  claim_content_json TEXT NOT NULL CHECK (json_valid(claim_content_json) = 1),
  claim_content_sha256 TEXT NOT NULL CHECK (length(claim_content_sha256) = 64 AND claim_content_sha256 NOT GLOB '*[^0-9a-f]*'),
  theorem_statement TEXT,
  theorem_statement_sha256 TEXT,
  issuer_principal_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (
    (claim_kind = 'proof_claim' AND theorem_statement IS NOT NULL AND length(theorem_statement) > 0 AND length(theorem_statement_sha256) = 64 AND theorem_statement_sha256 NOT GLOB '*[^0-9a-f]*')
    OR
    (claim_kind <> 'proof_claim' AND theorem_statement IS NULL AND theorem_statement_sha256 IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS wc_policy_decisions_v2 (
  policy_decision_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'policy_decision/v2'),
  claim_id TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('allow','deny','escalate')),
  scope TEXT NOT NULL CHECK (scope IN ('theorem_promotion','replay_pass','authority_supersession','computation')),
  authority_principal_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(reason) > 0),
  created_at TEXT NOT NULL,
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id)
);

CREATE TABLE IF NOT EXISTS wc_verifier_principals_v2 (
  verifier_principal_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verifier_principal/v2'),
  key_id TEXT NOT NULL UNIQUE,
  signature_algorithm TEXT NOT NULL CHECK (signature_algorithm IN ('Ed25519','ECDSA-P256-SHA256','RSA-PSS-SHA256')),
  public_key_fingerprint_sha256 TEXT NOT NULL CHECK (length(public_key_fingerprint_sha256) = 64 AND public_key_fingerprint_sha256 NOT GLOB '*[^0-9a-f]*'),
  status TEXT NOT NULL CHECK (status IN ('active','revoked','retired')),
  valid_from TEXT NOT NULL,
  valid_until TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wc_lean_compiler_witnesses_v2 (
  lean_compiler_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'lean_compiler_witness/v2'),
  claim_id TEXT NOT NULL,
  claim_content_sha256 TEXT NOT NULL CHECK (length(claim_content_sha256) = 64 AND claim_content_sha256 NOT GLOB '*[^0-9a-f]*'),
  theorem_statement_sha256 TEXT NOT NULL CHECK (length(theorem_statement_sha256) = 64 AND theorem_statement_sha256 NOT GLOB '*[^0-9a-f]*'),
  proof_artifact_sha256 TEXT NOT NULL CHECK (length(proof_artifact_sha256) = 64 AND proof_artifact_sha256 NOT GLOB '*[^0-9a-f]*'),
  source_tree_sha256 TEXT NOT NULL CHECK (length(source_tree_sha256) = 64 AND source_tree_sha256 NOT GLOB '*[^0-9a-f]*'),
  lakefile_sha256 TEXT NOT NULL CHECK (length(lakefile_sha256) = 64 AND lakefile_sha256 NOT GLOB '*[^0-9a-f]*'),
  build_output_sha256 TEXT NOT NULL CHECK (length(build_output_sha256) = 64 AND build_output_sha256 NOT GLOB '*[^0-9a-f]*'),
  toolchain TEXT NOT NULL,
  command_json TEXT NOT NULL CHECK (json_valid(command_json) = 1 AND json_type(command_json) = 'array' AND json_array_length(command_json) > 0),
  execution_mode TEXT NOT NULL CHECK (execution_mode = 'strict'),
  result TEXT NOT NULL CHECK (result IN ('passed','failed','toolchain_unavailable','failed_static_scan','failed_lake_build','signature_failed')),
  contains_sorry INTEGER NOT NULL CHECK (contains_sorry IN (0,1)),
  contains_admit INTEGER NOT NULL CHECK (contains_admit IN (0,1)),
  unapproved_axiom_count INTEGER NOT NULL CHECK (unapproved_axiom_count >= 0),
  theorem_name TEXT NOT NULL CHECK (length(theorem_name) > 0),
  theorem_status TEXT NOT NULL CHECK (theorem_status IN ('proved','failed','sorry_stub','axiom_dependent','source_hash_mismatch')),
  verifier_principal_id TEXT NOT NULL,
  key_id TEXT NOT NULL,
  signature_algorithm TEXT NOT NULL,
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64 AND signed_payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  signature TEXT NOT NULL CHECK (length(signature) >= 43 AND signature NOT GLOB '*[^A-Za-z0-9_-]*'),
  created_at TEXT NOT NULL,
  CHECK (result <> 'passed' OR (contains_sorry = 0 AND contains_admit = 0 AND unapproved_axiom_count = 0 AND theorem_status = 'proved')),
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (verifier_principal_id) REFERENCES wc_verifier_principals_v2(verifier_principal_id)
);

CREATE TRIGGER IF NOT EXISTS wc_compiler_witness_v2_insert_guard
BEFORE INSERT ON wc_lean_compiler_witnesses_v2
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_claims_v2 c
    WHERE c.claim_id = NEW.claim_id
      AND c.claim_kind = 'proof_claim'
      AND c.claim_content_sha256 = NEW.claim_content_sha256
      AND c.theorem_statement_sha256 = NEW.theorem_statement_sha256
  ) THEN RAISE(ABORT, 'compiler witness claim/theorem hash mismatch') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_verifier_principals_v2 v
    WHERE v.verifier_principal_id = NEW.verifier_principal_id
      AND v.key_id = NEW.key_id
      AND v.signature_algorithm = NEW.signature_algorithm
      AND v.status = 'active'
  ) THEN RAISE(ABORT, 'compiler witness verifier/key is not active or does not match') END;
END;

CREATE TABLE IF NOT EXISTS wc_proof_witnesses_v2 (
  proof_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'proof_witness/v2'),
  claim_id TEXT NOT NULL,
  claim_content_sha256 TEXT NOT NULL,
  theorem_statement_sha256 TEXT NOT NULL,
  proof_artifact_sha256 TEXT NOT NULL,
  lean_compiler_witness_id TEXT NOT NULL,
  theorem_name TEXT NOT NULL,
  theorem_status TEXT NOT NULL CHECK (theorem_status IN ('proved','failed')),
  policy_decision_id TEXT NOT NULL,
  verifier_principal_id TEXT NOT NULL,
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64 AND signed_payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  signature TEXT NOT NULL CHECK (length(signature) >= 43 AND signature NOT GLOB '*[^A-Za-z0-9_-]*'),
  created_at TEXT NOT NULL,
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (lean_compiler_witness_id) REFERENCES wc_lean_compiler_witnesses_v2(lean_compiler_witness_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (verifier_principal_id) REFERENCES wc_verifier_principals_v2(verifier_principal_id)
);

CREATE TRIGGER IF NOT EXISTS wc_proof_witness_v2_insert_guard
BEFORE INSERT ON wc_proof_witnesses_v2
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_lean_compiler_witnesses_v2 l
    WHERE l.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND l.claim_id = NEW.claim_id
      AND l.claim_content_sha256 = NEW.claim_content_sha256
      AND l.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND l.proof_artifact_sha256 = NEW.proof_artifact_sha256
      AND l.theorem_name = NEW.theorem_name
      AND l.verifier_principal_id = NEW.verifier_principal_id
      AND l.result = 'passed'
      AND l.theorem_status = 'proved'
      AND l.contains_sorry = 0
      AND l.contains_admit = 0
      AND l.unapproved_axiom_count = 0
  ) THEN RAISE(ABORT, 'proof witness does not match a passing content-bound compiler witness') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_policy_decisions_v2 p
    WHERE p.policy_decision_id = NEW.policy_decision_id
      AND p.claim_id = NEW.claim_id
      AND p.decision = 'allow'
      AND p.scope = 'theorem_promotion'
  ) THEN RAISE(ABORT, 'proof witness policy is not an exact theorem-promotion allow') END;
END;

CREATE TABLE IF NOT EXISTS wc_non_collapse_transitions_v2 (
  transition_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'non_collapse_transition/v2'),
  claim_id TEXT NOT NULL,
  source_primitive_category TEXT NOT NULL,
  target_primitive_category TEXT NOT NULL,
  transition_kind TEXT NOT NULL CHECK (transition_kind IN ('identity','measurement','observation','promotion','demotion','proof_upgrade','replay_verification','authority_transfer','invalid_attempt')),
  transition_status TEXT NOT NULL CHECK (transition_status IN ('allowed','denied','escalated','requires_external_witness','requires_proof_witness')),
  external_witness_ref TEXT,
  proof_witness_id TEXT,
  policy_decision_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(reason) > 0),
  created_at TEXT NOT NULL,
  CHECK (transition_kind <> 'identity' OR source_primitive_category = target_primitive_category),
  CHECK (transition_status <> 'allowed' OR transition_kind <> 'proof_upgrade' OR (source_primitive_category = 'conjectural' AND target_primitive_category = 'theorem' AND proof_witness_id IS NOT NULL)),
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (proof_witness_id) REFERENCES wc_proof_witnesses_v2(proof_witness_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id)
);

CREATE TRIGGER IF NOT EXISTS wc_non_collapse_v2_insert_guard
BEFORE INSERT ON wc_non_collapse_transitions_v2
WHEN NEW.transition_status = 'allowed' AND NEW.transition_kind = 'proof_upgrade'
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_proof_witnesses_v2 pw
    WHERE pw.proof_witness_id = NEW.proof_witness_id
      AND pw.claim_id = NEW.claim_id
      AND pw.policy_decision_id = NEW.policy_decision_id
      AND pw.theorem_status = 'proved'
  ) THEN RAISE(ABORT, 'non-collapse proof upgrade does not match claim/proof/policy') END;
END;

CREATE TABLE IF NOT EXISTS wc_claim_status_events_v2 (
  status_event_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'claim_status_event/v2'),
  claim_id TEXT NOT NULL,
  source_status TEXT NOT NULL,
  target_status TEXT NOT NULL,
  transition_kind TEXT NOT NULL,
  allowed INTEGER NOT NULL CHECK (allowed IN (0,1)),
  policy_decision_id TEXT NOT NULL,
  proof_witness_id TEXT,
  lean_compiler_witness_id TEXT,
  non_collapse_transition_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (allowed = 0 OR target_status NOT IN ('theorem','proof_verified') OR (source_status = 'conjecture' AND transition_kind = 'prove' AND proof_witness_id IS NOT NULL AND lean_compiler_witness_id IS NOT NULL)),
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (proof_witness_id) REFERENCES wc_proof_witnesses_v2(proof_witness_id),
  FOREIGN KEY (lean_compiler_witness_id) REFERENCES wc_lean_compiler_witnesses_v2(lean_compiler_witness_id),
  FOREIGN KEY (non_collapse_transition_id) REFERENCES wc_non_collapse_transitions_v2(transition_id)
);

CREATE TRIGGER IF NOT EXISTS wc_status_event_v2_insert_guard
BEFORE INSERT ON wc_claim_status_events_v2
WHEN NEW.allowed = 1 AND NEW.target_status IN ('theorem','proof_verified')
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_proof_witnesses_v2 pw
    JOIN wc_lean_compiler_witnesses_v2 lc ON lc.lean_compiler_witness_id = NEW.lean_compiler_witness_id
    JOIN wc_non_collapse_transitions_v2 nc ON nc.transition_id = NEW.non_collapse_transition_id
    WHERE pw.proof_witness_id = NEW.proof_witness_id
      AND pw.claim_id = NEW.claim_id
      AND pw.policy_decision_id = NEW.policy_decision_id
      AND pw.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND lc.claim_id = NEW.claim_id
      AND lc.result = 'passed'
      AND nc.claim_id = NEW.claim_id
      AND nc.policy_decision_id = NEW.policy_decision_id
      AND nc.proof_witness_id = NEW.proof_witness_id
      AND nc.source_primitive_category = 'conjectural'
      AND nc.target_primitive_category = 'theorem'
      AND nc.transition_kind = 'proof_upgrade'
      AND nc.transition_status = 'allowed'
  ) THEN RAISE(ABORT, 'theorem status event authority conjunction mismatch') END;
END;

CREATE TABLE IF NOT EXISTS wc_theorem_promotion_gates_v2 (
  theorem_promotion_gate_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'theorem_promotion_gate/v2'),
  claim_id TEXT NOT NULL,
  claim_content_sha256 TEXT NOT NULL,
  theorem_statement_sha256 TEXT NOT NULL,
  status_event_id TEXT NOT NULL,
  proof_witness_id TEXT NOT NULL,
  lean_compiler_witness_id TEXT NOT NULL,
  non_collapse_transition_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  verifier_principal_id TEXT NOT NULL,
  allowed INTEGER NOT NULL CHECK (allowed IN (0,1)),
  rejection_reason TEXT,
  created_at TEXT NOT NULL,
  CHECK ((allowed = 1 AND rejection_reason IS NULL) OR (allowed = 0 AND rejection_reason IS NOT NULL AND length(rejection_reason) > 0)),
  FOREIGN KEY (claim_id) REFERENCES wc_claims_v2(claim_id),
  FOREIGN KEY (status_event_id) REFERENCES wc_claim_status_events_v2(status_event_id),
  FOREIGN KEY (proof_witness_id) REFERENCES wc_proof_witnesses_v2(proof_witness_id),
  FOREIGN KEY (lean_compiler_witness_id) REFERENCES wc_lean_compiler_witnesses_v2(lean_compiler_witness_id),
  FOREIGN KEY (non_collapse_transition_id) REFERENCES wc_non_collapse_transitions_v2(transition_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (verifier_principal_id) REFERENCES wc_verifier_principals_v2(verifier_principal_id)
);

CREATE TRIGGER IF NOT EXISTS wc_theorem_gate_v2_allowed_insert_guard
BEFORE INSERT ON wc_theorem_promotion_gates_v2
WHEN NEW.allowed = 1
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1
    FROM wc_claims_v2 c
    JOIN wc_policy_decisions_v2 p ON p.policy_decision_id = NEW.policy_decision_id
    JOIN wc_lean_compiler_witnesses_v2 lc ON lc.lean_compiler_witness_id = NEW.lean_compiler_witness_id
    JOIN wc_proof_witnesses_v2 pw ON pw.proof_witness_id = NEW.proof_witness_id
    JOIN wc_non_collapse_transitions_v2 nc ON nc.transition_id = NEW.non_collapse_transition_id
    JOIN wc_claim_status_events_v2 se ON se.status_event_id = NEW.status_event_id
    JOIN wc_verifier_principals_v2 vp ON vp.verifier_principal_id = NEW.verifier_principal_id
    WHERE c.claim_id = NEW.claim_id
      AND c.claim_kind = 'proof_claim'
      AND c.claim_content_sha256 = NEW.claim_content_sha256
      AND c.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND p.claim_id = NEW.claim_id AND p.decision = 'allow' AND p.scope = 'theorem_promotion'
      AND lc.claim_id = NEW.claim_id
      AND lc.claim_content_sha256 = NEW.claim_content_sha256
      AND lc.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND lc.result = 'passed' AND lc.theorem_status = 'proved'
      AND lc.contains_sorry = 0 AND lc.contains_admit = 0 AND lc.unapproved_axiom_count = 0
      AND lc.verifier_principal_id = NEW.verifier_principal_id
      AND pw.claim_id = NEW.claim_id
      AND pw.claim_content_sha256 = NEW.claim_content_sha256
      AND pw.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND pw.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND pw.policy_decision_id = NEW.policy_decision_id
      AND pw.verifier_principal_id = NEW.verifier_principal_id
      AND pw.theorem_status = 'proved'
      AND nc.claim_id = NEW.claim_id
      AND nc.source_primitive_category = 'conjectural'
      AND nc.target_primitive_category = 'theorem'
      AND nc.transition_kind = 'proof_upgrade'
      AND nc.transition_status = 'allowed'
      AND nc.proof_witness_id = NEW.proof_witness_id
      AND nc.policy_decision_id = NEW.policy_decision_id
      AND se.claim_id = NEW.claim_id
      AND se.source_status = 'conjecture'
      AND se.target_status IN ('theorem','proof_verified')
      AND se.transition_kind = 'prove'
      AND se.allowed = 1
      AND se.policy_decision_id = NEW.policy_decision_id
      AND se.proof_witness_id = NEW.proof_witness_id
      AND se.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND se.non_collapse_transition_id = NEW.non_collapse_transition_id
      AND vp.status = 'active'
  ) THEN RAISE(ABORT, 'theorem gate exact authority conjunction failed') END;
END;

CREATE VIEW IF NOT EXISTS wc_authoritative_theorems_v2 AS
SELECT g.theorem_promotion_gate_id, g.claim_id, g.claim_content_sha256,
       g.theorem_statement_sha256, g.proof_witness_id,
       g.lean_compiler_witness_id, g.policy_decision_id, g.created_at
FROM wc_theorem_promotion_gates_v2 g
WHERE g.allowed = 1;

CREATE TABLE IF NOT EXISTS wc_replay_manifests_v2 (
  manifest_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'replay_assumption_manifest/v2'),
  deep_time_intent TEXT NOT NULL,
  assumptions_json TEXT NOT NULL CHECK (json_valid(assumptions_json) = 1 AND json_type(assumptions_json) = 'array' AND json_array_length(assumptions_json) > 0),
  required_assumption_ids_json TEXT NOT NULL CHECK (json_valid(required_assumption_ids_json) = 1 AND json_type(required_assumption_ids_json) = 'array' AND json_array_length(required_assumption_ids_json) > 0),
  failure_mode TEXT NOT NULL,
  manifest_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wc_verification_grammars_v2 (
  grammar_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verification_grammar/v2'),
  instructions_json TEXT NOT NULL CHECK (json_valid(instructions_json) = 1 AND json_type(instructions_json) = 'array' AND json_array_length(instructions_json) > 0),
  grammar_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wc_verification_results_v2 (
  verification_result_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verification_result/v2'),
  grammar_id TEXT NOT NULL,
  grammar_sha256 TEXT NOT NULL,
  manifest_id TEXT NOT NULL,
  manifest_sha256 TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pass','fail','inconclusive','error')),
  executed_instruction_results_json TEXT NOT NULL CHECK (json_valid(executed_instruction_results_json) = 1 AND json_type(executed_instruction_results_json) = 'array' AND json_array_length(executed_instruction_results_json) > 0),
  satisfied_assumption_ids_json TEXT NOT NULL CHECK (json_valid(satisfied_assumption_ids_json) = 1 AND json_type(satisfied_assumption_ids_json) = 'array' AND json_array_length(satisfied_assumption_ids_json) > 0),
  verifier_principal_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (grammar_id) REFERENCES wc_verification_grammars_v2(grammar_id),
  FOREIGN KEY (manifest_id) REFERENCES wc_replay_manifests_v2(manifest_id),
  FOREIGN KEY (verifier_principal_id) REFERENCES wc_verifier_principals_v2(verifier_principal_id)
);

CREATE TRIGGER IF NOT EXISTS wc_verification_result_v2_pass_guard
BEFORE INSERT ON wc_verification_results_v2
WHEN NEW.status = 'pass'
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_verification_grammars_v2 g
    WHERE g.grammar_id = NEW.grammar_id AND g.grammar_sha256 = NEW.grammar_sha256
  ) THEN RAISE(ABORT, 'verification result grammar hash mismatch') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_replay_manifests_v2 m
    WHERE m.manifest_id = NEW.manifest_id AND m.manifest_sha256 = NEW.manifest_sha256
  ) THEN RAISE(ABORT, 'verification result manifest hash mismatch') END;
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM json_each((SELECT required_assumption_ids_json FROM wc_replay_manifests_v2 WHERE manifest_id = NEW.manifest_id)) req
    WHERE NOT EXISTS (
      SELECT 1 FROM json_each(NEW.satisfied_assumption_ids_json) sat WHERE sat.value = req.value
    ) OR NOT EXISTS (
      SELECT 1 FROM json_each((SELECT assumptions_json FROM wc_replay_manifests_v2 WHERE manifest_id = NEW.manifest_id)) a
      WHERE json_extract(a.value, '$.assumption_id') = req.value
        AND json_extract(a.value, '$.status') = 'satisfied'
        AND json_extract(a.value, '$.required_for_pass') = 1
    )
  ) THEN RAISE(ABORT, 'required replay assumption is missing or unsatisfied') END;
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM json_each(NEW.executed_instruction_results_json) r
    WHERE json_extract(r.value, '$.status') <> 'pass'
  ) THEN RAISE(ABORT, 'pass result contains non-pass instruction') END;
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM json_each((SELECT instructions_json FROM wc_verification_grammars_v2 WHERE grammar_id = NEW.grammar_id)) i
    WHERE NOT EXISTS (
      SELECT 1 FROM json_each(NEW.executed_instruction_results_json) r
      WHERE json_extract(r.value, '$.instruction_id') = json_extract(i.value, '$.instruction_id')
        AND json_extract(r.value, '$.status') = 'pass'
    )
  ) THEN RAISE(ABORT, 'pass result does not cover every grammar instruction') END;
END;

CREATE TABLE IF NOT EXISTS wc_authority_supersessions_v1 (
  supersession_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_supersession/v1'),
  record_type TEXT NOT NULL,
  superseded_record_id TEXT NOT NULL,
  replacement_record_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(reason) > 0),
  principal_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  CHECK (superseded_record_id <> replacement_record_id),
  UNIQUE (record_type, superseded_record_id)
);

CREATE TABLE IF NOT EXISTS wc_legacy_authority_quarantine (
  legacy_table TEXT NOT NULL,
  legacy_record_id TEXT NOT NULL,
  trust_status TEXT NOT NULL CHECK (trust_status = 'legacy_untrusted_for_promotion'),
  reason TEXT NOT NULL CHECK (reason = 'missing_v2_content_signature_binding'),
  recorded_at TEXT NOT NULL,
  PRIMARY KEY (legacy_table, legacy_record_id)
);

INSERT OR IGNORE INTO wc_legacy_authority_quarantine
SELECT 'srnn_lean_compiler_witnesses', lean_compiler_witness_id, 'legacy_untrusted_for_promotion', 'missing_v2_content_signature_binding', '2026-07-31T00:00:00-07:00'
FROM srnn_lean_compiler_witnesses;
INSERT OR IGNORE INTO wc_legacy_authority_quarantine
SELECT 'srnn_proof_witnesses', proof_witness_id, 'legacy_untrusted_for_promotion', 'missing_v2_content_signature_binding', '2026-07-31T00:00:00-07:00'
FROM srnn_proof_witnesses;
INSERT OR IGNORE INTO wc_legacy_authority_quarantine
SELECT 'srnn_theorem_promotion_gates', theorem_promotion_gate_id, 'legacy_untrusted_for_promotion', 'missing_v2_content_signature_binding', '2026-07-31T00:00:00-07:00'
FROM srnn_theorem_promotion_gates;

CREATE TRIGGER IF NOT EXISTS wc_claims_v2_no_update BEFORE UPDATE ON wc_claims_v2 BEGIN SELECT RAISE(ABORT, 'wc_claims_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_claims_v2_no_delete BEFORE DELETE ON wc_claims_v2 BEGIN SELECT RAISE(ABORT, 'wc_claims_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_policy_v2_no_update BEFORE UPDATE ON wc_policy_decisions_v2 BEGIN SELECT RAISE(ABORT, 'wc_policy_decisions_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_policy_v2_no_delete BEFORE DELETE ON wc_policy_decisions_v2 BEGIN SELECT RAISE(ABORT, 'wc_policy_decisions_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_verifier_v2_no_update BEFORE UPDATE ON wc_verifier_principals_v2 BEGIN SELECT RAISE(ABORT, 'wc_verifier_principals_v2 is append-only; supersede to rotate or revoke'); END;
CREATE TRIGGER IF NOT EXISTS wc_verifier_v2_no_delete BEFORE DELETE ON wc_verifier_principals_v2 BEGIN SELECT RAISE(ABORT, 'wc_verifier_principals_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_compiler_v2_no_update BEFORE UPDATE ON wc_lean_compiler_witnesses_v2 BEGIN SELECT RAISE(ABORT, 'wc_lean_compiler_witnesses_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_compiler_v2_no_delete BEFORE DELETE ON wc_lean_compiler_witnesses_v2 BEGIN SELECT RAISE(ABORT, 'wc_lean_compiler_witnesses_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_proof_v2_no_update BEFORE UPDATE ON wc_proof_witnesses_v2 BEGIN SELECT RAISE(ABORT, 'wc_proof_witnesses_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_proof_v2_no_delete BEFORE DELETE ON wc_proof_witnesses_v2 BEGIN SELECT RAISE(ABORT, 'wc_proof_witnesses_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_nc_v2_no_update BEFORE UPDATE ON wc_non_collapse_transitions_v2 BEGIN SELECT RAISE(ABORT, 'wc_non_collapse_transitions_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_nc_v2_no_delete BEFORE DELETE ON wc_non_collapse_transitions_v2 BEGIN SELECT RAISE(ABORT, 'wc_non_collapse_transitions_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_status_v2_no_update BEFORE UPDATE ON wc_claim_status_events_v2 BEGIN SELECT RAISE(ABORT, 'wc_claim_status_events_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_status_v2_no_delete BEFORE DELETE ON wc_claim_status_events_v2 BEGIN SELECT RAISE(ABORT, 'wc_claim_status_events_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_gate_v2_no_update BEFORE UPDATE ON wc_theorem_promotion_gates_v2 BEGIN SELECT RAISE(ABORT, 'wc_theorem_promotion_gates_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_gate_v2_no_delete BEFORE DELETE ON wc_theorem_promotion_gates_v2 BEGIN SELECT RAISE(ABORT, 'wc_theorem_promotion_gates_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_replay_manifest_v2_no_update BEFORE UPDATE ON wc_replay_manifests_v2 BEGIN SELECT RAISE(ABORT, 'wc_replay_manifests_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_replay_manifest_v2_no_delete BEFORE DELETE ON wc_replay_manifests_v2 BEGIN SELECT RAISE(ABORT, 'wc_replay_manifests_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_grammar_v2_no_update BEFORE UPDATE ON wc_verification_grammars_v2 BEGIN SELECT RAISE(ABORT, 'wc_verification_grammars_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_grammar_v2_no_delete BEFORE DELETE ON wc_verification_grammars_v2 BEGIN SELECT RAISE(ABORT, 'wc_verification_grammars_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_result_v2_no_update BEFORE UPDATE ON wc_verification_results_v2 BEGIN SELECT RAISE(ABORT, 'wc_verification_results_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_result_v2_no_delete BEFORE DELETE ON wc_verification_results_v2 BEGIN SELECT RAISE(ABORT, 'wc_verification_results_v2 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_supersession_no_update BEFORE UPDATE ON wc_authority_supersessions_v1 BEGIN SELECT RAISE(ABORT, 'wc_authority_supersessions_v1 is append-only'); END;
CREATE TRIGGER IF NOT EXISTS wc_supersession_no_delete BEFORE DELETE ON wc_authority_supersessions_v1 BEGIN SELECT RAISE(ABORT, 'wc_authority_supersessions_v1 is append-only'); END;

COMMIT;
