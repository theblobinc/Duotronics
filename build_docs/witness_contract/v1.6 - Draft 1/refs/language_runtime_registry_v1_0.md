# Language Runtime Registry v1.0

**Status:** reference draft  
**Version:** language-runtime-registry@v1.0

---

## 1. Registered runtime profiles

### Python

```yaml
runtime_id: python.default.v1
role: orchestration_and_fallback
entrypoints:
  - math artifact parser
  - interpreter sandbox prototype
  - SRNN witness ingestion
  - API layer
fallback_for:
  - julia kernels
  - lisp symbolic routines
```

### Julia

```yaml
runtime_id: julia.math-kernel.v1
role: numerical_math_kernel
entrypoints:
  - similarity matrix
  - graph algorithms
  - spectral analysis
  - numerical experiments
  - L-function coefficient experiments
bridge: JSON-RPC or HTTP subprocess
fallback: python_fallback_required
```

### Lisp / SBCL

```yaml
runtime_id: sbcl.symbolic.v1
role: symbolic_reasoner
entrypoints:
  - rule expansion
  - ontology query
  - symbolic rewrite
  - proof-sketch structural check
  - Langlands graph pattern query
bridge: JSON-RPC subprocess
fallback: python_fallback_required
```

### Rust

```yaml
runtime_id: rust.control-plane-candidate.v1
role: future_control_plane_candidate
status: candidate
notes: retained for compatibility with SRNN final architecture direction
```

### PHP

```yaml
runtime_id: php.legacy-shell.v1
role: legacy_frontend_proxy_only
status: deprecated_for_backend_authority
```

### Inform 7

```yaml
runtime_id: inform7.narrative-surface.v1
role: user_facing_narrative_surface_only
status: reference
```

---

## 2. Runtime conformance

A runtime must provide:

1. version identity;
2. dependency lock;
3. call witness schema;
4. timeout behavior;
5. error serialization;
6. replay behavior;
7. fallback or bypass policy;
8. policy gate for external actions;
9. artifact hash handling;
10. stdout/stderr capture.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
