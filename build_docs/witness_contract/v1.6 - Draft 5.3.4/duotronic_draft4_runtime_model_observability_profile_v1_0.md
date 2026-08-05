# Draft 4 Runtime Model Observability Profile v1.0

Status: Draft 4 observability profile.
Generated: 2026-05-08

## Scope

This profile adds model-runtime observability to the broader Duotronic
observability layer.

## Required observations

For every model served by the SRNN GPU worker or delegated through SRNN model
routing, implementations should expose:

```yaml
RuntimeModelObservation:
  model_key: string
  backend: string
  file: string
  path: string
  exists: boolean
  size_gb: float
  default_runtime: map
  requested_runtime: map
  applied_runtime: map
  unsupported_runtime: list[string]
  health_status: string
  smoke_status: string
  benchmark_status: string
  last_error: string
  observed_at: timestamp
```

## Large-context evidence

Large context values such as 262144 tokens must be recorded as requested and
applied values. They should not be silently assumed from model naming. If a
runtime accepts `num_ctx` but applies `n_ctx`, the normalized value must appear
in the observation.

## Cache behavior evidence

Runtime cache keys must include a digest of the runtime configuration when the
same model file can be loaded with different context/memory/KV-cache settings.
Draft 4 treats cache-key collision between incompatible runtime configs as a
release blocker.

## Prompt compaction evidence

Prompt compaction modes such as `deepseek_hybrid`, `deepseek_hca_csa`, or
`hybrid` are admissible only as runtime features. They do not change the witness
identity of the input unless the compacted prompt and compaction mode are also
captured as evidence.

## Suggested metrics

- model manifest completeness;
- smoke success rate;
- bench success rate;
- median time to first token;
- decode tokens per second;
- context size requested/applied mismatch rate;
- mlock requested/confirmed mismatch rate;
- failed-start rate by model key;
- cache eviction count;
- unsupported runtime flag count.
