# Start Here - Duotronic Witness Contract v1.7 Draft 1.3

**Status:** completed correctness-and-formal-integration candidate, not frozen.  
**Generated:** 2026-05-26.  
**Base:** v1.7 Draft 1.1 first-class Bayesian and knot promotion candidate.  
**Active package metadata:** `PACKAGE_METADATA_v1_7_draft_1_3.json`.  
**Active corpus index:** `CORPUS_INDEX_v1_7_draft_1_3.md`.  
**Active validator:** `executable/validators/validate_v1_7_draft_1_3_corpus.py`.

## What changed in Draft 1.3

Draft 1.3 carries out the requested correctness-and-formal-integration pass. It keeps Draft 1.1's first-class promotion, then hardens reproducibility, formal linkage, mathematical semantics, and validator coverage.

Promoted or hardened objects:

1. `BayesianModel` now carries explicit `model_family` semantics.
2. `BayesianUpdateWitness` and `BayesianUpdateReplayWitness` now bind reference algorithm IDs, including log-space replay.
3. `BayesianPosteriorPredictiveWitness`, `BayesianMarginalizationWitness`, `BayesianConditioningWitness`, `BayesianNegativeEvidenceWitness`, and `BayesianLossMatrixWitness` are first-class Draft 1.3 Bayesian objects.
4. `BayesianCalibrationReport` now has registry-backed scoring definitions.
5. `KnotReidemeisterMoveWitness` is restricted to Reidemeister/isotopy moves only.
6. `KnotBraidRelationWitness`, `KnotMarkovMoveWitness`, and `KnotPresentationTransitionWitness` are split into first-class objects.
7. `KnotDiagramWitness.encoding_payload` is typed for PD code, Gauss code, Dowker-Thistlethwaite code, grid diagrams, braid closures, and declared implementation-defined payloads.
8. `KnotBraidWordWitness` uses explicit generator-bound and zero-exponent policy semantics.
9. TLA module `BayesianKnotFirstClassPromotion` is integrated into the formal toolchain manifest and runner status.
10. The validator emits a structured JSON report with corpus errors, environment warnings, and toolchain warnings.
11. Draft 1.3 closes the schema-SQL persistence drift with `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json` and valid-fixture SQL round trips.
12. Draft 1.3 adds structured OpenAPI rejection, lookup, and computed replay responses.
13. Draft 1.3 expands the Bayesian/knot TLA module to record-level replay and authority-path invariants.

## Operating sequence

1. Boot the inherited v1.6 Draft 5.2.2 evidence-language layer.
2. Load the logical observer kernel in `executable/kernel/logical_observer_kernel_syscalls.yaml`.
3. Load the v1.7 Draft 1.3 schema supplement in `refs/schema_registry_v1_7_draft_1_3_completed.md`.
4. Load normalization/domain conventions from `refs/normalization_convention_registry_v1_7_draft_1_3.md`.
5. Load non-collapse category supplement from `refs/non_collapse_category_registry_v1_7_draft_1_3.md`.
6. Load Bayesian reference algorithms from `refs/bayesian_reference_algorithms_v1_7_draft_1_2.md`.
7. Load knot invariant family semantics from `refs/knot_invariant_family_registry_v1_7_draft_1_2.md`.
8. Load schema-SQL persistence mappings from `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json`.
9. Apply the SQL semantic boundary in `RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md`.
10. Persist v1.7 objects through `executable/sql/draft1_7_bayesian_knot_additions.sql`.
11. Expose v1.7 objects through `executable/openapi/draft1_7_bayesian_knot_openapi.yaml`.
12. Validate with `python executable/validators/validate_v1_7_draft_1_3_corpus.py`.

## Safety invariant

No runtime may silently collapse posterior probability into proof, invariant equality into knot equivalence, diagram or braid presentation into isotopy class, canonical hash equality into proof, or decision support into policy approval. Every promotion requires an explicit witness, policy decision, replay/checking path, and non-collapse transition.
