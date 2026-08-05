# Evidence Language Conformance Suite v1.0

## Required tests

1. Atomic claim schema validation.
2. Compound `And` formation with compatible scopes.
3. Compound claim rejection with incompatible scopes.
4. Modus ponens emits proposal InferenceWitness.
5. Modus ponens cannot promote theorem without proof witness.
6. Temporal propagation requires replay extension witness.
7. `audit_only` repetition cannot become authoritative.
8. Delegation cannot exceed delegator scope.
9. Deep-time replay package fails without assumption manifest.
10. Verification grammar execution is deterministic.
11. Computational evidence cannot collapse into theorem.
12. Self-trained cannot collapse into authoritative.
13. Null, empty, zero, absence remain distinct after serialization.

## Completion-candidate executable fixture binding

The prose cases in this suite are now bound to the fixture set in `refs/fixtures/draft5_2_evidence_language/` and the machine-readable vector file `executable/tests/draft5_2_conformance_vectors.json`.

Minimum executable gates:

1. All valid fixture JSON files must pass their referenced schemas.
2. `invalid_theorem_without_proof.fixture.json` must fail validation or runtime policy.
3. A deep-time replay request without all `required_assumptions` satisfied must fail with `replay_assumption_violation` or an equivalent denial.
4. A conjecture-to-theorem transition without proof witness references must fail.
5. A pragmatic force marker above delegated scope must be denied or escalated.
