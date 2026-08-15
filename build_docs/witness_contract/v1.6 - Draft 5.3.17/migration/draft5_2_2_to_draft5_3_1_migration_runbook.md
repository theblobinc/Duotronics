# Draft 5.2.2 to Draft 5.3.1 Migration Runbook

## Safety model

Draft 5.3.1 does not alter old authority tables in place. `CREATE TABLE IF NOT EXISTS` cannot strengthen constraints on a table that already exists, and mutating prior witness rows would destroy evidence. The migration creates a parallel v2 authority generation and quarantines legacy authority identifiers from automatic promotion.

## New installation

1. Enable SQLite foreign keys.
2. Apply `executable/sql/draft5_2_schema_additions.sql` for the carried evidence-language substrate.
3. Apply `migration/draft5_2_2_to_draft5_3_1.sql` once.
4. Run the canonical validator.
5. Direct new authority writes only to `wc_*_v2` tables.

## Existing installation

1. Stop authority-producing writes.
2. Make and independently verify a database backup.
3. Run `PRAGMA foreign_key_check` and `PRAGMA integrity_check`.
4. Apply `migration/draft5_2_2_to_draft5_3_1.sql` in one transaction.
5. Confirm schema generation `v1.6-draft-5.3.1` in `wc_schema_generations`.
6. Confirm every legacy compiler/proof/gate identifier appears in `wc_legacy_authority_quarantine` when the old table exists.
7. Re-run proof checks from original claim, statement, source, and artifact bytes. Insert new v2 records only from the controlled verifier.
8. Switch read paths to the v2 derived views and leave v1 rows available for replay.
9. Run adversarial, immutability, and happy-path tests before reopening writes.

## Rollback

Application rollback means switching code back to v1 read paths while retaining the additive v2 tables. Do not delete v2 evidence. A later governance-approved cleanup may deprecate tables only after retention and replay requirements are satisfied.

## Legacy semantics

Migration of identifiers is not migration of authority. A legacy row may be referenced as historical evidence, but it cannot satisfy a v2 theorem gate. The quarantine reason is `missing_v2_content_signature_binding` until a controlled re-verification produces new records.
