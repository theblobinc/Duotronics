# Duotronic Internal Decision and Planning Contract v1.0

**Status:** Research specification draft  
**Version:** internal-decision-planning-contract@v1.0  
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
