# Draft 5.3.5 to Draft 5.3.6 migration runbook

Draft 5.3.6 is additive. Preserve the 5.3.5 database and take an independently verified backup before applying the migration.

1. Register the SQLite canonical-JSON, SHA-256, and Ed25519 verification functions used by the prior migrations.
2. Enable `PRAGMA foreign_keys = ON` and verify `PRAGMA foreign_key_check` returns no rows.
3. Apply all migrations through `draft5_3_4_to_draft5_3_5.sql` if the database is older.
4. Apply `migration/draft5_3_5_to_draft5_3_6.sql` inside its transaction.
5. Confirm generation `v1.6-draft-5.3.6`, the v5 witness/gate tables, append-only triggers, and the authority-disabled view.
6. Do not copy v4 witnesses into v5. Re-run proof checks under the 5.3.6 runtime because the new execution, limit, handoff, dependency-closure, and trust-registry bindings cannot be inferred from older records.

Rollback is restore-only. The new authority records are append-only; do not drop or rewrite them in place.
