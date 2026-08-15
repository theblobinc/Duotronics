# Phase 3 Validation Suite Profile

**Status:** Research specification draft  
**Version:** phase3-validation-suite@v1.0  
**Document kind:** Markdown specification  
**Primary purpose:** Document the Draft 2 phase 3 validation suite and how Draft 3 should use it.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

The source now contains a unified Draft 2 Phase 3 validation suite. Draft 3 uses that suite as a readiness signal for SDK, formal model, threat model, mutation policy, proof interchange, OpenAPI, and core conformance layers.

## 2. Test categories

The unified suite includes these categories:

1. SDK structure validation.
2. Formal model validation.
3. Threat model validation.
4. Mutation policy tests.
5. Proof interchange tests.
6. OpenAPI export tests.
7. Duotronic core conformance tests.
8. Python SDK tests.

## 3. Required report

Every run should emit:

```yaml
DuotronicPhase3ValidationReport:
  run_id: string
  repo_head: string
  working_tree_clean: boolean
  categories:
    - name: string
      status: passed | failed | skipped
      message: string
      log_ref: string
  passed: integer
  failed: integer
  timestamp: string
```

## 4. Corpus rule

Draft 3 must not state "production-ready" solely because the phase-3 suite exists. Production readiness requires:

- all phase-3 categories pass;
- security closure items pass;
- working tree is clean;
- generated SDK/OpenAPI artifacts are regenerated from canonical sources;
- formal proof stubs are not represented as proven theorems.

## 5. Current risk note

The current source review observed the phase-3 suite file as modified in the working tree. That is a release risk until reviewed.
