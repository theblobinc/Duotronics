# Start Here — Duotronic Witness Contract v1.6 Draft 5.3.12

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_12.json` only.
2. Confirm `v1.6-draft-5.3.12`, permanent-unfrozen lifecycle, and disabled authority defaults.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_12.json` and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_12.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_12.json`; unclassified schemas fail closed.
5. Read `duotronic_witness_contract_v1_6_draft_5_3_12.md` and `migration/draft5_3_11_to_draft5_3_12_migration_runbook.md`.
6. Run `python3 executable/validators/validate_draft5_3_12_corpus.py` and require every descriptor-required phase to pass.
7. Treat `validation/production_loader/draft5_3_12_nonroot_loader_evidence.json` as passing only when its `status` is `passed`; `environment_unavailable` never satisfies production integration.
8. Keep authority disabled unless all eight external activation gates independently pass.

Python evidence is assembled from one current-revision record per target interpreter by `executable/validators/generate_draft5_3_12_python_evidence.py`. Validated and unavailable targets must be disjoint and each target must appear exactly once.

This standalone package contains no predecessor ZIP payloads. Historical archive hashes in `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_12.json` are lineage only.
