# Duotronic Runtime Recurrence Tuning Profile v1.1

Status: normative Draft 3 Completed profile.

## Purpose

This profile makes L2, L2M, and WG-RNN recurrence replayable and governable. It replaces hidden recurrence state with explicit witness-bearing records.

## TemporalWitness

```yaml
TemporalWitness:
  temporal_witness_id: string
  origin: string
  clock_family: real_time | monotonic_process | game_tick | media_frame | proof_step | simulated_tick | external
  tick_family: string
  count: integer
  canonical_ts: number | null
  observed_at: number | null
  ingested_at: number | null
  source_clock: string
  binding_confidence: number
  drift_model_ref: string | null
  authority_t: number
  freshness_state: current | stale | future | unknown
  ttl_class: ephemeral | slow_changing | stable | permanent | policy_bound
  replay_identity_ref: string
```

The primary replay coordinate is `(origin, clock_family, tick_family, count)`. Float timestamps are raw metadata unless policy grants them canonical status.

## MemoryUpdateRecord

Every L2 tick that writes, decays, quarantines, promotes, rejects, confirms, merges, splits, or prunes memory must emit:

```yaml
MemoryUpdateRecord:
  update_id: string
  loop_id: string
  node_id: string
  temporal_witness_id: string
  slot_id: string | null
  update_kind: write | decay | promote | quarantine_write | reject | confirm | merge | split | prune
  trust_status: raw | candidate | quarantine | canonicalized | rejected
  gate_values_before_clamp: object
  gate_values_after_clamp: object
  authority_t: number
  effective_authority_t: number
  policy_decision_id: string
  replay_identity_ref: string
  witness_event_id: string | null
```

Promoted facts without update records are not replay-complete.

## AbsenceWitness

```yaml
AbsenceWitness:
  absence_witness_id: string
  expected_source: string
  expected_tick: TemporalWitness
  absence_kind: sensor_missing | model_timeout | transport_gap | explicit_null | policy_blocked | runtime_disabled | unknown
  decay_intent:
    target_slot_id: string | null
    decay_family: string
    proposed_rate: number
    reason: string
  authority_scope: recurrence_continuity | sensor_health | model_health | policy | replay
  trust_status: candidate | canonicalized | rejected
  policy_decision_id: string | null
```

Silent gaps must be measured separately from explicit absence.

## DecayIntentWitness

```yaml
DecayIntentWitness:
  decay_witness_id: string
  slot_id: string
  curve_family: exponential | linear | step | custom
  half_life_s: number | null
  proposed_rate: number
  proposed_by: L2 | L3 | L4 | L5 | human | policy
  reason: string
  policy_decision_id: string
  effective_from: TemporalWitness
```

Slot age alone must not define decay. Use stability class, evidence density, contradiction rate, last successful replay, policy scope, then age.

## Reference defaults

These are reference defaults, not hard canon.

```yaml
write_threshold: 0.65
promote_threshold: 0.85
promote_consistent_witness_min: 3
quarantine_conflict_threshold: 0.40
l3_max_delta_per_parameter_per_cycle: 0.02
l3_update_budget_per_1000_witnesses: 10
```

Mathematical theorem promotion must not rely on similarity. A theorem requires proof authority, proof artifact identity, checker witness, policy approval, and replayable verification.

## Stale evidence rules

| Evidence class | Behavior |
|---|---|
| Ephemeral resource availability | Quarantine and block promotion. |
| Slow-changing chat/social/corpus evidence | Degrade temporal authority and retain candidate status unless fresh corroboration exists. |
| Permanent proof artifact | Preserve identity but require checker freshness and policy context. |
| Sensor stream | Emit absence or stale witness; do not infer continuity. |

