# NLA Self-Training Authority Contract v1.0

Status: active Draft 5.1 authority contract.

## Purpose

This contract defines how WG-RNN may train internal NLA models from its own
witness stream.

## Allowed training methods

```yaml
allowed_methods:
  - lora
  - adapter
  - projection_head
  - distillation
conditional_methods:
  - full_finetune
forbidden_by_default:
  - live_online_weight_update
  - unbounded_self_modification
  - training_on_unreviewed_private_text
```

## Training run object

```yaml
NlaSelfTrainingRun:
  training_run_id: string
  triggered_by: operator | scheduled_job | evaluation_gap | manual_test
  parent_models:
    av_model_id: string
    ar_model_id: string
  candidate_models:
    av_model_id: string
    ar_model_id: string
  dataset:
    curriculum_manifest_ref: string
    failure_manifest_ref: string
    heldout_manifest_ref: string
  constraints:
    offline_only: true
    max_steps: integer
    max_gpu_hours: number
    max_training_examples: integer
  outputs:
    checkpoint_refs: list
    metrics_ref: string
    self_training_witness_ref: string
```

## Authority rule

A training run produces a candidate model, not an active model. Candidate models
must pass lineage, replay, safety, and promotion gates before use.

## Failure conditions

A training run is rejected if it:

1. Uses examples without curriculum status.
2. Uses private/restricted examples without review.
3. Reduces heldout fidelity beyond threshold.
4. Increases confabulation rate.
5. Fails replay tests.
6. Lacks rollback metadata.
7. Attempts to alter production authority directly.
