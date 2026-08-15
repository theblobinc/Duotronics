# Duotronic Witness Contract v1.6 Draft 5.3.8

**Status:** corrective development draft; permanently not frozen. Theorem, promotion, and release authority are disabled by default.

Draft 5.3.8 incorporates the complete current corpus and supersedes Draft 5.3.7 on the active service, cache, authentication, sandbox measurement, witness identity, schema, and validation surfaces listed by the canonical descriptor. Earlier source-package archives are not embedded.

## Authenticated request authority

An authenticated principal is supplied only by trusted middleware. A request without that verified identity is rejected. The request body cannot supply `subject_id` or `authenticated_principal_id`. The verified principal is bound into policy resolution, idempotency scope, verifier requests and results, compiler witnesses, cache envelopes, and proof-check results.

## Untrusted idempotency cache

A completed cache row is data, not authority. The service stores a signed cache envelope and, on every hit, verifies its signature and payload digest, resolves current policy, validates the compiler-witness schema and signature, confirms signer authorization, and checks the current request ID, request digest, authenticated principal, claim and theorem digests, source bundle, profile, policy ID and digest, artifact path, and result status. The outer result status must match the signed witness result.

The SQLite path and parent are checked for symlinks, ownership, link count, and restrictive modes; database, WAL, and SHM files are constrained to mode `0600`. Every connection is explicitly closed. Admission is bounded by global and per-principal in-flight limits, completed-row retention, total rows, database bytes, and expired-lease cleanup. The `(state, lease_expires_at)` index supports routine expiry.

## Mandatory sandbox evidence

Every requested control has a governed evidence class. Both `environment_allowlist` and `explicit_entrypoint` are required measured-pass controls. The wrapper starts with an empty inherited environment, permits only configured literal keys plus explicitly governed runtime-created keys, compares the complete observed key set, validates configured values, and rejects every undeclared key. Entrypoint evidence is measured from the running process, not inferred from configuration intent.

Requested, emitted, accepted, applied, measured, and derived states remain distinct. Pre-execution failures leave accepted, applied, and measured state empty.

## Semantic and execution identities

`semantic_witness_content_id` is derived from the claim, theorem, source, policy, profile, principal, and logical result. Ephemeral host paths, exact OCI argv, mount manifests, runtime observations, request identifiers, and timestamps are excluded from it. Those exact details remain signed and auditable under `execution_evidence_content_id`. Equivalent logical executions therefore retain the same semantic ID while differing execution evidence receives a different ID.

## Portable validation

Python 3.12 and 3.13 are supported. Test totals come from a structured `unittest.TestResult`, not verbose-output line parsing. Warning detection is independent of count extraction, and the development-mode suite runs with warnings as errors. Required validation rejects failures, errors, skips, duplicates, stale totals, and any warning output.

## Authority boundary

Portable regression and schema validation do not activate authority. Strict Lean, strict TLC, a governed hermetic Lean image run, signed OCI-image and verifier-executable attestations, reproducible inspector-build attestations, clean committed-source provenance, and external governance authorization remain eight independent external gates. Unless each is supplied and verified, theorem authority, promotion authority, and release authority remain disabled.
