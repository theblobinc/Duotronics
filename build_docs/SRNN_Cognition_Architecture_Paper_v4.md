
# SRNN Cognition Architecture
## Theory, Mathematics, and Build Plan for the Cognition Layer
**Source design paper — drafted 2026-04-07**

### Abstract

This paper defines the cognition layer for the SRNN system as a recurrent media-chain architecture that sits between vector retrieval and symbolic reasoning. The immediate goal is not to build a general artificial mind, but to formalize how the SRNN can maintain a running semantic state while it walks a mixed chronological library of tracks, social posts, discoveries, and related web artifacts, reinforces relations, and explains its own transitions. The paper treats the current refactor state as the substrate: Milvus is the primary vector and metadata store, Ollama provides local embedding and model inference, Agno provides orchestration and tool surfaces, the daemon provides continual progression through the library, and the Common Lisp brain provides the native symbolic layer. The main contribution of this paper is a narrow cognition contract centered on the recurrence operator Φ, the latent context state h_t, the meta-object observation vector x_t, a loop-ensemble answer model, and a clean native/export indexing bridge.

## 1. Purpose and scope

The purpose of the cognition layer is to make the SRNN behave like a continuously updating semantic process rather than a collection of disconnected searches, playlists, and enrichment jobs. In practical terms, the cognition layer should do five things:

1. maintain a persistent hidden state while media advances;
2. integrate embeddings, symbolic meta-objects, and chronological order into one evolving chain;
3. separate local variation from true phase or regime shifts;
4. score whether nonlocal jumps remain semantically coherent;
5. expose enough structure that agents and dashboards can query the current state, explain decisions, and run experiments.

This paper focuses on the internal design needed to reach a strong v0. It does not attempt to freeze every future choice. The witness geometry ideas remain part of the design language and are now being promoted from optional accelerators to a planned integration point: Part IV defines a **Duotronic semantic witness bridge** that encodes temporal distance, arrangement distance, meta-object density, and synaptic strength as polygon witness configurations, giving the recurrent system a geometric concept of inter-neuron relationships.

### 1.1 2026 revision: storyboard ensembles, not genre buckets

The design target has now shifted in one important way: cognition should not be
reduced to genre tracking. The recurrent loops are meant to produce storyboard
traces built from music, lyrics, social media history, and web/search context.
The working model is:

- each cognition loop is one independent recurrent take over the ingested data,
- the shared chronology includes songs, linked social posts, discoveries, and
    story fragments,
- loop outputs are ranked against one another,
- and the final user-facing answer is a merged English statement rather than a
    raw regime label.

That means the term regime should be read narrowly: as one observable over the
chain, not as the whole cognitive product.

## 2. Current platform baseline

The current refactor state already contains the infrastructure required for cognition. The backend is consolidated under `srnn_server/`, with canonical Python modules in `srnn/`, symbolic reasoning in `srnn_lisp/`, local model infrastructure in Ollama, orchestration in Agno, a daemon-centered architecture, and Milvus as the primary vector store. The stack now includes collections such as `music_tracks`, `srnn_features`, `srnn_connections`, `meta_objects`, `dt_events`, `brain_memory`, `srnn_social_chronicle`, `srnn_bsky_meta_chain`, `srnn_discoveries`, `srnn_web_archive`, and `srnn_story_log`. The daemon model is already described as a chronological walk where each advance reinforces connections, updates recurrence chains, and logs events. This means the cognition design should be framed as a focused extension of the current system rather than a new platform rewrite.

## 3. Core theory: the SRNN as a recurrent media chain

The central theoretical claim is that the SRNN should be treated as a recurrent media chain rather than as a flat playlist plus vector search. A flat list can tell us what item comes next, but it cannot adequately represent delayed callbacks, recurring motifs, autobiographical echoes, or semantic state. A recurrent media chain can.

A base object is any realized media unit: a song, video, post, clip, event, or textual artifact. A meta-object is any extracted motif, reference, or higher-order feature cloud associated with that base object: colors, lyrical themes, moods, symbols, social anchors, scenes, or categorical activations. The chain’s identity is therefore distributed across:
- the realized base objects,
- chronological edges between them,
- meta-object linkages across them,
- and the hidden semantic state accumulated while the chain advances.

In this view, the daemon is not just playback infrastructure. It is the mechanism that advances cognition through time. Each track advance becomes a state transition, a memory event, and a reinforcement event.

### 3.1 Media-native neuron analogy

A useful internal analogy is to treat the realized media objects as the system's
native representational units. In that sense, the "neurons" of SRNN are not
abstract tensor positions but the actual base objects moving through the
chronicle: tracks, posts, searches, discoveries, story fragments, and daemon
events. What plays the role of "connections" are the recurrent relationships
between them: shared meta-objects, callback edges, temporal adjacency,
reinforced similarity links, and reference chains across the chronology.

Formally, this means that a base object `b_t` is a semantic unit whose state is
not meaningful in isolation. Its effective activation depends on the local
chronicle packet, the current hidden state, and the network of meta-object and
temporal relations around it. The meta-objects are therefore not separate from
the graph; they are part of the connective tissue through which the media-native
units predict, recall, and reinterpret one another.

This is an analogy, not a claim that songs are literal biological neurons. The
purpose of the analogy is architectural discipline: it keeps the design centered
on media-native units and their recurrent shared motifs instead of drifting back
toward generic genre buckets or undifferentiated embedding clouds.


## 4. Mathematical framework

### 4.1 Base objects and observed meta state

Let the realized media chain be:

    B = (b_1, b_2, ..., b_T)

where each `b_t` is a realized base object. Each base object carries a meta-object activation vector:

    x_t = (x_t1, x_t2, ..., x_tp)

where `x_t` may be dense, sparse, weighted, symbolic, or hybrid. This vector is an exported observation layer, not the total semantic truth of the object.

### 4.2 Native indexing and the zero bridge

The Duotronic notes are correct to distinguish the native public chain from exported measurement objects. The native public chain is one-based and presence-first:

    D+ = {1, 2, 3, ...}

The common export codomain remains zero-based:

    N0 = {0, 1, 2, ...}

The bridge is:

    E(d) = d - 1
    I(z) = z + 1

This is not cosmetic. It prevents the system from silently confusing four different things:
- structural omission,
- unknown,
- measured numeric zero,
- the first realized public chain element.

For the cognition layer, that means Lisp should never be forced to interpret the first public object as if it were the same thing as null, absent, or uninitialized state.

### 4.3 Time-directed graph model

A media chain is better modeled as a graph than as a list.

Temporal edges:

    E_T = {(b_t, b_t+1) : 1 <= t < T}

Meta-object edges are induced by a linkage kernel:

    Λ_ij = κ(b_i, b_j)

A simple starting point is weighted overlap:

    κ(b_i, b_j) = x_i^T W x_j

but the general formulation should allow directionality and reinterpretation. Later media may change the meaning of earlier media differently than earlier media predicts later media. This gives the full chain graph:

    G = (B, E_T, E_M)

where `E_M` is the set of weighted meta-object edges induced by `κ`.

### 4.4 Latent state and recurrence

The narrowest useful cognition model is recurrent and latent:

    θ_t ~ G(h_t-1, u_t)
    X_t | θ_t ~ F(θ_t)
    h_t = Φ(h_t-1, b_t, x_t, u_t)

where:
- `h_t` is the accumulated hidden semantic state,
- `θ_t` is a latent context or regime parameter,
- `X_t` is the observed meta-object vector,
- `u_t` is optional external context,
- `Φ` is the recurrence operator.

This is enough for prediction, reconstruction, regime detection, motif persistence analysis, and coherence-under-skip tests. It is also the right formal bridge between embeddings and symbolic reasoning. The embedding machinery does not become the mind; it becomes the observation layer that feeds the recurrent state update.

### 4.5 Why compound distributions matter

Compound distributions matter because the observed chain is rarely generated by a single flat process. The system first occupies or samples a latent context, then emits observed motifs conditional on that context. That gives:

    X_t | θ_t ~ F(. | θ_t)
    θ_t ~ G_t

and therefore the marginal observation law:

    H_t(x) = ∫ F(x | θ) dG_t(θ)

This matters because it gives a proper probabilistic language for mixed behavior: some motifs behave like stable regime markers, others behave like local noise.

### 4.6 Law of total variance

The law of total variance should be a first-class analytic tool:

    Var(Y) = E[Var(Y | Z)] + Var(E[Y | Z])

Interpretation:
- the first term is within-context variance;
- the second term is between-context variance.

In SRNN terms, this lets the system answer an important question motif by motif: is a feature changing because the current region is noisy, or because the chain has moved into a new semantic era? This is exactly the right tool for quantifying “vibe shift.”

### 4.7 Skip coherence

Skip coherence formalizes whether a nonlocal jump still preserves semantic continuity. A useful starting score is:

    C(i, j) = α κ(b_i, b_j) + (1 - α) sim(h_i, h_j)

where `κ` measures direct meta-object linkage and `sim(h_i, h_j)` measures alignment of hidden state. A path-based version can also be used:

    C(i, j) = max over paths π from i to j of Σ w(u, v)

The practical point is simple: when the user jumps from Song A to Song G, the system should estimate whether the semantic conversation survives the jump.

### 4.8 Witness geometry

Witness geometry is promoted from optional to planned. Part IV (§13) defines a **Duotronic semantic witness bridge** that extends the polygon witness system from digit-encoding to encoding temporal distance, arrangement distance, meta-object density (synapse count), and synaptic strength (weighted overlap) between any two base objects (neurons). A witness object `W_t` can serve as a sparse geometric signature derived from `x_t` through a map `Γ`, and the semantic witness extends this to encode the *relationship quality* between two neurons as a polygon lattice. This gives the recurrent cell a first-class geometric representation of how far apart two items are in time and in meta-object space, rather than relying solely on scalar decay constants.

The implementation uses the existing `DuotronicEncoder` (`srnn/duotronic/encoder.py`) and is implemented in `srnn/cognition/witness.py` (SemanticWitness, WitnessSectorProjector, TraversalPolicy).

**Part VI update (2026-04-08):** The witness is now a two-level design:

- **Level 1 — object witness** `W_t = Γ(b_t, x_t, c_t)`: the canonical packet signature (sparse sector scores, dominant sector, confidence). This is the existing `WitnessSignature` — what kind of packet this is, right now.
- **Level 2 — recurrent witness-state** `W̃_t = Ψ(W̃_{t-1}, W_t, h_{t-1}, b_t, x_t, u_t)`: a temporal witness process that carries memory across time — family persistence, callback residue, decay-adjusted motif mass, sector confidence traces, coherence drift, and branch-local regime hints.

The extended chain update becomes `h_t = Φ*(h_{t-1}, b_t, x_t, u_t, W_t, W̃_t, r_t)`. Each loop can also carry its own branch-local witness-state `W̃_t^(ℓ)`. See Part VI for the full mathematics and implementation sequence.

### 4.9 What is theory, what is analogy

A few distinctions should stay explicit:
- the recurrent latent-state model is a real modeling proposal;
- the law of total variance is a real statistical tool;
- the native/export index bridge is a real design rule;
- the Bessel-style subtract-one discussion is an analogy, not a proof;
- the phrase “semantic time crystal” is an internal metaphor, not a literal physical claim.

## 5. SRNN cognition theory

### 5.1 Cognition as traversal

The SRNN does not think in spite of traversal; it thinks through traversal. The daemon’s chronological walk is the temporal skeleton of cognition, but not the only evidence stream. Each loop traverses a shared chronicle that may include tracks, linked social posts, discoveries, web archives, and future story fragments. Each step:
- selects or confirms the next base object,
- gathers observed features,
- updates hidden state,
- reinforces graph structure,
- and logs a memory event.

### 5.2 Four memory layers

The cognition layer should be described using four memory layers.

**Observed episodic memory.**  
Stored in `dt_events`, `playback_log`, `decision_log`, and similar event streams. This is what happened, when, and why.

**Semantic object memory.**  
Stored in `meta_objects`, `srnn_features`, and enrichment artifacts. This is what the system knows about each item and motif.

**Relational memory.**  
Stored in `srnn_connections`, recurrence chains, `previous_object_id`, `parent_id`, and graph-derived edges. This is how items relate.

**Latent running memory.**  
Stored as the evolving chain state `h_t`, regime summaries, and compact brain snapshots. This is the system’s current semantic momentum.

### 5.3 Roles of each subsystem

**Milvus** should remain the authoritative store for embeddings, hybrid retrieval, and filterable metadata.  
**Ollama** should provide embedding generation and local inference, but not define the chain ontology.  
**Agno** should expose agents and tools, but should not replace the actual recurrent state machine.  
**The daemon** should be the temporal engine of cognition.  
**Common Lisp** should be the symbolic native layer: policy logic, chain semantics, explicit state transitions, and bridge discipline.

### 5.4 Why Lisp remains central

The Lisp layer matters because it is the right place to enforce:
- native one-based chain semantics,
- explicit null versus first-object distinctions,
- symbolic policies around recurrence,
- compact inspectable state objects,
- explainable transitions,
- and bridge rules for external APIs.

The Lisp brain should not be asked to do bulk vector search. It should consume summaries of observed state, update `h_t`, produce symbolic interpretations, and write back structured state outputs.

## 6. Architecture for the cognition layer

### 6.1 Data contract

The most important missing piece is a narrow data contract for cognition. Every cognition step should operate on the same conceptual packet:

- `native_index`
- `event_id`
- `source_type`
- `object_ref`
- `track_number` (optional when the current object is not itself a track)
- `timeline_ts`
- `base_object`
- `meta_summary`
- `context`
- `previous_state`
- `next_state`
- `observables`

The `meta_summary` should not be the full raw 384-dimensional payload unless needed for debugging. It should be a compact extracted packet:
- top motifs,
- salient categories,
- story axes from lyrics, social posts, discoveries, and web archives,
- feature counts,
- selected embedding references or hashes,
- relational cues,
- enrichment tier,
- temporal metadata.

### 6.2 Proposed recurrence interface

The core callable should be:

    phi_step(previous_state, event_record, meta_summary, context) -> next_state, observables

This function can exist in two implementations:
- a reference implementation in Python for fast iteration and tests;
- the authoritative symbolic implementation in SBCL for production cognition semantics.

### 6.3 Mapping theory to current collections

The current storage model already fits the theory well. The 2026 storyboard
revision expands `b_t` and `x_t` beyond tracks to include social, discovery,
web, and story evidence.

| Theoretical object | Proposed storage / source |
|---|---|
| `b_t` (base objects) | `music_tracks`, `dt_events`, `srnn_social_chronicle`, `srnn_bsky_meta_chain`, `srnn_discoveries`, `srnn_web_archive`, `srnn_story_log` |
| `x_t` (meta state) | `meta_objects`, `srnn_features`, social motifs, discovery tags, web metadata, story axes |
| `E_T` (temporal edges) | chronological order in `dt_events`, canonical timestamps across all source types |
| `E_M` (meta edges) | `srnn_connections`, `previous_object_id`, `parent_id`, recurrence outputs, social-to-track links |
| episodic memory | `dt_events`, `playback_log`, `decision_log` |
| semantic memory | `meta_objects`, enrichment data, `srnn_features` |
| social evidence | `srnn_social_chronicle` (~37k posts), `srnn_bsky_meta_chain` |
| discovery evidence | `srnn_discoveries`, `srnn_web_archive` |
| story evidence | `srnn_story_log`, claim blocks, storyboard artifacts |
| latent snapshots | `brain_memory` plus new chain-state records |

The main missing storage element is an explicit chain-state record keyed by native index, event id, and epoch.

### 6.4 Proposed service wiring

A clean v0 service flow looks like this:

1. **Daemon or loop scheduler** loads the current chronicle object.
2. **Feature assembly** loads `meta_objects`, `srnn_features`, `srnn_social_chronicle`, `srnn_bsky_meta_chain`, `srnn_discoveries`, `srnn_web_archive`, and recent context.
3. **Milvus retrieval** optionally fetches nearest motifs, neighbors, prior related memories, and loop-specific evidence.
4. **Meta summary builder** compresses the observation into a symbolic packet with story axes.
5. **Lisp phi service** receives `(previous_state, event_record, meta_summary, context)`.
6. **Phi update** returns `next_state` plus observables such as regime score, coherence, variance stats, and storyboard hints.
7. **Persistence layer** writes the new state snapshot and logs observables.
8. **Loop ensemble layer** ranks concurrent loop traces and composes a merged summary or long-form statement.
9. **Agent tools / dashboard** expose both the raw traces and the merged answer through APIs and explanations.

### 6.5 API shape

The current route strategy can support cognition if a few explicit state endpoints are added:

- `GET /xavi/brain/state/current`
- `GET /xavi/brain/state/history`
- `POST /xavi/brain/phi/step`
- `GET /xavi/brain/storyboards/current`
- `POST /xavi/brain/answers/compose`
- `GET /xavi/meta/variance`
- `GET /xavi/meta/coherence`
- `GET /xavi/meta/regimes`
- `GET /xavi/meta/chains/{track_number}`

These are not replacements for the daemon loop. They are observability and control surfaces for the cognition layer.

## 7. Build plan

### Phase A — Formalize the cognition contract

Deliverables:
- `CHAIN_CONTRACT.md`
- `phi_packet.schema.json`
- glossary of required terms

Rules to freeze:
- one-based native indexing,
- zero only in export/measurement layers,
- explicit unknown/absent/null representations,
- required fields for every cognition step,
- stable naming for base objects, meta objects, latent context, witnesses, and observables.

This phase is important because it prevents the math, Lisp code, Python code, and API payloads from drifting apart.

### Phase B — Build the state log

Add a dedicated chain-state record, either as:
- a new Milvus collection for compact state snapshots and observables,
- or a durable state log adjacent to `brain_memory`.

Each record should capture:
- native index,
- event id,
- epoch,
- previous state hash,
- next state hash,
- regime labels or scores,
- coherence metrics,
- motif summary,
- timestamp.

**Proposed `chain_state` schema:**

```python
CollectionSchema(
    fields=[
        FieldSchema("state_id",          DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("loop_id",           DataType.VARCHAR, max_length=64),
        FieldSchema("node_id",           DataType.VARCHAR, max_length=64),
        FieldSchema("native_index",      DataType.INT64),
        FieldSchema("epoch",             DataType.INT64),
        FieldSchema("step_count",        DataType.INT64),
        FieldSchema("source_type",       DataType.VARCHAR, max_length=32),
        FieldSchema("source_id",         DataType.VARCHAR, max_length=128),
        FieldSchema("regime_label",      DataType.VARCHAR, max_length=256),
        FieldSchema("regime_confidence", DataType.FLOAT),
        FieldSchema("coherence_score",   DataType.FLOAT),
        FieldSchema("variance_within",   DataType.FLOAT),
        FieldSchema("variance_between",  DataType.FLOAT),
        FieldSchema("active_story_axes", DataType.VARCHAR, max_length=4096),   # JSON
        FieldSchema("motif_masses",      DataType.VARCHAR, max_length=8192),   # JSON
        FieldSchema("state_hash",        DataType.VARCHAR, max_length=64),
        FieldSchema("prev_state_hash",   DataType.VARCHAR, max_length=64),
        FieldSchema("embedding",         DataType.FLOAT_VECTOR, dim=384),
        FieldSchema("created_at",        DataType.INT64),
    ],
    description="Chain-state snapshots for cognition replay and diagnostics"
)
```

This record is source-agnostic: the `source_type` field identifies whether the
triggering object was a track, social post, discovery, or any other chronicle
object type. The `embedding` is the state's compact vector representation for
similarity search across state history.

### Phase C — Build meta-summary extraction  ✅ (built)

Create a deterministic summary builder that maps rich observation layers into a concise symbolic packet. This should be testable without the daemon and reusable by agents.

Inputs:
- `music_tracks`
- `srnn_features`
- `meta_objects`
- `srnn_social_chronicle`
- `srnn_bsky_meta_chain`
- `srnn_discoveries`
- `srnn_web_archive`
- `srnn_story_log`
- recent playback and event history
- optional Milvus nearest-neighbor lookups

Outputs:
- salient motifs,
- salient story axes,
- top weighted relations,
- recent state hints,
- tier and enrichment markers,
- optional witness candidates.

### Phase D — Build Φ in reference form  ✅ (built)

Implement a reference `phi_step()` in Python. Keep it simple:
- update motif masses,
- update regime probabilities,
- compute local coherence,
- track persistent callbacks,
- emit a small number of observables.

The Python version is for experiments, fixtures, and parity tests.

**Implemented in** `srnn/cognition/phi.py` as `PhiOperator.phi_step()` with
story-axis accumulation (decay 0.94) and `_select_regime_label()` that prefers
story axes > themes > genres > motifs.

### Phase E — Build Φ in SBCL  ☐ (pending)

Implement the production symbolic state update in SBCL. The Lisp service should:
- accept the contract packet,
- validate native/export index rules,
- update the hidden state,
- emit a compact inspectable state object,
- return observables,
- and reject ambiguous null/zero coercions.

### Phase F — Wire Φ into the daemon  ✅ (built)

Integrate the phi step into the daemon loop after feature assembly and before persistence. The daemon should become the only authoritative writer of forward chain-state transitions during normal autonomous operation.

**Implemented in** `srnn/cognition/loop.py` — six loop types wired into the
daemon, deployed cluster-wide via systemd services on 3 nodes.

### Phase G — Add metrics and diagnostics  ☐ (pending)

The first metrics should be narrow and useful:
- motif variance decomposition,
- regime assignment confidence,
- skip coherence,
- state drift,
- callback persistence,
- recurrence density.

### Phase H — Expose tools and dashboard surfaces  ✅ (partial)

Wrap the cognition layer for Agno and UI use:
- current state inspection,
- explain-this-transition,
- compare two chain positions,
- skip-coherence analysis,
- regime timeline,
- motif drift chart.

**Partial:** 8 endpoints live at `/xavi/brain/*` (mounted in `xavi/app.py`
line 602). Dashboard widgets and agent tool wrappers pending.

### Phase I — Implement Duotronic semantic witness bridge  ✅ (built — see Part IV §13, Part V §4.3, Part VI)

The witness geometry work is implemented in `srnn/cognition/witness.py`:
- ✅ `SemanticWitness` encodes inter-neuron temporal and structural distances as polygon witness configurations,
- ✅ `WitnessSectorProjector` computes sparse sector signatures (K=8) on every chronicle packet,
- ✅ `TraversalPolicy` gives each loop a formal witness-sector policy,
- ✅ witness bias is injected into the recurrent cell's gate functions in `rnn_cell.py`,
- ✅ witness signatures are persisted per step via `CognitionStore`,
- ✅ witness-sector support drives ranking via `LoopRanker` (8-axis scoring).

**Next:** Part VI adds a recurrent witness-state `W̃_t` with its own update map `Ψ`, extending the witness from a static signature to a temporal process. See Phase 11 in REFACTOR_PLAN.

## 8. Acceptance criteria for a real cognition v0

A real v0 should satisfy the following tests.

**Contract discipline**
- The same event packet can be consumed by Python and SBCL implementations.
- Native/export index rules are never ambiguous.

**State continuity**
- Re-running the same fixed event sequence with fixed seeds gives reproducible state traces.
- State traces can be serialized and inspected.

**Variance usefulness**
- At least some motifs show meaningful within-context versus between-context decomposition.

**Coherence usefulness**
- Skip coherence distinguishes plausible jumps from incoherent jumps better than plain cosine similarity alone.

**Operational integration**
- The daemon updates state automatically.
- State endpoints expose useful diagnostics.
- Agents can explain track transitions using the same observables the daemon stores.
- Multiple loops can be ranked and merged into a coherent English response.
- Chronological social data measurably improves storyboard continuity for tracks that appear in both music and social history.

## 9. Risks and how to avoid them

**Risk: overbuilding witness geometry first.**  
Mitigated: Part IV §13 specifies a concrete, bounded semantic witness bridge. Implement after the recurrent cell and Redis meta-object exchange are working (Phase 4B).

**Risk: pushing raw embeddings directly into Lisp as the primary interface.**  
Avoid by using a compact meta-summary contract and letting Python/Milvus own heavy numeric retrieval.

**Risk: mixing metaphor with proof.**  
Avoid by labeling analogies as analogies and keeping the production system grounded in explicit state transitions, graph structure, and measurable statistics.

**Risk: agent sprawl replacing cognition.**  
Avoid by keeping Agno as an orchestration layer around the cognition core, not as the cognition core itself.

**Risk: status drift in the refactor roadmap.**  
Avoid by pinning this paper to the latest stated baseline and maintaining one canonical implementation-status table.

## 10. Recommended near-term milestone

The next milestone should not be “finish everything.” It should be:

**SRNN cognition v0**
- explicit chain contract,
- Python reference `phi_step`,
- SBCL `phi_step`,
- state snapshot logging,
- daemon integration,
- variance and skip-coherence metrics,
- inspectable `/xavi/brain/state/current` endpoint.

That is the smallest milestone that turns the existing platform into a genuine cognition stack.

## 11. Conclusion

The SRNN already has the infrastructure needed for cognition. What it lacks is not more containers or more broad architecture ideas, but a narrow and disciplined recurrent-state core. The proper mathematical center is a recurrent media-chain model with observed meta-object vectors, latent context, total-variance analysis, skip coherence, and a strict native/export bridge. The proper engineering center is a daemon-driven `phi_step` contract shared between Python experiments and a symbolic Lisp implementation. If that contract is built carefully, the system can evolve from vector-enhanced playlist infrastructure into a self-updating semantic process whose decisions, transitions, and memory states are inspectable, explainable, and experimentally extensible.

## Appendix A — Terminology

- **Base object**: realized song, video, post, event, or related media unit.
- **Meta object**: extracted motif, feature, reference, scene, or semantic signature.
- **Native public index**: one-based presence-first chain index.
- **Export index**: zero-based external representation when required.
- **Latent context**: hidden regime or semantic state parameter.
- **Recurrence operator Φ**: function that updates chain state at each step.
- **Skip coherence**: measure of whether nonlocal traversal preserves semantic continuity.
- **Witness (object witness)**: `W_t` — sparse geometric signature derived from meta state at time `t`. Canonical packet-level summary.
- **Witness-state (recurrent)**: `W̃_t` — temporal witness process carrying memory across time (Part VI). Updated via its own recurrence `Ψ`.
- **Witness sector**: named recurrent evidence region that packets project into (K=8 default sectors).

## Appendix B — Minimal implementation checklist

- [x] Freeze `CHAIN_CONTRACT.md` — `docs/CHAIN_CONTRACT.md`
- [x] Add `phi_packet.schema.json` — `docs/phi_packet.schema.json`
- [x] Define `chain_state` record format — `ChainStateRecord` in `srnn/cognition/state.py`; `srnn_chain_state` DDL in `loop.py`
- [x] Build `meta_summary` extractor — `srnn/cognition/meta_summary.py` (social, discovery, web, story enrichment; genre weight 0.35)
- [x] Implement Python `phi_step` — `srnn/cognition/phi.py` (story-axis accumulation, decay 0.94, `_select_regime_label()`)
- [x] Implement SBCL `phi_step` — `srnn_lisp/src/json-rpc.lisp`; Python bridge in `srnn/cognition/sbcl_bridge.py`
- [x] Add daemon hook — cognition loop types wired into daemon via `srnn/cognition/loop.py`
- [x] Define `CognitionState` — `srnn/cognition/state.py` (19 fields, 4 memory layers, `active_story_axes`)
- [x] Persist state and observables — `_save_snapshot()` / `_load_snapshot()` in `loop.py`; event-driven triggers on regime shift / high prediction error
- [x] Add `/xavi/brain/state/current` — mounted at `/xavi/brain/*` in `xavi/app.py`
- [x] Add variance and coherence diagnostics — `srnn/cognition/diagnostics.py`; skip coherence in `loop.py`; routes `/meta/variance`, `/meta/coherence`, `/diagnostics/gates/`, `/diagnostics/drift`
- [x] Create fixture-based parity tests — `tests/test_sbcl_parity.py` (33 pass, 3 xfail)
- [~] Add witness experiment behind a feature flag — `srnn/cognition/witness.py` fully implemented (SemanticWitness, TraversalPolicy); feature flag not yet added
- [x] Implement 6 loop types — chronological, exploratory, thematic, social, storyboard, replay
- [x] Implement contrastive loop — `loop.py` `_load_contrastive_tracks`; contrastive RNN cell style in `rnn_cell.py`
- [x] Implement narrator/synthesis loop — `loop.py` `_load_narrator_tracks`; narrator RNN cell style
- [x] Build loop ranking service — `srnn/cognition/ranking.py` — `LoopRanker` with 7-axis scoring
- [x] Build ranked-transfer merge — `srnn/cognition/merge.py` — `ClaimMerger` with witness-sector interference
- [x] Build English answer synthesis — `srnn/cognition/synthesis.py` — `Synthesizer` with Ollama + template fallback

**Part VI additions (two-level witness design):**

- [ ] Formalize two-level witness contract — object witness `W_t` schema + recurrent witness-state `W̃_t` schema + update map `Ψ`
- [ ] Implement minimal recurrent witness-state `Ψ` — family carryover, decay, callback persistence, drift score, regime evidence
- [ ] Add branch-local witness-state `W̃_t^(ℓ)` per loop
- [ ] Integrate witness trajectory into loop ranking (`WTraj_ℓ`)
- [ ] Expose witness-state inspection APIs
- [ ] Add witness feature flag for experiment gating

## 12. 2026 Revision B — Multi-loop storyboard ranking

The system model has now been tightened further. The cognition layer should be treated as a two-level architecture:

1. an authoritative recurrent chain updated by the daemon and Lisp `phi_step`, and
2. a ranked storyboard ensemble that reads from the shared chronicle and produces English-facing answers.

This revision changes the emphasis in three ways.

### 12.1 Regimes are observables, not the final product

Regimes should still be detected, but they should no longer be treated as the main answer surface. A regime score is one useful observable among several. The user-facing product is a storyboard answer built from tracks, lyrics, social chronology, discoveries, and related web evidence.

### 12.2 Seven recurrent takes over one chronicle

A good first implementation should run seven loop families over the same chronicle:

- chronological anchor;
- lyrics and motif;
- social resonance;
- discovery and search context;
- connection and callback;
- contrastive or alternate reading;
- narrator or synthesis loop.

Each loop owns a branch-local state and produces a replayable trace rather than a single scalar label.

**Implementation note (2026-04-08):** All seven loop families are now
represented in `srnn/cognition/loop.py`:

| Target loop | Implemented as | Status |
|---|---|---|
| chronological anchor | `chronological` | ✅ |
| lyrics and motif | `thematic` (closest match) | ✅ (to be specialized) |
| social resonance | `social` | ✅ |
| discovery and search | `storyboard` (includes discovery evidence) | ✅ |
| connection and callback | `exploratory` (random chain + motif discovery) | ✅ |
| contrastive | `contrastive` | ✅ |
| narrator / synthesis | `narrator` | ✅ |

The `replay` loop type is also implemented for historical sequence replay.

### 12.3 Ranking and merging sit above recurrence

The final answer should be built from a merge of loop traces, not from a single winning loop. The proper abstraction is:

    a_t = Merge(Rank(L_1, L_2, ..., L_n))

where each `L_i` is a loop trace, `Rank` scores traces for relevance and support, and `Merge` composes a short or long-form English answer.

### 12.4 Social chronology is first-class chain evidence

Songs, posts, discoveries, and searches should share one chronicle. Social media history provides timestamps, repeated language, artist mentions, linked songs, and real-world anchors. It therefore sharpens storyboard continuity and should be integrated into `meta_summary` packets and loop traversal.

### 12.5 New acceptance additions

A strong v0 should now also satisfy:

- multiple loops can replay the same chronicle window independently;
- social chronology improves at least some storyboard traces;
- ranked loop synthesis performs better than raw cosine or raw regime confidence;
- final English answers remain colorful but evidence-grounded.

## 13. 2026 Revision C — Predictive-coding interpretation of storyboard cognition

The storyboard ensemble can now be made more explicit by reading each loop as a
predictive-coding process rather than only as a retrieval strategy. Under this
view, each loop carries a branch-local generative hypothesis about what the
chronicle is doing next, and then updates that hypothesis using prediction
errors rather than only static similarity.

### 13.1 Each loop as a predictive hypothesis

For loop `i`, let the loop maintain a local predictive state `h_t^(i)` and a
predicted next observation packet `x_hat_(t+1)^(i)`. When the next chronicle
object arrives, the loop computes a residual:

    e_(t+1)^(i) = x_(t+1) - x_hat_(t+1)^(i)

where `x_(t+1)` is the observed mixed packet assembled from tracks, social
chronology, discoveries, web context, and meta-objects. The loop update then
becomes:

    h_(t+1)^(i) = Phi_pc(h_t^(i), x_(t+1), e_(t+1)^(i), u_(t+1))

This does not replace the canonical `Phi` formulation from earlier sections.
Instead, it clarifies what a loop is doing when it says “this looks like grief,”
“this looks like recovery,” or “this looks like a callback to an earlier social
period.” Each loop is proposing a model of the chronicle and then being judged
by how well it explains incoming evidence.

### 13.2 Precision-weighted ranking

Predictive coding also gives the ranker a stronger mathematical footing. A loop
should not only be scored by relevance and evidence density, but by how well it
reduces weighted prediction error across the chronicle window. A useful form is:

    Fit_i = - Sum_t || P_t^(i) * e_t^(i) ||^2

where `P_t^(i)` is a precision or reliability weight derived from timestamp
quality, recurrence support, social-link confidence, and evidence completeness.
High-precision residuals should matter more than low-precision ones. This lets
the system penalize storyboards that sound expressive but fail to account for
strong evidence.

### 13.3 Contrastive Predictive Coding as chronicle pretraining

Contrastive Predictive Coding (CPC) is a good fit for pretraining chronicle
encoders because it learns latent representations by predicting future samples
in latent space using a contrastive objective. For SRNN, that means the system
can train encoders over chronicle windows such as:

- track -> next lyrical / social / discovery context,
- social post -> nearby tracks and callbacks,
- discovery block -> subsequent motif bundle,
- story fragment -> later evidence confirmation or contradiction.

The important rule is that CPC should be used to improve observation packets,
link scoring, and chronicle embeddings, not to replace the symbolic daemon or
Lisp bridge.

### 13.4 Error-based predictive coding for digital branch loops

Recent error-based predictive-coding work is relevant because it is aimed at
making predictive coding practical on digital hardware. That makes it a good
candidate for branch-local loop scorers, meta-object update modules, and replay
workers on GPU/CPU nodes. The canonical daemon should still remain exact and
inspectable, but worker loops can use error-based predictive-coding modules to
update storyboard hypotheses more efficiently.

### 13.5 Contract additions

To support predictive-coding-style loops cleanly, the cognition packet should be
extended with:

- `predicted_story_axes`
- `predicted_next_packet`
- `prediction_error_packet`
- `precision_weights`
- `residual_summary`
- `fit_score`

These fields belong to branch-local loop traces and ranking logs. They should
not change the native one-based identity rules or the canonical event clock.

### 13.6 Part VII addendum — revised chain semantics and cheap worker math (2026-04-08)

Part VII revises the chain semantics from a frozen ontology into an active design surface. The development-phase state becomes `S_t = (C_t, H_t^canon, W_t, W̃_t, B_t)`, splitting the chain into four layers: chronicle ledger, canonical coordinator state, witness process layer, and approximate branch layer. This preserves Part I's canonical `Φ` recurrence for coordinator commits while allowing worker loops to run on aggressively cheaper math: int8 quantized recurrence, Count-Min Sketch witness mass, FWHT rotation, shift-add decay, sparse residuals, binary signatures, and shared sketches. Polygonal matrix semantics provide a structured operator language for sparse, canonicalizable, family-specific computation in the witness and sidecar planes.

See Part VII for the full cheap-math toolkit (§§5–15), polygonal operator semantics (§16), TurboQuant/Engram integration (§17), and implementation order (§20).
