# Start Here — Duotronic Witness Contract v1.6 Draft 5.3.15

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_15.json` only.
2. Confirm `v1.6-draft-5.3.15`, the permanently-not-frozen lifecycle, and disabled theorem, promotion, and release authority defaults.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_15.json` and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_15.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_15.json`; unknown authority-bearing schemas fail closed.
5. Read `duotronic_witness_contract_v1_6_draft_5_3_15.md` and `migration/draft5_3_14_to_draft5_3_15_migration_runbook.md`.
6. Run `python3 executable/validators/validate_draft5_3_15_corpus.py` and require every descriptor-required phase to pass.
7. Confirm `validation/production_loader/draft5_3_15_nonroot_loader_evidence.json` reports `passed` for both real loaders after actual UID/GID transition.
8. Treat the external monotonic anchor and separate audit publisher as required production trust domains; never replace them with proof-service-owned local files.
9. Keep authority disabled unless all eight external activation gates independently pass.

Python evidence is assembled from one current-revision record per target interpreter by `executable/validators/generate_draft5_3_15_python_evidence.py`. Validated and unavailable targets must be disjoint, and each target must appear exactly once.

This standalone package contains no predecessor ZIP payloads. Historical archive hashes in `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_15.json` are lineage only.
