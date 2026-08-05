# Duotronic Deployment Guide v1.0

**Status:** reference implementation guide with normative safety boundaries  
**Version:** deployment-guide@v1.0

## 1. Reference topology

```text
Ingress/API node
  Python/FastAPI transition API
  policy preflight
  DBP envelope validation

Canonical storage
  PostgreSQL: durable transactional truth
  object/artifact store: content-addressed blobs

Indexes and coordination
  Milvus: vector/semantic retrieval
  Redis: ephemeral coordination, pub/sub, enrollment, queue hints

Runtime workers
  interpreter sandbox workers
  proof checker workers
  Lisp/SBCL symbolic bridge
  Julia math-kernel bridge
  SRNN oracle/task workers
  multimodal ingest workers

Review surfaces
  admin CLI/dashboard
  human review queue
  audit/replay tools
```

## 2. Minimum services

1. `duotronic-api`
2. `duotronic-postgres`
3. `duotronic-redis`
4. `duotronic-milvus`
5. `duotronic-policy-engine`
6. `duotronic-worker-interpreter`
7. `duotronic-worker-srnn`
8. `duotronic-admin`

## 3. Optional services

1. `duotronic-lisp-bridge`
2. `duotronic-julia-bridge`
3. `duotronic-proof-lean`
4. `duotronic-proof-coq`
5. `duotronic-multimodal-ingest`
6. `duotronic-mcp-endpoint-proxy`

## 4. Environment variables

```text
DUOTRONIC_API_BIND=127.0.0.1:8080
DUOTRONIC_POSTGRES_DSN=postgresql://...
DUOTRONIC_REDIS_URL=redis://...
DUOTRONIC_MILVUS_URI=http://...
DUOTRONIC_POLICY_SNAPSHOT=policy-main
DUOTRONIC_ARTIFACT_ROOT=/var/lib/duotronic/artifacts
DUOTRONIC_SANDBOX_ROOT=/var/lib/duotronic/sandbox
DUOTRONIC_MCP_ENDPOINT_URL=http://127.0.0.1:8765/mcp
DUOTRONIC_MCP_API_KEY=...
```

## 5. Network exposure

Only the API or a reverse proxy should be externally exposed. PostgreSQL, Redis, Milvus, Lisp/Julia bridges, and interpreter workers must be private.

## 6. Scaling rules

1. API nodes are horizontally scalable if all canonical writes go to PostgreSQL.
2. Interpreter workers scale by sandbox queue depth and CPU/memory budgets.
3. Proof workers scale separately because dependency images are heavier.
4. Milvus scales by embedding load and query throughput, not canonical object count.
5. Redis should be treated as replaceable and recoverable.

## 7. Multimodal deployment note

For SRNN multimodal ingestion, a GPU VM may run decode/inference workers and post normalized detection payloads to the ingest service. The ingest service must validate schema, compute temporal deltas, and forward only policy-allowed witness payloads.

## 8. First deployment sequence

```text
create PostgreSQL schemas
-> install policy snapshot
-> start API in read-only health mode
-> start Redis and queue workers
-> start artifact store
-> start interpreter worker in sandbox-only mode
-> run conformance fixture pack
-> enable canonical writes
-> enable SRNN oracle ingestion
-> enable admin review queue
-> optionally enable MCP query endpoint
```

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
