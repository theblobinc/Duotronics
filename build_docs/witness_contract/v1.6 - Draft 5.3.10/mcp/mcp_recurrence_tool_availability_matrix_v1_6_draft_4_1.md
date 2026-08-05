# MCP Recurrence Tool Availability Matrix - v1.6 Draft 4.1

Status: active Draft 4.1 maturity matrix.  
Generated: 2026-05-09.  
Supersedes: ambiguous target/verified wording in earlier recurrence-tool docs.

## Purpose

Draft 3 separated verified MCP tools from target recurrence tools. Draft 4 saw
many recurrence tools become source-observed or test-backed. Draft 4.1 keeps the
maturity boundary explicit so the corpus does not over-claim production
availability.

## Maturity levels

```yaml
MCPToolMaturityLevels:
  target: specified but not observed in the current source or tests
  source_observed: source contains an implementation or route/tool definition
  test_backed: source-level tests exercise expected behavior
  runtime_observed: a live MCP server returned the tool or a valid response
  release_verified: runtime evidence is included in an approved release witness bundle
```

Only `release_verified` tools may be used as production release evidence.

## Tool matrix

| Tool | Draft 3 status | Draft 4.1 status | Read scope | Write scope | Release claim allowed |
|---|---:|---:|---:|---:|---:|
| `write_witness` | target | test_backed | no | `mcp:write` | no |
| `propose_decay` | target | test_backed | no | `mcp:write` | no |
| `query_slot` | target | test_backed | `mcp:read` | no | no |
| `emit_meta_diagnostics` | target | test_backed | no | `mcp:write` | no |
| `query_gap_ratio` | target | test_backed | `mcp:read` | no | no |
| `query_replay_divergence` | target | test_backed | `mcp:read` | no | no |
| `write_replay_divergence` | target | test_backed | no | `mcp:write` | no |
| `query_quarantine_age` | target | test_backed | `mcp:read` | no | no |
| `query_slot_lifecycle_stats` | target | test_backed | `mcp:read` | no | no |
| `query_absence_witnesses` | target | test_backed | `mcp:read` | no | no |
| `write_absence_witness` | target | test_backed | no | `mcp:write` | no |

## Required per-tool evidence object

```yaml
MCPRecurrenceToolAvailability:
  schema: mcp-recurrence-tool-availability@v1
  tool_name: string
  draft3_status: target | verified
  draft41_status: target | source_observed | test_backed | runtime_observed | release_verified
  read_scope_required: string | null
  write_scope_required: string | null
  input_schema_hash: sha256 | null
  output_schema_hash: sha256 | null
  policy_explain_present: boolean | unknown
  self_test_present: boolean | unknown
  state_changing_outputs_reference_witness_ids: boolean | unknown
  replay_verification_present: boolean | unknown
  runtime_evidence_ref: string | null
  release_bundle_ref: string | null
  release_claim_allowed: boolean
```

## Promotion rules

1. Source implementation alone promotes a target only to `source_observed`.
2. A passing unit or integration test promotes it to `test_backed`.
3. A live MCP call with principal/scope evidence promotes it to
   `runtime_observed`.
4. Only an approved release bundle with durable evidence promotes it to
   `release_verified`.
5. State-changing tools MUST return or reference witness IDs for their mutation
   records before they can be release-verified.
