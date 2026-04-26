# Corpus Review: v1.4 Draft 4 to v1.4 Draft 5

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.4-draft-4-to-draft-5  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record how Draft 5 addresses the remaining small gaps after Draft 4.

---

## 1. Review finding

Draft 4 was implementation-ready, but five smaller cross-cutting gaps remained:

1. no explicit permanent purge/right-to-be-forgotten mechanism beyond invalidation;
2. human-in-the-loop escalation was mentioned but not specified;
3. planner-triggered learning payloads could still theoretically set `promotion_requested: true`;
4. cross-version replay of stale self-models and lazy actions was implied but not explicit;
5. `DiversityWeightedAgreement` had no calibration or threshold guidance.

Draft 5 addresses these gaps.

---

## 2. Evidence purge and privacy deletion

Added:

```text
refs/duotronic_evidence_purge_and_privacy_deletion_contract_v1_0.md
```

New objects include:

1. `EvidencePurgeRequest`;
2. `EvidencePurgeAuthorization`;
3. `PurgeDependencyGraph`;
4. `EvidencePurgeEvent`;
5. `PurgeTombstone`;
6. `PurgeReplayImpactRecord`.

Purge is stronger than invalidation. It cascades to derived witnesses, lookup memory, self-models, profile candidates, action records, replay traces, and lab fixtures.

---

## 3. Human review and escalation

Added:

```text
refs/duotronic_human_review_and_escalation_protocol_v1_0.md
```

New objects include:

1. `HumanReviewRequest`;
2. `HumanReviewPacket`;
3. `HumanReviewDecision`;
4. `HumanReviewFeedbackRecord`;
5. `MultiPartyReviewRule`.

Human review is now a recorded evidence and governance event rather than an informal side channel.

---

## 4. Planner-triggered learning promotion guard

Updated the Auto-Profile Learning Contract:

```text
promotion_requested must be false for planner-triggered learning.
```

If a planner payload sets it to true, the system must reject it or override it to false and record a policy warning.

Only the Profile Synthesis Registry may create a `ProfilePromotionRequest`.

---

## 5. Cross-version replay and lazy actions

Updated the Internal Decision and Planning Contract and Policy Shield.

Old decision contexts may be replayed with stale self-models only if the replay identity pins snapshot version, policy version, staleness state, and purge state.

Default use is audit-only.

Lazy/deferred actions must be re-gated before execution if self-model, policy, source, lookup, or purge state changed.

---

## 6. Diversity score calibration

Updated Model Diversity and Adjudication Governance.

`DiversityWeightedAgreement` is observe-only unless calibrated.

Calibration requires fixture packs, thresholds, known failure modes, baselines, and policy-approved allowed use.

---

## 7. Implementation readiness

Draft 5 is suitable for a first prototype with the following minimal vertical slice:

1. import a small chronological dataset;
2. create evidence and source records;
3. build timeline and self-model snapshots;
4. run model diversity adjudication;
5. create a decision context and action candidate;
6. route a conflict or policy decision to human review;
7. execute a safe internal search;
8. record an action outcome;
9. test purge cascade and replay tombstones;
10. verify planner-triggered profile learning cannot promote directly.

---

## 8. Draft 5 principle

```text
Evidence can be forgotten,
human review is recorded,
planners cannot self-promote,
stale decisions replay only with pinned identity,
and uncalibrated diversity scores observe only.
```
