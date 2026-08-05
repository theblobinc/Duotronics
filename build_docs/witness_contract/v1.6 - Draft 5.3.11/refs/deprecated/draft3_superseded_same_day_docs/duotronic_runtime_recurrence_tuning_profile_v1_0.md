# Duotronic Runtime Recurrence Tuning Profile

**Status:** Research specification draft  
**Version:** runtime-recurrence-tuning@v1.0  
**Document kind:** Normative/runtime reference profile  
**Primary purpose:** Define how to tune L2, L2M, WG-RNN, and cognition layers without collapsing time, absence, decay, or policy into hidden state.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Scope

This profile applies to runtimes that implement L2 recurrent witness state, L2M lookup memory, WG-RNN persistent slots, L3 meta-control, L4 proposal flow, and L5 policy gating.

## 2. Hard rules

1. Time is a witness, not merely a float timestamp.
2. Every L2 tick emits a record: positive observation, explicit absence, transport failure, policy block, or replay synthetic tick.
3. Every memory update emits a `MemoryUpdateRecord`.
4. L2 decay and L2M decay must be separately parameterized.
5. Decay changes are proposed, witnessed, and policy-gated.
6. L3 parameter changes must be bounded and clamped.
7. L4 handles structural changes and learned profile proposals.
8. L5 policy gates promotion, external action, review, and rollback.

## 3. Temporal gap ratio

A runtime must be able to compute:

```text
gap_ratio = silent_missing_ticks / expected_ticks
```

Silent gaps should be less than 0.1 percent in normal operation. A gap is not silent if an explicit `AbsenceWitness`, `TransportFailureWitness`, or `PolicyBlockedTickWitness` is recorded.

## 4. Multi-scale recurrence

Reference cadence:

| Layer | Interval | Purpose |
|---|---:|---|
| L2 hot recurrence | 100-500 ms | continuity, gate response, local dynamics |
| L2M associative memory | 5-30 s | stable lookup slots and explicit keys |
| MetaDiagnostics | every 100-1000 witnesses | parameter review and drift detection |
| L4 proposal window | operator-defined | structural/profile changes |

## 5. L3 constraint profile

L3 update rules:

```yaml
L3ConstraintProfile:
  max_delta_per_parameter_per_cycle: 0.02
  max_l3_updates_per_1000_witnesses: 10
  requires_meta_diagnostics: true
  requires_policy_clamp_record: true
  structural_change_allowed: false
  structural_change_route: L4Proposal
```

These values are reference defaults. A domain profile may override them with fixtures and replay evidence.

## 6. Required records

```yaml
RuntimeRecurrenceTuningRecord:
  profile_id: runtime-recurrence-tuning@v1.0
  loop_id: string
  node_id: string
  time_window: string
  expected_ticks: integer
  observed_ticks: integer
  absence_witnesses: integer
  silent_gap_ratio: number
  l2_update_count: integer
  l2m_update_count: integer
  quarantine_count: integer
  promotion_count: integer
  decay_request_count: integer
  replay_divergence: number
  policy_clamp_count: integer
```

## 7. Non-claims

This profile does not assert one universal RNN architecture or one universal threshold. It constrains the witness and policy surface around recurrent memory.
