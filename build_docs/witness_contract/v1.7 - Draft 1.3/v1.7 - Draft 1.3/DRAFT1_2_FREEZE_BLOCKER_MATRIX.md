# Draft 1.2 Freeze Blocker Matrix

| Blocker | Status | Required closure evidence |
|---|---|---|
| Strict Lake build | Open | `lake build` pass with no `sorry`, `admit`, or unapproved axioms outside approved axiom surfaces. |
| Strict TLC run | Open | Strict `run_tla_model_check.py --mode strict` pass with TLC available for all manifest modules, including `BayesianKnotFirstClassPromotion`. |
| Human authority review | Open | Human review record approving Bayesian decision-support boundaries and knot-equivalence authority semantics. |
| Runtime conformance | Open | Executable service tests for SQL persistence, OpenAPI request validation, kernel syscall dispatch, and replay validators. |
| Bayesian approximate update policy | Open | Runtime policy for Monte Carlo seeds, error bounds, replay manifests, and stochastic-tool quarantine. |
| Knot mathematical authority | Open | Domain-specific review of invariant completeness and equivalence authority path semantics. |

Draft 1.2 is complete as a corpus hardening candidate but must not be frozen until all blockers are closed with attached evidence.
