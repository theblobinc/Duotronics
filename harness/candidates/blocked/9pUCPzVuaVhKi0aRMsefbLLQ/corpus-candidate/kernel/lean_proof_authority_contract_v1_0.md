# Lean Proof Authority Contract v1.0

**Status:** Draft 5.2.1 additive proof-authority layer.  
**Applies to:** Duotronic Evidence Language OS and Logical Observer Kernel.  
**Purpose:** Make Lean/Lake compilation a first-class proof authority for theorem and proof-verified claim promotion.

## 1. Boundary

Lean does not authorize runtime action, release, or policy by itself. Lean only establishes that a named formal theorem was accepted by the configured Lean compiler under a pinned toolchain, with no prohibited proof placeholders and no unapproved axiom dependencies.

The kernel may use Lean output only through typed witnesses:

```text
LeanCompilerWitness
ProofWitness
TheoremPromotionGate
```

## 2. Toolchain

Draft 5.2.1 pins the default toolchain in `lean-toolchain`:

```text
leanprover/lean4:v4.29.1
```

The project is a Lake package with `lakefile.lean`, `Duotronic.lean`, and modules under `Duotronic/`.

## 3. Proof-checking syscall

The kernel adds:

```text
check_proof()
```

Required witnesses:

```text
LeanCompilerWitness
ProofWitness
```

Execution steps:

```text
LOAD_LEAN_PROJECT
VERIFY_LEAN_TOOLCHAIN
RUN_LAKE_BUILD
SCAN_FOR_SORRY_OR_ADMIT
EXTRACT_THEOREM_STATUS
EMIT_LEAN_COMPILER_WITNESS
EMIT_PROOF_WITNESS
BIND_THEOREM_PROMOTION_GATE
```

## 4. Theorem promotion gate

A claim MUST NOT enter `theorem` or `proof_verified` status unless all of the following exist and agree:

1. `ProofWitness` references the target claim and theorem artifact.
2. `LeanCompilerWitness.result = passed`.
3. The Lean source tree hash matches the promoted claim binding.
4. The theorem status is `proved`.
5. No `sorry` or `admit` marker is present in executable Lean code.
6. No unapproved axiom dependency exists.
7. `TheoremPromotionGate.allowed = true`.
8. `ClaimStatusTransition` references the proof witness, Lean compiler witness, non-collapse transition, and promotion gate.

## 5. Fail-closed rule

A missing Lean toolchain may produce an advisory witness for development, but it cannot authorize theorem promotion. Production theorem promotion requires a strict `passed` Lean compiler witness.

## 6. Non-collapse relationship

Policy approval is not proof. Human attestation is not proof. Computational evidence is not theoremhood. A Lean compiler witness is not a runtime policy decision. The theorem promotion gate binds these distinct authorities without collapsing them.


## Draft 5.2.2 persistence hardening addendum

Draft 5.2.2 makes the persistence layer fail closed with the schema layer. The following are no longer runtime-only expectations; they are SQL-level requirements for SQLite-compatible stores:

1. `srnn_evidence_claims` rows whose `claim_status` or `epistemic_status` is `theorem` or `proof_verified` MUST include non-empty `proof_witness_refs_json`, non-empty `lean_compiler_witness_refs_json`, a `status_transition_id`, and a `theorem_promotion_gate_id`.
2. `srnn_claim_status_transitions` targeting `theorem` or `proof_verified` MUST be `transition_kind = prove` and MUST include non-empty proof witness refs, non-empty Lean compiler witness refs, and a theorem promotion gate id.
3. `srnn_inference_witnesses` whose output or conclusion status is `theorem` or `proof_verified` MUST include a proof witness ref, Lean compiler witness ref, and theorem promotion gate id.
4. `srnn_theorem_promotion_gates.allowed = 1` MUST be backed by an existing passing `srnn_lean_compiler_witnesses` row, an existing proved `srnn_proof_witnesses` row bound to the same claim/compiler pair, and an existing matching prove transition.
5. Advisory Lean results (`advisory_pass_lake_unavailable`) are explicitly non-promotional. Only `result = passed` may support an allowed theorem promotion gate.
