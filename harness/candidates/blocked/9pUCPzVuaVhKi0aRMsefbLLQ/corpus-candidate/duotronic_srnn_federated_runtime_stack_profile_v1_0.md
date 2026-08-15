# SRNN Federated Runtime Stack Profile v1.0

Status: Draft 4 runtime profile.
Generated: 2026-05-08

## Scope

This profile aligns the Duotronic corpus with the current SRNN Server unified
federated node stack. The SRNN runtime is no longer modeled as a single backend
process. It is a profile-driven stack where each node composes services by role.

## Profile groups

### Core storage profile

The core profile represents local storage and vector infrastructure for full
nodes:

- etcd for Milvus metadata;
- PostgreSQL for Jetstream-style application data;
- MinIO for object storage;
- Milvus for vector search and recurrent memory evidence.

### Application profile

The SRNN application profile runs the FastAPI/Agno backend, legacy-compatible
route modules, SRNN APIs, and tunnel surfaces. Draft 4 treats this as the
application control plane, not as the sole source of recurrent cognition.

### WG-RNN profile

The `wg-rnn` profile is a per-node recurrent cognition loop. It should carry:

- node identity;
- node role;
- Redis coordination URL;
- Milvus endpoint;
- MinIO endpoint;
- Ollama proxy endpoint;
- teacher model list;
- memory backend mode.

A Draft 4 conforming node should be able to report whether the WG-RNN service is
configured, started, healthy, and publishing witness-bearing memory updates.

### Model service profiles

The model layer includes:

- Ollama CPU profile;
- Ollama GPU profile;
- coordinator Ollama proxy;
- resource-node Ollama proxy remote profile;
- GPU worker enrichment service;
- llama-server subprocess under GPU worker control for selected large GGUF
  models.

### Support profiles

Support profiles include Redis/Valkey, SearXNG, Hovod, LibreChat, Agent Lab,
video-dl, and Stable Diffusion services. These are not all semantically
identical. Draft 4 requires any service that writes or mutates witness-bearing
state to declare its authority boundary.

## Runtime witness requirements

Every node-level service that participates in SRNN/Duotronic state should expose
or feed these witness fields:

```yaml
RuntimeServiceWitness:
  service_name: string
  node_id: string
  node_role: string
  compose_profile: string
  image_or_binary: string
  config_digest: string
  dependency_status: map
  health_status: ok|degraded|failed|unknown
  authority_boundary: observation|suggestion|mutation|governance
  evidence_uri: string
  observed_at: timestamp
```

## Non-claims

The presence of a compose service does not prove the service is running. The
presence of a container does not prove semantic correctness. Runtime authority
requires health evidence, config digest evidence, and conformance evidence.
