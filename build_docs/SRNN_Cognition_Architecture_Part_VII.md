# SRNN Cognition Architecture, Part VII
## Revised Chain Semantics, Cheap Worker Math, Polygonal Matrix Semantics, and Hardware-Agnostic Acceleration for the SRNN
**Source design paper — addendum drafted 2026-04-08**

## Abstract

Part VII is an implementation addendum to Parts I–VI of the SRNN cognition architecture. The earlier papers established the recurrent media-chain ontology, the canonical `Phi` recurrence, the storyboard loop ensemble, the witness-sector layer, and the two-level witness design with object witness `W_t` and recurrent witness-state `W~_t`. This paper makes a further development-stage shift: the chain semantics are no longer treated as frozen. They are treated as an active design surface.

The purpose of Part VII is to define a stronger development model for the SRNN in which:

1. the chain semantics may be revised as the system matures;
2. the witness/polygon layer can take on more of the worker-side update, search, sketch, and representation burden;
3. the canonical coordinator path remains the place where authoritative chronology is committed;
4. the branch-local loop ensemble is allowed to run on aggressively cheaper math;
5. TurboQuant and Engram are integrated into this picture as compression-plane and conditional-memory-plane components;
6. and polygon/pronic structures are promoted from a descriptive witness language into a practical representation language for compact matrices, sketches, gates, and sidecar search structures.

The central claim is conservative in one sense and aggressive in another. It is conservative in that the system still needs explicit write-authority rules and explicit invariants. It is aggressive in that the old chain semantics are no longer treated as a final destination. They are now one design generation in an evolving SRNN. Part VII therefore proposes a revised semantics for the development phase: exact canonical commits at the coordinator, approximate recurrent reasoning in worker loops, and a family of cheap mathematical operators that make multi-loop cognition practical on commodity CPU and low-GPU nodes.

---

## 1. Why Part VII exists

Parts I–VI progressively made the SRNN more explicit:

- Part I defined the recurrent media-chain and the canonical `Phi` contract.
- Part II separated the canonical cognition plane from compression and external memory.
- Part III defined the ranked storyboard loop ensemble over a mixed chronicle.
- Part V defined digital witnesses as branch selectors / sector markers rather than literal semantics.
- Part VI promoted the witness to a two-level design with recurrent witness-state `W~_t` and an extended recurrence `Phi*`.

A new design pressure now appears.

The system is no longer just trying to explain itself better. It is trying to run more of its cognition stack efficiently across heterogeneous nodes:

- coordinator nodes with exact semantics,
- worker nodes with cheap local updates,
- replay loops over long history,
- social chronology at large scale,
- ranking loops over many branch-local takes,
- and a witness system that now needs to be updated, stored, searched, and compared continuously.

This creates a new practical question:

> What is the best SRNN we can build now, not just the cleanest one we could describe earlier?

That is the motivation for Part VII.

Part VII therefore treats the earlier semantics as important prior work, but not as a prison. The chain semantics are now explicitly under active redesign.

---

## 2. Revised stance: the chain semantics are now under development

A correction matters here.

The earlier papers sometimes spoke as if the canonical chain semantics should be preserved and everything else should orbit them. That was useful when the main job was to prevent conceptual drift. It is less useful now that the system is being actively engineered.

The revised stance of Part VII is:

- the old semantics remain the current reference behavior;
- the new semantics may revise the role of witnesses, worker loops, and branch-local state;
- the only things that must stay explicit are the invariants and the write-authority boundaries.

So the real design rule is not:

> “Never change the chain semantics.”

It is:

> “Change the chain semantics deliberately, with explicit contracts, bounded approximations, and coordinator-versus-worker discipline.”

This is a better fit for the system as it now exists:

- the refactor plan already places the project after Phase 6, with storyboard cognition complete and Phase 11 focused on two-level witness dynamics;
- the stack already includes eight loop types, witness-sector signatures, ranked-transfer merge, social chronology integration, and branch-local loop isolation;
- the immediate next stage is therefore not “invent cognition from scratch,” but “make the multi-loop cognition plane cheaper, more scalable, and more inspectable.”

---

## 3. Revised development-phase chain semantics

### 3.1 The old picture

The old narrow picture was:

`h_t = Phi(h_(t-1), b_t, x_t, u_t)`

then later:

`W_t = Gamma(b_t, x_t, c_t)`

`W~_t = Psi(W~_(t-1), W_t, h_(t-1), b_t, x_t, u_t)`

`h_t = Phi*(h_(t-1), b_t, x_t, u_t, W_t, W~_t, r_t)`

This remains a good reference form.

### 3.2 The new development-phase interpretation

For the purposes of implementation, the chain should now be understood as a four-layer system:

1. **Chronicle ledger** — the ordered mixed-source packet stream.
2. **Canonical coordinator state** — the authoritative committed semantic state.
3. **Witness process layer** — object witness plus recurrent witness-state and any polygonal witness derivatives.
4. **Approximate branch layer** — cheap worker loops, replay loops, sidecar search, compressed residuals, and provisional trajectory scoring.

This gives a more useful development object:

`S_t = (C_t, H_t^canon, W_t, W~_t, B_t)`

where:

- `C_t` is the canonical chronicle ledger state at step `t`,
- `H_t^canon` is the coordinator-owned chain state,
- `W_t` is the object witness,
- `W~_t` is the recurrent witness-state,
- `B_t` is the collection of branch-local approximate loop states.

Then the effective semantics are split:

### Canonical commit rule

`(C_t, H_t^canon) = Commit(C_(t-1), H_(t-1)^canon, packet_t, validated_inputs_t)`

### Witness update rule

`(W_t, W~_t) = WitnessUpdate(W_(t-1), W~_(t-1), packet_t, H_(t-1)^canon)`

### Worker branch rule

`B_t = WorkerStep(B_(t-1), packet_t, W_t, W~_t, compressed_sidecars_t)`

This development-phase semantics says something important:

- the canonical coordinator still commits chronology,
- but the worker loops are now first-class semantic machinery for search, replay, prediction, contradiction testing, and answer formation,
- and they are allowed to run on approximations as long as those approximations are bounded and replay-tested.

That is the conceptual foundation of the cheap-math program.

---

## 4. The two-level witness design remains the hinge

Part VI already made the decisive move:

- `W_t` is the canonical packet witness,
- `W~_t` is the recurrent witness-state,
- and `W~_t` may carry family persistence, callback residue, decay-adjusted mass, regime evidence, and drift.

That still stands.

What Part VII changes is the implementation reading.

The witness system is now not only:

- a ranking feature,
- a branch selector,
- or a debugging layer.

It is also the natural home for:

- cheap sketch structures,
- compact approximate histories,
- branch-local residual memory,
- sector counters,
- callback traces,
- approximate search keys,
- and polygonal low-rank / low-bit encodings.

This is exactly why the new witness contract is useful:

- it already specifies family masses,
- story axes,
- callback persistence,
- contradiction pressure,
- coherence drift,
- expected signature,
- and regime evidence.

Those are all amenable to extremely cheap approximate arithmetic.

---

## 5. Cheap worker math: the new implementation thesis

The core implementation thesis of Part VII is simple:

> Keep canonical commits exact enough to audit. Make branch-local cognition extremely cheap.

This is appropriate because the branch loops are not the final truth object. They are provisional recurrent interpretations over one shared chronicle.

The following subsections define the recommended cheap-math toolkit.

---

## 6. Quantized recurrence for worker loops

### 6.1 Basic idea

The canonical coordinator recurrence stays in float / exact symbolic form.

Worker loops run a quantized shadow recurrence.

Let the exact worker-local hidden state be `h_t^(ℓ)` and the quantized state be `h^_t^(ℓ)`.

Use a quantizer `Q_b,R` mapping into `b` bits over bounded range `[-R, R]`.

Then the worker recurrence is:

`h^_t^(ℓ) = Q( Phi_worker( Q^{-1}(h^_(t-1)^(ℓ)), packet_t, witness_t ) )`

### 6.2 Error bound intuition

If the worker update map is `L`-Lipschitz with `L < 1`, then quantization error does not explode.

A standard recurrence-style bound is:

`|| h_t - h^_t ||_inf <= eps_q / (1 - L) + L^t || h_0 - h^_0 ||`

where `eps_q` is the one-step quantization error induced by the quantizer.

This is exactly the regime SRNN wants:

- canonical daemon exact enough for commit logic,
- worker loops stable enough for ranking and replay,
- ranking preserved because the worker loops only need order-preserving fit and support, not perfect reconstruction.

### 6.3 Recommendation

Implement an **int8 branch path** in `srnn/cognition/rnn_cell.py` and use it only for worker / replay / branch-local loops.

Do **not** make this the first coordinator path.

---

## 7. Fast Walsh–Hadamard instead of dense random rotation

### 7.1 Why this matters

Part II already placed TurboQuant and PolarQuant into the compression plane, not the canonical meaning plane. That still looks correct.

But the practical improvement is now clearer:

when a random-rotation step is wanted in the sidecar compression path, use a Fast Walsh–Hadamard Transform (FWHT) or a Hadamard-plus-sign diagonal transform instead of dense matrix multiplication.

### 7.2 Form

For vector `x`, define:

`y = (1 / sqrt(d)) H_d D x`

where:

- `H_d` is the Hadamard transform,
- `D` is a diagonal random sign matrix.

This preserves norms in expectation and gives a much cheaper Johnson–Lindenstrauss-style rotation than dense Gaussian multiplication.

### 7.3 SRNN fit

This belongs in:

- `turbo_quant.py`,
- sidecar vector packing,
- branch-local replay buffers,
- binary signature generation,
- and fast worker-side search.

This is also one place where polygonal matrix semantics can become practical, because a Hadamard-like structured transform is much easier to represent with patterned weighted cells than a fully dense arbitrary rotation.

---

## 8. Count-Min Sketch for recurrent witness mass

### 8.1 Motivation

The new witness contract defines:

- `family_mass`,
- `story_axis`,
- `open_callbacks`,
- `sector_trace`,
- `regime_evidence`,
- and `expected_signature`.

Some of these are tiny. Some will grow across large replay windows.

For worker loops, the most obvious target for sketching is `family_mass`.

### 8.2 Sketch form

Replace dictionary-heavy worker-side mass tables with a small Count-Min Sketch.

A generic worker update becomes:

`mass_t[k] ≈ lambda_k * mass_(t-1)[k] + delta_t[k]`

but stored through a sketch estimator.

### 8.3 Why it fits SRNN

This is an excellent fit because:

- witness families are sparse,
- overestimation is safer than underestimation for provisional loop support,
- low-support ghosts are later pruned,
- and the coordinator path can still keep the exact dictionary if desired.

So the sketch is semantically acceptable in the worker plane.

### 8.4 Recommendation

Implement sketch-backed `family_mass` behind a feature flag in `srnn/cognition/witness.py` for worker loops only.

---

## 9. Sparse predictive-coding residuals

Part III already introduced precision-weighted residual fit terms of the form:

`F_i = - Sum_t || P_t^(i) * e_t^(i) ||^2`

That naturally suggests a sparse storage rule.

### 9.1 Observation

In practice, most residual coordinates are low-energy.

### 9.2 Update

For worker loops, store only top-k or thresholded residual coordinates:

`e_sparse = TopK_tau(e)`

Then approximate fit by:

`F^_i = - Sum_t Sum_{j in top-k} ( P_jj e_j )^2`

### 9.3 Why this is good

This preserves:

- ranking order in many cases,
- contradiction diagnostics,
- and replay-friendly fit summaries,

while reducing:

- memory,
- bandwidth,
- and candidate-merge overhead.

This is especially useful for the narrator and contrastive loops.

---

## 10. Integer EMA and shift-add decay

Many SRNN state updates are already exponential decay updates:

- witness family mass,
- story-axis smoothing,
- contradiction pressure,
- open callback decay,
- regime evidence smoothing.

Worker loops do not need full float multiply-add for these.

A useful practical substitution is shift-add approximations for common decay factors.

Example approximations:

- `x <- x - (x >> 6) + new` approximates `lambda ≈ 0.984375`
- `x <- x - (x >> 5) + new` approximates `lambda ≈ 0.96875`
- `x <- x - (x >> 4) + new` approximates `lambda ≈ 0.9375`

This is ideal for worker-side witness-state updates and sketch counters.

It is not necessary for the canonical path unless later benchmarking proves it harmless.

---

## 11. Binary signatures for first-pass retrieval

### 11.1 Motivation

The branch loops need cheap candidate generation.

### 11.2 Rule

Add a fixed binary signature sidecar for embeddings or witness summaries, then:

- use Hamming distance or popcount as first-pass filter,
- rerank on float or on richer witness / chronicle scoring.

This gives a retrieval stack of the form:

`binary prefilter -> compressed sidecar candidate set -> float rerank -> loop update`

### 11.3 Placement

This belongs naturally beside:

- `milvus_schema.py` sidecar fields,
- `turbo_quant.py` or a related sidecar builder,
- branch-local candidate generation,
- and possibly witness-family template lookup.

It is not the canonical truth store.

---

## 12. Shared sketch across the seven / eight loops

The loop ensemble already consists of multiple recurrent takes over the same chronicle.

That suggests a low-rank shared state design.

### 12.1 Shared base sketch

Instead of fully independent loop states, define a shared base sketch `H_t` and loop-specific residuals `Delta_t^(ℓ)`:

`h_t^(ℓ) ≈ W_ℓ H_t + Delta_t^(ℓ)`

where:

- `H_t` is a small shared sketch of the active chronicle dynamics,
- `W_ℓ` is the loop-specific projection / decoder,
- `Delta_t^(ℓ)` is the loop-specific residual.

### 12.2 Why this matters

The loops share most evidence:

- same chronicle,
- same local packets,
- same witness signatures,
- same recent callbacks,
- same social anchors.

So a low-rank shared base is plausible.

### 12.3 Use

This is most useful for:

- replay loops,
- long-window social loops,
- narrative synthesis workers,
- and shadow ranking workers.

---

## 13. Hebbian synaptic plasticity for `srnn_connections`

The older notes you added are still very good here.

Treat connection weights as online synapses, not just static similarity cache.

A simple local update is:

`Delta w_ij = eta ( x_i dot x_j - gamma w_ij )`

This is ideal for CPU nodes because it is:

- local,
- incremental,
- cheap,
- and aligned with your ontology that base objects are the native units and shared meta-objects are the connective fabric.

This should be added as an **online update option** for branch-local reinforcement and later tested for coordinator commit influence.

---

## 14. Sinkhorn divergence for storyboard coherence

The current ranker already computes coherence and predictive fit.

A stronger geometry-aware coherence layer can be added by comparing loop traces as distributions over:

- witness sectors,
- story axes,
- or motif bundles.

A Sinkhorn divergence or entropic transport approximation is a strong candidate for the trace-level coherence metric.

This is especially attractive because:

- the chronicle is sparse,
- the distributions are structured,
- and worker-side approximate transport can be much more informative than cosine-over-summaries.

Use this in the ranking layer, not in the canonical daemon path.

---

## 15. Nyström approximation and TT trace compression

Two other older suggestions remain good implementation targets:

### 15.1 Nyström for large social chronology kernels

Use low-rank kernel approximation for large social-post similarity or witness-sector kernels.

This is valuable because the refactor state already includes a large embedded social chronology and the loop ensemble is storyboard-first, not track-only.

### 15.2 Tensor-train style trace compression

Long replay traces are expensive to keep dense.

Use a compressed trace representation for:

- long replay storage,
- cross-node trace shipping,
- historical loop comparison,
- and narrative rehydration.

This is an excellent worker-side optimization and fits the replay loop naturally.

---

## 16. Polygonal matrix semantics

This section should be read as a **restricted operator proposal**, not as a claim that every matrix in SRNN ought to become polygonal. The right claim is narrower and stronger:

> **Some SRNN operators are better understood as structured families of local cells than as anonymous dense float arrays.**

That matters because much of the system already operates on sparse, canonicalizable, family-tagged structure: witness sectors, callback traces, loop policies, reinforcement edges, and low-bit worker-side updates. In those places, a polygonal operator language can be more natural than a generic matrix, because the operator already has interpretable local parts: center mass, boundary occupancy, family rules, and family-specific decay or transition behavior. This fits the broader SRNN direction where chronicle objects are the native units, meta-object relations form the connective fabric, and witnesses already act as structured packet signatures rather than arbitrary embeddings alone.  

### 16.1 What is being claimed

A matrix or linear-like operator need not always be represented as a dense floating-point array. In some parts of SRNN it can instead be represented as a **family of weighted polygon cells** whose local fields determine the effective coefficient or transition rule.

A generic polygonal entry is:

[
P_{ij} = (m_{ij}, c_{ij}, \mathbf{w}*{ij}, \mathbf{x}*{ij}, \sigma_{ij}, f_{ij})
]

where:

* (m_{ij}) is the polygon family or arity,
* (c_{ij}) is the center state,
* (\mathbf{w}_{ij}) is the vertex-weight vector,
* (\mathbf{x}_{ij}) is the vertex-occupancy or count vector,
* (\sigma_{ij}) is the canonicalization/orientation policy,
* (f_{ij}) is the family tag.

The entry is then interpreted by a family-specific decoder:

[
A_{ij} = \mathrm{Decode}(P_{ij})
]

or, when a dual-signal channel is needed,

[
D_{ij} = (p_{ij}, q_{ij}) = \mathrm{Decode}*{\mathrm{dual}}(P*{ij}).
]

This is the key distinction: the polygonal object is **not** the matrix value itself. It is a structured encoding from which the value is induced. Different families may decode differently. That is a feature, not a bug, because the SRNN already distinguishes between witness families, source types, and recurrence roles rather than forcing all structure into one uniform metric space.  

### 16.2 What this is good for

Polygonal matrix semantics are most believable and most useful in the following cases:

* sparse matrices,
* adjacency and reinforcement operators,
* witness-family transition tables,
* gate banks and decay banks,
* sketch matrices,
* structured search transforms,
* low-rank or block-local sidecar operators,
* compressed branch-memory operators.

This is a much stronger position than claiming that all dense tensors should become polygons. For a tiny dense matrix, such as an (8 \times 8) witness-family transition table, an ordinary dense array is still the simplest and best default. The polygonal form becomes interesting only when it adds one of four concrete benefits:

1. **canonicalization** — multiple structurally equivalent entries collapse to one canonical representation;
2. **family-awareness** — different operator families can obey different ladders, decay rules, or parity constraints;
3. **bit efficiency** — center/vertex/count representations can be packed more cheaply than float arrays;
4. **local interpretability** — the operator can be read as an arrangement of meaningful local cells rather than as opaque coefficients.

So the paper should say this explicitly: polygonal semantics are a **specialized operator language**, not a universal replacement for ordinary matrices.

### 16.3 Family-specific ladders and pronic structure

One reason the idea remains alive from the older Duotronic work is that polygonal entries do not have to share a single universal ladder. Different families may use different vertex-weight schedules and different decode rules.

That means one family may use:

* pronic or even-gap ladders,
* parity-bridged ladders,
* dual-signal decode channels,
* center-heavy local mass,
* or family-specific count rules.

Formally, the decoder can be written as:

[
\mathrm{Decode}*{f}(P*{ij}) =
g_f!\left(c_{ij}, \mathbf{w}*{ij}, \mathbf{x}*{ij}, \sigma_{ij}\right)
]

so that the meaning of the same occupancy pattern may differ by family. This is exactly why polygonal operators should be described as a **familyed operator language**. They are not one monolithic numeric replacement. They are a typed operator system whose families correspond to different recurrence roles, witness regimes, or sidecar computation modes.

This is also compatible with the measurement-layer discipline in the earlier work: standard vectors, matrices, and probability tables are still allowed on export, as long as the system does not confuse structural omission with numeric zero or collapse family semantics into a single flat array prematurely. 

### 16.4 Concrete SRNN use cases

The section becomes much stronger if it names where polygonal matrices are actually useful in SRNN code.

#### A. Witness-family transition operators

Suppose the system has (K=8) witness families. The simplest transition object is an ordinary dense matrix
[
T \in \mathbb{R}^{8 \times 8}.
]

That is fine when all you need is a small learned table.

But if the transitions are family-typed — for example, some sectors are callback-rich, some are temporal-local, some are cross-source, and some obey different persistence ladders — then each entry can instead be represented as a polygonal cell whose decode reflects that family logic:

[
T_{ab} = \mathrm{Decode}*f(P*{ab}).
]

This is not cheaper because (8 \times 8) is large. It is useful because the transition table becomes:

* canonicalizable,
* inspectable,
* family-aware,
* and naturally packable for worker-side low-bit execution.

#### B. Gate banks in `rnn_cell.py`

The current witness contract already routes recurrent witness-state into gate computation through witness-derived bias and contradiction gating. 

A polygonal gate bank can encode a small bank of gate perturbations or biases where each cell corresponds to a family-conditioned local gate rule. In that case, multiplication by a vector is not full matrix multiplication. It is a **banked local apply**:

[
y_i = \sum_{j \in \mathcal{N}(i)} \mathrm{Decode}(P_{ij}),x_j
]

with (\mathcal{N}(i)) sparse and small.

That makes the polygonal representation competitive with sparse matrices, because the operator is already local, typed, and low-bit.

#### C. Reinforcement and callback adjacency

Part IV already frames SRNN recurrence in graph terms: chronicle objects act like neurons, and meta-object overlaps act like synaptic connections. 

A reinforcement operator over that graph can be represented as a polygonal adjacency layer when the entries carry structured local state such as:

* overlap density,
* callback richness,
* temporal distance band,
* source-crossing flag,
* contradiction penalty.

In that case the polygonal entry is not just “another way to store a scalar.” It is an entry that *remembers why* the scalar exists.

#### D. Sidecar search and sketch transforms

The worker-side math notes already point toward count-min sketches, compressed sensing, Nyström features, and low-bit sidecar transforms as cheap representations for branch-local search and loop updates.  

Polygonal operator families fit naturally here as:

* compact sketch-update operators,
* bit-packed local transforms,
* family-specific sidecar decoders,
* or structured routing stencils for witness-side search.

This is a stronger story than “polygonal matrices replace linear algebra.” They become one more **cheap operator substrate** in the worker and sidecar planes.

### 16.5 A concrete Python model

The reviewer is right that the paper should show what a polygonal cell looks like in code. A minimal reference model is:

```python
from dataclasses import dataclass
from typing import Sequence, Literal

Family = Literal[
    "temporal_local",
    "temporal_distant",
    "high_density",
    "social_anchored",
    "callback_rich",
    "cross_source",
    "motif_recurrence",
    "low_evidence",
]

@dataclass(frozen=True)
class PolygonCell:
    sides: int
    center: float
    vertex_weights: Sequence[float]
    vertex_counts: Sequence[int]
    family: Family
    orientation: int = 0
    dual: bool = False

def decode_scalar(cell: PolygonCell) -> float:
    return cell.center + sum(
        w * x for w, x in zip(cell.vertex_weights, cell.vertex_counts)
    )

def decode_dual(cell: PolygonCell) -> tuple[float, float]:
    base = decode_scalar(cell)
    # simple example: positive mass from center and odd vertices,
    # inhibitory mass from even vertices
    p = cell.center + sum(
        w * x for k, (w, x) in enumerate(zip(cell.vertex_weights, cell.vertex_counts))
        if k % 2 == 0
    )
    q = sum(
        w * x for k, (w, x) in enumerate(zip(cell.vertex_weights, cell.vertex_counts))
        if k % 2 == 1
    )
    return (p, q)

def apply_polygon_row(row: Sequence[PolygonCell], x: Sequence[float]) -> float:
    total = 0.0
    for cell, xj in zip(row, x):
        total += decode_scalar(cell) * xj
    return total
```

This example is intentionally simple. It shows that a polygonal matrix can be treated as a matrix of structured entries whose decoded values participate in ordinary multiplication. The point is not that this beats BLAS for dense algebra. The point is that it gives SRNN a way to store and apply **typed, canonicalizable, low-bit local operators** when that structure already exists.

### 16.6 When it is cheaper than dense, sparse, or low-rank

The reviewer also asks the right performance question: why use this instead of a sparse matrix or low-rank factorization?

The answer should be explicit.

Use a **dense matrix** when:

* the matrix is tiny and ordinary,
* family tags add no value,
* you need straightforward linear algebra.

Use a **sparse matrix** when:

* support is sparse,
* entries are just numbers,
* standard sparse kernels already solve the problem.

Use a **low-rank factorization** when:

* the operator is approximately global and compressible,
* factor storage is cheaper than entrywise storage,
* interpretation is secondary.

Use a **polygonal operator** when:

* entries are sparse **and** structured,
* canonicalization matters,
* family-specific decode rules matter,
* low-bit packing matters,
* or worker-side updates want small local entry objects rather than generic floats.

So polygonal matrices do **not** win by replacing all matrix math. They win in the narrower regime where SRNN already wants structured local operators and typed witness-family logic.

### 16.7 Strong caution

This section should end with a clear boundary.

Polygonal matrix semantics do **not** mean:

* replace every float tensor with polygons,
* replace every small dense table with a more complicated object,
* or claim that the canonical chain is “nothing but polygons.”

They mean something narrower and more practical:

> **Polygonal operators are eligible as worker-side and sidecar representations for structured, sparse, canonicalizable, family-specific computation.**

That is a real upgrade to the architecture because it gives the SRNN another operator substrate exactly where the system already wants low-bit, typed, interpretable structure: witness dynamics, gate perturbation, reinforcement edges, sidecar transforms, and branch-local update rules. It also fits the graph view cleanly: matrices and graphs are equivalent descriptions of connectivity, so a polygonal entry can be understood as a structured edge object in a graph-derived operator, rather than as a mystical replacement for ordinary matrix algebra. 

---

## 17. TurboQuant and Engram in Part VII

Part II already said the right thing:

- TurboQuant belongs to the compression plane first,
- Engram belongs to the conditional memory plane first.

That still holds.

Part VII extends that advice with more specific roles.

### 17.1 TurboQuant in Part VII

TurboQuant should now be read as the **numeric sidecar counterpart** to the cheap-worker program.

Use it for:

- compressed local vector replicas,
- branch-local candidate search,
- replay buffers,
- agent-side KV cache experimentation,
- and any structured low-bit sidecar whose errors are corrected by rerank or by canonical validation.

The Hadamard / structured-rotation recommendation strengthens this.

### 17.2 Engram in Part VII

Engram should now be read as the **lookup-memory counterpart** to the dynamic witness system.

A natural Part VII move is to define witness-facing memory tables for:

- witness-family templates,
- lyric n-gram bundles,
- callback motifs,
- story fragments,
- social chain templates,
- and chronicle-local symbolic packets.

Then retrieval becomes:

`r_t = Retrieve(k_t, M)`

and the richer recurrence becomes:

`h_t = Phi**( h_(t-1), b_t, x_t, u_t, W_t, W~_t, r_t, sidecar_t )`

The important thing is that Engram retrieval is deterministic and explicit rather than prompt-bloated.

### 17.3 Combined view

TurboQuant + Engram + Part VI witness dynamics now form a clear three-part worker strategy:

- **TurboQuant / compact search** for cheap candidate transport,
- **Engram / lookup memory** for cheap recall of semi-static structure,
- **Recurrent witness-state** for cheap temporal accumulation and explanation.

That is a much stronger story than any of them alone.

---

## 18. Recent efficiency work that actually helps

The request here is practical: not every new paper is worth forcing into SRNN.

The best recent fits I found are the ones closest to your actual bottlenecks.

### 18.1 TurboQuant remains relevant now

TurboQuant is not only a 2025 paper; it also received a fresh 2026 push through Google Research’s March 2026 release around ICLR 2026, with explicit claims about strong KV-cache compression and vector-search utility. That keeps it timely for Part VII’s compression-plane discussion even if the original paper predates the last six months.

### 18.2 OjaKV is a strong recent fit

OjaKV is a recent 2026 low-rank KV-cache compression proposal with online subspace adaptation. Even if SRNN never uses it directly in the daemon, it is a good conceptual fit for:

- adaptive worker-side cache compression,
- branch-local replay,
- and context-sensitive compressed memory that evolves online instead of relying only on one offline subspace.

### 18.3 KV-CoRE is useful as a benchmark discipline

KV-CoRE is useful less as a direct deployment method and more as a measurement discipline: it emphasizes that compressibility is data-dependent. That is highly relevant to SRNN, because different chronicle regions, loop types, and witness families will not compress equally well.

### 18.4 What I did **not** want to do

I do not want to pad Part VII with every flashy efficiency paper in circulation. The useful additions are the ones that match your architecture:

- compression of worker-side transport,
- explicit lookup memory,
- adaptive low-rank or sketch state,
- branch-local cheap recurrence,
- and fast approximate replay.

That is enough.

---

## 19. Recent papers that are worth mentioning, but not overcommitting to

If a short “recent related work” section is wanted, the cleanest set is:

1. **TurboQuant / PolarQuant** — strong compression-plane fit, especially sidecars and KV experiments.
2. **OjaKV** — online low-rank KV adaptation; relevant to adaptive worker caches.
3. **KV-CoRE** — useful benchmarking lens for data-dependent compressibility.

The more mature older ideas that still remain directly useful in SRNN are:

4. **CPC** for future-aware chronicle embedding and link learning.
5. **error-based predictive coding** for worker-side residual updates.
6. **RuVector** for experimental graph/vector sidecars.
7. **Nyström / Sinkhorn / TT** for large chronicle geometry and replay efficiency.

That is the right size of bibliography for a practical Part VII.

---

## 20. Recommended implementation order

The refactor plan already puts the system just after the storyboard ensemble and before the two-level witness implementation is fully finished.

So the right implementation order is:

### Phase VII-A — finish Part VI contract and recurrent witness-state

1. finish `WITNESS_CONTRACT.md`
2. implement `RecurrentWitnessState`
3. wire `Psi` into `loop.py`
4. pass witness-state into `rnn_cell.py` and ranking

### Phase VII-B — cheap worker math behind feature flags

5. add int8 worker recurrence path
6. add sketch-backed worker `family_mass`
7. add sparse residual storage for worker loops
8. add shift-add decay options for worker-side witness updates

### Phase VII-C — search sidecars and compressed retrieval

9. add binary signature first-pass filter
10. add TurboQuant / FWHT sidecar experiments
11. add candidate prefilter -> float rerank pipeline

### Phase VII-D — conditional memory

12. add Engram-style memory tables for witness families, motifs, callbacks, story fragments
13. add deterministic lookup keys derived from `(packet, W_t, W~_t, query_context)`

### Phase VII-E — polygonal operator experiments

14. implement polygonal operator prototypes for witness-family tables and loop-policy matrices
15. benchmark them as representations for sparse / low-rank / low-bit worker operators
16. only later consider broader matrix substitution

### Phase VII-F — evaluation gates

17. compare float worker loops vs cheap worker loops on ranking agreement
18. compare binary prefilter + compressed search vs float-only search on recall@k and answer quality
19. compare exact witness dictionaries vs sketch-backed witness-state on ranking stability
20. compare loop Kendall tau before and after quantized worker rollout

---

## 21. Minimal parity and safety gates

Because Part VII explicitly revises semantics in development, it needs clear gates.

### 21.1 Canonical safety gates

- no corruption of the coordinator commit ledger;
- no change in native/export null handling at the commit boundary;
- no silent coercion of unknown to zero;
- no loss of replayability for the canonical chain.

### 21.2 Worker fidelity gates

- ranking agreement with float worker baseline;
- stable top-k loop identity over representative chronicle windows;
- bounded divergence in witness trajectory metrics;
- no catastrophic failure in long replay windows.

### 21.3 Search / memory gates

- candidate recall remains acceptable under compressed prefilter;
- rerank restores canonical-quality candidate order;
- memory lookup improves story continuity or prompt economy rather than bloating control flow.

### 21.4 Polygon operator gates

- canonicalization stable across languages / runtimes;
- decode / encode deterministic for chosen family;
- no operator ambiguity from symmetry policy;
- performance win is real enough to justify complexity.

---

## 22. Why the polygon/matrix idea helps the paper

Yes — it helps the paper.

It helps because it finally gives the older Duotronic work a realistic landing place in SRNN.

Not as:

- “the whole chain is now polygons,”
- or “replace the daemon with white-paper numeration.”

But as:

- a structured witness representation layer,
- a compact worker-math layer,
- a matrix/operator language for sparse and family-specific transforms,
- a canonicalizable low-bit state representation,
- and a bridge between your older Duotronic numeration ideas and the newer SRNN witness process.

That is exactly the kind of “moved on, but not wasted” integration that a good Part VII should perform.

---

## 23. Final recommendation

Part VII should be adopted as a development-stage design paper for the next SRNN cycle.

Its value is threefold:

1. it frees the project from treating the old chain semantics as untouchable;
2. it gives the multi-loop worker plane a serious cheap-math program;
3. it gives the older polygon / Duotronic work a concrete implementation home inside the newer witness-centered SRNN.

The cleanest way to summarize the outcome is:

> coordinator commits exact chronicle truth; worker loops run bounded cheap recurrent math; witnesses become compact temporal operators; TurboQuant compresses transport; Engram handles lookup memory; polygonal operators become a real representation language for sparse recurrent computation.

That is a better system than the earlier papers alone could specify.

---

## References

### Internal SRNN papers and notes

- Part I — `SRNN_Cognition_Architecture_Paper_v4.md`
- Part II — `SRNN_Cognition_Architecture_Part_II.md`
- Part III — `SRNN_Cognition_Architecture_Part_III_v3.md`
- Part V — `SRNN_Cognition_Architecture_Part_V.md`
- Part VI — `SRNN_Cognition_Architecture_Part_VI.md`
- `REFACTOR_PLAN_v5.md`
- `SRNN Recurrent Witness Contract` (user-provided design note)
- older Duotronic white-paper materials supplied in chat

### External references

- Amir Zandieh et al., **TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate**, arXiv:2504.19874.
- Google Research Blog, **TurboQuant: Redefining AI efficiency with extreme compression**, March 24, 2026.
- DeepSeek AI, **Engram: Conditional Memory via Scalable Lookup** (repository / design pattern reference).
- Jian Chen et al., **KV-CoRE: Benchmarking Data-Dependent Low-Rank Compressibility of KV-Caches in LLMs**, arXiv:2602.05929.
- OjaKV authors, **OjaKV: Context-Aware Online Low-Rank KV Cache Compression**, ACL ARR 2026 January submission.
- earlier worker-side references already named in prior parts: CPC, error-based predictive coding, RuVector, Sinkhorn divergence, Nyström approximation, tensor-train compression.
