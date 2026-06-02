# SRNN Backend Current-State Review — 2026-04-30

**Status:** Draft 2 source-review note  
**Purpose:** Summarize current SRNN backend state used by the v1.6 Draft 2 corpus.

---

## 1. Current git state observed through MCP

```yaml
git_head: 3b52b6a
recent_commit: Auto-register identity oracle adapters
working_tree_note: untracked worktree path observed
```

The MCP self-test reports the endpoint and core paths as operational.

---

## 2. Backend capabilities reflected in Draft 2

1. Identity oracle adapters are auto-registered by importing the oracle package.
2. Structured temporal payloads can become WG-RNN witness events without heavyweight ML models.
3. Oracle job worker persists `witness_event_id` from oracle result payloads.
4. Multimodal ingest service validates frame witnesses, enriches temporal deltas, and forwards normalized payloads to MCP.
5. Minecraft/Mineflayer tools support observation, action, multimodal ingest, reward ingest, and episode export.
6. Direct filesystem write and host command execution MCP tools exist and are governed as higher-risk mutation tools.
7. Mutating tools can auto-create backup snapshots and git commit/push changes when configured.
8. Audit logging redacts sensitive fields.
9. Remote and S3 backup tooling are present in the MCP surface.
10. Cognition tools exist but at least one schema mismatch was observed.

---

## 3. Required documentation updates applied

| Backend feature | Draft 2 document |
|---|---|
| Auto-registered identity adapters | `duotronic_srnn_git_commit_integration_notes_2026_04_30.md` |
| Direct mutation tools | `duotronic_direct_mutation_tools_security_addendum_v1_0.md` |
| MCP live manifest | `duotronic_mcp_tool_manifest_snapshot_2026_04_30.md` |
| MCP runtime observations | `duotronic_mcp_runtime_observation_log_2026_04_30.md` |
| MCP policies | `duotronic_mcp_policy_snapshot_2026_04_30.md` |
| Minecraft actions | `duotronic_minecraft_mcp_action_profile_v1_1.md` |
| Multimodal witness runtime | `duotronic_multimodal_witness_runtime_profile_v1_1.md` |
| Cognition schema mismatch | `duotronic_cognition_loop_migration_note_v1_0.md` |

---

## 4. Release blocker notes

1. Fix cognition-loop schema mismatch.
2. Decide whether direct host mutation tools are allowed in production mode.
3. Ensure backup and git-sync outcomes are themselves witness records.
4. Verify database introspection without fallback mode.
5. Clarify Playwright browser-tool installation status.
6. Ensure Minecraft mode remains disabled unless explicitly approved.

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
