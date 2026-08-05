# Start Here — Duotronic Witness Contract v1.6 Draft 5.3.8

## Canonical boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_8.json` only.
2. Confirm `v1.6-draft-5.3.8`, the permanent-unfrozen lifecycle, and disabled authority defaults.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_8.json` and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_8.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_8.json`; unclassified schemas fail closed.
5. Read `duotronic_witness_contract_v1_6_draft_5_3_8.md` and `migration/draft5_3_7_to_draft5_3_8_migration_runbook.md`.
6. Run `python3 executable/validators/validate_draft5_3_8_corpus.py` and require every descriptor-required phase to pass.

## Active corrective surfaces

- `authority/hermetic_lean_sandbox_profile_v5.json`
- `schemas/effective_sandbox_invocation_v5.schema.json`
- `schemas/lean_verifier_request_v5.schema.json`
- `schemas/lean_verifier_result_v6.schema.json`
- `schemas/lean_compiler_witness_v7.schema.json`
- `schemas/proof_check_request_v2.schema.json`
- `schemas/proof_check_result_v6.schema.json`
- `schemas/idempotency_cache_envelope_v1.schema.json`
- `executable/runtime/proof_check_service.py`
- `executable/runtime/proof_check_wsgi.py`
- `DRAFT5_3_8_REGRESSION_COUNTS.json`
- `DRAFT5_3_8_PYTHON_MATRIX_VALIDATION.json`

The WSGI boundary accepts identity only through the trusted `witness.authenticated_principal_id` middleware key. Request bodies cannot assert a subject. Completed cache rows are never authoritative by themselves: the signed envelope, current policy, compiler-witness signature, signer authorization, status, and every request/principal/content binding are checked again.

## Authority state

The portable package is regression evidence only. Strict Lean, strict TLC, governed hermetic-image execution, signed OCI-image build attestation, signed verifier-executable attestation, reproducible inspector-build attestation, clean committed-source provenance, and external governance authorization are separate incomplete gates. Theorem, promotion, and release authority remain disabled.
