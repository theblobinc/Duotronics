# Draft 5.3.1 to Draft 5.3.2 Migration Runbook

**Status:** normative development runbook; not frozen.

1. Back up the database and verify the backup independently.
2. Stop authority writes while allowing read-only replay.
3. Register `wc_shake256_512`, `wc_public_key_fingerprint`, `wc_ml_dsa_87_verify`, and `wc_is_canonical_json` from `executable/runtime/proof_authority.py` on the migration connection.
4. Confirm the Draft 5.3.1 generation exists.
5. Apply `migration/draft5_3_1_to_draft5_3_2.sql` exactly once in its transaction.
6. Register public key bytes for every verifier intended for 5.3.2 authority and insert an initial active status event.
7. Do not synthesize signature bindings for historical compiler/proof rows. Re-run the exact Draft 5.3.2 proof check to create new signed records and verified bindings.
8. Confirm expired, revoked, retired, and superseded keys are absent from `wc_currently_valid_verifiers_v3`.
9. Confirm historical gates lacking 5.3.2 bindings are absent from `wc_authoritative_theorems_v2`.
10. Run the canonical validator and retain its report.

Rollback restores the verified backup. Do not attempt to remove append-only lifecycle or signature rows piecemeal.
