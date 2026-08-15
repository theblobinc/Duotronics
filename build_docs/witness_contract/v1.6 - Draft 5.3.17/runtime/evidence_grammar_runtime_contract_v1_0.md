# Evidence Grammar Runtime Contract v1.0

**Draft:** v1.6 Draft 5.2

## Purpose

Defines runtime behavior for validating evidence-language expressions.

## Runtime responsibilities

- parse claim expressions,
- validate atomic claim references,
- validate compound operators,
- enforce authority scope compatibility,
- invoke policy decisions for composition,
- invoke non-collapse checks,
- emit `CompoundClaimWitness` or reject.

## Minimal grammar

```ebnf
claim      ::= atomic | compound
compound   ::= and | or | implies | temporal_since
and        ::= "And(" claim "," claim ")"
or         ::= "Or(" claim "," claim ")"
implies    ::= "Implies(" claim "," claim ")"
temporal_since ::= "TemporalSince(" claim "," time_window ")"
```

## Failure modes

- `claim_not_found`
- `scope_incompatible`
- `runtime_mode_incompatible`
- `missing_composition_policy`
- `non_collapse_violation`
- `evidence_bundle_union_failed`

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
