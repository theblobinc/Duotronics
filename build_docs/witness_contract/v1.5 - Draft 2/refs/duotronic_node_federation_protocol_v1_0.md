# Duotronic Node Federation Protocol v1.0

**Status:** Source-spec baseline candidate  
**Version:** node-federation-protocol@v1.0  
**Document kind:** Normative auto-join, node admission, heartbeat, registry sync, and graceful departure protocol  
**Primary purpose:** Define how Dockerized or otherwise containerized Duotronic nodes join a distributed cluster, authenticate over DBP v2 full-duplex streams, publish resource self-models, receive lane layouts, and become eligible for witness-gated task delegation.

---

## 1. Scope

This protocol governs:

1. node auto-join;
2. coordinator discovery;
3. DBP v2 control stream establishment;
4. DBP-HS1 or pre-shared S2 bootstrap;
5. `NodeHello`;
6. `NodeAccept`;
7. `NodeReject`;
8. registry hash negotiation;
9. semantic descriptor sync;
10. lane layout assignment;
11. resource heartbeat;
12. task command readiness;
13. disconnect and stale-node invalidation;
14. graceful departure;
15. node revocation.

The protocol assumes the DBP inter-node lane profile defined in `duotronic_dbp_inter_node_full_duplex_profile_v1_0.md`.

---

## 2. Central rule

> **Status tag:** normative

A node is not trusted because it connected.

A newly connected node becomes schedulable only after:

```text
transport authentication
-> NodeHello validation
-> identity and capability policy check
-> semantic descriptor compatibility
-> registry hash compatibility
-> initial resource witness validation
-> NodeAccept
-> fresh heartbeat
-> policy-approved runtime mode
```

Until then, the node is `candidate` or `audit_only`.

---

## 3. Node identity

```yaml
NodeIdentity:
  node_identity_id: string
  node_id: string
  cluster_id: string
  identity_kind: self_signed | psk_bootstrap | mtls | coordinator_signed | hardware_bound | custom
  public_key_ref: string | null
  public_key_hash: string | null
  bootstrap_secret_ref: string | null
  image_digest: string | null
  daemon_version: string
  dbp_stack_version: string
  container_runtime: docker | podman | bare_metal | custom
  trust_status: candidate | admitted | restricted | revoked | rejected
```

Self-signed identity is sufficient for candidate admission only. Higher authority requires policy approval, registry trust, or signed admission.

---

## 4. Coordinator discovery

A node may discover a coordinator through:

1. environment variable;
2. local config file;
3. service discovery;
4. DNS;
5. static IP;
6. mTLS WebSocket endpoint;
7. SSH tunnel;
8. preconfigured DBP endpoint.

Reference environment variable:

```text
DUOTRONIC_COORDINATOR_ADDR=dbp+wss://coordinator.local:9443
```

Discovery does not imply trust.

---

## 5. Federation handshake flow

```text
container start
-> daemon boot
-> collect initial metrics
-> create initial EvidenceBundle + ResourceAvailabilityWitness
-> open DBP control stream
-> authenticate with DBP-HS1 or PSK S2
-> send NodeHello
-> coordinator validates
-> coordinator policy check
-> coordinator replies NodeAccept or NodeReject
-> node installs semantic descriptor and lane layout
-> node starts heartbeat and command listener
```

---

## 6. NodeHello

`NodeHello` is carried in the DBP command lane or dedicated federation lane.

```yaml
NodeHello:
  node_hello_id: string
  protocol_version: node-federation-protocol@v1.0
  cluster_id: string
  node_identity:
    node_id: string
    identity_kind: self_signed | psk_bootstrap | mtls | coordinator_signed | hardware_bound | custom
    public_key_hash: string | null
    image_digest: string | null
    daemon_version: string
    dbp_stack_version: string
  transport:
    dbp_profile_id: dbp-cluster-full-duplex-v1
    supported_security_modes:
      - S2
    dbp_hs1_supported: true | false
    compression_supported: []
  capabilities:
    cpu_total_cores: number
    ram_total_bytes: integer
    gpu_devices: []
    disk_classes: []
    network_interfaces: []
    supported_task_types:
      - run_model_inference
      - start_profile_learning
      - execute_search
      - replay_trace
      - purge_cascade
    container_runtime: docker | podman | bare_metal | custom
    max_containers: integer
  registries:
    schema_registry_hash: string
    family_registry_hash: string
    policy_snapshot_hash: string | null
    semantic_descriptor_hash: string | null
  initial_self_model_snapshot_ref: string
  initial_resource_availability_witness_ref: string
  node_witness_event_ref: string
  timestamp: string
  signature_ref: string | null
```

The initial self-model and resource witness must be dereferenceable in the DBP payload, command lane, or associated semantic descriptor payload.

---

## 7. NodeAccept

```yaml
NodeAccept:
  node_accept_id: string
  node_hello_id: string
  coordinator_node_id: string
  accepted_node_id: string
  admission_status: admitted | restricted | sandbox | audit_only
  assigned_actor_scope_id: string
  assigned_node_role: worker | model_worker | search_worker | profile_worker | replay_worker | purge_worker | hybrid
  semantic_descriptor:
    descriptor_id: string
    descriptor_hash: string
    version: string
  registry_sync:
    schema_registry_hash: string
    family_registry_hash: string
    policy_snapshot_hash: string
    profile_registry_hash: string | null
  lane_layout:
    dbp_lane_layout_id: string
    downlink_lanes: []
    uplink_lanes: []
  heartbeat:
    heartbeat_interval_seconds: integer
    heartbeat_timeout_seconds: integer
  allowed_task_types: []
  allowed_privacy_classes: []
  learning_mode: blocked | audit_only | sandbox | active
  runtime_mode: audit_only | sandbox | restricted | normal
  policy_decision_id: string
  issued_at: string
  signature_ref: string | null
```

A node is not schedulable until `NodeAccept` is policy-approved and heartbeat begins.

---

## 8. NodeReject

```yaml
NodeReject:
  node_reject_id: string
  node_hello_id: string
  coordinator_node_id: string
  rejected_node_id: string | null
  rejection_reason: auth_failed | unsupported_security | registry_mismatch | policy_block | capability_mismatch | image_untrusted | privacy_block | malformed | custom
  retry_allowed: true | false
  retry_after_seconds: integer | null
  policy_decision_id: string
  issued_at: string
```

Rejected nodes must not receive authority-bearing semantic payloads.

---

## 9. Node heartbeat

A heartbeat is a resource and liveness update.

```yaml
NodeHeartbeat:
  node_heartbeat_id: string
  node_id: string
  cluster_id: string
  sequence: integer
  timestamp: string
  resource_availability_witness_id: string
  task_queue_witness_id: string | null
  current_runtime_mode: audit_only | sandbox | restricted | normal | degraded | blocked
  alarms: []
  dbp_session_id: string
  signature_ref: string | null
```

Default prototype heartbeat interval:

```yaml
heartbeat_interval_seconds: 5
heartbeat_timeout_seconds: 30
```

If heartbeat timeout occurs, emit invalidation.

---

## 10. Node disconnect and staleness

```yaml
NodeDisconnectEvent:
  node_disconnect_event_id: string
  node_id: string
  cluster_id: string
  detected_at: string
  disconnect_kind: graceful | heartbeat_timeout | transport_error | policy_revoked | unknown
  affected_delegated_task_ids: []
  required_action: mark_stale | pause_tasks | reassign_tasks | revoke_node | human_review
  self_model_invalidation_event_id: string
```

A disconnected node's resource witness authority is zero for new scheduling.

---

## 11. Graceful departure

```yaml
NodeDepart:
  node_depart_id: string
  node_id: string
  cluster_id: string
  reason: maintenance | shutdown | policy | overload | manual | custom
  active_task_policy: finish | cancel | reassign | checkpoint
  issued_at: string
  signature_ref: string | null
```

Coordinator response:

```yaml
NodeDepartAck:
  node_depart_ack_id: string
  node_depart_id: string
  coordinator_node_id: string
  accepted: true | false
  task_actions: []
  policy_decision_id: string
  issued_at: string
```

---

## 12. Node revocation

```yaml
NodeRevocation:
  node_revocation_id: string
  node_id: string
  cluster_id: string
  reason: compromised | stale | policy_change | repeated_failure | purge_request | manual | custom
  revoked_at: string
  revoked_by: policy | coordinator | human | custom
  affected_sessions: []
  affected_tasks: []
  required_action: block_new_tasks | cancel_tasks | quarantine_outputs | purge_outputs | human_review
  policy_decision_id: string
```

Revoked nodes must not receive new tasks or authority-bearing registry updates.

---

## 13. Registry sync

Node admission binds registry hashes.

If hashes mismatch, coordinator may:

1. reject node;
2. send registry sync;
3. admit in `audit_only`;
4. admit in `sandbox`;
5. require human/operator review.

```yaml
RegistrySyncMessage:
  registry_sync_message_id: string
  coordinator_node_id: string
  target_node_id: string
  schema_registry_hash: string
  family_registry_hash: string
  policy_snapshot_hash: string
  semantic_descriptor_hash: string
  payload_ref: string
  policy_decision_id: string
```

Registry sync must be replay-bound.

---

## 14. Security requirements

> **Status tag:** normative

Authority-bearing federation requires S2.

Allowed bootstrap modes:

1. DBP-HS1 handshake that establishes S2 session keys;
2. pre-shared S2 key for local prototype;
3. mTLS transport plus DBP S2 payload authentication;
4. SSH tunnel plus DBP S2 payload authentication.

Rejected for authority-bearing semantic use:

1. Open frames;
2. S1-only frames;
3. unsigned or unauthenticated `NodeHello`;
4. registry updates over unauthenticated lanes;
5. task commands over unauthenticated lanes.

---

## 15. Auto-federation with Docker

A Dockerized node may join automatically if:

1. image digest matches policy or admission rules;
2. bootstrap S2/DBP-HS1 credentials are present;
3. coordinator is reachable;
4. node daemon can produce `NodeHello`;
5. initial resource witness is valid;
6. node capabilities match allowed roles;
7. policy admits the node.

Auto-federation does not bypass node admission policy.

---

## 16. Conformance requirements

A conforming node federation implementation must pass fixtures for:

1. valid NodeHello -> NodeAccept;
2. malformed NodeHello -> NodeReject;
3. unsupported security -> NodeReject;
4. stale heartbeat -> SelfModelInvalidationEvent;
5. graceful NodeDepart -> task reassign/finish;
6. registry mismatch -> sync, sandbox, or reject;
7. revoked node -> no new tasks;
8. resource witness freshness -> schedulability;
9. DBP lane layout binding -> replay identity;
10. Open/S1 frame rejection for authority-bearing federation.
