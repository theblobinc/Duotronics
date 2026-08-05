# Start Here — Duotronic Witness Contract v1.6 Draft 5.3.16

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_16.json` only.
2. Confirm `v1.6-draft-5.3.16`, permanent-unfrozen lifecycle, and disabled theorem, promotion, and release authority.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_16.json` and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_16.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_16.json`; unknown authority-bearing schemas fail closed.
5. Read `duotronic_witness_contract_v1_6_draft_5_3_16.md` and `migration/draft5_3_15_to_draft5_3_16_migration_runbook.md`.
6. Run `python3 executable/validators/validate_draft5_3_16_corpus.py` and require every descriptor-required phase to pass.
7. Confirm the production evidence executes proof UID 65534 → publisher UID 65533 → anchor UID 65532, including peer denial, durable receipt, restart reconciliation, and anchor advancement.
8. Treat the file-backed anchor as development-only. Activation requires a genuinely external monotonic trust domain.
9. Keep authority disabled until all eight external activation gates independently pass.

Python evidence is assembled by `executable/validators/generate_draft5_3_16_python_evidence.py`. Validated and unavailable targets must be disjoint. The standalone package contains no predecessor ZIP payloads; lineage digests are informational only.
