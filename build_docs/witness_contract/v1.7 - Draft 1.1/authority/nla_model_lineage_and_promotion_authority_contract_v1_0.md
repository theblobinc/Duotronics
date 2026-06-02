# NLA Model Lineage and Promotion Authority Contract v1.0

Status: active Draft 5.1 authority contract.

## Purpose

Every AV/AR model or adapter used by WG-RNN must have lineage, evaluation, and
rollback metadata.

## Model lineage object

```yaml
NlaModelLineage:
  schema: nla-model-lineage/v1
  model_lineage_id: string
  role: av | ar | av_ar_pair
  parent_model_ids: list
  candidate_model_ids: list
  training_run_id: string | null
  source_observer_ids: list
  activation_space_ids: list
  checkpoint_refs: list
  checkpoint_sha256: list
  sidecar_refs: list
  sidecar_sha256: list
  eval_result_refs: list
  rollback_ref: string
  lifecycle_state: draft | trained | shadow | audit | release_candidate | active | deprecated | rolled_back
```

## Promotion authority

```yaml
NlaPromotionAuthority:
  from_state: string
  to_state: string
  required_evidence:
    - lineage_record
    - heldout_eval
    - replay_eval
    - safety_eval
    - privacy_review
    - rollback_ref
  approver: system | operator | release_committee
  approval_ref: string | null
```

## Rollback rule

No NLA model may become active without a rollback reference to the prior active
model or an explicit null-start release witness.
