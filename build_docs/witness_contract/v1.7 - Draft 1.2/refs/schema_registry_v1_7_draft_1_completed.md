# Schema Registry Supplement - v1.7 Draft 1

## Status

Normative supplement to the inherited v1.6 Draft 5.2.2 schema registry.

## Bayesian schemas

| Schema | Purpose |
|---|---|
| `schemas/bayesian_model.schema.json` | Declares Bayesian model, hypothesis space, observation space, and update method. |
| `schemas/bayesian_prior.schema.json` | Declares prior distribution and provenance. |
| `schemas/bayesian_likelihood.schema.json` | Declares observation likelihoods by hypothesis. |
| `schemas/bayesian_update_witness.schema.json` | Records update from prior and likelihood to posterior. |
| `schemas/bayesian_posterior_state.schema.json` | Declares normalized posterior belief state. |
| `schemas/bayesian_decision_witness.schema.json` | Records decision under posterior and utility/loss model. |
| `schemas/bayesian_calibration_report.schema.json` | Records calibration and scoring evidence. |

## Knot theory schemas

| Schema | Purpose |
|---|---|
| `schemas/knot_diagram_witness.schema.json` | Declares knot/link diagram presentation. |
| `schemas/knot_braid_word_witness.schema.json` | Declares braid word and closure convention. |
| `schemas/knot_reidemeister_move_witness.schema.json` | Records a checked diagram move. |
| `schemas/knot_invariant_witness.schema.json` | Records computed/proved invariant. |
| `schemas/knot_equivalence_witness.schema.json` | Records equivalence claim and authority path. |

## Registry invariant

Every v1.7 schema object must carry `schema_version`, an object-specific ID, and enough provenance for replay or refusal. Bayesian posterior and knot equivalence objects require non-collapse references or explicit refusal metadata.
