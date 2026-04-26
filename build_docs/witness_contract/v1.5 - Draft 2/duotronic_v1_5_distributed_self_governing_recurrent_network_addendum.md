# Duotronic v1.5 Draft Addendum: Distributed Self-Governing Recurrent Network

**Status:** Internal source corpus draft  
**Version:** v1.5-draft-addendum  
**Document kind:** Integrated v1.5 corpus addendum  
**Primary purpose:** Summarize and connect the v1.5 distributed cluster extension across resource witnesses, task delegation, DBP full-duplex inter-node transport, node federation, Docker-native deployment, policy gating, and conformance fixtures.

---

## 1. v1.5 thesis

v1.5 extends Duotronics into a distributed, federated, self-referential recurrent network.

A Duotronic cluster is a set of admitted nodes that:

1. publish resource availability as canonical witnesses;
2. communicate over DBP v2 S2 full-duplex streams;
3. self-federate through authenticated `NodeHello` / `NodeAccept`;
4. delegate tasks through policy-gated action candidates;
5. report outcomes as task witnesses;
6. use lookup memory and recurrent state to adapt scheduling;
7. invalidate stale node self-models;
8. reject raw metrics, unauthenticated transport, stale resource reports, and unapproved node capabilities.

The cluster does not become trustworthy because machines are connected. Trust still flows through:

```text
evidence -> witness -> canonicalization -> policy -> replay -> runtime authority
```

---

## 2. New v1.5 owning documents

1. `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md`
2. `refs/duotronic_node_federation_protocol_v1_0.md`
3. `refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md`
4. `refs/duotronic_container_deployment_and_node_lifecycle_reference_v1_0.md`
5. `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`

Updated v1.5 integration documents:

1. `refs/duotronic_policy_shield_guide_v1_8.md`
2. `refs/duotronic_schema_registry_v1_10.md`
3. `refs/duotronic_lab_evidence_registry_v1_7.md`
4. `refs/schemas/duotronic_v1_5_draft_2_starter_object_shapes.json`

---

## 3. Cluster runtime flow

```text
Docker node starts
-> collects local system metrics
-> wraps metrics as EvidenceBundle
-> emits ResourceMetricSourceRecord
-> canonicalizes ResourceAvailabilityWitness
-> creates NodeSelfModelSnapshot
-> opens DBP S2 / DBP-HS1 control stream
-> sends NodeHello
-> receives NodeAccept
-> publishes NodeHeartbeat
-> listens for delegate_task commands
-> executes task if local policy allows
-> emits TaskOutcomeWitness
-> coordinator updates lookup memory and recurrent state
```

---

## 4. Distributed delegation flow

```text
ClusterDecisionContext
-> planner proposes ActionCandidateWitness(action_kind=delegate_task)
-> TaskDelegationActionPayload
-> Policy Shield checks resource freshness, queue, privacy, transport, lane layout, and learning mode
-> DelegatedTaskRecord
-> DBP command lane
-> worker execution
-> TaskOutcomeWitness
-> DW-SSM update and/or profile-learning output
```

If any authority-bearing check fails:

```text
delegation_authority = 0
```

---

## 5. Resource witness rule

A node's metrics become scheduling evidence only through:

```text
ResourceMetricSourceRecord
-> ResourceAvailabilityWitness
-> freshness check
-> policy gate
```

The capacity score uses:

```text
capacity = p - lambda * q
```

and stability uses:

```text
S(p,q) = clamp01(1 - |q| / (|p| + |q| + epsilon))
```

The default stale threshold is:

```text
30 seconds
```

---

## 6. DBP cluster profile rule

The cluster DBP profile is:

```text
dbp-cluster-full-duplex-v1
```

Hard requirements:

1. authority-bearing traffic must use S2;
2. Open/S1 frames are rejected for semantic authority;
3. lane layout is identity-affecting;
4. direction is identity-affecting;
5. semantic descriptor is always required;
6. replay identity binds transport profile, lane layout, direction, registry hashes, and payload hash.

---

## 7. Node federation rule

A new node is not trusted because it connects.

A node becomes schedulable only after:

```text
DBP S2 authentication
-> NodeHello validation
-> identity and capability policy check
-> semantic descriptor and registry compatibility
-> valid initial resource witness
-> NodeAccept
-> fresh heartbeat
```

---

## 8. Hardware prototype

Reference prototype:

1. five dual-Xeon X5690 machines;
2. one Ryzen 5950X with RTX 2070 and Quadro P2000;
3. Docker on all machines;
4. 1 Gbps local network;
5. coordinator scheduling CPU-bound and GPU-bound tasks.

Demonstration goals:

1. automatic federation;
2. resource witness publication;
3. CPU-bound task distribution across Xeon nodes;
4. GPU task selection of GPU node;
5. search task distribution;
6. stale-node invalidation after heartbeat timeout;
7. task reassignment after overload/disconnect;
8. DBP S2 enforcement;
9. conformance fixture pass.

---

## 9. Recurrent-memory guardrails

> **Status tag:** normative

This section states the hard boundaries between fast recurrent computation and authoritative persistent memory in a distributed Duotronic cluster.

These rules apply to WG-RNN cells, DW-SSM state, lookup memory, or any other recurrent or persistent-state component in the cluster.

### 9.1 Fast recurrent state is computation only

Fast hidden state `h_t` and fast cell state `c_t` in any recurrent component are temporary computation artifacts.

They must not be:

1. stored as `CanonicalWitnessFact` without extraction through the full evidence pipeline;
2. used to directly approve a `SlotPromotionRequest`;
3. broadcast to other nodes as authoritative evidence;
4. used to override a policy gate or clamp;
5. fed back as the sole input to the next step's witness feature vector without external canonical evidence.

### 9.2 Persistent memory cannot self-confirm

A memory slot or lookup record must not raise its own stability or authority based solely on the cell's own prior outputs.

Self-confirmation is forbidden. Stability requires:

1. canonical witness facts from external evidence;
2. a successful replay trace;
3. retention diagnostics from the standard profile;
4. policy approval.

### 9.3 Scheduler feedback must not contaminate evidence quality

Task outcomes, resource witness values, queue pressure scores, or any scheduling-layer signal must not be injected directly into a recurrent cell as raw input for persistent memory updates.

Scheduling feedback must travel through:

```text
TaskOutcomeWitness
-> EvidenceBundle
-> CandidateWitness
-> canonicalization
-> CanonicalWitnessFact
-> WitnessFeatureVector
```

before it may influence memory gates in a WG-RNN or DW-SSM.

### 9.4 Task outcomes cannot rewrite policy autonomously

A `TaskOutcomeWitness` may produce evidence that a policy change is warranted. It may not directly modify any policy threshold, trust limit, or runtime mode.

Proposed policy changes from task outcomes must follow:

1. `PolicyChangeProposal`;
2. coordinator review;
3. human review if policy requires;
4. new policy snapshot;
5. broadcast and acknowledgment before taking effect.

### 9.5 Cluster-wide state synchronization boundary

Coordinator lookup memory and recurrent state may be updated with task outcome evidence.

The following are still required even in the distributed case:

1. canonicalization of outcome evidence before any state update;
2. policy gate before update affects scheduling authority;
3. replay identity binding that includes the remote node ID and transport replay identity;
4. the authority formula applies: `min(profile_requested, normalizer_confidence, policy_limit)`.

If a node is later revoked, any recurrent or lookup state derived solely from that node's output must be reviewed, demoted, or quarantined per policy.

---

## 10. Non-claims

v1.5 does not prescribe one scheduler, orchestrator, database, model runtime, or Rust implementation.

It specifies the witness, policy, replay, transport, and conformance requirements that a distributed Duotronic cluster must preserve.
