# Duotronic v1.5 Draft 2 Corpus

**Status:** Internal source corpus draft  
**Version:** v1.5-draft-2  
**Document kind:** Integrated source corpus for distributed Duotronic implementers, machine-learning systems, augmented-intelligence agents, and internal review  
**Primary purpose:** Extend the completed v1.4 Draft 5 corpus into a distributed, federated, self-governing recurrent network where nodes auto-federate over DBP v2 S2 full-duplex streams, publish computational resources as canonical witnesses, delegate tasks through policy-gated decisions, and adapt through task outcomes without granting authority to raw metrics or unauthenticated transport.

---

## 0. Program-level entry points

Before reading the v1.5 release notes below, new readers should anchor on:

1. `duotronic_program_charter_v1_0.md` — program scope, separation rule, and relationship to the legacy chapter material.
2. `v1_5_draft_2_reading_guide.md` — corpus map and reading order by role.
3. `duotronic_canonical_implementation_target_v0_1.md` — canonical implementation target status (currently TBD).
4. `refs/duotronic_source_architecture_overview_v1_7.md` — architecture map.
5. `refs/duotronic_glossary_v1_0.md` — terminology authority.

The rest of this README focuses on what v1.5 Draft 2 *adds* on top of the v1.4 Draft 5 corpus.

---

## Draft 2 addition: Witness-Gated Recurrent Cell

v1.5 Draft 2 adds the WG-RNN research profile:

```text
refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md
```

The WG-RNN is a Duotronic runtime cell that uses canonical witness features as explicit gates for persistent memory updates.

It adds:

1. `WitnessFeatureVector`
2. `MemorySlot`
3. `MemoryUpdateRecord`
4. `WitnessGatedRecurrentCellProfile`
5. `WitnessGatedRecurrentCellPolicy`
6. `SlotPromotionRequest`
7. purge-aware memory cascade records
8. hard policy clamps for write, decay, quarantine, and promotion gates
9. replayable local online adaptation without global backpropagation
10. fixtures and a worked music-preference memory example
11. a PyTorch implementation skeleton (`refs/examples/duotronic_wgrnn_pytorch_skeleton_v1_0.md`)
12. a closure and implementation roadmap (`v1_5_draft_2_next_steps.md`)

WG-RNN v1.0 is research-only until promoted through benchmark evidence, replay fixtures, retention diagnostics, purge tests, and policy approval.

## Draft 2 additions: Rho kernel and multi-view learning

v1.5 Draft 2 also incorporates two bounded research profiles:

1. `refs/duotronic_rho_padovan_recurrent_memory_kernel_v0_1.md` — an optional plastic-ratio / Padovan recurrence kernel for branch-local memory, ranking diagnostics, and canonical-shadow experiments.
2. `refs/duotronic_multi_view_learning_engine_contract_v0_1.md` — an additive concept-routing layer that preserves multiple valid views of the same concept and exposes formal guardrails in learning explanations.

Both profiles are experimental. The rho kernel must remain feature-flagged and non-canonical unless replay parity, ranking stability, diagnostics, and policy approval are present. The multi-view learning engine must not replace canonical witness extraction or synthesis; it routes and explains concepts above those layers.

## 1. What v1.5 adds

v1.5 adds the distributed cluster layer.

New capabilities:

1. node resource availability as canonical witness facts;
2. node-level self-model snapshots;
3. stale resource invalidation;
4. task queue witnesses;
5. resource-aware task delegation;
6. distributed conflict resolution for node overcommit;
7. task outcome witnesses;
8. DBP v2 S2 full-duplex cluster lanes;
9. Docker-native node auto-federation;
10. coordinator/worker heartbeat protocol;
11. policy-gated node admission and revocation;
12. cluster-wide learning mode;
13. conformance fixtures for a six-machine prototype.

---

## 2. Core v1.5 principle

```text
Raw machine metrics are not scheduling authority.
Connected nodes are not trusted by default.
Task delegation is an action candidate until policy approves it.
DBP transport must be S2 for authority-bearing semantic use.
Transport failure zeros delegation authority immediately.
Cluster-wide learning mode is enforced at delegation time, not node time.
```

---

## 3. New v1.5 source specs

1. `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md`
2. `refs/duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md`
3. `refs/duotronic_node_federation_protocol_v1_0.md`
4. `refs/duotronic_dbp_inter_node_full_duplex_profile_v1_0.md`
5. `refs/duotronic_container_deployment_and_node_lifecycle_reference_v1_0.md`
6. `refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`

Updated integration specs:

1. `refs/duotronic_policy_shield_guide_v1_8.md`
2. `refs/duotronic_schema_registry_v1_10.md`
3. `refs/duotronic_lab_evidence_registry_v1_7.md`
4. `refs/schemas/duotronic_v1_5_draft_2_starter_object_shapes.json`

---

## 4. Cluster flow

```text
node metrics
-> EvidenceBundle
-> ResourceMetricSourceRecord
-> ResourceAvailabilityWitness
-> NodeSelfModelSnapshot
-> LookupMemoryRecord
-> ClusterDecisionContext
-> ActionCandidateWitness(delegate_task)
-> PolicyDecision
-> DelegatedTaskRecord
-> DBP command lane
-> worker execution
-> TaskOutcomeWitness
-> recurrent / lookup / learning update
```

---

## 5. Federation flow

```text
Docker container starts
-> daemon collects initial metrics
-> daemon creates initial resource witness
-> daemon opens DBP S2 control stream
-> NodeHello
-> coordinator validates identity, transport, registry, and capabilities
-> NodeAccept
-> semantic descriptor and lane layout installed
-> heartbeat/resource publishing begins
-> node becomes schedulable if policy permits
```

---

## 6. DBP profile

Production inter-node profile:

```text
dbp-cluster-full-duplex-v1
```

Reference lane layout:

| Lane | Name | Direction | Purpose |
|---:|---|---|---|
| 1 | semantic_descriptor | both | schema, registry, lane map |
| 2 | witness_payload | both | Witness8 / WSB2 payload |
| 3 | command | downlink | task delegation, policy, registry sync |
| 4 | resource | uplink | ResourceAvailabilityWitness, TaskQueueWitness |
| 5 | task_result | uplink | TaskOutcomeWitness, ActionOutcomeWitness |
| 6 | model_output | uplink | ModelWitness |
| 7 | search_evidence | uplink | EvidenceBundle, SourceEvidenceRecord |
| 8 | alarm_control | both | revocation, alarms, purge control |
| 9 | replay_audit | both | replay and audit refs |
| 10 | bulk_ref | both | large payload refs |

S2 is mandatory for authority-bearing semantic traffic.

---

## 7. Resource math

Resource capacity uses the Duotronic primitive:

```text
D = (p,q)
capacity = p - lambda * q
```

Stability:

```text
S(p,q) = clamp01(1 - |q| / (|p| + |q| + epsilon))
```

Reference defaults:

```yaml
lambda: 1.0
epsilon: 0.000001
max_staleness_seconds: 30
```

---

## 8. DW-SSM task outcome update

Task outcome evidence may enter DW-SSM recurrent state only through policy-clamped authority:

```text
eta_t = clamp_L5(c_t^norm * 1[J_t > 1] * h(J_t))
```

Authority remains:

```text
authority = min(profile_requested_authority, normalizer_confidence, policy_limit)
```

and is forced to zero if transport or canonicalization fails.

---

## 9. Hardware scenario

Target prototype:

| Machine class | Count | CPU | Threads | RAM | GPU |
|---|---:|---|---:|---:|---|
| Xeon worker | 5 | dual Xeon X5690 | 24 each / ~120 total | 400 GB total | none |
| GPU worker | 1 | Ryzen 5950X | 32 | local RAM | RTX 2070 + Quadro P2000 |

Network:

```yaml
local_network: 1Gbps
runtime: Docker
```

Prototype objectives:

1. automatic node federation;
2. fresh resource witness publication;
3. CPU task delegation to Xeon workers;
4. GPU task delegation to GPU node;
5. task redistribution when a node becomes stale or overloaded;
6. DBP S2 enforcement;
7. conformance fixture validation.

---

## 10. Compatibility with v1.4 Draft 5

v1.5 keeps the v1.4 Draft 5 trust model:

1. evidence before witness;
2. canonicalization before authority;
3. policy before runtime use;
4. replay identity before promotion;
5. purge/privacy and human review remain enforced;
6. planners cannot self-promote profiles;
7. raw model outputs are still evidence only.

v1.5 adds distributed scheduling and DBP cluster federation on top of that trust model.

---

## 11. Recommended implementation order

1. Implement DBP S2 session bootstrap for coordinator and one worker.
2. Implement `NodeHello` / `NodeAccept`.
3. Implement resource metric evidence and `ResourceAvailabilityWitness`.
4. Implement heartbeat every 5 seconds and 30-second stale invalidation.
5. Implement command lane `delegate_task` with weighted least-load scheduler (§20 of delegation contract).
6. Implement transport failure handling, retry/timeout/downgrade rules (§21 of delegation contract).
7. Implement cluster-wide learning mode enforcement at delegation time (§22 of delegation contract).
8. Implement a no-op task and `TaskOutcomeWitness`.
9. Implement CPU-bound model task delegation.
10. Add GPU worker detection and GPU-specific scheduling.
11. Add `TaskQueueWitness` and least-loaded scheduling.
12. Run the v1.5 conformance fixtures.


## Draft 2 WG-RNN memory loop

```text
chronological event
-> EvidenceBundle
-> CandidateWitness
-> CanonicalWitnessFact
-> WitnessFeatureVector
-> WG-RNN fast recurrence
-> policy-clamped memory gates
-> MemoryUpdateRecord
-> candidate / quarantined / stable MemorySlot
-> replay / retention / policy promotion
```

Hard boundary:

```text
Fast recurrent state is computation.
Persistent memory authority requires witness features, replay, and policy.
```

### Contamination prevention

Explicit guardrails enforce this boundary:

1. fast state (`h_t`, `c_t`) must never be used as a canonical witness fact or as the sole provenance of a persistent memory write;
2. scheduler feedback (task outcomes, queue pressure, load data) re-enters the system only through the full evidence canonicalization flow;
3. memory slots must not self-confirm their own beliefs — every canonical fact cited as promotion evidence must trace to an independent evidence source outside the memory bank;
4. gate thresholds must not drift autonomously — all threshold changes require a `PolicyChangeProposal`;
5. profile-learning tasks may not rewrite policy indirectly through task outcome payloads.

These rules are specified in section 27 of the WG-RNN contract.
