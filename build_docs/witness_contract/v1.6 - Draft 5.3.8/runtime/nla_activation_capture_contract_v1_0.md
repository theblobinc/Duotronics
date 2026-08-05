# NLA Activation Capture Contract v1.0

Status: active Draft 5 contract.  
Applies to: activation capture for Natural Language Autoencoder witnesses.

## Purpose

This contract defines what it means to capture an activation vector for NLA use.
It prevents activation capture from becoming unbounded hidden memory or an
untraceable interpretability claim.

## Capture object

```yaml
ActivationCaptureWitness:
  capture_id: string
  loop_id: string
  request_id: string
  source_model_id: string
  backend: transformers | sglang | llama_server | ollama | other
  backend_capability: hidden_states_available | hidden_states_unavailable | unknown
  layer_index: integer
  token_index: integer
  token_text_hash: sha256 | null
  d_model: integer
  dtype: float16 | bfloat16 | float32 | quantized | unknown
  vector_ref: string
  vector_sha256: sha256
  vector_norm_l2: number
  capture_time_utc: timestamp
  retention_class: ephemeral | fixture | audit_artifact | release_artifact
  transcript_ref: string | null
  redaction_status: none | redacted | restricted
```

## Required provenance

A capture is valid only if it records:

1. Source model identity.
2. Runtime backend.
3. Layer index.
4. Token position or pooling rule.
5. d_model.
6. Vector digest.
7. Norm and dtype.
8. Capture timestamp.
9. Retention class.
10. Replay or fixture reference when used in release evidence.

## Backend capabilities

Backends that do not expose hidden states may not claim native activation
capture. They may only create placeholder diagnostics with
`backend_capability: hidden_states_unavailable`.

## Retention rules

Activation vectors are sensitive internal artifacts. Draft 5 allows four
retention classes:

| Class | Rule |
|---|---|
| ephemeral | Deleted after scoring; digest retained |
| fixture | Stored in test fixture bundle |
| audit_artifact | Stored for bounded audit review |
| release_artifact | Stored with manifest, checksum, and approval record |

## Privacy and redaction

If a token or transcript segment may contain private user data, the raw token
text must not be copied into the NLA witness. Store a hash or redacted reference
instead.

## Norm and compatibility

The capture contract must preserve the vector norm before any NLA injection
scaling. AV injection scaling is a separate runtime operation and must not erase
capture evidence.

## Replay evidence

Release claims require a replay bundle containing:

1. Source prompt or approved redacted prompt fixture.
2. Model identifier and revision.
3. Layer and token selection.
4. Original vector digest.
5. AV output.
6. AR output or score.
7. Fidelity metrics.
8. Runtime configuration digest.

## Forbidden capture claims

1. Claiming residual-stream evidence from a backend that does not expose hidden
   states.
2. Storing raw activations indefinitely without retention class.
3. Mixing vectors from incompatible model dimensions.
4. Changing layer index without recording it.
5. Treating pooled embeddings as token residual activations without a pooling
   rule.
