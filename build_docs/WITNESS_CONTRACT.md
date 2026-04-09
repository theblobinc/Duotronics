# SRNN Recurrent Witness Contract

> **Created:** 2026-07-08
> **Scope:** Two-level witness dynamics in `srnn/cognition/witness.py`,
> `srnn/cognition/loop.py`, `srnn/cognition/rnn_cell.py`,
> `srnn/cognition/state.py`.
> **References:** Part VI — The Two-Level Witness Design

This document specifies the data types, update rules, decay rates, and
integration points for the recurrent witness-state W̃_t (Part VI §4.2).

---

## 1. Architecture Summary

The witness system has two levels:

| Level | Symbol | Object | Update |
|---|---|---|---|
| **L1 — Object witness** | W_t | `WitnessSignature` | Γ(b_t, x_t, c_t) — computed per packet |
| **L2 — Recurrent witness-state** | W̃_t | `RecurrentWitnessState` | Ψ(W̃_{t-1}, W_t, h_{t-1}, b_t, x_t, u_t) |

The extended chain update becomes:

    h_t = Φ*(h_{t-1}, b_t, x_t, u_t, W_t, W̃_t, r_t)

---

## 2. RecurrentWitnessState Fields

| Field | Type | Default | Decay | Description |
|---|---|---|---|---|
| `family_mass` | dict[str, float] | `{}` | per-family λ_k | Accumulated mass per witness sector |
| `story_axis` | dict[str, float] | `{}` | 0.95 | Witness evidence along story axes |
| `open_callbacks` | dict[str, float] | `{}` | ρ = 0.92 | Callback strength per motif key |
| `sector_trace` | dict[str, int] | `{}` | ±1 per step | Sector dominance persistence counter |
| `contradiction_pressure` | float | `0.0` | 0.85 | Accumulated contradiction signal |
| `coherence_drift` | float | `0.0` | — (recomputed) | RMSE between expected and actual W_t |
| `regime_evidence` | dict[str, float] | `{}` | 0.9 | Posterior regime evidence hints |
| `expected_signature` | dict[str, float] | `{}` | EMA α=0.3 | Predicted next W_t for drift computation |
| `step_count` | int | `0` | — | Number of Ψ updates |

### 2.1 Pruning thresholds

All dicts prune entries below `0.001` to prevent unbounded growth.

### 2.2 Null / absent semantics

An empty `RecurrentWitnessState()` represents time-zero (no witness history).
The Ψ function handles `None` / missing W_t gracefully — all evidence terms
are zero, only decay is applied.

---

## 3. Family Decay Rates (§5.2)

| Family / Sector | λ_k | Rationale |
|---|---|---|
| `temporal_local` | 0.90 | Fast — lyrical echoes |
| `temporal_distant` | 0.98 | Slow — long-horizon autobiographical |
| `high_density` | 0.95 | Moderate — meta-object clusters |
| `social_anchored` | 0.92 | Moderate-fast — social callbacks |
| `callback_rich` | 0.96 | Slow — narrative callbacks |
| `cross_source` | 0.93 | Moderate — cross-source bridges |
| `motif_recurrence` | 0.97 | Slow — recurring thematic motifs |
| `low_evidence` | 0.85 | Very fast — noisy/uncertain |

Default for unknown families: `λ = 0.94`.

---

## 4. Ψ Update Map

The recurrent witness-state update `witness_step()` proceeds in seven stages:

### 4.1 Family mass decay + accumulation

    family_mass_t[k] = λ_k · family_mass_{t-1}[k] + sector_scores[k]

### 4.2 Story-axis evidence

    story_axis_t[a] = 0.95 · story_axis_{t-1}[a] + packet.story_axes[a]

### 4.3 Callback persistence (§5.3)

    cb_{t,j} = ρ · cb_{t-1,j} + trigger_{t,j} - resolve_{t,j}

where ρ = 0.92, trigger ∈ {0,1}, resolve ∈ {0,1}.

### 4.4 Coherence drift (§5.5)

    drift_t = RMSE(expected_signature_{t-1}, sector_scores_t)

Expected signature updated via EMA:

    expected_t[k] = α · actual[k] + (1-α) · expected_{t-1}[k],  α = 0.3

### 4.5 Regime evidence (§5.4)

All prior regime evidence decayed by 0.9, then current regime boosted by
W_t.confidence.

### 4.6 Sector trace

For each sector: increment counter if it is the current dominant sector,
decrement (minimum 0) otherwise. New dominants start at 1.

### 4.7 Contradiction pressure

    pressure_t = 0.85 · pressure_{t-1} + 0.3 · drift_t + 0.1 · regime_instability

where regime_instability = 1 - (max_regime / sum_regimes).

---

## 5. Integration Points

### 5.1 CognitionState (`state.py`)

New field:

```python
recurrent_witness: dict = field(default_factory=dict)
```

Serialized as `recurrent_witness` in `to_dict()` / `from_dict()` using
`RecurrentWitnessState.to_dict()` / `.from_dict()`.

### 5.2 CognitionLoop (`loop.py`)

After witness accumulation (existing L1 code), invoke:

```python
w_t = WitnessSignature(sector_scores=sectors, dominant_sector=dominant, ...)
w_prev = RecurrentWitnessState.from_dict(self.state.recurrent_witness)
w_new = witness_step(w_prev, w_t, packet_dict, regime_label)
self.state.recurrent_witness = w_new.to_dict()
```

### 5.3 RecurrentCell (`rnn_cell.py`)

The Φ* extension passes `W̃_t` contributions into the gate computation:

1. Extract `family_mass` from recurrent witness state
2. Compute `recurrent_witness_bias` as weighted sum of family masses
3. Add to expression state: `+ recurrent_witness_bias * 0.03`
4. Add contradiction gating: scale proposal injection by
   `(1.0 - min(contradiction_pressure, 0.5))`

### 5.4 LoopRanker (`ranking.py`)

New axis `witness_trajectory` (weight 0.08, taken from existing pool):

    WTraj_ℓ = Σ_k family_mass_ℓ[k] · sector_persistence_ℓ[k] / step_count_ℓ

### 5.5 PhiOperator (`phi.py`)

If `regime_evidence` from W̃_t has a dominant regime with evidence > 0.5,
add as soft evidence to the variance-decomposition regime detection.

---

## 6. Serialization Format

```json
{
  "family_mass": {"temporal_local": 0.42, "high_density": 0.31},
  "story_axis": {"nostalgia": 0.88, "energy_arc": 0.55},
  "open_callbacks": {"motif_42": 0.67},
  "sector_trace": {"temporal_local": 5, "high_density": 2},
  "contradiction_pressure": 0.12,
  "coherence_drift": 0.08,
  "regime_evidence": {"stable": 0.82, "shift": 0.15},
  "expected_signature": {"temporal_local": 0.35, "high_density": 0.28},
  "step_count": 47
}
```

---

## 7. Invariants

1. `family_mass` values are non-negative and bounded above by
   1/(1-λ_k) ≈ 10–20 in steady state.
2. `contradiction_pressure` is non-negative.
3. `coherence_drift` is non-negative.
4. `step_count` increments monotonically.
5. `sector_trace` values are non-negative integers.
6. All dict keys are strings from the `DEFAULT_SECTORS` set or
   packet-derived identifiers.
7. `open_callbacks` values are non-negative after clamping.
8. An empty `RecurrentWitnessState()` is always a valid initial state.

---

## 8. Testing Requirements

### 8.1 Unit tests (`test_recurrent_witness.py`)

- Fresh state produces valid output after one Ψ step
- Family-mass decay matches λ_k rates within ε = 0.001
- Callback accumulation: trigger → present, resolve → removed
- Coherence drift: expected=actual → drift ≈ 0
- Boundary: 100-step run does not produce NaN/Inf/overflow
- Serialization round-trip preserves all fields

### 8.2 Integration tests

- CognitionLoop step with witness produces populated `recurrent_witness`
- RecurrentCell receives W̃_t and adjusts gate output
- Ranking with witness_trajectory axis changes loop scores
- Full 50-step loop run — all witness invariants hold at each step

---

## 9. Part VII — Cheap Worker-Side Alternatives

Part VII (2026-04-08) defines cheaper alternatives for worker loops
that do not need full float precision:

### 9.1 Count-Min Sketch `family_mass`

Worker loops may replace the dictionary-backed `family_mass` with a
small Count-Min Sketch. Overestimation is acceptable because
low-support ghosts are pruned at ranking time and the coordinator
path retains exact dictionaries. Feature-flagged in
`srnn/cognition/witness.py`.

### 9.2 Shift-add decay

Worker-side witness updates can approximate common λ values with
integer shift-add:

- `x ← x - (x >> 6) + new` ≈ λ = 0.984375
- `x ← x - (x >> 5) + new` ≈ λ = 0.96875
- `x ← x - (x >> 4) + new` ≈ λ = 0.9375

Not required for canonical path unless benchmarking proves harmless.

### 9.3 Polygonal witness-family transition tables

The `K=8` witness-family transition operator can optionally be
represented as a family of `PolygonCell` entries where each cell
carries family tag, center mass, vertex weights, and orientation.
Useful when canonicalization, family-awareness, bit efficiency, or
local interpretability matters. See Part VII §16 for the full
operator semantics.

### 9.4 Safety rule

All cheap alternatives must pass the canonical safety gates
(Part VII §21): no commit-ledger corruption, no null coercion,
ranking agreement with float baseline (Kendall τ ≥ 0.85), bounded
divergence in witness trajectory metrics.
