# Authority Delegation Chain Contract v1.0

**Draft:** v1.6 Draft 5.2

## Purpose

Defines how scoped authority is delegated without allowing scope expansion, time-bound leakage, or force escalation.

## Required fields

```yaml
delegation_chain_id: string
delegator_principal_id: string
delegate_principal_id: string
scope: string
force_limit: string
runtime_mode_limit: string
valid_from: string
valid_until: string
channel_authority: string
policy_decision_id: string
revoked: boolean
```

## Rules

- delegation must be explicit,
- delegation cannot exceed delegator authority,
- delegation cannot convert proposal authority into assert authority,
- revocation must be replayable,
- expired delegation fails closed,
- delegated authority cannot bypass non-collapse constraints.

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
