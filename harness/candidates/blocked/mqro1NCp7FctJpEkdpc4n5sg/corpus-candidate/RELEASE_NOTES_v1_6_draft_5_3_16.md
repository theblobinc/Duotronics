# Release Notes — v1.6 Draft 5.3.16

Draft 5.3.16 is a standalone, permanently-not-frozen, non-authoritative corrective development corpus based on Draft 5.3.15. It embeds no predecessor ZIPs.

## Portable corrections

- Publisher and anchor mutation endpoints require Linux `SO_PEERCRED` authorization and signed canonical requests bound to the target socket identity.
- Audit key lifecycle is recomputed from governance-signed registry snapshots at every record, receipt, checkpoint, seal, recovery, and anchor timestamp. Cycles, expiry, revocation, principal mismatch, and scope confusion fail closed.
- Same-segment anchors accept only exact no-op or sequence-plus-one transitions. Governance fields are immutable and states hash-chain to their predecessor.
- The file-backed anchor is explicitly development-only and cannot activate authority; a genuinely external monotonic backend remains required.
- Successor provisioning proves that the supplied terminal record is the actual checkpoint and anchor tail and identifies the actual predecessor segment.
- Publisher-domain event IDs are globally indexed across segment rotation and restart.
- Recovery authorizations are time-bounded, exact-state-bound, one-time, and replay-protected.
- Production publisher and anchor launchers are included.
- The integration executes proof UID 65534 → publisher UID 65533 → anchor UID 65532, publishes a real event, verifies a signed receipt, advances the anchor, restarts, reconciles a duplicate, and denies an unrelated UID.
- Complete-write loops and bounded ledger handling are used for durability paths.

## Validation and authority

The active descriptor contains 108 required portable phases and eight optional external activation phases. Python 3.12 receives no current-revision claim when unavailable. Portable completion does not substitute for strict Lean, strict TLC, governed hermetic image execution, signed image and verifier attestations, reproducible inspector builds, committed-source provenance, or external governance authorization. Theorem, promotion, and release authority remain disabled.
