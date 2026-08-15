# Corpus Index — Duotronic Witness Contract v1.6 Draft 5.3.1

**Status:** active development corpus; complete corrective build; not frozen.

## Canonical root set

- `CANONICAL_CORPUS_v1_6_draft_5_3_1.json`
- `README.md`
- `START_HERE.md`
- `duotronic_witness_contract_v1_6_draft_5_3_1.md`
- `RELEASE_NOTES_v1_6_draft_5_3_1.md`
- `PACKAGE_INVENTORY_v1_6_draft_5_3_1.json`
- `refs/manifest/CHECKSUMS_v1_6_draft_5_3_1.shake256_512`
- `refs/manifest/MANIFEST_v1_6_draft_5_3_1_complete.md`
- `refs/schema_registry_v1_6_draft_5_3_1.json`
- `DRAFT5_3_1_VALIDATION_REPORT.json`

## Canonical executable layer

- `executable/validators/validate_draft5_3_1_corpus.py`
- `executable/validators/validate_draft5_3_1_schemas.mjs`
- `executable/tests/test_positive_baseline.py`
- `executable/runtime/positive_baseline.py`
- `executable/sql/draft5_2_schema_additions.sql`
- `migration/draft5_2_2_to_draft5_3_1.sql`
- `executable/openapi/draft5_3_1_evidence_language_openapi.yaml`

## Canonical v2 schemas

The machine-readable registry is authoritative. Its v2 set covers claims, verifier principals, compiler witnesses, proof witnesses, non-collapse transitions, status events, theorem gates, replay assumptions, verification grammars/results, supersession, and positive-baseline cells.

## Mathematical integration

- `mathematics/Duotronic_Positive_Baseline_Polygonal_Computation_v1.2.md` — carried source specification.
- `mathematics/positive_baseline_witness_integration_profile_v1_0.md` — Witness Contract binding.
- `schemas/positive_baseline_cell_v1.schema.json` — syntactic record contract.
- `executable/runtime/positive_baseline.py` — semantic evaluator.

## Formal layer

- Existing Draft 5.2 Lean and TLA+ material remains present.
- `Duotronic/ProofAuthorityV2.lean` states the strengthened abstract gate conjunction.
- `formal/draft5_3_1/proof_authority_v2.tla` models append-only promotion.
- Strict tool execution remains required before freeze.

## Migration and compatibility

- `migration/draft5_2_2_to_draft5_3_1_migration_runbook.md`
- `migration/draft5_2_2_to_draft5_3_1.sql`
- V1 object generations are readable but not canonical for writes.
- Legacy authority records enter a quarantine registry and require re-verification.

## Historical closure

All 492 files from the extracted Draft 5.2.2 corpus were carried forward before corrective additions. The exact uploaded source archive is retained under `history/source_packages/`. Historical inventories, checksums, reviews, and release notes remain evidence about their own generation and do not participate in active version selection.

## Hash closure

The 5.3.1 inventory, checksum file, human manifest, and validation report are generated artifacts excluded from their own recursive hash closure. Every other regular file is listed with size and SHAKE256-512. The exclusion is explicit per record and is not a validation skip.
