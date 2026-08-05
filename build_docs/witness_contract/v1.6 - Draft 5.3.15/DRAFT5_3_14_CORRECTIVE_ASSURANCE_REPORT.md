# Draft 5.3.14 Corrective Assurance Report

Draft 5.3.14 closes the portable audit-integrity, request-deadline, regeneration, documentation, and audit-self-containment findings identified in the independent Draft 5.3.13 review.

## Rollback-resistant segmented audit

Production audit state is no longer inferred from the mutable JSONL segment alone. Each provisioned segment has a separately stored, canonical, signed checkpoint binding the segment identifier, expected sequence, expected tail-record SHA-256, predecessor sealed-segment tail, signer key, creation time, and segment status.

Ordinary production startup opens the segment and checkpoint without `O_CREAT`, verifies every audit record and embedded event, and requires the reconstructed segment tail to equal the protected checkpoint. Missing files, valid-prefix truncation, old-segment restoration, checkpoint mismatch, competing genesis, and unsealed successor transitions fail as `cache_audit_integrity_invalid`.

Segment rotation uses a signed terminal `cache_audit_segment_seal/v1` event. A successor segment is provisioned only with the predecessor terminal-record hash and cannot begin an unrelated genesis. Separate checkpoint storage is required in production; external append-only, WORM, or transparency-log anchoring remains the preferred deployment shape.

## Deadline-bounded publication

The request-wide monotonic deadline is passed into cache replay and audit publication. Audit locking uses nonblocking attempts bounded by the remaining budget. Deadline checks cover lock acquisition, full chain and checkpoint verification, append, record-file fsync, atomic checkpoint replacement, checkpoint-file fsync, and directory fsync.

Budget exhaustion cannot return a successful rotation classification. It produces the stable fail-closed `cache_audit_publication_failed` result. Regression coverage includes held-lock and delayed-fsync cases.

## Self-contained audit evidence

`cache_stale_row_evidence/v4` binds the exact verified envelope through its signed-payload SHA-256, canonical full-envelope SHA-256, and original envelope signature in addition to all request, principal, slot, policy, source, witness, and chronology bindings.

The sink maintains an allowlisted event-schema registry. Every event is canonicalized and schema-validated before signing and again during startup verification. The outer `event_schema_version` must equal the embedded `schema_version`; unknown event types and malformed signed event payloads are rejected.

## Reproducible regeneration and documentation

The root workflow invokes `build_schema_registry_v5314.py`. Required tests remove the current registry from a temporary source copy, regenerate it, and require exact-byte equality. The README now describes the actual Draft 5.3.14 changes and the precise integration limitation: UID/GID 65534 is representable, but the sandbox denies the `/proc` bind mount required by the descriptor-anchored SQLite chroot harness.

## Regression result

Current-revision Python evidence is generated independently for each available target interpreter. Python 3.13.5 is validated; Python 3.12 remains explicitly unavailable and receives no inherited claim. The active validator has 94 required portable phases and eight independent external activation gates.

## Remaining limits

The real non-root production-loader harness remains `environment_unavailable` until executed in a suitable multi-UID environment with the required procfs projection or an equivalent descriptor-anchored SQLite mechanism. All eight external activation gates remain incomplete. Theorem, promotion, and release authority remain disabled, and the corpus remains permanently not frozen.
