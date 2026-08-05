# MCP Recurrence Tool API Contract v1.2

Status: canonical target API.

## `write_witness`

```yaml
request:
  witness_kind: string
  payload: object
  temporal_witness: TemporalWitness
  replay_identity_ref: string | null
response:
  ok: boolean
  witness_event_id: string
  policy_decision_id: string
  canonical_status: raw | candidate | quarantine | canonicalized | rejected
```

## `propose_decay`

```yaml
request:
  slot_id: string
  curve_family: exponential | linear | step | custom
  half_life_s: number | null
  proposed_rate: number
  reason: string
response:
  ok: boolean
  decay_witness_id: string
  policy_decision_id: string
  status: candidate | escalated | rejected
```

## `query_overlay`

```yaml
request:
  loop_id: string | null
response:
  overlay: LiveRecurrentWitnessOverlay
```

## `query_slot`

```yaml
request:
  slot_id: string
response:
  slot_id: string
  first_seen: TemporalWitness
  last_seen: TemporalWitness
  last_update_record: MemoryUpdateRecord
  authority_t: number
  effective_authority_t: number
  decay_witness_id: string | null
  trust_status: string
```

## `emit_meta_diagnostics`

```yaml
request:
  loop_id: string
  temporal_witness: TemporalWitness
  gate_counts: object
  slot_lifecycle_stats: object
  replay_divergence_score: number | null
response:
  ok: boolean
  diagnostic_witness_id: string
```

