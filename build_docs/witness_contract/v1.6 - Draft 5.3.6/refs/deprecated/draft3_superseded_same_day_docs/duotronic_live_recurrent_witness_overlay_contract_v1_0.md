# Duotronic Live Recurrent Witness Overlay Contract

**Status:** Research specification draft  
**Version:** live-recurrent-overlay@v1.0  
**Document kind:** Runtime interface contract  
**Primary purpose:** Define the live recurrent witness overlay exposed by SRNN daemon and MCP diagnostics.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Purpose

The live recurrent witness overlay is a read-only runtime status payload that exposes the latest useful recurrent witness state for operators, MCP clients, dashboards, and replay diagnostics.

## 2. Minimal shape

```yaml
LiveRecurrentWitnessOverlay:
  loop_id: string
  node_id: string
  updated_at: string | null
  dominant_sector: string | null
  family_mass: object
  open_callbacks: object
  sector_trace: object
  regime_evidence: object
  contradiction_pressure: number
  coherence_drift: number
  temporal_state: object
  recurrent_temporal: object
  wg_rnn_runtime_last_update_record: object
  effective_authority_t: number
  freshness_state: current | stale | unknown | absent | custom
  ttl_class: ephemeral | time_sensitive | slow_changing | stable | custom
```

## 3. Loop selection

Default loop preference should favor canonical runtime loops before test loops:

```text
chrono-main
social-main
contrastive-main
narrator-main
explore-main
storyboard-main
thematic-main
social-bsky-main
main
global
chronological
```

Test loops may be returned only when explicitly requested or when no non-test loops exist.

## 4. Source compatibility

Snapshot readers must not require a physical `step` column. Step may be derived from `state_json.native_index`, `state_json.step_count`, or `state_json.step`.

## 5. Policy boundary

The overlay is not canonical truth by itself. It is a runtime status and diagnostic witness source. Actions based on it still require policy gates.
