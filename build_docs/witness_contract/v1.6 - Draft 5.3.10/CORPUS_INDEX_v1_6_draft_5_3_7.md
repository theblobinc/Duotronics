# Corpus Index — v1.6 Draft 5.3.7

The canonical entry point is `CANONICAL_CORPUS_v1_6_draft_5_3_7.json`.

- Contract: `duotronic_witness_contract_v1_6_draft_5_3_7.md`
- Runtime: `executable/runtime/proof_authority.py`
- Trusted verifier: `executable/trusted_verifier/verify_lean.py`
- Sandbox profile: `authority/hermetic_lean_sandbox_profile_v4.json`
- Active schemas: effective invocation v4, verifier result v5, compiler witness v6, proof-check result v5
- Migration: `migration/draft5_3_6_to_draft5_3_7.sql`
- Formal model: `formal/draft5_3_7/ProofAuthorityV8.tla`
- Validator: `executable/validators/validate_draft5_3_7_corpus.py`
- Generated counts: `DRAFT5_3_7_REGRESSION_COUNTS.json`
- Release notes: `RELEASE_NOTES_v1_6_draft_5_3_7.md`

Drafts 5.2.2 through 5.3.6 are retained exactly under `history/source_packages/`. They remain historical replay inputs, not active authority surfaces.
