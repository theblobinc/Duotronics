# GPU Worker App Observation - 2026-05-08

Status: source observation.
Generated: 2026-05-08

## Observed runtime surfaces

The current GPU worker application includes:

- deferred torch initialization;
- CPU and GPU capability lists;
- federation-mode and legacy API-key auth modes;
- llama-server runtime manager import path;
- narrative model registry with llama.cpp and llama-server backends;
- Qwen 35B A3B style and DeepSeek v4 Flash style large-model profiles;
- runtime config merge from environment, model defaults, and form overrides;
- `num_ctx` aliasing to `n_ctx`;
- runtime model manifest reporting;
- memlock diagnostics;
- runtime llama status, smoke, and bench endpoints.

## Draft 4 contract impact

These surfaces are now part of the runtime observability model. A deployment
that uses the GPU worker for large narrative models must report not only that a
model key exists, but which backend was selected and whether runtime flags were
actually applied or confirmed.
