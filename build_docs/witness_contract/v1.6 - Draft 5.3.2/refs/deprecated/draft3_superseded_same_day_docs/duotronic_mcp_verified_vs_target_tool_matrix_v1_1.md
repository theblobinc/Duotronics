# MCP Verified vs Target Tool Matrix v1.1

Status: observed plus target profile.

## Verified tool families

Observed MCP families include:

| Family | Examples | Role |
|---|---|---|
| Meta | `mcp_tool_manifest`, `mcp_capability_report`, `mcp_self_test`, `policy_explain` | Runtime discovery and policy inspection. |
| Repo | `read_repo_file`, `list_repo_dir`, `search_repo`, `git_status`, `create_worktree`, `apply_patch`, `commit_worktree` | Source review and isolated changes. |
| Ops | `list_jobs`, `request_service_restart`, `create_backup_snapshot`, backup tools | Controlled operations. |
| Cognition | `cognition_loops`, `cognition_snapshot`, `recurrent_witness_state`, L3/L4/L5 state tools | Runtime cognition inspection. |
| Witness | `witness_contract_outline`, `witness_contract_section`, `witness_control_artifacts` | Contract and control-artifact review. |
| Minecraft | `minecraft_status`, `minecraft_world_snapshot`, `minecraft_ingest_multimodal_witness`, action tools | External world-state/action witness integration. |
| Browser | `browser_screenshot`, `browser_get_text`, `browser_smoke_test`, `browser_network_trace` | UI and endpoint observation. |

## Target recurrence tools

These are desired tools and must not be claimed as verified until present in `mcp_tool_manifest`.

| Target tool | Purpose | Scope |
|---|---|---|
| `write_witness` | Append a witness packet. | `mcp:write` |
| `propose_decay` | Submit a `DecayIntentWitness`. | `mcp:write` |
| `query_slot` | Inspect a memory slot. | `mcp:read` |
| `emit_meta_diagnostics` | Persist gate/slot/replay diagnostics. | `mcp:write` |
| `query_gap_ratio` | Compute silent gaps. | `mcp:read` |
| `query_replay_divergence` | Return replay diff score. | `mcp:read` |
| `query_quarantine_age` | Report quarantine dwell time. | `mcp:read` |
| `query_slot_lifecycle_stats` | Report slot lifecycle counters. | `mcp:read` |

## Graduation rule

A target tool becomes verified only when:

1. it appears in the manifest;
2. `policy_explain(tool)` returns a policy;
3. self-test covers success and failure paths;
4. state-changing outputs reference witness IDs;
5. replay can verify the resulting state.

