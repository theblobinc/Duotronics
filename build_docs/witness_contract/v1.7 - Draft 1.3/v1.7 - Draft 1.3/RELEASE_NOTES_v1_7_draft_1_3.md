# Release Notes - v1.7 Draft 1.3

Draft 1.3 is a schema-SQL-runtime consistency pass over Draft 1.2. It does not attempt a broad new theory expansion.

## Closed fixes

- Added missing SQL persistence columns for required Draft 1.2 schema fields.
- Aligned SQL enums with Bayesian update methods, calibration scoring rules, and knot invariant families.
- Added schema-to-SQL persistence registry and validator enforcement.
- Fixed the Reidemeister/Markov SQL guard test so it exercises the intended CHECK constraint.
- Added SQL round-trip validation for every valid v1.7 Bayesian/knot fixture.
- Updated stale active contract and Lean comments from Draft 1.1 language to Draft 1.3.
- Expanded the TLA Bayesian/knot module from object-separation constants to record-level replay and authority-path invariants.
- Added structured OpenAPI validation/error/lookup/replay responses.
- Added negative fixtures for every typed knot diagram encoding and every Bayesian model family compatibility rule.

## Still not frozen

Strict Lake and strict TLC results remain environment/toolchain blockers until recorded by the target release environment.
