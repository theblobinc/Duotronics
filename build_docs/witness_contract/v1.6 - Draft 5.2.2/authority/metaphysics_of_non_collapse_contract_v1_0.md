# Metaphysics of Non-Collapse Contract v1.0

**Draft:** v1.6 Draft 5.2  
**Pillar:** Metaphysics of Non-Collapse  
**Status:** Normative contract

## 1. Purpose

This contract forbids the silent merging of distinct epistemic, semantic, or authority states.

## 2. Primitive distinctions

The canonical primitive category enum contains 21 forever-distinct categories:

`zero`, `absence`, `unknown`, `invalid`, `empty`, `null`, `computational_evidence`, `theorem`, `conjectural`, `self_trained`, `authoritative`, `audit_only`, `active`, `observation`, `proof`, `explanation`, `fact`, `policy_approval`, `human_attestation`, `synthetic_witness`, `activation_witness`.

The following representative pairs are explicitly forbidden collapse pairs:

| A | B |
|---|---|
| zero | absence |
| unknown | invalid |
| empty | null |
| computational_evidence | theorem |
| conjectural | theorem |
| self_trained | authoritative |
| audit_only | active |
| observation | proof |
| explanation | fact |
| policy_approval | human_attestation |
| synthetic_witness | activation_witness |

## 3. Axioms

### Axiom 1 — Non-Collapse

No inference, schema, policy, replay, training run, or migration may map two distinct primitive categories to the same authority state without an explicit witness that justifies the transition.

### Axiom 2 — Evidence Gap

Any trust-state transition requires evidence external to the state itself. Repetition of a state cannot promote it.

### Axiom 3 — Layered Verification

Promotion requires independent syntactic, pragmatic, semiotic, and non-collapse checks.

## 4. Enforcement layers

Non-collapse is enforced by:

- JSON schema constraints,
- Python validators,
- policy engine `NonCollapseConstraint`,
- replay verifier checks,
- formal model stubs,
- conformance tests,
- release gate review.

## 5. NLA special rule

A self-trained or internally trained NLA adapter can become a candidate, shadow, audit, or release candidate only through the Draft 5.1/Draft 5.2 gate path. It cannot become authoritative by training success alone.

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
