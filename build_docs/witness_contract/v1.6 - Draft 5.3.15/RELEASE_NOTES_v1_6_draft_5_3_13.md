# Release Notes — v1.6 Draft 5.3.13

Draft 5.3.13 is a standalone, permanently unfrozen, non-authoritative corrective development corpus based on Draft 5.3.12. It embeds no predecessor ZIPs; predecessor hashes are informational lineage only.

## Closed Draft 5.3.12 findings

### Historical cache rows are fully bound before rotation classification

Historical replay now verifies the signed envelope against the current authenticated principal, idempotency slot, canonical request digest, request ID, claim and claim-content digest, compiler profile, governed policy ID and digest, source bundle, proof-artifact path, and signed compiler-witness request bindings before it can enter the stale-rotation branch.

An authentic historical envelope transplanted to another idempotency key, principal, request, or claim returns `cache_integrity_invalid`. No stale-row evidence is emitted for a binding mismatch. A correctly bound historical row still returns `cache_key_rotation_requires_new_idempotency_key`.

### Retroactive registry authorization is rejected

Historical signing-time reconstruction now requires:

```text
historical_registry.created_at <= cache_signed_at
```

Signed registry lineage creation must also be at or after every registry it references, and registry predecessor/successor chronology remains strictly increasing. Cache signing time, historical registry creation time, and lineage creation time are included in stale-row evidence.

### Stale-row evidence is complete

The active `cache_stale_row_evidence/v3` surface binds:

- authenticated principal and idempotency key;
- request digest, request ID, claim ID, and claim-content digest;
- compiler profile, policy ID and digest, source bundle, and artifact path;
- compiler-witness signed-payload digest;
- cache signing, historical registry creation, and lineage creation times;
- the exact successful binding-verification result.

### Production audit evidence is durable and separately signed

Production configuration now requires a dedicated cache-audit Ed25519 keypair distinct from cache-envelope and compiler-witness authorities. The production loader installs a `SignedAppendOnlyAuditSink` rather than accepting the development no-op sink. Every append takes an exclusive advisory file lock and re-verifies the current tail so independently initialized service workers serialize correctly.

The sink writes canonical JSONL records with:

- a monotonically increasing sequence;
- a previous-record SHA-256 chain;
- the complete canonical evidence payload and digest;
- a dedicated audit signer identity;
- an Ed25519 signature;
- bounded record, segment-byte, and record-count limits;
- startup verification of canonical encoding, signatures, event hashes, sequence, and chain continuity.

Evidence is synchronously persisted before the rotation-specific `409` is returned. Audit publication failure returns the stable fail-closed error `cache_audit_publication_failed`.

## Regression coverage

Draft 5.3.13 adds adversarial coverage for:

- cross-idempotency transplantation;
- cross-principal transplantation;
- cross-request and cross-claim transplantation;
- registry creation after the claimed cache-signing time;
- lineage creation before a referenced registry;
- signed audit-chain restart verification;
- audit-chain tampering;
- audit-publication failure.

The active portable validator has 89 required phases, including four new cache-binding, chronology, evidence, and audit-sink phases.

## Environment qualification

Python 3.13.5 is available in the current build environment. The current revision passes 274/274 tests in normal and warnings-as-errors modes and has one complete 89/89 required-phase validator run. Python 3.12 is not installed and is explicitly recorded as unavailable for this changed revision; Draft 5.3.12 execution evidence is retained as predecessor evidence only and is not relabeled as Draft 5.3.13 validation.

The production non-root loader harness remains a real chroot → `setgid` → `setuid` integration. Its current result is recorded exactly as produced by the available environment and is not treated as an authority-activation substitute.

## Authority status

Strict Lean, strict TLC, governed-image execution, signed OCI image build attestation, signed verifier executable attestation, reproducible inspector build attestation, clean committed-source provenance, and external governance authorization remain incomplete. Theorem, promotion, and release authority remain disabled.
