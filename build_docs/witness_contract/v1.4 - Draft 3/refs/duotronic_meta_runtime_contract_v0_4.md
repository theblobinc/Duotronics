# Duotronic Meta Runtime Contract v0.4

**Status:** Research specification draft  
**Version:** meta-runtime-contract@v0.4  
**Supersedes:** meta-runtime-contract@v0.3  
**Document kind:** Normative meta-runtime contract plus profile-learning control rules  
**Primary purpose:** Define how L3, L4, L5, objective bundles, policy snapshots, shadow replay, profile proposals, model-node adjudication, and lab-derived evidence operate over canonical lower-layer facts without redefining lower-layer semantics.

---

## 1. Executive summary

The meta runtime has higher-order control authority, not higher semantic authority.

It may:

1. tune bounded runtime controls;
2. compare candidate profiles;
3. run shadow replay;
4. veto unsafe changes;
5. request more evidence;
6. demote weak profiles;
7. coordinate distributed model nodes;
8. record decision evidence;
9. evaluate lab-derived adapters;
10. stage profile candidates.

It may not redefine:

1. DPFC arithmetic;
2. family semantics;
3. canonical identity;
4. normalizer output;
5. transport/source validation;
6. lower-layer witness facts;
7. registry-pinned schemas;
8. policy shield hard stops.

---

## 2. Hard rules

1. Replay identity freshness is required for promotion.
2. Objective bundle freshness is required for optimization.
3. L5 veto dominates objective improvement.
4. L4 semantic changes require migration and rollback.
5. Meta-object normalization must be deterministic.
6. Metrics require policy authority before influencing decisions.
7. Lab-derived evidence is research-valid until promoted.
8. A lab artifact never overwrites a lower-layer canonical object.
9. Model consensus is evidence, not authority.
10. Search/social source volume is evidence, not authority.
11. Candidate profiles require policy-approved staging before runtime use.
12. Profile promotion must be reversible.

---

## 3. Meta objects

```yaml
MetaObject:
  meta_object_id: string
  kind: objective_bundle | policy_snapshot | profile_proposal | migration_proposal | replay_result | adjudication_result | veto_record
  source_refs: []
  canonical_lower_layer_refs: []
  normalizer_id: string
  replay_identity_ref: string
  policy_snapshot_ref: string
  status: candidate | audit_only | approved | vetoed | deprecated
```

A meta object can refer to lower-layer facts. It cannot silently rewrite them.

---

## 4. Objective bundles

Objective bundles may express goals such as:

1. improve profile parse coverage;
2. reduce contradiction rate;
3. increase replay stability;
4. reduce false promotion;
5. preserve absence/zero separation;
6. reduce lookup latency;
7. increase evidence diversity;
8. improve node agreement;
9. reduce unsafe search expansion.

Objective improvement is not enough for promotion. Policy and replay still dominate.

---

## 5. Shadow replay

Shadow replay runs candidate behavior against recorded traces without changing authoritative runtime state.

Required for:

1. learned profile promotion;
2. normalizer changes;
3. bridge changes;
4. policy mode changes;
5. distributed node adjudication changes;
6. source-reliability metric changes;
7. retention metric promotion.

A shadow replay result must include:

```yaml
ShadowReplayResult:
  replay_result_id: string
  candidate_ref: string
  trace_set_id: string
  baseline_profile_id: string | null
  candidate_profile_id: string
  changed_outputs: []
  preserved_invariants: []
  unexpected_losses: []
  policy_violations: []
  recommendation: reject | continue_observing | sandbox | promote | human_review
```

---

## 6. L4 profile proposals

L4 may propose:

1. new profile;
2. profile promotion;
3. profile demotion;
4. profile merge;
5. profile split;
6. bridge update;
7. normalizer update;
8. migration plan;
9. fixture pack update;
10. policy threshold update.

All L4 proposals require L5 review if they can affect authority.

---

## 7. L5 policy dominance

L5 may:

1. approve;
2. block;
3. degrade;
4. bypass;
5. require human review;
6. require more fixtures;
7. require replay;
8. require rollback plan;
9. demote;
10. revoke a profile.

L5 decisions must be recorded as policy snapshots.

---

## 8. Distributed model coordination

Meta runtime may coordinate model roles but must preserve model outputs as raw evidence.

A coordinator may summarize:

1. which models agreed;
2. which disagreed;
3. which sources support;
4. which sources contradict;
5. which fixtures fail;
6. which uncertainty remains.

It may not treat coordination output as canonical truth.

---

## 9. Non-claims

The meta runtime is not a super-semantic layer. It governs, compares, tests, and vetoes. It does not become the mathematical or semantic source of truth.


---

## 10. Draft 3 self-informing meta runtime

> **Status tag:** normative

The meta runtime may use Duotronic evidence to inform internal decisions, but it must not bypass lower-layer trust.

Allowed meta-runtime inputs:

1. canonical witness facts;
2. audit-only candidate witnesses;
3. chronological timeline witnesses;
4. self-model snapshots;
5. lookup memory records;
6. model diversity adjudication records;
7. decision contexts;
8. action outcome witnesses;
9. retention diagnostics;
10. policy snapshots.

The meta runtime may propose:

1. search actions;
2. model calls;
3. profile learning expansions;
4. contradiction checks;
5. demotions;
6. promotions;
7. memory invalidation;
8. human review;
9. no-action decisions.

The meta runtime may not execute external side effects without L5 policy approval.

---

## 11. Objective bundles for internal rationality

> **Status tag:** reference

Draft 3 supports objective bundles for bounded rationality.

Example objective dimensions:

1. maximize source-grounded support;
2. minimize unresolved contradiction;
3. preserve uncertainty;
4. reduce model oracle risk;
5. increase diversity of adjudication;
6. respect privacy;
7. minimize irreversible actions;
8. prefer reversible internal actions;
9. improve self-model predictive stability;
10. improve profile parse coverage.

Objective improvement remains subordinate to L5 policy.

---

## 12. Planner shadow replay

> **Status tag:** normative

Planner behavior may be shadow-replayed before promotion.

A planner shadow replay should compare:

1. decision contexts;
2. proposed actions;
3. policy decisions;
4. executed vs not-executed outcomes;
5. unexpected effects;
6. contradiction changes;
7. lookup-memory changes;
8. source expansion behavior.

A planner must not become a reference or normative decision component without replay and rollback support.
