# Pragmatic Authority Conformance Suite v1.0

## Tests

- force indicator is preserved in policy decision.
- missing intended audience blocks deep-time claim.
- delegated authority cannot exceed scope.
- channel authority cannot override proof requirement.
- audit-only output cannot become assertive by repetition.
- NLA observer output cannot become fact by explanation alone.

## Completion-candidate executable fixture binding

The prose cases in this suite are now bound to the fixture set in `refs/fixtures/draft5_2_evidence_language/` and the machine-readable vector file `executable/tests/draft5_2_conformance_vectors.json`.

Minimum executable gates:

1. All valid fixture JSON files must pass their referenced schemas.
2. `invalid_theorem_without_proof.fixture.json` must fail validation or runtime policy.
3. A deep-time replay request without all `required_assumptions` satisfied must fail with `replay_assumption_violation` or an equivalent denial.
4. A conjecture-to-theorem transition without proof witness references must fail.
5. A pragmatic force marker above delegated scope must be denied or escalated.
