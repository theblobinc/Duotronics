# NLA Shadow, Audit, and Release Gate Contract v1.0

Status: active Draft 5.1 authority contract.

## Gate states

```text
trained -> shadow -> accepted_for_audit -> release_candidate -> promoted
```

## Shadow gate

A candidate may enter shadow mode if:

1. Schema validates.
2. Lineage validates.
3. Sidecar validates.
4. Heldout evaluation exists.
5. It cannot affect outputs.
6. It cannot write memory.
7. It has a rollback ref.

## Audit gate

A shadow candidate may become audit-capable if:

1. Replay pass rate meets threshold.
2. Reconstruction fidelity does not regress.
3. Confabulation rate does not increase.
4. Failure examples are handled better or not worse.
5. Human-review triggers still fire.
6. Security review passes.

## Release gate

An audit candidate may become active only if:

1. Operator approval exists.
2. Release bundle exists.
3. Rollback is tested.
4. Telemetry and monitoring are enabled.
5. Drift detection is enabled.
6. Model lineage record is immutable.

## Default thresholds

```yaml
shadow_gate:
  heldout_replay_pass_min: 0.80
audit_gate:
  heldout_replay_pass_min: 0.90
  confabulation_regression_max: 0.00
  privacy_violation_count_max: 0
release_gate:
  heldout_replay_pass_min: 0.95
  operator_approval_required: true
  rollback_required: true
```
