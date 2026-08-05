# Syntax of Evidence Contract v1.0

**Draft:** v1.6 Draft 5.2  
**Pillar:** Syntax of Evidence  
**Status:** Normative contract

## 1. Purpose

This contract defines the formal grammar used to express evidence claims in the Duotronic witness corpus. It turns witness facts, math claims, proof witnesses, NLA activation witnesses, replay results, and policy decisions into well-formed claim objects that can be composed, inferred from, replayed, and audited.

## 2. Claim classes

### AtomicClaim

An atomic claim is a single irreducible claim with:

- `claim_id`
- `claim_type`
- `canonical_identity_hash`
- `evidence_bundle_refs`
- `authority_scope`
- `runtime_mode`
- `policy_decision_id`
- `replay_identity_ref`
- `non_collapse_class`

Examples include `CanonicalWitnessFact`, `MathClaim`, `ProofWitness`, `ReplayVerificationWitness`, and `NaturalLanguageActivationWitness`.

### CompoundClaim

A compound claim is a claim built from other claims using a defined operator:

```text
And(A, B)
Or(A, B)
Implies(A, B)
TemporalSince(A, TimeWindow)
```

A compound claim is never automatically stronger than its premises. It is a new witnessed structure that requires a composition policy decision.

### InferenceClaim

An inference claim records that a conclusion was proposed from premises under a named evidence-preserving rule. It is not proof unless the conclusion's target status explicitly requires and receives proof authority.

## 3. Formation rules

A claim is well-formed only if:

1. every referenced claim has a stable identity hash,
2. authority scopes are compatible or explicitly bridged by policy,
3. runtime modes are compatible or explicitly downgraded,
4. every operator has a `composition_policy_id`,
5. every transition has a witnessed `policy_decision_id`,
6. evidence bundles are unioned without loss,
7. no primitive non-collapse distinction is merged.

## 4. Valid operators

| Operator | Meaning | Special requirement |
|---|---|---|
| `and` | both premises are claimed jointly | compatible authority scopes |
| `or` | at least one premise is claimed | disjunctive evidence must remain explicit |
| `implies` | premise supports conclusion under rule | separate inference witness required |
| `temporal_since` | claim persisted over a time window | replay extension witness required |

## 5. Inference rules

Valid inference rules include:

- conjunction elimination,
- modus ponens as proposal,
- temporal propagation with replay evidence,
- identity-preserving replay extension,
- authority-preserving composition.

No inference may promote computation to theorem or self-trained model to authority.

## 6. Required witness types

- `CompoundClaimWitness`
- `InferenceWitness`
- `TemporalScopeWitness`
- `CompositionPolicy`
- `ClaimStatusTransition`

## 7. Runtime obligations

The runtime must reject:

- incompatible scopes without policy bridge,
- inference without witness,
- theorem promotion without proof checker witness,
- authority promotion from repetition,
- unknown/invalid collapse,
- null/empty/zero collapse,
- self-trained/authoritative collapse.

## 8. Acceptance

A Syntax of Evidence implementation is conformant when every composed or inferred claim creates a new witness, records all premises, preserves replay identity, and passes non-collapse validation.

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
