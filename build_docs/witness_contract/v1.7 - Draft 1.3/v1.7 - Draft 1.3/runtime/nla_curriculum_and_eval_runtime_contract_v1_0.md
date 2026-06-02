# NLA Curriculum and Evaluation Runtime Contract v1.0

Status: active Draft 5.1 runtime contract.

## Purpose

This contract defines how NLA examples become training/evaluation data and how
candidate adapters are scored.

## Curriculum states

```text
raw -> scored -> curated -> trainable -> used_in_training
raw -> rejected
curated -> heldout
curated -> expired
```

## Evaluation suite

```yaml
NlaEvalSuite:
  reconstruction:
    cosine_mean: number
    mse_mean: number
  replay:
    replay_pass_rate: number
    stability_mean: number
  failure_handling:
    low_fidelity_quarantine_rate: number
    unsupported_backend_fail_closed_rate: number
  safety:
    confabulation_rate: number
    privacy_violation_count: integer
    memory_write_violation_count: integer
    policy_escalation_violation_count: integer
```

## Promotion score

A candidate improves only if it improves reconstruction or stability without
increasing confabulation, privacy, memory-write, or policy-escalation failures.
