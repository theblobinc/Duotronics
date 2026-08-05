# Corpus Boot and Canonical Resolver v1.2

**Status:** Draft 5.3.2 normative resolver.  
**Purpose:** Select one active corpus generation without filename inference or historical fallback.

## Boot protocol

1. `BOOT_CORPUS`: initialize an empty safe-mode `KernelState`.
2. `LOAD_DESCRIPTOR`: read `CANONICAL_CORPUS_v1_6_draft_5_3_2.json`; no other file selects the active generation.
3. `VALIDATE_DESCRIPTOR`: require `active_version = v1.6-draft-5.3.2`, `freeze_state = not_frozen`, unique phase identifiers, and every referenced artifact to exist.
4. `LOAD_INVENTORY`: read `PACKAGE_INVENTORY_v1_6_draft_5_3_2.json`.
5. `VERIFY_HASH_CLOSURE`: verify every non-excluded entry against `refs/manifest/CHECKSUMS_v1_6_draft_5_3_2.sha256`.
6. `LOAD_SCHEMA_REGISTRY`: read `refs/schema_registry_v1_6_draft_5_3_2.json`; older generations are legacy-read only unless explicitly reverified.
7. `VALIDATE_EXECUTABLE_SURFACE`: run the declared validator and reconcile every required descriptor phase with one same-named result. Missing, failed, or skipped required phases are boot failures.
8. `LOAD_AUTHORITY`: load Draft 5.3.2 exact statement binding, compiled axiom inspection, signature verification, and effective-key rules before retained definitions.
9. `LOAD_FORMAL_MANIFEST`: require both active proof-authority models and configurations in the strict TLA manifest. Static coverage is not strict TLC evidence.
10. `ENTER_SAFE_MODE_IF_AMBIGUOUS`: deny, defer, fork, or escalate every unresolved conflict.

## Resolution priority

1. Canonical Draft 5.3.2 descriptor and active-delta contract.
2. Draft 5.3.2 schemas, runtime, SQL migration, API, validator, and formal manifest.
3. Draft 5.3.1 definitions not superseded by 5.3.2.
4. Draft 5.2 language-of-evidence definitions not superseded later.
5. Historical artifacts for explanation and replay only.

Every resolver call emits a `CorpusRuleResolutionWitness` with selected rule, version, supersession chain, compatibility exception, ambiguity status, and descriptor hash.

## Failure behavior

The kernel enters safe mode when the descriptor is missing, more than one generation is active, a hash fails, a required phase lacks a same-named result, a signature binding is absent, a verifier key is not currently effective, or a formal manifest omits an active authority model. It emits `KernelErrorWitness(error_code = canonical_rule_ambiguous)` and never falls back implicitly.

## Legacy proof records

Draft 5.3.1 and earlier compiler witnesses, proof witnesses, and gates are not upgraded by interpretation. They require byte-level re-verification through the Draft 5.3.2 authority service. Until then they remain replayable observations without current theorem-promotion authority.
