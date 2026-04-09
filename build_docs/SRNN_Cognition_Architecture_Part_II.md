# SRNN Cognition Architecture, Part II
## Compression, External Memory, and System Efficiency for the Duotronic SRNN

**Purpose.** This document is a second source paper for the SRNN cognition effort. Part I defined the native chain semantics, recurrent state, and Duotronic mathematical program. Part III defined the storyboard-first loop ensemble, ranked synthesis, and social chronology integration. Part II explains how TurboQuant, PolarQuant, and Engram-like conditional memory can be used to improve the performance of the SRNN and its surrounding subsystems without weakening the canonical cognition loop.

**Implementation stance.** The main recommendation of this paper is conservative: keep the canonical Duotronic cognition loop exact and authoritative, and apply compression and external memory first to supporting planes such as vector retrieval, cache storage, sidecar search, and agent memory. In other words, use these techniques to make the system faster, larger, and cheaper before using them to change the semantics of the chain itself.

**2026 storyboard context.** The cognition layer now operates over a mixed
chronicle of tracks, social posts (37k in `srnn_social_chronicle`), web
discoveries, archive fragments, and story log entries. The loop ensemble
produces storyboard traces ranked by relevance, evidence density, coherence, and
predictive fit. Compression and conditional memory therefore serve an expanded
observation substrate, not just a music-only pipeline.

## 1. Current baseline and why this addendum exists

The current refactor state already gives the SRNN the substrate needed for a serious cognition system. The uploaded refactor plan places the project at a state where Milvus, MinIO, etcd, Ollama, Agno, the daemon loop, the Lisp brain, and federation are already present in the architecture, with the daemon defined as the self-playing chronological walk that advances the network through time [I1]. The same document also shows that the system already has 384-dimensional embeddings for `music_tracks`, `srnn_features`, `meta_objects`, `dt_events`, and `brain_memory`, and that Milvus is now the authoritative vector store while Agno memory integration is still pending [I1].

Part I established the core mathematical view: the native media object is not merely a list, but a recurrent graph of base objects and meta-object relations; the native public index is one-based; the realized state is updated by the recurrence operator `h_t = Phi(h_(t-1), b_t, x_t, u_t)`; and the first practical observables are latent regime changes, total-variance decompositions, and skip coherence [I2].

This addendum exists because the system now faces a different question: once the cognition loop is defined, how should the surrounding numeric substrate be optimized so the SRNN can run at larger scale, across more nodes, with cheaper memory and faster retrieval?

The answer is not to replace the Duotronic theory. The answer is to add a second plane around it:

1. a **compression plane** for vectors, cache state, and sidecar search; and
2. a **conditional memory plane** for fast deterministic lookup of static or semi-static symbolic knowledge.

TurboQuant and PolarQuant fit the first plane. Engram fits the second.

## 2. A simple design rule

The most important design rule in this paper is:

**Do not quantize the meaning layer first. Quantize the transport layer first.**

In SRNN terms, the following objects should remain exact in v0:

- native one-based chain identity,
- canonical event ordering,
- recurrence updates in the authoritative daemon,
- connection reinforcement deltas,
- explicit meta-object edges,
- witness labels and bridge rules,
- symbolic Lisp decisions.

The following objects are better candidates for compression or lookup acceleration:

- float embeddings used for retrieval,
- large vector replicas and read caches,
- agent-side long-context KV caches,
- secondary search indexes,
- branch-local replay buffers,
- static motif dictionaries and phrase memories,
- story fragments, lyric shards, and pattern tables.

This separation preserves the ontology from Part I while still letting the runtime become much more efficient.

## 3. What TurboQuant and PolarQuant contribute

### 3.1 Core idea

TurboQuant is a vector quantization method aimed at preserving both reconstruction quality and inner-product quality under strong compression. The paper describes a data-oblivious, online approach that randomly rotates vectors, induces a concentrated coordinate distribution, applies scalar quantizers coordinatewise, and then uses a 1-bit Quantized JL residual stage to remove bias in inner-product estimation [R1].

The Google Research explanation presents TurboQuant as a two-stage pipeline:

1. **PolarQuant stage** for the main compression mass, and
2. **QJL residual stage** for bias correction on the remaining error [R2].

The paper reports that, for KV-cache quantization, TurboQuant achieves quality neutrality at about 3.5 bits per channel and only marginal degradation at 2.5 bits per channel, while also outperforming classical product quantization approaches for nearest-neighbor search with near-zero indexing time in the reported experiments [R1].

### 3.2 Why polar coordinates matter

PolarQuant matters because SRNN vectors, like many model vectors, are not well-behaved under naive coordinatewise quantization. High-dimensional embeddings and KV tensors often contain heavy coordinates or local outliers. PolarQuant addresses this by applying a random rotation first, then representing the rotated vector in a polar-style hierarchy where radii and angles can be quantized with lower overhead [R2].

For SRNN this matters in two places:

- embeddings stored or replicated for retrieval, and
- KV caches used by agent models during long-context inference.

### 3.3 What the current open implementations actually support

The best current evidence for immediate local experimentation is not a polished production stack but a research ecosystem.

- The official TurboQuant paper and blog establish the algorithmic claim [R1][R2].
- The `abdelstark/turboquant` Rust crate is explicitly described as **alpha**, suitable for research and benchmarking rather than production inference. It exposes CPU and experimental GPU paths, a quantized KV-cache abstraction, and a CPU-oriented ONNX real-model evaluation path [R3].
- The `llama.cpp` discussion shows active fork-based work with functional CPU, Metal, and CUDA implementations plus reported 4x to 5x KV compression versus FP16, but it also states clearly that mainline integration and universal production readiness are not there yet [R4].
- The `vLLM` path is not mature support today; the source we reviewed is an open feature request rather than an implemented backend [R5].

So the correct engineering reading is: **TurboQuant is ready for SRNN benchmarking and sidecar experimentation, not for replacing your whole inference layer today.**

## 4. What Engram contributes

### 4.1 Core idea

Engram comes from a different direction. Its claim is not primarily about compressing vectors, but about adding **conditional memory via scalable lookup**. The repository describes Engram as a complementary sparsity axis alongside MoE: not conditional computation, but conditional retrieval from static memory using deterministic addressing and O(1) lookup [R6].

The important SRNN-relevant claims are:

- lookup is deterministic rather than attention-wide,
- memory tables can be offloaded to host memory,
- the mechanism is meant to reduce the need for early layers to reconstruct static patterns repeatedly,
- the retrieved memory is fused back into the dynamic hidden state [R6].

### 4.2 Why this matters for SRNN

SRNN already has a distinction between:

- dynamic chain state (`h_t`), and
- semi-static or slowly-changing memory such as motifs, recurrence chains, story fragments, enrichment facts, and agent knowledge.

That means Engram is a natural fit conceptually. It should not be read as "swap in the DeepSeek architecture wholesale." It should be read as a design pattern for **memory that should be looked up rather than recomputed.**

For SRNN, that includes:

- lyric n-grams and phrase fragments,
- motif bundles and meta-object signatures,
- track-sequence n-grams,
- event-sequence motifs from `dt_events`,
- story fragments from `story_log`,
- persistent agent memories from `brain_memory`,
- witness-family templates,
- social-post templates and response patterns.

## 5. The three-plane model for SRNN v0

Part I gave the system a canonical cognition loop. Part II recommends splitting the runtime into three planes.

### 5.1 Plane A: the canonical cognition plane

This is the authoritative Duotronic loop.

Inputs:

- base object `b_t`,
- observed feature vector `x_t`,
- optional context `u_t`,
- prior state `h_(t-1)`.

Update:

`h_t = Phi(h_(t-1), b_t, x_t, u_t)`

Responsibilities:

- preserve native one-based indexing,
- maintain chronology,
- update reinforcement,
- update recurrence chains,
- emit canonical events,
- write authoritative state snapshots.

This remains the source of truth.

### 5.2 Plane B: the compression plane

This plane accelerates numeric transport and retrieval.

It is responsible for:

- compressed vector replicas,
- sidecar ANN search,
- compressed branch replay buffers,
- long-context KV-cache experiments,
- node-local memory reduction.

A generic notation is:

`z = Q_TQ(v; beta)`

where `v` is a float vector, `beta` is a bit budget, and `Q_TQ` is a TurboQuant-style encoder.

Reconstruction or estimator form:

`v_hat = D_TQ(z)`

or, when only similarities are needed,

`score(q, z)` is computed from the compressed representation or a low-cost estimator.

Important rule: Plane B is allowed to approximate **retrieval math**, but not **native chain identity**.

### 5.3 Plane C: the conditional memory plane

This plane stores static or semi-static structures that do not need to be re-derived on every step.

A generic notation is:

`r_t = Retrieve(k_t, M)`

where:

- `k_t` is a deterministic key built from the current state,
- `M` is a memory table,
- `r_t` is the retrieved memory payload.

The extended recurrence then becomes:

`h_t = Phi_star(h_(t-1), b_t, x_t, u_t, r_t)`

In other words, Engram-style lookup augments the recurrence operator rather than replacing it.

## 6. Where TurboQuant should go in SRNN

### 6.1 Not inside the first symbolic bridge

The first and strongest recommendation is negative:

**Do not put TurboQuant in the Lisp bridge first.**

The Lisp bridge is where you are trying to preserve exact distinctions such as:

- unknown vs absent vs measured zero,
- native index vs export index,
- witness labels and motif identity,
- causal ordering of events.

Those are bad first targets for lossy numeric compression.

### 6.2 First target: sidecar vector search

The strongest early use case is a sidecar compressed search path for large embedding collections. Your refactor already shows that the system has 384-dimensional embeddings for `music_tracks`, `srnn_features`, `meta_objects`, `dt_events`, `brain_memory`, and more, all living in Milvus [I1].

That suggests the following deployment:

- keep Milvus as the authoritative float store;
- add a compressed local search sidecar per node for hot-path recall;
- use TurboQuant or PolarQuant-derived packing only for the sidecar;
- fall back to full Milvus float search for reranking and final confirmation.

This gives you three wins:

1. smaller node-local memory use,
2. faster branch-local search on worker and resource nodes,
3. a safe way to test distortion effects without corrupting the source of truth.

### 6.3 Second target: FAISS hot-path replacement or augmentation

Your refactor notes already describe a local FAISS hot-path cache rebuilt on daemon startup while Milvus stays authoritative [I1]. That is almost a perfect insertion point.

Instead of thinking "replace Milvus with TurboQuant," think:

`Milvus (truth) -> TurboQuant sidecar / FAISS sidecar (fast local read path) -> rerank on canonical store`

The daemon can then perform:

1. compressed candidate recall,
2. float rerank on top-N,
3. recurrence update on the winning candidate.

### 6.4 Third target: agent inference caches

The agent fleet - research, coding, reasoning, DJ, curator, enricher - is exactly the sort of multi-model workload where KV-cache compression can matter. However, your current stack is centered on Ollama, not a ready-made TurboQuant backend [I1].

So the correct build path is:

- benchmark TurboQuant on a parallel inference surface first,
- keep Ollama as the production control path,
- use `llama.cpp` forks or the Rust crate as auxiliary evaluation surfaces,
- only move an SRNN agent onto a TurboQuant-capable runtime after measured wins.

Practical candidates:

- long-context research agent,
- coding agent with large source windows,
- curator agent replaying large event histories,
- narrative/story agent consuming long `dt_events` traces.

### 6.5 Fourth target: replicated node snapshots

Because the project is already federated and multi-node [I1], compressed vector replicas are also useful as shipping artifacts.

Instead of copying only float snapshots between nodes, you can also ship:

- compressed `brain_memory` shards,
- compressed `meta_objects` vector replicas,
- compressed `dt_events` embeddings,
- compressed branch histories for speculative loops.

This lowers RAM and disk pressure on worker nodes that do not need perfect local copies of the entire float substrate.

## 7. Where Engram should go in SRNN

### 7.1 First target: `brain_memory`

The refactor plan explicitly says agents still lack persistent memory and proposes a shared `brain_memory` collection for cross-agent knowledge [I1]. That is the clearest insertion point for an Engram-like subsystem.

The first version does not need the full DeepSeek implementation. It only needs the Engram principle:

- deterministic keying,
- fast lookup,
- static or semi-static tables,
- retrieval fused into dynamic reasoning.

A simple first key family could be:

`k_t = Hash(epoch, witness_family, motif_bundle, lyric_ngram, event_type, recent_track_ids)`

The payload could contain:

- prior story fragments,
- motif summaries,
- candidate transitions,
- curated callbacks,
- symbolic notes from Lisp,
- embeddings or references to embeddings,
- confidence and provenance.

### 7.2 Second target: motif and sequence memory

The daemon loop already treats recurrence chains as memory and advances chronologically through `dt_events` [I1]. An Engram-style memory table lets the system store **sequence-level regularities** explicitly.

Useful memory families include:

- track bigrams and trigrams,
- motif co-occurrence bundles,
- lyric phrase n-grams,
- social-response templates,
- witness-family transitions,
- event-pattern templates such as "dark ambient run followed by visual saturation shift."

These should live in a new store, for example `engram_memory`, with fields like:

- `key`,
- `memory_type`,
- `payload_json`,
- `source_refs`,
- `weight`,
- `created_at`,
- `updated_at`,
- `embedding` optional.

### 7.3 Third target: Lisp-assisted retrieval

The Lisp layer should not become the bulk storage engine, but it is a strong candidate for **key synthesis and symbolic gating**.

Recommended split:

- Python computes numeric signatures and candidate keys.
- Lisp validates symbolic compatibility, native/export consistency, and witness-family constraints.
- Retrieved memories are returned to the daemon as symbolic packets.

That preserves Lisp as the arbiter of meaning while keeping large lookup tables in more practical stores.

## 8. The theoretical wiring

The best abstract form for the combined system is:

1. Observe the current object and export features.
2. Build a witness or key signature.
3. Retrieve compressed candidates and external memories.
4. Rerank or validate them.
5. Feed the validated payload back into the recurrence update.

In symbols:

`W_t = Gamma(x_t)`

`k_t = K(h_(t-1), b_t, x_t, W_t, u_t)`

`r_t = Retrieve(k_t, M)`

`c_t = Search_TQ(q_t, Z)`

`h_t = Phi_star(h_(t-1), b_t, x_t, u_t, r_t, c_t)`

Where:

- `Gamma` is the witness map from Part I,
- `K` is a deterministic keying function,
- `M` is an Engram-like memory table,
- `Search_TQ` is the compressed search sidecar,
- `Z` is a compressed vector shard or index,
- `Phi_star` is the recurrence operator extended with retrieved memory and compressed-search evidence.

This is the core theoretical wiring for Part II.

## 9. What should and should not be compressed

### 9.1 Good early targets

- replica embeddings in hot caches,
- branch-local search indexes,
- agent KV caches in experimental runtimes,
- compressed history windows for replay,
- worker-node copies of cold vector stores,
- bulk memory tables whose payloads are embedding-heavy,
- `srnn_social_chronicle` embeddings for branch-local social resonance loops,
- `srnn_discoveries` and `srnn_web_archive` embeddings for discovery loop sidecars,
- loop-trace embedding snapshots shipped between nodes for ranking.

### 9.2 Bad early targets

- canonical `h_t` snapshots,
- one-based native indices,
- reinforcement deltas in the authoritative loop,
- symbolic witness labels,
- control-plane state such as epoch and cursor,
- schema fields that distinguish unknown / absent / zero,
- active story-axis weights in `CognitionState.active_story_axes`,
- canonical loop-ranking scores used for answer composition.

### 9.3 Conditional targets

These are worth testing only after parity gates exist:

- compressed `brain_memory` payload vectors,
- compressed `meta_objects` embeddings in the daemon hot path,
- compressed `dt_events` embeddings for long-range narrative retrieval,
- compressed story fragments for low-priority worker loops,
- compressed `chronicle_objects` embeddings for branch-local loop replay,
- compressed claim-block embeddings for answer-merge clustering.

## 10. A concrete build plan

### Phase 0: measurement before modification

Before adding any new subsystem, record baseline metrics.

Required baselines:

- Milvus query latency by collection,
- daemon candidate-generation latency,
- agent token/sec and max usable context window,
- memory use by node role,
- skip-coherence metric quality,
- regime-detection quality,
- false-positive rate in candidate recall.

Without this, compression wins cannot be judged honestly.

### Phase 1: compressed search sidecar

Build `srnn/turbo_quant.py` into a benchmark harness first, not a mandatory dependency. Your refactor inventory already shows this file exists in the consolidated backend [I1].

Deliverables:

- exporter for selected Milvus collections to local float shards,
- TurboQuant packing path for research experiments,
- compressed candidate-recall API,
- rerank-on-float fallback,
- metrics for recall@k, latency, RAM, disk, and coherence impact.

Collections to start with:

- `brain_memory`,
- `meta_objects`,
- `dt_events`.

Do **not** start with `music_tracks`, because the canonical playlist loop already depends heavily on that path.

### Phase 2: Engram-style memory registry

Create a first `engram_memory` collection or table.

Recommended schema:

- `memory_id`,
- `key`,
- `memory_type`,
- `payload_json`,
- `source_collection`,
- `source_id`,
- `weight`,
- `ttl` optional,
- `embedding` optional,
- `created_at`,
- `updated_at`.

Initial memory families:

- lyric n-grams,
- motif bundles,
- witness families,
- event-sequence templates,
- story fragments,
- agent memo packets.

### Phase 3: daemon integration

Add two optional calls around the canonical update:

1. `compressed_candidates = search_sidecar(...)`
2. `retrieved_memory = engram_lookup(...)`

Then extend the daemon step so that only validated summaries reach the canonical recurrence update.

The daemon remains single-writer for the authoritative loop. Worker nodes may compute speculative compressed search and memory suggestions, but only the canonical coordinator loop commits state.

### Phase 4: branch and worker support

Once the canonical loop is stable, worker nodes can use compressed sidecars much more aggressively.

Good worker-node uses:

- speculative horizon planning,
- shadow replay over long history,
- narrative generation over large event windows,
- motif clustering,
- witness-family mining,
- long-context agent tasks.

This fits the current coordinator/resource/worker profile structure in the refactor plan [I1].

### Phase 5: selective inference migration

Only after the above phases should you consider moving one or more agents onto a TurboQuant-capable runtime.

Suggested order:

1. researcher agent,
2. curator agent,
3. coding agent,
4. reasoning agent,
5. DJ daemon only if the evaluation shows no semantic degradation.

The DJ daemon should be last because it is the canonical cognition clock.

## 11. Metrics and gates

Part II needs its own gates, in addition to the mathematical gates from Part I.

### 11.1 Compression gates

- recall@k versus float baseline,
- rerank agreement with float baseline,
- latency improvement,
- RAM reduction,
- storage reduction,
- stability across node restarts,
- branch replay fidelity.

### 11.2 Memory gates

- lookup hit rate,
- precision of retrieved motif bundles,
- reduction in repeated derivation work,
- story continuity improvement,
- improvement in skip-coherence prediction,
- reduction in prompt length for agent tasks.

### 11.3 Cognition safety gates

- no corruption of canonical epoch and cursor,
- no coercion of unknown to zero,
- no change in native/export bridge semantics,
- no reduction in validated coherence metrics beyond threshold,
- no regression in reinforcement behavior.

## 12. A recommended deployment map

### Coordinator node

Run:

- canonical daemon,
- float Milvus truth,
- Lisp brain,
- Engram lookup service,
- rerank service,
- event commit log.

Avoid:

- risky experimental inference backends in the authoritative path.

### Resource node

Run:

- GPU-heavy embedding and rerank jobs,
- TurboQuant benchmarking,
- long-context agent experiments,
- compressed sidecar index builds,
- batch narrative or replay jobs,
- contrastive and narrator loop workers (GPU-accelerated),
- CPC chronicle encoder training.

### Worker nodes

Run:

- compressed local vector shards,
- speculative horizon search,
- branch-local memory mining,
- low-priority Engram table generation,
- shadow replay and story synthesis,
- social-resonance and discovery loop workers,
- ePC-style branch-local predictive-coding updaters.

This preserves canonical meaning while letting the cluster exploit cheaper local replicas.

## 13. What success looks like

The success condition for Part II is not "everything is quantized." The success condition is:

- the daemon stays semantically stable,
- the vector substrate becomes cheaper and faster,
- the agents can reason over larger history windows,
- branch workers can replay more history with less RAM,
- memory retrieval becomes more explicit and less prompt-bloated,
- Lisp receives better symbolic packets rather than larger piles of floats.

If that happens, then Part II has done its job.

## 14. Final recommendation

The right next move is:

1. keep Part I as the ontology and recurrence source of truth,
2. treat TurboQuant as a sidecar compression and retrieval research layer,
3. treat Engram as a lookup-memory design pattern for `brain_memory` and motif tables,
4. wire both into the daemon only through validated summaries,
5. leave the canonical chain exact until parity metrics prove otherwise.

That gives the SRNN a credible path toward larger-scale cognition without sacrificing the parts of the theory that make it distinct.

## References

**[I1]** Uploaded internal refactor document: *SRNN Server Refactoring Plan* / `Pasted markdown.md`, dated 2026-04-07.

**[I2]** Uploaded internal math document: *Duotronic Media Chain Research Source Notes* / `Pasted text.txt`.

**[R1]** Amir Zandieh, Majid Daliri, Majid Hadian, and Vahab Mirrokni. *TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate*. arXiv:2504.19874. https://arxiv.org/abs/2504.19874

**[R2]** Google Research Blog. *TurboQuant: Redefining AI efficiency with extreme compression*. March 24, 2026. https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/

**[R3]** `abdelstark/turboquant` repository README. https://github.com/abdelstark/turboquant

**[R4]** `ggml-org/llama.cpp` discussion #20969, *TurboQuant - Extreme KV Cache Quantization*. https://github.com/ggml-org/llama.cpp/discussions/20969

**[R5]** `vllm-project/vllm` issue #38171, *Add TurboQuant Support for KV Cache Quantization*. This is an open feature request, not production support. https://github.com/vllm-project/vllm/issues/38171

**[R6]** `deepseek-ai/Engram` repository README, *Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models*. https://github.com/deepseek-ai/Engram

**[I3]** Internal source design paper: Part VI — Two-Level Witness Dynamics, Recurrent Witness-State, and Expanded Mathematical Capability, 2026-04-08. Extends witness-family templates and Engram witness keys with a recurrent witness-state `W̃_t` carrying temporal memory.

**[I4]** Internal source design paper: Part VII — Revised Chain Semantics, Cheap Worker Math, Polygonal Matrix Semantics, and Hardware-Agnostic Acceleration, 2026-04-08. Elevates TurboQuant to "numeric sidecar counterpart" and Engram to "lookup-memory counterpart" in a three-part worker strategy (TurboQuant for cheap candidate transport, Engram for cheap recall, RecurrentWitnessState for cheap temporal accumulation). Adds FWHT structured rotation for sidecar compression paths, int8 quantized worker recurrence, Count-Min Sketch witness mass, and polygonal operator language for sparse worker-side transforms.
