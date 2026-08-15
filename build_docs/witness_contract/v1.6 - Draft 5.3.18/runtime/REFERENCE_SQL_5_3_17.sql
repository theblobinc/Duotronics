-- Reference PostgreSQL shape for Contract 5.3.17.
-- Production migrations must be additive, idempotent, and evidence-emitting.

CREATE TABLE IF NOT EXISTS contract_versions (
    contract_version text PRIMARY KEY,
    descriptor_id text NOT NULL UNIQUE,
    descriptor_json jsonb NOT NULL,
    crypto_suite_id text NOT NULL,
    write_enabled boolean NOT NULL DEFAULT false,
    authority_enabled boolean NOT NULL DEFAULT false,
    installed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS semantic_contents (
    semantic_content_id text PRIMARY KEY,
    contract_version text NOT NULL REFERENCES contract_versions(contract_version),
    content_type text NOT NULL,
    canonical_body bytea NOT NULL,
    schema_id text NOT NULL,
    inserted_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS witness_envelopes (
    envelope_id text PRIMARY KEY,
    semantic_content_id text NOT NULL REFERENCES semantic_contents(semantic_content_id),
    corpus_id text NOT NULL,
    observer_principal_id text NOT NULL,
    policy_id text NOT NULL,
    previous_envelope_id text REFERENCES witness_envelopes(envelope_id),
    event_sequence bigint NOT NULL CHECK (event_sequence > 0),
    created_at timestamptz NOT NULL,
    canonical_envelope bytea NOT NULL
);

CREATE INDEX IF NOT EXISTS witness_envelopes_content_idx
    ON witness_envelopes (semantic_content_id, created_at);

CREATE TABLE IF NOT EXISTS crypto_keys (
    key_id text PRIMARY KEY,
    principal_id text NOT NULL,
    algorithm_id text NOT NULL,
    purpose text NOT NULL,
    public_key bytea NOT NULL,
    registry_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'retired', 'revoked')),
    valid_from timestamptz NOT NULL,
    valid_until timestamptz,
    predecessor_key_id text REFERENCES crypto_keys(key_id),
    CHECK (valid_until IS NULL OR valid_until > valid_from)
);

CREATE TABLE IF NOT EXISTS attestations (
    attestation_id text PRIMARY KEY,
    envelope_id text NOT NULL REFERENCES witness_envelopes(envelope_id),
    semantic_content_id text NOT NULL REFERENCES semantic_contents(semantic_content_id),
    suite_id text NOT NULL,
    algorithm_id text NOT NULL,
    key_id text NOT NULL REFERENCES crypto_keys(key_id),
    purpose text NOT NULL,
    signature bytea NOT NULL,
    canonical_payload bytea NOT NULL,
    verified_at timestamptz,
    verification_status text NOT NULL DEFAULT 'unverified'
        CHECK (verification_status IN ('unverified', 'valid', 'invalid', 'revoked'))
);

CREATE INDEX IF NOT EXISTS attestations_envelope_idx
    ON attestations (envelope_id, purpose, verification_status);

CREATE TABLE IF NOT EXISTS meta_object_edges (
    edge_content_id text PRIMARY KEY,
    source_content_id text NOT NULL REFERENCES semantic_contents(semantic_content_id),
    relation_type text NOT NULL,
    target_content_id text NOT NULL REFERENCES semantic_contents(semantic_content_id),
    context_content_id text REFERENCES semantic_contents(semantic_content_id),
    assumption_manifest_id text,
    policy_id text NOT NULL,
    valid_from timestamptz,
    valid_until timestamptz,
    supersedes_edge_id text REFERENCES meta_object_edges(edge_content_id),
    canonical_edge bytea NOT NULL,
    CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
);

CREATE INDEX IF NOT EXISTS meta_edges_source_relation_idx
    ON meta_object_edges (source_content_id, relation_type);
CREATE INDEX IF NOT EXISTS meta_edges_target_relation_idx
    ON meta_object_edges (target_content_id, relation_type);

CREATE TABLE IF NOT EXISTS recurrent_witness_states (
    state_id text PRIMARY KEY,
    branch_id text NOT NULL,
    object_witness_id text NOT NULL,
    previous_state_id text REFERENCES recurrent_witness_states(state_id),
    update_rule_id text NOT NULL,
    canonical_input_root_id text NOT NULL,
    state_json jsonb NOT NULL,
    authoritative boolean NOT NULL DEFAULT false CHECK (authoritative = false)
);

CREATE TABLE IF NOT EXISTS legacy_mapping_witnesses (
    mapping_witness_id text PRIMARY KEY,
    legacy_namespace text NOT NULL,
    legacy_opaque_id text NOT NULL,
    legacy_bytes_commitment text NOT NULL,
    new_semantic_content_id text NOT NULL REFERENCES semantic_contents(semantic_content_id),
    new_envelope_id text NOT NULL REFERENCES witness_envelopes(envelope_id),
    migration_policy_id text NOT NULL,
    execution_witness_id text NOT NULL,
    UNIQUE (legacy_namespace, legacy_opaque_id, migration_policy_id)
);
