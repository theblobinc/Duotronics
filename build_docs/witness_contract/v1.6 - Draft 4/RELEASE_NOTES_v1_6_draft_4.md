# Release Notes - Duotronic v1.6 Draft 4

Status: release notes.
Generated: 2026-05-08

## Summary

Draft 4 is the complete successor package to Draft 3. It keeps the full Draft 3
corpus and applies a new SRNN Server source refresh focused on federated runtime
composition, WG-RNN service deployment, GPU worker large-model execution,
llama-server readiness, runtime observability, and MCP/Agent Lab mutation
backup evidence.

## Included update classes

### 1. Full Draft 3 carry-forward

The uploaded Draft 3 package was used as the physical base for Draft 4. All
files were copied forward before adding Draft 4 material. This prevents the
missing-guts problem that occurs when a release package contains only an overlay
or materializer.

### 2. SRNN federated stack update

Draft 4 reflects the current SRNN Server compose shape:

- `core` profile for etcd, PostgreSQL, MinIO, and Milvus style stores;
- `srnn` and `srnn-gpu` application services;
- `wg-rnn` per-node recurrent cognition service;
- `gpu-worker` enrichment worker path;
- `ollama` and `ollama-gpu` model services;
- `ollama-proxy` and `ollama-proxy-remote` delegation boundaries;
- Redis/Valkey state bus;
- SearXNG, Hovod, LibreChat, Agent Lab, video-dl, and Stable Diffusion profiles.

### 3. GPU worker large-model runtime update

Draft 4 records the GPU worker's newer runtime surface:

- llama-server manager import path and fallback import behavior;
- Qwen 35B A3B and DeepSeek v4 Flash style model profiles;
- 262144 context defaults for large narrative models;
- `no_mmap`, `mlock`, `n_cpu_moe`, `cache_type_k`, and `cache_type_v` runtime
  controls;
- runtime config parsing with `num_ctx` aliasing to `n_ctx`;
- runtime model manifest reporting paths, existence, size, backend, and default
  runtime settings;
- `/runtime/llama/status`, `/runtime/models`, `/runtime/llama/smoke`, and
  `/runtime/llama/bench` style observation surfaces;
- prompt compaction support for DeepSeek-style hybrid compaction.

### 4. Llama-server runtime manager update

Draft 4 treats `LlamaServerRuntimeManager` and `LlamaServerConfig` as a runtime
readiness surface. The manager is documented as responsible for:

- command construction;
- binary discovery and version reporting;
- health/model readiness polling;
- log tail collection;
- failed-start cleanup;
- effective-command reporting;
- local completion/smoke and streaming benchmark support.

### 5. Source-level test coverage update

Draft 4 records the new SRNN tests covering:

- llama-server command construction;
- startup success and startup failure cleanup;
- binary discovery/version status;
- runtime config coercion and aliasing;
- model cache key separation by runtime hash;
- supported llama.cpp runtime kwargs;
- runtime models manifest path and file-size reporting;
- memlock diagnostics.

### 6. Mutation backup evidence update

Recent MCP/Agent Lab commits are recorded as backup-log witness changes. Draft 4
treats those records as evidence that a mutation pathway created backup records,
not as proof that the mutation was semantically safe or release-approved.

## Release boundary

Draft 4 is a corpus and conformance package. It is intended to guide and bind
implementation, but it does not replace runtime verification. Any deployment
claim still requires live evidence from the SRNN cluster, test output, and
operator-approved release records.
