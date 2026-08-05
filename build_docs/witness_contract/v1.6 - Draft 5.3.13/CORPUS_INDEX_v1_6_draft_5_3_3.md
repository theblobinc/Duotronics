# Corpus Index — Duotronic Witness Contract v1.6 Draft 5.3.3

**Status:** complete active living draft; permanently not frozen.

## Canonical roots

- `CANONICAL_CORPUS_v1_6_draft_5_3_3.json`
- `START_HERE.md`
- `duotronic_witness_contract_v1_6_draft_5_3_3.md`
- `RELEASE_NOTES_v1_6_draft_5_3_3.md`
- `PACKAGE_INVENTORY_v1_6_draft_5_3_3.json`
- `refs/manifest/CHECKSUMS_v1_6_draft_5_3_3.sha256`
- `refs/schema_registry_v1_6_draft_5_3_3.json`
- `DRAFT5_3_3_VALIDATION_REPORT.json`

## Executable authority layer

- `executable/runtime/proof_authority.py`
- `executable/runtime/proof_check_service.py`
- `executable/tests/test_proof_authority.py`
- `executable/tests/test_sql_authority_lifecycle_v533.py`
- `executable/formal/run_hermetic_proof_authority_integration.py`
- `authority/hermetic_lean_sandbox_profile_v1.json`
- `migration/draft5_3_2_to_draft5_3_3.sql`
- `executable/openapi/draft5_3_3_evidence_language_openapi.yaml`

## Formal layer

- `formal/draft5_3_1/ProofAuthorityV2.tla`
- `formal/draft5_3_2/ProofAuthorityV3.tla`
- `formal/draft5_3_3/ProofAuthorityV4.tla`
- `refs/formal_toolchain/tla_toolchain_manifest_v1_0.json`
- `refs/formal_toolchain/lean_toolchain_manifest_v1_0.json`

## Mathematical layer

The v1.2 positive-baseline paper, integration profile, schema, evaluator, and
tests remain canonical computational-evidence components.

## Historical closure

Exact Draft 5.2.2, 5.3.1, and 5.3.2 ZIP archives are retained under
`history/source_packages/`. They never select active behavior.

The active inventory, checksum file, human manifest, and validation report are
the four explicit self-referential hash exclusions. Every other regular file is
listed with size and SHA-256.
