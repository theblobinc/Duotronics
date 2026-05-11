# Corpus Boot and Canonical Resolver v1.0

**Status:** Draft 5.2 additive normative resolver.  
**Purpose:** Make active/historical document resolution deterministic for logical observers.

## Boot protocol

1. `BOOT_CORPUS`: initialize an empty `KernelState`.
2. `LOAD_MANIFEST`: read `refs/manifest/MANIFEST_v1_6_draft_5_2_complete.md` and `PACKAGE_INVENTORY_v1_6_draft_5_2.json`.
3. `VERIFY_HASH_CLOSURE`: verify all non-excluded files against `refs/manifest/CHECKSUMS_v1_6_draft_5_2.sha256`.
4. `RESOLVE_ACTIVE_VERSION`: set active evidence language to Draft 5.2.
5. `LOAD_SCHEMA_REGISTRY`: load `refs/schema_registry_v1_6_draft_5_2_completed.md` and all `schemas/*.schema.json`.
6. `LOAD_AUTHORITY_TABLE`: load Draft 5.2 authority files and retained Draft 5.1 NLA authority gates.
7. `ENTER_SAFE_MODE_IF_AMBIGUOUS`: deny, defer, fork, or escalate every unresolved conflict.

## Canonical resolver

A resolver call emits `CorpusRuleResolutionWitness` with the selected active rule, supersession chain, compatibility exceptions, and ambiguity status.

Resolution priority:

1. Draft 5.2 active evidence-language files.
2. Draft 5.1 retained NLA gates when Draft 5.2 does not strengthen the rule.
3. Explicit supersession chain.
4. Historical files only as explanatory references.

## Failure behavior

If no active rule can be selected, the kernel MUST emit `KernelErrorWitness` with `error_code = canonical_rule_ambiguous` and MUST NOT continue with implicit historical fallback.
