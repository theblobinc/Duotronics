# Bayesian Calibration Scoring Registry - v1.7 Draft 1.2

## Scoring definitions

- `bayes:calibration:brier:v1` - mean squared error between predicted probabilities and observed binary outcomes. Lower is better; not proof.
- `bayes:calibration:log_score:v1` - negative log predictive probability assigned to observed outcomes. Requires handling of zero-probability events by explicit rejection or epsilon policy.
- `bayes:calibration:reliability_bins:v1` - bin-level report with count, mean predicted probability, and empirical frequency.
- `bayes:calibration:expected_calibration_error:v1` - weighted average of bin calibration gaps.

## Required distinction

Calibration reports measure probabilistic forecast behavior. They do not promote a posterior into theorem, proof, fact, policy approval, or human attestation.
