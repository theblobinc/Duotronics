# Duotronic Internal Decision and Planning Contract v1.2

**Status:** Research specification draft  
**Version:** internal-decision-planning-contract@v1.2  
**Supersedes:** internal-decision-planning-contract@v1.1  
**Supersedes:** internal-decision-planning-contract@v1.0  
**Document kind:** Normative internal decision, planner, action-witness, and bounded-rationality contract plus reference schemas  
**Primary purpose:** Define how Duotronic systems may use canonical witness facts, lookup memory, recurrent state, search, social evidence, model outputs, and learned profiles to inform their own internal decisions and actions without bypassing witness validation, policy gating, replay, or rollback.

---

## 1. Scope

This contract applies when the Duotronic system uses evidence to make decisions for itself, another agent, a workflow, a project, or a runtime process.

Examples:

1. choose which model to call;
2. choose which source to search;
3. decide whether to expand a profile-learning run;
4. choose likely next action from chronological history;
5. decide whether a claim needs contradiction search;
6. decide whether to add an item to a playlist or recommendation set;
7. decide whether to post, message, call an API, update memory, or trigger a workflow;
8. decide whether to promote, demote, or quarantine a profile candidate;
9. decide whether to run a high-speed loop or replay;
10. decide which witness should gate another model.

The contract explicitly supports systems that do not primarily output to humans. A Duotronic system may use canonical witness facts internally for rational action selection.

---

## 2. Central rule

> **Status tag:** normative

An action is a witness candidate before it is an action.

Any planner, model, rule engine, reinforcement learner, heuristic, or augmented-intelligence module that proposes an action must emit an `ActionCandidateWitness`.

The action may execute only after policy gating.

---

## 3. Bounded rationality model

Duotronic decision-making is bounded rationality, not omniscience.

The system attempts to act rationally by:

1. collecting evidence;
2. extracting witnesses;
3. canonicalizing what can be canonicalized;
4. preserving uncertainty;
5. comparing model outputs;
6. detecting contradictions;
7. querying memory;
8. searching when permitted;
9. evaluating candidate actions;
10. applying policy constraints;
11. recording action outcomes;
12. updating future evidence.

The system does not guarantee perfect rationality, truth, optimality, or alignment.

---

## 4. Decision context

```yaml
DecisionContext:
  decision_context_id: string
  objective_ref: string
  actor_ref: string
  decision_scope: internal_only | user_assistive | workflow | external_action | profile_governance | model_routing | custom
  input_canonical_fact_refs: []
  input_audit_fact_refs: []
  input_self_model_snapshot_refs: []
  input_lookup_query_refs: []
  input_model_witness_refs: []
  uncertainty_refs: []
  contradiction_refs: []
  privacy_class: public | internal | restricted | sensitive | mixed
  runtime_mode: audit_only | sandbox | restricted | normal
  learning_mode: blocked | audit_only | sandbox | active | not_applicable
```

---

## 5. Action candidate witness

```yaml
ActionCandidateWitness:
  action_candidate_id: string
  decision_context_id: string
  proposed_by:
    kind: model | rule | planner | human | policy | hybrid
    ref: string
  action_kind: search | ingest | query_memory | call_model | update_profile | update_lookup | recommend | create_message | external_api_call | promote_profile | demote_profile | no_action | custom
  action_payload_ref: string | null
  expected_effect: string
  supporting_witness_refs: []
  contradicting_witness_refs: []
  uncertainty_refs: []
  risk_assessment_ref: string | null
  reversibility: reversible | partially_reversible | irreversible | unknown
  required_policy_gate: string
  status: raw | candidate | policy_approved | executed | rejected | rolled_back
```

---

## 6. Policy-gated action execution

```yaml
ActionExecutionRecord:
  action_execution_id: string
  action_candidate_id: string
  policy_decision_id: string
  execution_node_id: string
  executed_at: string
  execution_status: success | failed | partial | blocked | rolled_back
  output_evidence_bundle_ids: []
  resulting_witness_ids: []
  rollback_ref: string | null
```

Actions that affect external systems require stricter policy than internal reasoning actions.

Default action policy:

| Action class | Default mode |
|---|---|
| memory query | restricted or normal if canonical |
| search expansion | sandbox or restricted |
| source ingestion | restricted with privacy checks |
| model call | restricted with privacy/model policy |
| profile update | sandbox until promoted |
| lookup update | restricted if canonical, audit-only if candidate |
| external post/message/API | blocked unless explicit L5 approval |
| profile promotion/demotion | requires L5 policy |
| no-action | always allowed but should be logged if decision-critical |

---

## 7. Internal self-informing loop

A Duotronic system may run an internal decision loop:

```text
canonical facts
-> lookup memory
-> recurrent state
-> decision context
-> action candidates
-> policy gate
-> action execution
-> new evidence
-> witness extraction
-> memory update
```

The loop may be high-speed if it uses a declared HighSpeedLoopProfile. Promotion or irreversible action still requires the appropriate replay and policy path.

---

## 8. Search as an action

Search is not just data retrieval. Search is an action that changes what evidence is available.

A search action candidate must declare:

1. query profile;
2. search engine/source;
3. privacy class;
4. purpose;
5. expected evidence type;
6. stopping condition;
7. policy limit;
8. whether results can feed auto-profile learning.

---

## 9. Planner modules

A planner module may be:

1. an LLM;
2. a symbolic planner;
3. a reinforcement-learning agent;
4. a rules engine;
5. a heuristic scheduler;
6. a DW-SSM gate;
7. a hybrid model;
8. a human-in-the-loop workflow.

Every planner output that matters must be wrapped as an action candidate witness.

Planner authority comes from policy, not from model confidence.

---

## 10. Truth and rationality fields

Decision systems may use truth-related fields, but must preserve scope.

```yaml
DecisionSupportFact:
  fact_ref: string
  authority_scope: representation_identity | lookup_fact | claim_support | profile_support | action_support | custom
  truth_status: not_applicable | unknown | supported | contradicted | disputed | policy_accepted
  decision_relevance: required | helpful | weak | contradictory | unknown
```

A `policy_accepted` fact is not necessarily externally true. It is accepted for the declared decision scope.

---

## 11. Outcome learning

After an action executes, the result becomes new evidence.

```yaml
ActionOutcomeWitness:
  action_outcome_witness_id: string
  action_execution_id: string
  expected_effect: string
  observed_effect: string
  success_metric_refs: []
  unexpected_effects: []
  source_evidence_ids: []
  policy_followup: none | audit | rollback | demote | human_review
```

Outcome witnesses may update future planner behavior, but only through the same profile, memory, retention, and policy layers.

---

## 12. Non-claims

This contract does not solve alignment or guarantee rationality. It gives Duotronic systems a governed way to use evidence, memory, models, and policy to make internal decisions.


---

## 13. Planner-triggered profile learning

> **Status tag:** normative

A planner may propose starting an auto-profile learning run, but it may not directly create a promoted profile.

Planner-triggered profile learning is an action.

The planner must emit an `ActionCandidateWitness` with:

```yaml
action_kind: start_profile_learning
```

and a payload shaped as:

```yaml
ProfileLearningActionPayload:
  profile_learning_action_payload_id: string
  target_unknown_pattern_refs: []
  source_evidence_ids: []
  source_stream_ids: []
  proposed_profile_kind: symbolic_numeric | natural_language_semantic | glyphic_visual | graph | matrix | tensor | geometry | search_source | social_source | transport_adapter | custom | unknown
  learning_objective: string
  requested_learning_mode: audit_only | sandbox | active
  allowed_models: []
  allowed_sources: []
  max_privacy_class: public | internal | restricted | sensitive
  fixture_generation_requested: true | false
  promotion_requested: false
```

`promotion_requested` must default to `false`. A planner may request a learning run. It may not request direct promotion without a separate Profile Promotion Request.

### 13.1 Policy gate for learning actions

A `start_profile_learning` action requires:

1. learning mode permits the run;
2. source privacy permits the run;
3. allowed models are declared;
4. expected profile kind is declared or explicitly unknown;
5. output defaults to `candidate_profile`;
6. sandbox or audit-only mode unless L5 allows active learning.

---

## 14. Policy change proposals

> **Status tag:** normative

A planner may propose a policy change, but policy change is self-modification and requires a separate approval workflow.

A planner must not change L5 policy directly.

```yaml
PolicyChangeProposal:
  policy_change_proposal_id: string
  proposed_by:
    kind: planner | human | policy | model | hybrid
    ref: string
  target_policy_ref: string
  proposed_change_kind: learning_mode_change | runtime_mode_change | allowed_model_change | source_permission_change | action_permission_change | threshold_change | rollback_rule_change | custom
  prior_policy_snapshot_id: string
  proposed_policy_snapshot_ref: string
  rationale: string
  supporting_witness_refs: []
  contradicting_witness_refs: []
  risk_assessment_ref: string
  reversibility: reversible | partially_reversible | irreversible | unknown
  requested_effective_time: string | null
  required_approval: human | l5_policy | multi_party | external_governance | custom
  status: candidate | approved | rejected | withdrawn | superseded
```

### 14.1 Policy change authority

Default rules:

1. A planner may propose a policy change.
2. A planner may not approve its own policy change.
3. Increasing authority requires stricter approval than decreasing authority.
4. Changes from `audit_only` to `sandbox`, `sandbox` to `active`, or `restricted` to `normal` require L5 approval.
5. External side-effect permissions require explicit L5 approval and, where configured, human review.
6. Policy changes must create a new policy snapshot.

### 14.2 Conservative fallback

If a policy change proposal conflicts with existing policy, the current stricter policy remains active until approval.

---

## 15. Action conflict resolution

> **Status tag:** normative

Multiple planners, models, policies, or humans may propose contradictory actions for the same decision context.

Action conflicts must be explicit.

```yaml
ActionConflictRecord:
  action_conflict_id: string
  decision_context_id: string
  action_candidate_ids: []
  conflict_type: execute_vs_block | mutually_exclusive_actions | priority_conflict | privacy_conflict | resource_conflict | policy_conflict | timing_conflict | custom
  conflict_detected_by: planner | policy | adjudicator | human | system
  default_resolution: most_restrictive_policy_wins | preserve_uncertainty | human_review | policy_review | no_action
  resolved_action_candidate_id: string | null
  policy_decision_id: string
  status: unresolved | resolved | escalated | rejected
```

### 15.1 Default conflict rule

If actions conflict and no approved resolution exists:

```text
most restrictive policy wins
```

If the system cannot determine the most restrictive safe path, it must select `no_action`, `audit_only`, or `human_review`.

### 15.2 Examples

| Conflict | Default action |
|---|---|
| one planner says search, another says do not search due to privacy | privacy block or human review |
| one planner says promote profile, another says keep sandbox | keep sandbox |
| one planner says call external API, another flags irreversible side effect | block or human review |
| two searches exceed resource budget | throttle or policy review |
| planner proposes policy increase, L5 does not approve | reject proposal |

---

## 16. LikelyActionWitness relationship

> **Status tag:** normative

A `LikelyActionWitness` predicts or estimates action tendency.

An `ActionCandidateWitness` proposes an executable or evaluable action.

They are related but not interchangeable.

A likely action may support a decision context:

```yaml
DecisionContext:
  input_canonical_fact_refs:
    - likely-action-fact-ref
```

A likely action may support an action candidate:

```yaml
ActionCandidateWitness:
  supporting_witness_refs:
    - likely-action-witness-id
```

But the conversion requires a separate proposal event.

```yaml
LikelyActionToActionLink:
  link_id: string
  likely_action_witness_id: string
  action_candidate_id: string
  conversion_author: planner | policy | human | hybrid
  conversion_reason: string
  policy_decision_id: string
```

The absence of a link means the likely action remains a prediction only.

---

## 17. Planner output classes

> **Status tag:** reference

A planner may emit:

1. `ActionCandidateWitness`;
2. `PolicyChangeProposal`;
3. `ProfileLearningActionPayload`;
4. `ActionConflictRecord`;
5. `DecisionSupportFact`;
6. `no_action` decision;
7. request for more evidence;
8. request for human review.

All planner outputs that influence runtime must be witness-wrapped and policy-gated.


---

## 18. Human review integration

> **Status tag:** normative

When an action conflict, policy change proposal, external side effect, ambiguous actor scope, or purge-related decision routes to `human_review`, the planner must not continue as though a decision has been made.

The system must create a `HumanReviewRequest`.

A planner may include recommended options, but the reviewer decision must be recorded as `HumanReviewDecision`.

If human review expires, the default outcome is:

```text
no_action, reject, audit_only, or most_restrictive_policy
```

depending on the policy class.

### 18.1 Human review as decision input

A later decision context may include:

```yaml
input_human_review_decision_refs: []
```

Human decisions are evidence and policy inputs. They are not automatically semantic proof.

---

## 19. Lazy and deferred action replay

> **Status tag:** normative

A lazy action is an action candidate proposed at one time but executed later.

```yaml
LazyActionRecord:
  lazy_action_record_id: string
  action_candidate_id: string
  decision_context_id: string
  created_under_self_model_snapshot_id: string | null
  created_under_self_model_version: integer | null
  created_under_policy_snapshot_id: string
  defer_reason: scheduled | waiting_for_review | waiting_for_resource | waiting_for_evidence | custom
  expiry_time: string | null
  revalidation_required: true
  status: pending | expired | revalidated | executed | rejected | cancelled
```

If the self-model, policy, source evidence, or lookup memory changes before execution, the lazy action must be re-gated.

Default rule:

```text
stale lazy actions do not execute
```

They may be replayed audit-only if replay identity pins the old snapshot version and policy snapshot.

---

## 20. Replay with stale decision contexts

> **Status tag:** normative

An old decision context may be replayed for audit even if its self-model snapshot is stale.

Replay identity must record:

1. decision context ID;
2. self-model snapshot ID and version;
3. whether the snapshot was valid at original decision time;
4. current staleness/invalidation state;
5. policy snapshot at original decision time;
6. policy snapshot at replay time;
7. whether any evidence has been purged.

Allowed use:

| Replay condition | Allowed use |
|---|---|
| exact historical audit replay | audit_only |
| stale snapshot used to justify new action | blocked unless policy exception |
| purged evidence in replay | tombstone-only or blocked |
| lazy action after invalidation | revalidation required |
