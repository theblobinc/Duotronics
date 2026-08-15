# Corpus Index — Duotronic Witness Contract v1.6 Draft 5.3.4

**Status:** corrective development draft; permanently not frozen.

## Canonical roots

- `CANONICAL_CORPUS_v1_6_draft_5_3_4.json`
- `START_HERE.md`
- `duotronic_witness_contract_v1_6_draft_5_3_4.md`
- `RELEASE_NOTES_v1_6_draft_5_3_4.md`
- `SPEC_CHANGE_REQUEST_v1_6_draft_5_3_4.json`
- `PACKAGE_INVENTORY_v1_6_draft_5_3_4.json`
- `refs/manifest/CHECKSUMS_v1_6_draft_5_3_4.shake256_512`
- `refs/schema_registry_v1_6_draft_5_3_4.json`
- `DRAFT5_3_4_VALIDATION_REPORT.json`

## Executable authority layer

- `executable/runtime/proof_authority.py`
- `executable/runtime/proof_check_service.py`
- `executable/trusted_verifier/compile_lean.py`
- `executable/trusted_verifier/verify_lean.py`
- `executable/tests/test_proof_authority.py`
- `executable/tests/test_sql_authority_lifecycle_v534.py`
- `authority/hermetic_lean_sandbox_profile_v2.json`
- `migration/draft5_3_3_to_draft5_3_4.sql`
- `executable/openapi/draft5_3_4_evidence_language_openapi.yaml`

## Active schemas

- `schemas/governed_compiler_registry_v2.schema.json`
- `schemas/effective_sandbox_invocation_v1.schema.json`
- `schemas/lean_verifier_result_v2.schema.json`
- `schemas/lean_compiler_witness_v3.schema.json`
- `schemas/governance_authorization_witness_v2.schema.json`
- `schemas/governance_event_v1.schema.json`
- `schemas/authority_snapshot_v2.schema.json`
- `schemas/authority_supersession_v3.schema.json`
- `schemas/build_attestation_v1.schema.json`
- `schemas/release_activation_evidence_v1.schema.json`
- `schemas/theorem_promotion_gate_v3.schema.json`

## Formal and mathematical layers

ProofAuthority V2–V5, the Draft 5.3.4 structural Lean inspector, formal
toolchain manifests, and the positive-baseline/bijective mathematical profile
remain part of the active corpus.

## Historical closure

Exact Draft 5.2.2, 5.3.1, 5.3.2, and 5.3.3 ZIPs are retained under
`history/source_packages/` and never select active behavior. The inventory,
checksum file, human manifest, and validator report are the four explicit
self-referential hash exclusions; every other regular file is SHAKE256-512 covered.
