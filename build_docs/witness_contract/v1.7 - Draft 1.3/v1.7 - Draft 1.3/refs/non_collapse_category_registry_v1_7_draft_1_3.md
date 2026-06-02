# Draft 1.3 Active Alias for `non_collapse_category_registry_v1_7_draft_1_2.md`

# Non-Collapse Category Registry Supplement - v1.7 Draft 1.2

## Status

Normative supplement to `schemas/non_collapse_state.schema.json` and `schemas/non_collapse_transition.schema.json`.

## Promoted categories

- `probabilistic_prior`
- `probabilistic_likelihood`
- `probabilistic_posterior`
- `bayesian_decision_support`
- `bayesian_calibration_evidence`
- `knot_diagram_presentation`
- `knot_braid_presentation`
- `knot_reidemeister_trace`
- `knot_invariant_evidence`
- `knot_canonical_form`
- `knot_equivalence_claim`

## Rule

These are primitive non-collapse categories, not metadata fallbacks. A v1.7 Draft 1.2 runtime MUST use these categories for Bayesian and knot transitions and MUST NOT collapse them into generic `computational_evidence` unless emitting a backward-compatibility projection witness.


## Draft 1.2 added categories

- `bayesian_posterior_predictive`
- `bayesian_marginalization`
- `bayesian_conditioning`
- `bayesian_negative_evidence`
- `bayesian_decision_loss_model`
- `knot_braid_relation_transition`
- `knot_markov_transition`
- `knot_presentation_transition`


---

## Draft 1.3 Redo Supplement

This Draft 1.3 alias is the active reader entrypoint. It carries forward the Draft 1.2 registry semantics and explicitly binds them to Draft 1.3's SQL persistence registry, runtime semantic boundary, expanded positive fixture coverage, duplicate Bayesian hypothesis-ID rejection, and deeper typed knot-encoding semantic validation.

Active companions:

- `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json`
- `RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md`
- `executable/tests/draft1_7_bayesian_knot_conformance_vectors.json`
- `executable/validators/validate_v1_7_draft_1_3_corpus.py`
