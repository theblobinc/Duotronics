# NLA Training Memory Cell Authority Contract v1.0

Status: active Draft 5.1 authority contract.

## Purpose

WG-RNN may store internal NLA training data, but only in explicit memory cells
with separate authority from user memory and system policy memory.

## Memory cells

```yaml
NlaTrainingMemoryAuthority:
  nla_raw_capture_cell:
    authority: store_activation_refs_only
    may_store_raw_vectors: conditional
    may_store_user_text: redacted_only
    may_train_from: false_until_curated
  nla_candidate_explanation_cell:
    authority: store_candidate_text
    may_train_from: false_until_scored
  nla_reconstruction_cell:
    authority: store_ar_metrics
    may_train_from: true_for_scored_pairs
  nla_curriculum_cell:
    authority: trainable_dataset
    may_train_from: true
    requires_privacy_review: true
  nla_failure_cell:
    authority: negative_training_dataset
    may_train_from: true
    requires_label_review: true
  nla_model_lineage_cell:
    authority: release_artifact
    may_train_from: false
```

## Separation rule

NLA training memory is not user memory. It must not be surfaced as a remembered
fact about a user. It may only be used to train/evaluate NLA adapters under the
self-training authority contract.

## Required memory metadata

```yaml
NlaTrainingExample:
  example_id: string
  observer_id: string
  activation_space_id: string
  source_event_id: string
  activation_ref: string
  activation_shake256_512: shake256_512
  explanation_text_shake256_512: shake256_512
  explanation_text_ref: string
  reconstruction_metrics_ref: string
  privacy_class: public | internal | private | restricted
  curriculum_status: raw | scored | curated | heldout | rejected | expired
  retention_class: ephemeral | bounded | audit | release
```

## Retention rules

Raw vectors default to bounded retention. Curated examples may be retained longer
only when privacy class, source, digest, and review metadata are present.
