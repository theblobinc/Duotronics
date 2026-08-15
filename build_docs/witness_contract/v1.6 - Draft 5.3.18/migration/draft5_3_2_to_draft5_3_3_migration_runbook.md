# Migration runbook — Draft 5.3.2 to Draft 5.3.3

1. Stop theorem-promotion writes and take a verified database backup.
2. Register the SQLite canonical-JSON, SHAKE256-512, key-fingerprint, and ML-DSA-87
   functions from `executable/runtime/proof_authority.py`.
3. Apply, in order, the 5.2.2→5.3.1, 5.3.1→5.3.2, and
   `draft5_3_2_to_draft5_3_3.sql` migrations.
4. Provision a governance public key only through the deployment's external
   trust-anchor ceremony. The migration intentionally provisions no trust key.
5. Issue signed governance authorization witnesses and signed v2 activation
   events for verifier keys that remain authorized. Unsigned v1 lifecycle rows
   remain historical and cannot authorize a 5.3.3 gate.
6. Re-run every theorem through the governed hermetic compiler profile. Earlier
   compiler witnesses lack the immutable snapshot and dependency-closure fields
   and are ineligible for new gates.
7. Create a signed authority snapshot and query
   `wc_authoritative_theorems_as_of_v3` for deterministic replay.
8. Run the complete 5.3.3 validator and retain its report with the migration
   evidence. Roll back by restoring the pre-migration backup; do not delete
   append-only authority records.
