# SRNN GPU Worker Llama-Server Runtime Profile v1.0

Status: Draft 4 runtime profile.
Generated: 2026-05-08

## Scope

This profile documents the updated SRNN GPU worker runtime surface for large
narrative models. It supplements the existing multimodal and recurrence runtime
profiles.

## Runtime model families

Draft 4 recognizes two backend classes for GPU-worker narrative models:

1. `llama_cpp_python` for in-process llama.cpp models.
2. `llama_server` for a managed local llama-server subprocess.

The current large-model profiles include Qwen 35B A3B style entries and a
DeepSeek v4 Flash style entry using 262144 context defaults and llama-server
execution.

## Runtime controls

The runtime control surface includes:

```yaml
NarrativeRuntimeConfig:
  backend: llama_cpp_python|llama_server
  model_key: string
  model_path: string
  n_ctx: integer
  no_mmap: boolean
  mlock: boolean
  n_cpu_moe: integer
  cache_type_k: string
  cache_type_v: string
  prompt_compaction_mode: string
  attention_compression_mode: string
```

The `num_ctx` alias should resolve to `n_ctx` for compatibility with shared
configuration sources. Unsupported parameters must be reported explicitly rather
than silently treated as applied.

## Llama-server readiness

A llama-server runtime is not ready just because the model key exists. Draft 4
requires evidence for:

1. binary path resolution;
2. binary executability;
3. binary version or empty-version status;
4. command construction;
5. process start;
6. health endpoint or models endpoint readiness;
7. recent log tail;
8. effective command and shell-rendered command;
9. failed-start cleanup if readiness is not achieved.

## Smoke and benchmark surfaces

Draft 4 treats smoke and bench endpoints as conformance evidence producers:

- smoke endpoint proves one selected model can load and produce one response;
- bench endpoint records time-to-first-token, decode tokens per second, total
  latency, generated token count, runtime feature request/application, and
  memlock diagnostics.

## Security and operations boundary

`mlock` and `no_mmap` are operationally significant. A runtime claiming locked
memory must report memlock limit, IPC_LOCK capability, recent log failure state,
and loaded status. Draft 4 does not allow `mlock=true` in config to be treated
as confirmation that pages were actually locked.
