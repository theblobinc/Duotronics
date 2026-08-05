# Truth Observer Activation Authority Profile v1.0

Status: active Draft 5.1 authority contract.

## Purpose

This profile defines how any AI model, runtime, tool, or service becomes a truth
observer for WG-RNN and what kind of evidence it may contribute.

## Authority object

```yaml
TruthObserverActivationAuthority:
  schema: truth-observer-activation-authority/v1
  observer_id: string
  observer_kind: llm | embedding_model | reranker | tool_model | api_model | human | other
  model_id: string
  backend: transformers | sglang | vllm | llama_cpp | ollama | api_only | other
  evidence_authority:
    output_text: boolean
    logits: boolean
    embeddings: boolean
    hidden_states: boolean
    tool_traces: boolean
    calibration_scores: boolean
  activation_authority:
    residual_stream: boolean
    mlp_activation: boolean
    attention_output: boolean
    pooled_embedding: boolean
  nla_authority:
    can_capture_for_nla: boolean
    can_train_nla: boolean
    can_run_nla_inference: boolean
    compatible_adapter_refs: list
  fallback:
    mode: logits_or_output_witness_only | output_text_only | unavailable
  approval:
    registered_by: string
    registered_at: timestamp
    review_required: boolean
```

## Authority rules

1. A backend with no hidden-state access cannot claim residual-stream NLA.
2. API-only models may still act as truth observers through output/logit/tool
   evidence if those are available.
3. NLA training authority requires a declared activation space.
4. Every observer must have a stable `observer_id`.
5. Every observer profile must include a fallback mode.
6. Observer authority is revocable.

## Evidence classes

```text
E0 output evidence only
E1 logits or probabilities
E2 embeddings
E3 hidden states or residual stream
E4 tool traces plus hidden states
E5 release-verified activation observer
```

NLA self-training requires E3 or higher unless it is explicitly training an
output-only explanation model rather than an activation-language autoencoder.
