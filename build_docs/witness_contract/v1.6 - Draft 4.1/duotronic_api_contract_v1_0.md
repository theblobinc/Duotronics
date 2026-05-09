# Duotronic API Contract v1.0

**Status:** normative implementation contract  
**Version:** api-contract@v1.0  
**Document kind:** HTTP/API and request-response specification  
**Primary purpose:** Define the transition API surface for v1.6 prototypes, including witness submission, mathematical object registration, interpreter runs, policy decisions, task/oracle operations, replay packages, and admin review.

## 1. Scope

The transition API is the Python/FastAPI-compatible surface used while the final control-plane language remains under decision. The API is language-neutral at the contract level. A later Rust control-plane may implement the same endpoints or expose DBP-compatible equivalents.

The API must never bypass:

```text
request authentication
-> DBP v2 envelope validation
-> schema validation
-> policy preflight where required
-> durable canonical transaction
-> replay record
```

## 2. Required transport rules

1. All non-localhost deployments must use TLS.
2. Every mutating request must include a principal identity.
3. Every mutating request must produce an audit record.
4. Every accepted canonical object must be wrapped or referenced by a DBP v2 envelope.
5. Idempotent writes must accept `Idempotency-Key` and must not duplicate canonical objects.
6. `X-Duotronic-Policy-Snapshot` may pin a policy snapshot for replay; runtime use may reject stale snapshots.

## 3. Common headers

```yaml
Authorization: Bearer <token>
X-Duotronic-Principal: <principal_id>
X-Duotronic-Node: <node_id>
X-Duotronic-Policy-Snapshot: <policy_snapshot_id optional>
Idempotency-Key: <uuid optional for writes>
Content-Type: application/json
```

## 4. Common response envelope

```yaml
ApiResponse:
  ok: boolean
  request_id: string
  envelope_id: string | null
  policy_decision_id: string | null
  replay_identity_ref: string | null
  result: object | null
  error:
    code: string
    message: string
    details: object
```

## 5. Health and metadata endpoints

```text
GET /v1/health
GET /v1/version
GET /v1/capabilities
GET /v1/schemas
GET /v1/policy/snapshots/current
```

`/v1/capabilities` must report enabled runtimes, bridge health, database health, queue health, proof-checker availability, and whether external network access is enabled for interpreter sandboxes.

## 6. DBP envelope endpoints

```text
POST /v1/dbp/envelopes/validate
POST /v1/dbp/envelopes
GET  /v1/dbp/envelopes/{envelope_id}
GET  /v1/dbp/envelopes/by-hash/{payload_hash}
```

Validation may run without persistence. Persistence requires policy evaluation when the object affects canonical identity, witness authority, interpreter execution, or external action.

## 7. Evidence and witness endpoints

```text
POST /v1/evidence
POST /v1/witnesses/candidates
POST /v1/witnesses/canonicalize
GET  /v1/witnesses/{witness_id}
GET  /v1/witnesses/by-object/{canonical_object_id}
POST /v1/witnesses/contradictions
POST /v1/witnesses/human-review/request
POST /v1/witnesses/human-review/decision
```

`POST /v1/witnesses/canonicalize` must select a registered normalizer, produce a canonical identity hash, and return a policy decision. It may return `audit_only` or `rejected` without error if the witness is well-formed but not authoritative.

## 8. Mathematical canon endpoints

```text
POST /v1/math/objects
GET  /v1/math/objects/{canonical_math_object_id}
POST /v1/math/claims
GET  /v1/math/claims/{claim_id}
POST /v1/math/claims/{claim_id}/evidence
POST /v1/math/claims/{claim_id}/status-transition
POST /v1/math/domains/register
GET  /v1/math/domains
POST /v1/math/query
```

A mathematical claim status transition must state whether the target status is one of:

```text
raw_claim
normalized_claim
computational_evidence
heuristic_evidence
conjecture
conditional_theorem
proof_submitted
machine_checked_theorem
human_reviewed_theorem
disputed
retracted
```

Open conjectures may be represented canonically; they must not be promoted to theorem status without a proof witness accepted by policy.

## 9. Langlands endpoints

```text
POST /v1/math/langlands/objects
POST /v1/math/langlands/bridges
POST /v1/math/langlands/local-factor-checks
POST /v1/math/langlands/functorial-transfer-candidates
GET  /v1/math/langlands/objects/{object_id}
```

Langlands bridge submissions must declare source object, target object, preservation claims, local/global factor data, bad-place handling, status, and whether the assertion is theorem-backed, conjectural, or computational evidence only.

## 10. Interpreter and proof endpoints

```text
POST /v1/interpreter/runs
GET  /v1/interpreter/runs/{run_id}
POST /v1/interpreter/runs/{run_id}/cancel
POST /v1/proof/checker-runs
GET  /v1/proof/checker-runs/{checker_run_id}
```

`POST /v1/interpreter/runs` request:

```yaml
InterpreterRunRequest:
  language: python | julia | lisp | sage | magma | pari_gp | lean | coq | custom
  runtime_profile_id: string
  code_ref: string | null
  code_inline: string | null
  input_artifact_refs: []
  network_policy: disabled | allowlisted | unrestricted_policy_exception
  filesystem_policy: scratch_only | read_only_inputs | declared_outputs
  cpu_limit_ms: integer
  memory_limit_mb: integer
  wall_clock_limit_ms: integer
  expected_outputs: []
  authority_scope: computation | proof_check | data_transform | diagnostic
```

Interpreter output is a witness. It is not proof unless it is a proof-checker run under an approved proof authority profile.

## 11. Policy endpoints

```text
POST /v1/policy/evaluate
POST /v1/policy/preflight
POST /v1/policy/override/request
POST /v1/policy/override/decision
GET  /v1/policy/decisions/{policy_decision_id}
```

Policy decisions must be durable, replayable, and explainable. Runtime may not silently continue after a policy veto.

## 12. SRNN task and oracle endpoints

```text
POST /v1/srnn/tasks
GET  /v1/srnn/tasks/{task_id}
POST /v1/srnn/oracle-jobs
GET  /v1/srnn/oracle-jobs/{job_id}
POST /v1/srnn/oracle-results
GET  /v1/srnn/witness-events/{witness_event_id}
POST /v1/srnn/mcp/query
```

Oracle job success must persist `witness_event_id` if an oracle result emits one. A job without a witness event may succeed as a computation, but it cannot be treated as canonical witness authority.

## 13. Replay endpoints

```text
POST /v1/replay/packages
GET  /v1/replay/packages/{replay_package_id}
POST /v1/replay/packages/{replay_package_id}/verify
POST /v1/replay/packages/{replay_package_id}/rerun
```

Replay verification must pin schema versions, normalizer versions, policy snapshot, runtime versions, input hashes, and expected output hashes.

## 14. Admin endpoints

```text
GET  /v1/admin/review-queue
POST /v1/admin/review-queue/{review_id}/decision
GET  /v1/admin/contradictions
GET  /v1/admin/promotions
POST /v1/admin/promotions/{promotion_id}/decision
GET  /v1/admin/audit-log
```

Admin endpoints require separate admin principal scope and must never be reachable by unauthenticated internal service calls.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
