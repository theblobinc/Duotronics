# Duotronic Witness Contract v1.6 Draft 5.3.12

**Status:** corrective development draft; permanently not frozen. Theorem, promotion, and release authority are disabled by default.

Draft 5.3.12 incorporates the complete current corpus and supersedes Draft 5.3.11 on the validator-orchestration, historical cache verification, production-loader integration, schema, and validation surfaces listed by the canonical descriptor. Earlier source-package archives are not embedded.

## Governed two-domain Lean execution

The untrusted compiler records every submitted module and exactly one generated binding in `compiled_modules`, applies `-DwarningAsError=true` to every compilation, rejects warning diagnostics, and emits command digests and a bounded artifact manifest. The trusted consumer validates that exact producer output.

Both OCI domains run as the trusted non-root launcher identity through keep-ID mapping. The trusted launcher inspects runtime controls, owns the writable request directories, and host-seals the compiler handoff before inspection. The inspector validates `/handoff`, rejects ambient `LEAN_PATH`, and initializes Lean only with the pinned sysroot and `/handoff/olean` search root.

Compilation and inspection each have a separately typed execution-evidence record containing the exact invocation and argv digests, mounts, runtime identity, control-state evidence, resource observations, remaining request budget, process result, warning policy, and handoff state. Both records are bound into the signed result and compiler witness.

## Authenticated request authority

An authenticated principal is supplied only by trusted middleware. A request without that verified identity is rejected. The request body cannot supply `subject_id` or `authenticated_principal_id`. The verified principal is bound into policy resolution, idempotency scope, verifier requests and results, compiler witnesses, cache envelopes, and proof-check results.

## Untrusted idempotency cache

A completed cache row is data, not authority. The service stores a signed cache envelope and, on every hit, verifies its signature and payload digest, resolves current policy, validates the compiler-witness schema and signature, confirms signer authorization, and checks the current request ID, request digest, authenticated principal, claim and theorem digests, source bundle, profile, policy ID and digest, artifact path, and result status. The outer result status must match the signed witness result.

The SQLite path and parent are checked for symlinks, ownership, link count, and restrictive modes; database, WAL, and SHM files are constrained to mode `0600`. Every connection is explicitly closed. Admission is bounded by global and per-principal in-flight limits, completed-row retention, total rows, database bytes, and expired-lease cleanup. The `(state, lease_expires_at)` index supports routine expiry.

One monotonic deadline covers snapshotting, compilation, and inspection. Active workers renew owner-fenced leases, and a result can be published only by the live exact owner. Production cache signing uses a distinct key and principal with a cache-only authorization scope and governance-signed rotation registry. SQLite completion growth, schema version, integrity, exact object layout, full ancestry, descriptor-relative identity, and canonical duplicate-free cached JSON are enforced.

The active `idempotency_cache_envelope/v3` signs the selected key's `status_changed_at` with its validity interval, state, predecessor, and registry digest. Signing and replay require a non-future status change coherent with the key interval. Retirement takes effect at `valid_until`; revocation takes effect at its recorded status-change time. Rotation predecessors must be complete, older, non-active, same-principal, same-scope, and acyclic.

Cache-registry history is governed by a signed lineage whose digests bind each canonical historical registry, its unique successor, replay policy, and policy-revoked key set. Every historical path must be acyclic, chronologically ordered, and terminate at the current registry.

When a completed row is bound to a superseded cache-signing registry, replay first canonical-parses and schema-validates the row, resolves the signer in that historical snapshot, verifies the row signature, and verifies the signed lineage to the current registry. Only then is v2 stale-row evidence emitted and `cache_key_rotation_requires_new_idempotency_key` returned. Unknown, forged, altered, or revoked historical signers return `cache_integrity_invalid` without rotation evidence. The service does not silently delete the row or re-execute under the old key.

## Production trust-root ownership

The production loaders reject UID or GID zero before reading configuration. They descriptor-walk the absolute root with `O_NOFOLLOW`: immutable `/` and system ancestors may be UID 0, but no ancestor may be group/world writable. The final trust root and sensitive descendants must be owned by the service UID and use private modes. Files must be regular, single-link, service-owned, bounded, and stable across descriptor reads. Root-owned immutable ancestors therefore coexist with a non-root `/etc/witness-authority` service root without making root execution valid.

The production integration harness creates that exact `/etc`-style shape in a chroot and invokes both production loaders after an actual `setgid`/`setuid` transition. A launcher environment that cannot represent the intended UID/GID produces `environment_unavailable`, which is never equivalent to a passing loader run.

## Canonical authority inputs

Service configuration and every authority-bearing compiler, proof-policy, trusted-artifact, platform-capability, and cache-signing JSON document are parsed with duplicate-key rejection and canonical re-encoding equality before schema and signature checks. Authority schema documents reject duplicate keys before compilation. Signed data cannot acquire cross-parser meaning through duplicate fields, alternate order/whitespace, or noncanonical numeric encodings.

## Mandatory sandbox evidence

Every requested control has a governed evidence class. Both `environment_allowlist` and `explicit_entrypoint` are required measured-pass controls. The wrapper starts with an empty inherited environment, permits only configured literal keys plus explicitly governed runtime-created keys, compares the complete observed key set, validates configured values, and rejects every undeclared key. Entrypoint evidence is measured from the running process, not inferred from configuration intent.

Requested, emitted, accepted, applied, measured, and derived states remain distinct. Pre-execution failures leave accepted, applied, and measured state empty.

## Semantic and execution identities

`semantic_witness_content_id` is derived from the claim, theorem, source, policy, profile, principal, and logical result. Ephemeral host paths, exact OCI argv, mount manifests, runtime observations, request identifiers, and timestamps are excluded from it. Those exact details remain signed and auditable under `execution_evidence_content_id`. Equivalent logical executions therefore retain the same semantic ID while differing execution evidence receives a different ID.

## Portable validation

Required phases execute in independent process groups with regular RLIMIT-bounded temporary capture files. Timeout handling closes the parent's capture descriptors, enumerates process descendants, sends bounded TERM/KILL sequences, and performs bounded reaping. Nested substage markers identify full-suite start and completion without waiting for captured-pipe EOF.

Descendant identity binds the PID to its Linux process start-time ticks, so PID reuse cannot redirect a later signal. The packaged reliability evidence requires ten complete validator passes on each validated Python line, with zero surviving descendants and all parent capture descriptors closed.

Python 3.12 and 3.13 are targets. Each interpreter produces its own hash-covered evidence record, and a deterministic merge requires each target exactly once across disjoint validated and unavailable sets. Existing interpreter evidence is never silently relabeled as current-revision evidence. The generated matrix is authoritative for which exact patch versions were actually validated.

Test totals come from a structured `unittest.TestResult`, not verbose-output line parsing. Warning detection is independent of count extraction, and the development-mode suite runs with warnings as errors. Required validation rejects failures, errors, skips, duplicates, stale totals, contradictory Python accounting, and any warning output.

## Authority boundary

Portable regression and schema validation do not activate authority. Strict Lean, strict TLC, a governed hermetic Lean image run, signed OCI-image and verifier-executable attestations, reproducible inspector-build attestations, clean committed-source provenance, and external governance authorization remain eight independent external gates. Unless each is supplied and verified, theorem authority, promotion authority, and release authority remain disabled.
