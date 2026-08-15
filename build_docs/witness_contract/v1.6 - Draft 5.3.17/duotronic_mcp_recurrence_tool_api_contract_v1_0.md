# Duotronic MCP Recurrence Tool API Contract

**Status:** Research specification draft  
**Version:** mcp-recurrence-tool-api@v1.0  
**Document kind:** Target API contract  
**Primary purpose:** Define target MCP APIs for recurrence tuning and diagnostics.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Status

This contract defines target APIs. Implementations must advertise actual availability through `mcp_tool_manifest` or equivalent.

## 2. query_gap_ratio

```yaml
request:
  loop_id: string
  start_time: string | null
  end_time: string | null
response:
  expected_ticks: integer
  observed_ticks: integer
  absence_witnesses: integer
  silent_missing_ticks: integer
  silent_gap_ratio: number
```

## 3. query_slot_lifecycle_stats

```yaml
request:
  loop_id: string
  slot_family: string | null
  time_window: string | null
response:
  active_slots: integer
  candidate_slots: integer
  stable_slots: integer
  quarantined_slots: integer
  decayed_slots: integer
  purged_slots: integer
  promotion_latency_ms_p50: number
  promotion_latency_ms_p95: number
  quarantine_age_ms_p95: number
```

## 4. propose_decay

```yaml
request:
  target_slot_id: string
  curve_family: exponential | linear | step | custom
  half_life_s: number | null
  rate: number | null
  reason: string
response:
  decay_intent_id: string
  policy_decision_id: string | null
  runtime_mode: candidate | audit_only | applied | rejected
```

## 5. emit_meta_diagnostics

```yaml
request:
  loop_id: string
  diagnostics_json: string
  authority_scope: string
response:
  meta_diagnostics_id: string
  accepted: boolean
  runtime_mode: audit_only | candidate | normal
```

## 6. query_replay_divergence

```yaml
request:
  replay_package_id: string
response:
  divergence_score: number
  first_mismatch_ref: string | null
  affected_slots: list
  policy_action: continue | degrade | quarantine | reject | human_review
```
