# Corpus Index — v1.6 Draft 5.3.11

The canonical entry point is `CANONICAL_CORPUS_v1_6_draft_5_3_11.json`.

- Contract: `duotronic_witness_contract_v1_6_draft_5_3_11.md`
- Runtime: `executable/runtime/proof_authority.py`
- Authenticated boundary: `executable/runtime/proof_check_service.py` and `executable/runtime/proof_check_wsgi.py`
- Trusted compiler/inspector: `executable/trusted_verifier/compile_lean.py` and `executable/trusted_verifier/verify_lean.py`
- Sandbox profile: `authority/hermetic_lean_sandbox_profile_v5.json`
- Active cache schemas: envelope v3 and cache-signing registry v2
- Active Lean schemas: invocation v5, handoff v3, verifier request v5/result v6, compiler witness v8
- Active service schemas: proof request v2/result v7 and dual-domain evidence v1
- Service migration: `migration/draft5_3_10_to_draft5_3_11_migration_runbook.md`
- Formal model: `formal/draft5_3_7/ProofAuthorityV8.tla`
- Validator: `executable/validators/validate_draft5_3_11_corpus.py`
- Python evidence generator: `executable/validators/generate_draft5_3_11_python_evidence.py`
- Generated counts: `DRAFT5_3_11_REGRESSION_COUNTS.json`
- Release notes: `RELEASE_NOTES_v1_6_draft_5_3_11.md`
- Predecessor digest lineage: `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_11.json`

No historical source-package ZIP is embedded. Lineage digests are informational and do not participate in active authority selection.
