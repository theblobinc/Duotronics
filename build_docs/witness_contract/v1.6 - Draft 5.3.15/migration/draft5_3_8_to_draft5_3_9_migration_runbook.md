# Draft 5.3.8 → Draft 5.3.9 Service Migration Runbook

Draft 5.3.9 changes the governed-image compile handoff, module search path, mount lifecycle, dual-domain evidence, cache-signing authority, request deadline, idempotency lease, and SQLite persistence contract. It does not reinterpret existing authority SQL records; `migration/draft5_3_6_to_draft5_3_7.sql` remains the latest authority-database migration.

## Deployment sequence

1. Build every inspector surface from `formal/draft5_3_6/lean` and verify the selected-source tree and output digests.
2. Run both OCI domains with keep-ID mapping to the non-root authority service identity. Create private writable directories under that same identity.
3. Let compilation emit the complete handoff manifest, including exactly one `generated_binding` module and the governed warning-as-error command digest for every module.
4. After compiler exit, inspect runtime controls, validate ownership, fsync the handoff, and host-seal every artifact to `0440` and directory to `0550` before trusted inspection.
5. Pass `/handoff` explicitly. Reject ambient `LEAN_PATH`; construct the Lean module search root only from `/handoff/olean` plus the pinned sysroot.
6. Persist separately typed compilation and inspection evidence from the trusted launcher/runtime inspection layer and bind both records into the signed verifier result and witness.
7. Configure a cache key and principal distinct from the compiler-witness authority. Install a governance-signed cache registry entry with cache-only scope, validity, status, and rotation predecessor.
8. Configure one request timeout, lease renewal interval, cache-envelope byte maximum, database byte maximum, and exact SQLite schema version. Existing non-v1 or noncanonical cache databases fail closed and require an explicit offline migration or replacement.
9. Run the producer-to-consumer, warnings-as-errors, database, lease, deadline, schema, and phase-isolation regressions. Then run the full Draft 5.3.9 validator on each claimed Python version.

## Activation state

This migration creates no release-activation evidence. Theorem, promotion, and release authority remain disabled until all eight external activation gates are independently verified and externally authorized.
