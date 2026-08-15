# Live Recurrent Witness Overlay Contract v1.2

Status: canonical; supersedes v1.0 and v1.1.

## Purpose

The live overlay is mandatory for Draft 3 real-time recurrence. Without it, recurrence falls back to batch promotion and continuity is lost.

## Endpoint/tool behavior

A conforming runtime exposes an overlay through one or more of:

```text
MCP query_overlay
MCP recurrent_witness_state
HTTP /duotronic/v1/mcp/recurrence/query_overlay
daemon status live_recurrent_witness
```

## Required shape

```yaml
LiveRecurrentWitnessOverlay:
  loop_id: string
  node_id: string
  step: integer
  updated_at: string
  dominant_sector: string
  family_mass: object
  open_callbacks: object
  sector_trace: object
  regime_evidence: object
  contradiction_pressure: number
  coherence_drift: number
  temporal_state:
    last_canonical_ts: number | null
    delta_t_s_ema: number | null
    temporal_fit: number | null
    temporal_residual: number | null
  recurrent_temporal:
    effective_authority_t: number
    freshness_state: current | stale | future | unknown
    ttl_class: ephemeral | slow_changing | stable | permanent | policy_bound
  wg_rnn_runtime_last_update_record: MemoryUpdateRecord
  slot_lifecycle_stats: object
  gate_counts: object
  replay_divergence_score: number | null
```

## Canonical loop selection

Prefer canonical loops before test loops:

```text
chrono-main
social-main
contrastive-main
narrator-main
explore-main
storyboard-main
thematic-main
main
global
chronological
```

Test loops may be selected only when explicitly requested.

## Conformance checks

1. Overlay returns without SQL error.
2. Overlay includes temporal state.
3. Overlay includes gate counts.
4. Overlay includes last update record.
5. Overlay exposes `effective_authority_t`.
6. Overlay identifies stale/current state.
7. Overlay can be replay-linked.

## Current known bug

The live MCP `cognition_loops` query still returns:

```text
column "step" does not exist
```

Therefore the overlay is not runtime-closed until migration 001 is applied and verified.

