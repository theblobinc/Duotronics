# Corpus Review - v1.7 Draft 1 to v1.7 Draft 1.1

Draft 1.1 addresses the first-class promotion gaps found in Draft 1.

## Closed gaps

1. `BayesianModel` now has SQL, OpenAPI, fixture, validator, and Lean coverage.
2. `BayesianDecisionWitness` and `BayesianCalibrationReport` now have persistence and API coverage.
3. Bayesian exact update replay is validator-enforced by `BayesianUpdateReplayWitness`.
4. `KnotBraidWordWitness` now has SQL, OpenAPI, fixture, validator, and Lean coverage.
5. Knot equivalence authority paths are first-class via `KnotEquivalenceAuthorityPath`.
6. Reidemeister traces are first-class via `KnotReidemeisterTraceWitness`.
7. Canonicalization and collision policy are first-class via `KnotCanonicalizationWitness`.
8. Invariant completeness is first-class and proof-bound via `KnotInvariantCompletenessWitness`.
9. Bayesian/knot non-collapse categories are promoted into schemas.
10. Normalization and domain conventions are registered.

## Remaining freeze gates

- Strict target-environment Lake build.
- Strict target-environment TLC run.
- Human authority review.
- Production implementation conformance.
