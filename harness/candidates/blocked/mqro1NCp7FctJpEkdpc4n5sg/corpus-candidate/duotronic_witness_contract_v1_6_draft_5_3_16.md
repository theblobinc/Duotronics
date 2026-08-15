# Duotronic Witness Contract v1.6 — Draft 5.3.16

## Status

This corrective corpus is permanently not frozen and non-authoritative. Theorem, promotion, and release authority default to disabled.

## 1. Authority rule

A result becomes authoritative only when every portable binding and all eight independent external gates are verified. Portable regression evidence cannot activate authority.

## 2. Cache integrity

Cached envelopes must canonically bind principal, idempotency slot, request, claim, policy, source, proof artifact, compiler profile, compiler witness, result, signer, and chronology before historical rotation classification.

## 3. Service authentication

Proof-service → publisher and publisher → anchor mutations require both Linux `SO_PEERCRED` allowlisting and a signed canonical request bound to the operation, principal, payload digest, deadline, request ID, nonce, target service, and exact socket identity. Root is not implicitly trusted. World-writable sockets fail closed.

## 4. Audit-key lifecycle

Every record, receipt, checkpoint, seal, recovery artifact, and anchor state resolves an applicable governance-signed registry snapshot and recomputes signer status, validity, revocation, principal, scope, and rotation lineage at the artifact timestamp. Rotation cycles fail. Record, receipt, checkpoint/recovery, and anchor scopes are distinct.

## 5. Anchor semantics

Inside a segment, an anchor accepts only an exact idempotent no-op or `sequence = previous + 1`. Namespace, epoch, segment, registry hashes, transition authorization, and predecessor binding are immutable. Every new state binds the previous anchor-state SHAKE256-512.

The file-backed anchor is development-only and cannot enable authority because its storage owner may restore an older valid prefix. Activation requires a genuinely independent monotonic trust domain.

## 6. Segment succession

Genesis requires separate governance authorization. A successor requires a governance-signed transition, verified sealed checkpoint, actual terminal record, current anchor, and signer lifecycle. The canonical terminal-record SHAKE256-512 must equal both checkpoint and anchor tails; outer record and embedded seal must identify the actual predecessor segment.

Normal event capacity reserves a terminal-seal slot and byte budget.

## 7. Idempotency and recovery

A global durable publisher-domain event-ID index survives sealing, successor provisioning, restart, and timeout reconciliation. Recovery authorizations require `created_at <= now < expires_at`, a short maximum lifetime, exact before-state and file identities, and one-time durable consumption. Replay fails closed.

## 8. Durability

All writes use complete-write loops. Logs and ledgers are size-checked before allocation and read in bounded chunks. Partial writes, ENOSPC, temporary cleanup, and restart recovery are governed and tested.

## 9. Production execution

The integration executes proof UID/GID 65534 → publisher UID/GID 65533 → anchor UID/GID 65532. Both real proof loaders run after privilege drop. A real event is durably published, a signed receipt is verified, the anchor advances, restart replay reconciles the duplicate, and an unrelated UID is denied.

## 10. External gates

Authority remains disabled until strict Lean, strict TLC, governed hermetic image execution, signed OCI attestation, signed verifier attestation, reproducible inspector builds, clean committed-source provenance, and external governance authorization all pass independently.
