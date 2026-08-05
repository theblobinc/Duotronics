# Duotronic MCP Missing Runtime Tools Backlog

**Status:** Research specification draft  
**Version:** mcp-runtime-backlog@v1.0  
**Document kind:** Implementation backlog  
**Primary purpose:** List target MCP tools needed for tighter Draft 3 recurrence control.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Backlog status

The tools in this document are target implementation tasks. They must not be treated as available until observed in a manifest and covered by policy.

## 2. Critical target tools

### 2.1 write_witness

Writes a typed witness into the runtime intake path.

```yaml
write_witness:
  risk: db_write
  required_scope: mcp:write
  approval_required: false
  required_fields:
    witness_kind: string
    payload_json: string
    loop_id: string
    node_id: string
    temporal_witness_id: string
```

### 2.2 propose_decay

Proposes a decay curve for an L2M or WG-RNN slot.

```yaml
propose_decay:
  risk: db_write
  required_scope: mcp:write
  approval_required: false
  routes_to_policy: true
```

### 2.3 query_slot

Reads one memory slot and its lifecycle history.

```yaml
query_slot:
  risk: read_only
  required_scope: mcp:read
```

### 2.4 emit_meta_diagnostics

Emits an L3 diagnostics record without promoting a parameter update.

```yaml
emit_meta_diagnostics:
  risk: db_write
  required_scope: mcp:write
```

## 3. High-value query tools

```text
query_gap_ratio
query_replay_divergence
query_quarantine_age
query_slot_lifecycle_stats
query_policy_clamps
query_absence_witnesses
```

## 4. Conformance rule

A runtime may implement equivalent functionality under different names only if the manifest maps the alias to this backlog item.
