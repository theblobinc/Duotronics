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
