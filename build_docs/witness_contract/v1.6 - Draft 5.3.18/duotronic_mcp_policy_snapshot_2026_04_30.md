# MCP Policy Snapshot — 2026-04-30

**Status:** Runtime policy observation  
**Purpose:** Capture observed policy classifications for selected MCP tools.

---

## 1. Observed principal scopes

```text
mcp:read
mcp:write
mcp:ops-request
mcp:minecraft-action
```

---

## 2. Selected tool policies

### 2.1 `minecraft_ingest_multimodal_witness`

```yaml
risk: db_write
required_scope: mcp:write
approval_required: false
description: Ingest external video/audio/image witness payload
allowed_for_principal: true
```

Draft 2 interpretation:

- This is a witness-ingest action.
- It mutates witness/queue state.
- It does not require human approval by default, but it must still emit a tool-call witness and source provenance.

### 2.2 `minecraft_collect_blocks`

```yaml
risk: external_action
required_scope: mcp:minecraft-action
approval_required: true
description: Collect nearby blocks via collectblock plugin
allowed_for_principal: true
```

Draft 2 interpretation:

- This is an external-world action.
- It requires explicit approval.
- It must emit action candidate, policy decision, execution record, and action outcome witness.

---

## 3. Policy class taxonomy

```text
read_only
db_write
repo_write
service_mutation
external_action
admin_action
proof_promotion
theorem_promotion
```

---

## 4. Required records by policy class

| Policy class | Required records |
|---|---|
| read_only | tool-call witness |
| db_write | tool-call witness, affected object refs |
| repo_write | tool-call witness, backup/git sync refs |
| service_mutation | ops job, approval if required, backup snapshot |
| external_action | action candidate, policy decision, execution, outcome witness |
| proof_promotion | proof witness, checker run, human review if configured |
| theorem_promotion | proof witness, accepted checker result, policy decision, review record |
