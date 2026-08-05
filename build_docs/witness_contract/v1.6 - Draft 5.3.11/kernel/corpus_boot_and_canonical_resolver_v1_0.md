# Corpus Boot and Canonical Resolver v1.0

**Status:** Draft 5.3.11 normative resolver; permanently not frozen.

## Boot algorithm

1. Enter safe mode and load only `CANONICAL_CORPUS_v1_6_draft_5_3_11.json`.
2. Require `v1.6-draft-5.3.11`, permanent-unfrozen lifecycle, unique validation phases, disabled authority defaults, and all selected artifacts.
3. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_11.json` against final files and `refs/manifest/CHECKSUMS_v1_6_draft_5_3_11.sha256`.
4. Load `refs/schema_registry_v1_6_draft_5_3_11.json`; unclassified schemas fail, and earlier generations remain replay-only unless reverified and rewritten.
5. Reject any embedded ZIP source package. Load `history/SOURCE_PACKAGE_LINEAGE_v1_6_draft_5_3_11.json` only as non-authoritative digest lineage.
6. Run `python3 executable/validators/validate_draft5_3_11_corpus.py` and reconcile required phases by exact identifier.
7. Load sandbox profile v5, invocation v5, compile handoff v3, verifier request v5/result v6, compiler witness v8, proof request v2/result v7, cache envelope v3, and cache-signing registry v2.
8. Require a verified middleware principal before policy, cache, verifier, witness, or result processing.
9. Treat completed cache records as untrusted and reverify current policy, signed envelope, signed witness, authorized signer, status chronology, and every request/principal/content binding. A superseded registry requires a new idempotency key.
10. Keep theorem, promotion, and release authority disabled unless all eight external activation phases pass and external governance authorization is valid.

## Precedence

1. Draft 5.3.11 descriptor and active contract.
2. Draft 5.3.11 policy, schemas, runtime, wrappers, API, validator, sandbox, provenance, and release evidence.
3. Earlier definitions not expressly superseded by Draft 5.3.11, under their original replay semantics.

Historical filenames do not select authority. Only the active descriptor and its exact referenced paths do.
