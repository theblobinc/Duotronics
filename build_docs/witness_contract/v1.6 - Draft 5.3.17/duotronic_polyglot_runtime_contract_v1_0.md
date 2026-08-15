# Duotronic Polyglot Runtime Contract v1.0

**Status:** normative draft  
**Version:** polyglot-runtime@v1.0

---

## 1. Purpose

The v1.6 runtime supports Python, Julia, and Lisp as first-class implementation surfaces for mathematical witnesses and interpreter execution.

The runtime is language-aware but authority-agnostic: a language may compute, parse, reason, or orchestrate only within its declared role.

---

## 2. Language roles

| Runtime | v1.6 role | Authority boundary |
|---|---|---|
| Python | orchestration, parsing, API, glue, fallback interpreter, artifact extraction | transitional runtime and fallback; not automatically final control plane |
| Julia | numerical kernels, linear algebra, graph algorithms, high-performance math, certified numeric wrappers | not commit authority; emits computation witnesses |
| Lisp / SBCL | symbolic reasoning, rule expansion, ontology queries, rewrite systems, interpreter strategies | symbolic specialist; cannot promote proofs alone |
| Rust | candidate future control plane | not required in this draft but kept as target-compatible |
| PHP | legacy integration shell only | no final backend authority |
| Inform 7 | narrative interaction surface only | no backend authority |

---

## 3. Bridge protocol

All cross-runtime calls use a witness-bearing bridge.

```yaml
PolyglotCallWitness:
  call_id: string
  source_runtime: string
  target_runtime: string
  method: string
  input_hash: string
  input_schema_id: string
  output_hash: string | null
  output_schema_id: string | null
  stdout_ref: string | null
  stderr_ref: string | null
  latency_ms: number | null
  success: true | false
  error_ref: string | null
  replay_identity_ref: string
```

---

## 4. Fallback rule

Any Julia or Lisp path used for runtime service must declare one of:

```text
no_fallback_required
python_fallback_required
safe_bypass_allowed
audit_only_if_backend_missing
```

The SRNN meta-object pattern uses Python fallback for the Lisp/Jula cooperative selector.

---

## 5. Julia kernel profile

```yaml
JuliaKernelProfile:
  profile_id: string
  package_project_ref: string
  sysimage_ref: string | null
  entrypoints: []
  numerical_tolerance_policy: string
  deterministic_seed_policy: string
  gpu_policy: disabled | optional | required
  fallback_policy: string
```

Recommended v1.6 kernels:

1. symbolic/numeric similarity matrix;
2. spectral graph algorithms;
3. recurrence graph community detection;
4. L-function coefficient computations where safe;
5. certified interval arithmetic wrappers;
6. linear algebra for automorphic data experiments.

---

## 6. Lisp symbolic profile

```yaml
LispSymbolicProfile:
  profile_id: string
  implementation: sbcl | ccl | ecl | racket | custom
  package_ref: string
  exported_functions: []
  hot_reload_allowed: true | false
  macro_expansion_audit: required | optional | forbidden
  rule_engine_ref: string
  fallback_policy: string
```

Recommended v1.6 uses:

1. symbolic query expansion;
2. theorem dependency rewriting;
3. ontology and domain registry navigation;
4. proof-sketch structural checks;
5. Langlands object graph pattern matching;
6. interpreter strategy definitions.

---

## 7. Python profile

```yaml
PythonRuntimeProfile:
  profile_id: string
  python_version: string
  environment_lock_ref: string
  allowed_packages: []
  denied_packages: []
  sandbox_profile_ref: string
  entrypoints: []
  fallback_for: []
```

Python remains the required fallback runtime in this draft.

---

## 8. Storage and authority

The runtime must distinguish:

1. canonical transactional store;
2. vector/semantic index;
3. ephemeral cache;
4. legacy compatibility store.

No language runtime becomes authority because it can write to a database. Writes require a policy and witness path.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 2 corpus alongside all v1.5 Draft 2 carry-forward files.
