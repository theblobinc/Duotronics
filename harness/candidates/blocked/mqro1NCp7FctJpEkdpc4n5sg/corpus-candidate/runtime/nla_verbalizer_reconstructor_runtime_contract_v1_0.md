# NLA Verbalizer and Reconstructor Runtime Contract v1.0

Status: active Draft 5 runtime contract.  
Applies to: Activation Verbalizer (AV), Activation Reconstructor (AR), NLA sidecar
metadata, and inference runtime.

## Purpose

This contract defines the runtime obligations for the two-model NLA pair.

## Roles

```yaml
ActivationVerbalizer:
  direction: vector_to_text
  output: natural_language_explanation

ActivationReconstructor:
  direction: text_to_vector
  output: reconstructed_activation_vector
```

## Required sidecar fields

An AV or AR model must load an NLA sidecar and assert at startup:

```yaml
nla_sidecar:
  kind: nla_model
  role: av | ar
  model_family: string
  d_model: integer
  extraction_layer_index: integer
  injection_scale: number | null
  mse_scale: number | null
  injection_token_id: integer | null
  injection_char: string | null
  prompt_template_hash: shake256_512
  tokenizer_revision: string | null
  base_model_revision: string | null
```

Sidecar fields are load-bearing. Runtime code may not hardcode injection tokens,
prompt templates, scale factors, or layer indexes when a sidecar is available.

## AV obligations

The AV runtime must:

1. Verify model/layer/d_model compatibility.
2. Verify sidecar/tokenizer agreement.
3. Apply required injection scaling.
4. Inject the vector at the verified prompt position.
5. Use the exact sidecar prompt template.
6. Return raw output and parsed explanation.
7. Mark parser status.
8. Detect common injection failure signatures.
9. Record runtime backend and configuration digest.

## AR obligations

The AR runtime must:

1. Verify explanation template integrity.
2. Reconstruct a vector with the expected d_model.
3. Normalize prediction and gold vectors according to scoring contract.
4. Return MSE and cosine similarity.
5. Record reconstruction model identity and digest.
6. Fail closed when dimensions mismatch.

## Output envelope

```json
{
  "av_raw_text": "...",
  "explanation_text": "...",
  "explanation_tags_valid": true,
  "ar_available": true,
  "reconstruction_vector_ref": "vec://...",
  "mse": 0.18,
  "cosine_similarity": 0.91,
  "runtime_config_digest": "shake256-512:...",
  "sidecar_digest": "shake256-512:..."
}
```

## Unsupported runtime handling

If the configured backend cannot support input embeddings, hidden-state capture,
or required injection semantics, the runtime must return:

```yaml
status: unsupported_backend
accepted_witness: false
may_promote: false
```

## Runtime health checks

A release-capable NLA runtime must expose:

1. AV model loaded status.
2. AR model loaded status.
3. Sidecar digest.
4. Backend type.
5. Hidden-state support.
6. Input-embedding support.
7. Last successful smoke decode.
8. Last successful AR score.
9. Failure counters.
10. Quarantine counters.

## Failure classes

```yaml
failure_classes:
  - sidecar_missing
  - sidecar_tokenizer_mismatch
  - incompatible_d_model
  - incompatible_layer
  - injection_position_not_found
  - av_generation_failed
  - explanation_parse_failed
  - ar_unavailable
  - reconstruction_dimension_mismatch
  - fidelity_below_threshold
  - unsupported_backend
```
