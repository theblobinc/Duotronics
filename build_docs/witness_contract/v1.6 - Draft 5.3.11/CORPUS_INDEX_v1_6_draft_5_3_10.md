# Corpus Index — v1.6 Draft 5.3.10

The canonical entry point is `CANONICAL_CORPUS_v1_6_draft_5_3_10.json`.

- Contract: `duotronic_witness_contract_v1_6_draft_5_3_10.md`
- Runtime: `executable/runtime/proof_authority.py`
- Authenticated service boundary: `executable/runtime/proof_check_service.py` and `proof_check_wsgi.py`
- Trusted verifier: `executable/trusted_verifier/verify_lean.py`
- Sandbox profile: `authority/hermetic_lean_sandbox_profile_v5.json`
- Active schemas: invocation v5, dual-domain execution evidence v1, compile handoff v2, verifier request v5/result v6, compiler witness v7, proof request v2/result v6, cache envelope v1, cache signing registry v1
- Latest authority SQL boundary: `migration/draft5_3_6_to_draft5_3_7.sql`
- Service migration: `migration/draft5_3_8_to_draft5_3_10_migration_runbook.md`
- Formal model: `formal/draft5_3_7/ProofAuthorityV8.tla`
- Validator: `executable/validators/validate_draft5_3_10_corpus.py`
- Generated counts: `DRAFT5_3_10_REGRESSION_COUNTS.json`
- Release notes: `RELEASE_NOTES_v1_6_draft_5_3_10.md`
- Predecessor digest lineage: `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_10.json`

No historical source-package ZIP is embedded. All changed source is merged into this standalone 5.3.10 corpus; lineage digests are informational and do not participate in active authority selection.
