# Duotronic DBP Inter-Node Full-Duplex Profile v1.0

**Status:** Source-spec baseline candidate  
**Version:** dbp-cluster-full-duplex-v1  
**Document kind:** Normative DBP v2 inter-node transport profile for Duotronic clusters  
**Primary purpose:** Define a production-oriented DBP v2 full-duplex inter-node communication profile for coordinator/worker clusters, including lane assignments, direction semantics, authority envelope rules, replay identity binding, and example frame layout.

---

## 1. Scope

This profile defines DBP transport behavior for:

1. node federation;
2. resource witness publishing;
3. task delegation commands;
4. policy and registry sync;
5. model witness upload;
6. search/source evidence upload;
7. task outcome reporting;
8. alarms and health events;
9. purge cascade commands;
10. replay-bound inter-node communication.

It assumes DBP v2 frames with:

1. fixed 4096-byte Float32 frame payload model where applicable;
2. S2 authenticated/encrypted authority envelopes;
3. MUX/ABB lane multiplexing;
4. semantic descriptors;
5. replay identity binding.

This document does not redefine DBP v2. It defines a Duotronic cluster profile over DBP v2.

---

## 2. Profile ID

```yaml
DBPInterNodeProfile:
  transport_profile_id: dbp-cluster-full-duplex-v1
  dbp_version: "2.0"
  security_required: S2
  full_duplex: true
  frame_size_bytes: 4096
  lane_model: mux_abb
  semantic_descriptor_required: true
  authority_bearing_open_frames_allowed: false
  authority_bearing_s1_frames_allowed: false
```

---

## 3. Direction model

There are two logical directions:

### 3.1 Downlink

```text
coordinator -> worker
```

Used for:

1. task commands;
2. policy updates;
3. registry sync;
4. semantic descriptor sync;
5. cancellation;
6. checkpoint request;
7. purge cascade command;
8. heartbeat config;
9. revocation.

### 3.2 Uplink

```text
worker -> coordinator
```

Used for:

1. resource witnesses;
2. task queue witnesses;
3. model witnesses;
4. candidate witnesses;
5. action outcomes;
6. search evidence bundles;
7. alarms;
8. logs and audit references;
9. federation messages;
10. purge completion records.

Direction is identity-affecting and must be included in replay digest.

---

## 4. Lane layout

Reference lane layout:

| Lane | Name | Direction | Required | Payload |
|---:|---|---|---|---|
| 1 | `semantic_descriptor` | both | yes | descriptor hash, schema refs, lane map |
| 2 | `witness_payload` | both | yes | `witness8_dense` or `wsb2_sparse` |
| 3 | `command` | downlink | yes | task delegation, policy, registry, federation commands |
| 4 | `resource` | uplink | yes | `ResourceAvailabilityWitness`, `TaskQueueWitness` |
| 5 | `task_result` | uplink | yes | `TaskOutcomeWitness`, `ActionOutcomeWitness` |
| 6 | `model_output` | uplink | optional | `ModelWitness`, model output refs |
| 7 | `search_evidence` | uplink | optional | evidence bundles and source records |
| 8 | `alarm_control` | both | optional | alarms, revocation, disconnect, purge control |
| 9 | `replay_audit` | both | optional | replay identity, trace refs, audit records |
| 10 | `bulk_ref` | both | optional | references to large external/bulk payloads |

Machine-readable layout:

```yaml
DBPLaneLayout:
  dbp_lane_layout_id: dbp-cluster-full-duplex-v1-layout-a
  lanes:
    - lane_id: 1
      name: semantic_descriptor
      allowed_directions: [downlink, uplink]
      required: true
      payload_profiles: [semantic_descriptor]
    - lane_id: 2
      name: witness_payload
      allowed_directions: [downlink, uplink]
      required: true
      payload_profiles: [witness8_dense, wsb2_sparse]
    - lane_id: 3
      name: command
      allowed_directions: [downlink]
      required: true
      payload_profiles: [command_json, command_canonical_binary]
    - lane_id: 4
      name: resource
      allowed_directions: [uplink]
      required: true
      payload_profiles: [ResourceAvailabilityWitness, TaskQueueWitness]
    - lane_id: 5
      name: task_result
      allowed_directions: [uplink]
      required: true
      payload_profiles: [TaskOutcomeWitness, ActionOutcomeWitness]
    - lane_id: 6
      name: model_output
      allowed_directions: [uplink]
      required: false
      payload_profiles: [ModelWitness]
    - lane_id: 7
      name: search_evidence
      allowed_directions: [uplink]
      required: false
      payload_profiles: [EvidenceBundle, SourceEvidenceRecord]
    - lane_id: 8
      name: alarm_control
      allowed_directions: [downlink, uplink]
      required: false
      payload_profiles: [Alarm, NodeRevocation, NodeDisconnectEvent, PurgeCommand]
    - lane_id: 9
      name: replay_audit
      allowed_directions: [downlink, uplink]
      required: false
      payload_profiles: [ReplayIdentity, AuditRecord]
    - lane_id: 10
      name: bulk_ref
      allowed_directions: [downlink, uplink]
      required: false
      payload_profiles: [BulkPayloadReference]
```

---

## 5. Semantic descriptor

Lane 1 must always carry or reference the active semantic descriptor.

```yaml
ClusterSemanticDescriptor:
  descriptor_id: string
  descriptor_version: string
  descriptor_hash: string
  schema_registry_hash: string
  family_registry_hash: string
  profile_registry_hash: string | null
  policy_snapshot_hash: string
  lane_layout_id: dbp-cluster-full-duplex-v1-layout-a
  transport_profile_id: dbp-cluster-full-duplex-v1
  allowed_payload_profiles: []
  generated_at: string
  coordinator_node_id: string
```

Payloads whose schema or profile is not covered by the semantic descriptor are audit-only or rejected.

---

## 6. Authority envelope

> **Status tag:** normative

Any semantic payload that can influence trust, scheduling, policy, witness memory, profile learning, lookup memory, recurrent state, purge, or task execution requires S2.

```yaml
AuthorityEnvelope:
  transport_profile_id: dbp-cluster-full-duplex-v1
  security_mode: S2
  authority_bearing: true
  semantic_descriptor_hash: string
  lane_layout_id: string
  direction: downlink | uplink
  session_id: string
  frame_sequence: integer
  payload_hash: string
  auth_tag: string
```

Open and S1 frames:

1. may be used only for non-authority diagnostics if policy permits;
2. must be rejected for authority-bearing semantic use;
3. must not carry task commands, resource witnesses, registry updates, profile candidates, or policy decisions.

---

## 7. Replay identity binding

> **Status tag:** normative

Replay identity must bind all identity-affecting transport fields.

```yaml
DBPClusterReplayIdentity:
  replay_identity_id: string
  transport_profile_id: dbp-cluster-full-duplex-v1
  dbp_version: "2.0"
  security_mode: S2
  semantic_descriptor_hash: string
  lane_layout_id: string
  direction: downlink | uplink
  session_id_hash: string
  coordinator_node_id: string
  worker_node_id: string
  schema_registry_hash: string
  policy_snapshot_hash: string
  payload_profile_id: string
  payload_hash: string
  frame_sequence_range: string
  digest: string
```

Reference digest:

```text
digest = sha256(canonical_serialize(
  transport_profile_id,
  dbp_version,
  security_mode,
  semantic_descriptor_hash,
  lane_layout_id,
  direction,
  session_id_hash,
  coordinator_node_id,
  worker_node_id,
  schema_registry_hash,
  policy_snapshot_hash,
  payload_profile_id,
  payload_hash,
  frame_sequence_range
))
```

---

## 8. Example downlink task command

```yaml
DBPDownlinkCommandFrame:
  direction: downlink
  lane_id: 3
  lane_name: command
  security_mode: S2
  payload_kind: TaskDelegationActionPayload
  semantic_descriptor_hash: sha256:...
  payload_hash: sha256:...
  command:
    action_kind: delegate_task
    target_node_id: node-gpu-5950x-01
    task_type: run_model_inference
    task_payload_ref: bulk_ref:model-task-0001
```

Lane 10 may carry a large payload reference rather than in-frame model inputs.

---

## 9. Example uplink resource witness

```yaml
DBPUplinkResourceFrame:
  direction: uplink
  lane_id: 4
  lane_name: resource
  security_mode: S2
  payload_kind: ResourceAvailabilityWitness
  semantic_descriptor_hash: sha256:...
  payload_hash: sha256:...
  resource_availability_witness_id: raw-gpu-5950x-20260426T120000Z
```

The resource witness has no scheduling authority until canonicalization and policy checks pass.

---

## 10. Example uplink task result

```yaml
DBPUplinkTaskResultFrame:
  direction: uplink
  lane_id: 5
  lane_name: task_result
  security_mode: S2
  payload_kind: TaskOutcomeWitness
  semantic_descriptor_hash: sha256:...
  payload_hash: sha256:...
  delegated_task_id: dt-model-infer-0001
  task_outcome_witness_id: tow-model-infer-0001
```

---

## 11. Lane failure behavior

| Failure | Required action |
|---|---|
| missing semantic descriptor | reject authority-bearing payload |
| lane not allowed for direction | reject payload |
| Open/S1 authority-bearing frame | reject and alarm |
| semantic descriptor hash mismatch | reject or registry sync |
| lane payload profile mismatch | reject or audit-only |
| S2 authentication failure | reject, close session, possible revocation |
| frame sequence gap | audit-only or replay failure depending on policy |
| resource lane stale | mark node stale |
| command lane malformed | reject command |
| task result hash mismatch | reject outcome |

---

## 12. Non-claims

This profile does not prescribe a physical network, TLS stack, SSH tunnel implementation, or DBP library.

It prescribes the semantic, lane, security, replay, and authority requirements for inter-node Duotronic communication.
