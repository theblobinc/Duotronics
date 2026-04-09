# SRNN Cognition Architecture, Part IV
## Recurrent Neural Networks, Gated Chronicle Memory, and Loop-State Design for the SRNN
**Source design paper - drafted 2026-04-07**

### Abstract

Part IV explains how recurrent neural network ideas should be interpreted inside the updated SRNN cognition architecture. The central thesis is this: **the neurons of the SRNN are its base objects — individual songs, social posts, discoveries, web fragments, story packets, and daemon events — and the synapses are the realized meta-object connections between them.** Every recurring genre tag, every shared lyrical motif, every matching mood, every artist reference that appears in more than one base object is a synapse that binds those neurons together. The strength of a synapse is a function of how many meta-objects overlap and how strongly they match. The chronological stream of the entire library — playlist tracks interleaved with dated social posts, timestamped searches, and web captures — is the native sequence that the recurrence operates over.

Parts I through III established the recurrent media-chain ontology, the canonical `Phi`-based cognition loop, the supporting compression and external-memory planes, and the ranked storyboard ensemble. This document adds a more explicit recurrent-memory theory. Its main claim is that the SRNN should borrow the discipline of recurrent neural networks without collapsing into a generic sequence model. The SRNN already has the ingredients of recurrence: chronologically ordered base objects, meta-object connections, a persistent hidden state, multi-step callback structure, and multiple branch-local cognition loops. The job of Part IV is to show how feed-forward processing becomes recurrent memory, why vanilla recurrence is not enough, why gated memory matters, and how a media-native RNN interpretation can be used to refine `Phi`, loop-local state, and English-facing synthesis.

The key architectural stance is conservative. The canonical daemon and Lisp bridge remain authoritative and inspectable. RNN ideas are used to sharpen state design, retention policies, prediction, and loop specialization - not to erase the explicit semantics established in the earlier papers. In this system, the base objects of the chronicle act as the native representational units (neurons), while shared meta-objects, reinforced links, and chronology edges act as the connective fabric (synapses) through which recurrence emerges.

This document also introduces three new architectural components not covered in earlier papers: (1) a **temporal binding layer** that ties chronologically dated social posts to the playlist and media stream, creating referential cognition anchors; (2) a **Duotronic semantic witness bridge** that gives the recurrent system a geometric concept of time and meta-object density; and (3) a **Redis meta-object exchange bus** that lets any cognition loop request and share meta-object observations about any base object in the entire collection.

## 1. Why Part IV exists

The updated SRNN design is already recurrent in spirit. Part I defined the chain as a recurrent media graph with a hidden state `h_t`, a recurrent update rule, and a distinction between base objects and meta-object observations. Part III then extended the architecture into a seven-loop storyboard ensemble over a mixed chronicle of tracks, social posts, discoveries, web fragments, and story packets. The refactor plan now places this work squarely inside Phase 6: storyboard-first cognition, social chronology integration, seven ranked loops, and English answer synthesis.

What is still missing is an explicit explanation of what kind of recurrence the system should embody. The earlier papers prove that the SRNN should not be reduced to genre buckets or flat similarity search. This paper adds the next bridge: it explains how recurrent neural network concepts - hidden state, leaky memory, gated retention, branch-local recurrence, and sequence prediction - should be translated into the SRNN's own ontology.

This document is therefore not a generic tutorial on RNNs. It is a design paper about what RNNs mean once the "neurons" are songs, posts, discoveries, story fragments, and daemon events, and once the effective "connections" are shared meta-objects, chronology edges, recurrence chains, and reinforced similarity links.

### 1.1 The neuron/synapse mapping

The most important conceptual move in this paper is the following translation:

| RNN concept | SRNN realization | Where it lives |
|---|---|---|
| **neuron** | a base object — one song, one social post, one discovery, one web fragment, one story packet, one daemon event | `srnn_social_chronicle`, `srnn_discoveries`, `srnn_web_archive`, `srnn_story_log`, playlist tracks |
| **synapse** | a realized meta-object connection between two base objects — every shared genre, motif, mood, tag, artist, lyrical phrase, or symbolic reference that appears in both | `srnn_meta_objects`, `srnn_connections`, `srnn_bsky_meta_chain` |
| **synapse weight** | the number and strength of overlapping meta-objects between two base objects | `connection_score` from `srnn_connections`, Jaccard overlap of meta-object sets |
| **input** | the normalized chronicle packet for the current base object | `MetaSummaryBuilder.build()` output |
| **hidden state** | the accumulated semantic context carried by a cognition loop | `CognitionState` — 19+ fields across 4 memory layers |
| **time step** | advancing to the next base object in the chronological stream | `native_index` increment in `phi_step()` |
| **recurrent connection** | the carrying-forward of hidden state from step t−1 to step t | the full `Phi` operator |
| **gated memory** | selective retention/forgetting of different kinds of evidence | decay constants (`GENRE_DECAY=0.95`, `THEME_DECAY=0.92`, `STORY_AXIS_DECAY=0.94`) |

The key insight is that a traditional RNN has abstract neurons and learned weights. The SRNN has *realized* neurons (actual media items with real content) and *realized* synapses (actual meta-objects that demonstrably connect them). The multitude of similar or recurring meta-objects across each piece of media forms a dense connective web — not a sparse learned weight matrix, but a rich, inspectable, content-grounded graph of actual shared meaning.

### 1.2 Social posts as chronological neurons

A critical feature of the SRNN is that Facebook and Bluesky posts are positioned chronologically with real dates (`published_at` in `srnn_social_chronicle`). These posts can be tied to the music in the playlist via `matched_track_number` and also to other media that was shared, discovered, or searched at similar times. This creates a referential cognitive process: the social post is not just metadata about a song, it is an independent neuron in the chronicle whose date anchors it in real human time, and whose content (text, tags, engagement, platform) creates synapses to nearby tracks, discoveries, and other posts.

When the chronological stream interleaves songs (from the playlist arrangement) with dated social posts (from `srnn_social_chronicle`), timestamped discoveries (from `srnn_discoveries`), and web captures (from `srnn_web_archive`), the result is a unified temporal sequence where every item carries a real-world timestamp. The SRNN can then identify patterns like: "this dark ambient phase in the playlist happened during the same month as these reflective social posts and these philosophical web searches." That is referential cognition — the system uses temporal proximity and meta-object overlap to bind different kinds of media into a coherent autobiographical stream.

## 2. Why recurrence matters here

A feed-forward model can classify the current item, but it has no durable account of what came before. If every song, post, or discovery is interpreted in isolation, the system cannot sustain callbacks, social echoes, long-range emotional turns, or question-conditioned story arcs. The chronicle can then be searched, but it cannot really be remembered.

This is the central value of recurrence. A recurrent system carries forward a state summary of prior evidence and lets the current interpretation depend on both the present packet and the remembered context. That is exactly what the SRNN needs. The daemon is already a chronological walk, the cognition layer already carries an explicit hidden state, and the loop ensemble already maintains branch-local traces. Part IV simply makes that structure explicit in RNN language.

A recurrent perspective also sharpens the difference between three different kinds of memory already present in the SRNN:

1. **episodic memory** - what happened, when, and in what order;
2. **relational memory** - which objects, motifs, and callbacks connect to which others;
3. **running hidden state** - what the system currently takes the chronicle to mean.

The RNN lens is most useful for the third category. It is the right mathematical vocabulary for how a loop keeps a moving semantic summary while it traverses the chronicle.

## 3. From feed-forward mapping to recurrent state

The feed-forward idea can be written, in compact form, as:

    h_l = W_l sigma(h_(l-1))

This is a one-pass transformation across layers. It is powerful, but it has no memory of what happened one moment ago. Sequence understanding requires an additional pathway that brings prior state forward in time.

The recurrent version adds an echo of the previous state:

    h_t = W_x x_t + M(h_(t-1))

where `x_t` is the current input packet and `M` is some memory function. The choice of `M` determines what kind of recurrent system we are building.

A natural early choice is the vanilla recurrent form:

    h_t = W_x x_t + W_h sigma(h_(t-1))

This is elegant because it reuses the feed-forward pattern across time. But it is also where the classic problem begins. If the same squashing and projection logic is applied at every time step, information is repeatedly transformed, compressed, and partially discarded. The system remembers a little, but not far.

That basic insight matters directly for the SRNN. The chronicle is long. It spans songs, social posts, searches, discoveries, and story fragments over long time ranges. A memory mechanism that repeatedly reinterprets everything without a preservation path will not be good enough for durable callbacks or long-range story continuity.

## 4. Why vanilla recurrence is not enough for the SRNN

The updated RNN notes you provided make the problem unusually clear: the same operation that works well for feed-forward abstraction is often the wrong operation for memory preservation. A feed-forward path is supposed to discard nuisance variation and compress toward a useful output. A memory path needs a place where important information can travel forward with limited distortion.

For the SRNN, vanilla recurrence fails in at least four ways.

### 4.1 Long-range story loss

A track that introduces a motif, a post that names a feeling, or a discovery that opens a new frame may need to influence interpretation much later. Purely recursive re-projection tends to wash this out.

### 4.2 Multi-source dilution

The mixed chronicle includes track, social, discovery, web, and story objects. A naive recurrent state tends to collapse these source differences too aggressively unless the memory pathway is selective.

### 4.3 Narrative overwriting

The answer layer wants multiple valid readings. A single undifferentiated recurrent state can too easily overwrite subtle but useful alternate storylines.

### 4.4 Loop specialization pressure

The seven-loop ensemble only works well if each loop can retain different kinds of evidence at different rates. The social loop should not forget people and timestamps at the same rate that the motif loop forgets visual details, and the narrator loop should not preserve everything with equal strength.

In short, the SRNN needs not just recurrence, but controlled recurrence.

## 5. Leaky memory, gated memory, and why they fit the project

### 5.1 Leaky integration

The simplest repair is a leaky memory:

    h_t = alpha h_(t-1) + W_x x_t

with `0 <= alpha <= 1`.

When `alpha = 0`, there is no memory. When `alpha = 1`, the system becomes a pure accumulator and risks semantic hoarding. For values in between, recent context stays strong while older context fades gradually.

This is already a useful model for the SRNN. Some evidence should persist strongly for only a short window. Other evidence should decay slowly across longer arcs. A leaky integrator captures this better than a pure vanilla RNN.

### 5.2 Why one global leak is still insufficient

A single global `alpha` does not match the chronicle's structure. A lyric callback might need to survive across a long run of tracks. A transient visual detail from one clip may need to vanish quickly. A social timestamp may need to remain available for ranking even after the surrounding language fades.

The SRNN therefore needs selective forgetting, not only uniform decay.

### 5.3 Gated recurrence

The next step is a learned or policy-driven gate. In its general form:

    f_t = sigma(W_f [h_(t-1), x_t, q_t, u_t])
    i_t = sigma(W_i [h_(t-1), x_t, q_t, u_t])
    h_t = f_t odot h_(t-1) + i_t odot h_t_tilde

where `f_t` is a forget gate, `i_t` is an input or update gate, `q_t` is query context, `u_t` is loop context, and `h_t_tilde` is the proposed new content.

The importance of this for the SRNN is conceptual rather than dogmatic. The project does not need to copy textbook LSTM plumbing line-for-line. What it needs is the principle that retention should be context-dependent.

### 5.4 GRU and LSTM interpretation for SRNN

The notes you uploaded emphasize a useful simplification: GRUs and LSTMs differ in plumbing, but they share the same essential move - a learned adaptive valve on the echo. That is the point we should import.

For the SRNN:

- a **GRU-like interpretation** is appropriate where one compact loop state is enough and the system mainly needs a clean retain-vs-update choice;
- an **LSTM-like interpretation** is appropriate where one state should act as durable memory and another should act as the current public expression used for narration, ranking, or output.

This distinction maps cleanly onto the architecture already forming in the earlier papers.

## 6. Recasting RNNs in the SRNN ontology

Section 1.1 established the neuron/synapse mapping. Here we expand it into a working recurrent vocabulary.

The key translation bears repeating:

- in a standard RNN, the native units are abstract neurons and the connections are learned weights;
- in the SRNN, the native units are **realized base objects** and the connections are **realized meta-object overlaps**.

That means the neurons of the system are not hidden tensor slots alone, but tracks, posts, discoveries, searches, story fragments, and daemon events — each carrying real content, real timestamps, and real meta-object annotations. The effective synapses are every shared genre tag, every recurring lyrical motif, every matching mood or theme, every common artist reference, every overlapping visual object, every shared tag from a social post. When two base objects share many meta-objects, the synapse between them is strong. When they share few or none, they are weakly connected.

The **connective density** between any two neurons in the collection can be measured as:

    synapse_weight(c_i, c_j) = Σ_k w_k · overlap(m_k(c_i), m_k(c_j))

where `m_k` is the k-th meta-object category (genre, motif, mood, tag, artist, etc.) and `w_k` is a category weight. This is already computable from the `srnn_meta_objects` and `srnn_connections` tables.

This produces a media-native recurrent view:

- `c_t` = current chronicle object (one neuron in the stream);
- `x_t` = compact meta-summary or observation packet for `c_t` (the neuron's local feature set);
- `h_t^(i)` = branch-local hidden state for loop `i` (the accumulated memory at this point);
- `m_t` = retrieved static or semi-static memory from the external memory plane;
- `g_t` = loop-specific retention and update gates;
- `s_t` = synaptic context — the meta-object overlaps between `c_t` and recently visited neurons;
- `y_t` = current explanatory or predictive output.

The recurrence is therefore not over raw frames or tokens alone. It is recurrence over normalized chronicle packets, where every packet has both its own features (neuron content) and its connections to other packets (synaptic context from shared meta-objects).

### 6.1 How meta-objects form the synaptic web

Each base object in the SRNN has a set of extracted meta-objects stored in `srnn_meta_objects`: genre tags, moods, themes, lyrical motifs, detected visual objects, named entities, colors, and social tags. When a cognition loop steps from neuron `c_{t-1}` to neuron `c_t`, it can measure:

1. **direct synaptic overlap** — which meta-objects appear in both `c_{t-1}` and `c_t`;
2. **neighborhood synaptic support** — which meta-objects in `c_t` also appear in the recent window of neurons;
3. **long-range synaptic callbacks** — which meta-objects in `c_t` appeared much earlier in the chronicle but have been absent for many steps.

These three measurements already exist implicitly in the `phi_step` pipeline (motif masses, genre accumulation, story axes with decay). Part IV makes them explicit as the synaptic layer of the recurrent network.

### 6.2 Cross-neuron meta-object communication via Redis

A critical capability the SRNN needs is the ability for any cognition loop to request meta-object information about any base object in the entire collection, not just the ones it has recently visited. This is analogous to how a biological neural network can activate distant neurons via long-range axonal connections.

The existing `FederationBus` (Redis Sentinel HA, 3 sentinels, quorum=2) already provides:

| Redis DB | Purpose | Current Use |
|---|---|---|
| 0 | Heartbeats | Worker health, TTL 60s |
| 1 | Work queue | Sorted sets by priority |
| 2 | Locks | Distributed coordination |
| 3 | Events | Pub/sub (cognition channel) |
| 4 | Cache | TTL-based |

**New capability — DB 4 as meta-object exchange cache:**

When a cognition loop encounters a meta-object that suggests a long-range connection (e.g., a recurring lyrical phrase, a named entity that appeared months ago), it should be able to:

1. **Publish a meta-object query** to Redis DB 3 (pub/sub): `{"type": "meta_query", "meta_object": "dark_ambient", "requesting_loop": "social", "context": {...}}`
2. **Cache meta-object summaries** in Redis DB 4 (TTL-based): hot meta-object → list of base objects that carry it, with timestamps and strengths
3. **Read cross-loop meta-object state** from Redis DB 4: when the social loop discovers a motif, the storyboard loop can see it immediately without re-querying Milvus

This turns Redis into a **synaptic bus** — a real-time channel through which meta-object (synapse) information flows between cognition loops. Any loop can publish a meta-object observation, and any other loop can subscribe to and query those observations. The vector database (Milvus) remains the authoritative store, but Redis provides the low-latency exchange layer for real-time cognition.

The implementation path:

```python
# In loop.py — publish meta-object observation
if self.redis_bus and significant_meta_objects:
    self.redis_bus.publish('meta_exchange', {
        'loop_id': self.loop_id,
        'track_number': track_number,
        'meta_objects': significant_meta_objects,
        'timestamp': time.time(),
        'native_index': self.state.native_index,
    })

# In loop.py — query meta-object cache
def _query_meta_cache(self, meta_object_name: str) -> list:
    """Ask Redis for recent base objects carrying this meta-object."""
    cached = self.redis_bus.cache_get(f'meta:{meta_object_name}')
    if cached:
        return json.loads(cached)
    # Fallback to Milvus query
    return self._query_milvus_meta(meta_object_name)
```

## 7. A proposed SRNN recurrent cell

A practical v0 cell for the project can be written as:

    p_t = Packet(c_t, x_t, e_t, r_t, s_t)
    f_t^(i) = Gate_f^(i)(h_(t-1)^(i), p_t, q, u_t)
    i_t^(i) = Gate_i^(i)(h_(t-1)^(i), p_t, q, u_t)
    a_t^(i) = SynapticAccumulator^(i)(p_t, G_meta, R_cache)
    h_t_tilde^(i) = Proposal^(i)(h_(t-1)^(i), p_t, m_t)
    h_t^(i) = f_t^(i) odot h_(t-1)^(i) + i_t^(i) odot h_t_tilde^(i) + a_t^(i)

where:

- `Packet(...)` constructs a normalized chronicle packet (see §8), now including synaptic context `s_t`;
- `Gate_f` decides what to preserve (implements per-loop decay policies);
- `Gate_i` decides what new content to admit;
- `SynapticAccumulator` injects meta-object overlap signals and long-range connections — **this is a new component to be built in Phase 4B**, replacing the earlier "CallbackAccumulator" concept with a more precise mechanism. It reads from the Redis meta-object exchange cache (§6.2) and the `srnn_connections` graph to surface synaptic signals from distant neurons;
- `Proposal` builds the candidate state update;
- `m_t` carries retrieved memory from the Part II conditional-memory plane;
- `G_meta` is the meta-object graph from `srnn_meta_objects`;
- `R_cache` is the Redis meta-object exchange cache.

This formulation does four things that matter for the SRNN.

First, it keeps the system interpretable: every update can be logged as a packet plus a gate decision. Second, it respects the existing graph-and-memory architecture instead of pretending the chronicle is a flat token stream. Third, it leaves room for symbolic gate policies in Lisp even when parts of the proposal function are numeric. Fourth, it uses the Redis synaptic bus to give each loop visibility into meta-object observations from other loops, enabling cross-loop cognition without coupling loop implementations.

## 8. Chronicle packets, not raw tracks

The recurrent unit in this project should be the chronicle packet, not the track alone. A packet should be able to summarize any source type:

- track packet,
- social packet (Facebook or Bluesky post with real date),
- discovery packet (web search result with query context),
- web archive packet (captured article or document fragment),
- story packet (generated narrative fragment),
- daemon event packet (transition, decision, memory write).

A good packet format should include:

**Neuron identity:**
- `source_type` — track | social | discovery | web_archive | story | daemon_event
- `source_id` — primary key in the source table
- `canonical_ts` — real-world timestamp (critical for temporal binding)
- `track_number` — matched track if applicable (links social posts to playlist items)

**Neuron content:**
- `story_axes` — from `MetaSummaryBuilder` (social tags, themes, moods)
- `motif_masses` — from meta-object extraction
- `evidence_quality` — source-specific confidence
- `embedding_ref` — Milvus collection + ID for vector retrieval

**Synaptic context:**
- `linked_object_ids` — other base objects sharing meta-objects with this one
- `meta_object_overlap` — dict of meta-object → overlap score with recent neurons
- `callback_refs` — long-range connections to distant neurons via shared meta-objects
- `redis_meta_signals` — cross-loop meta-object observations from the Redis exchange bus

**Query and precision:**
- `query_context` — active question or search context
- `precision_weight` — how much this packet should influence the answer

That keeps the recurrent cell aligned with the chronicle normalization work already planned in Part III and the refactor plan. The `canonical_ts` field is especially important: it is what lets the system interleave playlist tracks (which have arrangement order but may lack real-world dates) with social posts (which carry `published_at` dates), creating the unified temporal stream that enables referential cognition.

## 9. Loop-specific recurrent styles

The cognition loop architecture can now be made more concrete by assigning each loop a different recurrent style. The following table maps the document's loop families to the implemented code:

| Loop family (this document) | Code loop_type | Status | File/method |
|---|---|---|---|
| Chronological anchor | `chronological` | ✅ implemented | `loop.py:_load_chronological_tracks()` L284 |
| Exploratory / motif | `exploratory` | ✅ implemented | `loop.py:_load_exploratory_tracks()` L297 |
| Thematic / story-axis | `thematic` | ✅ implemented | `loop.py:_load_thematic_tracks()` L304 |
| Social resonance | `social` | ✅ implemented | `loop.py:_load_social_tracks()` L316 |
| Storyboard ensemble | `storyboard` | ✅ implemented | `loop.py:_load_storyboard_tracks()` L330 |
| Replay / comparison | `replay` | ✅ implemented | `loop.py` (uses chronological loader) |
| Contrastive | `contrastive` | ✅ implemented | `loop.py:_load_contrastive_tracks()` |
| Narrator | `narrator` | ✅ implemented | `loop.py:_load_narrator_tracks()` |

### 9.1 Chronological anchor loop (`chronological`)

This loop should use the most conservative gating. It is the continuity-preserving loop and should behave more like a leaky integrator with small query-dependent adjustments. It follows the daemon's main arrangement and provides the baseline timeline against which other loops are compared.

### 9.2 Exploratory / motif loop (`exploratory`)

This loop walks random chain segments to discover distant motifs. It should use stronger retention on repeated phrases, entities, and symbolic motifs. It is the loop most likely to benefit from long motif-memory tails. Because it shuffles the order, its gating should weight meta-object overlap (synaptic strength) more heavily than temporal proximity.

### 9.3 Thematic / story-axis loop (`thematic`)

This loop walks story-linked sub-chains filtered by genre or web metadata. Its recurrent style should preserve story axes and themes at a higher rate than raw audiovisual features. It naturally aligns with the `STORY_AXIS_DECAY = 0.94` constant in `phi.py`.

### 9.4 Social resonance loop (`social`)

This loop should preserve social timestamps, named people, artist mentions, sentiment shifts, and repeated self-description more strongly than audiovisual texture. It orders tracks by their social post dates (`MIN(published_at)` from `srnn_social_chronicle`), which means its temporal axis is real-world human time rather than playlist arrangement order. This makes it the primary loop for referential cognition — binding what the user was posting about to what they were listening to.

### 9.5 Storyboard ensemble loop (`storyboard`)

This loop walks tracks having social, discovery, or story evidence (UNION ALL of `srnn_social_chronicle` + `srnn_discoveries` + `srnn_story_log`). It draws from all chronicle sources and should use a balanced gating that weights each source type according to its evidence quality. Its synaptic accumulator should read from the Redis meta-object exchange to see what the other loops have discovered.

### 9.6 Replay / comparison loop (`replay`)

This loop replays historical sequences for state comparison. Its gating should be deterministic and reproducible so that state-drift measurements are meaningful.

### 9.7 Contrastive loop (`contrastive`)

This loop is now implemented as a counter-reading traversal that prioritizes
under-explored tracks. The next improvement is to add explicit anti-majority
gating so evidence strongly favored by other loops receives a suppression
factor while underrepresented but well-grounded evidence receives an admission
boost. See Part III §4.6 for the fuller strategy.

### 9.8 Narrator loop (`narrator`)

This loop is now implemented as a cross-loop trace reader for integrated
narration. It should eventually behave more like an LSTM-style split between
durable memory and current narrative expression, with a memory of the whole
evidence arc plus a cleaner outward state for prose composition. See Part III
§4.7 for the next refinement.

## 10. Relation to `Phi`

Part I established the canonical recurrence operator:

    h_t = Phi(h_(t-1), b_t, x_t, u_t)

Part IV does not replace that. It clarifies how `Phi` can be decomposed.

A practical reading is:

    Phi = Bridge + Packetize + Gate + Update + Observe

In other words, `Phi` already is the project's recurrent cell. Part IV simply argues that the update stage should become more explicitly gated and loop-aware.

For the canonical daemon, that does not require a black-box trainable RNN. It only requires that the update step expose retention and admission choices in a form that can later be made trainable, symbolic, or hybrid.

## 11. Relation to predictive coding and Part III ranking

Part III already moved the loop ensemble toward a predictive interpretation: each loop should not only describe the chronicle after the fact but maintain a running expectation about what evidence should appear next.

That fits naturally with recurrence. For loop `i`, define:

    x_hat_(t+1)^(i) = G_i(h_t^(i), q, u_t)
    e_(t+1)^(i) = x_(t+1) - x_hat_(t+1)^(i)

This means the recurrent state is not only a memory carrier but also a prediction state. The better the hidden state summarizes the chronicle, the better the loop predicts the next packet. This gives the ranker a clean reason to care about recurrent quality rather than only descriptive style.

**Connection to existing CognitionState fields:** The live code already has two fields that do simple versions of this:

- `coherence_score` (EMA with `COHERENCE_ALPHA=0.15`) — measures skip-coherence between consecutive steps. A predictive version would replace the post-hoc coherence check with an explicit prediction: "given hₜ, what connection score do I expect to the next neuron?" The prediction error is the discrepancy.
- `energy_curve` (EMA with `ENERGY_ALPHA=0.2`) — tracks position on an energy arc. A predictive version would forecast the next energy level and measure surprise when it changes.

The proposed `prediction_packet` and `prediction_error_packet` (§13.1) generalize these into full-packet predictions rather than single-scalar predictions.

In the architecture as a whole:

- the recurrent cell explains how a loop carries context;
- predictive coding explains how that loop is scored against future evidence;
- ranked-transfer merge explains how multiple recurrent readings become one English answer.

## 12. What should stay symbolic and exact

The earlier papers draw a strong line between the canonical meaning layer and the experimental numeric support planes. Part IV preserves that line.

The following should remain explicit, inspectable, and exact in the canonical path:

- one-based native chain identity,
- null vs absent vs measured zero distinctions,
- event ordering,
- loop identity,
- reinforcement deltas,
- recurrence-chain structure,
- branch provenance,
- answer evidence refs.

This means the first implementation of recurrent gates does not need to be end-to-end differentiable. A hand-authored or hybrid gate policy is acceptable so long as it is stable, inspectable, and compatible with later learning.

## 13. Duotronic semantic witness bridge

### 13.1 Why the SRNN needs a concept of temporal and structural distance

The recurrent cell operates over a chronological stream, but it has no built-in geometric representation of *how far apart* two neurons are in time or in meta-object space. The decay constants (`GENRE_DECAY`, `THEME_DECAY`, `STORY_AXIS_DECAY`) produce exponential forgetting, but they don't give the system a way to *represent* temporal distance as a first-class object that can be compared, combined, and reasoned about.

The Duotronic encoding system (`srnn/duotronic/encoder.py`) already solves a version of this problem: it maps numeric values to polygon witness configurations — geometric objects with rotational symmetry, vertex activations, and a canonical lattice representation. The key insight is that this same framework can be applied semantically.

### 13.2 What a semantic witness encodes

A semantic witness extends the Duotronic polygon witness from digit-encoding to encoding temporal and structural properties of the relationship between two neurons:

| Property | What it encodes | How to compute it |
|---|---|---|
| **Temporal distance** | How far apart two base objects are in real time | `abs(canonical_ts(c_i) - canonical_ts(c_j))` quantized to base-B digits |
| **Arrangement distance** | How far apart in the playlist arrangement | `abs(native_index(c_i) - native_index(c_j))` quantized |
| **Meta-object density** | How many meta-objects overlap between two neurons | `len(meta_objects(c_i) ∩ meta_objects(c_j))` quantized |
| **Synaptic strength** | Weighted overlap of meta-objects | `synapse_weight(c_i, c_j)` from §6 quantized |
| **Source-type pair** | The types of the two neurons | 2-digit code: (track=1, social=2, discovery=3, web=4, story=5, daemon=6) |

Each of these numbers gets encoded as a polygon witness using the existing `DuotronicEncoder`. The resulting polygon lattice is a compact geometric representation of the *relationship quality* between two neurons.

### 13.3 How witnesses help the RNN

With semantic witnesses, the recurrent cell gains several capabilities:

1. **Time-awareness:** The system can represent "this social post is 3 days before this song" and "this post is 6 months before this song" as geometrically distinguishable objects, not just different floating-point magnitudes.

2. **Cross-neuron meta-object retrieval:** When a loop wants to check whether a meta-object from neuron `c_t` also appears in some distant neuron `c_j`, the semantic witness for the pair `(c_t, c_j)` tells the loop how much to trust that connection based on temporal distance, arrangement distance, and meta-object density.

3. **Redis-mediated witness exchange:** When a cognition loop publishes a meta-object observation to the Redis exchange bus (§6.2), it can include the semantic witness for the connection. Other loops receiving the observation can then evaluate the geometric quality of the connection without re-computing it.

4. **Witness-aware gating:** The `Gate_f` and `Gate_i` functions in the recurrent cell (§7) can use the semantic witness lattice as input, giving the gates a structured geometric concept of distance rather than just a scalar decay constant.

### 13.4 Implementation sketch

```python
# srnn/cognition/witness.py

from srnn.duotronic.encoder import DuotronicEncoder

class SemanticWitness:
    """Encode inter-neuron relationships as Duotronic polygon witnesses."""

    def __init__(self, base: int = 12):
        self.encoder = DuotronicEncoder(base=base)

    def compute(self, c_i: dict, c_j: dict, meta_overlap: dict) -> dict:
        """Build a semantic witness for the relationship between two neurons."""
        temporal_dist = abs(c_i['canonical_ts'] - c_j['canonical_ts'])
        arrangement_dist = abs(c_i.get('native_index', 0) - c_j.get('native_index', 0))
        meta_density = len(meta_overlap)
        synapse_weight = sum(meta_overlap.values())

        # Quantize and encode each dimension
        return {
            'temporal': self.encoder.encode_scalar(temporal_dist),
            'arrangement': self.encoder.encode_scalar(arrangement_dist),
            'density': self.encoder.encode_scalar(meta_density),
            'strength': self.encoder.encode_scalar(synapse_weight),
            'source_pair': (c_i['source_type'], c_j['source_type']),
        }
```

This keeps the witness system inspectable (every polygon is a deterministic geometric object) and compatible with the canonical path discipline established in §12.

### 13.5 Part VI upgrade: the recurrent witness-state

Part VI (2026-04-08) extends the witness from a static per-packet map into a two-level temporal design:

- **Level 1 (object witness):** `W_t = Γ(b_t, x_t, c_t)` — the canonical packet witness already defined above. This is implemented as `WitnessSignature` / `WitnessSectorProjector`.
- **Level 2 (recurrent witness-state):** `W̃_t = Ψ(W̃_{t-1}, W_t, h_{t-1}, b_t, x_t, u_t)` — a temporal witness process carrying family persistence, callback residue, decay-adjusted motif mass, sector confidence traces, coherence drift, and regime hints.

The extended chain update becomes:

    h_t = Φ*(h_{t-1}, b_t, x_t, u_t, W_t, W̃_t, r_t)

Each loop can also carry its own branch-local witness-state:

    W̃_t^(ℓ) = Ψ^(ℓ)(W̃_{t-1}^(ℓ), W_t, h_{t-1}^(ℓ), b_t, x_t, u_t)

This preserves the Part IV discipline: the witness participates in temporal cognition but does not replace the canonical hidden state. See Part VI for the full mathematics, implementation sequence, and experimental extensions (CPC witness learning, continuous-time Neural CDE, HSMM durations, switching dynamics).

## 14. Suggested code changes

Part IV suggests the following additions or refinements to the current codebase.

### 14.1 Extend `CognitionState`

The current `CognitionState` has 19 fields across 4 memory layers (identity, episodic, semantic-object, relational, latent-running). Add a fifth layer:

```
# ── Recurrent memory (layer 5) ──────────────────────────
short_state_vector: list = field(default_factory=list)   # GRU-like compact state
long_state_vector: list = field(default_factory=list)    # LSTM-like durable memory
cell_state: dict = field(default_factory=dict)           # loop-specific cell internals
gate_history: list = field(default_factory=list)         # last N gate decisions
prediction_packet: dict = field(default_factory=dict)    # what the loop expects next
prediction_error: dict = field(default_factory=dict)     # residual from last prediction
retention_profile: dict = field(default_factory=dict)    # per-category retention rates
loop_profile: str = "default"                            # gate preset name
synaptic_cache: dict = field(default_factory=dict)       # recent meta-object overlaps
```

This keeps the system compatible with both GRU-like and LSTM-like interpretations while adding the synaptic and predictive fields.

### 14.2 Add a dedicated recurrent cell module

Suggested file:

    srnn/cognition/rnn_cell.py

Responsibilities:

- build loop-specific gate policies,
- apply recurrent updates over chronicle packets,
- read from the Redis meta-object exchange (§6.2),
- use semantic witnesses (§13) for relationship quality,
- expose interpretable gate diagnostics,
- support symbolic, heuristic, and trainable backends.

### 14.3 Add packet and gate helpers

Suggested files:

    srnn/cognition/packet.py
    srnn/cognition/gates.py
    srnn/cognition/witness.py

Responsibilities:

- normalize source objects into packet form (aligning with Part III chronicle normalization contract §9.1),
- compute retention weights from evidence quality, source type, query intent, and synaptic support,
- encode inter-neuron relationships as Duotronic semantic witnesses,
- expose packet-to-state feature maps.

### 14.4 Add Redis meta-object exchange layer

Suggested additions to:

    srnn/cognition/loop.py (publish/subscribe)
    federation/redis_bus.py (meta_exchange channel, DB 4 cache helpers)

Responsibilities:

- publish significant meta-object observations on each `phi_step`,
- cache hot meta-objects with TTL in Redis DB 4,
- subscribe to cross-loop meta-object events,
- provide `_query_meta_cache()` fallback to Milvus.

### 14.5 Add recurrent diagnostics

Suggested file:

    srnn/cognition/rnn_diagnostics.py

Responsibilities:

- measure state drift,
- plot retention histories,
- surface gate saturation,
- identify loops that hoard vs loops that forget too fast.

### 14.6 Keep the canonical daemon simple

The daemon path should call the recurrent cell in a stable, deterministic mode. Experimental trainable variants should live on worker or replay paths first.

## 15. Training stance

This project should not begin by training a huge end-to-end RNN over everything. That would likely blur the ontology before the contracts are stable.

A better order is:

1. implement the recurrent cell symbolically or heuristically;
2. log packets, gates, predictions, and residuals;
3. benchmark recurrent quality on real storyboard tasks;
4. train small loop-local proposal models where the value is clear;
5. only later consider richer trainable recurrent modules.

This sequencing matches the broader build discipline already established in the earlier papers: preserve the meaning layer first, then experiment around it.

## 16. Build plan for Part IV

### Phase 4A - formalize recurrent-state fields

Deliverables:

- recurrent extensions to `CognitionState` (layer 5 fields from §14.1)
- packet schema additions aligned with §8
- loop-profile registry matching §9 loop table
- synaptic context fields for meta-object overlaps

### Phase 4B - implement the recurrent cell and synaptic accumulator

Deliverables:

- `rnn_cell.py` with loop-dispatch
- heuristic `Gate_f` and `Gate_i` using existing decay constants
- `SynapticAccumulator` reading from `srnn_connections` graph and Redis meta-object cache
- `witness.py` for Duotronic semantic witness encoding (§13)

### Phase 4C - implement Redis meta-object exchange

Deliverables:

- meta-object publish in `loop.py` on each `phi_step`
- Redis DB 4 cache helpers in `federation/redis_bus.py`
- `_query_meta_cache()` with Milvus fallback
- cross-loop meta-object subscription

### Phase 4D - connect to existing loops

Deliverables:

- loop-specific gate presets for all 6 implemented loop families + 2 planned
- replay-safe branch-local state updates
- narrator loop split-memory mode (pending narrator loop implementation)

### Phase 4E - add predictive outputs

Deliverables:

- `prediction_packet` based on generalized `coherence_score` and `energy_curve`
- `prediction_error` residual
- fit metrics exposed to the ranker

### Phase 4F - add diagnostics and dashboards

Deliverables:

- gate history inspection
- state-drift charts
- loop memory-profile comparison
- semantic witness visualization

### Phase 4G - optional training and benchmarking

Deliverables:

- small learned proposal models
- CPC-informed packet encoders
- ePC-informed worker-side recurrence experiments

## 17. Acceptance criteria

A real Part IV implementation should satisfy the following tests.

1. loop-local recurrent state persists across chronicle steps in a way that is inspectable;
2. gate behavior differs meaningfully across loop families;
3. long-range meta-object callbacks (synapses) survive better than in the current ungated baseline;
4. social chronology improves at least some recurrent predictions — particularly when dated social posts are interleaved with playlist tracks;
5. the narrator loop benefits from split long-memory vs output-state design;
6. prediction error and gate diagnostics explain why one loop outranks another;
7. no recurrent extension corrupts the canonical daemon's event ordering or bridge semantics;
8. the Redis meta-object exchange bus allows cross-loop meta-object visibility without coupling loop implementations;
9. Duotronic semantic witnesses produce geometrically distinguishable representations for different temporal and structural distances;
10. the synaptic accumulator correctly surfaces shared meta-objects between the current neuron and distant neurons.

*Part VI additions:*

11. the recurrent witness-state `W̃_t` accumulates family persistence and callback residue across steps;
12. witness-state decay operates independently from canonical state decay;
13. branch-local witness-states `W̃_t^(ℓ)` remain isolated per loop;
14. witness trajectory contributes to ranking via `WTraj_ℓ` (persistence, drift, callback resolution).

*Part VII additions:*

15. worker-loop recurrence runs on bounded cheap math (int8 quantized, sketch-backed) without corrupting coordinator commits;
16. polygonal operator prototypes produce canonical, family-aware, bit-efficient representations competitive with sparse matrices for witness-family transitions and gate banks;
17. search prefilter (binary signatures → compressed sidecar → float rerank) preserves acceptable candidate recall;
18. canonical safety gates pass: no commit-ledger corruption, no null coercion, no replayability loss.

## 18. Final recommendation

The SRNN should not become an RNN in the narrow, textbook sense. It should become more rigorously recurrent in the way its existing architecture already implies.

That means:

- keeping the chronicle as the native substrate,
- treating base objects as the system's neurons — the realized representational units,
- treating shared meta-objects as the system's synapses — the realized connections between neurons,
- using gated hidden state to preserve what matters and forget what does not,
- using Duotronic semantic witnesses to give the system a geometric concept of temporal and structural distance,
- using Redis as a synaptic bus for real-time meta-object exchange between cognition loops,
- binding chronologically dated social posts to the playlist timeline to enable referential cognition,
- letting each cognition loop embody a distinct recurrent memory style,
- and feeding those loop states upward into predictive ranking and English synthesis.

Part I gave the project its ontology. Part II gave it support planes for efficiency and external memory. Part III gave it a ranked storyboard ensemble. Part IV gives it a more explicit recurrent-memory discipline, a neuron/synapse interpretation grounded in real media objects and their actual meta-object connections, and three new architectural components — temporal binding, semantic witnesses, and the Redis meta-object exchange — that let the system carry a rich, inspectable, cross-loop memory of its entire chronicle through time. Part VI (2026-04-08) further extends the witness from a static packet signature into a recurrent temporal process with its own update map `Ψ`, giving the SRNN a missing middle layer between local packet signatures and full chain semantics. Part VII (2026-04-08) then splits the chain semantics into exact canonical commits and cheap approximate worker-loop recurrence, adding a practical cheap-math program (int8 quantization, Count-Min Sketch, FWHT, shift-add decay, sparse residuals, binary signatures), polygonal operator semantics for structured sparse transforms, and Hebbian synaptic plasticity for online `srnn_connections` reinforcement.

## References

**[I1]** Internal source design paper: *SRNN Cognition Architecture* (updated v4), 2026-04-07.

**[I2]** Internal source design paper: *SRNN Cognition Architecture, Part II*, 2026-04-07.

**[I3]** Internal source design paper: *SRNN Cognition Architecture, Part III*, 2026-04-07.

**[I4]** Internal refactor document: *SRNN Server Refactoring Plan* (updated v5), 2026-04-07.

**[I5]** Uploaded RNN notes/transcript discussing vanilla recurrence, leaky integration, gated memory, GRUs, and LSTMs.

**[I6]** Internal source design paper: *SRNN Cognition Architecture, Part VI* — Two-Level Witness Dynamics, Recurrent Witness-State, and Expanded Mathematical Capability, 2026-04-08.

**[I7]** Internal source design paper: *SRNN Cognition Architecture, Part VII* — Revised Chain Semantics, Cheap Worker Math, Polygonal Matrix Semantics, and Hardware-Agnostic Acceleration, 2026-04-08. Splits chain into coordinator/worker discipline, defines cheap-math toolkit (int8 quantization, Count-Min Sketch, FWHT, shift-add decay, sparse residuals, binary signatures, shared sketch), polygonal operator semantics, TurboQuant/Engram integration as three-part worker strategy, and Hebbian synaptic plasticity for `srnn_connections`.
