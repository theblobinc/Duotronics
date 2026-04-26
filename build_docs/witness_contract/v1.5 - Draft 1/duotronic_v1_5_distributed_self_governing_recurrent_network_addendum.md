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
2. `refs/duotronic_schema_registry_v1_9.md`
3. `refs/duotronic_lab_evidence_registry_v1_6.md`
4. `refs/schemas/duotronic_v1_5_draft_starter_object_shapes.json`

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

## 9. Non-claims

v1.5 does not prescribe one scheduler, orchestrator, database, model runtime, or Rust implementation.

It specifies the witness, policy, replay, transport, and conformance requirements that a distributed Duotronic cluster must preserve.
