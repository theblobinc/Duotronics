# Runtime Readiness Evidence Persistence Profile

Status: active Draft 4.1 runtime evidence profile.  
Generated: 2026-05-09.  
Extends: `runtime/llama_server_runtime_readiness_contract_v1_0.md`.

## Purpose

Runtime readiness claims need durable evidence. Draft 4.1 requires status,
command, logs, smoke, benchmark, and model-file observations to persist as
referenceable witness records instead of transient console output.

## Canonical object

```yaml
RuntimeReadinessEvidenceRef:
  schema: runtime-readiness-evidence-ref@v1
  readiness_witness_id: string
  observed_at: timestamp
  node_id: string
  service_id: string
  backend: llama_server | llama_cpp_python | ollama | ollama_proxy | unknown
  runtime_config_digest: shake256_512
  model_id: string
  model_file_path: string | null
  model_file_hash: shake256_512 | null
  model_file_size_bytes: integer | null
  effective_command_hash: shake256_512 | null
  process_status: running | stopped | failed | unknown
  readiness_status: ready | warming | degraded | failed | unknown
  status_payload_hash: shake256_512 | null
  log_tail_hash: shake256_512 | null
  failed_start_log_ref: string | null
  smoke_result_id: string | null
  bench_result_id: string | null
  persisted_to: db | jsonl | artifact | mcp_result | release_bundle | mixed
  retention_policy: string | null
```

## Persistence requirements

1. A readiness claim MUST include a readiness witness ID.
2. A model availability claim MUST include model path, size, and preferably hash.
3. A command construction claim MUST include effective command hash or kwargs
   hash.
4. A startup failure claim MUST preserve failed-start logs.
5. A smoke/benchmark claim MUST link to result records.
6. A release bundle MUST include enough evidence to reconstruct the readiness
   state without live access to the machine.

## Evidence downgrade rules

```yaml
RuntimeEvidenceDowngradeRules:
  no_model_hash: model_identity_partial
  no_effective_command_hash: runtime_flags_unverified
  no_status_payload_hash: readiness_transient
  no_log_tail_hash: failure_debug_incomplete
  no_smoke_result: functional_readiness_unproven
  no_bench_result: performance_claim_disallowed
```
