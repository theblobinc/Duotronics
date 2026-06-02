# Draft 1.3 Active Alias for `normalization_convention_registry_v1_7_draft_1_2.md`

# Normalization and Domain Convention Registry - v1.7 Draft 1.2

## Status

Normative registry for Bayesian and knot-theory replay semantics in v1.7 Draft 1.2.

## Bayesian likelihood conventions

| Convention ID | Meaning | Validator rule |
|---|---|---|
| `bayes:probability_mass:v1` | Hypothesis-conditional probabilities in ordinary probability space. | Values must be nonnegative and normally bounded by `[0, 1]` when used as probabilities. |
| `bayes:relative_likelihood:v1` | Non-normalized likelihood scores in ordinary space. | Values must be nonnegative; replay must normalize. |
| `bayes:log_likelihood:v1` | Log likelihood scores. | Negative values are allowed; replay must exponentiate or use log-sum-exp. |

## Knot conventions

| Convention ID | Meaning | Non-collapse rule |
|---|---|---|
| `knot:pd_code:v1` | Planar diagram code with ordered crossing tuples. | Presentation is not equivalence. |
| `knot:braid_standard_closure:v1` | Braid word interpreted under standard closure. | Braid presentation is not isotopy class without Markov/equivalence witness. |
| `knot:diagram_crossing_count:v1` | Count of crossings in submitted diagram only. | Computed support is not minimal crossing number or equivalence proof. |
| `knot:canonical_pd_sha256:v1` | SHA-256 over declared canonical PD payload. | Hash equality requires collision policy and payload replay. |

## Domain conventions

| Domain ID | Meaning |
|---|---|
| `domain:knot:diagram-identity:v1` | Exact presentation identity under declared encoding and relabeling policy. |
| `domain:knot:oriented-ambient-isotopy:v1` | Oriented ambient isotopy claims. |
| `domain:knot:braid-markov-equivalence:v1` | Braid closures compared through Markov-equivalence authority. |
| `domain:bayes:finite-discrete-hypotheses:v1` | Finite discrete hypothesis spaces with explicit hypothesis IDs. |

A runtime MUST reject or defer any v1.7 Draft 1.2 Bayesian/knot replay whose convention ID is missing from this registry or an explicit successor registry.


## Draft 1.2 added conventions

- `bayes:exact_discrete_bayes:v1` - linear-space finite discrete Bayes replay.
- `bayes:log_space_discrete_bayes:v1` - log-sum-exp finite discrete Bayes replay.
- `bayes:bounded_monte_carlo:v1` - approximate replay with explicit error bound.
- `knot:gauss_code:v1` - typed Gauss code payload convention.
- `knot:dowker_thistlethwaite:v1` - typed DT code payload convention.
- `knot:grid_diagram:v1` - typed grid diagram payload convention.
- `knot:braid_closure_payload:v1` - typed braid-closure payload convention.


---

## Draft 1.3 Redo Supplement

This Draft 1.3 alias is the active reader entrypoint. It carries forward the Draft 1.2 registry semantics and explicitly binds them to Draft 1.3's SQL persistence registry, runtime semantic boundary, expanded positive fixture coverage, duplicate Bayesian hypothesis-ID rejection, and deeper typed knot-encoding semantic validation.

Active companions:

- `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json`
- `RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md`
- `executable/tests/draft1_7_bayesian_knot_conformance_vectors.json`
- `executable/validators/validate_v1_7_draft_1_3_corpus.py`
