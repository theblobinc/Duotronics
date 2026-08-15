# Semiotics of Replay Contract v1.0

**Draft:** v1.6 Draft 5.2  
**Pillar:** Semiotics of Replay  
**Status:** Normative contract

## 1. Purpose

This contract defines how a claim can be understood and verified by a future reader who may lack the original language, culture, tools, or assumptions.

## 2. Replay Assumption Manifest

Every deep-time-intended claim must include a `ReplayAssumptionManifest` with:

- semantic assumptions,
- cultural assumptions,
- metrological assumptions,
- computational assumptions,
- schema assumptions,
- policy assumptions,
- failure-mode assumptions.

The manifest is versioned, hashed, and witnessed.

## 3. Verification Grammar

Every deep-time replay package must include a deterministic grammar describing how to verify the claim from package contents alone.

The grammar must not depend on external prose.

## 4. Replay signs

A ReplaySign may be:

- iconic, such as a diagram,
- indexical, such as a hash pointer or timestamp,
- structural, such as a DBP envelope shape,
- procedural, such as a minimal verification algorithm.

Deep-time packages should include at least one indexical sign and one structural sign. Civilizational-survival packages should include iconic signs.

## 5. Replay package classes

```text
legacy_replay_package
standard_replay_package
self_describing_replay_package
deep_time_replay_package
```

## 6. Conformance

A replay package is Draft 5.2-conformant when a verifier can decide its verification status using only the package, the assumption manifest, the verification grammar, and the DBP envelope structure.

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
