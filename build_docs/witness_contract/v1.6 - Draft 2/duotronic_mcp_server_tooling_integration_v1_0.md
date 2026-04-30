# Duotronic MCP Server Tooling Integration v1.0

**Status:** Draft 2 normative integration profile  
**Purpose:** Define how Duotronics records and uses live MCP server tooling as witness-bearing infrastructure.

---

## 1. MCP endpoint role

The MCP endpoint is not merely an automation surface. In v1.6 Draft 2 it is a witnessable operational substrate.

The endpoint can provide:

1. tool manifest observations;
2. capability reports;
3. self-test results;
4. repo status;
5. database inspection;
6. policy explanations;
7. Minecraft/Mineflayer runtime status;
8. SRNN cognition and witness state;
9. backup and ops state;
10. browser and social tooling.

---

## 2. MCPToolManifestWitness

```yaml
MCPToolManifestWitness:
  witness_id: string
  server_name: string
  observed_at: string
  tool_count: integer
  groups: {}
  all_tools_hash: string
  source: mcp_tool_manifest
  trust_status: raw | candidate | canonicalized
```

The manifest is a runtime observation. It is not automatically a stable API contract until versioned and policy-approved.

---

## 3. MCPCapabilityReportWitness

```yaml
MCPCapabilityReportWitness:
  witness_id: string
  server_name: string
  base_dir: string
  transport_security: {}
  auth_keys_configured: boolean
  docker_installed: boolean
  playwright_installed: boolean
  tool_count: integer
  observed_at: string
```

---

## 4. MCPSelfTestWitness

```yaml
MCPSelfTestWitness:
  witness_id: string
  ok: boolean
  error_count: integer
  principal_scopes: []
  git_head: string
  git_status: string
  docker_container_count: integer
  path_checks: {}
  database_checks: {}
  warnings: []
```

---

## 5. Policy explanation integration

Every high-risk tool should have a policy explanation query result.

Example:

```yaml
MCPPolicyExplanationWitness:
  tool: minecraft_collect_blocks
  risk: external_action
  required_scope: mcp:minecraft-action
  approval_required: true
  allowed_for_principal: true
```

---

## 6. Mutating MCP tools

Mutating tools include:

1. repository writes;
2. direct filesystem writes;
3. host command execution;
4. service restarts;
5. stack deploys;
6. Minecraft actions;
7. database writes.

Such tools require:

1. explicit policy entry;
2. required scope;
3. audit record;
4. redacted arguments;
5. backup/git sync where applicable;
6. result witness;
7. rollback path where applicable.

---

## 7. Fallback and degraded observations

Some MCP tools may return fallback responses from web APIs or degraded results.

A fallback response must be marked:

```text
runtime_status = degraded_fallback
```

It must not be confused with a direct authoritative local database query.

---

## 8. Draft 2 observed state summary

Draft 2 observed:

1. MCP server `xavi-agent-lab`;
2. 127 tools in manifest;
3. principal scopes: read, write, ops-request, minecraft-action;
4. Docker installed;
5. DNS rebinding protection enabled;
6. auth keys configured;
7. Git head `3b52b6a`;
8. Minecraft bridge file exists but mode is disabled;
9. cognition loop query returned a schema error requiring migration attention.
