# Llama-Server Runtime Observation - 2026-05-08

Status: source observation.
Generated: 2026-05-08

## Observed objects

- `LlamaServerConfig`
- `LlamaServerRuntimeManager`

## Observed config fields

- model path;
- host;
- port;
- context size;
- no-mmap flag;
- mlock flag;
- CPU-MoE split count;
- K cache type;
- V cache type.

## Observed manager responsibilities

- command construction;
- binary path resolution;
- binary existence check;
- binary version detection;
- log tailing;
- readiness polling via health/models endpoints;
- process start and stop;
- failed-start cleanup;
- status reporting;
- completion calls with streaming and non-streaming timing.

## Draft 4 contract impact

The manager is the correct boundary for readiness evidence. Direct callers
should not infer readiness from the model registry or model file alone.
