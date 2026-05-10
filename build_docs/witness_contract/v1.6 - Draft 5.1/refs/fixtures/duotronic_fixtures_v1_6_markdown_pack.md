# Duotronic Fixtures v1.6 Markdown Pack

**Status:** reference fixture pack  
**Version:** fixtures-v1.6@v1.0

## 1. DBP envelope fixture

```yaml
valid_envelope_minimal:
  dbp_version: "2.0"
  envelope_id: "env-fixture-001"
  object_kind: "CanonicalMathObject"
  schema:
    schema_id: "duotronic.math.object"
    schema_version: "1.0"
    schema_hash: "sha256:fixture"
  identity:
    canonical_identity_hash: "sha256:fixture-identity"
    normalizer_id: "fixture-normalizer"
    normalizer_version: "1.0"
    serializer_id: "canonical-json"
    serializer_version: "1.0"
  payload:
    media_type: "application/json"
    inline: {"object_kind":"integer","value":1}
    artifact_ref: null
    payload_hash: "sha256:fixture-payload"
    payload_size: 32
```

## 2. Math claim fixture

```yaml
math_claim_conjecture:
  claim_id: "claim-fixture-langlands-001"
  claim_kind: "correspondence_claim"
  domain_ids: ["langlands"]
  current_status: "conjecture"
  normalized_statement_json:
    text: "A functorial transfer candidate is represented but not proven."
```

## 3. Interpreter run fixture

```yaml
interpreter_run_python_success:
  language: "python"
  code_inline: "print(2 + 2)"
  expected_stdout: "4"
  authority_scope: "computation"
  expected_status: "succeeded"
```

## 4. Policy deny fixture

```yaml
policy_deny_theorem_without_proof:
  action_kind: "promote_claim"
  from_status: "conjecture"
  to_status: "machine_checked_theorem"
  proof_witness_ids: []
  expected_decision: "deny"
```

## 5. SRNN oracle fixture

```yaml
oracle_job_with_witness_event:
  job_id: "job-fixture-001"
  loop_id: "chrono-main"
  node_id: "main"
  oracle_id: "vision-yolo-main"
  result_payload:
    witness_event_id: "evt-fixture-001"
  expected_persisted_witness_event_id: "evt-fixture-001"
```

## 6. MCP endpoint fixture

```yaml
mcp_query_health_success:
  method: "srnn_health"
  response_status: "success"
  authority_scope: "diagnostics"
  expected_truth_status: "not_applicable"
```

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
