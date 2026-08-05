# Release Notes — v1.6 Draft 5.3.14

Draft 5.3.14 is a standalone, permanently-not-frozen, non-authoritative corrective development corpus based on Draft 5.3.13. It embeds no predecessor ZIPs; predecessor hashes are informational lineage only.

## Closed Draft 5.3.13 findings

### Rollback- and deletion-resistant audit state

The signed audit log is now segmented and paired with a separately stored signed checkpoint. The checkpoint binds the expected segment ID, next sequence, current tail-record digest, previous sealed-segment tail, signer identity, creation time, and status.

Normal production startup does not create a missing log or checkpoint. It verifies the complete segment, all record signatures and hashes, every embedded event schema, and exact equality with the checkpoint. A valid-prefix truncation, complete deletion, old-segment restoration, empty replacement, competing genesis, checkpoint rollback, or unsealed transition returns `cache_audit_integrity_invalid`.

A governed rotation appends a signed terminal `cache_audit_segment_seal/v1` record. The successor segment binds the predecessor terminal-record SHA-256 and cannot start an unrelated chain. Production configuration requires the checkpoint to reside outside the mutable log directory. External WORM or transparency-log anchoring remains recommended for activation deployments.

### Audit publication obeys the request-wide deadline

The monotonic request deadline is propagated through historical cache replay and audit publication. Exclusive locking uses nonblocking attempts with deadline-bounded retries. Chain verification, append, record fsync, atomic checkpoint replacement, checkpoint fsync, and directory fsync are all budget checked.

A stale request can no longer exceed its governed deadline and still return `cache_key_rotation_requires_new_idempotency_key`. Lock or persistence budget exhaustion fails closed as `cache_audit_publication_failed`.

### Stale evidence binds the exact cache envelope

The active `cache_stale_row_evidence/v4` event adds:

- `cache_envelope_signed_payload_sha256`;
- `cache_envelope_canonical_sha256`;
- `cache_envelope_signature`.

These fields are verified before publication and allow the signed audit record to identify the exact original envelope independently of the SQLite row.

### Embedded audit events are schema-governed

The audit sink uses an allowlisted event-schema registry. Events are canonicalized and validated before append and again during startup verification. The outer event version must equal the embedded event version. Unknown or structurally invalid events are rejected even when the outer audit record is otherwise correctly signed.

### Current-revision regeneration is tested from absence

The documented workflow now runs:

```sh
python3 executable/validators/build_schema_registry_v5314.py
```

A required regression removes the current schema registry in a temporary source tree, regenerates it, and compares exact bytes. Packaged generated artifacts are no longer sufficient to mask a stale documented command.

### Root documentation is current

The root README describes the actual Draft 5.3.14 audit changes. It also records the production integration result precisely: UID/GID 65534 was representable, but the environment denied bind-mounting `/proc` into the chroot, so fd-anchored SQLite and both real production loaders remain unexecuted.

## Regression coverage

Draft 5.3.14 adds coverage for:

- valid-prefix truncation and complete log deletion;
- older segment and checkpoint restoration;
- competing genesis and unsealed successor creation;
- signed segment sealing and predecessor-tail binding;
- held audit locks and delayed persistence beyond the request budget;
- exact cache-envelope digest and signature binding;
- unknown or malformed embedded audit events;
- startup revalidation of signed event schemas;
- byte-exact schema-registry regeneration from absence.

The active portable validator contains 94 required phases. The eight external activation gates remain optional skipped phases until independently supplied.

## Environment qualification

Python 3.13.5 is available in the current build environment and is recorded using current-revision evidence. Python 3.12 is not installed and is explicitly recorded as unavailable, with no inherited Draft 5.3.13 execution claim.

The non-root production-loader harness remains accurately `environment_unavailable`: UID/GID 65534 was representable, but `/proc` could not be bind-mounted into the chroot. Neither production loader is represented as passing.

## Authority status

Strict Lean, strict TLC, governed hermetic image execution, signed OCI image build attestation, signed verifier executable attestation, reproducible inspector build attestation, clean committed-source provenance, and external governance authorization remain incomplete. Theorem, promotion, and release authority remain disabled.
