Draft 5.2.2 additive update: Lean proof authority integration is included and SQL persistence has been hardened to match the schemas. The root now contains a Lake package, proof witness schemas, a check_proof syscall, SQL/OpenAPI persistence, and a theorem promotion gate.

# Duotronic Witness Contract v1.6 Draft 5.2 - Completion Candidate

**Status:** Completed Draft 5.2 review candidate; not frozen for release.  
**Generated:** 2026-05-11.  
**Base:** v1.6 Draft 5.2 uploaded corpus plus consistency-pass supplements.  
**Primary contract:** `duotronic_witness_contract_v1_6_draft_5_2.md`.  
**Start file:** `START_HERE.md`.

## Purpose

This package is a standalone evidence-language operating corpus for Duotronic v1.6 Draft 5.2.
It preserves the Draft 5.1 NLA authority and safety layer while completing the Draft 5.2 formal language of evidence around:

1. Syntax of evidence.
2. Pragmatics of authority.
3. Semiotics of replay.
4. Metaphysics of non-collapse.

The completed package supplies first-class evidence claims, compositional claims, inference witnesses, replay assumptions, verification grammars, pragmatic force markers, authority delegation chains, non-collapse states and transitions, SQL persistence, OpenAPI runtime surface, fixtures, and validation helpers.

## Non-freeze rule

This corpus is complete enough to implement and review, but it is intentionally marked as a **completion candidate**. Do not freeze it until implementation tests, human review, and runtime conformance have passed.

## Core operating rule

An AI or runtime may use this corpus as an operating specification only if it preserves all non-collapse distinctions. It must never silently transform unknown into invalid, absence into zero, computation into proof, conjecture into theorem, policy approval into truth, self-trained behavior into authority, or audit witness into activation-backed fact.

## Fast path

1. `START_HERE.md`
2. `EVIDENCE_LANGUAGE_OPERATING_SYSTEM_PRIMER_v1_0.md`
3. `duotronic_witness_contract_v1_6_draft_5_2.md`
4. `CORPUS_INDEX_v1_6_draft_5_2.md`
5. `DRAFT5_2_COMPLETION_REVIEW_REPORT_v1_0.md`
6. `refs/schema_registry_v1_6_draft_5_2_completed.md`
7. `schemas/evidence_claim.schema.json`
8. `schemas/compound_claim_witness.schema.json`
9. `schemas/inference_witness.schema.json`
10. `schemas/non_collapse_state.schema.json`
11. `schemas/non_collapse_transition.schema.json`
12. `schemas/replay_assumption_manifest.schema.json`
13. `schemas/verification_grammar.schema.json`
14. `executable/sql/draft5_2_schema_additions.sql`
15. `executable/openapi/draft5_2_evidence_language_openapi.yaml`
16. `executable/validators/validate_draft5_2_2_corpus.py`

## Compatibility

Draft 5.2 completes the evidence-language layer. Draft 5.1 remains authoritative for NLA self-training, release promotion, rollback, activation witness safety, truth-observer authority, and audit-only restrictions unless an active Draft 5.2 file explicitly strengthens the rule.

## Logical observer kernel update

This package also includes the Draft 5.2 logical observer kernel addendum. The evidence language defines the objects and transitions; the kernel defines the deterministic machine that runs them. Start with `kernel/logical_observer_kernel_contract_v1_0.md`, then load `executable/kernel/logical_observer_kernel_syscalls.yaml`, the observer/task/transaction/error schemas in `schemas/`, and `refs/normative_rule_coverage_matrix_v1_6_draft_5_2.json`.

## TLA+ Formal Toolchain Integration

Draft 5.2.2 includes both the TLA+ formal execution surface and a Lean/Lake proof-authority surface. Use `python executable/formal/run_tla_model_check.py --mode advisory` for portable TLA checks, `--mode strict` when `TLA2TOOLS_JAR` or `tools/tla2tools.jar` is available, and `python executable/formal/run_lean_build.py --mode advisory --json` for portable Lean static checks. Production theorem promotion requires strict Lean proof authority: an actual `lake build` pass must produce a `LeanCompilerWitness` before theorem/proof_verified status can be committed.


## Draft 5.2.2 freeze-blocker closure

Draft 5.2.2 closes documentation drift from 5.2.1 and strengthens SQL persistence to match the JSON schemas: theorem/proof_verified claims, transitions, and inference witnesses now require Lean compiler witness references and theorem promotion gate references where applicable. Allowed theorem promotion gates are guarded by SQLite foreign keys and triggers binding them to an existing passing `LeanCompilerWitness`, a proved `ProofWitness`, and a matching prove transition. Strict `lake build` and strict TLC execution remain CI/toolchain responsibilities when those tools are installed; advisory runners record unavailable toolchains without authorizing theorem promotion.


## Draft 5.2.2 corrective hardening

The SQL persistence layer now requires exact theorem-gate witness-ID membership: allowed theorem promotion gates must match the proof and Lean compiler witness IDs present in the claim and transition JSON arrays, not merely non-empty arrays.
