# Browser Chat and Workbench Invocation Witness Contract

Status: active Draft 4.1 authority contract.  
Generated: 2026-05-09.  
Applies to: browser chat routes, workbench file/Python/command operations, and
browser-mediated MCP tool calls.

## Purpose

The browser path has different authority properties than direct MCP calls. It can
include JWT authentication, signed request bodies, nonces, timestamp checks,
allowlisted tool calls, and workbench mutation surfaces. Draft 4.1 requires each
browser-mediated invocation to produce or link to invocation evidence.

## Canonical object

```yaml
BrowserChatToolInvocationWitness:
  schema: browser-chat-tool-invocation@v1
  request_id: string
  client_id: string | null
  route: string
  auth_subject: string | null
  auth_method: jwt | signed_request | local | unknown
  timestamp_utc: timestamp
  nonce: string | null
  nonce_replay_check: passed | failed | not_applicable
  request_body_sha256: sha256
  signature_verified: boolean | not_applicable
  tool_name: string | null
  allowlist_result: allowed | denied | not_applicable
  workbench_capability_flag: python_enabled | file_workspace_enabled | commands_enabled | none | unknown
  mutation_surface: none | file | command | python | mcp_write | mixed
  mutation_requires_backup: boolean | unknown
  audit_event_id: string | null
  result_witness_ref: string | null
  denial_reason: string | null
```

## Required denial behavior

Browser-mediated calls MUST be denied or downgraded when:

1. the request signature fails;
2. the nonce is reused inside the replay window;
3. the requested MCP tool is not allowlisted;
4. the workbench capability flag is disabled;
5. a mutation is requested without required backup policy evidence;
6. the caller lacks the needed read/write scope.

## Minimum audit fields

```yaml
BrowserInvocationAuditMinimum:
  request_id: required
  route: required
  principal_or_subject: required_when_authenticated
  request_body_sha256: required
  nonce_or_replay_marker: required_for_signed_requests
  allowlist_decision: required_for_tool_calls
  mutation_surface: required
  result_or_denial: required
```

## Relationship to MCP evidence

Browser invocation evidence does not replace MCP recurrence-tool evidence. When a
browser request calls an MCP tool, the browser witness MUST reference the MCP
witness or audit record for that tool call.
