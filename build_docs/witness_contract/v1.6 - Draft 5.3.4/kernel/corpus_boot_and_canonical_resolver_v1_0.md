# Corpus Boot and Canonical Resolver v1.4

**Status:** Draft 5.3.4 normative resolver; permanently unfrozen.

## Boot protocol

1. Enter safe mode.
2. Load only `CANONICAL_CORPUS_v1_6_draft_5_3_4.json`.
3. Require `v1.6-draft-5.3.4`, permanent-unfrozen lifecycle, unique phases,
   disabled default authority, and every selected artifact.
4. Verify `PACKAGE_INVENTORY_v1_6_draft_5_3_4.json` against
   `refs/manifest/CHECKSUMS_v1_6_draft_5_3_4.sha256`.
5. Load `refs/schema_registry_v1_6_draft_5_3_4.json`; earlier generations are
   replay-only unless reverified and rewritten under active schemas.
6. Run the canonical validator and reconcile required phases by exact ID.
7. Load the snapshot-first runtime, two-domain verifier, signed-result schema,
   event ledger, ledger snapshot, typed supersession, and sandbox v2.
8. Require ProofAuthority V2, V3, V4, and V5 in the formal manifest.
9. Enter safe mode on ambiguity; never infer active behavior from filenames.

## Resolution priority

1. Draft 5.3.4 descriptor and active contract.
2. Draft 5.3.4 schemas, runtime, trusted verifier, SQL, API, validator,
   sandbox, formal model, and release evidence.
3. Draft 5.3.3 definitions not superseded by 5.3.4.
4. Earlier definitions not superseded later.
5. Historical artifacts for explanation and replay only.

Legacy witnesses and snapshots are never upgraded by interpretation. The
portable corpus provisions no release-activation row, so theorem authority
remains disabled by construction.
