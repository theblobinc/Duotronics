# Corpus Review: v1.4 Draft 3 to v1.4 Draft 4

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.4-draft-3-to-draft-4  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record how Draft 4 addresses the remaining implementation gaps found after reviewing Draft 3.

---

## 1. Review finding

Draft 3 was conceptually complete, but several implementation-level issues remained:

1. no worked end-to-end self-informing loop;
2. planner-triggered profile learning was underspecified;
3. policy self-modification was not governed;
4. action conflicts across planners were underspecified;
5. self-model snapshots lacked versioning/invalidation;
6. multi-actor scoping needed clarification;
7. high-speed loops lacked resource budgets;
8. `LikelyActionWitness` and `ActionCandidateWitness` needed a clearer boundary.

Draft 4 addresses these directly.

---

## 2. Major Draft 4 additions

### 2.1 Worked example

Added:

```text
refs/examples/duotronic_worked_self_informing_loop_youtube_music_v1_0.md
```

The example traces a YouTube-like music-history workflow from evidence ingestion through action outcome.

### 2.2 Planner-triggered profile learning

Added `ProfileLearningActionPayload` and `PlannerTriggeredLearningRun`.

A planner may request profile learning only through a policy-gated `ActionCandidateWitness` with `action_kind: start_profile_learning`.

### 2.3 Policy change proposals

Added `PolicyChangeProposal`.

The system may propose policy changes. It may not apply them silently. Increasing authority requires explicit L5 approval.

### 2.4 Action conflict resolution

Added `ActionConflictRecord`.

Default rule:

```text
most restrictive policy wins
```

If no safe restrictive path can be determined, the system chooses no-action, audit-only, policy review, or human review.

### 2.5 Self-model versioning and invalidation

Added:

1. `ActorScope`;
2. versioned `SelfModelSnapshot`;
3. `SelfModelInvalidationEvent`;
4. invalidation propagation rules.

### 2.6 Multi-actor scoping

Every self-model must be actor-scoped or explicitly group/organization-scoped.

Ambiguous actor selection routes to audit-only, disambiguation, or most restrictive policy.

### 2.7 Resource limits

Added resource budget and overload policy to `HighSpeedLoopProfile`, plus `LoopResourceViolationEvent`.

High-speed loops without resource budgets may run only in audit-only mode.

### 2.8 Likely action vs action candidate

Clarified:

```text
LikelyActionWitness = prediction
ActionCandidateWitness = proposal
```

A likely action cannot auto-execute. Conversion requires `LikelyActionToActionLink` and policy.

---

## 3. Implementation readiness

Draft 4 is now ready for a first proof of concept:

1. import a small chronological media history;
2. create evidence bundles and personal-history records;
3. build a timeline witness;
4. derive preference witnesses with multiple models;
5. adjudicate model outputs;
6. write lookup memory records;
7. create a self-model snapshot;
8. run a restricted decision context;
9. propose a search action;
10. policy-gate and execute it;
11. record action outcome;
12. update memory and invalidation records.

---

## 4. Final Draft 4 principle

```text
The system may model itself or many actors,
but each model is scoped, versioned, invalidatable, and policy-gated.
```
