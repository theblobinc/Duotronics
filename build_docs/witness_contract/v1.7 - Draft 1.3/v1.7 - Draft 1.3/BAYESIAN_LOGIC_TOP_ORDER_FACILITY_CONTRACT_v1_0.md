# Bayesian Logic Top-Order Facility Contract v1.0

## 1. Status

This file is normative for Duotronic Witness Contract v1.7 Draft 1.3.

Bayesian logic is promoted to a top-order epistemic facility. It is not a presentation-only addendum and not merely a statistical annotation on generic inference. A runtime that claims v1.7 Draft 1.3 Bayesian support MUST implement the witness objects, non-collapse distinctions, persistence hooks, replay checks, and validation gates described here.

## 2. Purpose

The Bayesian facility allows a runtime to represent, update, audit, replay, calibrate, and use probabilistic belief states for decision support while preserving all epistemic distinctions required by the witness contract.

## 3. Non-collapse distinctions

A Bayesian runtime MUST preserve these distinctions:

1. Prior is not posterior.
2. Likelihood is not observation.
3. Probability is not truth.
4. High posterior probability is not proof.
5. Calibration is not theorem authority.
6. Bayesian decision is not policy approval.
7. Model evidence is not human attestation.
8. Posterior update is not claim promotion unless a separate `ClaimStatusTransition` authorizes promotion.
9. Predictive success is not source integrity unless provenance is also witnessed.
10. Absence of data is not negative evidence unless the missingness model is explicit.
11. Replay success is not policy permission.
12. Log-likelihood values are not probabilities.

## 4. Bayesian object model

The v1.7 Draft 1.3 Bayesian layer defines these first-class witness objects:

- `BayesianModel`
- `BayesianPrior`
- `BayesianLikelihood`
- `BayesianUpdateWitness`
- `BayesianUpdateReplayWitness`
- `BayesianPosteriorState`
- `BayesianCalibrationReport`
- `BayesianDecisionWitness`

Every object above has schema, fixture, SQL persistence, OpenAPI surface, validator coverage, and Lean surface parity.

## 5. Canonical Bayesian update

The canonical discrete update form is:

```text
posterior(h_i) = prior(h_i) * likelihood(e | h_i) / sum_j(prior(h_j) * likelihood(e | h_j))
```

For `exact_discrete_bayes`, the runtime MUST be able to recompute the posterior from the declared prior and likelihood within validator tolerance. For `log_space_discrete_bayes`, likelihood values are log-likelihoods and may be negative; replay MUST use log-space semantics such as log-sum-exp or an equivalent declared deterministic grammar.

## 6. First-class replay rule

A Bayesian update is accepted only when it is accompanied by either:

- a `BayesianUpdateReplayWitness` with matching model, prior, likelihood, update, and posterior references; or
- a bounded approximation witness with explicit error bounds and refusal semantics for unbounded cases.

The hypothesis set MUST match across model, prior, likelihood, posterior, update witness, and replay witness.

## 7. Decision and calibration bounds

`BayesianDecisionWitness` is decision support. It may become policy-approved only when a separate policy decision witness is referenced. `BayesianCalibrationReport` is trust evidence. It may never become proof or theorem authority without proof promotion gates outside Bayesian logic.

## 8. Required syscalls

A v1.7 Draft 1.3 Bayesian runtime MUST expose:

- `bayes_model`
- `bayes_update`
- `bayes_replay_update`
- `bayes_calibrate`
- `bayes_decide`

## 9. Required schema invariants

1. Every model has at least two hypotheses.
2. Prior and posterior distributions must use the model hypothesis set.
3. Likelihood rows must use the model hypothesis set.
4. Probability values must be in `[0, 1]`.
5. Non-log likelihood values must be nonnegative.
6. Discrete probability distributions must sum to `1.0` within validator tolerance unless explicitly rejected.
7. Approximate updates must declare an error bound or a reason why one is unavailable.
8. Bayesian decisions must declare utility or loss semantics.
9. A policy-approved Bayesian decision must reference a policy decision witness.
10. Replay must verify model consistency and hypothesis-set consistency.

## 10. Non-collapse transition rule

Bayesian transitions MUST use the promoted primitive categories `probabilistic_prior`, `probabilistic_likelihood`, `probabilistic_posterior`, `bayesian_calibration_evidence`, and `bayesian_decision_support`. These are not metadata fallbacks.

## 11. Failure states

A runtime MUST fail closed for non-normalized posterior, missing model, missing prior reference, missing likelihood reference, hidden observation data, model version mismatch, hypothesis-set mismatch, posterior used as proof authority, Bayesian decision used as policy approval without policy witness, or exact update whose replay does not reproduce the posterior.


## Draft 1.2 hardening addendum

Bayesian models MUST declare `model_family`. Discrete, conjugate, graphical, hierarchical, particle/Monte Carlo, and external-verified families are distinguished. Log-likelihood replay MUST use `bayes:log_space_discrete_bayes:v1` and log-sum-exp semantics. Posterior predictive, marginalization, conditioning, negative/missing evidence, loss matrices, abstention thresholds, and human-review thresholds are first-class witness surfaces. Calibration scoring MUST reference the Draft 1.2 scoring registry.


## Draft 1.3 schema-SQL-runtime consistency addendum

Draft 1.3 closes the schema-to-SQL drift found during implementation review. Every required first-class Bayesian and knot schema field must either map to a SQL column in `executable/sql/draft1_7_bayesian_knot_additions.sql` or be declared in `refs/schema_sql_persistence_registry_v1_7_draft_1_3.json` as intentionally not persisted. SQL remains a persistence and coarse-guard layer; semantic acceptance of JSON payload internals, Bayesian replay, knot encoding well-formedness, authority paths, and invariant completeness MUST pass through the validator or logical observer kernel before runtime acceptance.
