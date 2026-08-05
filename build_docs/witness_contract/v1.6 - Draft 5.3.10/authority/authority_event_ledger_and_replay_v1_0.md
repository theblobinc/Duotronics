# Authority Event Ledger and Replay Profile v1.0

Every authority event receives a monotonically increasing immutable sequence.
Every signed snapshot binds an effective time, ledger high-water sequence, and
canonical event-set root. Historical evaluation includes only events satisfying
both bounds.

A later-recorded event with an earlier effective time cannot enter an earlier
snapshot. It may enter a new snapshot only with explicit backdated correction
authorization and evidence. Snapshot supersession never deletes or rewrites the
superseded snapshot.

Governance authorization is exact by action scope, target type, target ID,
policy version, principal, and half-open validity interval. Lifecycle status is
derived from signed events, not direct mutable status fields.
