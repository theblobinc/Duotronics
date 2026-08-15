# Draft 5.2.2 Lean Proof Authority SQL Hardening Report

Status: completion candidate; additive to Draft 5.2.1; not frozen until strict CI/toolchain run.

## Closed issues

1. Documentation drift: `README.md` and `START_HERE.md` no longer describe the formal layer as TLA-only. They now state that Draft 5.2.2 includes TLA+ plus Lean/Lake proof authority.
2. SQL/schema mismatch: SQL persistence now requires Lean compiler witness refs and theorem promotion gates for theorem/proof_verified claims and transitions, matching the JSON schema layer.
3. Orphan theorem-promotion gates: allowed gates are now constrained by foreign keys and SQLite triggers tying them to passing Lean compiler witnesses, proved proof witnesses, matching prove transitions, and non-collapse transition ids.
4. Strict formal execution status: advisory validation remains portable. Strict Lean (`lake build`) and strict TLA+ (`run_tla_model_check.py --mode strict`) remain required in CI or another environment where Lake/TLC are installed before freeze.

## Persistence rule

No theorem/proof_verified persistence path may be committed by proof witness alone. A valid path now requires:

```text
ProofWitness
+ LeanCompilerWitness(result = passed)
+ TheoremPromotionGate(allowed = true)
+ ClaimStatusTransition(kind = prove)
+ NonCollapseTransition
+ PolicyDecision
```

Advisory or unavailable toolchain checks never authorize theorem promotion.
