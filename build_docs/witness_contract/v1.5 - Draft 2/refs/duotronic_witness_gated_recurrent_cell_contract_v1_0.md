# Duotronic Witness-Gated Recurrent Cell Contract v1.0

**Status:** Research profile specification  
**Version:** witness-gated-recurrent-cell@v1.0  
**Document kind:** Normative research-profile contract plus reference formulas, schemas, pseudocode, fixtures, and worked example  
**Primary purpose:** Define the Witness-Gated Recurrent Cell (WG-RNN), a Duotronic runtime component that uses canonical witness features as explicit memory-control gates for fast recurrence, persistent witness memory, local online adaptation, replayable memory updates, and policy-clamped memory promotion.

---

## 1. Scope

This contract specifies the WG-RNN cell as a Duotronic runtime component.

It covers:

1. fast LSTM-style recurrence conditioned on witness features;
2. persistent witness memory slots;
3. canonical witness feature vectors;
4. policy-clamped write, decay, quarantine, and promotion gates;
5. slot attention and slot update rules;
6. candidate, quarantined, stable, deprecated, and tombstoned memory states;
7. local witness-conditioned online adaptation;
8. replayable memory update records;
9. memory promotion requests;
10. purge cascade behavior for memory slots;
11. fixtures for core behaviors;
12. a worked chronological music-preference example.

The WG-RNN is not a general replacement for neural-network training. It is a Duotronic memory-control component.

It must obey the Witness Contract, Policy Shield, Purge/Privacy Contract, Human Review Protocol, Lookup Memory and Replay Profile, Chronological Self-Evidence Contract, and v1.5 distributed cluster constraints.

---

## 2. Research status

> **Status tag:** normative

WG-RNN v1.0 is a research profile.

It may be used for:

1. audit-only experiments;
2. sandbox memory experiments;
3. replayable prototype runs;
4. fixture generation;
5. candidate profile learning;
6. internal research diagnostics.

It must not be treated as normative memory behavior until promoted through:

1. fixture evidence;
2. replay traces;
3. retention diagnostics;
4. purge cascade tests;
5. contradiction tests;
6. human-review tests where required;
7. policy approval;
8. Family Registry handoff if promoted beyond research status.

---

## 3. Core rule

> **Status tag:** normative

A WG-RNN cell must not update long-term memory from raw input.

The required flow is:

```text
chronological event
-> EvidenceBundle
-> CandidateWitness
-> canonicalization
-> CanonicalWitnessFact
-> WitnessFeatureVector
-> WG-RNN gate computation
-> policy clamp
-> MemoryUpdateRecord
-> candidate/quarantined/stable memory slot
```

Raw sensor data, raw text, raw model output, raw source metadata, raw system metrics, raw search results, or raw DBP payloads must not directly drive WG-RNN persistent memory.

Fast recurrent computation may process embeddings for temporary computation, but persistent memory authority comes only from witness-derived features and policy.

---

## 4. Inputs at time step t

At each step, the cell receives:

```yaml
WGRNNStepInput:
  step_id: string
  cell_profile_id: string
  timestamp: string
  x_t_ref: string
  x_t_embedding_profile_id: string
  prior_fast_hidden_state_ref: string
  prior_fast_cell_state_ref: string
  prior_memory_bank_ref: string
  witness_feature_vector_id: string
  policy_context_ref: string | null
  canonical_witness_fact_refs: []
  candidate_witness_refs: []
  transport_replay_identity_ref: string | null
```

Mathematically:

1. input vector `x_t`;
2. prior fast hidden state `h_{t-1}`;
3. prior fast cell state `c_{t-1}`;
4. prior witness memory `M_{t-1} = {m_{t-1}^k}_{k=1}^K`;
5. witness feature vector `w_t`;
6. optional policy context `p_t`.

The witness feature vector must be derived from a `CanonicalWitnessFact` or from a policy-approved `CandidateWitness` under `audit_only` with no promotion authority.

---

## 5. Witness feature vector

> **Status tag:** normative

`WitnessFeatureVector` is a structured Duotronic object. It is not merely a neural embedding.

```yaml
WitnessFeatureVector:
  witness_feature_vector_id: string
  source_canonical_witness_fact_ids: []
  source_candidate_witness_ids: []
  source_policy_decision_ids: []
  source_human_review_decision_ids: []
  source_purge_event_ids: []
  source_replay_identity_refs: []

  confidence_score: number
  contradiction_score: number
  novelty_score: number
  recurrence_score: number
  source_integrity: number
  source_diversity: number
  replayability_score: number
  policy_allow_write: true | false
  policy_allow_promote: true | false
  staleness_score: number
  invalidation_score: number
  human_review_required: true | false
  action_risk: number

  authority_inputs:
    profile_requested_authority: number
    normalizer_confidence: number
    policy_limit: number
    transport_validated: true | false
    canonicalization_validated: true | false

  feature_normalizer_id: string
  schema_id: string
  created_at: string
  created_by_node_id: string | null
  trust_status: candidate | canonicalized | audit_only | rejected
```

### 5.1 Field bounds

Unless a profile declares otherwise:

```text
confidence_score       in [0,1]
contradiction_score    in [0,1]
novelty_score          in [0,1]
recurrence_score       in [0,1]
source_integrity       in [0,1]
source_diversity       in [0,1]
replayability_score    in [0,1]
staleness_score        in [0,1]
invalidation_score     in [0,1]
action_risk            in [0,1]
```

Boolean-derived fields must be derived from explicit policy decisions, not inferred silently.

---

## 6. Fast short-term recurrence

> **Status tag:** reference formula with normative trust boundary

The WG-RNN may compute a fast recurrence similar to LSTM-style recurrence.

The fast recurrence is useful for immediate computation but does not create long-term truth.

Query:

```text
q_t = W_q x_t + U_q h_{t-1} + B_q w_t
```

Memory read:

```text
r_t = read(M_{t-1}, q_t)
```

Fast candidate and gates:

```text
u_t = tanh(W_u x_t + U_u h_{t-1} + V_u r_t + B_u w_t + P_u p_t + b_u)
i_t = sigmoid(W_i x_t + U_i h_{t-1} + V_i r_t + B_i w_t + P_i p_t + b_i)
f_t = sigmoid(W_f x_t + U_f h_{t-1} + V_f r_t + B_f w_t + P_f p_t + b_f)
o_t = sigmoid(W_o x_t + U_o h_{t-1} + V_o r_t + B_o w_t + P_o p_t + b_o)
```

Fast state update:

```text
c_t = f_t ⊙ c_{t-1} + i_t ⊙ u_t
h_t = o_t ⊙ tanh(c_t)
```

### 6.1 Fast state authority

Fast state may support:

1. candidate computation;
2. attention;
3. temporary working memory;
4. action candidate support;
5. diagnostic signals.

Fast state must not be treated as a canonical witness fact without extraction, replay, and policy approval.

---

## 7. Persistent witness memory

The persistent memory bank is:

```text
M_t = {m_t^k}_{k=1}^{K}
```

Each slot is a structured object.

```yaml
MemorySlot:
  slot_id: integer
  memory_bank_id: string
  content_vector_ref: string
  content_vector_hash: string
  content_profile_id: string
  stability_score: number
  contradiction_score: number
  novelty_score: number
  recurrence_score: number
  last_written_at: string | null
  created_at: string
  trust_status: candidate | stable | quarantined | deprecated | tombstoned
  provenance_hashes: []
  canonical_witness_fact_refs: []
  candidate_witness_refs: []
  memory_update_record_refs: []
  replay_identity: string
  policy_decision_id: string | null
  purge_tombstone_id: string | null
```

### 7.1 Trust status meanings

| Status | Meaning | Authority |
|---|---|---|
| `candidate` | provisional memory slot | audit/sandbox only unless policy grants restricted use |
| `quarantined` | isolated due to contradiction, novelty, low confidence, risk, or review requirement | no promotion, no normal action support |
| `stable` | promoted through replay, retention, and policy | policy-scoped authority |
| `deprecated` | retained for replay/migration only | no new normal use |
| `tombstoned` | content removed or disabled due to purge/pruning | no runtime use |

Stable memory slots may be represented as `CanonicalWitnessFact` objects only after promotion approval.

Candidate and quarantined slots are `CandidateWitness`-like memory artifacts.

---

## 8. Witness-specific memory gates

The WG-RNN computes four memory gates before policy clamps:

```text
g_write       = sigmoid(W_w x_t + U_w h_{t-1} + V_w r_t + B_w^write w_t + P_w p_t + b_w)
g_decay       = sigmoid(W_d x_t + U_d h_{t-1} + V_d r_t + B_d^decay w_t + P_d p_t + b_d)
g_quarantine  = sigmoid(W_q^g x_t + U_q^g h_{t-1} + V_q^g r_t + B_q^g w_t + P_q^g p_t + b_q)
g_promote     = sigmoid(W_p^g x_t + U_p^g h_{t-1} + V_p^g r_t + B_p^g w_t + P_p^g p_t + b_p)
```

### 8.1 Gate meanings

| Gate | Meaning |
|---|---|
| `g_write` | whether new content can be written at all |
| `g_decay` | whether existing memory should weaken |
| `g_quarantine` | whether new content must be isolated |
| `g_promote` | whether candidate memory can move toward stable memory |

The learned or computed gate value is never final authority. Policy clamps are mandatory.

---

## 9. Hard policy clamps

> **Status tag:** normative

The following clamps are mandatory and override learned gate values.

### 9.1 Write clamp

If:

```text
policy_allow_write == false
```

or:

```text
invalidation_score > threshold_invalidate
```

then:

```text
g_write <- 0
```

### 9.2 Promotion clamp

If:

```text
replayability_score < min_replay
```

or:

```text
contradiction_score > max_contradiction
```

or:

```text
policy_allow_promote == false
```

then:

```text
g_promote <- 0
```

### 9.3 Quarantine clamp

If:

```text
novelty_score > high_novelty_threshold
```

and:

```text
confidence_score < low_confidence_threshold
```

then:

```text
g_quarantine <- 1
```

### 9.4 Human review clamp

If:

```text
human_review_required == true
```

then:

```text
g_promote <- 0
g_write <- min(g_write, candidate_write_upper_bound)
```

The default `candidate_write_upper_bound` is:

```yaml
candidate_write_upper_bound: 0.10
```

unless policy declares stricter behavior.

### 9.5 Action risk clamp

If:

```text
action_risk > risk_limit
```

then:

```text
g_write <- 0
```

and conflicting slots may receive forced decay:

```text
g_decay_conflicting_slots <- max(g_decay_conflicting_slots, forced_conflict_decay_min)
```

### 9.6 Transport and canonicalization clamp

If transport validation fails or canonicalization fails:

```text
authority_t <- 0
g_write <- 0
g_promote <- 0
```

---

## 10. Authority

> **Status tag:** normative

Memory state-change authority is:

```text
authority_t = min(
  profile_requested_authority,
  w_t.confidence_score,
  w_t.authority_inputs.normalizer_confidence,
  w_t.authority_inputs.policy_limit
)
```

If:

```text
transport_validated == false
```

or:

```text
canonicalization_validated == false
```

then:

```text
authority_t = 0
```

A memory update with `authority_t = 0` may be logged for audit diagnostics but must not change persistent memory.

---

## 11. Slot attention and update

### 11.1 Slot attention

```text
a_t^k = softmax_k((W_a q_t + U_a h_{t-1})^T m_{t-1}^k)
```

The profile may bias attention by:

1. recency;
2. staleness;
3. trust status;
4. actor scope;
5. source lineage;
6. contradiction class;
7. purge state.

### 11.2 Candidate slot content

```text
m_tilde_t^k = tanh(W_m x_t + U_m h_t + V_m m_{t-1}^k + B_m w_t + P_m p_t + b_m)
```

### 11.3 Per-slot write strength

```text
g_write_tk = a_t^k * g_write
```

### 11.4 Candidate memory update

For candidate or newly allocated slots:

```text
m_cand_t^k =
  (1 - g_decay) m_{t-1}^k
  + g_write_tk (1 - g_quarantine) m_tilde_t^k
```

If `g_quarantine` is high, content is written to quarantine instead of candidate memory.

### 11.5 Stable memory update

For stable slots:

```text
m_stable_t^k =
  (1 - g_decay) m_stable_{t-1}^k
  + g_promote ⊙ (g_write_tk m_tilde_t^k)
```

Stable memory never receives direct writes from the current step without promotion.

### 11.6 Quarantine memory update

A quarantined slot may store content only for:

1. contradiction investigation;
2. red-team fixtures;
3. human review;
4. future replay;
5. purge-safe audit.

Quarantined memory has no normal action authority.

---

## 12. Slot management

> **Status tag:** normative

Slot management is rule-based and witness-recorded, not hidden neural mutation.

### 12.1 Split

If a slot contradiction score exceeds threshold:

```text
contradiction_score > split_contradiction_threshold
```

then create a new candidate or quarantined slot containing the conflicting content.

```yaml
SlotSplitRecord:
  slot_split_record_id: string
  source_slot_id: integer
  new_slot_id: integer
  split_reason: contradiction | actor_scope_conflict | purge_boundary | semantic_boundary | custom
  contradiction_refs: []
  policy_decision_id: string
  memory_update_record_id: string
```

### 12.2 Consolidation

If two stable slots are consistently similar, they may be merged only through a recorded bridge operation.

```yaml
SlotConsolidationRecord:
  slot_consolidation_record_id: string
  source_slot_ids: []
  target_slot_id: integer
  bridge_profile_id: string
  degeneracy_class_ref: string | null
  preserved_invariants: []
  expected_loss: []
  policy_decision_id: string
```

Consolidation is not string similarity alone. It requires policy and bridge records.

### 12.3 Pruning

Candidate or quarantined slots that remain stale beyond policy may be tombstoned.

```yaml
MemorySlotPruneRecord:
  memory_slot_prune_record_id: string
  slot_id: integer
  prune_reason: stale_candidate | purge | policy | capacity | manual | custom
  purge_tombstone_id: string | null
  policy_decision_id: string
```

### 12.4 Promotion

Promotion requires a `SlotPromotionRequest`.

---

## 13. Slot promotion

A slot can become stable only through replay, retention, and policy.

```yaml
SlotPromotionRequest:
  slot_promotion_request_id: string
  memory_slot_id: integer
  memory_bank_id: string
  requested_target_status: stable
  supporting_memory_update_record_ids: []
  supporting_canonical_witness_fact_ids: []
  replay_trace_set_id: string
  retention_metric_ids: []
  contradiction_review_refs: []
  purge_check_refs: []
  human_review_decision_ids: []
  promotion_gate_value: number
  promotion_threshold: number
  policy_decision_id: string | null
  status: candidate | approved | rejected | human_review | superseded
```

### 13.1 Promotion requirements

A promotion request may be approved only if:

1. `g_promote` exceeded threshold during relevant updates;
2. replay trace exists and passes;
3. retention diagnostics pass;
4. contradiction score is within policy limit;
5. purge lineage check passes;
6. human review is completed if required;
7. Policy Shield approves the promotion;
8. stable slot authority scope is declared.

---

## 14. Memory update record

Every persistent memory update must create a replayable record.

```yaml
MemoryUpdateRecord:
  memory_update_record_id: string
  cell_profile_id: string
  memory_bank_id: string
  step_id: string
  timestamp: string

  input_refs:
    x_t_ref: string
    prior_fast_hidden_state_ref: string
    prior_fast_cell_state_ref: string
    prior_memory_bank_ref: string
    witness_feature_vector_id: string
    canonical_witness_fact_refs: []
    candidate_witness_refs: []
    policy_context_ref: string | null

  gate_values_before_clamp:
    g_write: number
    g_decay: number
    g_quarantine: number
    g_promote: number

  gate_values_after_clamp:
    g_write: number
    g_decay: number
    g_quarantine: number
    g_promote: number

  authority_t: number
  affected_slot_ids: []
  slot_attention: []
  update_kind: no_op | candidate_write | quarantine_write | stable_decay | promotion_write | split | consolidation | prune | tombstone

  output_refs:
    new_fast_hidden_state_ref: string
    new_fast_cell_state_ref: string
    new_memory_bank_ref: string
    new_or_updated_memory_slot_refs: []

  replay:
    replay_identity_ref: string
    deterministic_required: true
    replay_trace_id: string | null
    transport_replay_identity_ref: string | null

  policy_decision_id: string
  trust_status: candidate | canonicalized | audit_only | rejected
```

If an update cannot be replayed, it may remain diagnostic but has zero promotion authority.

---

## 15. WG-RNN profile

```yaml
WitnessGatedRecurrentCellProfile:
  cell_profile_id: string
  version: string
  status: research_profile | sandbox_runtime_profile | reference_profile | normative_profile | deprecated_profile
  owner_document: duotronic_witness_gated_recurrent_cell_contract_v1_0.md

  dimensions:
    input_dim: integer
    hidden_dim: integer
    cell_dim: integer
    memory_slot_dim: integer
    max_memory_slots: integer
    witness_feature_dim: integer
    policy_context_dim: integer

  memory:
    memory_bank_id: string
    slot_allocation_policy: first_free | attention_low_conflict | actor_scoped | custom
    quarantine_region_enabled: true
    stable_partition_enabled: true
    max_candidate_slots: integer
    max_quarantined_slots: integer
    max_stable_slots: integer

  gates:
    write_gate_profile_id: string
    decay_gate_profile_id: string
    quarantine_gate_profile_id: string
    promotion_gate_profile_id: string
    hard_clamp_policy_id: string

  local_adaptation:
    content_adaptation_enabled: true | false
    fast_weight_adaptation_enabled: true | false
    gate_threshold_adaptation_allowed: false
    max_content_learning_rate: number
    max_fast_weight_learning_rate: number
    max_update_norm: number
    replay_required_for_updates: true

  replay:
    deterministic_required: true
    replay_identity_profile_id: string
    fixture_pack_id: string
    retention_metric_ids: []

  authority:
    allowed_runtime_modes:
      - audit_only
      - sandbox
      - restricted
    promotion_requires_policy: true
    stable_memory_requires_slot_promotion: true

  purge:
    purge_cascade_required: true
    tombstone_on_full_lineage_purge: true
    demote_on_partial_lineage_purge: true
```

---

## 16. WG-RNN policy

```yaml
WitnessGatedRecurrentCellPolicy:
  wg_rnn_policy_id: string
  cell_profile_id: string
  runtime_mode: audit_only | sandbox | restricted | normal
  learning_mode: blocked | audit_only | sandbox | active

  thresholds:
    threshold_invalidate: number
    min_replay: number
    max_contradiction: number
    high_novelty_threshold: number
    low_confidence_threshold: number
    risk_limit: number
    candidate_write_upper_bound: number
    promotion_threshold: number
    split_contradiction_threshold: number
    prune_stale_after_seconds: integer | null

  limits:
    max_memory_slots: integer
    max_updates_per_minute: integer
    max_promotions_per_hour: integer
    max_fast_weight_update_norm: number
    max_content_update_norm: number

  allowed_sources:
    allow_canonical_witness_facts: true
    allow_candidate_witness_audit_only: true | false
    allow_raw_inputs_for_persistent_memory: false

  local_adaptation:
    content_adaptation_allowed: true | false
    fast_weight_adaptation_allowed: true | false
    gate_threshold_adaptation_allowed: false

  human_review:
    require_review_for_high_novelty: true | false
    require_review_for_contradiction_split: true | false
    require_review_for_promotion: true | false

  purge:
    block_writes_after_purge_seconds: integer | null
    require_lineage_check_before_promotion: true

  policy_decision_id: string
```

### 16.1 Mandatory policy defaults

```yaml
allow_raw_inputs_for_persistent_memory: false
gate_threshold_adaptation_allowed: false
replay_required_for_updates: true
stable_memory_requires_slot_promotion: true
```

---

## 17. Local self-training rules

> **Status tag:** normative for WG-RNN local adaptation

The WG-RNN does not require offline backpropagation to update persistent memory. It uses local, witness-conditioned adaptation rules.

### 17.1 Content adaptation

```text
Delta m_t^k =
  eta * g_write_tk
  * recurrence_score_t
  * (1 - contradiction_score_t)
  * (m_tilde_t^k - m_{t-1}^k)
```

The applied update must be bounded by policy:

```text
||Delta m_t^k|| <= max_content_update_norm
```

### 17.2 Fast weight adaptation

Optional local adapter update:

```text
Delta A_t = lambda * g_write * h_t u_t^T - rho A_t
```

where `A_t` is a local projection or read-head adapter matrix.

This is Hebbian-style local adaptation, not global gradient backpropagation.

It must be:

1. bounded;
2. rate-limited;
3. replay-logged;
4. policy-approved;
5. demotable on replay failure.

### 17.3 Gate threshold adaptation

Gate thresholds such as `min_replay`, `max_contradiction`, or `risk_limit` must not be tuned autonomously.

Changing thresholds requires:

1. `PolicyChangeProposal`;
2. human review where policy requires;
3. new policy snapshot;
4. replay of affected memory paths if authority changes.

---

## 18. Pseudocode step function

```text
function WGRNN_STEP(input):
    assert input.witness_feature_vector is present

    w = load(input.witness_feature_vector)
    policy = load_policy(input.cell_profile_id, input.policy_context_ref)

    if not w.authority_inputs.transport_validated:
        return no_op_update(authority=0, reason="transport_failed")

    if not w.authority_inputs.canonicalization_validated:
        return no_op_update(authority=0, reason="canonicalization_failed")

    M_prev = load(input.prior_memory_bank_ref)
    h_prev = load(input.prior_fast_hidden_state_ref)
    c_prev = load(input.prior_fast_cell_state_ref)
    x = load_embedding(input.x_t_ref)

    q = W_q x + U_q h_prev + B_q w
    r = read(M_prev, q)

    u = tanh(W_u x + U_u h_prev + V_u r + B_u w + P_u p + b_u)
    i = sigmoid(W_i x + U_i h_prev + V_i r + B_i w + P_i p + b_i)
    f = sigmoid(W_f x + U_f h_prev + V_f r + B_f w + P_f p + b_f)
    o = sigmoid(W_o x + U_o h_prev + V_o r + B_o w + P_o p + b_o)

    c = f * c_prev + i * u
    h = o * tanh(c)

    g_write_raw = sigmoid(...)
    g_decay_raw = sigmoid(...)
    g_quarantine_raw = sigmoid(...)
    g_promote_raw = sigmoid(...)

    gates = apply_policy_clamps(
        g_write_raw,
        g_decay_raw,
        g_quarantine_raw,
        g_promote_raw,
        w,
        policy
    )

    authority = min(
        w.authority_inputs.profile_requested_authority,
        w.confidence_score,
        w.authority_inputs.normalizer_confidence,
        w.authority_inputs.policy_limit
    )

    if authority == 0 or gates.g_write == 0 and gates.g_promote == 0:
        return record_memory_update(no_op)

    attention = compute_slot_attention(M_prev, q, h_prev)

    for slot in M_prev.slots:
        m_tilde = candidate_slot_content(x, h, slot, w, p)
        g_write_slot = attention[slot.id] * gates.g_write

        if gates.g_quarantine is high:
            write_or_allocate_quarantine_slot(m_tilde)
        else if slot.trust_status in {candidate, quarantined}:
            update_candidate_slot(slot, g_write_slot, gates.g_decay, m_tilde)
        else if slot.trust_status == stable:
            decay_stable_slot(slot, gates.g_decay)
            if gates.g_promote >= policy.thresholds.promotion_threshold:
                apply_promotion_write(slot, g_write_slot, gates.g_promote, m_tilde)

    perform_rule_based_slot_management()

    record MemoryUpdateRecord with:
        input refs
        gate values before clamp
        gate values after clamp
        authority
        affected slots
        replay identity
        policy decision

    return h, c, M_new, MemoryUpdateRecord
```

---

## 19. Replay identity

WG-RNN replay identity must bind:

1. cell profile ID and version;
2. weight/profile hashes;
3. memory bank ID;
4. prior memory bank hash;
5. input witness feature vector hash;
6. source canonical witness fact hashes;
7. policy snapshot ID;
8. clamp thresholds;
9. slot allocation policy;
10. transport replay identity;
11. purge state;
12. human review state;
13. deterministic serialization profile.

```yaml
WGRNNReplayIdentity:
  replay_identity_id: string
  cell_profile_id: string
  cell_profile_hash: string
  memory_bank_id: string
  prior_memory_bank_hash: string
  witness_feature_vector_hash: string
  canonical_witness_fact_hashes: []
  policy_snapshot_id: string
  clamp_threshold_hash: string
  slot_allocation_policy_hash: string
  transport_replay_identity_ref: string | null
  purge_state_hash: string
  human_review_state_hash: string
  digest: string
```

---

## 20. Purge behavior

> **Status tag:** normative

If underlying evidence is purged, memory slots written entirely from that evidence must be tombstoned.

If underlying evidence is partially purged, memory slots must be:

1. demoted to candidate;
2. quarantined;
3. rebuilt from remaining lineage; or
4. tombstoned;

according to policy.

```yaml
MemoryPurgeImpactRecord:
  memory_purge_impact_record_id: string
  purge_event_id: string
  affected_memory_bank_ids: []
  affected_slot_ids: []
  affected_memory_update_record_ids: []
  required_action: demote_to_candidate | quarantine | rebuild | tombstone | human_review
  new_slot_statuses: []
  blocked_write_until: string | null
  policy_decision_id: string
```

After purge, writes to conflicting slots may be temporarily blocked:

```text
g_write <- 0
```

until purge cascade and replay impact are resolved.

---

## 21. Human review behavior

Human review may be required for:

1. high novelty;
2. contradiction split;
3. promotion;
4. action-risk memory;
5. purge ambiguity;
6. actor-scope ambiguity;
7. threshold policy changes.

If `human_review_required == true`, promotion is blocked and write is candidate-only.

Human decisions must be referenced in memory update or promotion records.

---

## 22. Distributed cluster behavior

In v1.5 distributed clusters, WG-RNN updates may run on worker nodes.

Requirements:

1. input witness facts must be available through DBP S2 or local canonical store;
2. DBP replay identity must be included if input crossed nodes;
3. memory update authority is zero if DBP transport validation failed;
4. delegated WG-RNN tasks must use `TaskDelegationActionPayload`;
5. `TaskOutcomeWitness` must include `MemoryUpdateRecord` refs;
6. resource witnesses cannot themselves become persistent memory unless canonicalized and policy-approved.

---

## 23. Fixtures

### Fixture A: valid write under high-confidence canonical evidence

Input:

```yaml
WitnessFeatureVector:
  confidence_score: 0.92
  contradiction_score: 0.05
  novelty_score: 0.30
  recurrence_score: 0.80
  replayability_score: 0.95
  policy_allow_write: true
  policy_allow_promote: false
  invalidation_score: 0.00
  human_review_required: false
  action_risk: 0.10
  authority_inputs:
    profile_requested_authority: 0.80
    normalizer_confidence: 0.90
    policy_limit: 0.70
    transport_validated: true
    canonicalization_validated: true
```

Expected:

```yaml
expected:
  g_write_after_clamp: positive
  authority_t: 0.70
  update_kind: candidate_write
  stable_write_allowed: false
```

### Fixture B: blocked write under invalidation

Input:

```yaml
WitnessFeatureVector:
  policy_allow_write: true
  invalidation_score: 0.95
Policy:
  threshold_invalidate: 0.50
```

Expected:

```yaml
expected:
  g_write_after_clamp: 0
  persistent_memory_changed: false
  update_kind: no_op
```

### Fixture C: quarantine under high novelty and low confidence

Input:

```yaml
WitnessFeatureVector:
  novelty_score: 0.94
  confidence_score: 0.31
Policy:
  high_novelty_threshold: 0.80
  low_confidence_threshold: 0.50
```

Expected:

```yaml
expected:
  g_quarantine_after_clamp: 1
  slot_status: quarantined
  promotion_allowed: false
```

### Fixture D: promotion after stable recurrence

Input:

```yaml
SlotPromotionRequest:
  promotion_gate_value: 0.91
  promotion_threshold: 0.85
  replay_trace_set_id: replay-wgrnn-pref-001
  retention_metric_ids:
    - retention-pref-stability-001
  contradiction_review_refs: []
  purge_check_refs:
    - purge-lineage-clear-001
PolicyDecision:
  decision: allow
```

Expected:

```yaml
expected:
  slot_status_after: stable
  canonical_witness_fact_created: true
```

### Fixture E: contradiction split

Input:

```yaml
MemorySlot:
  slot_id: 7
  contradiction_score: 0.88
Policy:
  split_contradiction_threshold: 0.75
```

Expected:

```yaml
expected:
  SlotSplitRecord_created: true
  original_slot_unchanged: true
  new_slot_status: candidate
```

### Fixture F: purge cascade on memory slots

Input:

```yaml
EvidencePurgeEvent:
  purge_event_id: epe-song-history-0042
MemorySlot:
  slot_id: 12
  provenance_hashes:
    - hash-of-purged-evidence
  trust_status: stable
```

Expected:

```yaml
expected:
  MemoryPurgeImpactRecord_created: true
  slot_status_after: tombstoned
  stable_authority_after: 0
```

### Fixture G: transport failure zeroes authority

Input:

```yaml
WitnessFeatureVector:
  confidence_score: 0.99
  policy_allow_write: true
  authority_inputs:
    transport_validated: false
    canonicalization_validated: true
```

Expected:

```yaml
expected:
  authority_t: 0
  g_write_after_clamp: 0
  g_promote_after_clamp: 0
```

### Fixture H: human review required

Input:

```yaml
WitnessFeatureVector:
  human_review_required: true
  policy_allow_write: true
  policy_allow_promote: true
Policy:
  candidate_write_upper_bound: 0.10
```

Expected:

```yaml
expected:
  g_promote_after_clamp: 0
  g_write_after_clamp_lte: 0.10
  stable_write_allowed: false
```

---

## 24. Worked example: chronological music preference memory

### 24.1 Evidence stream

A user watches and likes several synthwave and instrumental electronic tracks over multiple days.

Flow:

```text
watch/listen events
-> EvidenceBundle
-> PersonalHistorySourceRecord
-> ChronologicalEvidenceStream
-> PreferenceWitness
-> CanonicalWitnessFact
-> WitnessFeatureVector
-> WG-RNN memory update
```

### 24.2 Day 1: candidate memory

Witness features:

```yaml
confidence_score: 0.68
novelty_score: 0.55
recurrence_score: 0.35
contradiction_score: 0.05
replayability_score: 0.80
policy_allow_write: true
policy_allow_promote: false
```

Result:

```yaml
MemorySlot:
  slot_id: 3
  trust_status: candidate
  content_profile_id: music-preference-vector@0.1
  canonical_witness_fact_refs:
    - cwf-music-pref-day1
```

The system may use this slot for audit/sandbox recommendation analysis only.

### 24.3 Day 3: recurrence strengthens slot

The pattern recurs across more evidence.

```yaml
recurrence_score: 0.78
confidence_score: 0.84
replayability_score: 0.91
policy_allow_write: true
policy_allow_promote: false
```

The candidate slot is updated and stability increases.

```yaml
stability_score: 0.72
trust_status: candidate
```

No promotion occurs yet because policy has not allowed promotion.

### 24.4 Day 5: contradiction appears

The user repeatedly skips several tracks from the same inferred cluster.

```yaml
contradiction_score: 0.82
novelty_score: 0.40
confidence_score: 0.76
```

Policy threshold:

```yaml
split_contradiction_threshold: 0.75
```

Result:

```yaml
SlotSplitRecord:
  split_reason: contradiction
  source_slot_id: 3
  new_slot_id: 4
```

Slot 3 remains the original synthwave preference candidate. Slot 4 becomes a candidate exception slot, e.g. “dislikes vocal-heavy synthwave tracks”.

### 24.5 Day 7: promotion request

Repeated evidence supports an instrumental-electronic preference with stable recurrence and replay.

```yaml
SlotPromotionRequest:
  memory_slot_id: 3
  requested_target_status: stable
  supporting_canonical_witness_fact_ids:
    - cwf-music-pref-day1
    - cwf-music-pref-day3
    - cwf-music-pref-day7
  replay_trace_set_id: replay-music-pref-wgrnn-001
  retention_metric_ids:
    - retention-music-pref-stability-001
  promotion_gate_value: 0.89
  promotion_threshold: 0.85
```

Policy approves restricted stable use.

```yaml
MemorySlot:
  slot_id: 3
  trust_status: stable
```

The stable slot can now support internal preference lookup and restricted recommendation planning.

### 24.6 Novel unchecked music trend

A single new genre appears with high novelty and low confidence.

```yaml
novelty_score: 0.96
confidence_score: 0.28
human_review_required: false
```

Result:

```yaml
slot_status: quarantined
promotion_allowed: false
```

The system must not act on this novelty as a stable preference.

### 24.7 Purge event

The user purges one sensitive music-history item.

If slot 3 partially depended on the purged item, the system creates:

```yaml
MemoryPurgeImpactRecord:
  required_action: rebuild
```

If a quarantined slot entirely depended on the purged item:

```yaml
required_action: tombstone
```

The cell blocks writes to affected conflicting slots until purge cascade resolves.

---

## 25. Non-claims

WG-RNN v1.0 does not prove a new learning theory.

It specifies a Duotronic-compatible recurrent memory component that keeps trust, provenance, contradiction, replay, purge, human review, and policy visible in the memory update path.

It is a research profile until benchmarked and promoted.

---

## 26. Chronological self-training specification

> **Status tag:** normative for WG-RNN local online adaptation

The WG-RNN is designed to process evidence in chronological order and update its own persistent memory as that evidence arrives. This section specifies how that self-training loop works and what it may and may not do.

### 26.1 What "self-training" means here

Self-training in the WG-RNN sense means:

1. the cell processes incoming canonical witness facts one step at a time in chronological order;
2. at each step it may update candidate memory slot content through a local delta rule;
3. it may optionally update a local fast-weight adapter through a Hebbian-style rule;
4. every update is bounded by witness features, policy clamps, and rate limits;
5. no global loss function, no backpropagation through time, and no optimizer state such as Adam or SGD are used.

This is not pre-training on a large corpus. It is online, step-by-step memory consolidation driven by the chronological evidence stream the cell is fed.

### 26.2 Chronological stream training loop

At each time step `t` in the chronological evidence stream, the following sequence must occur:

```text
1. Assert canonical evidence is available for step t.
2. Assert WitnessFeatureVector is derived from CanonicalWitnessFact, not raw input.
3. Load policy and apply transport/canonicalization checks.
4. Compute fast recurrence: q_t, r_t, h_t, c_t.
5. Compute raw gate values: g_write, g_decay, g_quarantine, g_promote.
6. Apply policy clamps (section 9). Clamped values override raw values unconditionally.
7. Compute authority_t = min(profile_requested, w_t.confidence_score, normalizer_confidence, policy_limit).
8. If authority_t == 0 or both g_write and g_promote are 0: record no_op MemoryUpdateRecord and skip to step 12.
9. For each memory slot: compute attention, candidate content, per-slot write strength.
10. Apply candidate, stable, or quarantine update per slot trust status.
11. Optionally apply content adaptation delta (section 17.1) and fast-weight adaptation delta (section 17.2).
12. Record MemoryUpdateRecord with all inputs, gate values before and after clamp, authority, slot impacts, and replay identity.
13. Advance to step t+1. The prior memory bank state is the new M_t.
```

Every iteration of this loop must produce a MemoryUpdateRecord regardless of whether persistent memory was changed. A no_op record is valid and required.

### 26.3 What makes this different from GPU-based training

| Property | GPU-based neural training | WG-RNN self-training |
|---|---|---|
| Learning signal | Global gradient from a loss function | Local witness feature gate values |
| Update granularity | Batch or mini-batch | One canonical evidence step at a time |
| Parameter scope | All weights updated jointly | Memory slot content and optional fast-weight adapter only |
| Gate thresholds | Learned as parameters | Fixed by policy; cannot be autonomously adjusted |
| Memory write authority | Gradient magnitude | min(profile_requested, confidence, normalizer_confidence, policy_limit) |
| Promotion | Implicit in loss minimization | Explicit SlotPromotionRequest with replay, retention, and policy checks |
| Auditability | None required by architecture | Every update is a replayable MemoryUpdateRecord |
| Purge support | Not defined | Memory slots carry lineage hashes and cascade on purge |

### 26.4 What the cell may update autonomously

Within a single step, the cell may:

1. update candidate memory slot content by the content adaptation delta (section 17.1);
2. update a local fast-weight adapter by the Hebbian delta (section 17.2), if `fast_weight_adaptation_enabled == true`;
3. decay stable and candidate slot content by `g_decay`;
4. allocate a new candidate or quarantined slot;
5. split a slot whose contradiction score exceeds threshold.

### 26.5 What the cell may not update autonomously

The cell must not:

1. directly promote a candidate slot to stable without a `SlotPromotionRequest` and policy approval;
2. modify any policy threshold including `min_replay`, `max_contradiction`, `risk_limit`, or `candidate_write_upper_bound`;
3. modify its own replay identity binding;
4. write a canonical witness fact on its own behalf without the standard evidence → witness → canonicalization pipeline;
5. self-confirm a memory slot by referencing only prior outputs of the same cell;
6. override a policy clamp based on gate value magnitude;
7. bypass human review when `human_review_required == true`;
8. write to stable slots directly without a promotion record.

### 26.6 Chronological ordering requirement

Evidence must be presented to the cell in chronological order as determined by the `ChronologicalEvidenceStream` contract.

Out-of-order evidence is permitted only in:

1. replay traces, where the target step is explicitly declared;
2. fixtures, where the ordering is fixed and documented;
3. audit-only diagnostic runs that do not affect persistent memory.

Processing out-of-order evidence as live chronological input must be flagged and may be quarantined or rejected depending on policy.

---

## 27. Architectural barriers against unbounded self-modification

> **Status tag:** normative

This section explicitly answers the question: what prevents the WG-RNN from modifying its own memory cells without limit?

### 27.1 Barrier summary

| Barrier | Enforcement point | Effect |
|---|---|---|
| Write gate requires witness features | Gate computation uses `w_t` | Raw input alone cannot produce a valid write signal |
| Policy clamps override all gate values | Applied after gate computation | Policy decision is always the ceiling |
| Gate thresholds are policy-only | Cannot be modified by the cell | The cell cannot lower its own barriers |
| Authority ceiling | `min(profile, confidence, normalizer, policy_limit)` | Authority is bounded to the weakest approved factor |
| Rate limits | `max_updates_per_minute`, `max_promotions_per_hour` | Prevents high-frequency unreviewed self-modification |
| Stable write requires promotion | `SlotPromotionRequest` + policy | The cell cannot write to stable memory directly |
| Contradiction causes quarantine | Clamp 9.3 | Contradictory content is isolated, not written to candidate memory |
| High novelty causes quarantine | Clamp 9.3 | Unknown patterns are isolated until reviewed |
| Human review blocks promotion | Clamp 9.4 | Promotion is frozen when a human decision is pending |
| Purge blocks conflicting writes | Section 20 clamp | Content derived from purged evidence cannot be rewritten |
| Fast state is not persistent truth | Section 6 authority boundary | `h_t` and `c_t` cannot become canonical facts without extraction, replay, and policy |
| Memory self-confirmation forbidden | Section 27.2 | A slot cannot raise its own stability score using only its own prior content |

### 27.2 Self-confirmation prohibition

A memory slot must not be used as the sole evidence for its own continued stability or promotion.

A slot's `canonical_witness_fact_refs` must refer to externally sourced canonical witness facts, not to MemoryUpdateRecords that themselves only reference the same slot.

Self-referential promotion chains are rejected by the policy shield.

### 27.3 Gate threshold lock

The following thresholds are read from policy at each step and must not be overwritten by the cell at runtime:

1. `threshold_invalidate`
2. `min_replay`
3. `max_contradiction`
4. `high_novelty_threshold`
5. `low_confidence_threshold`
6. `risk_limit`
7. `candidate_write_upper_bound`
8. `promotion_threshold`
9. `split_contradiction_threshold`
10. `prune_stale_after_seconds`

Changing any threshold requires a `PolicyChangeProposal` through the standard policy path. The cell may not propose or approve its own policy changes.

### 27.4 Fast state authority boundary

`h_t` and `c_t` are temporary computation artifacts.

They may be used for:

1. gate queries;
2. memory read attention;
3. candidate content computation;
4. diagnostic signals;
5. fast-weight adapter updates.

They may not be used to:

1. directly construct a `CanonicalWitnessFact`;
2. override a policy clamp;
3. set a slot trust status;
4. produce a `SlotPromotionRequest` without external evidence review;
5. write to a stable memory slot.

### 27.5 Scheduler feedback isolation

When WG-RNN cells run in a distributed cluster, scheduler feedback such as task outcomes, resource witness values, and queue pressure must not be fed directly to the cell as `x_t` without being wrapped as canonical witness evidence first.

Scheduler feedback entering the cell as raw embeddings is forbidden for persistent memory updates. It must be wrapped as:

```text
TaskOutcomeWitness
-> EvidenceBundle
-> CandidateWitness
-> canonicalization
-> CanonicalWitnessFact
-> WitnessFeatureVector
```

before it may drive memory gates.

### 27.6 What the barriers collectively enforce

Together, the barriers ensure:

1. the cell cannot continuously write to itself unless the incoming evidence stream consistently produces high-authority witness features;
2. the cell cannot lower its own trust thresholds to inflate its own authority;
3. the cell cannot promote its own memory to stable status without external validation;
4. the cell cannot contaminate its trusted memory with raw sensor data, raw model outputs, or scheduler feedback that has not been through the full evidence pipeline;
5. every change to persistent memory is auditable, replayable, and reversible through purge or demotion.
