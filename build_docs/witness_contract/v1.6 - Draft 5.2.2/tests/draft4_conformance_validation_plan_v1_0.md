# Draft 4 Conformance Validation Plan v1.0

Status: Draft 4 conformance plan.
Generated: 2026-05-08

## Test groups

### Package integrity

- Verify every Draft 3 file is present in Draft 4.
- Verify all Draft 4 new files are present.
- Verify the manifest file count equals the filesystem count.
- Verify checksums are present for every file.

### SRNN GPU worker runtime tests

- Run `tests/test_gpu_worker_runtime_config.py`.
- Run `tests/test_llama_server_runtime.py`.
- Confirm command construction includes model path, ctx size, no-mmap, mlock,
  n-cpu-moe, cache-type-k, and cache-type-v when configured.
- Confirm failed-start behavior stops the subprocess and preserves error state.
- Confirm runtime config aliasing maps `num_ctx` to `n_ctx`.
- Confirm model cache keys separate different runtime configs.
- Confirm model manifests report file path, existence, size, backend, and
  default runtime.

### Runtime smoke tests

- Call `/runtime/models` on each GPU worker.
- Call `/runtime/llama/status` before load.
- Call `/runtime/llama/smoke` for each llama-server model key.
- Call `/runtime/llama/bench` with bounded runs.
- Store outputs as replayable evidence.

### Federated stack tests

- Validate compose config for each node profile.
- Confirm Ollama proxy reports model inventory.
- Confirm SRNN app reports health.
- Confirm WG-RNN service starts with node identity.
- Confirm Redis, Milvus, and MinIO configuration is reachable from WG-RNN.

### Mutation backup tests

- Confirm backup records are append-only.
- Confirm backup IDs are unique.
- Confirm command-triggered backups link to changed file lists or metadata.
- Confirm release-sensitive paths require policy and approval evidence.
