# Draft 5.3.3 to Draft 5.3.4 Migration and Rollback Runbook

## Preconditions

1. Stop authority writes and take a restorable database snapshot.
2. Verify the Draft 5.3.3 schema generation and corpus hash closure.
3. Register the canonical JSON, SHA-256, authority-event-root, public-key
   fingerprint, and Ed25519 SQLite functions.
4. Keep theorem and promotion authority disabled.

## Apply

Apply, in one controlled migration chain:

```text
executable/sql/draft5_2_schema_additions.sql
migration/draft5_2_2_to_draft5_3_1.sql
migration/draft5_3_1_to_draft5_3_2.sql
migration/draft5_3_2_to_draft5_3_3.sql
migration/draft5_3_3_to_draft5_3_4.sql
```

The new migration adds action-scope mapping, v2 governance authorizations,
typed record indexing, compiler profiles, v3 compiler witnesses, the authority
event ledger, v2 ledger snapshots, v3 typed supersessions, release activation
evidence, v3 theorem gates, append-only triggers, and cutoff-aware views.

## Backfill

Existing verifier keys, promotion gates, compiler witnesses, and proof witnesses
are indexed for typed historical lookup. They are not re-signed, reinterpreted,
or upgraded to Draft 5.3.4 authority. Existing effective-time snapshots remain
legacy records. Create new event-ledger records and v2 snapshots prospectively.

Backdated corrections require their own authorization, correction reason,
affected-snapshot list, and correction mode. Do not alter earlier snapshots.

## Validation

Run the 5.3.4 validator and require all required phases to pass. Confirm:

- `PRAGMA foreign_key_check` is empty;
- event sequences are monotonic and append-only;
- snapshot event roots recompute at each cutoff;
- prior snapshots remain stable after later backdated events;
- typed supersession rejects invalid chains; and
- `wc_release_activation_evidence_v1` is empty unless externally governed
  release evidence has been provisioned.

## Rollback

SQLite DDL rollback after committed authority events is not logically lossless.
Restore the pre-migration database snapshot for a full rollback. Do not copy
5.3.4 signed records into 5.3.3 tables or silently reinterpret them. If 5.3.4
events must be retained during service rollback, preserve the database
read-only for replay and start a new 5.3.3-compatible write database under an
explicit operational incident record.
