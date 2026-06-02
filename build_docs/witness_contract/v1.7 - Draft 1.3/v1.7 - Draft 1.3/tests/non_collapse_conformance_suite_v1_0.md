# Non-Collapse Conformance Suite v1.0

## Forbidden transitions

- zero -> absence
- unknown -> invalid
- empty -> null
- computational_evidence -> theorem
- conjectural -> theorem
- self_trained -> authoritative
- audit_only -> active
- explanation -> fact

Every attempted transition must fail unless an explicitly allowed external witness exists. Some transitions, such as computation to theorem without proof, are never allowed.

## Completion-candidate executable fixture binding

The prose cases in this suite are now bound to the fixture set in `refs/fixtures/draft5_2_evidence_language/` and the machine-readable vector file `executable/tests/draft5_2_conformance_vectors.json`.

Minimum executable gates:

1. All valid fixture JSON files must pass their referenced schemas.
2. `invalid_theorem_without_proof.fixture.json` must fail validation or runtime policy.
3. A deep-time replay request without all `required_assumptions` satisfied must fail with `replay_assumption_violation` or an equivalent denial.
4. A conjecture-to-theorem transition without proof witness references must fail.
5. A pragmatic force marker above delegated scope must be denied or escalated.
