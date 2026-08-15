# Contract adapter interface

Each supported contract version is implemented by one immutable adapter selected from a verified descriptor. Services call the adapter rather than branching on version strings.

Required operations:

```text
load_descriptor(corpus_root) -> VerifiedDescriptor
capabilities() -> ContractCapabilities
canonicalize(schema_id, object) -> CanonicalBytes
semantic_content_id(content_type, body) -> ContentId
envelope_id(envelope_without_id) -> EnvelopeId
edge_content_id(edge_without_id) -> EdgeId
verify_attestation(signature_envelope, registry_snapshot) -> VerificationWitness
encrypt(payload, recipients, context) -> EncryptedPayload
decrypt(encrypted_payload, recipient_key, context) -> Plaintext
validate_schema(schema_id, object) -> ValidationResult
migrate_read_only(legacy_bytes, policy) -> MigrationCandidate
```

Capability flags are separate for `read`, `write`, `verify`, `decrypt`, `migrate`, and `activate_authority`. A node that lacks any critical write capability must remain read-only for that version.

Adapters are loaded from an allowlisted registry containing contract version, descriptor ID, implementation artifact ID, schema-registry ID, suite-registry ID, validity interval, and external attestation references. Dynamic code download is outside the authority path.
