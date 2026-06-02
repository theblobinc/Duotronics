# Duotronic Witness Contract v1.7 Draft 1.3

**Status:** completed correctness-and-formal-integration candidate; not frozen for release.  
**Generated:** 2026-05-26.  
**Base:** v1.7 Draft 1.1 first-class Bayesian and knot promotion candidate.  
**Primary inherited contract:** `duotronic_witness_contract_v1_6_draft_5_2.md`.  
**v1.7 additions:** Bayesian top-order facility and first-class knot theory witness facility.  
**Start file:** `START_HERE.md`.

## Purpose

This package is a standalone evidence-language operating corpus for Duotronic v1.7 Draft 1.3. It preserves all v1.6 Draft 5.2.2 and v1.7 Draft 1.1 content while hardening the active v1.7 layer for reproducible validation, stronger formal integration, typed knot encodings, explicit Bayesian replay semantics, and split knot-presentation transition witnesses.

v1.7 Draft 1.3 adds and hardens these normative facilities:

1. **Bayesian logic top-order facility** with explicit model-family typing, reference replay algorithms, posterior predictive, marginalization, conditioning, negative-evidence/missing-data, calibration scoring, and decision-theory witnesses.
2. **Knot theory witness facility** with typed diagram payloads, split Reidemeister/braid/Markov transition witnesses, presentation-transition wrappers, braid generator semantic validation, and invariant-family registry coverage.

## Core operating rule

An AI or runtime may use this corpus only if it preserves all non-collapse distinctions. It must never silently transform unknown into invalid, absence into zero, computation into proof, conjecture into theorem, policy approval into truth, self-trained behavior into authority, posterior probability into fact, invariant equality into knot equivalence, canonical hash equality into proof, or audit witness into activation-backed fact.

## Fast path

1. `START_HERE.md`
2. `CORPUS_INDEX_v1_7_draft_1_3.md`
3. `BAYESIAN_LOGIC_TOP_ORDER_FACILITY_CONTRACT_v1_0.md`
4. `KNOT_THEORY_WITNESS_FACILITY_CONTRACT_v1_0.md`
5. `refs/schema_registry_v1_7_draft_1_3_completed.md`
6. `refs/normalization_convention_registry_v1_7_draft_1_3.md`
7. `refs/non_collapse_category_registry_v1_7_draft_1_3.md`
8. `refs/bayesian_reference_algorithms_v1_7_draft_1_2.md`
9. `refs/bayesian_calibration_scoring_registry_v1_7_draft_1_2.md`
10. `refs/knot_invariant_family_registry_v1_7_draft_1_2.md`
11. `executable/kernel/logical_observer_kernel_syscalls.yaml`
12. `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json`
13. `RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md`
14. `executable/sql/draft1_7_bayesian_knot_additions.sql`
15. `executable/openapi/draft1_7_bayesian_knot_openapi.yaml`
16. `executable/tests/draft1_7_bayesian_knot_conformance_vectors.json`
17. `executable/validators/validate_v1_7_draft_1_3_corpus.py`

## Compatibility

v1.7 Draft 1.3 is additive over v1.7 Draft 1.1. Existing v1.6 and v1.7 Draft 1.1 objects remain valid unless a Draft 1.3 object explicitly opts into stricter Bayesian or knot-theory witness semantics. The v1.6 theorem-promotion, proof-authority, non-collapse, NLA, replay, and SQL hardening rules remain in force.

## Validation

Run:

```bash
python executable/validators/validate_v1_7_draft_1_3_corpus.py
```

The Draft 1.3 validator hardens inherited validator execution for noisy Python environments, emits `DRAFT1_3_VALIDATION_REPORT.json`, separates corpus errors from environment/toolchain warnings, validates first-class schemas and fixtures, checks Bayesian replay semantics including log-space replay, validates typed knot encodings and braid generator bounds, verifies SQL/OpenAPI/kernel coverage, checks TLA manifest integration, and verifies package inventory integrity.

## Non-freeze rule

This corpus is complete enough to implement and review, but it remains a completion candidate. Do not freeze it until human review, runtime conformance, strict TLA/TLC where required, and strict Lean/Lake where required have passed and are recorded in `DRAFT1_3_FREEZE_BLOCKER_MATRIX.md`.
