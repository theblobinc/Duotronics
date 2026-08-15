# Draft 5.2.1 Local Validation Report

Generated: 2026-05-11T00:00:00Z

Checks executed in this environment:

```text
python3 executable/validators/validate_draft5_2_1_corpus.py
python3 executable/validators/validate_draft5_2_corpus.py
python3 executable/formal/run_lean_build.py --mode advisory --json
python3 executable/formal/run_tla_model_check.py
```

Observed results:

```text
Draft 5.2.1 corpus validation checks passed.
Lean advisory status: advisory_pass_lake_unavailable
TLA+ advisory status: advisory_pass_tlc_unavailable
```

Notes:

- Lake was not installed in the execution environment, so actual `lake build` could not be run here.
- The Lean runner performed static checks over executable Lean files and found no forbidden proof markers and no unapproved axiom declarations.
- Strict theorem promotion remains fail-closed: production promotion requires `run_lean_build.py --mode strict --json` to produce a strict `passed` Lean compiler witness.
