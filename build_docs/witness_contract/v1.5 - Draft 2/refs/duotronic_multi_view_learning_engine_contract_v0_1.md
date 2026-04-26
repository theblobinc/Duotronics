# Duotronic Multi-View Learning Engine Contract v0.1

**Status:** Research profile specification  
**Version:** multi-view-learning-engine@v0.1  
**Document kind:** Concept-routing and explanation contract  
**Primary purpose:** Define an additive learning layer that preserves multiple valid views of one concept, routes a learner to the most appropriate view, and keeps formal guardrails visible instead of flattening distinct explanations into one vague answer.

---

## 1. Scope

This profile adds a multi-view learning engine to v1.5 Draft 2.

It covers:

1. canonical concept profiles;
2. multiple valid view profiles for one concept;
3. explicit bridges between views;
4. misconception detection as contradiction pressure between views;
5. learner-intent routing;
6. explanation contracts with formal guardrails;
7. diagnostics explaining why a view was selected.

It does not replace the canonical SRNN chain, witness extraction, ranking, merge, synthesis, or policy shield. It sits above them as a pedagogy and concept-routing layer.

---

## 2. Core rule

A learning answer must not silently collapse valid views.

The required flow is:

```text
learner question
-> ConceptProfile lookup
-> LearnerIntent estimate
-> ViewProfile selection
-> bridge declaration if multiple views are combined
-> misconception check
-> ExplanationContract
-> diagnostics
```

If an answer combines views, the bridge must be declared. If a view is selected for intuition, at least one formal guardrail or operation must also be returned.

---

## 3. Object classes

The profile adds these schema classes:

1. `ConceptProfile`;
2. `ViewProfile`;
3. `ViewBridge`;
4. `LearnerIntent`;
5. `MisconceptionRecord`;
6. `ExplanationContract`;
7. `LearningSessionState`;
8. `LearningRouteDiagnostics`.

---

## 4. Required semantic distinctions

The engine must preserve Duotronic semantic discipline:

| State | Meaning |
|---|---|
| `structurally_absent` | no learner answer or no view material exists |
| `present_unknown` | a view exists but confidence is insufficient |
| `present_conditional` | a view is valid only under declared conditions |
| `present_realized` | a view is selected and supported for the learner intent |
| `present_error` | a learner assertion contradicts the concept guardrails |
| `rejected_untrusted` | source or bridge failed validation |

An unselected valid view is not an invalid view. A missing learner answer is not a wrong answer. A misconception is not the same as low confidence.

---

## 5. Tensor baseline profile

The first required profile is `tensor` because it demonstrates the many-valid-views problem.

Required views:

1. `tensor_computational_array`;
2. `tensor_functional_multilinear`;
3. `tensor_geometric_transform`;
4. `tensor_abstract_product`.

The engine must know that the computational-array view is valid for programming and machine-learning work, but incomplete as a total mathematical definition unless basis and transformation guardrails are declared.

---

## 6. Explanation contract

Every explanation route must return:

1. `concept_id`;
2. `selected_view_id`;
3. `selection_reason`;
4. `formal_guardrails`;
5. `operations` the learner can perform;
6. `bridge_ids` if views are combined or if another view is nearby;
7. `misconception_warnings`;
8. `diagnostics`.

An intuition-only answer is nonconforming.

---

## 7. Harness mirror

The v1.5 Draft 2 harness mirrors the executable subset with:

```text
op: route_learning_view
```

The initial fixture proves that a tensor programming question routes to the computational-array view while preserving the formal basis/transformation guardrail and naming a bridge to the geometric view.
