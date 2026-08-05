PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

INSERT OR IGNORE INTO wc_schema_generations(generation, applied_at, source_generation, migration_sha256)
VALUES ('v1.6-draft-5.3.2', '2026-07-31T00:00:00-07:00', 'v1.6-draft-5.3.1', NULL);

-- The v2 identifier is retained for wire compatibility, but Draft 5.3.2 makes
-- these statement-binding and Lean-inspection fields mandatory for authority.
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN proof_artifact_relative_path TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN proof_module TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN generated_witness_module_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN generated_witness_module_path TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN exact_build_target TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN compiler_executable_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN axiom_dependencies_json TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN axiom_inspection_complete INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN statement_binding_confirmed INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN warnings_as_errors INTEGER;
ALTER TABLE wc_proof_witnesses_v2 ADD COLUMN key_id TEXT;
ALTER TABLE wc_theorem_promotion_gates_v2 ADD COLUMN key_id TEXT;

CREATE TABLE wc_verifier_keys_v3 (
  key_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verifier_key/v3'),
  verifier_principal_id TEXT NOT NULL,
  signature_algorithm TEXT NOT NULL CHECK (signature_algorithm = 'Ed25519'),
  public_key_base64url TEXT NOT NULL CHECK (length(public_key_base64url) = 43 AND public_key_base64url NOT GLOB '*[^A-Za-z0-9_-]*'),
  public_key_fingerprint_sha256 TEXT NOT NULL CHECK (length(public_key_fingerprint_sha256) = 64 AND public_key_fingerprint_sha256 NOT GLOB '*[^0-9a-f]*'),
  valid_from TEXT NOT NULL CHECK (julianday(valid_from) IS NOT NULL),
  valid_until TEXT CHECK (valid_until IS NULL OR julianday(valid_until) IS NOT NULL),
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  CHECK (valid_until IS NULL OR julianday(valid_until) >= julianday(valid_from)),
  FOREIGN KEY (verifier_principal_id) REFERENCES wc_verifier_principals_v2(verifier_principal_id)
);

CREATE TRIGGER wc_verifier_key_v3_insert_guard
BEFORE INSERT ON wc_verifier_keys_v3
BEGIN
  SELECT CASE WHEN wc_public_key_fingerprint(NEW.public_key_base64url) IS NULL
    OR wc_public_key_fingerprint(NEW.public_key_base64url) <> NEW.public_key_fingerprint_sha256
    THEN RAISE(ABORT, 'verifier key public bytes do not match fingerprint') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_verifier_principals_v2 p
    WHERE p.verifier_principal_id = NEW.verifier_principal_id
      AND p.key_id = NEW.key_id
      AND p.signature_algorithm = NEW.signature_algorithm
      AND p.public_key_fingerprint_sha256 = NEW.public_key_fingerprint_sha256
      AND p.status = 'active'
  ) THEN RAISE(ABORT, 'verifier key does not match its append-only principal registration') END;
END;

CREATE TABLE wc_verifier_key_status_events_v1 (
  key_status_event_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verifier_key_status_event/v1'),
  key_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','revoked','retired','superseded')),
  replacement_key_id TEXT,
  reason TEXT NOT NULL CHECK (length(reason) > 0),
  effective_at TEXT NOT NULL CHECK (julianday(effective_at) IS NOT NULL),
  recorded_at TEXT NOT NULL CHECK (julianday(recorded_at) IS NOT NULL),
  authority_principal_id TEXT NOT NULL,
  CHECK (
    (status = 'superseded' AND replacement_key_id IS NOT NULL AND replacement_key_id <> key_id)
    OR (status <> 'superseded' AND replacement_key_id IS NULL)
  ),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id),
  FOREIGN KEY (replacement_key_id) REFERENCES wc_verifier_keys_v3(key_id)
);

CREATE TRIGGER wc_verifier_key_status_event_insert_guard
BEFORE INSERT ON wc_verifier_key_status_events_v1
BEGIN
  SELECT CASE WHEN NEW.status = 'active' AND EXISTS (
    SELECT 1 FROM wc_verifier_key_status_events_v1 e
    WHERE e.key_id = NEW.key_id
      AND e.status IN ('revoked','retired','superseded')
      AND julianday(e.effective_at) <= julianday(NEW.effective_at)
  ) THEN RAISE(ABORT, 'terminal verifier-key status cannot be reactivated') END;
END;

CREATE VIEW wc_currently_valid_verifiers_v3 AS
SELECT
  k.key_id,
  k.verifier_principal_id,
  k.signature_algorithm,
  k.public_key_base64url,
  k.public_key_fingerprint_sha256,
  k.valid_from,
  k.valid_until
FROM wc_verifier_keys_v3 k
JOIN wc_verifier_principals_v2 p
  ON p.verifier_principal_id = k.verifier_principal_id
 AND p.key_id = k.key_id
WHERE p.status = 'active'
  AND julianday('now') >= julianday(k.valid_from)
  AND (k.valid_until IS NULL OR julianday('now') <= julianday(k.valid_until))
  AND (
    SELECT e.status
    FROM wc_verifier_key_status_events_v1 e
    WHERE e.key_id = k.key_id
      AND julianday(e.effective_at) <= julianday('now')
    ORDER BY julianday(e.effective_at) DESC, julianday(e.recorded_at) DESC, e.key_status_event_id DESC
    LIMIT 1
  ) = 'active'
  AND NOT EXISTS (
    SELECT 1 FROM wc_authority_supersessions_v1 s
    WHERE s.record_type = 'verifier_principal'
      AND s.superseded_record_id = k.verifier_principal_id
  );

CREATE TABLE wc_authority_signature_bindings_v1 (
  signature_binding_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_signature_binding/v1'),
  record_type TEXT NOT NULL CHECK (record_type IN ('lean_compiler_witness','proof_witness')),
  record_id TEXT NOT NULL,
  key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1 AND json_type(signed_payload_canonical_json) = 'object'),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64 AND signed_payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  signature_verified_at TEXT NOT NULL CHECK (julianday(signature_verified_at) IS NOT NULL),
  UNIQUE (record_type, record_id),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id)
);

CREATE TRIGGER wc_signature_binding_canonical_insert_guard
BEFORE INSERT ON wc_authority_signature_bindings_v1
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    THEN RAISE(ABORT, 'signature-binding payload is not canonical JSON') END;
END;

CREATE TRIGGER wc_compiler_signature_binding_insert_guard
BEFORE INSERT ON wc_authority_signature_bindings_v1
WHEN NEW.record_type = 'lean_compiler_witness'
BEGIN
  SELECT CASE WHEN wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'compiler signature-binding payload hash mismatch') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1
    FROM wc_lean_compiler_witnesses_v2 l
    JOIN wc_verifier_keys_v3 k ON k.key_id = NEW.key_id
    WHERE l.lean_compiler_witness_id = NEW.record_id
      AND l.key_id = NEW.key_id
      AND l.verifier_principal_id = k.verifier_principal_id
      AND l.signature_algorithm = k.signature_algorithm
      AND l.signed_payload_sha256 = NEW.signed_payload_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = l.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_compiler_witness_id') = l.lean_compiler_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.claim_id') = l.claim_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.claim_content_sha256') = l.claim_content_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_statement_sha256') = l.theorem_statement_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.proof_artifact_sha256') = l.proof_artifact_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.proof_artifact_relative_path') = l.proof_artifact_relative_path
      AND json_extract(NEW.signed_payload_canonical_json, '$.proof_module') = l.proof_module
      AND json_extract(NEW.signed_payload_canonical_json, '$.source_tree_sha256') = l.source_tree_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lakefile_sha256') = l.lakefile_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.generated_witness_module_sha256') = l.generated_witness_module_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.generated_witness_module_path') = l.generated_witness_module_path
      AND json_extract(NEW.signed_payload_canonical_json, '$.exact_build_target') = l.exact_build_target
      AND json_extract(NEW.signed_payload_canonical_json, '$.compiler_executable_sha256') = l.compiler_executable_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.build_output_sha256') = l.build_output_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.toolchain') = l.toolchain
      AND json(json_extract(NEW.signed_payload_canonical_json, '$.command')) = json(l.command_json)
      AND json_extract(NEW.signed_payload_canonical_json, '$.execution_mode') = l.execution_mode
      AND json_extract(NEW.signed_payload_canonical_json, '$.result') = l.result
      AND json_extract(NEW.signed_payload_canonical_json, '$.contains_sorry') = l.contains_sorry
      AND json_extract(NEW.signed_payload_canonical_json, '$.contains_admit') = l.contains_admit
      AND json_extract(NEW.signed_payload_canonical_json, '$.unapproved_axiom_count') = l.unapproved_axiom_count
      AND json(json_extract(NEW.signed_payload_canonical_json, '$.axiom_dependencies')) = json(l.axiom_dependencies_json)
      AND json_extract(NEW.signed_payload_canonical_json, '$.axiom_inspection_complete') = l.axiom_inspection_complete
      AND json_extract(NEW.signed_payload_canonical_json, '$.statement_binding_confirmed') = l.statement_binding_confirmed
      AND json_extract(NEW.signed_payload_canonical_json, '$.warnings_as_errors') = l.warnings_as_errors
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_name') = l.theorem_name
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_status') = l.theorem_status
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_principal_id') = l.verifier_principal_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.key_id') = l.key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.signature_algorithm') = l.signature_algorithm
      AND json_extract(NEW.signed_payload_canonical_json, '$.created_at') = l.created_at
      AND wc_ed25519_verify(k.public_key_base64url, NEW.signed_payload_canonical_json, l.signature) = 1
  ) THEN RAISE(ABORT, 'compiler signature does not verify over the exact stored authority fields') END;
END;

CREATE TRIGGER wc_proof_signature_binding_insert_guard
BEFORE INSERT ON wc_authority_signature_bindings_v1
WHEN NEW.record_type = 'proof_witness'
BEGIN
  SELECT CASE WHEN wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'proof signature-binding payload hash mismatch') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1
    FROM wc_proof_witnesses_v2 p
    JOIN wc_verifier_keys_v3 k ON k.key_id = NEW.key_id
    WHERE p.proof_witness_id = NEW.record_id
      AND p.key_id = NEW.key_id
      AND p.verifier_principal_id = k.verifier_principal_id
      AND p.signed_payload_sha256 = NEW.signed_payload_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = p.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.proof_witness_id') = p.proof_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.claim_id') = p.claim_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.claim_content_sha256') = p.claim_content_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_statement_sha256') = p.theorem_statement_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.proof_artifact_sha256') = p.proof_artifact_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_compiler_witness_id') = p.lean_compiler_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_name') = p.theorem_name
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_status') = p.theorem_status
      AND json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') = p.policy_decision_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_principal_id') = p.verifier_principal_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.key_id') = p.key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.created_at') = p.created_at
      AND wc_ed25519_verify(k.public_key_base64url, NEW.signed_payload_canonical_json, p.signature) = 1
  ) THEN RAISE(ABORT, 'proof signature does not verify over the exact stored authority fields') END;
END;

DROP TRIGGER wc_theorem_gate_v2_allowed_insert_guard;
DROP VIEW wc_authoritative_theorems_v2;

CREATE TRIGGER wc_theorem_gate_v2_allowed_insert_guard
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
    JOIN wc_currently_valid_verifiers_v3 ev
      ON ev.verifier_principal_id = NEW.verifier_principal_id AND ev.key_id = NEW.key_id
    JOIN wc_authority_signature_bindings_v1 lsb
      ON lsb.record_type = 'lean_compiler_witness' AND lsb.record_id = NEW.lean_compiler_witness_id AND lsb.key_id = NEW.key_id
    JOIN wc_authority_signature_bindings_v1 psb
      ON psb.record_type = 'proof_witness' AND psb.record_id = NEW.proof_witness_id AND psb.key_id = NEW.key_id
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
      AND lc.axiom_inspection_complete = 1
      AND lc.statement_binding_confirmed = 1
      AND lc.warnings_as_errors = 1
      AND lc.generated_witness_module_sha256 IS NOT NULL
      AND lc.generated_witness_module_path = lc.exact_build_target
      AND lc.compiler_executable_sha256 IS NOT NULL
      AND lc.verifier_principal_id = NEW.verifier_principal_id
      AND lc.key_id = NEW.key_id
      AND pw.claim_id = NEW.claim_id
      AND pw.claim_content_sha256 = NEW.claim_content_sha256
      AND pw.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND pw.lean_compiler_witness_id = NEW.lean_compiler_witness_id
      AND pw.policy_decision_id = NEW.policy_decision_id
      AND pw.verifier_principal_id = NEW.verifier_principal_id
      AND pw.key_id = NEW.key_id
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
      AND julianday(NEW.created_at) IS NOT NULL
      AND julianday(NEW.created_at) >= julianday(ev.valid_from)
      AND (ev.valid_until IS NULL OR julianday(NEW.created_at) <= julianday(ev.valid_until))
      AND julianday(lc.created_at) >= julianday(ev.valid_from)
      AND (ev.valid_until IS NULL OR julianday(lc.created_at) <= julianday(ev.valid_until))
      AND julianday(pw.created_at) >= julianday(ev.valid_from)
      AND (ev.valid_until IS NULL OR julianday(pw.created_at) <= julianday(ev.valid_until))
      AND julianday(lsb.signature_verified_at) <= julianday(NEW.created_at)
      AND julianday(psb.signature_verified_at) <= julianday(NEW.created_at)
      AND (
        SELECT e.status FROM wc_verifier_key_status_events_v1 e
        WHERE e.key_id = NEW.key_id AND julianday(e.effective_at) <= julianday(NEW.created_at)
        ORDER BY julianday(e.effective_at) DESC, julianday(e.recorded_at) DESC, e.key_status_event_id DESC
        LIMIT 1
      ) = 'active'
  ) THEN RAISE(ABORT, 'theorem gate exact authority, signature, statement-binding, or effective-key conjunction failed') END;
END;

CREATE VIEW wc_authoritative_theorems_v2 AS
SELECT
  g.theorem_promotion_gate_id,
  g.claim_id,
  g.claim_content_sha256,
  g.theorem_statement_sha256,
  g.proof_witness_id,
  g.lean_compiler_witness_id,
  g.policy_decision_id,
  g.verifier_principal_id,
  g.key_id,
  g.created_at
FROM wc_theorem_promotion_gates_v2 g
JOIN wc_currently_valid_verifiers_v3 ev
  ON ev.verifier_principal_id = g.verifier_principal_id AND ev.key_id = g.key_id
JOIN wc_authority_signature_bindings_v1 lsb
  ON lsb.record_type = 'lean_compiler_witness' AND lsb.record_id = g.lean_compiler_witness_id AND lsb.key_id = g.key_id
JOIN wc_authority_signature_bindings_v1 psb
  ON psb.record_type = 'proof_witness' AND psb.record_id = g.proof_witness_id AND psb.key_id = g.key_id
WHERE g.allowed = 1
  AND NOT EXISTS (
    SELECT 1 FROM wc_authority_supersessions_v1 s
    WHERE s.record_type = 'promotion_gate'
      AND s.superseded_record_id = g.theorem_promotion_gate_id
  );

CREATE TRIGGER wc_verifier_keys_v3_no_update BEFORE UPDATE ON wc_verifier_keys_v3 BEGIN SELECT RAISE(ABORT, 'wc_verifier_keys_v3 is append-only'); END;
CREATE TRIGGER wc_verifier_keys_v3_no_delete BEFORE DELETE ON wc_verifier_keys_v3 BEGIN SELECT RAISE(ABORT, 'wc_verifier_keys_v3 is append-only'); END;
CREATE TRIGGER wc_key_status_v1_no_update BEFORE UPDATE ON wc_verifier_key_status_events_v1 BEGIN SELECT RAISE(ABORT, 'wc_verifier_key_status_events_v1 is append-only'); END;
CREATE TRIGGER wc_key_status_v1_no_delete BEFORE DELETE ON wc_verifier_key_status_events_v1 BEGIN SELECT RAISE(ABORT, 'wc_verifier_key_status_events_v1 is append-only'); END;
CREATE TRIGGER wc_signature_binding_v1_no_update BEFORE UPDATE ON wc_authority_signature_bindings_v1 BEGIN SELECT RAISE(ABORT, 'wc_authority_signature_bindings_v1 is append-only'); END;
CREATE TRIGGER wc_signature_binding_v1_no_delete BEFORE DELETE ON wc_authority_signature_bindings_v1 BEGIN SELECT RAISE(ABORT, 'wc_authority_signature_bindings_v1 is append-only'); END;

COMMIT;
