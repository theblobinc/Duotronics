# Duotronic Source Architecture Overview v1.7

**Status:** Internal source architecture draft  
**Version:** 1.7-source-overview  
**Document kind:** Reference architecture and reading guide  
**Primary purpose:** Explain the current v1.4 Duotronic source-spec stack, including DPFC, the Witness Contract, representation bridges, auto-profile learning, distributed model nodes, search/social evidence ingestion, and policy-gated profile promotion.

---

## 1. What Duotronics is in v1.4

Duotronics is a presence-first, witness-gated, representation-bridging and profile-learning framework.

It is designed to take many forms of information, including mathematical notation, scripts, language, images, documents, social feeds, search results, and machine-learning model outputs, and route them through explicit witness and canonicalization paths.

The system is not built around a single universal parser. It is built around profiles.

A profile declares:

1. what kind of object exists;
2. how to validate it;
3. how to distinguish absence, zero, invalidity, and unknown;
4. how to normalize it;
5. how to serialize it;
6. how to bridge it into the DPFC core or another canonical object layer;
7. how to test it;
8. how to govern its authority.

The v1.4 addition is that profiles may be learned or proposed automatically, but they still require validation, replay, retention diagnostics, registry staging, and policy approval.

---

## 2. The source-spec stack

```text
Source Architecture
|
|-- DPFC Core
|   |-- realized magnitudes
|   |-- family-native values
|   |-- canonical identity
|   |-- bridge boundaries
|   |-- export/import policy
|
|-- Representation Bridge Contract
|   |-- source profile
|   |-- target profile
|   |-- canonical object
|   |-- preservation claims
|   |-- expected loss
|
|-- Witness Contract
|   |-- evidence bundles
|   |-- model witnesses
|   |-- candidate witnesses
|   |-- canonical witness facts
|   |-- L1/L2/L2M/L3/L4/L5 runtime path
|
|-- Auto-Profile Learning Contract
|   |-- segmentation discovery
|   |-- relation discovery
|   |-- candidate profile synthesis
|   |-- fixture generation
|   |-- cross-model adjudication
|
|-- Distributed Model Node Protocol
|   |-- node-local inference
|   |-- model witness emission
|   |-- cross-node replay
|   |-- cluster adjudication
|
|-- Search and Social Evidence Ingestion
|   |-- source records
|   |-- claim witnesses
|   |-- source reliability diagnostics
|   |-- contradiction witnesses
|
|-- Registries and Implementation Specs
|   |-- schema registry
|   |-- family registry
|   |-- profile synthesis registry
|   |-- normalizer profiles
|   |-- transport profiles
|   |-- policy shield
|   |-- migration guide
|   |-- retention diagnostics
|
`-- Research and Reference Profiles
    |-- Roman numerals
    |-- English claim/evidence
    |-- glyphic script visual-semantic
    |-- EDO
    |-- acoustics
    |-- QCD analogy
    |-- selective witness state spaces
    |-- GCD-jump recurrences
    `-- pronic-centered polygon families
```

---

## 3. Primary data movement

The standard runtime flow is:

```text
raw event
-> source/transport validation
-> evidence bundle
-> modality decode
-> candidate witness extraction
-> registry lookup
-> normalizer selection
-> canonicalization
-> policy gate
-> lookup memory
-> recurrent state
-> retention diagnostics
-> replay identity
-> possible meta or architecture action
```

The auto-profile learning flow is:

```text
unprofiled stream
-> evidence bundle cluster
-> model witnesses
-> segmentation candidates
-> relation candidates
-> witness candidates
-> profile candidate
-> normalizer candidate
-> bridge candidate
-> fixture pack
-> replay trace set
-> adjudication
-> registry staging
-> sandbox or rejection
```

The two flows are intentionally separate. The first flow uses approved profiles. The second flow proposes new profiles.

---

## 4. Ownership boundaries

| Concern | Owning document |
|---|---|
| Positive core and family-aware representation | DPFC |
| Runtime trust and failure states | Witness Contract |
| Bridge profile schema and preservation/loss rules | Representation Bridge Contract |
| Learned profile lifecycle | Auto-Profile Learning Contract |
| Multi-model distributed witness emission | Distributed Model Node Protocol |
| Search/social source evidence | Search Social Evidence Ingestion |
| Profile staging and status ladder | Profile Synthesis Registry |
| Versioned IDs and compatibility | Schema Registry |
| Family declaration and promotion | Family Registry |
| Deterministic normal-form construction | Normalizer Profiles |
| Transport and source wrappers | Transport Profiles |
| Runtime modes, vetoes, bypass, rollback | Policy Shield Guide |
| Semantic changes and replay migration | Migration Guide |
| Measurement of preservation | Retention Diagnostics |
| Historical fixtures and lab lineage | Lab Evidence Registry |

---

## 5. What systems must not confuse

1. Raw source data is not a witness fact.
2. A witness candidate is not canonical identity.
3. A model output is not authority.
4. A learned profile is not a promoted profile.
5. Search support is not proof.
6. Social agreement is not proof.
7. A glyphic visual identity is not necessarily a translation.
8. A normalized English claim is not necessarily a true claim.
9. A bridge that preserves value may still lose display or provenance.
10. A policy-approved runtime gate is not a mathematical theorem.

---

## 6. Minimal implementation shape

A minimal v1.4 implementation should include:

```text
EvidenceBundleStore
ModelWitnessStore
CandidateWitnessStore
CanonicalWitnessStore
SchemaRegistry
FamilyRegistry
ProfileSynthesisRegistry
NormalizerRegistry
BridgeRegistry
PolicyShield
ReplayHarness
RetentionDiagnostics
MigrationPlanner
DistributedNodeEventLog
```

Minimum APIs:

```text
ingest_evidence()
emit_model_witness()
create_candidate_witness()
synthesize_profile_candidate()
validate_profile_candidate()
canonicalize()
bridge()
policy_gate()
record_replay()
score_retention()
stage_profile()
promote_or_reject_profile()
```

---

## 7. Reading order

For architecture review:

1. README
2. Source Architecture Overview
3. DPFC
4. Witness Contract
5. Representation Bridge Contract
6. Auto-Profile Learning Contract
7. Distributed Model Node Protocol
8. Search/Social Evidence Ingestion
9. Profile Synthesis Registry
10. Policy Shield Guide
11. Migration Guide

For implementation:

1. Schema Registry
2. Family Registry
3. Normalizer Profiles
4. Representation Bridge Contract
5. Transport Profiles
6. Witness Contract
7. Auto-Profile Learning Contract
8. Retention Diagnostics
9. Policy Shield Guide
10. Migration Guide


---

## 8. Draft 2 architecture clarification

> **Status tag:** reference

Draft 2 adds a central glossary and hardens the profile lifecycle.

The architecture now separates four distinct concerns:

1. **Profile synthesis:** candidate creation, testing, rejection, demotion, and promotion requests.
2. **Family registration:** promoted runtime-referenceable profiles and families.
3. **Learning mode:** whether auto-profile learning may run and what sources/models it may invoke.
4. **Runtime mode:** whether a profile, witness, bridge, source, or gate may influence operation.

A learned or hand-authored profile moves through the Profile Synthesis Registry first. If it is promoted to `reference_profile` or `normative_profile`, it receives a Family Registry handoff record and a runtime-referenceable Family Registry entry.

---

## 9. Draft 3 self-informing system architecture

> **Status tag:** reference

Draft 3 extends the v1.4 architecture with a self-informing loop.

```text
chronological evidence streams
-> timeline witnesses
-> self-reference edges
-> derived preference / habit / likely-action witnesses
-> lookup memory and recurrent state
-> decision context
-> action candidate witness
-> L5 policy gate
-> action execution
-> action outcome witness
-> new evidence
```

This loop allows Duotronic systems to reason internally using their own evidence stores without becoming an ungoverned agent.

### 9.1 New Draft 3 source specs

1. `duotronic_chronological_self_evidence_contract_v1_2.md`
2. `duotronic_lookup_memory_and_replay_profile_v1_2.md`
3. `duotronic_internal_decision_and_planning_contract_v1_2.md`
4. `duotronic_model_diversity_and_adjudication_governance_v1_1.md`

### 9.2 New architecture boundary

The system may use evidence to make internal decisions.

It may not skip:

1. evidence wrapping;
2. witness extraction;
3. canonicalization where required;
4. model diversity governance where required;
5. lookup provenance;
6. policy gating;
7. action outcome recording.

### 9.3 External oracle mitigation

Duotronic does not solve model bias. It makes model reliance explicit by wrapping model outputs as witnesses, comparing diverse models, recording oracle-risk profiles, preserving uncertainty, and allowing L5 policy to down-weight or block homogeneous agreement.

---

## 10. Draft 4 implementation-hardening architecture

> **Status tag:** reference

Draft 4 hardens the self-informing architecture for implementation.

The new action-oriented path is:

```text
timeline / self-model / lookup memory
-> decision context
-> action candidates from one or more planners
-> action conflict record if needed
-> policy decision
-> action execution record
-> action outcome witness
-> invalidation or memory update
```

### 10.1 Planner-triggered profile learning

A planner can propose a profile-learning run only by emitting an `ActionCandidateWitness` with `action_kind: start_profile_learning`.

That action references a `ProfileLearningActionPayload`.

If policy allows the action, the Auto-Profile Learning Contract records a `PlannerTriggeredLearningRun`. The output remains candidate material.

### 10.2 Policy change governance

A planner can propose policy change through `PolicyChangeProposal`.

Policy changes are not self-executing. The active policy remains the current approved policy snapshot until L5 or the configured governance workflow approves a new snapshot.

### 10.3 Self-model invalidation

Self-model snapshots are versioned and actor-scoped. New evidence, source deletion, policy changes, profile demotion, or lookup invalidation may create a `SelfModelInvalidationEvent`.

### 10.4 High-speed loop budgets

High-speed loops now require resource budgets outside audit-only mode. Resource violations create `LoopResourceViolationEvent` records and may throttle, pause, degrade, stop, or trigger policy review.

### 10.5 Worked example

The worked self-informing trace is located at:

```text
refs/examples/duotronic_worked_self_informing_loop_youtube_music_v1_0.md
```

This example should be used as the first implementation walkthrough.

---

## 11. Draft 5 privacy, human review, and calibration hardening

> **Status tag:** reference

Draft 5 adds the final cross-cutting governance mechanisms needed before a first prototype:

1. evidence purge and privacy deletion;
2. human-in-the-loop review protocol;
3. planner-triggered learning promotion guard;
4. cross-version replay rules for stale self-models and lazy actions;
5. observe-only default for uncalibrated diversity-weighted agreement scores.

### 11.1 Purge architecture

```text
EvidencePurgeRequest
-> PurgeDependencyGraph
-> EvidencePurgeAuthorization
-> EvidencePurgeEvent
-> cascade to witnesses / lookup / profiles / self-models / actions / replay
-> PurgeTombstone and PurgeReplayImpactRecord
```

Purge is stronger than invalidation. It removes, tombstones, quarantines, or cryptographically erases according to policy.

### 11.2 Human review architecture

```text
trigger
-> HumanReviewRequest
-> HumanReviewPacket
-> HumanReviewDecision
-> HumanReviewFeedbackRecord
-> policy / profile / action / purge / fixture impact
```

Human review is a recorded evidence event, not an undocumented side channel.

### 11.3 Planner promotion guard

Planner-triggered profile learning may create candidate material only. Direct promotion is ignored or rejected. The Profile Synthesis Registry is the only promotion path.

### 11.4 Replay architecture for stale self-models

Old decision contexts may be replayed for audit if snapshot versions, policy versions, and purge state are pinned. Stale or purge-impacted decisions may not justify new runtime actions unless policy explicitly permits.

### 11.5 Diversity score calibration

Diversity-weighted agreement scores remain observe-only until calibrated and policy-approved.

---

## 12. Draft 5 completion-pass architecture

> **Status tag:** reference

The Draft 5 completion pass resolves the last nonblocking governance gaps.

### 12.1 Purge proof path

```text
EvidencePurgeEvent
-> PurgeAttestation
-> optional ExternalPurgeNotarization
-> PurgeAttestationVerification
```

This provides a portable, content-safe proof path for auditors or external compliance systems.

### 12.2 External index invalidation path

```text
ExternalIndexTarget
-> ExternalIndexInvalidationRequest
-> ExternalIndexInvalidationResult
-> residual risk record
-> purge attestation
```

This standardizes purge propagation to vector stores, graph stores, search indexes, caches, feature stores, and other external indexes.

### 12.3 Human review timeout path

```text
HumanReviewRequest without deadline
-> HumanReviewTimeoutPolicy
-> computed deadline/default
-> HumanReviewExpirationEvent if unanswered
```

This prevents human review from becoming an indefinite pending state.

### 12.4 Meta-runtime governance replay

```text
shadow replay
-> MetaReplayGovernanceState
-> pinned stale self-models / purge events / human decisions / diversity calibration
-> audit-only or policy-exception runtime reuse
```

---

## 13. v1.5 distributed self-governing recurrent network architecture

> **Status tag:** reference

v1.5 extends the corpus from a self-informing single-system architecture to a distributed, federated, self-governing recurrent network.

The new cluster loop is:

```text
node system metrics
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
-> target node execution
-> TaskOutcomeWitness
-> recurrent / lookup / profile-learning update
```

The new federation loop is:

```text
Docker container start
-> initial resource witness
-> DBP S2 / DBP-HS1 connection
-> NodeHello
-> policy admission
-> NodeAccept
-> lane layout install
-> heartbeat/resource publishing
-> task command listening
```

The new DBP cluster transport profile is:

```text
dbp-cluster-full-duplex-v1
```

### 13.1 v1.5 owning specs

1. `duotronic_distributed_task_delegation_and_resource_witness_contract_v1_0.md`
2. `duotronic_node_federation_protocol_v1_0.md`
3. `duotronic_dbp_inter_node_full_duplex_profile_v1_0.md`
4. `duotronic_container_deployment_and_node_lifecycle_reference_v1_0.md`
5. `duotronic_v1_5_cluster_conformance_fixtures_v1_0.md`

### 13.2 v1.5 hard boundary

Raw machine metrics are not scheduling authority.

A node can contribute resources only through:

```text
evidence wrapping
-> resource witness canonicalization
-> freshness check
-> node admission policy
-> task delegation policy
-> DBP S2 transport
```

### 13.3 v1.5 prototype topology

The reference prototype contains:

1. five dual-Xeon X5690 workers;
2. one Ryzen 5950X worker with RTX 2070 and Quadro P2000;
3. 1 Gbps LAN;
4. Dockerized node daemon on every machine;
5. coordinator scheduling CPU/GPU/search/profile tasks.

---

## 14. v1.5 Draft 2 WG-RNN architecture

> **Status tag:** reference

v1.5 Draft 2 adds the Witness-Gated Recurrent Cell as a research-profile runtime memory component.

WG-RNN flow:

```text
chronological evidence
-> canonical witness facts
-> WitnessFeatureVector
-> fast recurrent computation
-> witness-specific gates
-> hard policy clamps
-> MemoryUpdateRecord
-> candidate / quarantined / stable memory slot
```

The cell separates:

1. fast recurrent state for computation;
2. persistent witness memory for structured long-term memory;
3. witness features for gate control;
4. policy clamps for trust enforcement;
5. replay records for every memory update;
6. slot promotion for stable memory.

Raw inputs do not update persistent memory. Fast state does not become truth.
