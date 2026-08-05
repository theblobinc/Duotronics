# NLA Release Evidence Bundle Specification v1.0

Status: active Draft 5.1 evidence bundle spec.

A Draft 5.1 NLA release bundle must include:

```yaml
required_evidence:
  truth_observer_profiles: required
  activation_capture_fixtures: required_for_activation_nla_claims
  training_examples_manifest: required_for_self_training_claims
  heldout_eval_manifest: required_for_self_training_claims
  replay_results: required
  regression_report: required
  candidate_model_lineage: required
  rollback_reference: required
  safety_review: required
  operator_approval: required_for_release_promotion
```

If any item is missing, the candidate model may remain in shadow or audit mode but
may not be release-promoted.
