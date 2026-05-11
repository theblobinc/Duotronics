# Duotronic Temporal Witness and Absence Profile

**Status:** Research specification draft  
**Version:** temporal-witness-absence@v1.0  
**Document kind:** Normative profile  
**Primary purpose:** Define TemporalWitness, AbsenceWitness, decay intent, and gap accounting for recurrence replay.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. TemporalWitness

A temporal witness represents time as a scoped and replayable object.

```yaml
TemporalWitness:
  temporal_witness_id: string
  origin:
    origin_id: string
    origin_kind: wall_clock | monotonic_clock | media_clock | game_tick | block_height | proof_step | custom
    origin_description: string
  tick_family:
    family_id: string
    unit: nanosecond | millisecond | frame | sample | tick | proof_step | custom
    resolution: number
    drift_policy: none | measured | bounded | unknown
  count:
    native_count: integer
    external_timestamp: string | null
    unix_time_s: number | null
  binding:
    source_clock: string
    binding_confidence: number
    temporal_edge_weight: number
  replay:
    replay_identity_ref: string
    deterministic_replay: true | false
```

`unix_time_s` is metadata. It is not the canonical temporal identity by itself.

## 2. AbsenceWitness

An absence witness distinguishes missing evidence from positive evidence that nothing happened.

```yaml
AbsenceWitness:
  absence_witness_id: string
  expected_source: string
  expected_tick: TemporalWitness
  absence_kind: sensor_missing | model_timeout | transport_gap | explicit_null | policy_blocked | inactive_source | replay_omission
  decay_intent:
    target_slot_id: string | null
    decay_family: string
    proposed_rate: number
    reason: string
  authority_scope: recurrence_continuity | lookup_memory | proof_replay | runtime_gate | custom
  trust_status: raw | candidate | canonicalized | audit_only | rejected
```

## 3. Gap accounting

```yaml
TemporalGapSummary:
  loop_id: string
  expected_ticks: integer
  observed_positive_ticks: integer
  absence_witness_ticks: integer
  transport_failure_ticks: integer
  policy_blocked_ticks: integer
  silent_missing_ticks: integer
  silent_gap_ratio: number
```

`silent_missing_ticks` must not be silently folded into continuity. A runtime can degrade or bypass, but it must not hallucinate evidence.

## 4. Decay intent

Decay is not simply a numeric curve. It is a proposed effect on memory authority.

```yaml
DecayIntentWitness:
  decay_intent_id: string
  target_slot_id: string
  proposed_by: runtime | L3 | L4 | human | policy | custom
  curve:
    family: exponential | linear | step | custom
    half_life_s: number | null
    rate: number | null
  basis:
    age_s: number
    evidence_density: number
    contradiction_rate: number
    last_successful_replay: string | null
    policy_scope: string
  policy_decision_id: string | null
```

Age may inform decay. Age alone must not determine decay.

## 5. Conformance checks

A conforming runtime must demonstrate:

1. non-float canonical temporal identity;
2. explicit absence handling;
3. replay identity for temporal events;
4. gap ratio calculation;
5. decay intent records;
6. no silent continuity through missing ticks.
