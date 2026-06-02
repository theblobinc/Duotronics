# Release Notes - v1.7 Draft 1.1

Draft 1.1 completes first-class promotion work identified in Draft 1 review.

## Added

- SQL, OpenAPI, fixtures, validator checks, and formal surface parity for `BayesianModel`, `BayesianDecisionWitness`, and `BayesianCalibrationReport`.
- New `BayesianUpdateReplayWitness` for exact/bounded replay semantics.
- SQL, OpenAPI, fixtures, validator checks, and Lean parity for `KnotBraidWordWitness`.
- New first-class `KnotEquivalenceAuthorityPath`.
- New `KnotReidemeisterTraceWitness`.
- New `KnotCanonicalizationWitness`.
- New `KnotInvariantCompletenessWitness`.
- Promoted Bayesian/knot non-collapse primitive categories.
- Normalization/domain convention registry.
- TLA+ first-class-promotion invariant module.

## Changed

- Knot theory is now framed as a first-class witness facility, not a second-class addendum.
- `KnotEquivalenceWitness` now requires `authority_path_id`.
- Bayesian likelihoods allow negative values only under `log_likelihood` semantics, enforced by validator.
- Exact Bayesian updates are replay-checked against prior × likelihood normalization.

## Still not frozen

Draft 1.1 remains an implementation-review candidate pending strict deployment CI, human review, and environment-specific Lake/TLC authority checks.
