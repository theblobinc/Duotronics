# Duotronic Policy Engine Specification v1.0

**Status:** normative implementation contract  
**Version:** policy-engine@v1.0  
**Document kind:** policy expression, evaluation, override, and replay specification

## 1. Purpose

The policy engine turns evidence, identity, runtime mode, principal scope, action risk, and replay state into an explicit decision. Policy approval is not semantic proof; it is permission to proceed inside a declared authority scope.

## 2. Default rule

```text
missing policy -> deny
stale policy -> deny or audit_only
malformed request -> reject
unknown principal -> deny
unknown runtime -> deny
external action without approval -> deny
mathematical theorem promotion without proof authority -> deny
```

## 3. Policy snapshot

```yaml
PolicySnapshot:
  policy_snapshot_id: string
  version: string
  created_at: string
  status: draft | active | deprecated | revoked
  rules: []
  default_decision: deny | audit_only
  signature: string
```

## 4. Decision request

```yaml
PolicyDecisionRequest:
  request_id: string
  principal:
    principal_id: string
    scopes: []
    auth_strength: anonymous | token | mTLS | signed_node | human_admin
  action:
    action_kind: ingest_evidence | canonicalize | execute_code | check_proof | promote_claim | delegate_task | external_action | purge | query_mcp | custom
    target_kind: string
    target_ref: string
  context:
    runtime_mode_requested: normal | restricted | sandbox | audit_only
    authority_scope_requested: string
    data_class: public | internal | restricted | sensitive | unknown
    network_access_requested: boolean
    filesystem_write_requested: boolean
    external_side_effect: boolean
    replay_identity_ref: string | null
    source_node_id: string | null
    risk_score: number | null
```

## 5. Decision output

```yaml
PolicyDecision:
  policy_decision_id: string
  request_id: string
  policy_snapshot_id: string
  decision: allow | deny | allow_with_obligations | audit_only | sandbox_only | human_review_required | degraded | bypass
  runtime_mode: normal | restricted | sandbox | audit_only | degraded | blocked
  obligations:
    - obligation_kind: log | redact | sandbox | second_oracle | human_review | replay_required | purge_check | rate_limit
      parameters: object
  rationale: string
  decided_at: string
```

## 6. Rule syntax

A v1.6 implementation may use JSON policy rules or compile them into Rego or another engine. The normative interchange shape is JSON:

```yaml
PolicyRule:
  rule_id: string
  priority: integer
  when:
    all: []
    any: []
    not: []
  then:
    decision: allow | deny | audit_only | sandbox_only | human_review_required
    obligations: []
    rationale: string
```

Condition operators:

```text
eq, neq, in, not_in, exists, missing, gt, gte, lt, lte, matches, scope_includes, runtime_at_most, risk_at_most
```

## 7. Mandatory gates

1. `execute_code` requires sandbox policy.
2. `check_proof` requires proof authority profile.
3. `promote_claim` requires status-transition policy and evidence witness IDs.
4. `delegate_task` requires node admission and resource witness freshness.
5. `external_action` requires explicit approval unless a narrower policy grants preapproval.
6. `query_mcp` requires source endpoint profile and redaction policy.
7. `purge` requires purge authorization and dependency graph.

## 8. Override rule

Overrides are not inline booleans. They require:

```text
PolicyOverrideRequest
-> HumanReviewPacket or configured governance workflow
-> PolicyOverrideDecision
-> new PolicyDecision
-> audit event
```

## 9. Replay rule

Replay must evaluate either the exact historical policy snapshot or a declared replay-equivalence policy. It must not silently use current policy to justify past behavior unless the replay target is explicitly `current-policy-simulation`.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
