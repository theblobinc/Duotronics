# Start Here - Duotronic Witness Contract v1.7 Draft 1.1

**Status:** completed first-class-promotion implementation-review candidate, not frozen.  
**Generated:** 2026-05-26.  
**Base:** v1.7 Draft 1 Bayesian top-order and knot witness draft.  
**Active package metadata:** `PACKAGE_METADATA_v1_7_draft_1_1.json`.  
**Active corpus index:** `CORPUS_INDEX_v1_7_draft_1_1.md`.  
**Active validator:** `executable/validators/validate_v1_7_draft_1_1_corpus.py`.

## What changed in Draft 1.1

Draft 1.1 carries out the first-class promotion review. It adds persistence, API, fixture, validator, kernel, Lean, TLA, and registry coverage for objects that Draft 1 named but did not fully wire.

Promoted or completed objects:

1. `BayesianModel`
2. `BayesianDecisionWitness`
3. `BayesianCalibrationReport`
4. `BayesianUpdateReplayWitness`
5. `KnotBraidWordWitness`
6. `KnotEquivalenceAuthorityPath`
7. `KnotReidemeisterTraceWitness`
8. `KnotCanonicalizationWitness`
9. `KnotInvariantCompletenessWitness`
10. Bayesian/knot non-collapse primitive categories
11. Normalization and domain convention registries

## Operating sequence

1. Boot the inherited v1.6 Draft 5.2.2 evidence-language layer.
2. Load the logical observer kernel in `executable/kernel/logical_observer_kernel_syscalls.yaml`.
3. Load the v1.7 Draft 1.1 schema supplement in `refs/schema_registry_v1_7_draft_1_1_completed.md`.
4. Load normalization/domain conventions from `refs/normalization_convention_registry_v1_7_draft_1_1.md`.
5. Load non-collapse category supplement from `refs/non_collapse_category_registry_v1_7_draft_1_1.md`.
6. Persist v1.7 objects through `executable/sql/draft1_7_bayesian_knot_additions.sql`.
7. Expose v1.7 objects through `executable/openapi/draft1_7_bayesian_knot_openapi.yaml`.
8. Validate with `python executable/validators/validate_v1_7_draft_1_1_corpus.py`.

## Safety invariant

No runtime may silently collapse posterior probability into proof, invariant equality into knot equivalence, diagram or braid presentation into isotopy class, canonical hash equality into proof, or decision support into policy approval. Every promotion requires an explicit witness, policy decision, replay/checking path, and non-collapse transition.
