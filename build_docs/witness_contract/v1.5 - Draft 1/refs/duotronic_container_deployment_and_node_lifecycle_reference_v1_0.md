# Duotronic Container Deployment and Node Lifecycle Reference v1.0

**Status:** Reference implementation guide  
**Version:** container-deployment-node-lifecycle@v1.0  
**Document kind:** Non-normative deployment reference with normative boundary reminders  
**Primary purpose:** Describe how to package and run a Duotronic node as a Docker container that federates into a DBP v2 cluster, publishes resource witnesses, receives delegated tasks, executes local Duotronic components, and reports outcomes without bypassing witness, policy, replay, or purge boundaries.

---

## 1. Scope

This guide is a reference deployment pattern. It does not prescribe a required orchestrator.

It covers:

1. node daemon responsibilities;
2. Docker image layout;
3. environment variables;
4. volume mounts;
5. model packaging;
6. DBP bootstrap configuration;
7. resource metric collection;
8. main node loop;
9. task execution loop;
10. logging and audit output;
11. graceful shutdown;
12. hardware prototype scenario.

A deployment may use Docker, Podman, systemd, Kubernetes, Nomad, bare metal, or custom supervisors. The witness and policy requirements remain the same.

---

## 2. Reference node components

A Duotronic node container should include:

1. `duotronic-node-daemon`  
   Long-running daemon. Prefer Rust or another systems language for DBP v2 transport, S2 security, and deterministic serialization.

2. DBP v2 stack  
   Full-duplex DBP lanes, S2 envelope, semantic descriptor verification, replay identity calculation.

3. Witness runtime  
   Evidence bundle creation, canonicalization, resource witness creation, task outcome witness creation.

4. Local Policy Shield  
   Enforces local restrictions before accepting commands or emitting outputs.

5. Resource collector  
   Uses `sysinfo`, `/proc`, Docker API, `nvidia-smi`, NVML, or platform-specific collectors.

6. Model/task executor  
   Optional local model inference, profile-learning workers, search workers, replay workers, purge workers.

7. Local lookup cache  
   Optional Redis, embedded KV, SQLite, RocksDB, or in-memory cache. It must not become authority without provenance.

8. Audit/log writer  
   Emits node events, transport events, task records, policy decisions, and purge/human-review references.

---

## 3. Reference Docker image

Example high-level Dockerfile shape:

```dockerfile
FROM debian:stable-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY duotronic-node-daemon /usr/local/bin/duotronic-node-daemon
COPY registry/ /opt/duotronic/registry/
COPY models/ /opt/duotronic/models/
COPY policy/ /opt/duotronic/policy/

ENTRYPOINT ["/usr/local/bin/duotronic-node-daemon"]
```

GPU images may use NVIDIA CUDA base images and mount GPU devices.

---

## 4. Environment variables

Recommended environment variables:

```yaml
DUOTRONIC_NODE_ID: node-xeon-01
DUOTRONIC_CLUSTER_ID: local-prototype-cluster
DUOTRONIC_NODE_ROLE: worker
DUOTRONIC_COORDINATOR_ADDR: dbp+wss://coordinator.local:9443
DUOTRONIC_BOOTSTRAP_MODE: psk_s2 | dbp_hs1 | mtls
DUOTRONIC_BOOTSTRAP_PSK_FILE: /run/secrets/duotronic_bootstrap_psk
DUOTRONIC_REGISTRY_DIR: /opt/duotronic/registry
DUOTRONIC_POLICY_DIR: /opt/duotronic/policy
DUOTRONIC_MODEL_DIR: /opt/duotronic/models
DUOTRONIC_DATA_DIR: /var/lib/duotronic
DUOTRONIC_LOG_DIR: /var/log/duotronic
DUOTRONIC_RESOURCE_INTERVAL_SECONDS: "5"
DUOTRONIC_RESOURCE_STALE_SECONDS: "30"
DUOTRONIC_MAX_CONTAINERS: "4"
DUOTRONIC_ALLOWED_TASK_TYPES: run_model_inference,start_profile_learning,execute_search,replay_trace
DUOTRONIC_PRIVACY_CLASS_MAX: internal | restricted | sensitive
DUOTRONIC_LEARNING_MODE: blocked | audit_only | sandbox | active
DUOTRONIC_RUNTIME_MODE: audit_only | sandbox | restricted | normal
DUOTRONIC_DBPF_PROFILE: dbp-cluster-full-duplex-v1
```

Environment variables must not override policy. If env and policy conflict, stricter policy wins.

---

## 5. Volume mounts

Recommended mounts:

```yaml
volumes:
  - /srv/duotronic/registry:/opt/duotronic/registry:ro
  - /srv/duotronic/policy:/opt/duotronic/policy:ro
  - /srv/duotronic/models:/opt/duotronic/models:ro
  - /srv/duotronic/data/node-xeon-01:/var/lib/duotronic
  - /srv/duotronic/logs/node-xeon-01:/var/log/duotronic
  - /srv/duotronic/secrets/node-xeon-01:/run/secrets:ro
```

GPU worker example:

```yaml
device_requests:
  - driver: nvidia
    count: all
    capabilities: [gpu]
```

---

## 6. Node startup lifecycle

```text
process start
-> read environment
-> load local policy
-> load registry snapshots
-> initialize DBP stack
-> collect initial resource metrics
-> wrap metrics as EvidenceBundle
-> normalize ResourceAvailabilityWitness
-> create node self-model snapshot
-> open coordinator control connection
-> DBP-HS1 or S2 bootstrap
-> send NodeHello
-> receive NodeAccept / NodeReject
-> install lane layout and semantic descriptor
-> enter main loop
```

If `NodeReject` occurs, the node must not execute cluster tasks.

---

## 7. Main loop

Reference main loop:

```text
every N seconds:
  collect metrics
  create EvidenceBundle
  create ResourceMetricSourceRecord
  canonicalize ResourceAvailabilityWitness
  update TaskQueueWitness
  emit NodeHeartbeat on DBP uplink resource lane

continuously:
  listen for command lane frames
  verify S2 envelope
  verify semantic descriptor hash
  verify lane direction and payload profile
  create ActionCandidateWitness or DelegatedTaskRecord
  apply local policy
  accept/reject task
  execute task if allowed
  emit TaskOutcomeWitness
```

Default prototype:

```yaml
resource_interval_seconds: 5
resource_stale_seconds: 30
```

---

## 8. Task execution loop

When a task command arrives:

```text
verify DBP S2
-> validate semantic descriptor
-> validate TaskDelegationActionPayload
-> check local policy
-> reserve resources
-> create DelegatedTaskRecord
-> execute task
-> collect output evidence
-> canonicalize task outcome
-> emit TaskOutcomeWitness
-> release resource lease
```

A worker must be allowed to refuse a task if its local resource witness has changed or local policy is stricter than coordinator policy.

---

## 9. Resource collection implementation notes

Recommended Linux collectors:

| Resource | Collector |
|---|---|
| CPU cores/load | `sysinfo`, `/proc/stat`, `/proc/loadavg` |
| RAM free | `sysinfo`, `/proc/meminfo` |
| GPU memory/utilization | NVML, `nvidia-smi` |
| disk I/O | `/proc/diskstats`, cgroups, iostat-like collector |
| network bandwidth | `/proc/net/dev`, cgroups |
| containers | Docker Engine API, container runtime API |
| thermal throttle | platform-specific sensor collector |

Metric collectors must record collector version and collection method.

---

## 10. Example docker run commands

Coordinator:

```bash
docker run -d \
  --name duotronic-coordinator \
  --network host \
  -e DUOTRONIC_NODE_ID=coordinator-01 \
  -e DUOTRONIC_CLUSTER_ID=local-prototype-cluster \
  -e DUOTRONIC_NODE_ROLE=coordinator \
  -e DUOTRONIC_BOOTSTRAP_MODE=psk_s2 \
  -e DUOTRONIC_BOOTSTRAP_PSK_FILE=/run/secrets/duotronic_bootstrap_psk \
  -v /srv/duotronic:/srv/duotronic \
  duotronic-node:1.5-draft
```

Worker:

```bash
docker run -d \
  --name duotronic-xeon-01 \
  --network host \
  -e DUOTRONIC_NODE_ID=node-xeon-01 \
  -e DUOTRONIC_CLUSTER_ID=local-prototype-cluster \
  -e DUOTRONIC_NODE_ROLE=worker \
  -e DUOTRONIC_COORDINATOR_ADDR=dbp+wss://coordinator.local:9443 \
  -e DUOTRONIC_BOOTSTRAP_MODE=psk_s2 \
  -e DUOTRONIC_BOOTSTRAP_PSK_FILE=/run/secrets/duotronic_bootstrap_psk \
  -e DUOTRONIC_RESOURCE_INTERVAL_SECONDS=5 \
  -e DUOTRONIC_RESOURCE_STALE_SECONDS=30 \
  -e DUOTRONIC_MAX_CONTAINERS=4 \
  -v /srv/duotronic/data/node-xeon-01:/var/lib/duotronic \
  -v /srv/duotronic/logs/node-xeon-01:/var/log/duotronic \
  -v /srv/duotronic/secrets/node-xeon-01:/run/secrets:ro \
  duotronic-node:1.5-draft
```

GPU worker:

```bash
docker run -d \
  --name duotronic-gpu-01 \
  --network host \
  --gpus all \
  -e DUOTRONIC_NODE_ID=node-gpu-5950x-01 \
  -e DUOTRONIC_NODE_ROLE=model_worker \
  -e DUOTRONIC_COORDINATOR_ADDR=dbp+wss://coordinator.local:9443 \
  -v /srv/duotronic/data/node-gpu-5950x-01:/var/lib/duotronic \
  duotronic-node-gpu:1.5-draft
```

---

## 11. Prototype hardware mapping

Prototype cluster:

```yaml
ClusterHardwareProfile:
  cluster_id: local-prototype-cluster
  network: 1Gbps LAN
  nodes:
    - node_class: xeon_worker
      count: 5
      cpu: dual Xeon X5690
      cores_per_node: 12
      threads_per_node: 24
      ram_total_cluster_bytes: 400000000000
      gpu: none
    - node_class: gpu_worker
      count: 1
      cpu: AMD Ryzen 5950X
      cores_per_node: 16
      threads_per_node: 32
      gpu:
        - NVIDIA RTX 2070
        - NVIDIA Quadro P2000
```

Reference scheduling expectations:

1. CPU-only inference tasks spread across Xeon workers.
2. GPU tasks prefer `node-gpu-5950x-01`.
3. Profile-learning tasks may use CPU nodes unless GPU models required.
4. Search tasks prefer nodes with low queue pressure and available network.
5. If GPU node resource witness is stale, GPU tasks pause or queue.
6. If a Xeon node disconnects, coordinator reassigns tasks after heartbeat timeout.

---

## 12. Logging and audit

Minimum logs:

1. DBP session events;
2. NodeHello/NodeAccept/NodeReject;
3. resource witness hashes;
4. heartbeat events;
5. task delegation payload hashes;
6. policy decisions;
7. action execution records;
8. task outcome witness hashes;
9. lane validation errors;
10. purge and human-review references;
11. node disconnect/revocation.

Logs are evidence candidates. They must be wrapped if used as witness inputs.

---

## 13. Graceful shutdown

On shutdown, node should:

1. stop accepting new tasks;
2. emit `NodeDepart`;
3. checkpoint or finish active tasks if policy permits;
4. send final resource/task queue witness;
5. close DBP session;
6. persist logs;
7. release resource leases.

If shutdown is not graceful, coordinator handles heartbeat timeout.

---

## 14. Non-normative implementation checklist

First prototype checklist:

1. build a coordinator container;
2. build a worker container;
3. implement S2 bootstrap using pre-shared key;
4. implement NodeHello/NodeAccept;
5. implement resource collection every 5 seconds;
6. implement resource witness canonicalization;
7. implement command lane task delegation;
8. implement task outcome witness;
9. implement heartbeat timeout invalidation;
10. demonstrate least-loaded scheduling across two workers;
11. demonstrate GPU-node preference for GPU tasks;
12. demonstrate reassignment on worker disconnect.
