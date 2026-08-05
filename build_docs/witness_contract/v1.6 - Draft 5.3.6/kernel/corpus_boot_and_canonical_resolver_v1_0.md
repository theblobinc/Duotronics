# Corpus Boot and Canonical Resolver v1.6

**Status:** Draft 5.3.6 normative resolver; permanently not frozen.

## Boot protocol

1. Enter safe mode.
2. Load only `CANONICAL_CORPUS_v1_6_draft_5_3_6.json`.
3. Require `v1.6-draft-5.3.6`, permanent-unfrozen lifecycle, unique phases,
   disabled authority defaults, and every selected artifact.
4. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_6.json` against final files and
   `refs/manifest/CHECKSUMS_v1_6_draft_5_3_6.sha256`.
5. Load `refs/schema_registry_v1_6_draft_5_3_6.json`; unclassified schemas
   fail, and earlier generations are replay-only unless reverified and rewritten.
6. Require package provenance; `unpublished_workspace` disables activation.
7. Run `python3 executable/validators/validate_draft5_3_6_corpus.py` and
   reconcile required phases by exact ID.
8. Load policy-bound authority runtime, explicit-entrypoint two-domain
   verifier, measured sandbox v3, compiler witness v5, synchronous API, event
   ledger, cutoff snapshot, typed supersession, and Draft 5.3.6 migration.
9. Require ProofAuthority V2 through V7 in the formal manifest.
10. Enter safe mode on ambiguity; never infer active behavior from filenames.

## Resolution priority

1. Draft 5.3.6 descriptor and active contract.
2. Draft 5.3.6 policy, schemas, runtime, trusted wrappers, SQL, API, validator,
   sandbox, formal model, provenance, and release evidence.
3. Draft 5.3.5 definitions not superseded by 5.3.6.
4. Earlier definitions not superseded later.
5. Historical artifacts for explanation and replay only.

Legacy witnesses, policies, and snapshots are never upgraded by interpretation.
The portable corpus provisions no release activation and lacks committed-source
and external activation evidence, so theorem authority remains disabled.
