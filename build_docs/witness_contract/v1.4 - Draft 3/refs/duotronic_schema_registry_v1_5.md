# Duotronic Schema Registry v1.5

**Status:** Source-spec baseline candidate  
**Version:** schema-registry@v1.5  
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
witness/contract@10.14.0
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

## 5. v1.4 new registered classes

v1.4 introduces these major schema classes:

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
