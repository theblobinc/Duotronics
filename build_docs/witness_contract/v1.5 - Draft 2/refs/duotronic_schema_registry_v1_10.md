# Duotronic Schema Registry v1.10

**Status:** Source-spec baseline candidate  
**Version:** schema-registry@v1.10  
**Supersedes:** schema-registry@v1.9  
**Supersedes:** schema-registry@v1.8  
**Supersedes:** schema-registry@v1.7  
**Supersedes:** schema-registry@v1.6  
**Supersedes:** schema-registry@v1.5  
**Supersedes:** schema-registry@v1.4  
**Supersedes:** schema-registry@v1.3  
**Document kind:** Normative registry plus reference schemas  
**Primary purpose:** Define stable identifiers, version rules, compatibility classes, schema-entry shapes, and fixture conventions used by DPFC, the Witness Contract, representation bridges, auto-profile learning, distributed nodes, search/social evidence, retention diagnostics, policy shielding, and migration.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

The Schema Registry governs machine-readable identifiers for source documents and runtime artifacts.

It covers:

1. document identifiers;
2. schema identifiers;
3. family identifiers;
4. profile identifiers;
5. bridge identifiers;
6. normalizer identifiers;
7. transport/source profile identifiers;
8. evidence bundle schemas;
9. model witness schemas;
10. node event schemas;
11. retention metric identifiers;
12. policy profile identifiers;
13. migration profile identifiers;
14. replay identity identifiers;
15. fixture-pack identifiers.

---

## 2. Identifier rule

Every object that affects canonical identity, trust, transport/source validation, profile synthesis, retention scoring, migration, replay, or policy must carry a versioned identifier.

Recommended shape:

```text
namespace/name@major.minor.patch
```

Examples:

```text
dpfc/core@5.14.0
witness/contract@10.16.0
bridge/roman-to-core@1.0.0
profile/roman-numeral@0.1.0
evidence/source-record@1.0.0
model-witness/base@1.0.0
node-event/base@1.0.0
policy/profile-promotion-minsafe@1.0.0
```

---

## 3. Compatibility classes

| Class | Meaning | Required action |
|---|---|---|
| patch-compatible | no semantic change | replay optional unless policy requires |
| minor-compatible | additive compatible change | replay recommended |
| semantic-change | can alter identity, bridge, policy, or interpretation | migration and replay required |
| incompatible | old and new cannot safely mix | explicit migration or rejection |
| research-only | not approved for authority | audit-only or sandbox |
| deprecated | allowed only for replay or migration | no new promotion |
| rejected | known unsafe or failed | blocked unless new evidence opens a new candidate |

---

## 4. Registry entry schema

```yaml
SchemaRegistryEntry:
  registry_entry_id: string
  object_id: string
  version: string
  kind: document | schema | family | profile | bridge | normalizer | transport | evidence | model_witness | node_event | policy | migration | metric | fixture
  status: candidate | research_valid | sandbox_runtime | reference | normative | deprecated | rejected
  owner_document: string
  compatibility_class: string
  canonical_identity_impact: none | possible | direct
  replay_required: true | false
  migration_required: true | false
  dependencies: []
  fixture_pack_id: string | null
```

---

## 5. Carried-forward profile-learning registered classes

The carried-forward profile-learning baseline introduces these major schema classes:

1. `EvidenceBundle`;
2. `SourceEvidenceRecord`;
3. `ModelWitness`;
4. `NodeWitnessEvent`;
5. `CandidateWitness`;
6. `AutoProfileCandidate`;
7. `RepresentationBridgeProfile`;
8. `BridgeResult`;
9. `CandidateProfileRecord`;
10. `ProfilePromotionRequest`;
11. `CrossModelAdjudication`;
12. `ShadowReplayResult`.

---

## 6. Non-claims

The Schema Registry supplies stable names and compatibility rules. It does not decide trust. Trust requires the Witness Contract and Policy Shield.


---

## 7. Draft 2 required object schemas

> **Status tag:** normative

The starter object shape bundle must include at least these schema classes:

1. `EvidenceBundle`;
2. `SourceEvidenceRecord`;
3. `SourceAvailabilityEvent`;
4. `ModelWitness`;
5. `ModelExecutionRecord`;
6. `NodeWitnessEvent`;
7. `NonDeterminismRecord`;
8. `CandidateWitness`;
9. `CanonicalWitnessFact`;
10. `AutoProfileCandidate`;
11. `RepresentationBridgeProfile`;
12. `BridgeResult`;
13. `CandidateProfileRecord`;
14. `ProfilePromotionRequest`;
15. `FamilyRegistryHandoff`;
16. `PolicyDecision`;
17. `LearningPolicy`;
18. `RetentionMetricSpec`;
19. `MigrationPlan`;
20. `ShadowReplayResult`;
21. `CrossModelAdjudication`;
22. `VisualIdentity`;
23. `ClaimWitness`.

Schema entries may start as skeletons, but each must identify required fields, status values, and owning document.


---

## 8. Draft 3 required object schemas

> **Status tag:** normative

Draft 3 adds these schema classes:

1. `ChronologicalEvidenceStream`;
2. `SelfReferenceEdge`;
3. `PersonalHistorySourceRecord`;
4. `TimelineWitness`;
5. `PreferenceWitness`;
6. `HabitWitness`;
7. `LikelyActionWitness`;
8. `SelfModelSnapshot`;
9. `LookupMemoryRecord`;
10. `HighSpeedLoopProfile`;
11. `LookupInvalidationEvent`;
12. `DecisionContext`;
13. `ActionCandidateWitness`;
14. `ActionExecutionRecord`;
15. `ActionOutcomeWitness`;
16. `DecisionSupportFact`;
17. `OracleRiskProfile`;
18. `ModelDiversitySet`;
19. `ModelAdjudicationRecord`;
20. `DiversityWeightedAgreement`.

Each object must identify owning document, required fields, policy mode fields where applicable, and replay or provenance fields where applicable.


---

## 9. Draft 4 required object schemas

> **Status tag:** normative

Draft 4 adds these schema classes:

1. `ActorScope`;
2. `SelfModelInvalidationEvent`;
3. `LikelyActionToActionLink`;
4. `LoopResourceViolationEvent`;
5. `ProfileLearningActionPayload`;
6. `PlannerTriggeredLearningRun`;
7. `PolicyChangeProposal`;
8. `ActionConflictRecord`.

These are cross-cutting safety and implementation objects. They must be included in starter object shapes and any implementation schema registry that claims v1.4 Draft 4 compatibility.


---

## 10. Draft 5 required object schemas

> **Status tag:** normative

Draft 5 adds these schema classes:

1. `EvidencePurgeRequest`;
2. `EvidencePurgeAuthorization`;
3. `PurgeDependencyGraph`;
4. `EvidencePurgeEvent`;
5. `PurgeTombstone`;
6. `PurgeReplayImpactRecord`;
7. `HumanReviewRequest`;
8. `HumanReviewPacket`;
9. `HumanReviewDecision`;
10. `HumanReviewFeedbackRecord`;
11. `MultiPartyReviewRule`;
12. `LazyActionRecord`;
13. `LookupPurgeImpact`;
14. `ProfilePurgeImpactRecord`;
15. `DiversityScoreCalibrationProfile`.

Any implementation claiming v1.4 Draft 5 compatibility must include these object classes or declare them out of scope with a policy reason.


---

## 11. Draft 5 completion-pass required object schemas

> **Status tag:** normative

The Draft 5 completion pass adds these schema classes:

1. `PurgeAttestation`;
2. `ExternalPurgeNotarization`;
3. `PurgeAttestationVerification`;
4. `ExternalIndexTarget`;
5. `ExternalIndexInvalidationRequest`;
6. `ExternalIndexInvalidationResult`;
7. `HumanReviewTimeoutPolicy`;
8. `HumanReviewExpirationEvent`;
9. `LookupExternalIndexMapping`;
10. `PurgeProofPolicy`;
11. `MetaReplayGovernanceState`.

These are required for complete Draft 5 governance compatibility when purge, human review, external index invalidation, or meta-runtime replay are in scope.


---

## 12. v1.5 distributed cluster object schemas

> **Status tag:** normative

v1.5 adds the following schema classes for distributed self-governing recurrent networks:

1. `ResourceMetricSourceRecord`;
2. `ResourceAvailabilityWitness`;
3. `NodeSelfModelSnapshot`;
4. `TaskQueueWitness`;
5. `TaskDelegationActionPayload`;
6. `DelegatedTaskRecord`;
7. `TaskOutcomeWitness`;
8. `ClusterDecisionContext`;
9. `TaskDelegationConflict`;
10. `NodeIdentity`;
11. `NodeHello`;
12. `NodeAccept`;
13. `NodeReject`;
14. `NodeHeartbeat`;
15. `NodeDisconnectEvent`;
16. `NodeDepart`;
17. `NodeDepartAck`;
18. `NodeRevocation`;
19. `RegistrySyncMessage`;
20. `DBPInterNodeProfile`;
21. `DBPLaneLayout`;
22. `ClusterSemanticDescriptor`;
23. `AuthorityEnvelope`;
24. `DBPClusterReplayIdentity`;
25. `ClusterDelegationPolicy`;
26. `NodeAdmissionPolicy`;
27. `ClusterLearningPolicy`;
28. `NodeQuarantinePolicy`;
29. `ClusterHardwareProfile`.

Any implementation claiming v1.5 cluster compatibility must include these schema classes or explicitly mark them out of scope.


---

## 13. v1.5 Draft 2 WG-RNN object schemas

> **Status tag:** normative

v1.5 Draft 2 adds the following WG-RNN research-profile schema classes:

1. `WGRNNStepInput`;
2. `WitnessFeatureVector`;
3. `MemorySlot`;
4. `SlotSplitRecord`;
5. `SlotConsolidationRecord`;
6. `MemorySlotPruneRecord`;
7. `SlotPromotionRequest`;
8. `MemoryUpdateRecord`;
9. `WitnessGatedRecurrentCellProfile`;
10. `WitnessGatedRecurrentCellPolicy`;
11. `WGRNNReplayIdentity`;
12. `MemoryPurgeImpactRecord`.

These schema classes are owned by:

```text
refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md
```

WG-RNN v1.0 is a research profile. Implementations must not treat it as normative memory behavior unless promoted through replay, fixtures, retention diagnostics, and policy.

## 14. v1.5 Draft 2 cognition research object schemas

> **Status tag:** normative research-profile registry

v1.5 Draft 2 adds the following bounded cognition research schema classes.

Rho-Padovan recurrent-memory kernel:

1. `RhoKernelConfig`;
2. `RhoPadovanTrace`;
3. `RhoMemoryStepInput`;
4. `RhoMemoryStepResult`;
5. `RhoKernelDiagnostics`;
6. `RhoKernelReplayIdentity`.

Multi-view learning engine:

1. `ConceptProfile`;
2. `ViewProfile`;
3. `ViewBridge`;
4. `LearnerIntent`;
5. `MisconceptionRecord`;
6. `ExplanationContract`;
7. `LearningSessionState`;
8. `LearningRouteDiagnostics`.

These schema classes are owned by:

```text
refs/duotronic_rho_padovan_recurrent_memory_kernel_v0_1.md
refs/duotronic_multi_view_learning_engine_contract_v0_1.md
```

Both profiles are research-only. Implementations must not treat rho recurrence or learning-view routing as canonical witness authority without explicit policy approval and replay evidence.
