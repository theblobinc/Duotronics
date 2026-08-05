PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

INSERT OR IGNORE INTO wc_schema_generations(generation, applied_at, source_generation, migration_sha256)
VALUES ('v1.6-draft-5.3.4', '2026-07-31T00:00:00-07:00', 'v1.6-draft-5.3.3', NULL);

CREATE TABLE wc_governance_action_scope_map_v1 (
  event_type TEXT PRIMARY KEY,
  required_scope TEXT NOT NULL UNIQUE,
  target_type TEXT NOT NULL
);

INSERT INTO wc_governance_action_scope_map_v1(event_type, required_scope, target_type) VALUES
  ('verifier_key_activate','verifier_key_activate','verifier_key'),
  ('verifier_key_retire','verifier_key_retire','verifier_key'),
  ('verifier_key_revoke','verifier_key_revoke','verifier_key'),
  ('compiler_profile_activate','compiler_profile_activate','compiler_profile'),
  ('compiler_profile_revoke','compiler_profile_revoke','compiler_profile'),
  ('promotion_gate_approve','promotion_gate_approve','promotion_gate'),
  ('promotion_gate_withdraw','promotion_gate_withdraw','promotion_gate'),
  ('authority_record_supersede','authority_record_supersede','authority_record'),
  ('authority_snapshot_create','authority_snapshot_create','authority_snapshot'),
  ('authority_snapshot_supersede','authority_snapshot_supersede','authority_snapshot'),
  ('backdated_event_authorize','backdated_event_authorize','authority_event');

CREATE TABLE wc_governance_authorization_witnesses_v2 (
  authorization_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'governance_authorization_witness/v2'),
  action_scope TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  principal_id TEXT NOT NULL,
  governance_policy_version TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision = 'allow'),
  valid_from TEXT NOT NULL CHECK (julianday(valid_from) IS NOT NULL),
  valid_until TEXT CHECK (valid_until IS NULL OR julianday(valid_until) IS NOT NULL),
  signer_key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64 AND signed_payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  signature TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  CHECK (valid_until IS NULL OR julianday(valid_from) < julianday(valid_until)),
  FOREIGN KEY (signer_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_governance_authorization_v2_insert_guard
BEFORE INSERT ON wc_governance_authorization_witnesses_v2
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'governance authorization is not canonical and hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    WHERE g.governance_key_id = NEW.signer_key_id
      AND julianday(NEW.created_at) >= julianday(g.valid_from)
      AND (g.valid_until IS NULL OR julianday(NEW.created_at) < julianday(g.valid_until))
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = NEW.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') = NEW.authorization_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.action_scope') = NEW.action_scope
      AND json_extract(NEW.signed_payload_canonical_json, '$.target_type') = NEW.target_type
      AND json_extract(NEW.signed_payload_canonical_json, '$.target_id') = NEW.target_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.principal_id') = NEW.principal_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.governance_policy_version') = NEW.governance_policy_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.decision') = NEW.decision
      AND json_extract(NEW.signed_payload_canonical_json, '$.valid_from') = NEW.valid_from
      AND json_extract(NEW.signed_payload_canonical_json, '$.valid_until') IS NEW.valid_until
      AND json_extract(NEW.signed_payload_canonical_json, '$.signer_key_id') = NEW.signer_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.created_at') = NEW.created_at
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'governance authorization signature or key validity failed') END;
END;

CREATE TABLE wc_authority_record_index_v1 (
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  recorded_at TEXT NOT NULL CHECK (julianday(recorded_at) IS NOT NULL),
  PRIMARY KEY (record_type, record_id)
);

INSERT OR IGNORE INTO wc_authority_record_index_v1(record_type, record_id, recorded_at)
  SELECT 'verifier_key', key_id, created_at FROM wc_verifier_keys_v3;
INSERT OR IGNORE INTO wc_authority_record_index_v1(record_type, record_id, recorded_at)
  SELECT 'promotion_gate', theorem_promotion_gate_id, created_at FROM wc_theorem_promotion_gates_v2;
INSERT OR IGNORE INTO wc_authority_record_index_v1(record_type, record_id, recorded_at)
  SELECT 'compiler_witness', lean_compiler_witness_id, created_at FROM wc_lean_compiler_witnesses_v2;
INSERT OR IGNORE INTO wc_authority_record_index_v1(record_type, record_id, recorded_at)
  SELECT 'proof_witness', proof_witness_id, created_at FROM wc_proof_witnesses_v2;

CREATE TRIGGER wc_verifier_key_v3_index_534
AFTER INSERT ON wc_verifier_keys_v3
BEGIN
  INSERT INTO wc_authority_record_index_v1 VALUES ('verifier_key', NEW.key_id, NEW.created_at);
END;

CREATE TABLE wc_compiler_profiles_v2 (
  compiler_profile_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'compiler_profile/v2'),
  registry_sha256 TEXT NOT NULL CHECK (length(registry_sha256) = 64),
  oci_image_digest TEXT NOT NULL CHECK (oci_image_digest GLOB 'sha256:*'),
  oci_runtime_sha256 TEXT NOT NULL CHECK (length(oci_runtime_sha256) = 64),
  oci_runtime_version TEXT NOT NULL,
  verifier_executable_sha256 TEXT NOT NULL CHECK (length(verifier_executable_sha256) = 64),
  lean_executable_sha256 TEXT NOT NULL CHECK (length(lean_executable_sha256) = 64),
  lake_executable_sha256 TEXT NOT NULL CHECK (length(lake_executable_sha256) = 64),
  lean_stdlib_tree_sha256 TEXT NOT NULL CHECK (length(lean_stdlib_tree_sha256) = 64),
  dependency_closure_sha256 TEXT NOT NULL CHECK (length(dependency_closure_sha256) = 64),
  sandbox_policy_sha256 TEXT NOT NULL CHECK (length(sandbox_policy_sha256) = 64),
  verifier_source_revision TEXT NOT NULL,
  verifier_build_attestation_id TEXT NOT NULL,
  verifier_result_signer_key_id TEXT NOT NULL,
  verifier_result_public_key_base64url TEXT NOT NULL CHECK (length(verifier_result_public_key_base64url) = 43),
  valid_from TEXT NOT NULL CHECK (julianday(valid_from) IS NOT NULL),
  valid_until TEXT CHECK (valid_until IS NULL OR julianday(valid_until) IS NOT NULL),
  governance_key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64),
  signature TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  CHECK (valid_until IS NULL OR julianday(valid_from) < julianday(valid_until)),
  FOREIGN KEY (governance_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_compiler_profile_v2_insert_guard
BEFORE INSERT ON wc_compiler_profiles_v2
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'compiler profile is not canonical and hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    WHERE g.governance_key_id = NEW.governance_key_id
      AND julianday(NEW.created_at) >= julianday(g.valid_from)
      AND (g.valid_until IS NULL OR julianday(NEW.created_at) < julianday(g.valid_until))
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = NEW.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.compiler_profile_id') = NEW.compiler_profile_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.registry_sha256') = NEW.registry_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.oci_image_digest') = NEW.oci_image_digest
      AND json_extract(NEW.signed_payload_canonical_json, '$.oci_runtime_sha256') = NEW.oci_runtime_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.oci_runtime_version') = NEW.oci_runtime_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_executable_sha256') = NEW.verifier_executable_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_executable_sha256') = NEW.lean_executable_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lake_executable_sha256') = NEW.lake_executable_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_stdlib_tree_sha256') = NEW.lean_stdlib_tree_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.dependency_closure_sha256') = NEW.dependency_closure_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.sandbox_policy_sha256') = NEW.sandbox_policy_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_source_revision') = NEW.verifier_source_revision
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_build_attestation_id') = NEW.verifier_build_attestation_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_result_signer_key_id') = NEW.verifier_result_signer_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_result_public_key_base64url') = NEW.verifier_result_public_key_base64url
      AND json_extract(NEW.signed_payload_canonical_json, '$.valid_from') = NEW.valid_from
      AND json_extract(NEW.signed_payload_canonical_json, '$.valid_until') IS NEW.valid_until
      AND json_extract(NEW.signed_payload_canonical_json, '$.governance_key_id') = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.created_at') = NEW.created_at
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'compiler profile governance signature or field binding failed') END;
END;

CREATE TRIGGER wc_compiler_profile_v2_index
AFTER INSERT ON wc_compiler_profiles_v2
BEGIN
  INSERT INTO wc_authority_record_index_v1 VALUES ('compiler_profile', NEW.compiler_profile_id, NEW.created_at);
END;

CREATE TABLE wc_lean_compiler_witnesses_v3 (
  lean_compiler_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'lean_compiler_witness/v3'),
  semantic_witness_content_id TEXT NOT NULL,
  claim_id TEXT NOT NULL,
  claim_content_sha256 TEXT NOT NULL CHECK (length(claim_content_sha256) = 64),
  theorem_statement_sha256 TEXT NOT NULL CHECK (length(theorem_statement_sha256) = 64),
  immutable_snapshot_id TEXT NOT NULL CHECK (immutable_snapshot_id GLOB 'sha256:*'),
  immutable_snapshot_tree_sha256 TEXT NOT NULL CHECK (length(immutable_snapshot_tree_sha256) = 64),
  proof_artifact_relative_path TEXT NOT NULL CHECK (proof_artifact_relative_path NOT LIKE '/%' AND proof_artifact_relative_path NOT LIKE '%..%' AND proof_artifact_relative_path NOT LIKE '%\%'),
  proof_artifact_sha256 TEXT NOT NULL CHECK (length(proof_artifact_sha256) = 64),
  generated_binding_module_sha256 TEXT NOT NULL CHECK (length(generated_binding_module_sha256) = 64),
  generated_binding_request_sha256 TEXT NOT NULL CHECK (length(generated_binding_request_sha256) = 64),
  compiler_profile_id TEXT NOT NULL,
  verifier_result_payload_sha256 TEXT NOT NULL CHECK (length(verifier_result_payload_sha256) = 64),
  verifier_result_signer_key_id TEXT NOT NULL,
  verifier_result_signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(verifier_result_signed_payload_canonical_json) = 1),
  verifier_result_signature TEXT NOT NULL,
  expected_type_expression_hash TEXT NOT NULL CHECK (length(expected_type_expression_hash) = 64),
  actual_type_expression_hash TEXT NOT NULL CHECK (length(actual_type_expression_hash) = 64),
  axiom_set_sha256 TEXT NOT NULL CHECK (length(axiom_set_sha256) = 64),
  result TEXT NOT NULL CHECK (result IN ('passed','failed','toolchain_unavailable')),
  theorem_status TEXT NOT NULL CHECK (theorem_status IN ('proved','failed','sorry_stub','axiom_dependent')),
  statement_binding_confirmed INTEGER NOT NULL CHECK (statement_binding_confirmed IN (0,1)),
  snapshot_verified_immutable INTEGER NOT NULL CHECK (snapshot_verified_immutable IN (0,1)),
  result_channel_isolated INTEGER NOT NULL CHECK (result_channel_isolated IN (0,1)),
  authority_snapshot_id TEXT NOT NULL,
  authority_ledger_high_water_sequence INTEGER NOT NULL CHECK (authority_ledger_high_water_sequence >= 0),
  key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64),
  signature TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (compiler_profile_id) REFERENCES wc_compiler_profiles_v2(compiler_profile_id),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id)
);

CREATE TRIGGER wc_compiler_witness_v3_insert_guard
BEFORE INSERT ON wc_lean_compiler_witnesses_v3
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'compiler witness v3 is not canonical and hash-bound') END;
  SELECT CASE WHEN NEW.result = 'passed' AND (
    NEW.theorem_status <> 'proved' OR NEW.statement_binding_confirmed <> 1
    OR NEW.snapshot_verified_immutable <> 1 OR NEW.result_channel_isolated <> 1
    OR NEW.expected_type_expression_hash <> NEW.actual_type_expression_hash)
    THEN RAISE(ABORT, 'passing compiler witness lacks mandatory 5.3.4 closure') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_verifier_keys_v3 k
    WHERE k.key_id = NEW.key_id
      AND wc_ed25519_verify(k.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'compiler witness signature invalid') END;
  SELECT CASE WHEN json_extract(NEW.signed_payload_canonical_json, '$.schema_version') <> NEW.schema_version
    OR json_extract(NEW.signed_payload_canonical_json, '$.lean_compiler_witness_id') <> NEW.lean_compiler_witness_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.semantic_witness_content_id') <> NEW.semantic_witness_content_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.claim_id') <> NEW.claim_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.claim_content_sha256') <> NEW.claim_content_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.theorem_statement_sha256') <> NEW.theorem_statement_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.immutable_snapshot_id') <> NEW.immutable_snapshot_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.immutable_snapshot_tree_sha256') <> NEW.immutable_snapshot_tree_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.proof_artifact_relative_path') <> NEW.proof_artifact_relative_path
    OR json_extract(NEW.signed_payload_canonical_json, '$.proof_artifact_sha256') <> NEW.proof_artifact_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.generated_binding_module_sha256') <> NEW.generated_binding_module_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.generated_binding_request_sha256') <> NEW.generated_binding_request_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.compiler_profile_id') <> NEW.compiler_profile_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.verifier_result_payload_sha256') <> NEW.verifier_result_payload_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.verifier_result_signer_key_id') <> NEW.verifier_result_signer_key_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.verifier_result_signature') <> NEW.verifier_result_signature
    OR json_extract(NEW.signed_payload_canonical_json, '$.expected_type_expression_hash') <> NEW.expected_type_expression_hash
    OR json_extract(NEW.signed_payload_canonical_json, '$.actual_type_expression_hash') <> NEW.actual_type_expression_hash
    OR json_extract(NEW.signed_payload_canonical_json, '$.axiom_set_sha256') <> NEW.axiom_set_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.result') <> NEW.result
    OR json_extract(NEW.signed_payload_canonical_json, '$.theorem_status') <> NEW.theorem_status
    OR json_extract(NEW.signed_payload_canonical_json, '$.statement_binding_confirmed') <> NEW.statement_binding_confirmed
    OR json_extract(NEW.signed_payload_canonical_json, '$.snapshot_verified_immutable') <> NEW.snapshot_verified_immutable
    OR json_extract(NEW.signed_payload_canonical_json, '$.result_channel_isolated') <> NEW.result_channel_isolated
    OR json_extract(NEW.signed_payload_canonical_json, '$.authority_snapshot_id') <> NEW.authority_snapshot_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.authority_ledger_high_water_sequence') <> NEW.authority_ledger_high_water_sequence
    OR json_extract(NEW.signed_payload_canonical_json, '$.key_id') <> NEW.key_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.created_at') <> NEW.created_at
    THEN RAISE(ABORT, 'compiler witness signature does not bind the authority columns') END;
  SELECT CASE WHEN NEW.result = 'passed' AND (wc_is_canonical_json(NEW.verifier_result_signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.verifier_result_signed_payload_canonical_json) <> NEW.verifier_result_payload_sha256
    OR NOT EXISTS (
      SELECT 1 FROM wc_compiler_profiles_v2 p
      WHERE p.compiler_profile_id = NEW.compiler_profile_id
        AND p.verifier_result_signer_key_id = NEW.verifier_result_signer_key_id
        AND julianday(NEW.created_at) >= julianday(p.valid_from)
        AND (p.valid_until IS NULL OR julianday(NEW.created_at) < julianday(p.valid_until))
        AND wc_ed25519_verify(p.verifier_result_public_key_base64url, NEW.verifier_result_signed_payload_canonical_json, NEW.verifier_result_signature) = 1
    )) THEN RAISE(ABORT, 'trusted verifier result signature or profile binding invalid') END;
END;

CREATE TRIGGER wc_compiler_witness_v3_index
AFTER INSERT ON wc_lean_compiler_witnesses_v3
BEGIN
  INSERT INTO wc_authority_record_index_v1 VALUES ('compiler_witness', NEW.lean_compiler_witness_id, NEW.created_at);
END;

CREATE TABLE wc_authority_events_v1 (
  authority_event_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  schema_version TEXT NOT NULL CHECK (schema_version = 'governance_event/v1'),
  event_type TEXT NOT NULL,
  action_scope TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  effective_at TEXT NOT NULL CHECK (julianday(effective_at) IS NOT NULL),
  recorded_at TEXT NOT NULL CHECK (julianday(recorded_at) IS NOT NULL),
  reason_code TEXT NOT NULL,
  rationale TEXT NOT NULL,
  governance_policy_version TEXT NOT NULL,
  authorization_witness_id TEXT NOT NULL,
  signer_key_id TEXT NOT NULL,
  is_backdated INTEGER NOT NULL CHECK (is_backdated IN (0,1)),
  correction_reason TEXT,
  prior_affected_snapshot_ids_json TEXT NOT NULL CHECK (json_valid(prior_affected_snapshot_ids_json) = 1 AND json_type(prior_affected_snapshot_ids_json) = 'array'),
  correction_mode TEXT NOT NULL CHECK (correction_mode IN ('not_applicable','prospective_only','requires_snapshot_supersession')),
  backdate_authorization_witness_id TEXT,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  canonical_payload_sha256 TEXT NOT NULL CHECK (length(canonical_payload_sha256) = 64),
  signature TEXT NOT NULL,
  FOREIGN KEY (authorization_witness_id) REFERENCES wc_governance_authorization_witnesses_v2(authorization_witness_id),
  FOREIGN KEY (backdate_authorization_witness_id) REFERENCES wc_governance_authorization_witnesses_v2(authorization_witness_id),
  FOREIGN KEY (signer_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_authority_event_v1_insert_guard
BEFORE INSERT ON wc_authority_events_v1
BEGIN
  SELECT CASE WHEN NEW.authority_event_sequence <> COALESCE((SELECT max(authority_event_sequence) + 1 FROM wc_authority_events_v1), 1)
    THEN RAISE(ABORT, 'authority event sequence is not the next monotonic value') END;
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.canonical_payload_sha256
    THEN RAISE(ABORT, 'authority event is not canonical and hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_action_scope_map_v1 m
    JOIN wc_governance_authorization_witnesses_v2 a ON a.authorization_witness_id = NEW.authorization_witness_id
    JOIN wc_governance_authorities_v1 g ON g.governance_key_id = NEW.signer_key_id
    WHERE m.event_type = NEW.event_type AND m.required_scope = NEW.action_scope
      AND (m.target_type = NEW.target_type OR (m.target_type = 'authority_record' AND NEW.target_type <> ''))
      AND a.action_scope = NEW.action_scope AND a.target_type = NEW.target_type AND a.target_id = NEW.target_id
      AND a.governance_policy_version = NEW.governance_policy_version AND a.decision = 'allow'
      AND julianday(NEW.effective_at) >= julianday(a.valid_from)
      AND (a.valid_until IS NULL OR julianday(NEW.effective_at) < julianday(a.valid_until))
      AND a.signer_key_id = NEW.signer_key_id
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'authority event scope, authorization, or signature invalid') END;
  SELECT CASE WHEN NEW.event_type NOT IN ('authority_snapshot_create','promotion_gate_approve') AND NOT EXISTS (
    SELECT 1 FROM wc_authority_record_index_v1 r WHERE r.record_type = NEW.target_type AND r.record_id = NEW.target_id
  ) THEN RAISE(ABORT, 'authority event target does not exist with the declared type') END;
  SELECT CASE WHEN json_extract(NEW.signed_payload_canonical_json, '$.authority_event_sequence') <> NEW.authority_event_sequence
    OR json_extract(NEW.signed_payload_canonical_json, '$.event_id') <> NEW.event_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.event_type') <> NEW.event_type
    OR json_extract(NEW.signed_payload_canonical_json, '$.action_scope') <> NEW.action_scope
    OR json_extract(NEW.signed_payload_canonical_json, '$.target_type') <> NEW.target_type
    OR json_extract(NEW.signed_payload_canonical_json, '$.target_id') <> NEW.target_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.effective_at') <> NEW.effective_at
    OR json_extract(NEW.signed_payload_canonical_json, '$.recorded_at') <> NEW.recorded_at
    OR json_extract(NEW.signed_payload_canonical_json, '$.reason_code') <> NEW.reason_code
    OR json_extract(NEW.signed_payload_canonical_json, '$.rationale') <> NEW.rationale
    OR json_extract(NEW.signed_payload_canonical_json, '$.governance_policy_version') <> NEW.governance_policy_version
    OR json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') <> NEW.authorization_witness_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.signer_key_id') <> NEW.signer_key_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.is_backdated') <> NEW.is_backdated
    OR json_extract(NEW.signed_payload_canonical_json, '$.correction_reason') IS NOT NEW.correction_reason
    OR json(json_extract(NEW.signed_payload_canonical_json, '$.prior_affected_snapshot_ids')) <> json(NEW.prior_affected_snapshot_ids_json)
    OR json_extract(NEW.signed_payload_canonical_json, '$.correction_mode') <> NEW.correction_mode
    OR json_extract(NEW.signed_payload_canonical_json, '$.backdate_authorization_witness_id') IS NOT NEW.backdate_authorization_witness_id
    THEN RAISE(ABORT, 'authority event signature does not bind core fields') END;
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM wc_authority_events_v1 prior WHERE julianday(NEW.effective_at) < julianday(prior.recorded_at)
  ) AND (NEW.is_backdated <> 1 OR NEW.correction_reason IS NULL OR json_array_length(NEW.prior_affected_snapshot_ids_json) = 0
         OR NEW.correction_mode = 'not_applicable' OR NEW.backdate_authorization_witness_id IS NULL)
    THEN RAISE(ABORT, 'backdated event lacks correction evidence') END;
  SELECT CASE WHEN NEW.is_backdated = 1 AND NOT EXISTS (
    SELECT 1 FROM wc_governance_authorization_witnesses_v2 b
    WHERE b.authorization_witness_id = NEW.backdate_authorization_witness_id
      AND b.action_scope = 'backdated_event_authorize' AND b.target_type = 'authority_event'
      AND b.target_id = NEW.event_id AND b.governance_policy_version = NEW.governance_policy_version
      AND julianday(NEW.effective_at) >= julianday(b.valid_from)
      AND (b.valid_until IS NULL OR julianday(NEW.effective_at) < julianday(b.valid_until))
  ) THEN RAISE(ABORT, 'backdated event authorization invalid') END;
END;

CREATE TABLE wc_authority_snapshots_v2 (
  snapshot_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_snapshot/v2'),
  as_of_effective_time TEXT NOT NULL CHECK (julianday(as_of_effective_time) IS NOT NULL),
  ledger_high_water_sequence INTEGER NOT NULL CHECK (ledger_high_water_sequence >= 0),
  event_set_root_sha256 TEXT NOT NULL CHECK (length(event_set_root_sha256) = 64),
  authority_policy_version TEXT NOT NULL,
  snapshot_query_version TEXT NOT NULL CHECK (snapshot_query_version = 'authority_as_of_cutoff/v1'),
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  created_by_principal TEXT NOT NULL,
  authorization_witness_id TEXT NOT NULL,
  signer_key_id TEXT NOT NULL,
  supersedes_snapshot_id TEXT,
  supersession_reason TEXT,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64),
  snapshot_signature TEXT NOT NULL,
  FOREIGN KEY (authorization_witness_id) REFERENCES wc_governance_authorization_witnesses_v2(authorization_witness_id),
  FOREIGN KEY (signer_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id),
  FOREIGN KEY (supersedes_snapshot_id) REFERENCES wc_authority_snapshots_v2(snapshot_id),
  CHECK ((supersedes_snapshot_id IS NULL AND supersession_reason IS NULL) OR (supersedes_snapshot_id IS NOT NULL AND supersession_reason IS NOT NULL))
);

CREATE TRIGGER wc_authority_snapshot_v2_insert_guard
BEFORE INSERT ON wc_authority_snapshots_v2
BEGIN
  SELECT CASE WHEN NEW.ledger_high_water_sequence > COALESCE((SELECT max(authority_event_sequence) FROM wc_authority_events_v1), 0)
    THEN RAISE(ABORT, 'snapshot ledger cutoff exceeds recorded events') END;
  SELECT CASE WHEN NEW.event_set_root_sha256 <> wc_authority_event_root(COALESCE((
    SELECT '[' || group_concat('[' || authority_event_sequence || ',"' || canonical_payload_sha256 || '"]', ',') || ']'
    FROM (SELECT authority_event_sequence, canonical_payload_sha256 FROM wc_authority_events_v1
          WHERE authority_event_sequence <= NEW.ledger_high_water_sequence ORDER BY authority_event_sequence)
  ), '[]')) THEN RAISE(ABORT, 'snapshot event-set root does not match ledger cutoff') END;
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'authority snapshot is not canonical and hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorization_witnesses_v2 a
    JOIN wc_governance_authorities_v1 g ON g.governance_key_id = NEW.signer_key_id
    WHERE a.authorization_witness_id = NEW.authorization_witness_id
      AND a.action_scope = 'authority_snapshot_create' AND a.target_type = 'authority_snapshot' AND a.target_id = NEW.snapshot_id
      AND a.governance_policy_version = NEW.authority_policy_version
      AND julianday(NEW.created_at) >= julianday(a.valid_from)
      AND (a.valid_until IS NULL OR julianday(NEW.created_at) < julianday(a.valid_until))
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.snapshot_signature) = 1
  ) THEN RAISE(ABORT, 'snapshot authorization or signature invalid') END;
  SELECT CASE WHEN json_extract(NEW.signed_payload_canonical_json, '$.schema_version') <> NEW.schema_version
    OR json_extract(NEW.signed_payload_canonical_json, '$.snapshot_id') <> NEW.snapshot_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.ledger_high_water_sequence') <> NEW.ledger_high_water_sequence
    OR json_extract(NEW.signed_payload_canonical_json, '$.event_set_root_sha256') <> NEW.event_set_root_sha256
    OR json_extract(NEW.signed_payload_canonical_json, '$.as_of_effective_time') <> NEW.as_of_effective_time
    OR json_extract(NEW.signed_payload_canonical_json, '$.authority_policy_version') <> NEW.authority_policy_version
    OR json_extract(NEW.signed_payload_canonical_json, '$.snapshot_query_version') <> NEW.snapshot_query_version
    OR json_extract(NEW.signed_payload_canonical_json, '$.created_at') <> NEW.created_at
    OR json_extract(NEW.signed_payload_canonical_json, '$.created_by_principal') <> NEW.created_by_principal
    OR json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') <> NEW.authorization_witness_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.signer_key_id') <> NEW.signer_key_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.supersedes_snapshot_id') IS NOT NEW.supersedes_snapshot_id
    OR json_extract(NEW.signed_payload_canonical_json, '$.supersession_reason') IS NOT NEW.supersession_reason
    THEN RAISE(ABORT, 'snapshot signature does not bind the complete snapshot record') END;
END;

CREATE TRIGGER wc_authority_snapshot_v2_index
AFTER INSERT ON wc_authority_snapshots_v2
BEGIN
  INSERT INTO wc_authority_record_index_v1 VALUES ('authority_snapshot', NEW.snapshot_id, NEW.created_at);
END;

CREATE VIEW wc_authority_events_as_of_snapshot_v1 AS
SELECT s.snapshot_id, s.as_of_effective_time, s.ledger_high_water_sequence,
       e.authority_event_sequence, e.event_id, e.event_type, e.action_scope,
       e.target_type, e.target_id, e.effective_at, e.recorded_at
FROM wc_authority_snapshots_v2 s
JOIN wc_authority_events_v1 e
  ON e.authority_event_sequence <= s.ledger_high_water_sequence
 AND julianday(e.effective_at) <= julianday(s.as_of_effective_time);

CREATE TABLE wc_authority_supersessions_v3 (
  supersession_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_supersession/v3'),
  record_type TEXT NOT NULL,
  superseded_record_id TEXT NOT NULL,
  replacement_record_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  governance_event_id TEXT NOT NULL UNIQUE,
  effective_at TEXT NOT NULL CHECK (julianday(effective_at) IS NOT NULL),
  UNIQUE(record_type, superseded_record_id),
  FOREIGN KEY (record_type, superseded_record_id) REFERENCES wc_authority_record_index_v1(record_type, record_id),
  FOREIGN KEY (record_type, replacement_record_id) REFERENCES wc_authority_record_index_v1(record_type, record_id),
  FOREIGN KEY (governance_event_id) REFERENCES wc_authority_events_v1(event_id),
  CHECK (superseded_record_id <> replacement_record_id)
);

CREATE TRIGGER wc_authority_supersession_v3_insert_guard
BEFORE INSERT ON wc_authority_supersessions_v3
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_authority_events_v1 e
    WHERE e.event_id = NEW.governance_event_id AND e.event_type = 'authority_record_supersede'
      AND e.action_scope = 'authority_record_supersede' AND e.target_type = NEW.record_type
      AND e.target_id = NEW.superseded_record_id AND julianday(e.effective_at) = julianday(NEW.effective_at)
  ) THEN RAISE(ABORT, 'supersession lacks an exact typed governance event') END;
  SELECT CASE WHEN EXISTS (
    SELECT 1 FROM wc_authority_events_v1 e
    WHERE e.target_type = NEW.record_type AND e.target_id = NEW.replacement_record_id
      AND e.event_type IN ('verifier_key_revoke','compiler_profile_revoke','promotion_gate_withdraw')
      AND julianday(e.effective_at) <= julianday(NEW.effective_at)
  ) THEN RAISE(ABORT, 'supersession replacement is revoked or withdrawn') END;
  SELECT CASE WHEN EXISTS (
    WITH RECURSIVE chain(record_id) AS (
      SELECT replacement_record_id FROM wc_authority_supersessions_v3
       WHERE record_type = NEW.record_type AND superseded_record_id = NEW.replacement_record_id
      UNION ALL
      SELECT x.replacement_record_id FROM wc_authority_supersessions_v3 x JOIN chain c ON x.superseded_record_id = c.record_id
       WHERE x.record_type = NEW.record_type
    ) SELECT 1 FROM chain WHERE record_id = NEW.superseded_record_id
  ) THEN RAISE(ABORT, 'supersession cycle detected') END;
END;

CREATE TABLE wc_release_activation_evidence_v1 (
  package_version TEXT PRIMARY KEY CHECK (package_version = 'v1.6-draft-5.3.4'),
  result_channel_isolation INTEGER NOT NULL CHECK (result_channel_isolation = 1),
  snapshot_identity INTEGER NOT NULL CHECK (snapshot_identity = 1),
  historical_snapshot_immutability INTEGER NOT NULL CHECK (historical_snapshot_immutability = 1),
  execution_closure_identity INTEGER NOT NULL CHECK (execution_closure_identity = 1),
  real_lean_integration INTEGER NOT NULL CHECK (real_lean_integration = 1),
  strict_lean INTEGER NOT NULL CHECK (strict_lean = 1),
  strict_tlc INTEGER NOT NULL CHECK (strict_tlc = 1),
  external_governance_signature INTEGER NOT NULL CHECK (external_governance_signature = 1),
  signer_key_id TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64 AND signed_payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  signature TEXT NOT NULL,
  FOREIGN KEY (signer_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_release_activation_evidence_v1_insert_guard
BEFORE INSERT ON wc_release_activation_evidence_v1
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'release activation evidence is not canonical and hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    WHERE g.governance_key_id = NEW.signer_key_id
      AND julianday(NEW.created_at) >= julianday(g.valid_from)
      AND (g.valid_until IS NULL OR julianday(NEW.created_at) < julianday(g.valid_until))
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = 'release_activation_evidence/v1'
      AND json_extract(NEW.signed_payload_canonical_json, '$.package_version') = NEW.package_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.result_channel_isolation') = NEW.result_channel_isolation
      AND json_extract(NEW.signed_payload_canonical_json, '$.snapshot_identity') = NEW.snapshot_identity
      AND json_extract(NEW.signed_payload_canonical_json, '$.historical_snapshot_immutability') = NEW.historical_snapshot_immutability
      AND json_extract(NEW.signed_payload_canonical_json, '$.execution_closure_identity') = NEW.execution_closure_identity
      AND json_extract(NEW.signed_payload_canonical_json, '$.real_lean_integration') = NEW.real_lean_integration
      AND json_extract(NEW.signed_payload_canonical_json, '$.strict_lean') = NEW.strict_lean
      AND json_extract(NEW.signed_payload_canonical_json, '$.strict_tlc') = NEW.strict_tlc
      AND json_extract(NEW.signed_payload_canonical_json, '$.external_governance_signature') = NEW.external_governance_signature
      AND json_extract(NEW.signed_payload_canonical_json, '$.signer_key_id') = NEW.signer_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.created_at') = NEW.created_at
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'release activation evidence signature or trust-root validity failed') END;
END;

CREATE TABLE wc_theorem_promotion_gates_v3 (
  promotion_gate_id TEXT PRIMARY KEY,
  compiler_witness_id TEXT NOT NULL,
  authority_snapshot_id TEXT NOT NULL,
  approval_event_id TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  FOREIGN KEY (compiler_witness_id) REFERENCES wc_lean_compiler_witnesses_v3(lean_compiler_witness_id),
  FOREIGN KEY (authority_snapshot_id) REFERENCES wc_authority_snapshots_v2(snapshot_id),
  FOREIGN KEY (approval_event_id) REFERENCES wc_authority_events_v1(event_id)
);

CREATE TRIGGER wc_theorem_gate_v3_insert_guard
BEFORE INSERT ON wc_theorem_promotion_gates_v3
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_lean_compiler_witnesses_v3 c
    JOIN wc_authority_snapshots_v2 s ON s.snapshot_id = NEW.authority_snapshot_id
    JOIN wc_compiler_profiles_v2 p ON p.compiler_profile_id = c.compiler_profile_id
    JOIN wc_verifier_keys_v3 k ON k.key_id = c.key_id
    JOIN wc_authority_events_as_of_snapshot_v1 e
      ON e.snapshot_id = s.snapshot_id AND e.event_id = NEW.approval_event_id
    WHERE c.lean_compiler_witness_id = NEW.compiler_witness_id AND c.result = 'passed'
      AND c.statement_binding_confirmed = 1 AND c.snapshot_verified_immutable = 1 AND c.result_channel_isolated = 1
      AND c.authority_snapshot_id = s.snapshot_id AND c.authority_ledger_high_water_sequence = s.ledger_high_water_sequence
      AND c.verifier_result_signer_key_id = p.verifier_result_signer_key_id
      AND julianday(c.created_at) >= julianday(p.valid_from)
      AND (p.valid_until IS NULL OR julianday(c.created_at) < julianday(p.valid_until))
      AND julianday(c.created_at) >= julianday(k.valid_from)
      AND (k.valid_until IS NULL OR julianday(c.created_at) < julianday(k.valid_until))
      AND e.event_type = 'promotion_gate_approve' AND e.action_scope = 'promotion_gate_approve'
      AND e.target_type = 'promotion_gate' AND e.target_id = NEW.promotion_gate_id
      AND EXISTS (
        SELECT 1 FROM wc_authority_events_as_of_snapshot_v1 pe
        WHERE pe.snapshot_id = s.snapshot_id AND pe.event_type = 'compiler_profile_activate'
          AND pe.target_type = 'compiler_profile' AND pe.target_id = p.compiler_profile_id
      )
      AND NOT EXISTS (
        SELECT 1 FROM wc_authority_events_as_of_snapshot_v1 pr
        WHERE pr.snapshot_id = s.snapshot_id AND pr.event_type = 'compiler_profile_revoke'
          AND pr.target_type = 'compiler_profile' AND pr.target_id = p.compiler_profile_id
      )
      AND EXISTS (
        SELECT 1 FROM wc_authority_events_as_of_snapshot_v1 ke
        WHERE ke.snapshot_id = s.snapshot_id AND ke.event_type = 'verifier_key_activate'
          AND ke.target_type = 'verifier_key' AND ke.target_id = k.key_id
      )
      AND NOT EXISTS (
        SELECT 1 FROM wc_authority_events_as_of_snapshot_v1 kr
        WHERE kr.snapshot_id = s.snapshot_id AND kr.event_type IN ('verifier_key_revoke','verifier_key_retire')
          AND kr.target_type = 'verifier_key' AND kr.target_id = k.key_id
      )
  ) THEN RAISE(ABORT, '5.3.4 theorem gate lacks exact compiler, snapshot, or governance closure') END;
  SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM wc_release_activation_evidence_v1 WHERE package_version = 'v1.6-draft-5.3.4')
    THEN RAISE(ABORT, 'theorem authority remains disabled until all external release gates pass') END;
END;

CREATE TRIGGER wc_theorem_gate_v3_index
AFTER INSERT ON wc_theorem_promotion_gates_v3
BEGIN
  INSERT INTO wc_authority_record_index_v1 VALUES ('promotion_gate', NEW.promotion_gate_id, NEW.created_at);
END;

CREATE VIEW wc_authoritative_theorems_v3 AS
SELECT g.* FROM wc_theorem_promotion_gates_v3 g
JOIN wc_release_activation_evidence_v1 a ON a.package_version = 'v1.6-draft-5.3.4';

CREATE TRIGGER wc_governance_authorization_v2_no_update BEFORE UPDATE ON wc_governance_authorization_witnesses_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_governance_authorization_v2_no_delete BEFORE DELETE ON wc_governance_authorization_witnesses_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_authority_event_v1_no_update BEFORE UPDATE ON wc_authority_events_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_authority_event_v1_no_delete BEFORE DELETE ON wc_authority_events_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_authority_snapshot_v2_no_update BEFORE UPDATE ON wc_authority_snapshots_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_authority_snapshot_v2_no_delete BEFORE DELETE ON wc_authority_snapshots_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_authority_supersession_v3_no_update BEFORE UPDATE ON wc_authority_supersessions_v3 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_authority_supersession_v3_no_delete BEFORE DELETE ON wc_authority_supersessions_v3 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_profile_v2_no_update BEFORE UPDATE ON wc_compiler_profiles_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_profile_v2_no_delete BEFORE DELETE ON wc_compiler_profiles_v2 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_witness_v3_no_update BEFORE UPDATE ON wc_lean_compiler_witnesses_v3 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_compiler_witness_v3_no_delete BEFORE DELETE ON wc_lean_compiler_witnesses_v3 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_release_activation_evidence_v1_no_update BEFORE UPDATE ON wc_release_activation_evidence_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_release_activation_evidence_v1_no_delete BEFORE DELETE ON wc_release_activation_evidence_v1 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_theorem_gate_v3_no_update BEFORE UPDATE ON wc_theorem_promotion_gates_v3 BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER wc_theorem_gate_v3_no_delete BEFORE DELETE ON wc_theorem_promotion_gates_v3 BEGIN SELECT RAISE(ABORT, 'append-only'); END;

COMMIT;
