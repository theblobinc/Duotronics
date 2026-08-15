# Formal Models and Proof Status Profile

**Status:** Research specification draft  
**Version:** formal-models-proof-status@v1.0  
**Document kind:** Markdown specification  
**Primary purpose:** Document the TLA+ and Lean 4 proof artifacts and their promotion status.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

Draft 3 now includes formal models as first-class artifacts, but the corpus must distinguish between:

- a formal specification file;
- a theorem statement;
- a proof sketch;
- a checker-verified proof;
- a production-enforced invariant.

## 2. TLA+ profile

The TLA+ task delegation and policy core model covers:

- tasks;
- delegation depth;
- policy decisions;
- audit log;
- default-deny behavior;
- safety properties;
- liveness properties.

TLA+ promotion status requires a model-checker witness:

```yaml
TLAModelCheckWitness:
  spec_file: string
  config_file: string
  constants:
    MaxDelegationDepth: integer
    MaxTasks: integer
  checker: TLC
  checker_version: string
  result: passed | failed | inconclusive
  trace_ref: string
  timestamp: string
```

Without this witness, the TLA+ file is a specification artifact but not a checked proof artifact.

## 3. Lean 4 profile

Lean artifacts must classify each theorem:

```yaml
LeanTheoremStatus:
  theorem_name: string
  status: proved | sorry_stub | sketch | failed
  dependencies:
    - string
  checker_version: string
  file_hash: string
  proof_log_ref: string
```

A theorem containing `sorry` is not canonically proved. It remains useful as a proof obligation.

## 4. Current proof status categories

| Category | Meaning |
|---|---|
| Complete proof | checker accepts without stubs |
| Stub with strategy | theorem statement exists but is incomplete |
| Roadmap item | not yet formalized |
| Runtime invariant | implemented in code but not formally proved |
| Production invariant | implemented, tested, and formally or operationally witnessed |

## 5. Required bridge to runtime

Formal models must map to runtime controls:

| Formal concept | Runtime counterpart |
|---|---|
| Task | claim/proof/replay/interpreter operation |
| Policy decision | `PolicyDecision` or MCP policy result |
| Delegation depth | task chain depth / recursion bound |
| Audit log | append-only audit witness chain |
| Default deny | policy engine deny by default |
| Completed immutable | completed record cannot be mutated, only superseded |

## 6. Non-overclaim rule

The corpus must never convert a formal-model file into a proof claim merely because the file exists. Proof status requires checker evidence.
