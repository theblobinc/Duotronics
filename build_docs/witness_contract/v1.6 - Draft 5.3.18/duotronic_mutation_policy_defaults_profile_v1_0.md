# Mutation Policy Defaults Profile

**Status:** Research specification draft  
**Version:** mutation-policy-defaults@v1.0  
**Document kind:** Markdown specification  
**Primary purpose:** Document the default-deny automated mutation policy now present in SRNN source.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

Automated code mutation is itself a witness event. This profile defines how mutation policy must be represented in v1.6 Draft 3.

## 2. Mutation levels

```yaml
MutationLevel:
  DENY:
    meaning: no automated mutation is accepted
  REVIEW_REQUIRED:
    meaning: mutation may be proposed but requires human or L5 approval
  AUTO_ALLOWED:
    meaning: mutation may apply under bounded policy and tests
  GENERATED:
    meaning: generated artifacts may be regenerated from source-of-truth definitions
```

## 3. Mutation types

```yaml
MutationType:
  - refactor
  - bugfix
  - feature
  - docs
  - deps
  - codegen
  - security
```

## 4. Default path policy

| Path class | Default level | Notes |
|---|---|---|
| Oracle witness core | DENY | core trust anchor |
| Math canon identity | DENY or REVIEW_REQUIRED | changes affect canonical identity |
| DBP envelope identity | DENY or REVIEW_REQUIRED | changes affect serialization identity |
| Policy engine | REVIEW_REQUIRED | policy can alter authority |
| Replay package logic | REVIEW_REQUIRED | replay identity and validation risk |
| Proof validation | REVIEW_REQUIRED | false proof promotion risk |
| Interpreter helpers | AUTO_ALLOWED with sandbox tests | runtime risk bounded by sandbox |
| Math query helpers | AUTO_ALLOWED with fixture tests | retrieval does not equal truth |
| SDK generated clients | GENERATED | safe only from canonical OpenAPI |
| OpenAPI export | GENERATED | output artifact, not policy source |

## 5. Required mutation witness

Every automated mutation proposal must produce:

```yaml
MutationRequestWitness:
  path: string
  mutation_type: MutationType
  requested_by: principal
  description: string
  proposed_change_hash: string
  policy_match:
    path_pattern: string
    level: MutationLevel
    reason: string
    required_reviewer: string | null
  decision: deny | review_required | auto_allowed | generated
  tests_required:
    - string
  replay_package_required: boolean
  audit_ref: string
```

## 6. Promotion rule

A code mutation may be promoted to implementation-authoritative only when:

1. the mutation policy permits it;
2. required tests pass;
3. the changed files have replay or fixture coverage;
4. no DENY path is changed;
5. review-required paths have review evidence;
6. generated files trace back to a canonical generator and source input.
