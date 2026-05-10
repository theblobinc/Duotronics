# MCP Raw Observation Summaries — 2026-04-30

**Status:** runtime observation appendix  
**Purpose:** Preserve key structured MCP observations used by Draft 2.

## Tool manifest summary

```json
{
  "server": "xavi-agent-lab",
  "tool_count": 127,
  "groups": [
    "xavi",
    "repo",
    "ops",
    "browser",
    "meta",
    "social",
    "cognition",
    "witness",
    "backup",
    "minecraft"
  ],
  "notable_tools": [
    "mcp_tool_manifest",
    "mcp_capability_report",
    "mcp_self_test",
    "policy_explain",
    "write_file_system",
    "execute_system_command",
    "minecraft_ingest_multimodal_witness",
    "minecraft_collect_blocks",
    "cognition_loops"
  ]
}
```

## Capability summary

```json
{
  "server": "xavi-agent-lab",
  "base_dir": "/var/www/xavi/srnn_server",
  "dns_rebinding_protection": true,
  "allowed_hosts": [
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
    "mcp.xavi.app:*"
  ],
  "auth_keys_configured": true,
  "docker_installed": true,
  "playwright_installed": false,
  "tool_count": 127
}
```

## Self-test summary

```json
{
  "ok": true,
  "error_count": 0,
  "principal_scopes": [
    "mcp:read",
    "mcp:write",
    "mcp:ops-request",
    "mcp:minecraft-action"
  ],
  "git_head": "3b52b6a",
  "git_status": "?? worktrees/agent_duotronic-v1-6-full-impl/",
  "docker_container_count_observed": 85,
  "db_chat_ok": true,
  "db_srnn_ok": true,
  "fallback_manager_stats": true,
  "fallback_tier0": true
}
```

## System stats summary

```json
{
  "disk": {
    "total_gb": 786.37,
    "used_gb": 642.14,
    "free_gb": 104.22,
    "minimum_free_gb": 50.0,
    "safe_to_write": true
  },
  "enrichment": {
    "total_tracks": 0,
    "enriched": 0,
    "pct": 0
  },
  "fallback": true
}
```

## Known degraded observations

```json
{
  "list_tables": {
    "tables": [],
    "warning": "milvus_unavailable",
    "fallback": true
  },
  "cognition_loops": {
    "error": "column \"step\" does not exist"
  },
  "minecraft_status": {
    "mode": "disabled",
    "bridge_exists": true
  }
}
```
