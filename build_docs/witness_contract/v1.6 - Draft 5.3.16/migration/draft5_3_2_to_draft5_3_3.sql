PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

INSERT OR IGNORE INTO wc_schema_generations(generation, applied_at, source_generation, migration_sha256)
VALUES ('v1.6-draft-5.3.3', '2026-07-31T00:00:00-07:00', 'v1.6-draft-5.3.2', NULL);

-- Draft 5.3.3 retains the v2 compiler-witness wire identifier for migration
-- compatibility, but makes the governed hermetic closure fields mandatory for
-- any new authoritative theorem gate.
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN original_source_tree_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN immutable_snapshot_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN compiler_profile_id TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN compiler_registry_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN lake_executable_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN lean_executable_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN lean_stdlib_tree_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN dependency_closure_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN execution_image_digest TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN sandbox_policy_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN verifier_binary_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN structured_result_sha256 TEXT;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN snapshot_verified_immutable INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN clean_source_build INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN prebuilt_artifacts_rejected INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN hermetic_environment INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN network_disabled INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN resource_limits_enforced INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN structured_inspection_complete INTEGER;
ALTER TABLE wc_lean_compiler_witnesses_v2 ADD COLUMN trusted_timestamp_source TEXT;

CREATE TABLE wc_governance_authorities_v1 (
  governance_key_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'governance_authority/v1'),
  authority_principal_id TEXT NOT NULL,
  public_key_base64url TEXT NOT NULL CHECK (length(public_key_base64url) = 43 AND public_key_base64url NOT GLOB '*[^A-Za-z0-9_-]*'),
  public_key_fingerprint_sha256 TEXT NOT NULL CHECK (length(public_key_fingerprint_sha256) = 64 AND public_key_fingerprint_sha256 NOT GLOB '*[^0-9a-f]*'),
  valid_from TEXT NOT NULL CHECK (julianday(valid_from) IS NOT NULL),
  valid_until TEXT CHECK (valid_until IS NULL OR julianday(valid_until) IS NOT NULL),
  status TEXT NOT NULL CHECK (status = 'provisioned'),
  provisioning_witness_id TEXT NOT NULL CHECK (length(provisioning_witness_id) > 0),
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  CHECK (valid_until IS NULL OR julianday(valid_until) >= julianday(valid_from))
);

CREATE TRIGGER wc_governance_authority_insert_guard
BEFORE INSERT ON wc_governance_authorities_v1
BEGIN
  SELECT CASE WHEN wc_public_key_fingerprint(NEW.public_key_base64url) IS NULL
    OR wc_public_key_fingerprint(NEW.public_key_base64url) <> NEW.public_key_fingerprint_sha256
    THEN RAISE(ABORT, 'governance public key does not match its fingerprint') END;
END;

CREATE TABLE wc_governance_authorization_witnesses_v1 (
  authorization_witness_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'governance_authorization_witness/v1'),
  action_type TEXT NOT NULL CHECK (action_type IN ('verifier_key_status','authority_supersession','authority_snapshot')),
  target_record_type TEXT NOT NULL,
  target_record_id TEXT NOT NULL,
  policy_decision_id TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision = 'allow'),
  valid_from TEXT NOT NULL CHECK (julianday(valid_from) IS NOT NULL),
  valid_until TEXT CHECK (valid_until IS NULL OR julianday(valid_until) IS NOT NULL),
  governance_key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1 AND json_type(signed_payload_canonical_json) = 'object'),
  signed_payload_sha256 TEXT NOT NULL CHECK (length(signed_payload_sha256) = 64 AND signed_payload_sha256 NOT GLOB '*[^0-9a-f]*'),
  signature TEXT NOT NULL CHECK (length(signature) >= 43 AND signature NOT GLOB '*[^A-Za-z0-9_-]*'),
  created_at TEXT NOT NULL CHECK (julianday(created_at) IS NOT NULL),
  CHECK (valid_until IS NULL OR julianday(valid_until) >= julianday(valid_from)),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (governance_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_governance_authorization_insert_guard
BEFORE INSERT ON wc_governance_authorization_witnesses_v1
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'governance authorization payload is not canonical or hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    JOIN wc_policy_decisions_v2 p ON p.policy_decision_id = NEW.policy_decision_id
    WHERE g.governance_key_id = NEW.governance_key_id
      AND p.decision = 'allow' AND p.scope = 'authority_supersession'
      AND p.authority_principal_id = g.authority_principal_id
      AND julianday(NEW.created_at) >= julianday(g.valid_from)
      AND (g.valid_until IS NULL OR julianday(NEW.created_at) <= julianday(g.valid_until))
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = NEW.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') = NEW.authorization_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.action_type') = NEW.action_type
      AND json_extract(NEW.signed_payload_canonical_json, '$.target_record_type') = NEW.target_record_type
      AND json_extract(NEW.signed_payload_canonical_json, '$.target_record_id') = NEW.target_record_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') = NEW.policy_decision_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.decision') = NEW.decision
      AND json_extract(NEW.signed_payload_canonical_json, '$.valid_from') = NEW.valid_from
      AND json_extract(NEW.signed_payload_canonical_json, '$.valid_until') IS NEW.valid_until
      AND json_extract(NEW.signed_payload_canonical_json, '$.governance_key_id') = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.created_at') = NEW.created_at
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'governance authorization signature or policy binding failed') END;
END;

CREATE TABLE wc_verifier_key_status_events_v2 (
  key_status_event_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'verifier_key_status_event/v2'),
  key_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','revoked','retired','superseded')),
  replacement_key_id TEXT,
  reason TEXT NOT NULL CHECK (length(reason) > 0),
  effective_at TEXT NOT NULL CHECK (julianday(effective_at) IS NOT NULL),
  recorded_at TEXT NOT NULL CHECK (julianday(recorded_at) IS NOT NULL),
  policy_decision_id TEXT NOT NULL,
  authorization_witness_id TEXT NOT NULL,
  governance_key_id TEXT NOT NULL,
  timestamp_source TEXT NOT NULL CHECK (timestamp_source IN ('authority_service_clock','trusted_time_witness')),
  effective_time_witness_id TEXT,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1 AND json_type(signed_payload_canonical_json) = 'object'),
  signed_payload_sha256 TEXT NOT NULL,
  signature TEXT NOT NULL,
  CHECK ((status = 'superseded' AND replacement_key_id IS NOT NULL AND replacement_key_id <> key_id) OR (status <> 'superseded' AND replacement_key_id IS NULL)),
  CHECK ((timestamp_source = 'authority_service_clock' AND effective_time_witness_id IS NULL) OR (timestamp_source = 'trusted_time_witness' AND effective_time_witness_id IS NOT NULL)),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id),
  FOREIGN KEY (replacement_key_id) REFERENCES wc_verifier_keys_v3(key_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (authorization_witness_id) REFERENCES wc_governance_authorization_witnesses_v1(authorization_witness_id),
  FOREIGN KEY (governance_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_verifier_key_status_v2_insert_guard
BEFORE INSERT ON wc_verifier_key_status_events_v2
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1
    OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'key-status payload is not canonical or hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    JOIN wc_governance_authorization_witnesses_v1 a ON a.authorization_witness_id = NEW.authorization_witness_id
    WHERE g.governance_key_id = NEW.governance_key_id
      AND a.action_type = 'verifier_key_status' AND a.target_record_type = 'verifier_key'
      AND a.target_record_id = NEW.key_id AND a.policy_decision_id = NEW.policy_decision_id
      AND a.governance_key_id = NEW.governance_key_id
      AND julianday(NEW.effective_at) >= julianday(a.valid_from)
      AND (a.valid_until IS NULL OR julianday(NEW.effective_at) <= julianday(a.valid_until))
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = NEW.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.key_status_event_id') = NEW.key_status_event_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.key_id') = NEW.key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.status') = NEW.status
      AND json_extract(NEW.signed_payload_canonical_json, '$.replacement_key_id') IS NEW.replacement_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.reason') = NEW.reason
      AND json_extract(NEW.signed_payload_canonical_json, '$.effective_at') = NEW.effective_at
      AND json_extract(NEW.signed_payload_canonical_json, '$.recorded_at') = NEW.recorded_at
      AND json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') = NEW.policy_decision_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') = NEW.authorization_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.governance_key_id') = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.timestamp_source') = NEW.timestamp_source
      AND json_extract(NEW.signed_payload_canonical_json, '$.effective_time_witness_id') IS NEW.effective_time_witness_id
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'key-status governance signature or authorization binding failed') END;
  SELECT CASE WHEN NEW.status = 'active' AND EXISTS (
    SELECT 1 FROM wc_verifier_key_status_events_v2 e
    WHERE e.key_id = NEW.key_id AND e.status IN ('revoked','retired','superseded')
      AND julianday(e.effective_at) <= julianday(NEW.effective_at)
  ) THEN RAISE(ABORT, 'terminal key status cannot be reactivated') END;
END;

CREATE TABLE wc_authority_supersessions_v2 (
  supersession_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_supersession/v2'),
  record_type TEXT NOT NULL CHECK (record_type IN ('verifier_principal','verifier_key','compiler_witness','proof_witness','promotion_gate')),
  superseded_record_id TEXT NOT NULL,
  replacement_record_id TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (length(reason) > 0),
  effective_at TEXT NOT NULL CHECK (julianday(effective_at) IS NOT NULL),
  recorded_at TEXT NOT NULL CHECK (julianday(recorded_at) IS NOT NULL),
  policy_decision_id TEXT NOT NULL,
  authorization_witness_id TEXT NOT NULL,
  governance_key_id TEXT NOT NULL,
  timestamp_source TEXT NOT NULL CHECK (timestamp_source IN ('authority_service_clock','trusted_time_witness')),
  effective_time_witness_id TEXT,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL,
  signature TEXT NOT NULL,
  CHECK (superseded_record_id <> replacement_record_id),
  CHECK ((timestamp_source = 'authority_service_clock' AND effective_time_witness_id IS NULL) OR (timestamp_source = 'trusted_time_witness' AND effective_time_witness_id IS NOT NULL)),
  UNIQUE (record_type, superseded_record_id),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (authorization_witness_id) REFERENCES wc_governance_authorization_witnesses_v1(authorization_witness_id),
  FOREIGN KEY (governance_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_authority_supersession_v2_insert_guard
BEFORE INSERT ON wc_authority_supersessions_v2
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1 OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'supersession payload is not canonical or hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    JOIN wc_governance_authorization_witnesses_v1 a ON a.authorization_witness_id = NEW.authorization_witness_id
    WHERE g.governance_key_id = NEW.governance_key_id
      AND a.action_type = 'authority_supersession' AND a.target_record_type = NEW.record_type
      AND a.target_record_id = NEW.superseded_record_id AND a.policy_decision_id = NEW.policy_decision_id
      AND a.governance_key_id = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = NEW.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.supersession_id') = NEW.supersession_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.record_type') = NEW.record_type
      AND json_extract(NEW.signed_payload_canonical_json, '$.superseded_record_id') = NEW.superseded_record_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.replacement_record_id') = NEW.replacement_record_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.reason') = NEW.reason
      AND json_extract(NEW.signed_payload_canonical_json, '$.effective_at') = NEW.effective_at
      AND json_extract(NEW.signed_payload_canonical_json, '$.recorded_at') = NEW.recorded_at
      AND json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') = NEW.policy_decision_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') = NEW.authorization_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.governance_key_id') = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.timestamp_source') = NEW.timestamp_source
      AND json_extract(NEW.signed_payload_canonical_json, '$.effective_time_witness_id') IS NEW.effective_time_witness_id
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'supersession governance signature or authorization binding failed') END;
END;

CREATE TABLE wc_authority_snapshots_v1 (
  authority_snapshot_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_snapshot/v1'),
  evaluated_at TEXT NOT NULL CHECK (julianday(evaluated_at) IS NOT NULL),
  policy_decision_id TEXT NOT NULL,
  authorization_witness_id TEXT NOT NULL,
  governance_key_id TEXT NOT NULL,
  recorded_at TEXT NOT NULL CHECK (julianday(recorded_at) IS NOT NULL),
  timestamp_source TEXT NOT NULL CHECK (timestamp_source IN ('authority_service_clock','trusted_time_witness')),
  evaluation_time_witness_id TEXT,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL,
  signature TEXT NOT NULL,
  CHECK ((timestamp_source = 'authority_service_clock' AND evaluation_time_witness_id IS NULL) OR (timestamp_source = 'trusted_time_witness' AND evaluation_time_witness_id IS NOT NULL)),
  FOREIGN KEY (policy_decision_id) REFERENCES wc_policy_decisions_v2(policy_decision_id),
  FOREIGN KEY (authorization_witness_id) REFERENCES wc_governance_authorization_witnesses_v1(authorization_witness_id),
  FOREIGN KEY (governance_key_id) REFERENCES wc_governance_authorities_v1(governance_key_id)
);

CREATE TRIGGER wc_authority_snapshot_insert_guard
BEFORE INSERT ON wc_authority_snapshots_v1
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1 OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, 'authority snapshot payload is not canonical or hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_governance_authorities_v1 g
    JOIN wc_governance_authorization_witnesses_v1 a ON a.authorization_witness_id = NEW.authorization_witness_id
    WHERE g.governance_key_id = NEW.governance_key_id
      AND a.action_type = 'authority_snapshot' AND a.target_record_type = 'authority_snapshot'
      AND a.target_record_id = NEW.authority_snapshot_id AND a.policy_decision_id = NEW.policy_decision_id
      AND a.governance_key_id = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.schema_version') = NEW.schema_version
      AND json_extract(NEW.signed_payload_canonical_json, '$.authority_snapshot_id') = NEW.authority_snapshot_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.evaluated_at') = NEW.evaluated_at
      AND json_extract(NEW.signed_payload_canonical_json, '$.policy_decision_id') = NEW.policy_decision_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.authorization_witness_id') = NEW.authorization_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.governance_key_id') = NEW.governance_key_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.recorded_at') = NEW.recorded_at
      AND json_extract(NEW.signed_payload_canonical_json, '$.timestamp_source') = NEW.timestamp_source
      AND json_extract(NEW.signed_payload_canonical_json, '$.evaluation_time_witness_id') IS NEW.evaluation_time_witness_id
      AND wc_ed25519_verify(g.public_key_base64url, NEW.signed_payload_canonical_json, NEW.signature) = 1
  ) THEN RAISE(ABORT, 'authority snapshot governance signature or authorization binding failed') END;
END;

CREATE VIEW wc_verifier_validity_as_of_v4 AS
SELECT s.authority_snapshot_id, s.evaluated_at, k.key_id, k.verifier_principal_id,
       k.signature_algorithm, k.public_key_base64url, k.public_key_fingerprint_sha256,
       k.valid_from, k.valid_until
FROM wc_authority_snapshots_v1 s
JOIN wc_verifier_keys_v3 k
JOIN wc_verifier_principals_v2 p ON p.verifier_principal_id = k.verifier_principal_id AND p.key_id = k.key_id
WHERE p.status = 'active'
  AND julianday(s.evaluated_at) >= julianday(k.valid_from)
  AND (k.valid_until IS NULL OR julianday(s.evaluated_at) <= julianday(k.valid_until))
  AND (SELECT e.status FROM wc_verifier_key_status_events_v2 e
       WHERE e.key_id = k.key_id AND julianday(e.effective_at) <= julianday(s.evaluated_at)
       ORDER BY julianday(e.effective_at) DESC, julianday(e.recorded_at) DESC, e.key_status_event_id DESC LIMIT 1) = 'active'
  AND NOT EXISTS (SELECT 1 FROM wc_authority_supersessions_v2 x
                  WHERE x.record_type IN ('verifier_key','verifier_principal')
                    AND x.superseded_record_id IN (k.key_id,k.verifier_principal_id)
                    AND julianday(x.effective_at) <= julianday(s.evaluated_at));

CREATE VIEW wc_currently_valid_verifiers_v4 AS
SELECT k.key_id, k.verifier_principal_id, k.signature_algorithm, k.public_key_base64url,
       k.public_key_fingerprint_sha256, k.valid_from, k.valid_until
FROM wc_verifier_keys_v3 k
JOIN wc_verifier_principals_v2 p ON p.verifier_principal_id = k.verifier_principal_id AND p.key_id = k.key_id
WHERE p.status = 'active'
  AND julianday('now') >= julianday(k.valid_from)
  AND (k.valid_until IS NULL OR julianday('now') <= julianday(k.valid_until))
  AND (SELECT e.status FROM wc_verifier_key_status_events_v2 e
       WHERE e.key_id = k.key_id AND julianday(e.effective_at) <= julianday('now')
       ORDER BY julianday(e.effective_at) DESC, julianday(e.recorded_at) DESC, e.key_status_event_id DESC LIMIT 1) = 'active'
  AND NOT EXISTS (SELECT 1 FROM wc_authority_supersessions_v2 x
                  WHERE x.record_type IN ('verifier_key','verifier_principal')
                    AND x.superseded_record_id IN (k.key_id,k.verifier_principal_id)
                    AND julianday(x.effective_at) <= julianday('now'));

CREATE TABLE wc_authority_signature_bindings_v2 (
  signature_binding_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL CHECK (schema_version = 'authority_signature_binding/v2'),
  record_type TEXT NOT NULL CHECK (record_type = 'lean_compiler_witness_5_3_3'),
  record_id TEXT NOT NULL UNIQUE,
  key_id TEXT NOT NULL,
  signed_payload_canonical_json TEXT NOT NULL CHECK (json_valid(signed_payload_canonical_json) = 1),
  signed_payload_sha256 TEXT NOT NULL,
  signature_verified_at TEXT NOT NULL CHECK (julianday(signature_verified_at) IS NOT NULL),
  FOREIGN KEY (key_id) REFERENCES wc_verifier_keys_v3(key_id)
);

CREATE TRIGGER wc_compiler_signature_binding_v2_insert_guard
BEFORE INSERT ON wc_authority_signature_bindings_v2
BEGIN
  SELECT CASE WHEN wc_is_canonical_json(NEW.signed_payload_canonical_json) <> 1 OR wc_sha256(NEW.signed_payload_canonical_json) <> NEW.signed_payload_sha256
    THEN RAISE(ABORT, '5.3.3 compiler payload is not canonical or hash-bound') END;
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_lean_compiler_witnesses_v2 l JOIN wc_verifier_keys_v3 k ON k.key_id = NEW.key_id
    WHERE l.lean_compiler_witness_id = NEW.record_id AND l.key_id = NEW.key_id
      AND l.verifier_principal_id = k.verifier_principal_id AND l.signed_payload_sha256 = NEW.signed_payload_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_compiler_witness_id') = l.lean_compiler_witness_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.claim_id') = l.claim_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.claim_content_sha256') = l.claim_content_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.theorem_statement_sha256') = l.theorem_statement_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.proof_artifact_sha256') = l.proof_artifact_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.original_source_tree_sha256') = l.original_source_tree_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.immutable_snapshot_sha256') = l.immutable_snapshot_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.compiler_profile_id') = l.compiler_profile_id
      AND json_extract(NEW.signed_payload_canonical_json, '$.compiler_registry_sha256') = l.compiler_registry_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lake_executable_sha256') = l.lake_executable_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_executable_sha256') = l.lean_executable_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.lean_stdlib_tree_sha256') = l.lean_stdlib_tree_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.dependency_closure_sha256') = l.dependency_closure_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.execution_image_digest') = l.execution_image_digest
      AND json_extract(NEW.signed_payload_canonical_json, '$.sandbox_policy_sha256') = l.sandbox_policy_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.verifier_binary_sha256') = l.verifier_binary_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.structured_result_sha256') = l.structured_result_sha256
      AND json_extract(NEW.signed_payload_canonical_json, '$.snapshot_verified_immutable') = l.snapshot_verified_immutable
      AND json_extract(NEW.signed_payload_canonical_json, '$.clean_source_build') = l.clean_source_build
      AND json_extract(NEW.signed_payload_canonical_json, '$.prebuilt_artifacts_rejected') = l.prebuilt_artifacts_rejected
      AND json_extract(NEW.signed_payload_canonical_json, '$.hermetic_environment') = l.hermetic_environment
      AND json_extract(NEW.signed_payload_canonical_json, '$.network_disabled') = l.network_disabled
      AND json_extract(NEW.signed_payload_canonical_json, '$.resource_limits_enforced') = l.resource_limits_enforced
      AND json_extract(NEW.signed_payload_canonical_json, '$.structured_inspection_complete') = l.structured_inspection_complete
      AND json_extract(NEW.signed_payload_canonical_json, '$.trusted_timestamp_source') = l.trusted_timestamp_source
      AND wc_ed25519_verify(k.public_key_base64url, NEW.signed_payload_canonical_json, l.signature) = 1
  ) THEN RAISE(ABORT, '5.3.3 compiler signature does not bind the stored hermetic closure') END;
END;

DROP TRIGGER wc_theorem_gate_v2_allowed_insert_guard;
DROP VIEW wc_authoritative_theorems_v2;

CREATE TRIGGER wc_theorem_gate_v2_allowed_insert_guard
BEFORE INSERT ON wc_theorem_promotion_gates_v2
WHEN NEW.allowed = 1
BEGIN
  SELECT CASE WHEN NOT EXISTS (
    SELECT 1 FROM wc_claims_v2 c
    JOIN wc_policy_decisions_v2 p ON p.policy_decision_id = NEW.policy_decision_id
    JOIN wc_lean_compiler_witnesses_v2 lc ON lc.lean_compiler_witness_id = NEW.lean_compiler_witness_id
    JOIN wc_proof_witnesses_v2 pw ON pw.proof_witness_id = NEW.proof_witness_id
    JOIN wc_non_collapse_transitions_v2 nc ON nc.transition_id = NEW.non_collapse_transition_id
    JOIN wc_claim_status_events_v2 se ON se.status_event_id = NEW.status_event_id
    JOIN wc_verifier_keys_v3 k ON k.key_id = NEW.key_id AND k.verifier_principal_id = NEW.verifier_principal_id
    JOIN wc_authority_signature_bindings_v2 lsb ON lsb.record_id = NEW.lean_compiler_witness_id AND lsb.key_id = NEW.key_id
    JOIN wc_authority_signature_bindings_v1 lsb1 ON lsb1.record_type = 'lean_compiler_witness' AND lsb1.record_id = NEW.lean_compiler_witness_id AND lsb1.key_id = NEW.key_id
    JOIN wc_authority_signature_bindings_v1 psb ON psb.record_type = 'proof_witness' AND psb.record_id = NEW.proof_witness_id AND psb.key_id = NEW.key_id
    WHERE c.claim_id = NEW.claim_id AND c.claim_kind = 'proof_claim'
      AND c.claim_content_sha256 = NEW.claim_content_sha256 AND c.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND p.claim_id = NEW.claim_id AND p.decision = 'allow' AND p.scope = 'theorem_promotion'
      AND lc.claim_id = NEW.claim_id AND lc.claim_content_sha256 = NEW.claim_content_sha256 AND lc.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND lc.result = 'passed' AND lc.theorem_status = 'proved' AND lc.contains_sorry = 0 AND lc.contains_admit = 0 AND lc.unapproved_axiom_count = 0
      AND lc.axiom_inspection_complete = 1 AND lc.statement_binding_confirmed = 1 AND lc.warnings_as_errors = 1
      AND lc.original_source_tree_sha256 = lc.immutable_snapshot_sha256 AND lc.source_tree_sha256 = lc.immutable_snapshot_sha256
      AND lc.snapshot_verified_immutable = 1 AND lc.clean_source_build = 1 AND lc.prebuilt_artifacts_rejected = 1
      AND lc.hermetic_environment = 1 AND lc.network_disabled = 1 AND lc.resource_limits_enforced = 1 AND lc.structured_inspection_complete = 1
      AND lc.compiler_profile_id IS NOT NULL AND lc.compiler_registry_sha256 IS NOT NULL
      AND lc.lake_executable_sha256 IS NOT NULL AND lc.lean_executable_sha256 IS NOT NULL
      AND lc.lean_stdlib_tree_sha256 IS NOT NULL AND lc.dependency_closure_sha256 IS NOT NULL
      AND lc.execution_image_digest GLOB 'sha256:*' AND lc.sandbox_policy_sha256 IS NOT NULL AND lc.verifier_binary_sha256 IS NOT NULL
      AND lc.compiler_executable_sha256 = lc.lean_executable_sha256
      AND lc.verifier_principal_id = NEW.verifier_principal_id AND lc.key_id = NEW.key_id
      AND pw.claim_id = NEW.claim_id AND pw.claim_content_sha256 = NEW.claim_content_sha256 AND pw.theorem_statement_sha256 = NEW.theorem_statement_sha256
      AND pw.lean_compiler_witness_id = NEW.lean_compiler_witness_id AND pw.policy_decision_id = NEW.policy_decision_id
      AND pw.verifier_principal_id = NEW.verifier_principal_id AND pw.key_id = NEW.key_id AND pw.theorem_status = 'proved'
      AND nc.claim_id = NEW.claim_id AND nc.source_primitive_category = 'conjectural' AND nc.target_primitive_category = 'theorem'
      AND nc.transition_kind = 'proof_upgrade' AND nc.transition_status = 'allowed' AND nc.proof_witness_id = NEW.proof_witness_id AND nc.policy_decision_id = NEW.policy_decision_id
      AND se.claim_id = NEW.claim_id AND se.source_status = 'conjecture' AND se.target_status IN ('theorem','proof_verified') AND se.transition_kind = 'prove' AND se.allowed = 1
      AND se.policy_decision_id = NEW.policy_decision_id AND se.proof_witness_id = NEW.proof_witness_id AND se.lean_compiler_witness_id = NEW.lean_compiler_witness_id AND se.non_collapse_transition_id = NEW.non_collapse_transition_id
      AND julianday(NEW.created_at) >= julianday(k.valid_from) AND (k.valid_until IS NULL OR julianday(NEW.created_at) <= julianday(k.valid_until))
      AND (SELECT e.status FROM wc_verifier_key_status_events_v2 e WHERE e.key_id = NEW.key_id AND julianday(e.effective_at) <= julianday(NEW.created_at)
           ORDER BY julianday(e.effective_at) DESC, julianday(e.recorded_at) DESC, e.key_status_event_id DESC LIMIT 1) = 'active'
      AND NOT EXISTS (SELECT 1 FROM wc_authority_supersessions_v2 x WHERE x.record_type IN ('verifier_key','verifier_principal')
                      AND x.superseded_record_id IN (NEW.key_id,NEW.verifier_principal_id) AND julianday(x.effective_at) <= julianday(NEW.created_at))
  ) THEN RAISE(ABORT, '5.3.3 theorem gate hermetic authority conjunction failed') END;
END;

CREATE VIEW wc_authoritative_theorems_v2 AS
SELECT g.theorem_promotion_gate_id, g.claim_id, g.claim_content_sha256, g.theorem_statement_sha256,
       g.proof_witness_id, g.lean_compiler_witness_id, g.policy_decision_id,
       g.verifier_principal_id, g.key_id, g.created_at
FROM wc_theorem_promotion_gates_v2 g
JOIN wc_currently_valid_verifiers_v4 v ON v.key_id = g.key_id AND v.verifier_principal_id = g.verifier_principal_id
JOIN wc_authority_signature_bindings_v2 l ON l.record_id = g.lean_compiler_witness_id AND l.key_id = g.key_id
JOIN wc_authority_signature_bindings_v1 l1 ON l1.record_type = 'lean_compiler_witness' AND l1.record_id = g.lean_compiler_witness_id AND l1.key_id = g.key_id
JOIN wc_authority_signature_bindings_v1 p ON p.record_type = 'proof_witness' AND p.record_id = g.proof_witness_id AND p.key_id = g.key_id
WHERE g.allowed = 1
  AND NOT EXISTS (SELECT 1 FROM wc_authority_supersessions_v2 x WHERE x.record_type = 'promotion_gate'
                  AND x.superseded_record_id = g.theorem_promotion_gate_id AND julianday(x.effective_at) <= julianday('now'));

CREATE VIEW wc_authoritative_theorems_as_of_v3 AS
SELECT s.authority_snapshot_id, s.evaluated_at, g.theorem_promotion_gate_id, g.claim_id,
       g.claim_content_sha256, g.theorem_statement_sha256, g.proof_witness_id,
       g.lean_compiler_witness_id, g.policy_decision_id, g.verifier_principal_id, g.key_id, g.created_at
FROM wc_authority_snapshots_v1 s
JOIN wc_theorem_promotion_gates_v2 g ON g.allowed = 1 AND julianday(g.created_at) <= julianday(s.evaluated_at)
JOIN wc_verifier_validity_as_of_v4 v ON v.authority_snapshot_id = s.authority_snapshot_id AND v.key_id = g.key_id AND v.verifier_principal_id = g.verifier_principal_id
JOIN wc_authority_signature_bindings_v2 l ON l.record_id = g.lean_compiler_witness_id AND l.key_id = g.key_id
JOIN wc_authority_signature_bindings_v1 l1 ON l1.record_type = 'lean_compiler_witness' AND l1.record_id = g.lean_compiler_witness_id AND l1.key_id = g.key_id
JOIN wc_authority_signature_bindings_v1 p ON p.record_type = 'proof_witness' AND p.record_id = g.proof_witness_id AND p.key_id = g.key_id
WHERE NOT EXISTS (SELECT 1 FROM wc_authority_supersessions_v2 x WHERE x.record_type = 'promotion_gate'
                  AND x.superseded_record_id = g.theorem_promotion_gate_id AND julianday(x.effective_at) <= julianday(s.evaluated_at));

CREATE TRIGGER wc_governance_authorities_no_update BEFORE UPDATE ON wc_governance_authorities_v1 BEGIN SELECT RAISE(ABORT, 'wc_governance_authorities_v1 is append-only'); END;
CREATE TRIGGER wc_governance_authorities_no_delete BEFORE DELETE ON wc_governance_authorities_v1 BEGIN SELECT RAISE(ABORT, 'wc_governance_authorities_v1 is append-only'); END;
CREATE TRIGGER wc_governance_authorizations_no_update BEFORE UPDATE ON wc_governance_authorization_witnesses_v1 BEGIN SELECT RAISE(ABORT, 'wc_governance_authorization_witnesses_v1 is append-only'); END;
CREATE TRIGGER wc_governance_authorizations_no_delete BEFORE DELETE ON wc_governance_authorization_witnesses_v1 BEGIN SELECT RAISE(ABORT, 'wc_governance_authorization_witnesses_v1 is append-only'); END;
CREATE TRIGGER wc_key_status_v2_no_update BEFORE UPDATE ON wc_verifier_key_status_events_v2 BEGIN SELECT RAISE(ABORT, 'wc_verifier_key_status_events_v2 is append-only'); END;
CREATE TRIGGER wc_key_status_v2_no_delete BEFORE DELETE ON wc_verifier_key_status_events_v2 BEGIN SELECT RAISE(ABORT, 'wc_verifier_key_status_events_v2 is append-only'); END;
CREATE TRIGGER wc_supersession_v2_no_update BEFORE UPDATE ON wc_authority_supersessions_v2 BEGIN SELECT RAISE(ABORT, 'wc_authority_supersessions_v2 is append-only'); END;
CREATE TRIGGER wc_supersession_v2_no_delete BEFORE DELETE ON wc_authority_supersessions_v2 BEGIN SELECT RAISE(ABORT, 'wc_authority_supersessions_v2 is append-only'); END;
CREATE TRIGGER wc_authority_snapshots_no_update BEFORE UPDATE ON wc_authority_snapshots_v1 BEGIN SELECT RAISE(ABORT, 'wc_authority_snapshots_v1 is append-only'); END;
CREATE TRIGGER wc_authority_snapshots_no_delete BEFORE DELETE ON wc_authority_snapshots_v1 BEGIN SELECT RAISE(ABORT, 'wc_authority_snapshots_v1 is append-only'); END;
CREATE TRIGGER wc_signature_binding_v2_no_update BEFORE UPDATE ON wc_authority_signature_bindings_v2 BEGIN SELECT RAISE(ABORT, 'wc_authority_signature_bindings_v2 is append-only'); END;
CREATE TRIGGER wc_signature_binding_v2_no_delete BEFORE DELETE ON wc_authority_signature_bindings_v2 BEGIN SELECT RAISE(ABORT, 'wc_authority_signature_bindings_v2 is append-only'); END;

COMMIT;
