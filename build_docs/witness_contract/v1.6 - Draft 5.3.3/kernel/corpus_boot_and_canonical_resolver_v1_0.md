# Corpus Boot and Canonical Resolver v1.3

**Status:** Draft 5.3.3 normative resolver; living contract; permanently unfrozen.

## Boot protocol

1. Initialize an empty safe-mode kernel state.
2. Load only `CANONICAL_CORPUS_v1_6_draft_5_3_3.json` as root selector.
3. Require version `v1.6-draft-5.3.3`, permanent-unfrozen lifecycle policy,
   unique phase identifiers, and every selected artifact to exist.
4. Load `PACKAGE_INVENTORY_v1_6_draft_5_3_3.json` and verify every covered
   entry with `refs/manifest/CHECKSUMS_v1_6_draft_5_3_3.sha256`.
5. Load `refs/schema_registry_v1_6_draft_5_3_3.json`; older writes are legacy.
6. Run the canonical validator and reconcile every required phase by identifier.
7. Load Draft 5.3.3 governed registry, immutable snapshot, structured result,
   signed governance, and as-of replay rules before retained definitions.
8. Require ProofAuthority V2, V3, and V4 in the active TLA manifest.
9. Enter safe mode on ambiguity; never infer an active generation from names.

## Resolution priority

1. Draft 5.3.3 descriptor and active-delta contract.
2. Draft 5.3.3 schemas, runtime, service, SQL migration, API, validator, sandbox,
   and formal manifest.
3. Draft 5.3.2 definitions not superseded by 5.3.3.
4. Draft 5.3.1 and Draft 5.2 definitions not superseded later.
5. Historical artifacts for explanation and replay only.

Legacy compiler witnesses are not upgraded by interpretation. They require a new
5.3.3 governed hermetic verification. Unsigned v1 key events and supersessions
remain history and cannot authorize new theorem gates.
