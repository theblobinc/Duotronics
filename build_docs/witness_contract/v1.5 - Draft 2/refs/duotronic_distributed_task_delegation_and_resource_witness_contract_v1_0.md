# Duotronic Distributed Task Delegation and Resource Witness Contract v1.0

**Status:** Source-spec baseline candidate  
**Version:** distributed-task-delegation-resource-witness@v1.0  
**Document kind:** Normative distributed resource witness, task delegation, task queue, and cluster scheduling contract  
**Primary purpose:** Define how Duotronic nodes publish canonical computational resource availability, how planners delegate work across a cluster, how task queues become witness-bearing objects, how overload conflicts are resolved, and how delegated task outcomes feed back into evidence, lookup memory, self-models, policy, and recurrent state.

---

## 1. Scope

This contract extends the v1.4 Draft 5 self-informing architecture into a distributed, federated, recurrent cluster.

It covers:

1. resource metric evidence streams;
2. `ResourceAvailabilityWitness`;
3. node-level `ActorScope`;
4. node-level `SelfModelSnapshot`;
5. `NodeTaskQueue`;
6. `TaskQueueWitness`;
7. `TaskDelegationActionPayload`;
8. `DelegatedTaskRecord`;
9. `TaskOutcomeWitness`;
10. resource-aware `DecisionContext`;
11. scheduler/planner action candidates with `action_kind: delegate_task`;
12. task conflict resolution;
13. cluster lookup memory integration;
14. stale resource invalidation;
15. DW-SSM task outcome update authority;
16. prototype hardware fixture guidance.

This contract does not define the DBP wire protocol. DBP lane layout and security are owned by `duotronic_dbp_inter_node_full_duplex_profile_v1_0.md`.

---

## 2. Central rule

> **Status tag:** normative

A raw system metric is not authority.

CPU utilization, memory availability, GPU memory, disk throughput, network bandwidth, container count, or process state must enter as evidence, be canonicalized into a resource witness, be checked for freshness, and pass policy before it can affect task scheduling.

```text
system metrics
-> EvidenceBundle
-> Personal/System Metric SourceRecord
-> ChronologicalEvidenceStream
-> ResourceAvailabilityWitness
-> SelfModelSnapshot(node actor scope)
-> LookupMemoryRecord
-> DecisionContext
-> ActionCandidateWitness(delegate_task)
-> PolicyDecision
-> ActionExecutionRecord
-> TaskOutcomeWitness
```

If metric collection, canonicalization, freshness check, or policy validation fails, resource authority is zero for scheduling.

---

## 3. Node actor scope

A node is an actor for self-evidence purposes.

```yaml
ActorScope:
  actor_scope_id: string
  actor_ref: string
  actor_kind: system
  actor_ref_policy: direct | hashed | pseudonymous
  allowed_stream_ids: []
  excluded_stream_ids: []
  scope_purpose: cluster_resource_scheduling | task_execution | model_governance | custom
  privacy_class: internal | restricted | mixed
```

A machine, Docker container, worker process, coordinator, or DBP endpoint may have separate actor scopes if policy requires.

Recommended actor refs:

```text
node:<cluster_id>:<stable_node_id>
container:<cluster_id>:<node_id>:<container_id>
coordinator:<cluster_id>:<coordinator_id>
```

---

## 4. Resource metric evidence stream

A node reports resource metrics as a chronological self-evidence stream.

```yaml
ResourceMetricSourceRecord:
  resource_metric_record_id: string
  evidence_bundle_id: string
  node_id: string
  actor_scope_id: string
  capture_time: string
  metric_window_seconds: number
  metrics:
    cpu_total_cores: number
    cpu_available_cores: number
    cpu_utilization: number
    ram_total_bytes: integer
    ram_free_bytes: integer
    gpu_devices:
      - gpu_id: string
        gpu_name: string | null
        gpu_total_bytes: integer | null
        gpu_free_bytes: integer | null
        gpu_utilization: number | null
    disk_io_bandwidth_bytes_per_sec: number | null
    network_bandwidth_bytes_per_sec: number | null
    containers_running: integer
    max_containers: integer
    load_average_1m: number | null
    thermal_throttle: true | false | null
  collector:
    collector_id: string
    collector_version: string
    collection_method: sysinfo | nvidia_smi | procfs | docker_api | custom
  trust_status: raw | candidate | canonicalized | audit_only | rejected
```

The source record must be wrapped by `EvidenceBundle` before any semantic use.

---

## 5. Resource availability witness

> **Status tag:** normative

`ResourceAvailabilityWitness` is the canonical scheduling witness for node capacity.

```yaml
ResourceAvailabilityWitness:
  resource_availability_witness_id: string
  node_id: string
  actor_scope_id: string
  timestamp: string
  source_evidence_ids: []
  source_metric_record_ids: []
  normalizer_id: string
  schema_id: string

  cpu_available_cores: number
  ram_free_bytes: integer
  gpu_free_bytes: integer
  gpu_utilization: number | null
  disk_io_bandwidth: number | null
  network_bandwidth: number | null
  containers_running: integer
  max_containers: integer

  normalized_components:
    cpu_available_p: number
    ram_available_p: number
    gpu_available_p: number
    disk_io_p: number
    network_p: number
    container_headroom_p: number
    uncertainty_q: number

  effective_capacity_score: number
  stability_score: number
  confidence: number

  freshness:
    observed_at: string
    expires_at: string
    max_staleness_seconds: integer
    stale: true | false

  policy:
    policy_decision_id: string
    runtime_mode: audit_only | sandbox | restricted | normal
    allowed_task_classes: []

  canonical_identity_hash: string
  replay_identity_ref: string
  trust_status: candidate | canonicalized | audit_only | rejected | deprecated
```

### 5.1 Required field semantics

| Field | Meaning |
|---|---|
| `cpu_available_cores` | normalized or measured available CPU cores after local reservation policy |
| `ram_free_bytes` | free or allocatable RAM after reservation policy |
| `gpu_free_bytes` | total free GPU memory across allowed devices; zero if no GPU |
| `gpu_utilization` | aggregate or policy-selected GPU utilization; null if no GPU |
| `disk_io_bandwidth` | estimated available disk I/O bandwidth in bytes/sec |
| `network_bandwidth` | estimated available network bandwidth in bytes/sec |
| `containers_running` | running workload containers or worker slots |
| `max_containers` | policy-approved maximum concurrent containers/workers |
| `effective_capacity_score` | bounded 0-1 aggregate scheduler score |
| `confidence` | bounded 0-1 confidence after stability and policy clamps |

---

## 6. Resource capacity mathematics

> **Status tag:** normative

Resource availability uses the Duotronic primitive:

```text
D = (p, q)
```

where:

1. `p` is normalized available resource in `[0, 1]`;
2. `q` is uncertainty, variance, or instability in `[0, 1]` unless profile-specific;
3. `lambda` is a policy-configurable uncertainty penalty, default `1.0`.

### 6.1 Capacity score

```text
capacity = p - lambda * q
```

The scheduler must clamp aggregate capacity into `[0, 1]` before using it for authority-bearing decisions:

```text
effective_capacity_score = clamp01(weighted_capacity)
```

### 6.2 Stability term

```text
S(p,q) = clamp01(1 - |q| / (|p| + |q| + epsilon))
```

Recommended default:

```yaml
epsilon: 0.000001
lambda: 1.0
```

`S(p,q)` becomes the stability component of capacity confidence.

### 6.3 Suggested aggregate

A reference implementation may compute:

```text
p = weighted_mean(
  cpu_available_p,
  ram_available_p,
  gpu_available_p,
  disk_io_p,
  network_p,
  container_headroom_p
)

q = max(
  metric_variance_q,
  collector_age_q,
  missing_metric_q,
  policy_uncertainty_q
)

effective_capacity_score = clamp01(p - lambda * q)
confidence = min(S(p,q), normalizer_confidence, policy_limit)
```

This is a reference aggregate. A deployment may define a task-specific aggregate if it declares the profile and fixtures.

---

## 7. Staleness and invalidation

> **Status tag:** normative

Resource witnesses expire quickly.

Default prototype staleness rule:

```yaml
max_staleness_seconds: 30
```

If no fresh resource update arrives within the threshold, the node self-model becomes stale.

```yaml
SelfModelInvalidationEvent:
  self_model_invalidation_event_id: string
  self_model_snapshot_id: string
  actor_scope_id: string
  actor_ref: string
  trigger_kind: resource_heartbeat_timeout | resource_metric_stale | node_disconnected | policy_changed | manual | custom
  trigger_refs: []
  affected_lookup_record_ids: []
  affected_decision_context_ids: []
  required_action: mark_stale | rebuild_snapshot | demote_to_audit | remove_from_lookup | pause_tasks | reassign_tasks | human_review
  prior_snapshot_version: integer
  next_snapshot_policy: increment_version | rebuild_from_scratch | block_until_review
  event_time: string
```

A stale resource witness must not be used for new delegation unless policy explicitly permits stale audit replay.

---

## 8. Node self-model snapshot

A node-level `SelfModelSnapshot` includes resource witness state.

```yaml
NodeSelfModelSnapshot:
  self_model_snapshot_id: string
  actor_scope_id: string
  node_id: string
  snapshot_time: string
  version: integer
  prior_snapshot_id: string | null
  resource_availability_witness_id: string
  task_queue_witness_id: string | null
  canonical_fact_refs: []
  audit_only_fact_refs: []
  policy_decision_id: string
  runtime_mode: audit_only | sandbox | restricted | normal
  staleness_policy:
    max_age_seconds: 30
    invalidate_on_missing_heartbeat: true
    invalidate_on_policy_change: true
    invalidate_on_node_disconnect: true
```

The existing `SelfModelSnapshot` contract remains valid. `NodeSelfModelSnapshot` is a node-specialized profile.

---

## 9. Task queue witness

`TaskQueueWitness` models pending work per node.

```yaml
TaskQueueWitness:
  task_queue_witness_id: string
  node_id: string
  actor_scope_id: string
  timestamp: string
  source_evidence_ids: []
  queue_profile_id: string

  pending_tasks: integer
  running_tasks: integer
  blocked_tasks: integer
  completed_tasks_window: integer
  failed_tasks_window: integer
  estimated_cpu_reserved_cores: number
  estimated_ram_reserved_bytes: integer
  estimated_gpu_reserved_bytes: integer
  estimated_network_reserved_bytes_per_sec: number | null
  queue_latency_estimate_seconds: number | null

  task_class_counts:
    run_model_inference: integer
    start_profile_learning: integer
    execute_search: integer
    replay_trace: integer
    purge_cascade: integer
    custom: integer

  effective_queue_pressure: number
  confidence: number
  freshness:
    observed_at: string
    expires_at: string
    max_staleness_seconds: integer
    stale: true | false

  canonical_identity_hash: string
  replay_identity_ref: string
  trust_status: candidate | canonicalized | audit_only | rejected
```

### 9.1 Queue pressure reference formula

```text
queue_pressure = clamp01(
  running_tasks / max_containers
  + alpha * pending_tasks / max(1, max_containers)
  + beta * blocked_tasks / max(1, pending_tasks + running_tasks + blocked_tasks)
)
```

Recommended defaults:

```yaml
alpha: 0.25
beta: 0.50
```

---

## 10. Task delegation action payload

A planner delegates work by emitting an `ActionCandidateWitness` with:

```yaml
action_kind: delegate_task
```

The action payload is:

```yaml
TaskDelegationActionPayload:
  task_delegation_action_payload_id: string
  coordinator_node_id: string
  target_node_id: string
  target_actor_scope_id: string
  task_type: run_model_inference | start_profile_learning | execute_search | replay_trace | purge_cascade | resource_probe | custom
  task_payload_ref: string
  task_payload_lane_ref: string | null

  required_resources:
    cpu_cores: number
    ram_bytes: integer
    gpu_bytes: integer
    disk_io_bandwidth: number | null
    network_bandwidth: number | null
    containers: integer

  expected_duration_seconds: number | null
  priority: low | normal | high | urgent | policy_critical
  deadline: string | null
  privacy_class: public | internal | restricted | sensitive | mixed

  scheduling_basis:
    resource_availability_witness_id: string
    task_queue_witness_id: string | null
    node_self_model_snapshot_id: string
    lookup_record_refs: []

  policy:
    required_policy_gate: string
    learning_mode_required: blocked | audit_only | sandbox | active | not_applicable
    runtime_mode_requested: audit_only | sandbox | restricted | normal

  replay:
    replay_identity_ref: string
    transport_profile_id: string
    dbp_lane_layout_id: string
```

The planner may propose. Policy decides.

---

## 11. Delegated task record

After policy approval, the coordinator creates a delegated task record.

```yaml
DelegatedTaskRecord:
  delegated_task_id: string
  action_candidate_id: string
  task_delegation_action_payload_id: string
  policy_decision_id: string
  coordinator_node_id: string
  target_node_id: string
  assigned_at: string
  status: assigned | accepted | running | completed | failed | cancelled | reassigned | stale_blocked
  transport:
    dbp_session_id: string
    command_lane_id: integer
    task_payload_lane_ref: string | null
  resource_reservation:
    cpu_cores: number
    ram_bytes: integer
    gpu_bytes: integer
    containers: integer
  lease:
    lease_id: string
    lease_expires_at: string | null
    heartbeat_required_seconds: integer
```

Leases prevent silent overcommitment.

---

## 12. Task outcome witness

`TaskOutcomeWitness` extends the action outcome pattern for cluster work.

```yaml
TaskOutcomeWitness:
  task_outcome_witness_id: string
  delegated_task_id: string
  action_execution_id: string
  target_node_id: string
  task_type: run_model_inference | start_profile_learning | execute_search | replay_trace | purge_cascade | resource_probe | custom
  started_at: string
  completed_at: string | null
  execution_status: success | failed | partial | blocked | cancelled | timed_out | reassigned

  output_refs:
    evidence_bundle_ids: []
    model_witness_ids: []
    candidate_witness_ids: []
    candidate_profile_ids: []
    search_result_set_ids: []
    replay_result_ids: []
    purge_event_ids: []
    log_refs: []

  resource_usage:
    cpu_core_seconds: number | null
    peak_ram_bytes: integer | null
    peak_gpu_bytes: integer | null
    network_bytes: integer | null
    disk_read_bytes: integer | null
    disk_write_bytes: integer | null

  error:
    error_class: string | null
    error_message_hash: string | null
    retryable: true | false | null

  policy_followup: none | audit | retry | reassign | demote_node | human_review | purge_review
  canonical_identity_hash: string
  replay_identity_ref: string
  trust_status: candidate | canonicalized | audit_only | rejected
```

---

## 13. Resource-aware decision context

A cluster coordinator or distributed planner uses a decision context that includes node self-models.

```yaml
ClusterDecisionContext:
  decision_context_id: string
  cluster_id: string
  coordinator_node_id: string
  objective_ref: string
  decision_scope: cluster_task_delegation | node_admission | load_balancing | failover | profile_learning | custom

  available_node_self_model_snapshot_refs: []
  resource_availability_witness_refs: []
  task_queue_witness_refs: []
  stale_node_refs: []
  blocked_node_refs: []

  task_request_refs: []
  policy_snapshot_id: string
  learning_mode: blocked | audit_only | sandbox | active | not_applicable
  runtime_mode: audit_only | sandbox | restricted | normal
  privacy_class: public | internal | restricted | sensitive | mixed
```

---

## 14. Delegation policy checks

> **Status tag:** normative

A policy shield must check:

1. target node admitted and not revoked;
2. DBP session authenticated with S2 or better;
3. resource witness fresh;
4. self-model snapshot fresh;
5. task queue witness fresh or policy permits missing queue data;
6. capacity score meets required resource threshold;
7. queue pressure does not exceed policy limit;
8. privacy class can be processed by target node;
9. learning mode permits requested task;
10. runtime mode permits action;
11. no purge/legal hold conflict;
12. lane layout supports task payload and outcome;
13. replay identity binds transport profile and lane layout;
14. resource lease can be reserved without overcommit.

If any authority-bearing check fails, delegation authority is zero.

---

## 15. Task conflict handling

Task conflicts occur when planners overcommit nodes or propose incompatible assignments.

```yaml
TaskDelegationConflict:
  task_delegation_conflict_id: string
  decision_context_id: string
  action_candidate_ids: []
  target_node_ids: []
  conflict_type: overcommit_cpu | overcommit_ram | overcommit_gpu | queue_overload | privacy_conflict | policy_conflict | stale_resource | duplicate_task | custom
  detected_by: coordinator | policy | planner | node | human | custom
  default_resolution: most_restrictive_policy_wins | least_loaded_node_gets_task | highest_priority_task_wins | no_action | human_review
  resolved_action_candidate_ids: []
  rejected_action_candidate_ids: []
  policy_decision_id: string
  status: unresolved | resolved | escalated | rejected
```

Default resolution:

1. safety/privacy conflict: `most_restrictive_policy_wins`;
2. overcommit conflict: `least_loaded_node_gets_task` if all nodes are policy-equivalent;
3. priority conflict: highest priority may win only if policy permits;
4. uncertainty: `no_action` or `human_review`.

---

## 16. Hardware scenario reference profile

> **Status tag:** reference

Prototype cluster:

| Node class | Count | CPU | Threads | RAM | GPU |
|---|---:|---|---:|---:|---|
| Xeon workers | 5 | dual Xeon X5690 | 24 each / 120 total | 400 GB total | none |
| GPU worker | 1 | Ryzen 5950X | 32 | local RAM | RTX 2070 + Quadro P2000 |

Assumed network:

```yaml
network_bandwidth: 1Gbps LAN
```

Expected scheduling behavior:

1. CPU-bound inference and profile-learning fixtures prefer Xeon workers when GPU is not required.
2. GPU-accelerated tasks prefer the Ryzen/GPU node only when GPU availability witness is fresh.
3. Search tasks may run on any admitted node with network capacity and privacy permission.
4. If the GPU node becomes stale or overloaded, GPU tasks pause, reassign, or queue.
5. If a Xeon worker misses heartbeat for more than 30 seconds, its resource self-model invalidates and pending tasks are reassigned.
6. Cluster-wide learning mode must be active or sandbox before `start_profile_learning` tasks are delegated.

---

## 17. DW-SSM task outcome authority update

> **Status tag:** normative

When a delegated task produces outcome evidence, a DW-SSM may incorporate it using policy-clamped sparse event authority.

Base update equation:

```text
s_t = rho_t ⊙ s_{t-1}
    + beta_t ⊙ B_t u_t
    + lambda_t ⊙ m_t
    + eta_t ⊙ e^J_t
```

For task outcome evidence:

```text
eta_t = clamp_L5(c_t^norm * 1[J_t > 1] * h(J_t))
```

where:

1. `c_t^norm` is normalizer confidence;
2. `J_t` is an optional GCD-jump recurrence signal;
3. `h(J_t)` is a bounded profile-specific jump response;
4. `clamp_L5` applies policy constraints;
5. if transport or canonicalization fails, `eta_t = 0`.

Authority remains:

```text
authority = min(profile_requested_authority, normalizer_confidence, policy_limit)
```

and is forced to zero if transport, canonicalization, lane validation, or policy fails.

---

## 18. Replay identity binding

> **Status tag:** normative

A delegated task replay identity must hash all identity-affecting fields:

1. schema IDs;
2. normalizer IDs;
3. family/profile registry hashes;
4. transport profile ID;
5. export/import policy where applicable;
6. DBP semantic descriptor hash;
7. lane layout ID;
8. direction;
9. coordinator node ID;
10. target node ID;
11. task delegation payload hash;
12. resource witness hash;
13. task queue witness hash;
14. policy snapshot ID;
15. security mode;
16. session or handshake profile ID.

Reference digest:

```text
task_replay_identity =
  sha256(canonical_serialize(identity_affecting_fields))
```

---

## 19. Non-claims

This contract does not prescribe one scheduler algorithm, queue technology, orchestration platform, or model server.

It specifies the witness, policy, replay, and trust boundaries required for resource-aware delegation.
