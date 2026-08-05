# Migration Runbook — Draft 5.3.13 to Draft 5.3.14

## Purpose

Draft 5.3.14 replaces the Draft 5.3.13 single mutable audit chain with checkpointed signed segments, makes publication deadline-aware, upgrades stale evidence to v4, and repairs current-revision regeneration and documentation.

## Mandatory preconditions

- Keep theorem, promotion, and release authority disabled.
- Preserve the Draft 5.3.13 package and its SHA-256 as predecessor lineage evidence.
- Stop all proof-check workers before provisioning or rotating audit state.
- Install a dedicated audit signing key that is distinct from cache-envelope and compiler-witness signing keys.
- Provision a private audit-log directory and a separately protected checkpoint directory.

## Configuration changes

Add or update:

- `cache_audit_log_file`;
- `cache_audit_checkpoint_file`;
- `cache_audit_segment_id`;
- `cache_audit_previous_sealed_segment_tail_sha256`;
- dedicated audit signing and verification key paths;
- audit record, byte, and event-size bounds.

Production requires the log and checkpoint to have different parent directories. Ordinary startup must not provision either file.

## Genesis provisioning

1. Verify both directories are service-owned, private, non-symlinked, and on the intended protected storage.
2. Invoke the explicit provisioning path exactly once while workers are stopped.
3. Record the newly created segment ID and signed checkpoint outside the mutable log storage.
4. Start one worker and require full log/checkpoint verification.
5. Start the remaining workers only after the first startup succeeds.

Competing genesis creation, missing state, or a checkpoint/log mismatch is an integrity failure.

## Existing Draft 5.3.13 audit data

Draft 5.3.13 logs are not silently promoted to checkpointed v2 segments. Preserve them as predecessor audit artifacts. A governed migration may:

1. verify the complete Draft 5.3.13 chain with the predecessor implementation;
2. produce a signed migration attestation containing its final record digest;
3. provision the Draft 5.3.14 genesis segment with that attested digest as external predecessor context; and
4. retain both the old log and migration attestation in protected archival storage.

Do not edit, truncate, or rewrite the predecessor log in place.

## Segment rotation

1. Stop admission of new stale-row publications for the segment.
2. Acquire the segment lock within a governed deadline.
3. Append and fsync a signed `cache_audit_segment_seal/v1` terminal event.
4. Atomically persist and fsync the sealed checkpoint.
5. Copy or anchor the sealed segment and checkpoint to external append-only storage.
6. Provision the successor with `previous_sealed_segment_tail_sha256` equal to the terminal seal record digest.
7. Start workers and require successor/predecessor binding verification.

An unsealed predecessor or mismatched predecessor tail is rejected.

## Request deadline behavior

The proof-check request deadline now governs audit lock acquisition, verification, append, fsync, checkpoint replacement, and directory fsync. Capacity planning must reserve enough request budget for the configured maximum segment scan and durable writes. Budget exhaustion returns `cache_audit_publication_failed`; it must not be retried under the same idempotency key without operator review of audit state.

## Schema changes

Activate:

- `cache_stale_row_evidence/v4`;
- `cache_verification_evidence/v1`;
- `cache_audit_record/v2`;
- `cache_audit_checkpoint/v1`;
- `cache_audit_segment_seal/v1`.

Retain prior schemas only as explicitly classified legacy inputs. Unknown event schemas fail closed.

## Validation

Run the README workflow from a clean source copy. In particular, remove and regenerate the Draft 5.3.14 schema registry and require byte equality. Require all 94 portable phases to pass and treat each of the eight external activation gates independently.

## Rollback

Application rollback does not authorize audit rollback. Preserve every Draft 5.3.14 segment and checkpoint. Never restore an earlier valid prefix as current state. If rollback of the executable is necessary, stop proof-check traffic and preserve the current sealed or unsealed audit state for forensic review.
