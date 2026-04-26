# Duotronic Policy Shield Guide v1.5

**Status:** Source-spec baseline candidate  
**Version:** policy-shield-guide@v1.5  
**Supersedes:** policy-shield-guide@v1.4  
**Supersedes:** policy-shield-guide@v1.3  
**Document kind:** Normative L5 policy guide plus runtime mode matrix  
**Primary purpose:** Define how L5 shields runtime operation by enforcing feasibility, bypass modes, rollback authority, source governance, model-gating rules, profile promotion boundaries, and safe degradation.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

The Policy Shield is the L5 safety authority.

It governs:

1. source and transport failures;
2. canonicalization failures;
3. lookup failures;
4. model witness risks;
5. search/social evidence risks;
6. learned profile staging;
7. ML model gating;
8. profile promotion;
9. migration;
10. rollback.

---

## 2. Hard rules

L5 must enforce:

1. normal-form-before-trust;
2. transport/source validation before semantics;
3. no silent family reinterpretation;
4. no schema promotion without migration when semantic behavior changes;
5. bypass as valid behavior;
6. failed canonicalization as a first-class state;
7. replay mismatch blocks promotion;
8. metrics require baselines before authority;
9. raw model output cannot directly control authority;
10. search/social evidence cannot directly establish truth;
11. candidate profiles default to audit-only;
12. privacy class constrains model and node routing.

---

## 3. Runtime modes

| Mode | Meaning | Lookup | Recurrence | ML gating | Promotion |
|---|---|---|---|---|---|
| `normal` | all required checks pass | allowed | allowed | allowed | allowed by policy |
| `restricted` | safe but constrained | limited | conservative | limited | limited |
| `sandbox` | experimental isolated path | sandbox only | sandbox only | sandbox only | blocked except sandbox |
| `audit_only` | observe but do not affect authority | observe | no authority | no gate authority | blocked |
| `degraded` | warning state | limited | conservative | limited | blocked or limited |
| `family_bypass` | family-sensitive path disabled | generic only | conservative | blocked if family-dependent | blocked |
| `transport_bypass` | source or transport failed | blocked for failed path | no semantic update | blocked | blocked |
| `lookup_bypass` | lookup unavailable or unsafe | disabled | allowed without lookup | limited | blocked if dependent |
| `profile_bypass` | learned profile unsafe or unapproved | disabled | no profile use | blocked | blocked |
| `full_bypass` | unsafe semantic path | blocked | blocked or minimal | blocked | blocked |

---

## 4. Decision matrix

| Condition | Default mode | Required action |
|---|---|---|
| transport integrity failed | `transport_bypass` | reject semantic decode |
| source hash missing | `transport_bypass` | block source authority |
| absence-zero collision | `full_bypass` | reject decoder/profile |
| family registry missing | `family_bypass` | generic handling only |
| normalizer timeout | `degraded` | bypass affected path |
| replay identity mismatch | `full_bypass` | block promotion and rollback |
| retention metric lacks baseline | `audit_only` | observe only |
| migration plan missing | `degraded` | block L4 promotion |
| lookup p99 over ceiling | `lookup_bypass` | disable lookup enrichment |
| model disagreement high | `audit_only` | preserve uncertainty |
| search sources conflict | `audit_only` | create contradiction witness |
| learned profile has no fixtures | `audit_only` | block runtime use |
| learned profile passes sandbox only | `sandbox` | isolate runtime path |
| privacy class blocks model route | `transport_bypass` | block outbound inference |

---

## 5. ML gating policy

Witnesses may gate machine-learning models only under policy.

Gate classes:

1. input route;
2. model selection;
3. memory retrieval;
4. prompt or task profile selection;
5. search expansion;
6. tool access;
7. profile candidate generation;
8. output confidence handling;
9. safety review.

Gate authority requires:

1. canonical witness or approved sandbox witness;
2. runtime mode permitting gate use;
3. replay record;
4. rollback path;
5. audit log.

---

## 6. Profile promotion policy

Profile promotion requires:

1. profile candidate record;
2. evidence lineage;
3. model witness lineage;
4. fixture pack;
5. replay trace set;
6. retention metrics with baselines;
7. bridge preservation report;
8. normalizer stability report;
9. migration plan if semantic behavior changes;
10. rollback plan;
11. privacy review where source data is involved;
12. L5 decision record.

---

## 7. Policy decision schema

```yaml
PolicyDecision:
  policy_decision_id: string
  target_ref: string
  target_kind: evidence | witness | profile | bridge | normalizer | migration | model_gate | source
  input_status: string
  decision: allow | audit_only | restrict | sandbox | degrade | bypass | reject | rollback | human_review
  runtime_mode: normal | restricted | sandbox | audit_only | degraded | family_bypass | transport_bypass | lookup_bypass | profile_bypass | full_bypass
  reasons: []
  required_followup: []
  rollback_ref: string | null
  policy_snapshot_id: string
```

---

## 8. Non-claims

L5 policy approval does not prove mathematical truth or external-domain truth. It grants runtime permission under declared constraints.


---

## 9. Learning mode

> **Status tag:** normative

Draft 2 adds a separate policy dimension for the auto-profile learning pipeline.

Runtime mode controls how approved or candidate objects affect operation. Learning mode controls whether the system is allowed to run the profile-learning process at all.

Allowed learning modes:

| Learning mode | Meaning | Allowed actions |
|---|---|---|
| `blocked` | no auto-profile learning | store raw evidence only if permitted |
| `audit_only` | learning may observe and create candidate records | no model/tool expansion beyond approved audit path |
| `sandbox` | learning may invoke approved models and generate candidate profiles in isolation | sandbox fixtures, no runtime authority |
| `active` | learning may continuously propose profiles under policy | still requires promotion before authority |

### 9.1 Learning policy schema

```yaml
LearningPolicy:
  learning_policy_id: string
  learning_mode: blocked | audit_only | sandbox | active
  allowed_source_types: []
  allowed_model_ids: []
  allowed_node_roles: []
  max_privacy_class: public | internal | restricted | sensitive
  outbound_model_calls_allowed: true | false
  search_expansion_allowed: true | false
  social_feed_expansion_allowed: true | false
  profile_candidate_creation_allowed: true | false
  sandbox_runtime_allowed: true | false
  requires_human_review: true | false
```

### 9.2 Learning-mode enforcement

If `learning_mode: blocked`, the system must not create new candidate profiles.

If `learning_mode: audit_only`, the system may create evidence bundles, model witnesses, candidate witnesses, and candidate profiles, but it must not allow those outputs to gate runtime models or modify lookup authority.

If `learning_mode: sandbox`, the system may run isolated learning experiments and sandbox gates.

If `learning_mode: active`, the system may continuously create and test profile candidates, but promotion still requires the Profile Synthesis Registry and L5 policy approval.

### 9.3 Policy decision extension

`PolicyDecision` records must include:

```yaml
learning_mode: blocked | audit_only | sandbox | active | not_applicable
```

when the target relates to auto-profile learning.


---

## 10. Decision action policy

> **Status tag:** normative

Draft 3 adds policy handling for internal decisions and action candidates.

Every action candidate must receive a policy decision before execution.

Action classes and default policy:

| Action class | Default mode | Notes |
|---|---|---|
| `query_memory` | restricted | allowed if privacy and runtime mode permit |
| `search` | sandbox or restricted | query and result ingestion must be logged |
| `call_model` | restricted | must satisfy privacy and model routing policy |
| `update_profile` | sandbox | promotion still requires registry/policy |
| `update_lookup` | restricted or audit_only | depends on canonicality |
| `recommend` | restricted | user-facing recommendations need source scope |
| `create_message` | blocked | external communication requires explicit approval |
| `external_api_call` | blocked | external side effects require explicit approval |
| `promote_profile` | blocked by default | requires promotion request and L5 approval |
| `demote_profile` | restricted | must update dependencies |
| `no_action` | allowed | decision-critical no-action should be logged |

### 10.1 External side-effect boundary

External side effects include:

1. posting online;
2. sending a message;
3. writing to an external file;
4. making a purchase;
5. modifying a third-party system;
6. calling a public API with side effects;
7. publishing a claim;
8. deleting or altering evidence.

External side effects require explicit policy permission.

---

## 11. Self-evidence and self-model policy

> **Status tag:** normative

Chronological self-evidence and self-model snapshots require policy controls.

A self-model policy must declare:

```yaml
SelfModelPolicy:
  self_model_policy_id: string
  allowed_stream_ids: []
  excluded_stream_ids: []
  max_privacy_class: public | internal | restricted | sensitive
  allowed_derived_witnesses: []
  allowed_runtime_modes: []
  allowed_action_classes: []
  outbound_use_allowed: true | false
  model_training_allowed: true | false
  profile_learning_allowed: true | false
  deletion_propagation_required: true
```

A self-model must not be used for external action unless the policy explicitly permits external use.

---

## 12. Oracle-risk and diversity policy

> **Status tag:** normative

When model outputs support a profile, claim, translation, action, or gate, L5 may require a model diversity set.

Minimum policy fields:

```yaml
ModelDiversityPolicy:
  model_diversity_policy_id: string
  required_for:
    - profile_promotion
    - claim_support
    - action_execution
    - translation
    - glyphic_reading
    - source_reliability
  minimum_model_count: integer
  minimum_independence_class: low | medium | high | policy_specific
  require_falsifier: true | false
  homogeneous_agreement_action: allow | down_weight | audit_only | reject
  shared_failure_action: preserve_uncertainty | require_more_evidence | reject | human_review
```

A policy may permit one model for low-risk audit-only tasks. A policy should require diversity for promotion, external action, and high-authority decisions.

---

## 13. High-speed loop policy

> **Status tag:** normative

High-speed memory/replay loops must declare:

1. loop profile;
2. source streams;
3. memory classes;
4. model calls allowed;
5. runtime mode;
6. learning mode;
7. replay requirement;
8. invalidation policy;
9. allowed actions.

A high-speed loop running many times per second may support internal reasoning, but it must not bypass policy when creating, promoting, or executing actions.
