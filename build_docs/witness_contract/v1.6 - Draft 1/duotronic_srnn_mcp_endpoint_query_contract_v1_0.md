# SRNN MCP Endpoint Query Contract v1.0

**Status:** normative integration contract  
**Version:** srnn-mcp-endpoint-query@v1.0  
**Document kind:** MCP endpoint query and observation specification

## 1. Purpose

This document defines how the v1.6 corpus may query an SRNN server through an MCP endpoint app and incorporate answers into the witness system.

## 2. Endpoint profile

```yaml
McpEndpointProfile:
  endpoint_profile_id: string
  base_url: string
  protocol: mcp-json-rpc
  auth_kind: bearer | mTLS | local | none
  allowed_methods: []
  timeout_ms: integer
  redaction_profile_id: string
  authority_scope: diagnostics | source_evidence | task_status | witness_lookup | admin_only
  runtime_mode: audit_only | sandbox | restricted | normal
```

## 3. Query witness

```yaml
SRNNMCPQueryWitness:
  mcp_query_witness_id: string
  endpoint_profile_id: string
  method: string
  request_hash: string
  response_hash: string
  response_status: success | error | timeout | malformed | policy_veto
  extracted_candidate_witness_ids: []
  policy_decision_id: string
  replay_identity_ref: string
  created_at: string
```

## 4. JSON-RPC request

```json
{
  "jsonrpc": "2.0",
  "id": "query-uuid",
  "method": "tools/call",
  "params": {
    "name": "srnn_status_or_query_tool",
    "arguments": {}
  }
}
```

## 5. Recommended query methods

The endpoint app should expose or proxy these capabilities where available:

```text
srnn_health
srnn_capabilities
srnn_recent_oracle_jobs
srnn_get_oracle_job
srnn_recent_witness_events
srnn_get_witness_event
srnn_task_queue_status
srnn_runtime_lanes
srnn_policy_status
srnn_multimodal_ingest_status
srnn_minecraft_bridge_status
srnn_replay_status
```

## 6. Trust boundary

An MCP response is not canonical truth by default. It is source evidence from a registered endpoint. It may support diagnostics, task state, or witness lookup if policy permits. It may not promote a mathematical theorem, approve a policy override, or execute an external action by itself.

## 7. Failure handling

```text
endpoint_unreachable -> audit_only diagnostic
method_missing -> endpoint_profile_mismatch
malformed_response -> source_integrity_reject
auth_failure -> policy_veto and security event
stale_response -> degraded or audit_only
```

## 8. Packaging note

When a live MCP endpoint is queried during corpus generation, raw requests and responses must be captured in `duotronic_srnn_mcp_endpoint_observation_log_YYYY_MM_DD.md` or a machine-readable companion artifact. If the endpoint is unavailable to the generation environment, the corpus must say so rather than inventing observations.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
