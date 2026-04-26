# Corpus Review: v1.4 Draft 2 to v1.4 Draft 3

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.4-draft-2-to-draft-3  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record how Draft 3 responds to the concern that Duotronic depends on external models and heuristics, and how the corpus now supports self-referential chronological evidence, diverse model adjudication, high-speed memory, and internal decision-making.

---

## 1. Review concern

Draft 2 made profile learning governable, but the next concern was deeper:

```text
If Duotronic depends on external models, human heuristics, search engines, and social evidence, how does it avoid becoming dependent on a single biased oracle?
```

Draft 3 does not claim to solve alignment. It makes dependence explicit, governable, diverse, replayable where required, and policy-scoped.

---

## 2. Draft 3 architectural response

Draft 3 adds four owning source specs:

1. `duotronic_chronological_self_evidence_contract_v1_2.md`
2. `duotronic_lookup_memory_and_replay_profile_v1_2.md`
3. `duotronic_internal_decision_and_planning_contract_v1_2.md`
4. `duotronic_model_diversity_and_adjudication_governance_v1_1.md`

Together, they allow the system to ingest chronological self-evidence, run high-speed memory loops, compare diverse model witnesses, make internal decisions, and learn from action outcomes without granting authority to raw models or raw source streams.

---

## 3. Major principle

The new Draft 3 principle is:

```text
The system may inform itself,
but self-informing loops are still witness-gated.
```

The system may use personal history, project history, social history, YouTube-like media history, model output history, and prior Duotronic decisions as evidence. But those sources become evidence bundles, timeline witnesses, self-model snapshots, preference witnesses, likely-action witnesses, and action-support facts. They do not become identity, truth, or action authority by themselves.

---

## 4. Internal rationality layer

Draft 3 adds a decision pathway:

```text
canonical facts
-> lookup memory
-> recurrent state
-> decision context
-> action candidate witness
-> policy gate
-> action execution
-> action outcome witness
```

This makes planning and action part of the witness system.

A planner can be an LLM, symbolic planner, reinforcement learner, rule engine, DW-SSM gate, or human-assisted workflow. Its output is a candidate witness until policy approves it.

---

## 5. High-speed memory and Redis-like loops

Draft 3 explicitly permits Redis-like stores, key-value stores, vector stores, graph stores, and time-series stores as implementations of L2M lookup memory.

The important boundary is:

```text
fast lookup is not authority
```

A fast memory record must point back to canonical facts, source records, profile records, bridge results, policy decisions, or explicit audit-only candidates.

---

## 6. Model diversity and oracle-risk governance

Draft 3 adds model diversity sets and oracle-risk profiles.

Model agreement is stronger only when models are meaningfully diverse. Homogeneous agreement from models with shared data, shared architecture, or shared failure modes must be down-weighted or treated as weak support.

This mitigates the external-oracle critique without claiming to eliminate it.

---

## 7. New object classes

Draft 3 adds starter schema objects for:

1. `ChronologicalEvidenceStream`
2. `SelfReferenceEdge`
3. `PersonalHistorySourceRecord`
4. `TimelineWitness`
5. `PreferenceWitness`
6. `HabitWitness`
7. `LikelyActionWitness`
8. `SelfModelSnapshot`
9. `LookupMemoryRecord`
10. `HighSpeedLoopProfile`
11. `LookupInvalidationEvent`
12. `DecisionContext`
13. `ActionCandidateWitness`
14. `ActionExecutionRecord`
15. `ActionOutcomeWitness`
16. `DecisionSupportFact`
17. `OracleRiskProfile`
18. `ModelDiversitySet`
19. `ModelAdjudicationRecord`
20. `DiversityWeightedAgreement`

---

## 8. Implementation priority after Draft 3

Recommended proof-of-concept order:

1. ingest a small chronological personal or project dataset;
2. wrap items as evidence bundles and personal-history records;
3. build a timeline witness;
4. run two or more diverse models to extract topic/preference witnesses;
5. create a model adjudication record;
6. store derived witnesses in lookup memory;
7. run a restricted internal decision context;
8. emit an action candidate witness;
9. policy-gate the action;
10. record the action outcome.

A practical first target remains a small personal history example such as a limited YouTube-like watch-history dataset, followed by an English claim/evidence extractor and then a glyphic segmentation sandbox.

---

## 9. Final assessment

Draft 3 makes Duotronic more complete as an internal augmented-intelligence framework.

It now specifies not only how profiles are born, but how a Duotronic system can use evidence, memory, model diversity, and policy to inform its own decisions over time.
