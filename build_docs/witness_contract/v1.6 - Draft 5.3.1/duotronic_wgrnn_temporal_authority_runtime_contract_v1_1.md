# WG-RNN Temporal Authority Runtime Contract

**Status:** Research specification draft  
**Version:** wgrnn-temporal-authority@v1.1  
**Document kind:** Markdown specification  
**Primary purpose:** Specify current source-aligned WG-RNN temporal authority, freshness, and shim behavior.  
**Draft:** v1.6 Draft 3 updated source refresh  
**Generated:** 2026-04-30T18:15:00Z

---

## 1. Purpose

This document supersedes the v1.0 WG-RNN gate profile where it conflicts with the current SRNN runtime source. It defines the current Draft 3 updated runtime contract.

## 2. Always-enabled rollout

The WG-RNN rollout is considered authoritative even when environment variables request off mode. Runtime availability means:

- prototype-backed if Duotronics WG-RNN imports succeed;
- authoritative shim-backed if imports fail;
- no silent no-op fallback.

## 3. Input tensor

The runtime input tensor has ten features:

1. evidence quality;
2. binding confidence;
3. precision weight;
4. meta-object overlap count normalized;
5. log-normalized delta time;
6. log-normalized recency;
7. local density normalized;
8. temporal edge weight;
9. source clock is real time;
10. source clock is arrangement.

## 4. Temporal authority fields

Every runtime update record should expose gate fields:

```yaml
gate_values_after_clamp:
  authority: float
  raw_authority: float
  effective_authority: float
  effective_authority_t: float
  freshness_weight: float
  freshness_state: current | stale | unknown
  stale_action: degrade_authority | block_promotion
  source_clock: string
  source_clock_trust: float
  clock_confidence: float
  temporal_edge_weight: float
  confidence: float
  contradiction: float
```

## 5. Stale evidence behavior

### 5.1 Ephemeral stale evidence

If evidence is stale and its temporal profile says `block_promotion`, the update must be quarantined:

```yaml
update_kind: quarantine_write
trust_status: quarantine
```

### 5.2 Slow-changing stale evidence

If evidence is stale and its temporal profile says `degrade_authority`, authority may be reduced but the record does not automatically require quarantine.

## 6. Shim update record

The authoritative shim must emit:

```yaml
MemoryUpdateRecord:
  memory_update_record_id: string
  memory_bank_id: string
  step_id: string
  witness_feature_vector_id: string
  gate_values_before_clamp: object
  gate_values_after_clamp: object
  authority_t: float
  affected_slot_ids:
    - integer
  update_kind: candidate_write | quarantine_write
  trust_status: candidate | quarantine
  timestamp: number
  replay_identity_ref: sha256:string
  policy_decision_id: string
  input_refs:
    - string
  shim: true
```

## 7. Recurrent mirror

The recurrent witness mirror must include:

- family mass;
- sector trace;
- contradiction pressure;
- coherence drift;
- expected signature;
- step count;
- temporal state;
- `wgrnn.authority_t`;
- `wgrnn.update_kind`.

## 8. Half-life defaults

Current source defaults:

| Family | Half-life |
|---|---|
| temporal_local | 6 hours |
| social_anchored | 30 days |
| motif_recurrence | 90 days |
| callback_rich | 180 days |
| low_evidence | 1 hour |
| default | 7 days |

These are implementation defaults. They remain configurable reference defaults, not mathematical constants.

## 9. Lost witness record

When family mass decays below retention threshold, the mirror may emit:

```yaml
LostWitness:
  family: string
  previous_mass: float
  new_mass: float
  lost_reason: temporal_decay
  lost_at_pdt: string
  delta_t_s: float
```

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
