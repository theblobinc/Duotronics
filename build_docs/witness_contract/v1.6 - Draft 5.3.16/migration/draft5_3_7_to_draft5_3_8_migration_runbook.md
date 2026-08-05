# Draft 5.3.7 → Draft 5.3.8 Service Migration Runbook

Draft 5.3.8 changes the proof-check service, cache envelope, request identity, verifier bindings, and sandbox evidence surfaces. It does not reinterpret existing authority SQL records; `migration/draft5_3_6_to_draft5_3_7.sql` remains the latest authority-database migration.

## Deployment sequence

1. Install trusted authentication middleware that supplies `witness.authenticated_principal_id`. Reject requests when it is absent.
2. Deploy proof request v2 and remove `subject_id` from clients. Never translate a body subject into a trusted principal.
3. Configure a protected idempotency database parent and a mode-`0600` database owned by the service account. Reject symlinks, extra hard links, wrong owners, and group/world permissions for the database, WAL, and SHM files.
4. Configure global and per-principal in-flight limits, maximum completed rows, total rows, database bytes, lease duration, and completed retention.
5. Treat existing unsigned completed cache rows as incompatible. Start with an empty Draft 5.3.8 cache or allow the service to reject those rows fail-closed; do not migrate them into signed envelopes without authoritative re-execution.
6. Deploy invocation v5 and verifier request v5/result v6. Require `--unsetenv-all`, literal environment entries, governed runtime-created keys, and explicit-entrypoint measurement.
7. Deploy compiler witness v7 and proof result v6. Consumers must validate both semantic and execution-evidence identifiers and all authenticated bindings.
8. Run the full Draft 5.3.8 validator under Python 3.12 and 3.13 before a platform is admitted to the supported matrix.

## Activation state

This migration creates no release-activation evidence. Theorem, promotion, and release authority remain disabled until all eight external activation gates are independently verified and externally authorized.
