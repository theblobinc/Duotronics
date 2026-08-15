# Llama-Server Runtime Readiness Contract v1.0

Status: Draft 4 runtime contract.
Generated: 2026-05-08

## Purpose

This contract defines when a llama-server-backed model runtime may be treated as
ready by SRNN and Duotronics.

## Runtime object

```yaml
LlamaServerRuntimeWitness:
  backend: llama_server
  model_path: string
  host: string
  port: integer
  ctx_size: integer
  no_mmap: boolean
  mlock: boolean
  n_cpu_moe: integer
  cache_type_k: string
  cache_type_v: string
  binary_path: string
  binary_exists: boolean
  binary_version: string
  effective_command: list[string]
  effective_command_shell: string
  pid: integer
  loaded: boolean
  readiness_probe: health|models|failed|unknown
  recent_logs: list[string]
  last_start_error: string
  uptime_s: float
```

## Readiness levels

### Level 0 - declared

A model appears in a registry. No file or process evidence exists.

### Level 1 - file-observed

The model path exists and has a size. No backend process is known ready.

### Level 2 - command-constructible

The runtime manager can produce an effective command with expected flags.

### Level 3 - process-started

A process was started and has a PID. Health is not yet proven.

### Level 4 - endpoint-ready

The runtime responds through `/health` or `/v1/models`.

### Level 5 - smoke-verified

A smoke completion request succeeds and returns timing/runtime evidence.

### Level 6 - benchmarked

A benchmark run records multiple latency/decode observations and runtime feature
evidence.

Only Levels 5 and 6 support release-readiness claims.

## Failure handling

When readiness fails, the runtime must preserve:

- failed command;
- shell-rendered command;
- recent logs;
- failure code;
- cleanup result;
- timestamp;
- model key and runtime config digest.

A failed start must be a witness-bearing event, not an invisible exception.
