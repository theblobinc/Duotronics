# Migration Runbook — Draft 5.3.12 to Draft 5.3.13

## Scope

This is an application and trust-root configuration migration. The SQLite idempotency schema is unchanged.

## Required steps

1. Deploy the Draft 5.3.13 runtime and active schemas.
2. Add `cache_stale_row_evidence_v3.schema.json` and `cache_audit_record_v1.schema.json` to the protected schema root.
3. Generate a dedicated Ed25519 cache-audit keypair. It must not equal the cache-envelope keypair or compiler-witness keypair.
4. Add the following canonical service configuration fields:
   - `cache_audit_private_key_file`
   - `cache_audit_public_key_file`
   - `cache_audit_log_file`
   - `cache_audit_signer_principal_id`
   - `cache_audit_signer_key_id`
   - `cache_audit_maximum_record_bytes`
   - `cache_audit_maximum_log_bytes`
   - `cache_audit_maximum_records`
   - `cache_audit_rotation_policy`, fixed to `manual_governance_sealed_segment`
5. Ensure the audit-log parent is a real private service-owned directory. The log is created as one service-owned mode-0600 regular file.
6. Preserve the governed current and historical cache registries and signed lineage. Verify lineage creation is not earlier than any referenced registry.
7. Start the production loader. Startup must verify any existing audit segment before accepting traffic.
8. Run the stale-row regressions for correct rotation, cross-slot transplantation, cross-principal transplantation, cross-request transplantation, and retroactive registry authorization.
9. Run normal and warnings-as-errors test suites and the complete portable validator on every available target interpreter.

## Failure behavior

- Binding mismatch: `cache_integrity_invalid`; no stale evidence.
- Registry created after cache signing: `cache_integrity_invalid`; no stale evidence.
- Correctly bound governed predecessor: persist signed audit evidence, then `cache_key_rotation_requires_new_idempotency_key`.
- Audit persistence failure: `cache_audit_publication_failed`; do not claim evidence emission.

## Authority

Migration completion does not enable theorem, promotion, or release authority. All eight external activation gates remain separately required.
