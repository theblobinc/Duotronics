# Corpus Boot and Canonical Resolver v1.1

**Status:** Draft 5.3.1 normative resolver.  
**Purpose:** Select one active corpus generation without filename inference or historical fallback.

## Boot protocol

1. `BOOT_CORPUS`: initialize an empty safe-mode `KernelState`.
2. `LOAD_DESCRIPTOR`: read `CANONICAL_CORPUS_v1_6_draft_5_3_1.json`; no other file can select the active generation.
3. `VALIDATE_DESCRIPTOR`: require `active_version = v1.6-draft-5.3.1`, `freeze_state = not_frozen`, and every referenced artifact to exist.
4. `LOAD_INVENTORY`: read `PACKAGE_INVENTORY_v1_6_draft_5_3_1.json`.
5. `VERIFY_HASH_CLOSURE`: verify every non-excluded entry against `refs/manifest/CHECKSUMS_v1_6_draft_5_3_1.sha256`.
6. `LOAD_SCHEMA_REGISTRY`: read `refs/schema_registry_v1_6_draft_5_3_1.json`; use its canonical-write schemas. V1 schemas are legacy-read only.
7. `VALIDATE_EXECUTABLE_SURFACE`: run the declared validator. Missing dependencies and required skipped checks are boot failures.
8. `LOAD_AUTHORITY`: load Draft 5.3.1 v2 authority rules, then retained Draft 5.1/5.2 rules only for non-conflicting definitions and legacy replay.
9. `ENTER_SAFE_MODE_IF_AMBIGUOUS`: deny, defer, fork, or escalate every unresolved conflict.

## Resolution priority

1. Canonical Draft 5.3.1 descriptor and active-delta contract.
2. Draft 5.3.1 v2 schemas, SQL migration, API, and profiles.
3. Draft 5.2 language-of-evidence definitions not superseded by 5.3.1.
4. Draft 5.1 NLA gates not superseded by later rules.
5. Historical artifacts for explanation and replay only.

Every resolver call emits a `CorpusRuleResolutionWitness` with selected rule, version, supersession chain, compatibility exception, ambiguity status, and descriptor hash.

## Failure behavior

If the descriptor is missing, two active generations are selected, a hash fails, a required schema is missing, or no active rule can be selected, the kernel emits `KernelErrorWitness(error_code = canonical_rule_ambiguous)` and does not continue with implicit fallback.

## Legacy proof records

Draft 5.2.2 compiler witnesses, proof witnesses, and gates are never upgraded by interpretation. They require byte-level re-verification through the v2 authority service. Until then they remain replayable observations with `legacy_untrusted_for_promotion` status.
