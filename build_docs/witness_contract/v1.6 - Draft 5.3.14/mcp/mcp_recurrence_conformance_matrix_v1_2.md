# MCP Recurrence Conformance Matrix v1.2

Status: canonical conformance checklist.

| Tool | Required? | Current role | Required result |
|---|---:|---|---|
| `mcp_tool_manifest` | yes | discovery | Lists all tools. |
| `policy_explain` | yes | governance | Returns risk, scope, approval requirement. |
| `mcp_self_test` | yes | health | Passes core paths. |
| `write_witness` | yes | target mutation | Creates witness and returns witness_event_id. |
| `propose_decay` | yes | target mutation | Creates DecayIntentWitness. |
| `query_overlay` | yes | target read | Returns LiveRecurrentWitnessOverlay v1.2. |
| `query_slot` | yes | target read | Returns slot lifecycle and authority. |
| `emit_meta_diagnostics` | yes | target mutation | Records gate counts and diagnostics. |
| `query_gap_ratio` | yes | target read | Returns expected/written/absence/silent gaps. |
| `query_replay_divergence` | yes | target read | Returns replay diff score. |
| `query_quarantine_age` | yes | target read | Returns dwell time and escalation candidates. |
| `query_slot_lifecycle_stats` | yes | target read | Returns create/write/decay/promote/quarantine counts. |

## Pass criteria

A server passes this matrix only when:

1. all required tools are present or mapped to an equivalent tool;
2. each tool has a policy explanation;
3. each state-changing tool emits a witness ID;
4. denied-path tests exist;
5. replay can verify state changes.

## Current warning

Existing MCP has many verified tools but the recurrence-specific target set is not fully verified. Treat missing tools as Draft 3 implementation blockers, not tuning issues.

