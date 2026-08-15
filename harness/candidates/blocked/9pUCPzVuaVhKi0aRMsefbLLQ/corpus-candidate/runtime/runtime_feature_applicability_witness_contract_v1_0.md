# Runtime Feature Applicability Witness Contract

Status: active Draft 4.1 runtime contract.  
Generated: 2026-05-09.  
Extends: `duotronic_draft4_runtime_model_observability_profile_v1_0.md` and
`duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`.

## Purpose

Model runtime configuration can request features that a backend does not support.
Draft 4.1 separates requested, translated, applied, and unsupported runtime
features so evidence records do not confuse intent with actual behavior.

## Canonical object

```yaml
RuntimeFeatureApplicabilityWitness:
  schema: runtime-feature-applicability@v1
  observed_at: timestamp
  backend: llama_cpp_python | llama_server | ollama | ollama_proxy | cluster | unknown
  backend_version: string | null
  model_id: string
  model_file_path: string | null
  model_file_shake256_512: shake256_512 | null
  runtime_config_digest: shake256_512
  requested: map
  translated: map
  applied: map
  unsupported: list
  ignored: list
  warnings: list
  effective_command_hash: shake256_512 | null
  effective_kwargs_hash: shake256_512 | null
  status_endpoint_ref: string | null
```

## Required feature categories

Runtime evidence SHOULD classify these features when present:

```yaml
RuntimeFeatureCategories:
  context:
    - n_ctx
    - num_ctx
    - ctx_size
  memory:
    - no_mmap
    - mlock
    - memlock_limit
  moe:
    - n_cpu_moe
  kv_cache:
    - cache_type_k
    - cache_type_v
  serving:
    - host
    - port
    - binary_path
    - model_path
  prompt_management:
    - prompt_compaction
    - attention_compression
```

## Claim rules

1. `requested` means the user, profile, or manifest asked for the feature.
2. `translated` means the system mapped aliases or profile names into backend
   configuration.
3. `applied` means the backend command, kwargs, status, or runtime response shows
   the feature was actually used.
4. `unsupported` means the backend cannot apply the feature.
5. `ignored` means the feature was accepted by configuration parsing but had no
   observable runtime effect.
6. Release notes MUST NOT say a feature is active unless it appears in `applied`.
