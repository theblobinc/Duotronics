# Start Here — Duotronic Witness Contract v1.6 Draft 5.3.7

## Canonical boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_7.json` only.
2. Confirm version `v1.6-draft-5.3.7`, permanent-unfrozen lifecycle, and disabled authority defaults.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_7.json` and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_7.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_7.json`; unclassified schemas fail closed.
5. Read `duotronic_witness_contract_v1_6_draft_5_3_7.md` and the migration runbook.
6. Run `python3 executable/validators/validate_draft5_3_7_corpus.py` and require every descriptor-required phase to pass.

## Active corrective surfaces

- `authority/hermetic_lean_sandbox_profile_v4.json`
- `schemas/effective_sandbox_invocation_v4.schema.json`
- `schemas/lean_verifier_result_v5.schema.json`
- `schemas/lean_compiler_witness_v6.schema.json`
- `schemas/proof_check_result_v5.schema.json`
- `migration/draft5_3_6_to_draft5_3_7.sql`
- `formal/draft5_3_7/ProofAuthorityV8.tla`
- `DRAFT5_3_7_REGRESSION_COUNTS.json`

The active contract forbids the obsolete generic file-size control. It selects the compiler artifact limit for `untrusted_compilation` and the inspection output limit for `trusted_inspection`, binds that choice into the exact invocation and witnesses, and requires exact `rlimit_fsize` measurement.

## Authority state

The portable package is regression evidence only. Strict Lean, strict TLC, governed hermetic-image execution, signed OCI-image build attestation, signed verifier-executable attestation, reproducible inspector-build attestation, clean committed-source provenance, and external governance authorization are separate incomplete gates. Theorem, promotion, and release authority remain disabled.
