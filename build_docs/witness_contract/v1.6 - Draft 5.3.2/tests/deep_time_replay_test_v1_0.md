# Deep-Time Replay Test v1.0

## Purpose

Verify that a claim can be evaluated using only the replay package, replay assumption manifest, verification grammar, and DBP envelope structure.

## Test outline

1. Build self-describing replay package.
2. Remove access to source documentation.
3. Load only package artifacts.
4. Execute verification grammar.
5. Confirm all required assumptions are present.
6. Verify hashes.
7. Produce pass/fail/inconclusive result.
8. Confirm missing assumption causes failure.

## Completion-candidate executable fixture binding

The prose cases in this suite are now bound to the fixture set in `refs/fixtures/draft5_2_evidence_language/` and the machine-readable vector file `executable/tests/draft5_2_conformance_vectors.json`.

Minimum executable gates:

1. All valid fixture JSON files must pass their referenced schemas.
2. `invalid_theorem_without_proof.fixture.json` must fail validation or runtime policy.
3. A deep-time replay request without all `required_assumptions` satisfied must fail with `replay_assumption_violation` or an equivalent denial.
4. A conjecture-to-theorem transition without proof witness references must fail.
5. A pragmatic force marker above delegated scope must be denied or escalated.
