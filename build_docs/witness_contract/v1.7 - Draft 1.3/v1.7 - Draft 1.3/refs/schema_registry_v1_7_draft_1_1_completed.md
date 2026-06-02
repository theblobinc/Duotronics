# Schema Registry Supplement - v1.7 Draft 1.1

## Status

Normative supplement to the inherited v1.6 Draft 5.2.2 schema registry and successor to `refs/schema_registry_v1_7_draft_1_completed.md`.

## Bayesian schemas

| Schema | Purpose |
|---|---|
| `schemas/bayesian_model.schema.json` | Declares Bayesian model, hypothesis space, observation space, and update method. |
| `schemas/bayesian_prior.schema.json` | Declares prior distribution and provenance. |
| `schemas/bayesian_likelihood.schema.json` | Declares observation likelihoods by hypothesis. |
| `schemas/bayesian_update_witness.schema.json` | Records update from prior and likelihood to posterior. |
| `schemas/bayesian_update_replay_witness.schema.json` | Replays or bounds an update and verifies model/hypothesis consistency. |
| `schemas/bayesian_posterior_state.schema.json` | Declares normalized posterior belief state. |
| `schemas/bayesian_decision_witness.schema.json` | Records decision support under posterior and utility/loss model. |
| `schemas/bayesian_calibration_report.schema.json` | Records calibration and scoring evidence. |

## Knot theory schemas

| Schema | Purpose |
|---|---|
| `schemas/knot_diagram_witness.schema.json` | Declares knot/link diagram presentation. |
| `schemas/knot_braid_word_witness.schema.json` | Declares braid word and closure convention. |
| `schemas/knot_reidemeister_move_witness.schema.json` | Records a checked diagram move. |
| `schemas/knot_reidemeister_trace_witness.schema.json` | Records an ordered replayable move trace. |
| `schemas/knot_invariant_witness.schema.json` | Records computed/proved invariant. |
| `schemas/knot_invariant_completeness_witness.schema.json` | Binds completeness claim to proof authority and domain. |
| `schemas/knot_canonicalization_witness.schema.json` | Declares canonicalization algorithm, domain, hash, and collision policy. |
| `schemas/knot_equivalence_authority_path.schema.json` | First-class authority path for equivalence. |
| `schemas/knot_equivalence_witness.schema.json` | Records equivalence claim and references first-class authority path. |

## Registry invariant

Every v1.7 Draft 1.1 first-class object must have schema, fixture, SQL persistence, OpenAPI surface, validator coverage, and formal surface parity unless explicitly marked optional. Bayesian posterior and knot equivalence objects require non-collapse references; knot equivalence requires `authority_path_id`.
