# Duotronic Witness Contract v1.6 Draft 5.1

Status: active consolidated witness contract.  
Generated: 2026-05-09.  
Supersedes: Draft 5 for NLA authority and self-training interpretation.

## 1. Scope

Draft 5.1 defines the authority model that allows WG-RNN to build internal NLA
capability from its own evidence stream while preventing unsafe self-trust.

It extends the Draft 5 NLA layer with:

```text
L2n   Natural-Language Activation Witness
L2nt  NLA Training Memory Cell
L2no  Generic Truth-Observer Activation Interface
L2nl  NLA Model Lineage and Promotion Authority
```

## 2. Core principle

Self-training is allowed only as a witnessed, bounded, reviewable process.

```text
collect -> curate -> train -> evaluate -> shadow -> audit -> release
```

No self-trained NLA output may write memory, change policy authority, replace a
model, trigger mutation, or shape a user-facing answer until the relevant Draft
5.1 authority gate explicitly permits it.

## 3. Generic truth observer

A truth observer is any AI model, service, tool, or runtime that contributes
evidence to the WG-RNN witness lattice. It may expose hidden states, logits,
embeddings, output text, tool traces, probabilities, confidence metadata, or only
API-level results.

```yaml
TruthObserverActivationProfile:
  schema: truth-observer-activation-profile/v1
  observer_id: string
  model_id: string
  backend: transformers | sglang | vllm | llama_cpp | ollama | api_only | other
  hidden_states_available: boolean
  logits_available: boolean
  embeddings_available: boolean
  layer_count: integer | null
  d_model: integer | null
  tokenizer_ref: string | null
  activation_capture_modes:
    - residual_stream
    - mlp_activation
    - attention_output
    - embedding
    - logits
    - output_text
    - tool_trace
    - unavailable
  nla_training_allowed: boolean
  nla_inference_allowed: boolean
  fallback_mode: logits_or_output_witness_only | unavailable
```

If hidden states are unavailable, the observer may still contribute evidence,
but it may not claim residual-stream NLA.

## 4. NLA training memory cells

WG-RNN may store internal NLA training data in explicit memory cells:

```yaml
NlaTrainingMemoryCells:
  nla_raw_capture_cell:
    stores: activation refs, model/layer/token metadata, hashes
    retention: short_bounded_redacted
  nla_candidate_explanation_cell:
    stores: AV outputs, teacher explanations, operator notes
    retention: medium
  nla_reconstruction_cell:
    stores: AR reconstruction metrics, cosine, MSE, stability
    retention: medium
  nla_curriculum_cell:
    stores: high-quality accepted training pairs
    retention: long
  nla_failure_cell:
    stores: low-fidelity, confabulated, unsupported, quarantined examples
    retention: long_negative_training
  nla_model_lineage_cell:
    stores: AV/AR adapter versions, LoRA checkpoints, eval scores, rollback refs
    retention: release_artifact
```

These memory cells are not user memory. They are model-development evidence
stores governed by retention, privacy, and review policy.

## 5. Self-training witness

Every internal NLA training run must emit a `NlaSelfTrainingWitness`.

```yaml
NlaSelfTrainingWitness:
  schema: nla-self-training-witness/v1
  training_run_id: string
  parent_av_model_id: string
  parent_ar_model_id: string
  candidate_av_model_id: string
  candidate_ar_model_id: string
  training_data:
    curriculum_examples: integer
    failure_examples: integer
    heldout_examples: integer
    observer_model_families: list
    activation_layers: list
  training_method:
    method: lora | adapter | projection_head | full_finetune | distillation
    max_steps: integer
    compute_budget: string
    offline_only: boolean
  evaluation:
    reconstruction_cosine_before: number
    reconstruction_cosine_after: number
    mse_before: number
    mse_after: number
    confabulation_rate_before: number
    confabulation_rate_after: number
    replay_pass_rate: number
    regression_count: integer
  safety:
    may_write_memory: false
    may_change_policy_authority: false
    may_replace_active_model: false
    human_review_required: true
  decision:
    status: rejected | accepted_for_shadow | accepted_for_audit | promoted
    rollback_ref: string
```

## 6. Training authority states

```text
collected          examples gathered but not trainable
curated            examples pass privacy/fidelity checks
trainable          curriculum approved for a bounded training run
trained            candidate produced but not usable
shadow             candidate evaluated without affecting outputs
accepted_for_audit candidate may generate audit-only witnesses
release_candidate  candidate may be considered for active release
promoted           candidate becomes active only with release witness
rejected           candidate cannot be used
rolled_back        active candidate was reverted
```

## 7. Promotion gates

A candidate NLA adapter cannot move to the next authority state unless the gate
below is satisfied.

| From | To | Required gate |
|---|---|---|
| trained | shadow | schema, lineage, heldout eval, no policy regression |
| shadow | accepted_for_audit | replay pass, fidelity improvement, failure-rate non-regression |
| accepted_for_audit | release_candidate | human review, security review, privacy review |
| release_candidate | promoted | operator approval, rollback ref, release bundle |

## 8. Generic does not mean universal

Generic means the same WG-RNN interface and witness schema can support many
observers. It does not mean one AV/AR model works for every source model.

Each observer/model/layer/dimension space needs an explicit compatibility
profile and may need its own adapter.

## 9. Forbidden authority shortcuts

Draft 5.1 forbids:

1. Live weight updates that immediately affect authority.
2. Self-trained NLA memory writes into user memory.
3. NLA explanations treated as ground-truth hidden intent.
4. Promotion without replay results.
5. Promotion without rollback reference.
6. Promotion from a training run that used unredacted private data without
   retention and privacy review.
7. Residual-stream NLA claims from a backend that exposes only text/logits.
8. Replacing external or prior AV/AR models solely because the internal model is
   self-trained.

## 10. Release evidence minimum

```yaml
Draft51ReleaseEvidenceMinimum:
  truth_observer_registry_snapshot: required
  nla_training_memory_profile: required
  curriculum_manifest: required
  failure_memory_manifest: required
  self_training_witness: required_for_self_trained_adapters
  heldout_eval_results: required
  replay_eval_results: required
  model_lineage_record: required
  rollback_ref: required
  security_review: required
  human_review: required_for_promotion
  operator_release_approval: required_for_active_release
```

## 11. Default policy

```yaml
nla_self_training_policy:
  collect_examples: allowed
  curate_examples: allowed
  train_candidate_adapters: allowed_offline
  run_shadow_eval: allowed
  run_audit_only_inference: allowed_after_gate
  write_user_memory: denied
  change_policy_authority: denied
  replace_active_model: denied_without_release_gate
  trigger_mutation: denied
```
