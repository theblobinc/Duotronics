# Duotronic MCP Verified vs Target Tool Matrix

**Status:** Research specification draft  
**Version:** mcp-tool-matrix@v1.0  
**Document kind:** Runtime observation and target contract  
**Primary purpose:** Separate tools observed in the current MCP server from desired Draft 3 recurrence-control tools.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Purpose

Draft 3 distinguishes verified MCP tools from target tools. A document must not imply that a target tool exists until a manifest snapshot or source observation proves it.

## 2. Verified meta and diagnostics tools

Observed current MCP capabilities include:

```text
mcp_tool_manifest
mcp_capability_report
mcp_self_test
policy_explain
xavi_api_health_matrix
ops_service_catalog
get_job_artifact
create_backup_snapshot
list_backup_snapshots
get_backup_snapshot
verify_backup_snapshot
```

## 3. Verified repo and ops tools

Observed current MCP capabilities include:

```text
read_repo_file
list_repo_dir
search_repo
git_status
create_worktree
list_worktrees
apply_patch
diff_worktree
run_worktree_tests
commit_worktree
remove_worktree
write_file_system
execute_system_command
list_jobs
request_service_restart
request_stack_deploy
get_service_logs
get_audit_log
```

`write_file_system` and `execute_system_command` require additional policy and audit treatment because they mutate host state.

## 4. Verified cognition and witness tools

Observed current MCP capabilities include:

```text
cognition_loops
cognition_snapshot
recurrent_witness_state
meta_recurrent_witness_state
architectural_witness_state
cosmological_witness_state
cognition_gate_history
cognition_state_drift
cognition_memory_profile
cognition_prediction_analysis
cognition_witness_lattice
witness_contract_outline
witness_contract_section
witness_control_artifacts
```

## 5. Desired target recurrence tools

The following tools are Draft 3 targets. They are not current verified capabilities unless a later manifest proves them:

```text
write_witness
propose_decay
query_slot
emit_meta_diagnostics
query_gap_ratio
query_replay_divergence
query_quarantine_age
query_slot_lifecycle_stats
query_policy_clamps
query_absence_witnesses
```

## 6. Tool availability witness

```yaml
MCPToolAvailabilityWitness:
  tool_name: string
  observed: true | false
  source: mcp_tool_manifest | source_code | operator_report | test_fixture
  observed_at: string
  policy_explain_available: true | false
  required_scope: string | null
  approval_required: true | false | null
  runtime_mode: verified | target | deprecated | blocked
```
