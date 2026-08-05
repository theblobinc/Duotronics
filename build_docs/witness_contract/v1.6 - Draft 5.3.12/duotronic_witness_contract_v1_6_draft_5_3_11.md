# Duotronic Witness Contract v1.6 Draft 5.3.11

**Status:** corrective development draft; permanently not frozen. Theorem, promotion, and release authority are disabled by default.

Draft 5.3.11 incorporates the complete current corpus and supersedes Draft 5.3.10 on the governed-image, execution-evidence, request-lifecycle, cache-signing, trust-root, persistence, schema, and validation surfaces listed by the canonical descriptor. Earlier source-package archives are not embedded.

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

When a completed row is bound to a superseded cache-signing registry, the row is preserved as untrusted evidence and the service emits `cache_key_rotation_requires_new_idempotency_key`. The caller must submit a new idempotency key. The service does not silently delete the row or re-execute under the old key.

## Production trust-root ownership

The production loaders reject UID or GID zero before reading configuration. They descriptor-walk the absolute root with `O_NOFOLLOW`: immutable `/` and system ancestors may be UID 0, but no ancestor may be group/world writable. The final trust root and sensitive descendants must be owned by the service UID and use private modes. Files must be regular, single-link, service-owned, bounded, and stable across descriptor reads. Root-owned immutable ancestors therefore coexist with a non-root `/etc/witness-authority` service root without making root execution valid.

## Canonical authority inputs

Service configuration and every authority-bearing compiler, proof-policy, trusted-artifact, platform-capability, and cache-signing JSON document are parsed with duplicate-key rejection and canonical re-encoding equality before schema and signature checks. Authority schema documents reject duplicate keys before compilation. Signed data cannot acquire cross-parser meaning through duplicate fields, alternate order/whitespace, or noncanonical numeric encodings.

## Mandatory sandbox evidence

Every requested control has a governed evidence class. Both `environment_allowlist` and `explicit_entrypoint` are required measured-pass controls. The wrapper starts with an empty inherited environment, permits only configured literal keys plus explicitly governed runtime-created keys, compares the complete observed key set, validates configured values, and rejects every undeclared key. Entrypoint evidence is measured from the running process, not inferred from configuration intent.

Requested, emitted, accepted, applied, measured, and derived states remain distinct. Pre-execution failures leave accepted, applied, and measured state empty.

## Semantic and execution identities

`semantic_witness_content_id` is derived from the claim, theorem, source, policy, profile, principal, and logical result. Ephemeral host paths, exact OCI argv, mount manifests, runtime observations, request identifiers, and timestamps are excluded from it. Those exact details remain signed and auditable under `execution_evidence_content_id`. Equivalent logical executions therefore retain the same semantic ID while differing execution evidence receives a different ID.

## Portable validation

Python 3.12 and 3.13 are targets. Each interpreter produces its own hash-covered evidence record, and a deterministic merge requires each target exactly once across disjoint validated and unavailable sets. Existing interpreter evidence is preserved instead of overwritten. Current Draft 5.3.11 records validate Python 3.12.13 and 3.13.5.

Test totals come from a structured `unittest.TestResult`, not verbose-output line parsing. Warning detection is independent of count extraction, and the development-mode suite runs with warnings as errors. Required validation rejects failures, errors, skips, duplicates, stale totals, contradictory Python accounting, and any warning output.

## Authority boundary

Portable regression and schema validation do not activate authority. Strict Lean, strict TLC, a governed hermetic Lean image run, signed OCI-image and verifier-executable attestations, reproducible inspector-build attestations, clean committed-source provenance, and external governance authorization remain eight independent external gates. Unless each is supplied and verified, theorem authority, promotion authority, and release authority remain disabled.
