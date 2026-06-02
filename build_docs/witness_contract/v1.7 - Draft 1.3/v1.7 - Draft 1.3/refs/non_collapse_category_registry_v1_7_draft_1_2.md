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
