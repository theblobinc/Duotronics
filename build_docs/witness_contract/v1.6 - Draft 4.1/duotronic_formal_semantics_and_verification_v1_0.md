# Duotronic Formal Semantics and Verification Profile v1.0

**Status:** Draft 2 normative planning profile  
**Purpose:** Define how Duotronic core objects, witnesses, policy decisions, and mathematical-status transitions will be formalized in proof assistants and model checkers.

---

## 1. Scope

This profile covers formal models for:

1. `CanonicalMathObject`;
2. `ProofWitness`;
3. `ComputationWitness`;
4. `InterpreterRunWitness`;
5. `PolicyDecision`;
6. `HumanReviewDecision`;
7. `CanonicalWitnessFact`;
8. `MathStatusTransition`;
9. `CorpusMigrationWitness`;
10. SRNN task/witness queue state;
11. DBP v2 envelopes;
12. MCP tool-call witnesses.

The profile does not require that all mathematics inside the corpus be machine-proved. It requires that authority transitions and safety rules be machine-modelable.

---

## 2. Core safety properties

The formal model must include these invariants.

### 2.1 No conjecture-to-theorem without proof authority

```text
For every MathStatusTransition where:
  old_status in {conjecture, open_problem, computational_evidence, heuristic}
  new_status = theorem

There must exist:
  ProofWitness with checker_status = accepted
  PolicyDecision with action = approve_theorem_promotion
  HumanReviewDecision if profile requires human review
```

### 2.2 Computational evidence is not proof

```text
InterpreterRunWitness.certificate_kind in {
  none,
  numeric_interval,
  randomized_test,
  bounded_exhaustive_search,
  symbolic_simplification,
  proof_checker_acceptance
}

Only proof_checker_acceptance may be used as direct proof authority.
All other certificate kinds are evidence authority only.
```

### 2.3 MCP mutation tools never bypass policy

```text
Any MCPToolCallWitness where risk in {repo_write, service_mutation, external_action}
must have:
  principal_id
  required_scope
  policy_decision_id
  audit_record_id
  redacted_args_hash
```

### 2.4 Canonical identity is stable under replay

If replay inputs are unchanged, canonical identity hashes must remain unchanged.

### 2.5 Absence/zero invalidity separation

No formal reduction rule may collapse:

```text
absence
zero
unknown
invalid
origin
transport_inactive
external_zero
```

into a single native state.

---

## 3. Lean / Coq object model

The first formalization should define:

```text
inductive MathStatus
| raw_claim
| conjecture
| theorem
| refuted
| computational_evidence
| heuristic
| analogy
| deprecated

structure CanonicalMathObject :=
  (object_id : String)
  (family_id : String)
  (schema_version : String)
  (payload_hash : String)
  (status : MathStatus)

structure ProofWitness :=
  (proof_id : String)
  (target_object_id : String)
  (checker : String)
  (checker_version : String)
  (accepted : Bool)
  (proof_hash : String)

structure PolicyDecision :=
  (decision_id : String)
  (action : String)
  (approved : Bool)
  (scope : String)
```

The first theorem to prove:

```text
theorem no_unproved_theorem_promotion :
  forall transition,
  transition.new_status = theorem ->
  exists proof, proof.accepted = true /\ proof.target_object_id = transition.object_id
```

The exact proof-assistant syntax may differ. The semantic requirement is binding.

---

## 4. TLA+ state-machine model

A TLA+ model should cover:

1. evidence intake;
2. candidate witness creation;
3. canonicalization;
4. policy decision;
5. human review;
6. promotion;
7. replay;
8. MCP tool-call audit;
9. SRNN task dispatch;
10. rollback.

Minimum safety properties:

```text
NoUnsafePromotion
NoUnauditedMutation
NoDirectRawEvidenceAuthority
ReplayIdentityStable
ExternalActionRequiresPolicy
```

Minimum liveness properties:

```text
CandidateEventuallyReviewedOrExpired
QueuedTaskEventuallyDoneFailedOrCanceled
PolicyReviewEventuallyResolvedOrTimedOut
```

---

## 5. Verification artifacts

A conformant implementation may attach verification artifacts as:

```yaml
FormalVerificationArtifact:
  artifact_id: string
  formal_system: lean | coq | tla_plus | alloy | other
  source_ref: string
  source_hash: string
  checked_by: string
  checked_at: string
  result: accepted | rejected | timeout | not_run
  covers:
    - invariant_id
  trusted_as:
    - spec_support
    - implementation_support
    - theorem_promotion_support
```

---

## 6. Promotion requirements

A v1.6 implementation can claim `formal_semantics_supported` only if it includes:

1. at least one proof-assistant model of core status transitions;
2. at least one model-checker specification for policy/task state machines;
3. CI job records for verification checks;
4. fixture demonstrating blocked conjecture-to-theorem promotion without accepted proof;
5. replay logs for canonical identity stability.
