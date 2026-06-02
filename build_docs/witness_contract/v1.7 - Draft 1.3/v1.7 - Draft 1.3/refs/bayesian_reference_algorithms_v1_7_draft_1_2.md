# Bayesian Reference Algorithms - v1.7 Draft 1.2

## Status

Normative algorithm registry for Draft 1.2 Bayesian replay semantics. These algorithm identifiers are referenced by Bayesian update, replay, posterior predictive, marginalization, conditioning, negative-evidence, and decision-theory witnesses.

## Algorithms

### `bayes:exact_discrete_bayes:v1`

Inputs: finite hypothesis set, normalized prior probability mass, non-negative likelihood values, observation evidence ref.  
Replay rule: compute `normalization_constant = sum_h prior(h) * likelihood(h)`; reject if non-positive; compute `posterior(h) = prior(h) * likelihood(h) / normalization_constant`.

### `bayes:log_space_discrete_bayes:v1`

Inputs: finite hypothesis set, normalized prior probability mass, log-likelihood values.  
Replay rule: compute `log_weight(h) = log(prior(h)) + log_likelihood(h)`; compute `log_normalization_constant = logsumexp_h(log_weight(h))`; compute `posterior(h) = exp(log_weight(h) - log_normalization_constant)`. Log-likelihood values may be negative and must never be schema-checked as ordinary probabilities.

### `bayes:posterior_predictive_discrete:v1`

Computes a posterior predictive distribution by summing over posterior hypotheses and declared observation model values. Predictive probability is not truth and does not authorize policy action by itself.

### `bayes:marginalize_sum_out:v1`

Sums a joint distribution over declared marginalized variables and verifies that the result is normalized within tolerance.

### `bayes:condition_normalize:v1`

Restricts a distribution to states satisfying declared evidence and renormalizes by the condition probability. Reject if the condition probability is zero or unknown.

### `bayes:bounded_monte_carlo:v1`

Allows approximate updates only when an approximation method, sample/replay manifest, random-seed witness where applicable, and explicit error bound are present. Approximate posterior values are candidates, not proofs.

## Non-collapse rules

- Posterior probability is not fact.
- Calibration is not proof.
- Expected utility is not policy approval.
- Missing data is not zero probability unless an explicit model says so.
- Negative evidence must be modeled as evidence, not erased.
