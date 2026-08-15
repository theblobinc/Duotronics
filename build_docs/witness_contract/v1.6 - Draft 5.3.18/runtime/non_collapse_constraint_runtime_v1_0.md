# Non-Collapse Constraint Runtime Contract v1.0

**Draft:** v1.6 Draft 5.2

## Purpose

Defines a reusable runtime constraint that prevents forbidden state collapses.

## Runtime API

```python
check_non_collapse(source_state, target_state, context) -> NonCollapseDecision
```

## Required behavior

- fail closed on unknown state names,
- preserve primitive category distinctions,
- require external witness for trust-state transitions,
- emit audit event for every denial,
- never downgrade errors to warnings when authority is involved.

## Draft 5.2 completion-candidate hardening addendum

The completed corpus adds the missing operational detail required for implementation review. Active Draft 5.2 runtimes MUST preserve the following objects as first-class records and MUST NOT collapse them into prose-only metadata:

- `evidence_claim/v1`
- `composition_policy/v1`
- `compound_claim_witness/v1`
- `inference_witness/v1`
- `claim_status_transition/v1`
- `pragmatic_context/v1`
- `policy_decision_evidence_extension/v1`
- `authority_delegation_chain/v1`
- `non_collapse_state/v1`
- `non_collapse_transition/v1`
- `replay_assumption_manifest/v1`
- `replay_sign/v1`
- `verification_grammar/v1`
- `verification_result/v1`

A runtime that cannot emit the required witness object MUST deny, defer, or escalate the operation rather than silently promoting authority, truth status, replay status, model status, or proof status.
