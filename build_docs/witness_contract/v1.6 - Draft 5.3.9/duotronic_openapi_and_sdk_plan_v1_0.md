# Duotronic OpenAPI and SDK Plan v1.0

**Status:** Draft 2 implementation plan

## 1. OpenAPI generation

The API contract must be compiled into an OpenAPI 3.1 document.

Required tags:

1. `math-objects`
2. `witnesses`
3. `proofs`
4. `interpreter-runs`
5. `policy-decisions`
6. `human-review`
7. `mcp-observations`
8. `replay`
9. `admin`

## 2. Client SDKs

Generated clients should include:

1. Python;
2. TypeScript/JavaScript;
3. optional Julia;
4. optional Common Lisp wrapper for symbolic workflows.

## 3. SDK safety

SDKs must expose mutation methods separately from read-only methods.

High-risk methods must require explicit naming such as:

```text
approve_high_risk_action()
execute_mutating_mcp_tool()
promote_claim_to_theorem()
```

No SDK should hide policy gating.

## 4. Problem details

Errors must follow this shape:

```yaml
ProblemDetail:
  type: string
  title: string
  status: integer
  detail: string
  instance: string
  error_code: string
  witness_ref: string | null
  policy_decision_id: string | null
```
