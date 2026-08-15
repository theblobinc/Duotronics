# MCP Tool Manifest Snapshot — 2026-04-30

**Status:** Runtime observation witness  
**Source:** Xavi.app MCP endpoint  
**Server:** `xavi-agent-lab`

---

## 1. Summary

Observed tool count:

```text
127
```

Observed high-level groups:

```text
xavi
repo
ops
browser
meta
```

The full runtime also exposes additional domains such as social, cognition, witness, backup, and Minecraft/Mineflayer tooling.

---

## 2. Representative tool families

### 2.1 Xavi / SRNN data tools

```text
system_stats
tier0_status
daemon_status
disk_usage
list_tables
browse_table
query_database
get_track
search_tracks
enrichment_queue
enrichment_progress
```

### 2.2 Repository tools

```text
list_repo_dir
read_repo_file
search_repo
git_status
create_worktree
apply_patch
diff_worktree
run_worktree_tests
commit_worktree
remove_worktree
```

### 2.3 Ops tools

```text
list_jobs
ops_service_catalog
create_backup_snapshot
request_service_restart
request_stack_deploy
get_service_logs
get_audit_log
backup_s3_status
remote_backup_status
```

### 2.4 Meta tools

```text
mcp_tool_manifest
policy_explain
mcp_capability_report
mcp_self_test
```

### 2.5 Cognition / witness tools

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

### 2.6 Minecraft / Mineflayer tools

```text
minecraft_status
minecraft_runtime_status
minecraft_start_bridge
minecraft_stop_bridge
minecraft_list_bots
minecraft_spawn_bot
minecraft_stop_bot
minecraft_bot_status
minecraft_world_snapshot
minecraft_inventory
minecraft_nearby_entities
minecraft_nearby_blocks
minecraft_recent_events
minecraft_bot_chat
minecraft_bot_action
minecraft_bot_pathfind
minecraft_collect_blocks
minecraft_attack_nearest
minecraft_follow_entity
minecraft_stop_follow
minecraft_look_at
minecraft_ingest_reward
minecraft_export_episode
minecraft_ingest_multimodal_witness
```

---

## 3. Draft 2 significance

The tool manifest expands Duotronic runtime integration beyond static documents. It makes repo, ops, cognition, witness, backup, browser, social, and Minecraft tools first-class evidence sources.

A v1.6 implementation must distinguish:

1. tool existence;
2. tool availability;
3. tool policy;
4. current runtime mode;
5. successful tool execution;
6. witnessable result.
