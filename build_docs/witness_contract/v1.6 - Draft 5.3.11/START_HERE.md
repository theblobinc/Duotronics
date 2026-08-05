# Start Here — Duotronic Witness Contract v1.6 Draft 5.3.11

## Canonical boot

1. Load `CANONICAL_CORPUS_v1_6_draft_5_3_11.json` only.
2. Confirm `v1.6-draft-5.3.11`, permanent-unfrozen lifecycle, and disabled authority defaults.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_11.json` and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_11.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_11.json`; unclassified schemas fail closed.
5. Read `duotronic_witness_contract_v1_6_draft_5_3_11.md` and `migration/draft5_3_10_to_draft5_3_11_migration_runbook.md`.
6. Run `python3 executable/validators/validate_draft5_3_11_corpus.py` and require every descriptor-required phase to pass.

## Active corrective surfaces

- `authority/hermetic_lean_sandbox_profile_v5.json`
- `schemas/effective_sandbox_invocation_v5.schema.json`
- `schemas/lean_verifier_request_v5.schema.json`
- `schemas/lean_compile_handoff_v3.schema.json`
- `schemas/lean_verifier_result_v6.schema.json`
- `schemas/lean_compiler_witness_v8.schema.json`
- `schemas/proof_check_request_v2.schema.json`
- `schemas/proof_check_result_v7.schema.json`
- `schemas/idempotency_cache_envelope_v3.schema.json`
- `schemas/cache_signing_registry_v2.schema.json`
- `schemas/domain_execution_evidence_v1.schema.json`
- `executable/runtime/proof_authority.py`
- `executable/runtime/proof_check_service.py`
- `executable/runtime/proof_check_wsgi.py`
- `executable/validators/generate_draft5_3_11_python_evidence.py`
- `DRAFT5_3_11_REGRESSION_COUNTS.json`
- `DRAFT5_3_11_PYTHON_MATRIX_VALIDATION.json`

The WSGI boundary accepts identity only through trusted `witness.authenticated_principal_id` middleware. Request bodies cannot assert a subject. Cache rows are untrusted: every hit re-resolves policy and re-verifies the cache envelope, compiler witness, signer, current registry chronology, and every request/principal/content binding.

## Authority state

The portable package is regression evidence only. All eight external activation gates remain incomplete. Theorem, promotion, and release authority remain disabled.
