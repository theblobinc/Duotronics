# Duotronic Proof Interchange and Certificate Profile v1.0

**Status:** Draft 2 normative profile  
**Purpose:** Define how proof artifacts, proof-checker runs, computational certificates, and interpreter outputs become witnessable evidence.

---

## 1. Object families

### 1.1 ProofArtifact

```yaml
ProofArtifact:
  proof_artifact_id: string
  target_object_id: string
  proof_language: lean | coq | isabelle | agda | metamath | dedukti | itp_interchange | other
  source_ref: string
  source_hash: string
  dependency_hashes: []
  declared_theorem_statement_hash: string
  created_by: string
```

### 1.2 ProofCheckerRunWitness

```yaml
ProofCheckerRunWitness:
  run_id: string
  proof_artifact_id: string
  checker_id: string
  checker_version: string
  checker_container_hash: string
  result: accepted | rejected | timeout | unsupported | error
  stdout_hash: string
  stderr_hash: string
  replay_identity_ref: string
  policy_decision_id: string
```

### 1.3 ComputationalCertificate

```yaml
ComputationalCertificate:
  certificate_id: string
  computation_witness_id: string
  certificate_kind: none | interval | exact_symbolic | bounded_exhaustive | randomized | proof_checker_acceptance
  checker_id: string | null
  certificate_hash: string
  trusted_for: evidence | proof | diagnostic
```

---

## 2. Proof status rule

Only these paths may support theorem promotion:

```text
ProofArtifact
-> ProofCheckerRunWitness(result=accepted)
-> PolicyDecision(action=approve_theorem_promotion)
-> MathStatusTransition(new_status=theorem)
```

Computation-only certificates may support:

```text
computational_evidence
bounded_evidence
counterexample_candidate
diagnostic_support
```

They must not support direct theorem promotion.

---

## 3. Interchange formats

The corpus should support these proof interchange targets:

1. native Lean proof files;
2. native Coq proof files;
3. Dedukti-style interchange records;
4. theorem-prover problem records where applicable;
5. proof-carrying computation certificates;
6. proof checker logs and replay packages.

Draft 2 does not declare a single mandatory external interchange standard. It requires the proof profile to be explicit and replayable.

---

## 4. Cryptographic identity

Proof and certificate identity must use:

1. SHA3-256 or a stronger approved hash;
2. canonical byte serialization before hashing;
3. optional JWS signature for authority-bearing proof bundles;
4. dependency hash closure for reproducibility.

---

## 5. Re-check rule

High-value proof claims should be re-checkable on a second checker instance or independently built container.

A `ProofWitness` can be marked:

```text
single_checker_accepted
independently_rechecked
cross_system_translated
human_reviewed
deprecated_checker
```

---

## 6. Proof-carrying computation

An interpreter run may attach a certificate.

Example:

```yaml
InterpreterRunWitness:
  runtime: julia
  code_hash: sha3-256:...
  result_hash: sha3-256:...
  certificate:
    certificate_kind: interval
    certificate_hash: sha3-256:...
    trusted_for: evidence
```

Example theorem-grade run:

```yaml
InterpreterRunWitness:
  runtime: lean
  proof_checker_result: accepted
  certificate:
    certificate_kind: proof_checker_acceptance
    trusted_for: proof
```

---

## 7. Human review boundary

Human reviewers may confirm that a proof artifact is relevant to a claim. They do not replace proof checker acceptance unless the claim is explicitly a human-reviewed informal theorem.

Informal proof status must remain distinct:

```text
informal_proof_claim
peer_reviewed_informal
machine_checked_theorem
```
