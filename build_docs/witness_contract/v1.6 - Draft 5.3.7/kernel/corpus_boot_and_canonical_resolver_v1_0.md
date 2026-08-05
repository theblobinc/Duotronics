# Corpus Boot and Canonical Resolver v1.7

**Status:** Draft 5.3.7 normative resolver; permanently not frozen.

## Boot protocol

1. Enter safe mode and load only `CANONICAL_CORPUS_v1_6_draft_5_3_7.json`.
2. Require `v1.6-draft-5.3.7`, permanent-unfrozen lifecycle, unique validation phases, disabled authority defaults, and all selected artifacts.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_7.json` against final files and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_7.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_7.json`; unclassified schemas fail, and earlier generations remain replay-only unless reverified and rewritten.
5. Require package provenance; `unpublished_workspace` disables activation.
6. Run `python3 executable/validators/validate_draft5_3_7_corpus.py` and reconcile required phases by exact identifier.
7. Load sandbox profile v4, effective invocation v4, verifier result v5, compiler witness v6, proof-check result v5, and the Draft 5.3.7 migration.
8. Require ProofAuthority V2 through V8 in the formal manifest.
9. Enter safe mode on ambiguity; never infer active behavior from filenames.

## Resolution priority

1. Draft 5.3.7 descriptor and active contract.
2. Draft 5.3.7 policy, schemas, runtime, wrappers, SQL, API, validator, sandbox, formal model, provenance, and release evidence.
3. Draft 5.3.6 definitions not expressly superseded by Draft 5.3.7.
4. Earlier definitions not superseded later.
5. Historical artifacts for explanation and replay only.

Legacy witnesses, policies, and snapshots are never upgraded by interpretation. Portable validation supplies no external activation evidence, so theorem, promotion, and release authority remain disabled.
