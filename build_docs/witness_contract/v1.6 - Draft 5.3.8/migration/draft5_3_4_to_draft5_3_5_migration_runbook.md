# Draft 5.3.4 → Draft 5.3.5 migration runbook

1. Back up the database and verify the Draft 5.3.4 checksum closure.
2. Register the five SQLite authority functions from `proof_authority.py`.
3. Enable foreign keys and apply migrations through 5.3.4 in order.
4. Apply `migration/draft5_3_4_to_draft5_3_5.sql` inside its transaction.
5. Import only governance-signed policy registries and decisions whose canonical
   hashes were independently recomputed.
6. Write new compiler witnesses and theorem gates only to the v4 tables. Older
   rows remain immutable replay records and never gain 5.3.5 authority by
   reinterpretation.
7. Confirm `wc_authoritative_theorems_v4` is empty until a genuine 5.3.5 release
   activation record exists. The portable corpus intentionally provides none.

Rollback is restore-from-backup. The migration is additive and append-only; do
not drop the new tables to conceal records that were already accepted.
