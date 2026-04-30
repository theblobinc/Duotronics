# Duotronic Code Interpreter Plan v1.0

**Status:** reference draft with normative safety requirements  
**Version:** code-interpreter-plan@v1.0

---

## 1. Purpose

The v1.6 code interpreter executes Python, Julia, and Lisp snippets as witness-bearing computations.

It is intended for:

1. mathematical experiments;
2. canonical object construction;
3. L-function and representation data computations;
4. graph and recurrence analysis;
5. proof-support calculations;
6. fixture generation;
7. SRNN diagnostic replay.

---

## 2. Interpreter pipeline

```text
InterpreterRequest
-> policy preflight
-> language profile selection
-> environment lock resolution
-> sandbox creation
-> code execution
-> output capture
-> object/result parsing
-> computation witness creation
-> replay package creation
-> promotion or rejection gate
```

---

## 3. Interpreter request

```yaml
InterpreterRequest:
  request_id: string
  requested_by: string
  language: python | julia | lisp
  purpose: math_experiment | proof_support | data_transform | fixture_generation | srnn_diagnostic | custom
  code_ref: string
  input_object_refs: []
  allowed_runtime_seconds: integer
  allowed_memory_mb: integer
  network_policy: disabled | allowlisted | unrestricted_forbidden
  filesystem_policy: read_only | temp_write | artifact_write | forbidden
  package_policy_ref: string
  expected_output_schema: string | null
```

---

## 4. Execution record

```yaml
InterpreterExecutionRecord:
  execution_id: string
  request_id: string
  language: string
  runtime_version: string
  environment_hash: string
  package_lock_hash: string
  sandbox_id: string
  started_at: string
  finished_at: string
  exit_code: integer
  stdout_hash: string
  stderr_hash: string
  result_payload_hash: string | null
  result_object_refs: []
  deterministic_replay: true | false
  replay_instructions_ref: string
  trust_status: raw_execution | reproducible | verified_computation | rejected
```

---

## 5. Safety rules

1. Network is disabled by default.
2. Filesystem writes go only to a temporary artifact directory unless policy grants more.
3. Long-running computation must be killed by timeout.
4. Package installation requires an allowlisted lock file.
5. Any generated theorem-like claim starts as `computational_evidence`.
6. Interpreter output cannot update canonical math objects without a normalizer and policy gate.
7. Interpreter output cannot execute external actions.
8. Cross-runtime calls must produce `PolyglotCallWitness` records.
9. Randomized computations must record seed, RNG, and sample count.
10. Numeric computations must declare precision and error policy.

---

## 6. Math-specific execution profiles

### 6.1 Python math profile

Allowed use:

- parsing;
- orchestration;
- exact arithmetic with standard libraries;
- data loading;
- symbolic prototypes;
- fallback execution.

### 6.2 Julia math profile

Allowed use:

- high-performance numeric linear algebra;
- graph algorithms;
- spectral methods;
- certified numeric routines where package profile supports it;
- L-function coefficient experiments.

### 6.3 Lisp math profile

Allowed use:

- symbolic rewriting;
- rule-based proof sketch analysis;
- object graph traversal;
- notation expansion;
- query language and strategy definitions.

---

## 7. Langlands interpreter use

Langlands computations are allowed for:

1. local factor normalization checks;
2. Euler product coefficient experiments;
3. conductor and root-number metadata checks;
4. modular form coefficient comparison;
5. graphing correspondences between object records;
6. fixture generation.

They may not promote functoriality to theorem without proof witness.

---

## 8. Minimal implementation milestone

1. Python sandbox prototype.
2. Julia subprocess or HTTP kernel with locked environment.
3. SBCL JSON-RPC symbolic service.
4. Unified `InterpreterExecutionRecord` store.
5. Replay bundle writer.
6. Artifact hash and source hash tracker.
7. Policy gate and timeout enforcement.
8. First fixture pack: zeta/Dirichlet/Dedekind/Langlands object construction.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
