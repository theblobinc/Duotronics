# Draft 5.3.13 Corrective Assurance Report

Draft 5.3.13 closes the three portable stale-cache findings identified in the independent Draft 5.3.12 review.

## Binding order

The historical branch no longer classifies rotation immediately after signer and lineage authentication. The application now verifies every current slot, principal, request, policy, source, result, and compiler-witness binding first. Only a fully bound authentic predecessor row can produce stale-rotation evidence and the stable rotation conflict.

## Chronology

Historical signing evidence now proves that the authorizing registry existed no later than the cache signing time. Snapshot-lineage validation proves that the signed lineage was created no earlier than any registry it references, while the existing predecessor/successor chronology remains strictly increasing.

## Evidence completeness

`cache_stale_row_evidence/v3` carries the authenticated principal, idempotency key, request and claim digests, policy and source bindings, compiler-witness digest, cache signing time, historical registry creation time, lineage creation time, and a constant indicating that all required bindings were verified.

## Durable production audit

Production mode rejects construction without a real evidence sink. The production loader reads a dedicated audit keypair, verifies that it is distinct from cache and compiler-witness signing authorities, and creates a bounded append-only signed hash chain. Advisory file locking refreshes the verified tail under an exclusive lock before every append, preventing independently initialized worker processes from reusing sequence numbers or predecessor hashes. Existing records are verified at startup. A stale-rotation response is not returned until evidence persistence succeeds; publication failure is fail-closed.

## Regression result

The current-revision normal and warning-as-error suites each contain 274 tests and pass under Python 3.13.5. The complete portable validator has also completed one clean 89/89 required-phase run with eight external activation phases correctly skipped.

## Remaining limits

Python 3.12 current-revision execution is unavailable in this environment. The real non-root production-loader result is recorded separately. All eight external activation gates remain incomplete, so theorem, promotion, and release authority remain disabled and the corpus remains permanently not frozen.
