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
