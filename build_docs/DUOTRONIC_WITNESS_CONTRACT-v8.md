# SRNN Recurrent Witness Contract

> **Created:** 2026-04-08 | **Updated:** 2026-04-20
> **Version:** v8
> **Type:** Normative contract (semantics) + implementation binding appendices
> **Source-document note:** this document is intended to stand on its own. Suggestions from external reviews have been integrated as contract improvements rather than cited commentary.
> **Primary naming note:** the preferred name for the lookup memory layer is **L2M**. **L2.5** is retained only as a historical alias where needed for continuity with earlier drafts.
> **Example-data note:** hashes, IDs, and JSON artifacts in examples are illustrative but structurally realistic; they are not live production identifiers.
> **Revision note:** v8 preserves the bounded, audited, CPU-first higher-order design introduced in v6, retains L2M (historical alias L2.5) introduced in v7 and further hardens the contract for portability, lifecycle clarity, and backend pluggability:
> - **L2M** (historical alias **L2.5**) is the **lookup-backed witness memory** with typed keys, collision-aware multi-head hashing, context-aware gating, short local mixing, and prefetch semantics
> - **L3** remains an **event-triggered sparse meta-controller** with `spsa_meta_estimator` as the reference estimator and finite-difference fallback only when diagnostics require it
> - **L4** remains a **screened proposal layer** with cheap proxy ranking, multi-fidelity replay racing, and full locked `ShadowReplaySpec` replay reserved for finalists, now extended to search lookup-memory structure as well as recurrent structure
> - **L5** remains a **compiled governance shield** with Simplex-style certified fallback semantics, and now additionally constrains lookup-memory budgets, collision ceilings, and safe bypass behavior
> **v7-v8 hardening additions:** this revision adds explicit budgets and SLOs, canonical key construction requirements, collision-detection semantics, parameter-specific SPSA perturbation scales, screening-proxy correlation audits, an explicit L5 runtime mode model (`normal`, `degraded`, `bypass`), and an implementation-hazard warning for L2M.
> **Scope:** Five witness levels (L1-L5) plus one lookup-memory layer (L2M) across:
> `srnn/cognition/witness.py`, `srnn/cognition/loop.py`,
> `srnn/cognition/rnn_cell.py`, `srnn/cognition/state.py`,
> `srnn/meta/witness.py` (new), `srnn/meta/estimator.py` (new),
> `srnn/meta/triggers.py` (new), `srnn/architecture/` (new),
> `srnn/policy/constraints.py` (new), `srnn/policy/shield.py` (new),
> `srnn/memory/lookup.py` (new), `srnn/memory/hashing.py` (new),
> `srnn/memory/gating.py` (new), `srnn/memory/prefetch.py` (new)
> **Lineage note:** this document supersedes prior witness-contract drafts and is intended to stand on its own as the authoritative source specification.
>
> **Portability note:** The witness semantics defined in this contract
> (L1-L5 states, the L2M lookup substrate, update maps, decay / lookup /
> modulation rules, integration points, invariants, and testing
> requirements) are intended to be **implementation-language-agnostic** and
> **storage-agnostic**. They should survive:
>
> - backend language changes (e.g., Python -> Rust)
> - storage migration (SQLite -> PostgreSQL + Milvus + Redis)
> - API surface evolution
>
> Implementation bindings (specific Python class names, file paths,
> table names, or cache implementations) appear in integration-point
> sections and should be understood as current reference implementation
> details, not permanent contracts.

This document specifies the data types, update rules, decay rates,
lookup-memory rules, governance semantics, and integration points for
the recurrent witness system. The canonical witness hierarchy remains:
L1 (object witness), L2 (recurrent witness), L3 (meta-recurrent
controller), L4 (architectural witness / search layer), and L5
(cosmological witness / governance shield). In addition, v7 introduced
**L2M**, a lookup-backed witness memory layer that exists
between recurrent dynamics and higher-order control.

---

# Part A — Normative Contract

## 1. Architecture Summary

The witness system now comprises five levels plus one lookup-memory layer,
each operating on a different timescale and modifying either the
dynamics of the level below or the set of admissible actions available
to the lower levels.

In **v8**, the design is explicitly split into two classes of state:

- **Fast online recurrent state**: L1 and L2
- **Cheap explicit associative memory**: L2M
- **Slow bounded control**: L3
- **Staged structural change**: L4
- **Compiled policy / shield semantics**: L5

The most important v8 design rule is:

> **Stable witness facts should be retrieved by cheap lookup when
> possible, not repeatedly reconstructed through recurrent computation.**

This allows a pluggable fast-local-memory backend, with deterministic CPU fallback, to carry long-horizon witness facts
(entity grounding, callback anchors, motif bindings, cross-source links,
and scene-associated associations) while preserving L2 for fast online
continuity and leaving L3-L5 focused on control and governance.

| Layer | Symbol | Object | Update Frequency | Modifies |
|---|---|---|---|---|
| **L1 — Object witness** | \(W_t\) | `WitnessSignature` | Per packet | — |
| **L2 — Recurrent witness** | \(\tilde{W}_t\) | `RecurrentWitnessState` | Per packet | RNN gates / local recurrent dynamics |
| **L2M (historical alias L2.5) — Lookup witness memory layer** | \(M_t\) | `WitnessLookupMemory` | Per packet lookup + asynchronous maintenance | Hidden-state enrichment via retrieved witness facts |
| **L3 — Event-triggered meta-controller** | \(\hat{W}_\tau\) | `MetaRecurrentWitness` | Triggered when drift / contradiction / backlog policy fires | L2 hyperparameters and bounded lookup policy knobs |
| **L4 — Screened architectural witness** | \(\bar{W}_\mu\) | `ArchitecturalWitness` | Maintenance windows, with staged screening | Candidate deltas for recurrent and lookup-memory structure |
| **L5 — Shielded cosmological witness** | \(\breve{W}\) | `CosmologicalWitness` | Fixed / compiled / very slow | Feasible set, shield policy, approvals, rollback authority |

### 1.1 Budgets and SLO registry (normative defaults)

Unless deployment policy overrides them, the following defaults are part
of the contract and must be materialized in the active L5 policy:

| Budget / SLO | Target | Hard Ceiling | Default Action on Breach |
|---|---:|---:|---|
| recurrent step time | 35 ms | 50 ms | clamp L3, freeze L4 if persistent |
| lookup p99 latency | 120 us | 250 us | degrade lookup |
| lookup timeout rate | 0.02 | 0.10 | bypass lookup |
| key construction mean time | 40 us | 100 us | degrade or bypass lookup |
| collision rate EMA | 0.01 | 0.05 | degrade lookup |
| collision emergency ceiling | — | 0.12 | force bypass |
| lookup RAM per node | 1024 MB | 2048 MB | reject L4 proposal |
| prefetch queue memory | 16 MB | 64 MB | drain queue and degrade |
| gate fire rate floor | 0.05 | 0.01 | mark memory path ineffective |
| screening proxy correlation | 0.70 | 0.55 | disable or retrain screening |
| rollback rate EMA | 0.02 | 0.05 | reset promotion budget |

These values are contract defaults, not mere examples. If a deployment
chooses different ceilings, the active policy snapshot must record them
explicitly.

The recurrent chain remains:

\[
h_t = \Phi^*\bigl(h_{t-1}, b_t, x_t, u_t, W_t, \tilde{W}_t, r_t\bigr)
\]

with \(\tilde{W}_t\) governed by L2 hyperparameters \(\theta_t\), and
\(\theta_t\) itself supplied by the currently accepted L3 state:

\[
\tilde{W}_t = \Psi_{\theta_t}\bigl(\tilde{W}_{t-1}, W_t, \dots\bigr),
\qquad
\theta_t = \mathrm{apply}\bigl(\theta_{\mathrm{base}}, \hat{W}_\tau\bigr)
\]

The lookup-backed memory substrate injects retrieved witness facts
through a bounded gating path:

\[
r_t^{\mathrm{lookup}} = \Lambda\bigl(k_t, M_t\bigr),
\qquad
\gamma_t = G(h_t^{\mathrm{ctx}}, r_t^{\mathrm{lookup}}),
\qquad
h_t^{+} = h_t + \gamma_t \odot r_t^{\mathrm{lookup,mix}}
\]

where:

- \(k_t\) is the typed witness lookup key or key bundle,
- \(\Lambda\) is the retrieval operator,
- \(G\) is the context-aware gate,
- \(r_t^{\mathrm{lookup,mix}}\) is the optionally mixed / short-conv
  enriched retrieval output.

### 1.2 Core control-flow pseudocode (normative sketch)

The following sequence is the minimum integration order a conforming
implementation must preserve, even if it pipelines or batches the
individual operations differently:

```python
packet = next_packet()

# L1
w_t = extract_witness_signature(packet)

# early context / hot-path preparation
ctx_t = project_initial_context(packet, state)

# L2M key path
key_bundle = build_typed_witness_keys(packet, state, ctx_t)
typed_key = canonicalize_witness_key(key_bundle)
prefetch_handle = prefetch_lookup(typed_key, backend, policy.lookup_policy)

# resolve lookup under bounded timeout
retrieved_bundle = resolve_lookup(
    prefetch_handle,
    timeout_us=policy.lookup_policy["prefetch_timeout_us"],
)

# gate / mix / inject
gated_recall, lookup_diag = gate_lookup(
    ctx_t, retrieved_bundle, state.lookup_witness, policy
)
mixed_recall = mix_local(gated_recall)
ctx_t = inject_lookup(ctx_t, mixed_recall)

# L2 recurrent update
state.recurrent_witness, state.hidden = recurrent_witness_step(
    state.recurrent_witness,
    state.hidden,
    w_t,
    ctx_t,
    accepted_l3_policy=state.meta_recurrent_witness,
    lookup_mode=state.lookup_witness["bypass_mode"],
)

# telemetry and diagnostics
state.lookup_witness = update_lookup_diagnostics(
    state.lookup_witness, lookup_diag
)
emit_hot_path_metrics(state, lookup_diag)

# L3 trigger check
if should_run_l3(state, policy):
    run_l3_controller_step(state, policy)

# L4 maintenance / screening windows only
if should_run_l4(state, policy):
    run_l4_architect_step(state, policy)

# L5 shield runs continuously on the resulting state / metrics
state, policy = apply_runtime_shield(state, policy)
```

Normative implications:
1. key canonicalization must occur before lookup resolution,
2. lookup injection must happen before the main L2 recurrent update,
3. L2 must still execute correctly if `retrieved_bundle` is absent,
4. L5 shield actions may clamp, degrade, or bypass any lookup-dependent
   branch before the next step begins.

L4 does **not** directly rewrite the live network on every update.
Instead, it emits **candidate architecture deltas** that must pass:

1. cheap proxy screening,
2. multi-fidelity replay racing,
3. locked `ShadowReplaySpec` validation,
4. L5 shield / approval checks.

L5 defines the feasible set in which L2M, L3, and L4 are allowed to
operate, and it retains the certified fallback path:

- base L2 hyperparameters,
- lookup bypass or reduced lookup mode,
- accepted incumbent generation.

---

## 2. L1 — Object Witness (`WitnessSignature`)

L1 is the instantaneous witness signature extracted from the current
packet, event, frame, or observation. It is intentionally fast and
ephemeral. L1 does not attempt to solve long-horizon continuity or fact
storage; its job is to make the current step legible to the recurrent
and memory layers.

A conforming `WitnessSignature` must be able to express at least the
following classes of information:

- object or entity identity cues,
- role and source cues,
- local event / scene cues,
- callback-local markers,
- contradiction-local markers,
- bounded confidence or evidence markers.

Normative L1 semantics:

1. L1 must be computable on the hot path.
2. L1 may be uncertain, but uncertainty must be represented explicitly
   rather than silently omitted.
3. L1 may not depend on future packets.
4. L1 is permitted to be lossy so long as the loss is bounded and
   monotonic with respect to the extraction policy.
5. L1 output must remain meaningful under L2M bypass.

Recommended implementation shape:
- a compact typed structure,
- fixed field names or schema-versioned variants,
- bounded scalar and categorical components,
- no dependence on heavyweight global search.


---

## 3. L2 — Recurrent Witness State (`RecurrentWitnessState`)

L2 is the fast continuity layer. It carries short-horizon recurrent
state across packets and is responsible for preserving scene coherence,
callback persistence, contradiction accumulation, and continuity between
adjacent witness events.

Normative L2 responsibilities:

- maintain bounded continuity state across the current sequence,
- track family mass and local recurrence structure,
- maintain callback persistence and resolution pressure,
- track coherence drift and contradiction pressure,
- expose telemetry needed by L3, L4, and L5,
- remain correct under full L2M bypass.

The canonical L2 update remains the seven-stage witness update:

1. family mass update,
2. story / scene axis update,
3. callback update,
4. drift update,
5. regime-evidence update,
6. sector-trace update,
7. contradiction-pressure update.

In v8, all L2 hyperparameters remain **base values** that may be
boundedly modulated only by accepted L3 state. L2 may additionally
consume gated witness-memory retrievals from L2M, but those retrievals
must remain additive, bounded, and bypass-safe.

Normative L2 interaction rules:

- L2 may consume only **accepted** L3 policy settings.
- L2 may consume only **gated and shield-permitted** L2M retrievals.
- L2 must never consult unaccepted controller candidates.
- L2 must remain semantically valid when lookup is fully disabled.
- L2 must emit enough telemetry for objective scoring, trigger policies,
  and safety enforcement.


---

## 3A. L2M — Lookup Witness Memory Layer (`WitnessLookupMemory`)

### 3A.0 Purpose

L2M is a lookup-memory layer that stores and retrieves stable or
semi-stable witness facts more cheaply than repeated recurrent
reconstruction.

`WitnessLookupMemory` is the normative subsystem name. `L2M` is the preferred layer label in this revision, while `L2.5` is retained only as a historical alias for continuity with prior drafts.

Typical examples include:

- entity grounding,
- callback anchors and unresolved references,
- motif bindings,
- cross-source alignments,
- scene- or role-conditioned associations,
- recurring phrase or event templates,
- contradiction and repair patterns.

L2M is **not** a free-form reasoning layer. It is a lookup substrate
with the following design goals:

1. **cheap lookup over a pluggable fast-local-memory backend, with deterministic CPU fallback**,
2. **typed witness keys**, not arbitrary raw token storage,
3. **collision-aware multi-head hashing**,
4. **context-aware gating before injection**,
5. **optional short local mixing**, not global heavy computation,
6. **safe bypass semantics** when unavailable, stale, or shield-blocked.

### 3A.1 Witness key and value semantics

A lookup item is defined by a typed key:

\[
k_t \in \mathcal{K}_{\mathrm{witness}}
\]

where a key may be built from one or more of:

- `entity_id`
- `family_id`
- `motif_id`
- `callback_id`
- `role_id`
- `source_id`
- `scene_signature`
- `event_signature`
- `contradiction_signature`
- bounded n-gram or phrase IDs when text-bound lookup is desired

A value row stores a compact witness fact vector:

\[
v_t \in \mathbb{R}^{d_M}
\]

which may encode:

- semantic grounding,
- callback context,
- relation summaries,
- expected continuation priors,
- repair hints,
- cross-source anchors,
- motif or entity attributes.

Values may be learned end-to-end, refreshed offline, written from a
registry, or maintained through a bounded online update policy, but the
contract requires that retrieval preserve the typed-key semantics above,
that value staleness be representable, and that the update / eviction
policy be versioned and auditable.

#### 3A.1.1 Canonical key construction (normative)

Typed witness keys must be canonicalized before hashing.
Canonicalization is part of the witness contract because inconsistent key
construction destroys replay identity, collision auditing, and
cross-worker determinism.

Normative requirements:

1. key fields must appear in a schema-versioned canonical order,
2. absent fields must be represented explicitly rather than omitted
   implicitly,
3. integerization and normalization rules must be version-pinned,
4. the same input witness bundle must yield the same canonical key across
   process restarts and across workers sharing a read-only table,
5. canonicalization must be bounded in cost and metered,
6. the canonical wire representation must be schema-versioned and
   deterministic,
7. the schema version must uniquely identify both field ordering and
   canonicalization code / rules.

#### 3A.1.2 Key construction budget (normative)

Key construction is part of lookup cost. The total cost of:

- deriving typed IDs,
- canonicalizing the bundle,
- integerizing fields,
- and preparing hash inputs

must remain within the active L5 key-construction budget.

Default contract targets:
- target mean key-build time: **40 us**
- hard ceiling: **100 us**

If key construction persistently exceeds budget, the shield may force
`degraded` or `full_bypass` just as it would for slow lookup.

#### 3A.1.3 Lookup backend abstraction (normative)

The memory layer must be implemented behind a backend interface that is
pluggable at the storage / hash-family level.

A conforming `WitnessLookupBackend` must provide at minimum:

- `canonicalize(raw_key_bundle) -> typed_key`
- `lookup(typed_key, budget, mode) -> retrieved_rows`
- `prefetch(typed_key, budget, mode) -> handle`
- `resolve(handle, timeout_us) -> retrieved_rows | null`
- `diagnostics() -> backend_diagnostics`
- `optional_update(write_batch) -> update_report`

Normative requirements:
1. backend choice must not alter witness semantics within a fixed
   `schema_version`,
2. backend diagnostics must expose latency, timeout, hit-rate, and
   collision-related signals sufficient for L5 enforcement,
3. any non-CPU backend must specify a deterministic CPU fallback path,
4. backend migration is structural and therefore belongs to L4.

### 3A.2 State fields

| Field | Symbol | Type | Default | Description |
|---|---|---|---|---|
| `backend_family` | — | `str` | `xor-baseline-v1` | Selected lookup backend / hash family identifier |
| `table_count` | \(H_M\) | `int` | `8` | Number of independent hash heads / tables |
| `table_width` | \(M\) | `int` | implementation-defined | Slots per table |
| `value_dim_per_head` | \(d_h\) | `int` | `64` | Width of each per-head retrieval vector |
| `ngram_orders` | — | `list[int]` | `[1,2]` | Supported key composition orders |
| `positional_multipliers` | \(c_{p,h}\) | `dict \| null` | conditional | Required only for multiplier-based backends such as `xor-baseline-v1`; omitted for perfect-hash or keyed-hash families, or equivalent configuration for the selected `backend_family` |
| `lookup_gate_bias` | \(b_g\) | `float` | `0.0` | Additive gate bias, L3-bounded |
| `lookup_budget_logit` | \(\ell_B\) | `float` | `0.0` | Bounded control over the per-step normalized retrieval budget, mapped by policy into active heads / looked-up keys / prefetched bytes |
| `head_enable_mask` | — | `list[bool]` | all `true` | Head-wise enable / disable mask |
| `collision_rate_ema` | \(\hat{\chi}\) | `float` | `0.0` | Observed or estimated collision pressure |
| `hit_rate_ema` | \(\hat{h}\) | `float` | `0.0` | Effective retrieval hit rate |
| `gate_fire_rate_ema` | \(\hat{g}\) | `float` | `0.0` | Fraction of retrievals meaningfully injected |
| `prefetch_queue_depth_ema` | — | `float` | `0.0` | Rolling queue depth for asynchronous prefetch |
| `lookup_latency_us_ema` | — | `float` | `0.0` | Rolling lookup latency estimate |
| `bypass_mode` | — | `str` | `"off"` | `off`, `degraded`, or `full_bypass` |
| `schema_version` | — | `str` | required | Versioned key / value schema identifier |
| `value_update_policy` | — | `str` | required | `offline_refresh`, `bounded_online`, `registry_derived`, or versioned equivalent |
| `staleness_horizon_s` | — | `int` | policy-defined | Maximum admissible value age before degraded confidence |
| `eviction_policy_version` | — | `str` | required | Versioned eviction / tombstone / TTL policy |
| `telemetry_schema_version` | — | `str` | required | Version of emitted L2M diagnostics and metrics |

### 3A.3 Hashing semantics

The contract requires a **schema-versioned, order-sensitive, bounded-cost
hash family** for lookup addressing. The normative core does **not**
mandate a single hash algorithm. Instead, it requires that the selected
family satisfy all of the following:

1. deterministic within `schema_version`,
2. order-sensitive across key positions,
3. bounded in cost under the active lookup SLO,
4. collision-auditable,
5. replay-stable across restarts and across workers that share the same
   read-only table image.

#### 3A.3.0 Hash-family pluggability (normative)

A deployment may select among approved hash families, including but not
limited to:

- multiplicative-XOR baseline,
- modern fast non-cryptographic families,
- schema-pinned perfect or minimal-perfect layouts for static or
  semi-static tables,
- stronger adversarially resistant heads.

Normative requirements:

1. the chosen family must be recorded in `backend_family`,
2. any change in hash family, seed policy, or key-layout assumptions
   creates a new migration-bearing schema / backend version,
3. different families may coexist across heads only if replay identity
   remains deterministic and auditable,
4. a safe baseline family must remain available for fallback.

#### 3A.3.1 Reference baseline family (Appendix-B-aligned reference detail)

The current reference baseline is **order-sensitive multiplicative-XOR
hashing**.

For a key with integerized components \(i_0, i_1, \dots, i_{n-1}\),
head \(h\) computes:

\[
\mathrm{hash}_h(i_0,\dots,i_{n-1})
=
\left(
\bigoplus_{p=0}^{n-1} (c_{p,h} \cdot i_p)
\right)
\bmod M
\]

Reference-baseline requirements:

1. `c_{p,h}` are odd integers,
2. multipliers differ across positions,
3. every head uses an independent multiplier set,
4. the multiplier set must be reproducibly generated from a
   schema-version-pinned seed or generation rule, so that baseline
   configuration is not manual or operator-dependent.

These baseline rules apply to the reference family only; alternative
approved families may satisfy the normative core through different
mechanisms.

#### 3A.3.2 Multi-head collision mitigation

L2M mitigates collisions by retrieving across multiple independent
heads:

\[
r_t^{\mathrm{lookup}} = \mathrm{concat}(v_{t,1}, \dots, v_{t,H_M})
\]

Even if two distinct keys collide in one table, they should not
systematically collide across all heads.

Normative requirements:

- `collision_rate_ema` must be tracked continuously or on shadow audit,
- if collision pressure exceeds the L5 ceiling, the shield may force
  degraded mode or lookup bypass,
- L4 may propose table-count, table-width, head-dimension, or key-schema
  changes to reduce collisions.

#### 3A.3.3 Collision detection and semantic demotion (normative)

Collisions are allowed but may not silently corrupt witness semantics.
A conforming lookup implementation must provide a lightweight key check,
checksum, prefix match, or equivalent validation signal on retrieved
rows.

Normative requirements:

1. if a retrieved row fails its key check, the result must be treated as
   a miss or as a low-confidence hit,
2. collision pressure must demote effective retrieval confidence,
3. silent semantic collision is forbidden as a success case,
4. collision diagnostics must be exportable and replay-auditable,
5. shield policy may force degraded or bypass mode when collision
   pressure exceeds configured ceilings.

#### 3A.3.4 Optional adversarial-resistance head

For high-trust or adversarial deployments, L4 may promote or L5 may
require at least one stronger or cryptographic hash head. This is
optional by default, but when enabled it must remain schema-versioned,
deterministic, and auditable.

### 3A.4 Context-aware gating and local mixing

Raw lookup is not self-authorizing. Retrieved memory must be filtered by
context-aware gating before it influences the recurrent stream.

Let \(h_t^{\mathrm{ctx}}\) be the current contextual state at position or
packet \(t\). Let the retrieved vector be projected to a key and value:

\[
k_t^{M} = W_K r_t^{\mathrm{lookup}},
\qquad
v_t^{M} = W_V r_t^{\mathrm{lookup}}
\]

Define the gate score:

\[
\alpha_t
=
\sigma\Bigl(
\langle \mathrm{RMSNorm}(h_t^{\mathrm{ctx}}),
\mathrm{RMSNorm}(k_t^{M}) \rangle + b_g
\Bigr)
\]

and the gated value:

\[
\tilde{v}_t^{M} = \alpha_t \cdot v_t^{M}
\]

Normative gating rules:

1. Gate values must lie in \([0,1]\).
2. If the gate does not fire, retrieval must not contaminate the hidden
   state.
3. Gating must be bounded and stable under lookup bypass.
4. RMS-style normalization or an equivalent bounded normalizer is
   required before the gating dot product in the reference
   implementation.

#### 3A.4.1 Short local mixing

After gating, the substrate may optionally apply a short local mixing
operator along the packet or sequence axis:

\[
y_t^{M} = \mathrm{Mix}_{\mathrm{local}}(\tilde{v}_{t-w:t}^{M})
\]

where the reference implementation uses:

- depthwise causal convolution,
- short kernel (e.g. 3-7),
- SiLU or equivalent light nonlinearity,
- residual preservation.

This operator is intended only to:

- widen the receptive field slightly,
- add limited nonlinearity,
- preserve low compute.

Additional normative restrictions:

1. `Mix_local` must be **stateless with respect to the global sequence**
   beyond its explicit local window,
2. `Mix_local` must not depend on recurrent hidden state or future
   hidden-state guesses,
3. `Mix_local` may only transform retrieved / gated memory values,
4. residual preservation is required,
5. global dense mixing is forbidden at L2M.

### 3A.5 Prefetch, placement, and execution order

L2M is designed for fast-local-memory operation with deterministic CPU fallback.

Normative semantics:

1. Embedding / value tables may live in fast local memory, including CPU RAM, unified memory, or accelerator-local memory, provided a deterministic CPU fallback path exists.
2. Lookup indices may be computed as soon as the typed witness key is
   available.
3. Prefetch may overlap with earlier computation, provided determinism is
   preserved.
4. The substrate must expose a bounded timeout after which retrieval is
   treated as absent rather than stalling the recurrent loop.

Recommended placement:

- lookup should occur **after** minimal contextualization exists,
- lookup injection should occur **before** the most expensive recurrent
  reasoning stage that would otherwise reconstruct the same fact.

Normative placement anchor for the reference stack:

- perform lookup **after L1 extraction and initial context projection**,
- inject lookup-backed witness memory **before the main L2 gated
  recurrent update**.

This replaces the vaguer “early-but-not-first” wording with an explicit
control-flow anchor while still allowing alternate implementations to
respect the same semantic placement.

### 3A.5A Value lifecycle, update, and eviction semantics (normative)

L2M must define how values are written, refreshed, aged, and removed.
This is part of the contract because divergent value-lifecycle choices
create semantic drift even when keys and hashes are identical.

Admissible policy families include:

- `offline_refresh_only`
- `bounded_online_update`
- `registry_derived_with_decay`
- `hybrid_refresh`

Normative requirements:

1. the active lifecycle policy must be recorded in
   `value_update_policy`,
2. every stored value must carry staleness metadata sufficient to
   determine whether it is fresh, stale, or expired under policy,
3. online updates, if enabled, must be bounded by an explicit learning
   rate or bounded write budget,
   and their gradients or write-deltas must be gated by active L3 / L5
   policy and a per-step write budget,
4. evictions must be governed by a versioned policy and may use TTL,
   tombstones, recency, frequency, or explicit invalidation,
5. replay-deterministic evaluation must either freeze the underlying
   value image or pin the exact update log / snapshot used during replay,
6. family disable, schema migration, or semantic reinterpretation must
   define what happens to old values: ignore, tombstone, migrate, or
   garbage-collect.

### 3A.5B Minimal consistency rules for online and offline refresh

If the backend is read-mostly with offline refresh:
- the active snapshot ID must be recorded,
- refresh cutovers must occur only at explicit boundaries.

If bounded online update is enabled:
- writes must be auditable,
- write bursts must be budgeted,
- stale / conflicting values must be resolvable by policy rather than by
  undefined last-write-wins behavior.

### 3A.6 Null / absent semantics

A missing, timed-out, shield-blocked, or stale lookup must be treated as
an allowed no-op.

If lookup is unavailable:

- the recurrent path must still function,
- `bypass_mode` is set appropriately,
- L5 may force `degraded` or `full_bypass`,
- L3 must treat lookup diagnostics as reduced evidence rather than as a
  reason to violate trust-region or shield constraints.

---

## 4. Family Decay Rates (Base Values)

| Family / Sector | \( \lambda_k \) | Rationale |
|---|---|---|
| `temporal_local` | 0.90 | Fast — lyrical echoes |
| `temporal_distant` | 0.98 | Slow — long-horizon autobiographical |
| `high_density` | 0.95 | Moderate — meta-object clusters |
| `social_anchored` | 0.92 | Moderate-fast — social callbacks |
| `callback_rich` | 0.96 | Slow — narrative callbacks |
| `cross_source` | 0.93 | Moderate — cross-source bridges |
| `motif_recurrence` | 0.97 | Slow — recurring thematic motifs |
| `low_evidence` | 0.85 | Very fast — noisy / uncertain |

Default for unknown families: \( \lambda = 0.94 \).

In the revised contract, L3 may change these only through **bounded
effective values**:

\[
\lambda_k^{\mathrm{eff}} \in
[\lambda_k^{\min}, \lambda_k^{\max}],
\qquad
\lambda_k^{\min} = \max(0.70, \lambda_k \cdot 0.85),
\qquad
\lambda_k^{\max} = \min(0.999, \lambda_k \cdot 1.10)
\]

These bounds may be tightened by L5.

---

## 5. L2 \(\Psi\) Update Map (Recap)

The seven-stage update (family mass, story axis, callbacks, drift,
regime evidence, sector trace, contradiction pressure) remains as
previously defined, but now uses **accepted effective hyperparameters**
supplied by L3 and may incorporate **gated L2M retrievals**.

Normative additions:

1. L2 must never consult unaccepted L3 candidate values.
2. L2 must never consume ungated lookup memory.
3. Lookup injection must be additive and bypass-safe.
4. If L2M is bypassed, recurrent semantics reduce to the v6 path.

---

## 6. L3 — Meta-Recurrent Witness / Event-Triggered Sparse Meta-Controller (\(\hat{W}_\tau\))

### 6.0 Purpose

L3 is the **slow controller** for L2 and the bounded online policy
controller for lookup usage. In v8 it remains explicitly **sparse,
selective, and cheap**:

- it updates only when a trigger policy fires,
- it estimates an improvement direction with a constant-cost reference
  estimator,
- it preserves the same bounded trust-region and acceptance semantics as
  v6,
- it may control a very small number of lookup policy knobs,
- it falls back to certified base behavior whenever evidence is weak.

L3 does not invent arbitrary new semantics and does not directly rewrite
architecture.

### 6.1 Controlled parameter vector

L3 controls only the following quantities:

\[
\theta_\tau =
\{\ell_{\lambda,k},\; \ell_\rho,\; b_g,\; \ell_B\}
\]

where:

\[
\ell_{\lambda,k} = \log\!\left(\frac{\lambda_k^{\mathrm{eff}}}{\lambda_k}\right),
\qquad
\ell_\rho = \operatorname{logit}(\rho^{\mathrm{eff}})
\]

and the additional lookup controls are:

- \(b_g\): lookup gate bias
- \(\ell_B\): lookup-budget control (e.g. max active heads or per-step
  lookup budget in bounded logit / log-space)

Equivalently,

\[
\lambda_k^{\mathrm{eff}} = \lambda_k \cdot \exp(\ell_{\lambda,k}),
\qquad
\rho^{\mathrm{eff}} = \sigma(\ell_\rho)
\]

L3 **must not** control:

- hidden dimensions,
- gate topology,
- family membership,
- table count,
- table width,
- schema version,
- key layout,
- short-conv kernel size.

Those belong to L4.

### 6.2 State fields

| Field | Symbol | Type | Default | Update / Bound | Description |
|---|---|---|---|---|---|
| `log_decay_offset` | \(\ell_\lambda\) | `dict[str, float]` | `{}` (all 0.0) | bounded | Log-offset per family relative to base \( \lambda_k \) |
| `callback_logit` | \(\ell_\rho\) | `float` | `0.0` | bounded | Logit of effective callback persistence |
| `lookup_gate_bias` | \(b_g\) | `float` | `0.0` | bounded | Bias for lookup gating |
| `lookup_budget_logit` | \(\ell_B\) | `float` | `0.0` | bounded | Bounded retrieval budget control |
| `meta_momentum` | \(m\) | `dict[str, float]` + scalar | `0.0` | EMA \( \beta_m = 0.9 \) | Smoothed update direction |
| `regime_posterior` | \(\hat{R}\) | `dict[str, float]` | `{}` | EMA \( 0.95 \), normalized | Evidence over regimes such as `stable`, `shifting`, `fragmented`, `contradictory` |
| `shadow_objective_ema` | \(\hat{J}\) | `float` | `0.0` | EMA \( 0.95 \) | Smoothed L5-aligned objective proxy |
| `prediction_error_ema` | \(\hat{E}\) | `float` | `0.0` | EMA \( 0.95 \) | Mismatch between predicted and observed effect of L3 changes |
| `controller_confidence` | \(\hat{c}\) | `float` | `0.0` | derived, in \([0,1]\) | Scales how much of the candidate update may be applied |
| `update_trigger_state` | \(T\) | `dict` | `{}` | bounded | Drift detector / trigger-policy state |
| `last_trigger_step` | — | `int` | `0` | monotonic | Last step at which L3 actually ran |
| `trigger_cooldown_remaining` | — | `int` | `0` | \(\ge 0\) | Prevents back-to-back expensive L3 runs |
| `skip_reason` | — | `str \| null` | `null` | enum | Reason the current trigger window was skipped |
| `accepted_updates` | \(n_a\) | `int` | `0` | monotonic | Number of accepted L3 updates |
| `rejected_updates` | \(n_r\) | `int` | `0` | monotonic | Number of rejected L3 updates |
| `skipped_epochs` | \(n_s\) | `int` | `0` | monotonic | Number of trigger windows skipped |

### 6.3 Epoch summary metrics

At the end of a triggerable window, L3 forms an epoch summary vector
\(m_\tau\) over the recent trajectory:

\[
m_\tau =
\{
u_k,\; s_\tau,\; c_\tau,\; q_\tau,\; v_\tau,\; \Delta J_\tau,
\chi_\tau,\; h_\tau,\; g_\tau\}
\]

with:

- \(u_k\): average usage / occupancy of family \(k\)
- \(s_\tau\): switch rate (storyboard or regime boundaries per step)
- \(c_\tau\): contradiction pressure rate
- \(q_\tau\): callback resolution rate
- \(v_\tau\): constraint-violation rate reported by L5 monitors
- \(\Delta J_\tau\): change in shadow objective relative to previous
  accepted controller state
- \(\chi_\tau\): lookup collision pressure
- \(h_\tau\): effective lookup hit rate
- \(g_\tau\): lookup gate fire rate

The shadow objective remains an L5-aligned proxy:

\[
J_\tau^{\mathrm{shadow}} =
J_\tau^{\mathrm{L5}}
- \alpha_{\theta}\|\theta_\tau - \theta_{\tau-1}\|_2^2
- \alpha_M \cdot \mathrm{lookup\_cost}_\tau
\]

where `lookup_cost` may include latency, bypass pressure, collision
pressure, and memory-transfer overhead. Shadow scores are comparable
only within the same objective bundle.

### 6.3A Update trigger policy (normative)

L3 runs only when the `UpdateTriggerPolicy` fires.

A trigger may fire when one or more of the following exceed L5-approved
thresholds:

- contradiction-pressure surge,
- storyboard / regime switch surge,
- callback backlog growth,
- lookup gate fire collapse,
- lookup collision surge,
- persistent objective degradation,
- explicit audit interval expiry.

A trigger policy must define:

- detector family,
- thresholds,
- cooldown,
- minimum replay size,
- fallback action if evidence is insufficient.

### 6.3B Reference estimator semantics

The reference estimator is `spsa_meta_estimator`.

For a perturbation vector \(\Delta_\tau\) with independent symmetric
components:

\[
g_\tau^{\mathrm{SPSA}}
=
\frac{J(\theta_\tau + c_\tau \Delta_\tau) - J(\theta_\tau - c_\tau \Delta_\tau)}{2c_\tau}
\odot \Delta_\tau^{-1}
\]

Normative requirements:

1. SPSA is the reference estimator for the reference implementation.
2. Finite difference remains the certified fallback.
3. Trigger windows with insufficient evidence may skip or zero-update.
4. The estimator must preserve the same trust-region, acceptance, and
   diagnostic semantics as in v6.

#### 6.3B.1 Optional learned surrogate controller (normative opt-in)

Once sufficient `MetaDiagnostics` history exists, an implementation may
introduce a tiny learned surrogate for L3 proposal generation, provided
that all of the following remain true:

1. the surrogate preserves the same diagnostics surface as the baseline
   estimators,
2. SPSA or finite-difference fallback remains available at all times,
3. acceptance, rejection, trust-region, and shield-veto semantics remain
   unchanged,
4. replay evaluation remains the source of truth for acceptance,
5. the surrogate may be disabled by policy without changing controller
   state semantics.

The learned surrogate is therefore an optimization path, not a semantic
authority.

### 6.3.1 MetaDiagnostics telemetry (normative)

Every L3 control event must emit a versioned `MetaDiagnostics` record,
whether accepted, rejected, skipped, or bypassed.

A `MetaDiagnostics` record must contain at minimum:

- `diagnostic_id`, `epoch_step_count`, `timestamp`
- `estimator_id`, `estimator_version`
- `objective_version`, `objective_hash`, `reducer_version`,
  `metric_bundle_hash`, and derived `objective_bundle_hash`
- `replay_spec_hash`, `seed`
- `active_coordinates`
- `gradient_estimate`
- `gradient_noise_estimate`
- `meta_momentum`
- `candidate_update`
- `controller_confidence`
- `coverage_ratio`, `telemetry_coverage`, `objective_dispersion`
- `lookup_collision_rate`, `lookup_hit_rate`, `lookup_gate_fire_rate`
- `sufficient_evidence`
- `acceptance_decision`
- `rejection_reasons`

`rejection_reasons` must draw from a fixed enum that includes at least:

- `low_coverage`
- `low_confidence`
- `hard_violation`
- `objective_regression`
- `shield_block`
- `policy_freeze`
- `stale_objective_bundle`
- `estimator_failure`
- `lookup_bypass`

### 6.4 Candidate update function \(\Omega\)

L3 computes a **candidate** update on a reduced or locked shadow replay
buffer. The contract remains estimator-agnostic as long as the
implementation respects the semantics below.

#### 6.4.1 Local improvement signal

For each controlled parameter \(\theta_i\), compute or estimate a local
improvement signal \(g_{\tau,i}\).

Acceptable implementations include:

- SPSA,
- finite difference fallback,
- hypergradient approximation,
- a learned surrogate only if it preserves v7 diagnostics and fallback
  semantics.

#### 6.4.2 Momentum and clipping

\[
m_{\tau,i} =
\beta_m m_{\tau-1,i} +
(1-\beta_m)\,\mathrm{clip}(g_{\tau,i}, -g_{\max}, g_{\max})
\]

#### 6.4.3 Confidence gating

The controller confidence is derived from telemetry coverage,
prediction error, and lookup-health diagnostics:

\[
\hat{c}_\tau =
\mathrm{clip}\!\left(
1 - \frac{\hat{E}_\tau}{\sigma_J + \epsilon}
- \alpha_\chi \hat{\chi}_\tau,
0,
1
\right)
\]

If telemetry coverage is below minimum, or if L5 shield policy places
lookup in `full_bypass`, confidence for lookup-affecting coordinates is
forced to zero.

#### 6.4.4 Trust-region candidate

\[
\theta_{\tau+1}^{\mathrm{cand}} =
\Pi_{\mathcal{T}(\theta_\tau, \Delta_{\max})}
\left(
\theta_\tau + \eta_\tau \hat{c}_\tau m_\tau
\right)
\]

The trust region is:

\[
\|\theta_{\tau+1}^{\mathrm{cand}} - \theta_\tau\|_\infty \le \Delta_{\max}
\]

Recommended defaults:

- \( \Delta_{\max,\lambda} = 0.03 \) in log-space per event
- \( \Delta_{\max,\rho} = 0.15 \) in logit-space per event
- \( \Delta_{\max,b_g} = 0.20 \) per event
- \( \Delta_{\max,B} = 0.15 \) in budget-logit space per event

#### 6.4.4A Default SPSA perturbation scales (reference defaults)

The reference implementation must use parameter-specific perturbation
scales. Recommended defaults are:

- `log_decay_offset`: `c_lambda = 0.010`
- `callback_logit`: `c_rho = 0.040`
- `lookup_gate_bias`: `c_gate = 0.050`
- `lookup_budget_logit`: `c_budget = 0.040`

These defaults may be tightened by L5 policy or adapted slowly from
diagnostic history, but they may not be replaced by a single global
perturbation scale.

#### 6.4.5 Reference fallback semantics

The reference implementation must ship both:

- `spsa_meta_estimator`
- `finite_difference_meta_estimator`

The fallback order is:

1. SPSA if trigger fired and evidence suffices
2. finite difference if SPSA diagnostics indicate instability or sparse
   active coordinates require direct probing
3. zero-update if neither path has sufficient evidence

### 6.5 Acceptance, rejection, and fallback

L3 updates are never applied directly from candidate computation. They
are subject to an acceptance gate.

#### 6.5.1 Acceptance condition

Accept the candidate iff all of the following hold:

1. **Objective non-regression**
2. **No hard constraint violation**
3. **Sufficient confidence**
4. **Sufficient evidence**
5. **Fresh objective bundle and replay identity**
6. **No shield veto on lookup-affecting coordinates**

If accepted:

- apply accepted controller state,
- increment `accepted_updates`,
- persist diagnostics.

#### 6.5.2 Rejection rule

If rejected:

- keep previous values or relax toward base:

\[
\theta_{\tau+1} = (1-\kappa)\theta_\tau + \kappa\theta_{\mathrm{base}}
\]

- increment `rejected_updates`,
- persist rejection diagnostics.

### 6.6 Effective L2 and lookup hyperparameters

The accepted values are used during the next online interval:

\[
\lambda_k^{\mathrm{eff}} =
\mathrm{clip}\left(
\lambda_k \exp(\ell_{\lambda,k}),
\lambda_k^{\min},
\lambda_k^{\max}
\right)
\]

\[
\rho^{\mathrm{eff}} =
\mathrm{clip}\left(
\sigma(\ell_\rho),
\rho^{\min},
\rho^{\max}
\right)
\]

\[
b_g^{\mathrm{eff}} \in [b_g^{\min}, b_g^{\max}],
\qquad
B^{\mathrm{eff}} = \sigma(\ell_B)
\]

Lookup policy must remain bounded, and shield policy may further clamp
or override `b_g` and `B`.

### 6.7 Null / absent semantics

A fresh L3 state has:

- all log-offsets at `0.0`
- `callback_logit = 0.0`
- `lookup_gate_bias = 0.0`
- `lookup_budget_logit = 0.0`
- `meta_momentum = 0`
- `controller_confidence = 0`

If L3 is disabled or confidence is zero, effective values fall back to
base L2 parameters and base lookup policy.

---

## 7. L4 — Architectural Witness / Screened Proposal-Validation-Promotion Layer (\(\bar{W}_\mu\))

### 7.0 Purpose

L4 governs **architecture search and structural adaptation**, but only
through **versioned, validated, and reversible proposals**.

In v8, “architecture” explicitly includes both:

- recurrent structure,
- lookup-memory structure.

The live model is not allowed to self-mutate arbitrarily at runtime.
Structural changes are higher-risk than hyperparameter tuning and must
be promoted only after staged validation.

### 7.1 Admissible search space

L4 may propose deltas only in the approved search space
\( \mathcal{A} \). By default, \( \mathcal{A} \) includes:

1. enabling or disabling a witness family already known to the registry,
2. adjusting gate-feature mixing coefficients,
3. pruning persistently low-value / high-cost families,
4. changing sparsity masks or low-rank adapter widths,
5. changing routing coefficients among existing modules,
6. changing lookup `table_count`, `table_width`, `value_dim_per_head`,
   or `ngram_orders`,
7. changing short local mixing kernel size or head-enable masks,
8. changing lookup placement stage,
9. changing typed key schema or value schema **only with migration**,
10. changing prefetch budget, cache policy, or degraded-mode policy.

L4 may **not** perform the following as online self-modification:

- hidden-state dimension changes without migration,
- tensor shape changes that break serialization,
- state-schema changes without explicit migration,
- key-schema changes that invalidate historical meaning without
  migration,
- semantic reinterpretation of an existing witness family without
  explicit approval.

#### 7.1A Family-disable interaction with lookup memory (normative)

If a witness family is disabled, pruned, or semantically retired:

1. associated lookup keys may remain physically stored until eviction,
   migration, or garbage collection,
2. live retrievals associated with that family must be ignored, gated to
   zero, or treated as shield-blocked,
3. no disabled family may continue to influence the live recurrent path
   through stale lookup alone,
4. the active value lifecycle policy must specify whether affected rows
   are tombstoned, lazily evicted, migrated, or archived.

### 7.1.1 StateMigrationPlan (normative)

Any proposal that changes state layout, tensor shapes, checkpoint
schema, key schema, or lookup table schema must include a versioned
`StateMigrationPlan`.

It must contain:

- `plan_id`, `version`, `plan_hash`
- `from_generation`, `to_generation`
- `from_schema_version`, `to_schema_version`
- `transform_ref` and `transform_hash`
- `dry_run_replay_spec_hash`
- `forward_compat_checks`
- `rollback_restore_ref`
- `sentinel_ids`
- `defaulting_rules`, `dropped_fields`, `new_fields`
- `rollback_compatible`

Any material change creates a new `plan_hash` and invalidates prior
approvals.


### 7.2 State fields

| Field | Symbol | Type | Default | Description |
|---|---|---|---|---|
| `family_value_ema` | \(\bar{v}\) | `dict[str, float]` | `{}` | Estimated utility of each family |
| `family_cost_ema` | \(\bar{c}\) | `dict[str, float]` | `{}` | Estimated cost contribution |
| `gate_importance_ema` | \(\bar{\gamma}\) | `dict[str, float]` | `{}` | Importance of each L2 feature to each gate / route |
| `lookup_head_value_ema` | — | `dict[str, float]` | `{}` | Utility estimate per lookup head |
| `lookup_head_cost_ema` | — | `dict[str, float]` | `{}` | Cost estimate per lookup head |
| `collision_proxy_ema` | — | `float` | `0.0` | Cheap proxy for hash collision pressure |
| `candidate_queue` | — | `list[ArchitectureDeltaProposal]` | `[]` | Pending deltas awaiting validation |
| `shadow_eval_history` | — | `list[ArchitectureEvalRecord]` | `[]` | Validation results for candidate vs incumbent |
| `incumbent_generation` | \(\bar{g}\) | `int` | `0` | Active promoted architecture version |
| `rollback_generation` | — | `int \| null` | `null` | Most recent rollback-safe version |
| `promotion_budget` | \(\bar{B}\) | `int` | `1` | Maximum promotions currently available |
| `promotion_health_ema` | \(\bar{h}\) | `float` | `0.0` | Smoothed post-promotion health signal |
| `rollback_rate_ema` | \(\bar{r}\) | `float` | `0.0` | Smoothed rollback frequency |
| `last_promotion_sequence` | — | `int` | `0` | Sequence index of most recent promotion |

### 7.3 Evaluation objective

L4 does not optimize raw reward alone. It evaluates candidates using an
L5-approved score:

\[
S_\mu(d) =
\mathbb{E}[J_{\mathrm{shadow}}^{\mathrm{L5}} \mid d]
- \beta_{\mathrm{cx}} \cdot \mathrm{complexity}(d)
- \beta_{\chi} \cdot \mathrm{collision}(d)
- \beta_{L} \cdot \mathrm{latency}(d)
\]

subject to all hard constraints from L5.

Hard constraints are checked explicitly and are never “paid for” with a
higher score.

### 7.3.1 ScreeningStageSpec (normative)

Before expensive shadow replay, every candidate must pass a cheap
screening stage.

A `ScreeningStageSpec` contains at minimum:

- `spec_id`, `version`
- deterministic `seed`
- small replay subset or probe suite
- proxy metrics to compute
- objective bundle identity
- stage budget

Required screening proxies include at least:

- projected latency delta,
- projected memory delta,
- lookup collision proxy,
- lookup hit-rate proxy,
- gate-fire proxy,
- recurrent ablation or routing proxy,
- sentinel smoke results if configured.

Only the top `K_finalists` candidates may proceed to full replay.

#### 7.3.1A Screening-proxy audit requirement (normative)

Cheap screening is allowed only while its proxy ranking remains
meaningfully correlated with full replay outcomes.

Normative requirements:

1. correlation between screening proxy scores and full locked replay
   scores must be audited periodically,
2. the active policy must define both a target and a floor correlation,
3. if correlation drops below the hard floor, screening must be disabled,
   retrained, or routed to a safer reduced role,
4. audit artifacts must be retained with the same objective-bundle and
   replay-identity discipline used elsewhere in the contract.

Default contract values appear in the budgets table in §1.1.

Additional normative requirements:

5. proxy audits must run at least every `N_promotions_audit = 5`
   promotions or every `N_windows_audit = 20` screening windows,
   whichever comes first,
6. each audit must use at least `N_pairs_min = 500` paired screening /
   full-replay comparisons unless the deployment is too small to supply
   that many candidates, in which case the shortfall must be logged,
7. screening must track not only score correlation but also a ranking-
   stability or simple-regret metric over time,
8. if screening is under retraining or disabled, candidates must route
   directly to the safer evaluation path rather than silently using stale
   proxy weights.

### 7.3.2 ShadowReplaySpec (normative)

Every promotion-eligible L4 evaluation must be driven by a versioned
`ShadowReplaySpec`.

Candidate and incumbent are not allowed to choose their replay material
independently; they must be evaluated against the same materialized plan.

In v8, `ShadowReplaySpec` additionally records:

- required lookup fixtures,
- key-schema version,
- lookup bypass policy used during replay,
- collision-audit mode,
- prefetch normalization version.

### 7.4 Update function \(\Xi\)

#### 7.4.1 Telemetry aggregation

Update family and lookup telemetry EMAs from recent sequences.

Recommended statistics include:

- family average activation / mass,
- marginal contribution to objective proxy,
- latency delta,
- memory delta,
- gate sensitivity,
- lookup collision proxy,
- lookup gate fire rate,
- lookup hit rate,
- bypass incidence.

#### 7.4.2 Candidate generation

L4 may generate proposals such as:

- `prune_family(f)`
- `enable_family(f)`
- `adjust_gate_mix(g, j, delta)`
- `increase_adapter_rank(block, delta)`
- `tighten_sparse_mask(block)`
- `increase_lookup_heads(delta)`
- `resize_lookup_tables(delta)`
- `change_lookup_order([1,2] -> [1,2,3])`
- `move_lookup_stage(stage_a -> stage_b)`
- `change_short_conv_kernel(k)`
- `alter_prefetch_budget(delta)`

Candidate generation may use:

- ablation sweeps,
- bandit-style exploration,
- BOHB / Hyperband-style racing,
- replay-based heuristics,
- shared-scaffold or weight-sharing methods,
- constrained differentiable search.

#### 7.4.3 Staged evaluation

For each proposal \(d \in \mathcal{A}\):

1. cheap screening,
2. multi-fidelity replay racing on progressively larger budgets,
3. full locked shadow replay for finalists,
4. shield and sentinel verification,
5. approval path if required.

#### 7.4.4 Promotion rule

Promote candidate \(d^*\) only if:

\[
S_\mu(d^*) - S_\mu(d_{\mathrm{inc}}) \ge \delta_{\mathrm{promote}}
\]

and:

- hard constraints are satisfied,
- sentinel suite passes,
- promotion budget is available,
- required approvals are present,
- the recorded `objective_bundle_hash` and `replay_spec_hash` match,
- the shield authorizes the promotion path.

Promotion is atomic and occurs only at a sequence boundary.

#### 7.4.5 Adaptive promotion budget

Budget semantics remain as in v6, but repeated lookup regressions
(collision spikes, bypass spikes, or lookup-latency violations) also
reset budget to `base_budget`.

### 7.5 Rollback rule

If the promoted architecture regresses on post-promotion monitoring for
\(R\) consecutive windows, or any hard invariant is violated, the system
must rollback to `rollback_generation`.

Rollback is mandatory, not advisory.

### 7.6 Optional shared scaffold semantics

Lookup-memory proposals may optionally be evaluated in a shared scaffold
where recurrent and lookup blocks reuse common trained parameters and
only structural switches differ. Shared-scaffold evaluation is allowed
only if:

- score comparison remains bundle-consistent,
- shadow replay remains deterministic,
- migration and rollback remain well-defined.

### 7.7 L4 constraints

1. `promotion_budget` must remain within the L5 policy range.
2. No live shape changes without schema migration.
3. Every promoted delta must have validation record, incumbent score,
   candidate score, snapshot ID, generation ID, and
   `objective_bundle_hash`.
4. Total active family count must never exceed the L5 constraint
   `max_families`.
5. Any unresolved blocking coverage deficit blocks promotion unless a
   degraded-coverage path is explicitly authorized by L5.
6. Lookup-schema-changing proposals require a valid migration plan and
   dry-run report.
7. Candidates and incumbents must use the same materialized replay,
   lookup fixture set, and objective bundle.

---

## 8. L5 — Cosmological Witness / Governance Shield Layer (\(\breve{W}\))

### 8.0 Purpose

L5 encodes the formal contract for the whole self-modifying system.
It answers five questions:

1. What is the system trying to optimize?
2. What may never be violated?
3. Which changes may be applied automatically, and which require
   explicit approval?
4. When must the system bypass lookup or rollback structure?
5. What is the safe fallback controller / architecture?

L5 is a **compiled governance shield**, not a heavy online optimizer.

### 8.0A Runtime mode model (normative)

At runtime the shield must be in exactly one of three modes:

| Mode | Meaning | Allowed dominant actions |
|---|---|---|
| `normal` | all major budgets healthy | bounded L3 and staged L4 allowed |
| `degraded` | one or more budgets marginal | clamp L3, reduce lookup budget, freeze risky L4 |
| `bypass` | memory path or safety state unhealthy | bypass lookup, clamp L3, freeze L4, optionally rollback |

Mode transitions must be triggered by measurable inputs and logged as
first-class control events.

### 8.1 Formal contract

Let the full system state be:

\[
x_t = (S_t, h_t, \theta_t, M_t, \mathrm{arch}_t)
\]

Define the feasible set:

\[
\mathcal{F} =
\left\{
 x_t :
 I_i(x_t) = \mathrm{True}\ \forall i,
 \quad
 c_j(x_t) \le B_j\ \forall j
\right\}
\]

where:

- \(I_i\) are hard invariants,
- \(c_j\) are measurable resource / safety costs,
- \(B_j\) are hard budgets.

The objective is lexicographic:

1. **Maintain feasibility**
2. **Maximize approved utility**
3. **Minimize unnecessary complexity / churn**

### 8.1A Shield / Simplex semantics (normative)

L5 must provide a runtime shield capable of forcing one of the following
safe fallback regimes:

1. base L2 + full lookup bypass,
2. base L2 + degraded lookup,
3. accepted L2 + lookup bypass,
4. incumbent architecture rollback.

The shield may override L3 and veto L4 promotions, but it may not write
new unapproved structure.

### 8.2 State fields

| Field | Symbol | Type | Description |
|---|---|---|---|
| `primary_objective` | \(\breve{\mathcal{J}}\) | functional / DSL string | Human-readable main utility function |
| `objective_version` | — | `str` | Version tag for objective implementation |
| `objective_hash` | — | `str` | Hash of the executable objective implementation |
| `reducer_version` | — | `str` | Version tag for reducer / aggregation logic |
| `metric_bundle_hash` | — | `str` | Hash of metric composition, normalization, and comparison rules |
| `soft_terms` | \(w\) | `dict[str, float]` | Secondary reward terms and regularizers |
| `hard_constraints` | \(\breve{C}\) | `dict[str, bound or predicate]` | Non-negotiable resource and safety constraints |
| `invariant_set` | \(\breve{\mathcal{I}}\) | `set[Predicate]` | Properties that must hold at all times |
| `approval_policy` | \(\breve{A}\) | `dict` | Rules for auto-apply vs shadow-only vs operator approval |
| `trust_region_policy` | \(\breve{T}\) | `dict` | Maximum allowed L3 drift and L4 promotion frequency |
| `promotion_budget_policy` | — | `dict` | Base / max promotion budgets and replenishment rules |
| `shadow_replay_policy` | \(\breve{R}\) | `dict` | Rules for replay size, coverage quotas, synthetic fallback, and degraded-coverage handling |
| `lookup_policy` | — | `dict` | Bounds on lookup heads, RAM budget, gating policy, prefetch budget, and bypass thresholds |
| `sentinel_suite` | \(\breve{Q}\) | `list[...]` | Version-pinned sentinels that must not regress |
| `violation_policy` | \(\breve{V}\) | `dict` | Freeze / rollback / halt / bypass actions when constraints are breached |

### 8.2.1 Objective bundle and score comparability

The objective bundle semantics from v6 remain unchanged and apply to all
L3, L4, and L2M artifacts.

### 8.2.2 Sentinel suite formalisation

The sentinel semantics from v6 remain unchanged. v7 additionally allows
lookup-specific sentinels such as:

- high-collision stress,
- lookup-bypass recovery,
- callback-anchor retention,
- entity grounding integrity.

### 8.3 Hard vs. soft semantics

#### Hard semantics

These must hold continuously or at required evaluation boundaries:

- memory limit
- latency limit
- maximum family count
- serialization / schema compatibility
- invariant predicates such as `no_silent_coercion`
- maximum lookup RAM budget
- maximum lookup latency budget
- maximum collision-rate ceiling
- bounded prefetch queue memory
- maximum key-construction latency budget

#### Soft semantics

These may be traded off inside the feasible set:

- storyboard coherence
- callback resolution
- hyperparameter smoothness
- architecture simplicity
- lookup recall coverage
- lookup efficiency
- exploration preference

### 8.4 Interaction with lower levels

- **L2M bounds:** L5 supplies admissible lookup budgets, bypass rules,
  collision ceilings, and safe degraded modes.
- **L3 bounds:** L5 supplies admissible controller bounds for both
  recurrent and lookup policy parameters.
- **L4 approval:** L4 proposals are valid only if they pass shield and
  approval policy.
- **Freeze / rollback authority:** L5 may freeze L3, freeze L4,
  force lookup bypass, force rollback, or request operator intervention.
- **Objective bundle authority:** stale replay specs, stale approvals,
  and stale diagnostics are invalidated whenever the active objective
  bundle changes.

### 8.4.1 Operator approval workflow

The workflow remains as in v6. It now also applies to lookup-schema,
lookup-placement, and lookup-table-structure changes.

### 8.4.2 Risk-tiered approval and promotion budget policy

Default risk-tier guidance now additionally includes:

- `low`: head-enable-mask changes, prefetch-budget tuning, gate-bias
  defaults, minor kernel-size changes, or small lookup-width changes
  within hard budget.
- `medium`: table-count changes, moderate table-width changes,
  n-gram-order changes without schema break, or placement-stage changes.
- `high`: key-schema changes, lookup-schema migration, major RAM
  expansion, unresolved collision ceiling breach, or changes that alter
  witness meaning.

### 8.4.3 Shield runtime semantics (normative)

At runtime, the shield must evaluate at minimum:

- step-time budget,
- lookup-latency budget,
- lookup collision ceiling,
- prefetch queue ceiling,
- repeated lookup timeout frequency,
- hard invariant violations.

Possible actions include:

- `clamp_l3`
- `degrade_lookup`
- `bypass_lookup`
- `freeze_l4`
- `rollback_generation`
- `halt`

### 8.4.4 Simplex-style fallback semantics (normative)

The shield must maintain an explicitly identified fallback controller and
fallback architecture. Fallback must be restorable without learning-time
recomputation.

### 8.4.5 Minimal safe profile (normative starter profile)

A deployment may start in a deliberately conservative configuration
called the **minimal safe profile**. In this profile:

- L4 promotions are disabled,
- L3 may control only 2-3 coordinates,
- lookup starts in `degraded` mode by default,
- only a reduced head subset is active,
- fallback restore is exercised on startup or during smoke tests.

This profile is intended for first deployments, low-trust rollouts, and
CPU-constrained environments.

### 8.5 Default policy instance

The default instance below is a materialization of the budgets and SLO
registry in §1.1. If the two ever differ, the registry in §1.1 is
authoritative and the default instance must be regenerated.

```json
{
  "primary_objective": "storyboard_coherence",
  "objective_version": "storyboard_coherence@v4",
  "objective_hash": "sha256:obj-v8-9a1c4f6e2b70d1f3e4a5c67890123456789abcdeffedcba09876543210aa11bb",
  "reducer_version": "shadow_reducer@v3",
  "metric_bundle_hash": "sha256:metrics-v8-3c2d1e4f5a6b7081928374655647382910ffeeddccbbaa998877665544332211",
  "soft_terms": {
    "callback_resolution_rate": 0.10,
    "hyperparameter_smoothness": -0.02,
    "architecture_complexity": -0.01,
    "lookup_efficiency": 0.03
  },
  "hard_constraints": {
    "max_families": 20,
    "max_memory_mb": 512,
    "max_step_time_ms": 50,
    "max_lookup_ram_mb": 2048,
    "max_lookup_latency_us": 250,
    "max_collision_rate": 0.05,
    "max_prefetch_queue_mb": 64,
    "max_key_build_us": 100,
    "state_schema_compatibility": true
  },
  "approval_policy": {
    "l3_auto_apply": true,
    "l4_requires_shadow_eval": true,
    "medium_risk_auto_approve": false,
    "high_risk_requires_operator_approval": true,
    "degraded_coverage_review_requires_operator_approval": true
  },
  "trust_region_policy": {
    "max_l3_log_decay_step": 0.03,
    "max_l3_callback_logit_step": 0.15,
    "max_lookup_gate_bias_step": 0.20,
    "max_lookup_budget_logit_step": 0.15,
    "min_sequences_between_promotions": 10
  },
  "telemetry_schema_version": "telemetry@v1",
  "lookup_policy": {
    "base_head_count": 8,
    "max_head_count": 16,
    "max_ngram_order": 3,
    "bypass_on_collision_rate": 0.12,
    "bypass_on_timeout_rate": 0.10,
    "degraded_mode_head_count": 4,
    "prefetch_timeout_us": 400
  },
  "promotion_budget_policy": {
    "base_budget": 1,
    "max_budget": 3,
    "positive_windows_required": 2,
    "delta_health": 0.02,
    "rollback_rate_ceiling": 0.05
  },
  "shadow_replay_policy": {
    "min_sequences": 32,
    "min_steps": 2048,
    "recent_fraction": 0.50,
    "balanced_fraction": 0.30,
    "stress_fraction": 0.10,
    "fallback_strategy": "approved_synthetic_registry",
    "max_lookback_multiplier": 4,
    "degraded_coverage_requires_operator_approval": true
  },
  "sentinel_suite": [
    "stable_storyboard@v1",
    "high_contradiction_recovery@v1",
    "lookup_bypass_recovery@v1",
    "callback_anchor_retention@v1"
  ],
  "violation_policy": {
    "on_hard_violation": "rollback_and_freeze_l4",
    "on_repeated_l3_rejection": "decay_to_base",
    "on_lookup_collision_ceiling": "degrade_or_bypass_lookup"
  }
}
```

---

## 9. Extended architecture summary table

| Layer | Symbol | Object | Update Frequency | Modifies | Timescale |
|---|---|---|---|---|---|
| L1 | \(W_t\) | `WitnessSignature` | Per packet | — | Instantaneous |
| L2 | \(\tilde{W}_t\) | `RecurrentWitnessState` | Per packet | RNN gates / recurrent state flow | ~1–100 steps |
| L2M (historical alias L2.5) | \(M_t\) | `WitnessLookupMemory` | Per packet lookup + async maintenance | Hidden-state enrichment via retrieved witness facts | ~1–100 steps / async background |
| L3 | \(\hat{W}_\tau\) | `MetaRecurrentWitness` | Event-triggered | L2 and bounded lookup policy knobs | ~100–1000 steps |
| L4 | \(\bar{W}_\mu\) | `ArchitecturalWitness` | Maintenance / screening windows | Candidate recurrent and lookup structure deltas | ~10^3–10^6 steps |
| L5 | \(\breve{W}\) | `CosmologicalWitness` | Fixed / compiled / very slow | Feasible set, shield policy, approvals | System lifetime |

---

# Part B — Reference Bindings and Illustrative Artifacts

## 10. Integration points (reference implementation)

### 10.1 `CognitionState` (`state.py`)

Add explicit fields for higher-order control state and lookup state:

```python
recurrent_witness: dict = field(default_factory=dict)          # L2
lookup_witness: dict = field(default_factory=dict)             # L2M
meta_recurrent_witness: dict = field(default_factory=dict)     # L3
architectural_witness: dict = field(default_factory=dict)      # L4
cosmological_witness: dict = field(default_factory=dict)       # L5 policy snapshot / config
```

### 10.2 `CognitionLoop` (`loop.py`)

The loop now distinguishes:

1. object-witness extraction,
2. recurrent-state preparation,
3. lookup-key construction and prefetch,
4. gated lookup injection,
5. recurrent update,
6. event-triggered L3,
7. staged L4 only at maintenance windows.

Reference sketch:

```python
typed_key_bundle = build_witness_lookup_keys(packet, state.lookup_witness, policy)
prefetch_handle = prefetch_lookup_rows(typed_key_bundle, state.lookup_witness, policy)
retrieved_rows = resolve_lookup_rows(prefetch_handle, timeout_us=policy.lookup_timeout_us)
lookup_out, lookup_diag = gate_and_mix_lookup(state.hidden_ctx, retrieved_rows, state.lookup_witness, policy)
state.hidden = state.hidden + lookup_out
state.lookup_witness = update_lookup_diagnostics(state.lookup_witness, lookup_diag)
```

### 10.2.1 Meta estimator (`srnn/meta/estimator.py`)

The reference implementation must expose:

- `spsa_meta_estimator`
- `finite_difference_meta_estimator`

Both must conform to v8 diagnostics and fallback semantics.

### 10.2.2 Meta trigger module (`srnn/meta/triggers.py`)

New module responsible for:

- drift detection,
- contradiction / backlog trigger conditions,
- cooldown handling,
- lookup-health trigger inputs.

### 10.2.3 Meta diagnostics sink (`srnn/meta/diagnostics.py`)

Responsible for persisting `MetaDiagnostics` records and objective /
replay identity.

### 10.3 `RecurrentCell` (`rnn_cell.py`)

The cell consumes only:

- accepted effective hyperparameters,
- gated lookup output,
- shield-permitted lookup policy.

It must remain correct under lookup bypass.

### 10.3.0A `WitnessLookupBackend` reference contract

The reference stack should implement a backend abstraction that can
target fast local memory, including CPU RAM, unified memory, or accelerator-local memory, while still
supporting deterministic CPU fallback for replay and safe degraded-mode
operation.

### 10.3.1 Lookup modules (`srnn/memory/*.py`, reference implementation)

Required responsibilities:

- `hashing.py`: deterministic typed-key hashing
- `lookup.py`: multi-head retrieval and row assembly
- `gating.py`: RMS-normalized query/key gating and optional short mixing
- `prefetch.py`: asynchronous prefetch and timeout handling

### 10.4 Architecture manager (`srnn/architecture/manager.py`)

Responsibilities now include recurrent and lookup-memory proposals,
screening, replay racing, migration handling, promotion, snapshotting,
and rollback.

### 10.4.1 State migration (`srnn/architecture/state_migration.py`)

Must support migrations for recurrent state, lookup schema, and combined
checkpoint schema.

### 10.5 Constraint validator (`srnn/policy/constraints.py`)

Responsible for:

- hard constraint evaluation,
- sentinel checks,
- replay coverage checks,
- objective-bundle freshness,
- lookup collision ceilings,
- lookup latency ceilings,
- prefetch-queue ceilings.

### 10.5.1 Runtime shield (`srnn/policy/shield.py`)

Responsible for:

- forcing degraded / bypass lookup modes,
- clamping L3,
- freezing L4,
- invoking rollback,
- exposing certified fallback state.

### 10.6 LoopRanker / Monitoring (`ranking.py`, metrics)

L3 and L4 must consume an L5-approved reward proxy rather than ad hoc
metrics. Lookup-specific metrics are diagnostic features unless and until
explicitly included in the objective bundle.

---

## 10A. Telemetry Contract (Normative)

The witness system must emit a bounded-cardinality telemetry surface
sufficient to prove the major invariants and to support shield actions.

At minimum the active telemetry schema must export:

- recurrent step time,
- lookup latency,
- key-build time,
- timeout rate,
- hit rate,
- gate fire rate,
- collision rate,
- prefetch queue pressure,
- L3 controller confidence,
- L3 gradient-noise estimate,
- L4 screening-proxy correlation,
- rollback rate,
- current L5 runtime mode.

Telemetry rules:

1. every telemetry record must include `telemetry_schema_version`,
2. metric names must remain stable within a telemetry schema version,
3. cardinality must remain bounded,
4. alert thresholds must align with the active budget registry,
5. diagnostics must be retained across rollback windows.

## 11. Serialization formats

All JSON fragments in this section are illustrative but structurally realistic examples. Numeric limits in examples are aligned to the normative SLO registry in §1.1 unless explicitly marked otherwise.


### 11.1 L2M — `WitnessLookupMemory`

```json
{
  "backend_family": "xor-baseline-v1",
  "table_count": 8,
  "table_width": 1048576,
  "value_dim_per_head": 64,
  "ngram_orders": [1, 2],
  "schema_version": "lookup@v1",
  "telemetry_schema_version": "telemetry@v1",
  "lookup_gate_bias": 0.05,
  "lookup_budget_logit": -0.20,
  "head_enable_mask": [true, true, true, true, true, true, true, true],
  "collision_rate_ema": 0.031,
  "hit_rate_ema": 0.72,
  "gate_fire_rate_ema": 0.18,
  "prefetch_queue_depth_ema": 3.2,
  "lookup_latency_us_ema": 172.0,
  "bypass_mode": "off"
}
```

### 11.1A `LookupValueLifecyclePolicy`

```json
{
  "policy_id": "lookup-lifecycle@v1",
  "mode": "offline_refresh_only",
  "snapshot_id": "lookup-snapshot-2026-04-20-01",
  "staleness_horizon_s": 86400,
  "eviction_policy_version": "ttl-lru@v1",
  "online_write_budget_per_step": 0
}
```

### 11.1B `LookupDiagnostics`

```json
{
  "diagnostic_id": "lookup-2026-04-18-9921",
  "timestamp": "2026-04-18T23:17:00Z",
  "schema_version": "lookup@v1",
  "telemetry_schema_version": "telemetry@v1",
  "head_count": 8,
  "key_count": 3,
  "collision_rate": 0.028,
  "hit_rate": 0.75,
  "gate_fire_rate": 0.21,
  "timeout_rate": 0.01,
  "avg_latency_us": 166.4,
  "bypass_mode": "off"
}
```

### 11.2 L3 — `MetaRecurrentWitness`

```json
{
  "log_decay_offset": {
    "temporal_local": 0.02,
    "callback_rich": -0.01
  },
  "callback_logit": 0.35,
  "lookup_gate_bias": 0.05,
  "lookup_budget_logit": -0.20,
  "meta_momentum": {
    "temporal_local": 0.004,
    "callback_rich": -0.002,
    "__callback__": 0.010,
    "__lookup_gate__": 0.008,
    "__lookup_budget__": -0.003
  },
  "regime_posterior": {
    "stable": 0.74,
    "shifting": 0.18,
    "fragmented": 0.05,
    "contradictory": 0.03
  },
  "shadow_objective_ema": 0.81,
  "prediction_error_ema": 0.07,
  "controller_confidence": 0.84,
  "last_trigger_step": 12800,
  "trigger_cooldown_remaining": 0,
  "skip_reason": null,
  "accepted_updates": 11,
  "rejected_updates": 2,
  "skipped_epochs": 19
}
```

### 11.2A `MetaDiagnostics`

```json
{
  "diagnostic_id": "l3diag-2026-04-18-013",
  "epoch_step_count": 13,
  "timestamp": "2026-04-18T23:18:00Z",
  "estimator_id": "spsa_meta_estimator",
  "estimator_version": "spsa_meta_v1",
  "telemetry_schema_version": "telemetry@v1",
  "objective_version": "storyboard_coherence@v4",
  "objective_hash": "sha256:obj-v8-9a1c4f6e2b70d1f3e4a5c67890123456789abcdeffedcba09876543210aa11bb",
  "reducer_version": "shadow_reducer@v3",
  "metric_bundle_hash": "sha256:metrics-v8-3c2d1e4f5a6b7081928374655647382910ffeeddccbbaa998877665544332211",
  "objective_bundle_hash": "sha256:bundle-v8-1029384756abcdef1029384756abcdef1029384756abcdef1029384756abcd",
  "replay_spec_hash": "sha256:8b3f...",
  "seed": 41721,
  "active_coordinates": ["temporal_local", "callback_rich", "__lookup_gate__"],
  "gradient_estimate": {
    "temporal_local": 0.011,
    "callback_rich": -0.004,
    "__lookup_gate__": 0.018
  },
  "lookup_collision_rate": 0.031,
  "lookup_hit_rate": 0.72,
  "lookup_gate_fire_rate": 0.18,
  "controller_confidence": 0.84,
  "sufficient_evidence": true,
  "acceptance_decision": "accepted",
  "rejection_reasons": []
}
```

### 11.3 L4 — `ArchitecturalWitness`

```json
{
  "family_value_ema": {
    "temporal_local": 0.66,
    "callback_rich": 0.81
  },
  "family_cost_ema": {
    "temporal_local": 0.11,
    "callback_rich": 0.19
  },
  "lookup_head_value_ema": {
    "head_0": 0.48,
    "head_1": 0.51
  },
  "lookup_head_cost_ema": {
    "head_0": 0.03,
    "head_1": 0.03
  },
  "collision_proxy_ema": 0.027,
  "telemetry_schema_version": "telemetry@v1",
  "incumbent_generation": 6,
  "rollback_generation": 5,
  "promotion_budget": 1,
  "promotion_health_ema": 0.76,
  "rollback_rate_ema": 0.02,
  "last_promotion_sequence": 120
}
```

### 11.3A `ScreeningStageSpec`

```json
{
  "spec_id": "screen-2026-04-18-maint-01",
  "version": 1,
  "seed": 41721,
  "candidate_budget_steps": 256,
  "proxy_metrics": [
    "latency_delta",
    "memory_delta",
    "collision_proxy",
    "hit_rate_proxy",
    "gate_fire_proxy"
  ],
  "objective_bundle_hash": "sha256:bundle-v8-1029384756abcdef1029384756abcdef1029384756abcdef1029384756abcd",
  "finalist_count": 3
}
```

### 11.4 L5 — `CosmologicalWitness`

```json
{
  "primary_objective": "storyboard_coherence",
  "objective_version": "storyboard_coherence@v4",
  "objective_hash": "sha256:obj-v8-9a1c4f6e2b70d1f3e4a5c67890123456789abcdeffedcba09876543210aa11bb",
  "reducer_version": "shadow_reducer@v3",
  "metric_bundle_hash": "sha256:metrics-v8-3c2d1e4f5a6b7081928374655647382910ffeeddccbbaa998877665544332211",
  "objective_bundle_hash": "sha256:bundle-v8-1029384756abcdef1029384756abcdef1029384756abcdef1029384756abcd",
  "telemetry_schema_version": "telemetry@v1",
  "hard_constraints": {
    "max_families": 20,
    "max_memory_mb": 512,
    "max_step_time_ms": 50,
    "max_lookup_ram_mb": 2048,
    "max_lookup_latency_us": 250,
    "max_collision_rate": 0.05,
    "max_prefetch_queue_mb": 64,
    "max_key_build_us": 100
  },
  "lookup_policy": {
    "base_head_count": 8,
    "max_head_count": 16,
    "bypass_on_collision_rate": 0.12,
    "degraded_mode_head_count": 4
  },
  "violation_policy": {
    "on_hard_violation": "rollback_and_freeze_l4",
    "on_lookup_collision_ceiling": "degrade_or_bypass_lookup"
  }
}
```

---

## 12. Invariants (extended)

### 12.1 L2M invariants

1. Hashing and key canonicalization are deterministic within a schema version and consistent across process restarts and across distributed workers that share a read-only lookup table.
2. For backends using the multiplicative-XOR reference baseline, multiplier configuration is version-pinned and reproducible under the selected backend family.
3. Gate values are in \([0,1]\).
4. Lookup bypass does not invalidate recurrent execution.
5. Collision rate, timeout rate, key-build time, and lookup latency are measurable and shield-actionable.
6. Shield-forced bypass must override lookup injection.
7. Schema-changing lookup proposals require migration.

### 12.2 L3 invariants

1. All v6 controller invariants remain in force.
2. `lookup_gate_bias` and `lookup_budget_logit` remain within
   L5-approved bounds.
3. L3 may not change lookup schema or structure.
4. Lookup-affecting controller outputs may be zeroed by the shield.
5. Every L3 control event persists one `MetaDiagnostics` record.

### 12.3 L4 invariants

1. All v6 promotion and replay invariants remain in force.
2. Lookup-structure proposals require the same replay identity and
   bundle identity for incumbent and candidate.
3. Lookup-schema changes require a migration plan and approval.
4. Promotion budget resets on repeated lookup regressions as well as
   recurrent regressions.

### 12.4 L5 invariants

1. Hard constraints are never relaxed by soft objective improvement.
2. Every automatic change obeys `approval_policy`.
3. Every promoted architecture remains in the feasible set.
4. Lookup bypass and degraded mode are total policies, not undefined
   ad hoc behavior.
5. The shield always has an explicitly identified fallback state.

### 12.5 Control-artifact invariants

1. Every diagnostics and replay artifact includes the active objective
   bundle identity.
2. Lookup fixtures and key-schema versions are pinned for candidate vs
   incumbent comparisons.
3. Synthetic substitutions remain deterministic.
4. Approval records are invalid if bundle hash, replay hash, or proposal
   hash differ from the promoted delta.

---

## 13. Testing requirements (extended)

### 13.1 L2M unit tests (`test_lookup_witness.py`)

- the configured hash backend is deterministic within schema version and order-sensitive when the schema requires ordered keys;
- backend-specific baseline configuration is reproducible when a multiplier-based reference family is selected;
- multi-head retrieval or equivalent collision-mitigation logic reduces effective collision frequency;
- gate suppression prevents irrelevant retrieval injection;
- short local mixing preserves residual safety;
- timeout triggers degraded or bypass mode without stalling the loop;
- bypass mode preserves recurrent correctness.

### 13.2 L3 unit tests (`test_meta_witness.py`)

- event trigger policy fires only under configured conditions;
- SPSA reference estimator respects trust-region limits;
- finite-difference fallback is used only when required;
- low evidence forces zero-update or skip;
- lookup-affecting coordinates are clamped or zeroed under shield veto;
- diagnostics are emitted for accepted, rejected, skipped, and bypassed
  events.

### 13.3 L4 unit tests (`test_architectural_witness.py`)

- candidates are screened before full replay;
- multi-fidelity racing preserves deterministic ranking inputs;
- lookup-structure proposals use the same locked replay for incumbent
  and candidate;
- schema-changing proposals require migration and approval;
- repeated collision regressions reset promotion budget.

### 13.4 L5 unit tests (`test_cosmological_witness.py`)

- collision ceilings trigger degraded or bypass lookup;
- lookup-latency violations trigger shield actions;
- stale bundle artifacts are rejected;
- fallback controller / architecture are restorable;
- hard constraints veto otherwise higher-scoring candidates.

### 13.5 Integration tests

- L2M retrieval improves grounded witness behavior when keys are
  available and is harmless under bypass;
- L3 accepted updates affect L2 and lookup policy only through accepted
  state;
- L4 proposals are screened, replayed, then promoted only if L5
  approves;
- key-schema changes cannot promote without migration dry-run;
- hard lookup regressions trigger degraded mode or rollback;
- full system run with L1-L5 + L2M active maintains all invariants.

---



## Appendix A. Reference Baseline Details

This appendix records the current reference baseline choices for the default implementation. These details are informative for the reference build and are not the sole admissible realization of the normative core.

### A.1 Reference hash baseline
- backend family: `xor-baseline-v1`
- order-sensitive multiplicative-XOR hashing
- reproducible multiplier generation seeded from `schema_version` (the reference implementation must not require manual per-schema multiplier editing)
- independent per-head multiplier sets

### A.2 Reference gate normalizer
- RMS-style bounded normalizer before the gating dot product

### A.3 Reference local mixing
- short depthwise causal convolution
- light nonlinearity
- residual preservation

## Appendix B. Relation to Duotronics Framework

The revised hierarchy still maps cleanly onto the Duotronics layer
stack, with L2M acting as a practical memory substrate inside the
Potentiality / Observation boundary.

| Witness Component | Duotronics Layer | Role |
|---|---|---|
| L1 | Realization | Instantaneous signature |
| L2 | Potentiality | Continuity and short-term recurrent memory |
| L2M | Potentiality / Observation bridge | Cheap explicit associative memory |
| L3 | Observation (of L2 and L2M policy) | Bounded parameter adaptation / meta-control |
| L4 | Meta-Substrate | Versioned structural proposal and promotion |
| L5 | Meta-Meta-Substrate | Feasible-set law, shield, and approval policy |

---

## Appendix C. Cheap worker-side alternatives (Part VII)

v8 explicitly prefers cheap worker-side implementations where possible:

- quantized lookup tables,
- fast-local-memory witness value stores with deterministic CPU fallback,
- bitwise or integer-friendly hashing,
- bounded short-kernel local mixing,
- sparse event-triggered L3,
- staged L4 evaluation instead of uniform full replay.

Approximate implementations remain allowed only if they preserve:

- L3 trust-region semantics,
- L3 acceptance and fallback semantics,
- L5 shield authority,
- deterministic candidate vs incumbent comparison.

---

## Appendix D. Encyclopedia narrative mapping (extended)

| Witness Component | Narrative Analogy |
|---|---|
| L1 | Single scene beat |
| L2 | Scene / sequence continuity |
| L2M | The notebook of remembered names, motifs, and callback anchors |
| L3 | Editorial pacing and memory-tuning policy |
| L4 | Structural edit proposal, trial, and promotion |
| L5 | The publishing rules and safety checks that edits must obey |

---

## Appendix E. Implementation Hazard Warning

The most important implementation hazards in v8 are:

1. **expensive key construction** — if typed-key extraction becomes too
   heuristic or too slow, lookup no longer buys back compute,
2. **silent semantic collisions** — collisions must demote confidence or
   drop to miss semantics rather than contaminate state silently,
3. **stateful-mixing creep** — short local mixing must not expand into a
   second hidden recurrent model,
4. **screening drift** — L4 screening proxies that stop correlating with
   full replay must be disabled or retrained,
5. **portability leakage** — implementation choices must not silently
   redefine contract semantics.

These warnings are explanatory, but they name real operational failure
modes that implementers are expected to guard against.

## Appendix F. Non-normative design notes

The v8 stack is intentionally closer to:

- **hybrid explicit memory + learned recurrent computation** than pure
  latent-state accumulation,
- **cheap lookup for stable witness facts** than repeated recurrent
  reconstruction,
- **bounded online adaptation** than unconstrained self-modification,
- **screened architecture search with rollback** than live mutation,
- **compiled safety / governance** than heavy online meta-optimization.

The normative requirements are the state definitions, bounds, lookup
semantics, acceptance rules, invariants, and tests above.
