# Release Notes - v1.6 Draft 5.2.1

Draft 5.2.1 is an additive upgrade to Draft 5.2. It does not weaken existing witness, replay, policy, non-collapse, or logical observer kernel gates.

Primary addition: Lean proof authority integration.

Highlights:

- Adds a buildable Lean/Lake project.
- Adds `check_proof()` to the kernel syscall set.
- Adds `LeanCompilerWitness`, `ProofWitness`, and `TheoremPromotionGate` objects.
- Strengthens theorem/proof promotion: proof references alone are no longer enough; Lean compiler witness and promotion gate references are required.
- Adds SQL, OpenAPI, fixtures, validator checks, and manifest closure for the new layer.
