# SRNN Cognition Architecture, Part III
## Ranked Storyboard Loops, Social Chronology, and English Answer Synthesis
**Source design paper — drafted 2026-04-07**

### Abstract

Part III defines the ranking and synthesis layer that sits above the canonical SRNN cognition loop. Parts I and II established the recurrent chain semantics, the latent state update, the daemon-centered chronology, and the optional acceleration planes for compression and external memory. This document explains how the system should operate once multiple cognition loops are running over the same ingested history. The key claim is that the SRNN should not answer from a single regime label or a single nearest-neighbor path. It should answer from an ensemble of storyboard traces, each of which is an independent recurrent walk through a shared chronicle of songs, lyrics, social posts, web/search discoveries, and related meta-objects. Those traces are then ranked, filtered, and merged into English responses that remain colorful but evidence-grounded.

The ranking layer therefore becomes a second-order cognition system. The canonical daemon still owns chronology and authoritative state transitions, but the response layer compares multiple recurrent takes over the same evidence graph. The best answer is not simply the loudest loop. It is the most relevant, coherent, temporally grounded, and evidentially supported synthesis across loops.

## 1. Purpose and shift in emphasis

The cognition project has now moved beyond a simple question such as "what regime is the playlist in?" Regime detection still matters, but it is no longer the main product. The main product is a story-bearing answer surface.

The new working assumptions are:

1. cognition should be storyboard-first rather than genre-first;
2. songs are only one class of chronicle object among several;
3. social chronology is not side metadata but a core evidence stream;
4. internet search, discoveries, and web archives should feed the same recurrent graph;
5. multiple loops should be allowed to produce competing but meaningful interpretations;
6. the final answer should be an English synthesis, not a raw diagnostic vector.

In practical terms, this means the SRNN should be able to answer a question such as:

- what story is this playlist telling right now?
- what changed between the older social period and the newer track run?
- why did this dark ambient phase turn into a hopeful one?
- what callbacks keep reappearing across songs, posts, and searches?

The system does not answer those questions by forcing every object into a genre bucket. It answers them by letting multiple recurrent loops trace different story axes over the same chronicle, then ranking and merging those traces.

## 2. Shared chronicle model

### 2.1 Chronicle objects

Let the shared chronicle be:

    C = (c_1, c_2, ..., c_T)

where each chronicle object `c_t` is one of the following:

- a music track;
- a social post or social event;
- a search or discovery artifact;
- a web archive or extracted article/document fragment;
- a story fragment created by a prior loop;
- a daemon event such as a transition, decision, or memory write.

Each chronicle object carries:

- a timestamp or bounded time interval;
- a source type;
- one or more linked base objects;
- a meta-object packet;
- optional embeddings and witness signatures;
- recurrence links to older and newer objects.

### 2.2 Chronicle edges

The chronicle graph uses four edge families:

1. **temporal edges** from oldest to newest;
2. **connection edges** from similarity or reinforcement data;
3. **meta-object edges** from shared motifs, lyrics, symbols, scenes, or entities;
4. **reference edges** from social or web objects back to tracks, artists, themes, places, and prior events.

This gives a mixed graph:

    G_C = (C, E_time, E_conn, E_meta, E_ref)

The answer layer never replaces this graph. It samples or traverses it through different recurrent strategies.

### 2.3 Media-native neuron interpretation

In the SRNN's own ontology, the base objects of the chronicle act like the
system's native representational units. The "neurons" are therefore the media
objects themselves - songs, posts, searches, discoveries, story fragments, and
events - while the recurrent shared meta-objects and chronology edges act like
the effective connective fabric between them.

This matters because it changes what the loop ensemble is trying to rank.
Rather than ranking abstract genre labels or detached embeddings, the system is
ranking interpretations of how real chronicle objects activate, predict, and
refer to one another across time. Shared lyrics, repeated social phrases,
callback motifs, and reinforced links are not decoration; they are the active
connective pathways through which storyboard traces form.


## 3. From one loop to a loop ensemble

Part I defined the canonical recurrence update:

    h_t = Phi(h_(t-1), b_t, x_t, u_t)

Part III generalizes the runtime into an ensemble. Instead of one analysis pass, the system runs `n` loop variants over the same chronicle:

    L_1, L_2, ..., L_n

Each loop `L_i` has:

- its own traversal policy;
- its own retrieval emphasis;
- its own context window;
- its own motif weighting;
- its own story-construction bias;
- and its own branch-local hidden state `h_t^(i)`.

The canonical daemon remains the authoritative writer of chronology, reinforcement, and canonical chain state. The loop ensemble does not replace that authority. It reads from the shared chronicle and produces candidate storyboard traces.

## 4. Seven recommended cognition loops

The user vision already suggests a seven-loop ensemble. A good first implementation is:

**Implementation status (2026-04-08):** The full seven-loop family is now
represented in `srnn/cognition/loop.py`. The mapping between target loops and
implemented code:

| § | Target loop | Code type | Status |
|---|---|---|---|
| 4.1 | Chronological anchor | `chronological` | ✅ Primary daemon arrangement |
| 4.2 | Lyrics and motif | `thematic` | ✅ Story-linked sub-chain walk (to be specialized) |
| 4.3 | Social resonance | `social` | ✅ Social post chronological order |
| 4.4 | Discovery and search | `storyboard` | ✅ Tracks with social, discovery, or story evidence |
| 4.5 | Connection/callback | `exploratory` | ✅ Random chain segments for motif discovery |
| 4.6 | Contrastive | `contrastive` | ✅ Counter-reading / under-explored traversal |
| 4.7 | Narrator/synthesis | `narrator` | ✅ Cross-loop trace reader for integrated narration |

Additionally, `replay` is implemented for historical sequence replay.

### 4.1 Loop 1 — Chronological anchor loop

This loop walks the chronicle mostly in strict temporal order. It is the stabilizer. Its purpose is to explain the evidence stream as it actually unfolded.

Primary use:
- preserve historical continuity;
- give baseline interpretation;
- keep answer grounding tied to real sequence order.

### 4.2 Loop 2 — Lyrics and motif loop

This loop privileges lyrical fragments, repeated phrases, entities, moods, and extracted symbolic motifs. It is less interested in genre than in what keeps being said or implied.

Primary use:
- identify repeated lines or semantic callbacks;
- find image clusters and emotional arcs;
- build "what this keeps talking about" summaries.

### 4.3 Loop 3 — Social resonance loop

This loop traverses social chronology alongside tracks. It looks for songs mentioned in posts, posts that echo track language, temporal clusters around artists or moods, and repeated self-descriptions or reactions.

Primary use:
- connect private listening chronology to public or semi-public expression;
- identify song-post alignments;
- ground storyboards in lived timestamps.

### 4.4 Loop 4 — Discovery and search loop

This loop privileges web discoveries, searches, archive fragments, and enrichment results. It asks what the system was researching, discovering, or contextually surrounding the tracks with at the same time.

Primary use:
- attach outside-world context;
- explain thematic broadening or narrowing;
- connect tracks to internet-discovered frames.

### 4.5 Loop 5 — Connection and callback loop

This loop privileges `srnn_connections`, reinforcement deltas, recurrence chains, and meta-object callbacks. It answers the question: what keeps pulling the system back?

Primary use:
- expose durable callbacks;
- explain why far-apart tracks still feel linked;
- find long-range memory structures.

### 4.6 Loop 6 — Contrastive or alternate-take loop

**Status: ✅ Implemented as `contrastive`.**

This loop deliberately searches for competing interpretations. If most loops converge on grief, this loop checks whether the same evidence could support nostalgia, irony, recovery, or performance.

Primary use:
- reduce collapse onto the first plausible narrative;
- improve answer diversity;
- surface tensions inside the data.

Implementation strategy:
1. After other loops produce candidate traces, the contrastive loop receives
   their top story axes as a **suppression set**.
2. It re-traverses the same chronicle window but with inverted motif weights:
   motifs already heavily represented in other traces receive a penalty factor
   (e.g., 0.2×), while underrepresented motifs receive a boost (e.g., 3×).
3. The traversal should privilege chronicle objects whose meta-summary diverges
   from the majority interpretation, social posts that contradict the dominant
   mood, and discoveries that introduce outside-world counter-context.
4. The contrastive trace explicitly labels which claims from other loops it
   challenges, creating an `objections` field in the trace output.

Current implementation anchor in `loop.py`:
- `contrastive` is present in the loop dispatch table.
- `_load_contrastive_tracks()` prioritizes under-visited / under-explored
  tracks as a practical first approximation of an alternate reading.
- The next improvement is to add an explicit suppression set and objection
  labeling so the contrastive trace can challenge dominant claim clusters more
  directly.

### 4.7 Loop 7 — Synthesis or narrator loop

**Status: ✅ Implemented as `narrator`.**

This loop is not the final answer writer, but it is the loop most oriented toward prose. It takes candidate traces from the other loops, revisits the chronicle, and proposes an integrated long-form storyboard.

Primary use:
- draft the best long-form interpretation;
- propose section order;
- convert motif bundles into readable English.

Current implementation strategy:
1. The narrator loop reads other loop traces and revisits tracks in the order
  other loops have recently traversed them.
2. It provides a prose-oriented traversal profile that complements ranking,
  merge, and synthesis.
3. The next improvement is to make the traversal explicitly consensus-weighted
  across multi-loop chronicle objects rather than reading recent track traces
  alone.

## 5. Loop outputs as storyboard traces

Each loop should emit a structured artifact, not just a scalar score.

A loop trace `T_i` should contain:

- loop id and configuration id;
- query or prompt context;
- chronicle window used;
- visited chronicle objects in order;
- supporting meta-objects;
- a compact narrative label;
- evidence notes;
- recurrence notes;
- confidence and uncertainty notes;
- candidate short answer;
- candidate long-form statement.

A trace is therefore more like a storyboard strip than a classifier output. It should be inspectable and replayable.

## 6. Ranking stage

### 6.1 Why ranking is necessary

Once multiple loops exist, the system has a real choice problem. It cannot return all loops raw, and it cannot blindly pick the first or most confident one. The ranking stage is where answer quality is decided.

Let the loop set be:

    L = {L_1, L_2, ..., L_n}

and let each loop emit a trace `T_i` and candidate answer `A_i`.

The ranker should score each loop on several axes.

### 6.2 Core ranking features

A useful first scoring function is:

    Score_i(q) = w_r R_i + w_e E_i + w_c C_i + w_t T_i + w_m M_i + w_n N_i + w_s S_i - P_i

where:

- `R_i` = query relevance;
- `E_i` = evidence density and support quality;
- `C_i` = internal coherence of the trace;
- `T_i` = temporal fit to the requested window or chronicle question;
- `M_i` = recurrence or memory support;
- `N_i` = novelty relative to other loops;
- `S_i` = stylistic usefulness for English answering;
- `P_i` = penalties for contradiction, weak support, or overreach.

### 6.3 Feature meanings

**Query relevance.** Does the loop actually answer the user's question, or is it only generically interesting?

**Evidence density.** Are there enough concrete linked objects, not just vibes?

**Coherence.** Does the trace hold together as a story rather than a bag of motifs?

**Temporal fit.** Does the answer match the requested period, especially when social chronology is involved?

**Memory support.** Are the important claims backed by recurrence chains, callbacks, or repeated motifs?

**Novelty.** Does the loop add something the others do not?

**Stylistic usefulness.** Can this trace be turned into English that feels vivid without losing grounding?

### 6.4 Grounded colorfulness

The user-facing goal is colorful English. That does not mean hallucinated English. The response should feel expressive because it is rich in real motifs, linked timestamps, callbacks, and story motion. A good ranking term for this is not "creativity" but **grounded expressiveness**.

One practical rule is:

- colorful phrasing is allowed when it is anchored to real motif clusters or chronicle transitions;
- unsupported metaphor should be penalized;
- direct contradictions to evidence should zero out style bonuses.

## 7. Ranked-transfer merge

### 7.1 Why simple winner-take-all is weak

A pure winner-take-all ranker wastes useful secondary traces. Often the best final answer is a merge: one loop gives the clean chronology, another gives the motif callbacks, another adds social context.

### 7.2 STV-style intuition

A strong merge strategy is a **ranked-transfer** method analogous to transferable voting. Instead of electing candidates, the system elects claim clusters and answer sections.

Each loop ranks its preferred claims, motifs, or story blocks. The merge layer then:

1. selects the strongest high-support claim block;
2. reduces or transfers redundant weight from loops that already had their main contribution represented;
3. redistributes weight toward the next-compatible claim block;
4. repeats until the answer structure is filled.

This avoids the bad pattern where one dominant loop crowds out every other perspective.

### 7.3 Claim-block merge

A practical representation is:

- break each loop answer into claim blocks;
- attach evidence refs to each block;
- cluster semantically similar blocks across loops;
- assign each cluster a weighted score;
- pick top clusters while preserving diversity of loop origin;
- order them into a final answer outline.

This gives:

    FinalAnswer = Merge(ClaimClusters(T_1, ..., T_n))

## 8. Social chronology as first-class evidence

### 8.1 Why this matters

The user explicitly wants chronological social media data integrated because many songs already appear there. This is important for two reasons:

1. it provides a real external time frame for moods, references, artists, and repeated phrases;
2. it lets the storyboard layer connect songs to lived context rather than only to abstract similarity.

### 8.2 Social chronicle object model

Add a unified social chronicle pipeline that normalizes posts into chronicle objects with:

- post id;
- platform;
- canonical timestamp;
- text body;
- linked media ids;
- linked track ids or artist references;
- extracted entities and motifs;
- embeddings;
- recurrence links;
- provenance and privacy flags.

### 8.3 Social-to-track linking

The linking layer should support:

- direct mentions of song title, artist, album, lyric, or URL;
- approximate lyric overlap;
- artist/entity alignment;
- temporal proximity;
- social reactions near playback or discovery events;
- post-to-post motif callbacks.

The social chronology should then feed both the meta-object layer and the loop ensemble.

## 9. New state objects and collections

To support Part III cleanly, add or formalize these collections:

- `chronicle_objects` — normalized cross-source objects;
- `chronicle_edges` — temporal, motif, reference, and reinforcement edges;
- `srnn_social_chronicle` — normalized social posts and linked context;
- `loop_runs` — one record per loop execution;
- `loop_traces` — replayable storyboard traces;
- `loop_rankings` — ranking features and final scores;
- `answer_artifacts` — short answers, long-form answers, section plans, and summaries;
- `claim_blocks` — atomic answer units with evidence references;
- `storyboards` — persisted narrative strips or scene packets.

A minimal `loop_runs` record should include:

- loop id;
- branch id;
- query id;
- chronicle window;
- state seed;
- scoring config;
- start and end timestamps;
- output pointers.

### 9.1 Chronicle normalization contract

Every source that feeds the chronicle must produce objects conforming to a
single normalized schema. This prevents individual source adapters from
silently diverging.

**Required fields for every chronicle object:**

| Field | Type | Rule |
|---|---|---|
| `source_type` | enum | `track`, `social_post`, `discovery`, `web_archive`, `story_fragment`, `daemon_event` |
| `source_id` | string | Primary key from origin table (e.g., `track_number`, `post_uri`, `discovery_id`) |
| `canonical_ts` | int64 | Unix epoch milliseconds — the authoritative timestamp for ordering |
| `object_ref` | dict | Pointer back to the raw source record |
| `meta_summary` | dict | Compact packet from `MetaSummaryBuilder` |
| `embedding` | float[384] | Unified 384-dim nomic-embed-text vector |
| `story_axes` | list[str] | Extracted story axes (e.g., `temporal:tuesday`, `social:bluesky`, `lyrical:grief`) |
| `evidence_quality` | float | 0.0–1.0 score reflecting how much extractable evidence the object contains |
| `linked_object_ids` | list[str] | Cross-references to other chronicle objects |
| `recurrence_hash` | string | Stable hash for deduplication and callback detection |

**Source adapter responsibilities:**

| Source | Adapter | Timestamp source | Evidence quality heuristic |
|---|---|---|---|
| `music_tracks` + `srnn_features` | `adapt_track()` | `dt_events.created_at` | enrichment_level / 4.0 |
| `srnn_social_chronicle` | `adapt_social()` | `published_at` | len(content_text) > 50 ? 0.6 : 0.3 + engagement score |
| `srnn_discoveries` | `adapt_discovery()` | `discovered_at` | relevance_score |
| `srnn_web_archive` | `adapt_web()` | `archived_at` | len(extracted_text) / 2000, capped at 1.0 |
| `srnn_story_log` | `adapt_story()` | `created_at` | 0.5 (synthetic, always moderate) |
| `dt_events` | `adapt_event()` | `created_at` | 0.4 (structural, not rich content) |

This contract means every loop traverses the same object shape regardless of
whether the current step is a song, a Bluesky post, or a web discovery.

### 9.2 Chronicle edge contract

Edges between chronicle objects use four families:

| Edge family | Key | Weight derivation |
|---|---|---|
| `temporal` | `(src_ts, dst_ts)` | 1.0 for adjacent; decays by temporal distance |
| `connection` | `(src_id, dst_id)` | `srnn_connections.composite` + reinforcement |
| `meta_object` | `(src_id, dst_id, motif)` | shared motif count × confidence |
| `reference` | `(src_id, dst_id, ref_type)` | explicit link (e.g., post mentions artist, discovery references track) |

## 10. English answer synthesis

### 10.1 Short answer mode

For quick chat responses, the system should:

1. select 1 to 3 high-value claim blocks;
2. preserve temporal order when possible;
3. include just enough color to make the response feel alive;
4. keep evidence references available internally for inspection.

### 10.2 Long-form mode

For a longer answer, the system should emit:

- opening thesis;
- story arc by period or motif;
- supporting callbacks;
- tensions or alternate readings;
- concluding interpretation.

The narrator voice should come last, not first. The prose layer should be built on ranked traces, not used to invent them.

### 10.3 Example synthesis pattern

A good final answer often looks like:

- the chronological anchor loop sets the spine;
- the lyric loop adds motifs;
- the social loop supplies dates and lived context;
- the discovery loop adds outside-world framing;
- the callback loop surfaces deeper recurrence;
- the contrastive loop softens overconfidence;
- the narrator loop weaves them into one response.

### 10.4 Answer synthesis pipeline

The synthesis layer should be implemented as a three-stage pipeline:

**Stage 1: Claim-block extraction.**
Each loop trace is decomposed into claim blocks. A claim block is the smallest
unit that makes a testable interpretive statement. For example:

- "Between tracks 1200–1240, lyrical darkness increases while social posts shift
  to retrospective language."
- "The discovery of Burial's untrue.mp3 on 2025-11-03 coincides with a
  sustained ambient regime."

Each claim block carries:
- a natural-language assertion,
- a list of evidence refs (chronicle object IDs),
- a source loop ID,
- a confidence tier (strong / moderate / speculative),
- a contradiction flag (does this claim oppose another loop's claim?).

**Stage 2: Claim clustering and selection.**
Semantically similar claims from different loops are clustered (cosine
similarity > 0.75). Each cluster is scored:

    ClusterScore = max(claim_confidences) + 0.15 * num_supporting_loops
                   + 0.10 * evidence_density - 0.20 * contradiction_count

The top-K clusters are selected for inclusion in the answer, subject to a
diversity constraint: at least 2 different loops must be represented among the
selected clusters.

**Stage 3: Prose composition.**
An LLM (using the narrator loop's candidate long-form as a draft, or composing
from scratch if the narrator loop was not run) assembles the selected claim
clusters into prose. The composition prompt includes:
- the selected claim clusters in temporal order,
- evidence summaries for each cluster,
- a style directive ("colorful but grounded — every vivid phrase must be
  anchored to a real motif, timestamp, or callback"),
- a list of claims from the contrastive loop that should be acknowledged as
  tensions or alternate readings.

The hallucination guard rule is: if a claim block has fewer than 2 evidence refs,
it must be marked speculative in the output and cannot appear in a short answer.

### 10.5 Answer artifact structure

A persisted answer artifact should contain:

```json
{
  "query_id": "...",
  "short_answer": "text (1-3 sentences)",
  "long_answer": "text (3-8 paragraphs)",
  "outline": [
    {"section": "opening", "claim_cluster_ids": [...]},
    {"section": "arc", "claim_cluster_ids": [...]},
    {"section": "callbacks", "claim_cluster_ids": [...]},
    {"section": "tensions", "claim_cluster_ids": [...]},
    {"section": "conclusion", "claim_cluster_ids": [...]}
  ],
  "evidence_map": {"claim_id": ["chronicle_object_ids..."]},
  "loop_contributions": {"loop_id": "percentage_of_final_text"},
  "created_at": 1712505600000
}
```

## 11. Build plan for Part III

### Phase 6A — normalize the mixed chronicle ✅

Deliverables:
- `chronicle_objects` schema;
- `chronicle_edges` schema;
- social import pipeline;
- discovery/search normalization;
- object linking rules.

**Status:** Implemented. `srnn_social_chronicle` is populated (~37k posts), the
mixed chronicle is normalized through `srnn/cognition/chronicle.py`, and
persisted `chronicle_objects` / `chronicle_edges` artifacts now exist alongside
materialization and inspection APIs.

### Phase 6B — implement loop contracts ✅

Deliverables:
- `LoopPacket` schema — ✅ formalized as `ChroniclePacket` in `packet.py`;
- loop config registry — ✅ `CognitionLoop` in `srnn/cognition/loop.py`;
- per-loop state snapshots — ✅ `CognitionState` in `srnn/cognition/state.py` (19 fields, 4 memory layers);
- replay fixtures — ✅ `replay` loop type implemented.

### Phase 6C — implement seven loop types ✅

Deliverables:
- chronological anchor loop — ✅;
- lyrics/motif loop (as `thematic`) — ✅;
- social resonance loop — ✅;
- discovery/search loop (as `storyboard`) — ✅;
- callback loop (as `exploratory`) — ✅;
- contrastive loop — ✅;
- synthesis loop — ✅.

### Phase 6D — build ranking service ✅

Deliverables:
- ranking feature extractor — ✅;
- weighted scorer — ✅;
- contradiction penalties — partial, still improvable;
- evidence-density metrics — ✅;
- novelty controls — ✅.

### Phase 6E — build ranked-transfer merger ✅

Deliverables:
- claim-block extractor — ✅;
- clusterer / dedup layer — ✅;
- merge planner — ✅;
- short-answer composer — ✅;
- long-form composer — ✅.

### Phase 6F — expose APIs

All new cognition endpoints extend the existing `/xavi/brain/` router (live in
`xavi/app.py` line 602). Using a single prefix
keeps the API surface coherent:

- `POST /xavi/brain/loops/run`
- `GET /xavi/brain/loops/{run_id}`
- `GET /xavi/brain/rankings/{query_id}`
- `POST /xavi/brain/answers/compose`
- `GET /xavi/brain/storyboards/{query_id}`
- `GET /xavi/brain/social/chronicle`
- `GET /xavi/brain/social/links/{track_number}`
- `POST /xavi/brain/chronicle/materialize`
- `GET /xavi/brain/chronicle/objects`
- `GET /xavi/brain/chronicle/edges`
- `GET /xavi/brain/meta/chains/source/{source_type}/{source_id}`

## 12. Acceptance criteria

A real Part III implementation should pass these tests:

1. seven loops can replay the same chronicle window independently;
2. social chronology materially changes at least some storyboard traces;
3. ranking picks better answers than raw cosine or raw loop confidence alone;
4. the merge stage preserves supporting diversity instead of collapsing to one loop;
5. short answers are readable and specific;
6. long answers feel colorful without inventing unsupported claims;
7. users can inspect which loops and claim blocks produced the final answer.

## 13. Final recommendation

The proper next step is to treat the SRNN as a two-level cognition system:

- **level one:** the canonical daemon and recurrence core that own chronology and state;
- **level two:** a ranked storyboard ensemble that reads from that chronology, generates multiple recurrent takes, and merges them into English.

That lets the system do what the user actually wants: talk back in a way that feels interpretive, alive, and story-aware, while still being grounded in tracks, social history, web context, and explicit meta-object evidence.

## Appendix A — Recommended first metric weights

A useful first set of ranking weights is:

- relevance: 0.24
- evidence density: 0.20
- coherence: 0.18
- temporal fit: 0.14
- recurrence support: 0.12
- novelty/diversity: 0.07
- grounded expressiveness: 0.05

These should be treated as tunable defaults, not fixed truths.

## Appendix B — Minimal implementation checklist

- [x] build `chronicle_objects`
- [x] build `chronicle_edges`
- [x] import social chronology — `srnn_social_chronicle` populated (~37k posts), consumed by `meta_summary.py`
- [x] link posts to tracks and motifs — `_enrich_from_social()` links via `matched_track_number`
- [x] implement six loop configs — chronological, exploratory, thematic, social, storyboard, replay in `loop.py`
- [x] implement contrastive loop
- [x] implement narrator/synthesis loop
- [x] persist `loop_runs`
- [x] persist `loop_traces`
- [x] extract claim blocks
- [x] implement ranker
- [x] implement ranked-transfer merge
- [x] expose answer-composition APIs at `/xavi/brain/*`
- [ ] add storyboard inspection tools
- [x] add predictive-coding residual logging to loop traces
- [x] add precision-weighted fit terms to ranker
- [ ] train CPC chronicle encoders
- [ ] benchmark ePC workers for branch-local updates
- [ ] benchmark RuVector as graph/vector sidecar

**Part VI additions (two-level witness dynamics):**

- [ ] implement recurrent witness-state `W̃_t` with update map `Ψ` (family carryover, decay, callbacks, drift)
- [ ] add branch-local witness-state `W̃_t^(ℓ)` per loop
- [ ] add witness trajectory term `WTraj_ℓ` to ranking (persistence, callback resolution, drift control)
- [ ] persist witness-state at checkpoints and in loop traces
- [ ] expose witness-state inspection APIs

## 14. 2026 Revision B — Predictive coding, CPC, ePC, and RuVector integration

The ranking architecture becomes stronger if it is interpreted as a predictive
rather than only descriptive ensemble. The key shift is this: each loop should
not merely describe the chronicle after the fact; it should maintain a running
prediction about what chronicle evidence ought to appear next, then be ranked by
how well it explains the actual mixed sequence.

### 14.1 Predictive-coding view of the loop ensemble

For loop `i`, define a branch-local predicted packet:

    x_hat_(t+1)^(i) = G_i(h_t^(i), q, u_t)

and a residual after observing the next chronicle packet:

    e_(t+1)^(i) = x_(t+1) - x_hat_(t+1)^(i)

where `x_(t+1)` includes track features, meta-objects, social context,
discovery/search evidence, and recent callback structure. The loop now earns its
rank not only by being eloquent, but by minimizing weighted residuals over the
window.

A useful additional ranking term is therefore:

    F_i = - Sum_t || P_t^(i) * e_t^(i) ||^2

where `P_t^(i)` is a precision weight derived from evidence quality,
chronological confidence, and recurrence support.

### 14.2 Precision-weighted contradictions

Predictive coding also gives the ranker a principled contradiction penalty. A
loop that confidently predicts a hopeful continuation while the mixed evidence
shows darkening lyrical motifs, social stress markers, and low-support internet
context should be penalized more strongly than a loop making the same mistake in
a sparse evidence region.

This leads to a ranking rule that is not just “which loop sounds best?” but
“which loop best explains the data at the right precision?”

### 14.3 CPC for chronicle embedding and link learning

Contrastive Predictive Coding should be used as a pretraining layer for chronicle
representations. The best targets are:

- track windows predicting later social or discovery packets,
- social packets predicting nearby tracks and callbacks,
- discovery and archive windows predicting later motif bundles,
- story fragments predicting later confirmation or contradiction.

The output of this stage should be improved chronicle embeddings and link
features for `meta_summary`, not a replacement for the symbolic answer layer.

### 14.4 Error-based predictive coding in the worker loops

The `error_based_PC` project is especially relevant because it argues that
error-based predictive coding scales better on digital hardware than traditional
state-based variants, and that it converges much faster while remaining within a
predictive-coding framework. In SRNN terms, that makes it a strong candidate for:

- branch-local loop updaters,
- replay workers operating on long windows,
- meta-object residual scorers,
- social-to-track fit modules.

The authoritative daemon should remain simple and inspectable. The ePC-style
workers belong on the branch and replay side of the architecture.

### 14.5 RuVector in the search and coherence plane

RuVector is best treated as an experimental sidecar for graph/vector search,
metadata filtering, snapshots, and coherence experiments. Because it exposes
HNSW indexing, filtering, snapshots, graph/GNN components, and sparse inference,
it fits naturally into:

- branch-local candidate generation,
- callback-heavy graph walks,
- contradiction and coherence subgraphs,
- fast local replicas for ranking workers.

The key safety rule is unchanged: RuVector can accelerate loop search and
coherence analysis, but Milvus plus the canonical daemon remain the source of
truth until parity is demonstrated.

### 14.6 New loop-trace fields

A fully instrumented loop trace should now add:

- `predicted_next_packet`
- `prediction_error_packet`
- `precision_weights`
- `fit_score`
- `contradiction_energy`
- `candidate_search_backend` (`milvus`, `turboquant_sidecar`, `ruvector`, etc.)

This makes the ranker auditable and lets the dashboard explain not only which
loop won, but why the other loops lost.

### 14.7 Build additions

The next build steps should therefore include:

1. add residual logging to every storyboard loop,
2. add precision-weighted fit terms to the ranker,
3. train CPC chronicle encoders for social/track/discovery alignment,
4. benchmark ePC workers for branch-local update speed,
5. benchmark RuVector as a graph/vector sidecar for loop search,
6. expose contradiction-energy and fit diagnostics in the answer APIs.


## References

**[I1]** Internal refactor document: updated SRNN refactor plan reflecting Phase 6 storyboard cognition ensemble.

**[I2]** Internal source design papers: Part I and Part II of the SRNN cognition architecture.

**[I3]** Internal source design paper: Part IV — Recurrent Neural Networks, Gated Chronicle Memory, and Loop-State Design for the SRNN. Defines the neuron/synapse mapping (base objects = neurons, meta-object connections = synapses), the Duotronic semantic witness bridge, and the Redis meta-object exchange bus.

**[I4]** Internal source design paper: Part V — Decomposition, Digital Witness Sectors, and Universe-Ranked Storyboards. Defines witness-sector signatures, loop-universe decomposition, and interference-style merge.

**[I5]** Internal source design paper: Part VI — Two-Level Witness Dynamics, Recurrent Witness-State, and Expanded Mathematical Capability, 2026-04-08. Promotes the witness from a static signature to a two-level temporal design with recurrent witness-state `W̃_t` and update map `Ψ`. Witness trajectory terms `WTraj_ℓ` extend ranking with callback resolution, drift control, and family persistence.

**[I6]** Internal source design paper: Part VII — Revised Chain Semantics, Cheap Worker Math, Polygonal Matrix Semantics, and Hardware-Agnostic Acceleration, 2026-04-08. Defines cheap worker-loop math program: int8 quantized recurrence, Count-Min Sketch witness mass, sparse residuals, shift-add decay, shared sketch across loops, and binary signature first-pass retrieval. Worker loops can now run on bounded approximations while the canonical coordinator commits exact chronology. Introduces Sinkhorn divergence for storyboard coherence and Nyström approximation for social chronology kernels.

**[R1]** Predictive coding overview. Wikipedia. https://en.wikipedia.org/wiki/Predictive_coding

**[R2]** *Introduction to Predictive Coding Networks for Machine Learning*. arXiv:2506.06332v1. https://arxiv.org/html/2506.06332v1

**[R3]** Aaron van den Oord, Yazhe Li, Oriol Vinyals. *Representation Learning with Contrastive Predictive Coding*. arXiv:1807.03748. https://arxiv.org/abs/1807.03748

**[R4]** `cgoemaere/error_based_PC`. GitHub repository. https://github.com/cgoemaere/error_based_PC

**[R5]** `ruvnet/ruvector`. GitHub repository. https://github.com/ruvnet/ruvector

**[R6]** `deepseek-ai/Engram`. GitHub repository. https://github.com/deepseek-ai/Engram

**[R7]** *TurboQuant: Online Vector Quantization with Near-optimal Distortion Rate*. arXiv:2504.19874. https://arxiv.org/abs/2504.19874
