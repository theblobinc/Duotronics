# Lean Build README v1.0

Draft 5.2.1 adds a buildable Lean/Lake package at the corpus root.

Build command:

```bash
lake build
```

Portable validator:

```bash
python3 executable/formal/run_lean_build.py --mode advisory --json
```

Strict CI gate:

```bash
python3 executable/formal/run_lean_build.py --mode strict --json
```

The advisory mode passes static proof-surface checks when Lake is unavailable. Strict mode fails if Lake is not installed. Theorem promotion requires a strict `passed` Lean compiler witness; advisory mode is not sufficient for promotion.
