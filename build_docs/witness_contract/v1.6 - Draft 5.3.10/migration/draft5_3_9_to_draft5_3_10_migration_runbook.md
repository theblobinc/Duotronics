# Draft 5.3.9 → Draft 5.3.10 Service Migration Runbook

Draft 5.3.10 changes the governed-image compile handoff, module search path, mount lifecycle, dual-domain evidence, cache-signing authority, request deadline, idempotency lease, and SQLite persistence contract. It does not reinterpret existing authority SQL records; `migration/draft5_3_6_to_draft5_3_7.sql` remains the latest authority-database migration.

## Deployment sequence

1. Build every inspector surface from `formal/draft5_3_6/lean` and verify the selected-source tree and output digests.
2. Run both OCI domains with keep-ID mapping to the non-root authority service identity. Create private writable directories under that same identity.
3. Let compilation emit the complete handoff manifest, including exactly one `generated_binding` module and the governed warning-as-error command digest for every module.
4. After compiler exit, inspect runtime controls, validate ownership, fsync the handoff, and host-seal every artifact to `0440` and directory to `0550` before trusted inspection.
5. Pass `/handoff` explicitly. Reject ambient `LEAN_PATH`; construct the Lean module search root only from `/handoff/olean` plus the pinned sysroot.
6. Persist separately typed compilation and inspection evidence from the trusted launcher/runtime inspection layer and bind both records into the signed verifier result and witness.
7. Configure a cache key and principal distinct from the compiler-witness authority. Install a governance-signed cache registry entry with cache-only scope, validity, status, and rotation predecessor.
8. Configure one request timeout, lease renewal interval, cache-envelope byte maximum, database byte maximum, and exact SQLite schema version. An exact v1 cache schema migrates transactionally to v2; any weakened, unversioned, unknown, or noncanonical schema fails closed and requires an explicit offline migration or replacement.
9. Install and governance-sign the v2 cache-key registry. Validate every RFC 3339 interval, predecessor reference, same-principal/scope relationship, status transition, and the complete acyclic rotation chain. Retired or revoked keys cannot replay existing rows.
10. Budget witness validation/signing, cache-envelope signing, final lease renewal, database completion, and durable publication against the original monotonic deadline. Configure SQLite busy waits from the remaining budget only.
11. Run the producer-to-consumer, warnings-as-errors, exact-schema, connection-failure, cache-lineage, lease-loss, cancellation, deadline/publication, compile-command reconstruction, and phase-isolation regressions. Then run the full Draft 5.3.10 validator on each claimed Python version.

## Activation state

This migration creates no release-activation evidence. Theorem, promotion, and release authority remain disabled until all eight external activation gates are independently verified and externally authorized.
