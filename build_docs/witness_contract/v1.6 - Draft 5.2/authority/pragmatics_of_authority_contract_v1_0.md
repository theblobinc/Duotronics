# Pragmatics of Authority Contract v1.0

**Draft:** v1.6 Draft 5.2  
**Pillar:** Pragmatics of Authority  
**Status:** Normative contract

## 1. Purpose

This contract defines how the force of a statement is represented. Authority is not just a field on an object. It depends on who speaks, through which channel, to which audience, in which mode, and under what delegation.

## 2. Pragmatic context

Every authority-bearing statement must be able to declare:

- `principal_id`
- `authority_scope`
- `runtime_mode`
- `channel_authority`
- `intended_audience`
- `force_indicator`
- `minimum_interpretation_assumptions`
- `delegation_chain_ref`
- `replay_assumption_manifest_ref`

## 3. Force indicators

Allowed force indicators include:

```text
assert
propose
defer
veto
observe
replay_verify
delegate
revoke
audit_note
```

A force indicator is not inferred from content. It must be explicit.

## 4. Non-escalation

The following are forbidden:

- `audit_only` becoming authoritative by repetition,
- observer output becoming proof by policy approval,
- self-trained NLA becoming active without gate passage,
- delegated authority exceeding its scope,
- channel authority overriding proof constraints,
- absent audience declaration being treated as universal audience.

## 5. Delegation chains

An `AuthorityDelegationChain` must include:

- delegator,
- delegate,
- scope,
- force limits,
- temporal bounds,
- channel limits,
- policy decision ID,
- revocation state.

Delegation is itself a claim and must be witnessed.

## 6. Policy integration

The policy engine must evaluate `PragmaticConstraint` alongside ordinary allow/deny logic. Missing pragmatic context must fail closed for deep-time, release, theorem, active-model, or authoritative claims.

## 7. Runtime obligations

The runtime must preserve pragmatic context across DBP envelopes, replay packages, NLA release bundles, math claim promotions, and witness status transitions.

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
