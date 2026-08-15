# Draft 4 Source Evidence Summary

Generated: 2026-05-08

Draft 4 was built from the full uploaded Draft 3 ZIP, not from a thin overlay.
The uploaded Draft 3 package contained 205 files, including 199 Markdown files,
and about 806 KB of uncompressed content. Draft 4 keeps that entire corpus and
adds the Draft 4 update layer.

Source-visible SRNN updates incorporated in Draft 4:

1. The existing Draft 3 source refresh already represented the April 30 SRNN
   implementation pass: SDK and formal model work, OpenAPI export, cognition
   step migration, proof interchange fixtures, mutation policy, live recurrent
   witness overlay, stale evidence behavior, Python SDK runner correction, and
   WGRNN Firehose working-tree observations.
2. The May 2026 SRNN repository then added a more concrete runtime model layer
   around the GPU worker and llama-server execution path.
3. The current SRNN docker-compose stack now represents the unified federated
   node stack with profiles for core stores, Ollama/Ollama GPU, Redis, SRNN,
   SRNN GPU, GPU worker, Ollama proxy and remote proxy, Hovod, SearXNG,
   LibreChat, Agent Lab, video-dl, and Stable Diffusion profiles.
4. The compose stack now includes a per-node `wg-rnn` service that runs
   `python -m srnn.cognition` with Redis, Milvus, MinIO, and Ollama proxy
   configuration, treating WG-RNN as a live recurrent node service rather than
   only a prose target.
5. The GPU worker now includes a llama-server runtime manager path for large
   GGUF narrative models, including Qwen 35B A3B and DeepSeek v4 Flash style
   profiles, 262144 context defaults, no-mmap/mlock defaults, CPU-MoE split,
   KV-cache type controls, runtime model manifests, smoke/bench endpoints,
   memlock diagnostics, and effective-command reporting.
6. The SRNN test layer now covers the llama-server command builder, startup
   status, failed startup cleanup, binary discovery, runtime config coercion,
   cache-key isolation by runtime hash, supported runtime kwargs, model manifest
   path reporting, and memlock diagnostics.
7. Agent Lab/MCP auto-mutation commits added backup-log witness records for
   execute_system_command and service-restart preflight activity. Draft 4 treats
   those as governance evidence records, not as semantic proof that the mutation
   payload was safe.

Draft 4 release boundary:

- Draft 4 is a documentation, contract, and conformance update package.
- The SRNN runtime changes are represented from repository-visible source
  observations and commit metadata.
- This package does not claim that every runtime endpoint was executed in this
  environment, that every container was started, or that every test suite passed
  on production hardware.
- New runtime surfaces are promoted only to documented target/observed status
  unless the underlying source itself records executable tests or verified
  runtime status.

## Contract deltas

### Runtime capability is now more granular

Draft 3 separated verified runtime tools from target tools. Draft 4 extends that
pattern to runtime model execution. The system must distinguish:

- a model listed in a registry;
- a model file present on disk;
- a model backend selected by policy;
- a llama-server process command constructed correctly;
- a process started successfully;
- an endpoint ready to answer health/model queries;
- a smoke request completed;
- a benchmark result recorded with timing evidence.

Only the final stages can support operational readiness claims.

### WG-RNN is now a service boundary

Draft 4 treats per-node WG-RNN as a deployment and conformance boundary. A
running node should not merely contain SRNN code; it should expose an observable
recurrent cognition service with Redis/Milvus/MinIO/Ollama configuration and
node identity.

### Backup logs are witness records, not approval records

The recent Agent Lab backup-log commits are evidence that an automated mutation
path created backups. They must be preserved as audit material, but they do not
replace policy approval, semantic review, tests, or rollback validation.

## Required Draft 4 follow-up checks

1. Run the GPU worker runtime tests in SRNN Server.
2. Run the llama-server smoke endpoint against each configured large model.
3. Validate memlock settings on the actual GPU worker host.
4. Confirm the compose profiles used by main, gpu-1, and cpu-2 match the node
   role plan.
5. Confirm the `wg-rnn` service can publish recurrent witness updates through
   the configured Redis/Milvus/MinIO backends.
6. Preserve Agent Lab backup logs as append-only evidence.
