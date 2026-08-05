# Corpus Index — Duotronic Witness Contract v1.6 Draft 5.3.2

**Status:** active corrective development corpus; not frozen.

## Canonical root set

- `CANONICAL_CORPUS_v1_6_draft_5_3_2.json`
- `README.md`
- `START_HERE.md`
- `duotronic_witness_contract_v1_6_draft_5_3_2.md`
- `RELEASE_NOTES_v1_6_draft_5_3_2.md`
- `PACKAGE_INVENTORY_v1_6_draft_5_3_2.json`
- `refs/manifest/CHECKSUMS_v1_6_draft_5_3_2.sha256`
- `refs/manifest/MANIFEST_v1_6_draft_5_3_2_complete.md`
- `refs/schema_registry_v1_6_draft_5_3_2.json`
- `DRAFT5_3_2_VALIDATION_REPORT.json`

## Canonical executable layer

- `executable/runtime/proof_authority.py` — exact theorem-statement build and compiled axiom inspection.
- `executable/tests/test_proof_authority.py` — authority bypass regression suite.
- `executable/validators/validate_draft5_3_2_corpus.py` — descriptor-reconciled fail-closed validator.
- `executable/validators/validate_draft5_3_2_schemas.mjs` — vendored AJV schema/fixture runner.
- `executable/tests/test_positive_baseline.py`
- `executable/runtime/positive_baseline.py`
- `executable/sql/draft5_2_schema_additions.sql`
- `migration/draft5_2_2_to_draft5_3_1.sql`
- `migration/draft5_3_1_to_draft5_3_2.sql`
- `executable/openapi/draft5_3_2_evidence_language_openapi.yaml`

## Canonical authority schemas

The registry names the v2 claim/compiler/proof/gate generations, the v3 verifier-key registration, append-only key-status events, cryptographic signature bindings, replay objects, supersession, and positive-baseline computation records.

## Formal layer

- `refs/formal_toolchain/tla_toolchain_manifest_v1_0.json` is the only active TLA module list.
- `formal/draft5_3_1/ProofAuthorityV2.tla` and `.cfg` are active manifest entries.
- `formal/draft5_3_2/ProofAuthorityV3.tla` and `.cfg` model the new statement, axiom, signature, and effective-key requirements.
- Strict TLC for every manifest entry remains required before freeze.
- The existing Lean tree remains active; strict compilation remains required before freeze.

## Mathematical integration

- `mathematics/Duotronic_Positive_Baseline_Polygonal_Computation_v1.2.md`
- `mathematics/positive_baseline_witness_integration_profile_v1_0.md`
- `schemas/positive_baseline_cell_v1.schema.json`
- `executable/runtime/positive_baseline.py`

These objects produce computational evidence and do not bypass theorem promotion.

## Historical closure

The exact Draft 5.2.2 and Draft 5.3.1 source archives are under `history/source_packages/`. Historical manifests, reports, validators, and schemas remain evidence about their own generations and do not select active behavior.

## Hash closure

The active inventory, checksum file, human manifest, and validation report are explicit self-referential generated exclusions. Every other regular file—including vendored AJV runtime code and historical source archives—is listed with size and SHA-256.
