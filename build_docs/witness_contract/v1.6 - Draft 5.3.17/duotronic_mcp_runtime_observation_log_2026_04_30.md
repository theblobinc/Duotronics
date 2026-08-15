# MCP Runtime Observation Log — 2026-04-30

**Status:** Runtime observation log  
**Purpose:** Record observed MCP endpoint responses used to update v1.6 Draft 2.

---

## 1. Capability report

Observed:

```yaml
server: xavi-agent-lab
base_dir: /var/www/xavi/srnn_server
auth_keys_configured: true
docker_installed: true
playwright_installed: false
tool_count: 127
transport_security:
  enable_dns_rebinding_protection: true
  allowed_hosts:
    - 127.0.0.1:*
    - localhost:*
    - "[::1]:*"
    - mcp.xavi.app:*
```

Interpretation:

1. the MCP endpoint has active auth keys;
2. DNS rebinding protection is enabled;
3. Docker is available;
4. Playwright browser installation should be clarified before browser tooling is relied on;
5. MCP tooling must be described as a scoped, policy-governed operational surface.

---

## 2. Self-test

Observed:

```yaml
ok: true
error_count: 0
principal:
  type: chatgpt_user
  scopes:
    - mcp:read
    - mcp:write
    - mcp:ops-request
    - mcp:minecraft-action
git_head: 3b52b6a
git_status: "?? worktrees/agent_duotronic-v1-6-full-impl/"
```

Self-test also observed Docker containers, database checks, path checks, and fallback API responses.

Interpretation:

1. endpoint is operational;
2. repo has an untracked worktree path, which should be treated as implementation state;
3. self-test success does not mean every sub-tool returns semantically valid results.

---

## 3. System stats

Observed disk:

```yaml
total_gb: 786.37
used_gb: 642.14
free_gb: 104.22
minimum_free_gb: 50.0
safe_to_write: true
```

Interpretation:

1. current free space is above the minimum write threshold;
2. large local state means backup/retention policy matters;
3. release processes should check disk before interpreter or video-ingest workloads.

---

## 4. Database list-tables observation

Observed result:

```yaml
tables: []
warning: milvus_unavailable
_fallback: true
```

Interpretation:

1. fallback database browsing is available;
2. direct table introspection did not return a normal table list;
3. Draft 2 should require migration checks and local DB health probes before declaring production readiness.

---

## 5. Cognition loop observation

Observed error:

```text
column "step" does not exist
```

Interpretation:

1. at least one cognition tool expects a schema field that is absent in the current backend;
2. Draft 2 adds `duotronic_cognition_loop_migration_note_v1_0.md`;
3. this must be fixed before release-candidate status.

---

## 6. Minecraft status

Observed:

```yaml
mode: disabled
bridge_url: http://127.0.0.1:8766
bridge_timeout: 10
bridge_path: /var/www/xavi/srnn_server/mineflayer-bridge/server.js
bridge_exists: true
```

Interpretation:

1. Minecraft capability is installed but inactive;
2. docs must distinguish installed, configured, enabled, and active;
3. external-action tools must remain approval-gated.

---

## 7. Policy observations

Observed:

```yaml
minecraft_ingest_multimodal_witness:
  risk: db_write
  required_scope: mcp:write
  approval_required: false

minecraft_collect_blocks:
  risk: external_action
  required_scope: mcp:minecraft-action
  approval_required: true
```

Interpretation:

1. perception ingest and external actions are different risk classes;
2. DB write is allowed under write scope without per-call approval;
3. external Minecraft actions require approval.
