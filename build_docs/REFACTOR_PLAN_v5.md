# SRNN Server Refactoring Plan

> **Last updated:** 2026-04-09
> **Status:** Phase 5 complete. Phase 6 (cognition layer) is **COMPLETE**: 31/31 implementation steps done. Phase 7–10 complete (contract discipline, acceleration planes, integration hardening, cognition polish). Phase 11 (Part VI — two-level witness dynamics) is **COMPLETE**: 16/16 steps done. Phase 12 (Part VII — cheap worker math, polygonal operators, search sidecars) is **COMPLETE**: 20/20 steps done. Phase 13 (rollout hardening and compatibility cleanup) is **IN PROGRESS**: centralized worker rollout defaults, runtime diagnostics, and legacy test/schema repairs are now the active tranche. The 20-file cognition module implements all 8 loop types, gated recurrent cells, Duotronic witness bridge, 9-axis ranking (with witness_support + witness_trajectory), claim extraction, ranked-transfer merge with interference, English answer synthesis, full social chronology integration (71,579 Facebook + 427 Bluesky posts embedded), witness-sector signatures (K=8), loop-universe branch isolation, query-context (q_t) binding, SBCL phi_step bridge (JSON-RPC subprocess with circuit breaker), enriched Redis meta-object exchange (genre/theme overlap scoring, sibling observation consumption), source-type-aware temporal binding (confidence-weighted interpolation with parametric extrapolation rates), two-level witness dynamics (RecurrentWitnessState with Ψ update map, family-mass decay, callback persistence, contradiction gating, coherence drift tracking, witness regime evidence, and witness trajectory ranking), and Part VII worker/search extensions (int8 worker recurrence, sketch-backed witness mass, shift-add decay, sparse residual summaries, binary-prefiltered sidecar search, deterministic conditional-memory keys, polygonal operator prototypes, and parity/evaluation gates).

## Executive Summary

Centralize all SRNN backend logic, data, and infrastructure under
`/var/www/xavi/srnn_server/`. Eliminate SQLite as the primary database backend.
Replace it with a Docker-based Milvus + MinIO + etcd stack that natively supports
vector search, multimodal data, metadata fields, timestamps, recurrent links,
and hierarchical relationships. The system is federated: each node runs its own
Milvus instance and syncs via the existing SSH tunnel + MinIO + Redis mesh.
The Concrete CMS layer becomes a thin API proxy with zero backend logic or
direct database access.

The stack now includes Ollama (11 local LLMs, ~147 GB across 3 nodes via
distributed proxy), Agno (agent framework with 3 active agents), TrustGraph
(knowledge graph, ~50 containers), and Hovod (video platform, 5 containers).
Total: ~101 running Docker containers. The 3-node cluster (main + resource +
node2) provides 80 CPUs, 304 GB RAM, and 2 GPUs with work-stealing distributed
embedding and speculative LLM generation.

---

## 1. Current Architecture — Actual State (as of 2026-04-07)

```
/var/www/xavi/srnn_server/
├── srnn/                            ← Python backend (CANONICAL, consolidated)
│   ├── meta_objects/                ← 51-file core: extractors, enrichment, vectors
│   │   ├── api/                     ← REST routes (7 files)
│   │   ├── extractors/              ← 14 extractor modules
│   │   ├── enrichment/              ← Web enrichment pipeline
│   │   ├── similarity/              ← Similarity engine
│   │   ├── recurrence/              ← Recurrence chain analysis
│   │   ├── vector/                  ← Vector embedding + search
│   │   ├── julia/                   ← Julia math kernels
│   │   ├── lisp/                    ← SBCL symbolic reasoning
│   │   ├── standalone/              ← Self-contained node deployment
│   │   │   ├── app.py               ← FastAPI server (:8055)
│   │   │   ├── federation.py        ← Leader/worker/standalone roles
│   │   │   ├── docker-compose.yml
│   │   │   ├── Dockerfile
│   │   │   └── install.sh / deploy.sh
│   │   └── s3/                      ← MinIO config
│   ├── bsky_cataloger.py, bulk_enrich.py, model_router.py, turbo_quant.py
│   ├── cli.py, config.py, daemon.py, session.py, shuffle.py
│   ├── similarity.py, enricher.py, features.py, playlist.py
│   ├── schema.py, migrate.py, milvus_schema.py
│   ├── duotronic/                   ← Duotronic subsystem
│   ├── agent_lab/                   ← Agent experimentation
│   └── media/                       ← Media processing
│
├── db/                              ← ALL databases (canonical location)
│   ├── chat.sqlite                  (506 MB — music library)
│   ├── srnn.sqlite                  (144 MB — features, connections, state)
│   ├── duotronic.sqlite             (235 MB — duotronic events)
│   ├── facebook_data.sqlite         (95 MB)
│   ├── lyrics_vector_mining.sqlite  (28 MB) + .faiss
│   ├── media_context.sqlite         (7.8 MB)
│   ├── sear_data.sqlite             (266 KB)
│   ├── source_queue.sqlite          (152 KB)
│   ├── pipeline.sqlite              (0 — empty)
│   ├── etcd_data/                   ← etcd persistence
│   ├── milvus_volumes/              ← Milvus data
│   ├── minio_data/                  ← MinIO object storage
│   ├── faiss_indices/               ← FAISS index files
│   ├── .secrets/                    ← JWT secret (empty, needs migration)
│   ├── config/                      ← Config files
│   ├── music/                       ← Music processing scripts
│   └── processing/                  ← Frame cache, outputs
│
├── data/                            ← Private media + runtime artifacts
│   ├── music/                       ← Music files (68 GB)
│   ├── social/                      ← Facebook (37 GB) + Bluesky exports
│   ├── models/                      ← ML models
│   ├── stream/ , tmp/               ← Runtime
│   └── jwt_secret.key               ← JWT signing key (needs move to db/.secrets/)
│
├── api/                             ← Legacy route modules (imported by xavi/app.py)
│   ├── routes/                      ← 7 route files mounted in unified API
│   │   (main.py, auth.py, Dockerfile removed — dead code cleaned)
│   ├── Dockerfile                   ← Python 3.11 slim + ffmpeg + uvicorn
│   └── routes/                      ← 7 routers, ~60 endpoints
│       ├── srnn.py                  (22 endpoints)
│       ├── manager.py               (12 endpoints)
│       ├── enrichment.py            (14 endpoints)
│       ├── duotronic.py             (7 endpoints)
│       ├── brain.py                 (8 endpoints)
│       ├── stream.py                (3 endpoints)
│       └── meta_objects.py          (5 endpoints)
│
├── single_page/                     ← Frontend SPA (mirror of live/ views)
│   ├── chat/view.php
│   ├── manager/                     ← 14 manager panels
│   │   ├── _spa_shell.php
│   │   ├── overview/, tracks/, database/, fleet/, logs/
│   │   ├── brain/, playback/, stream_health/, lyrics/
│   │   ├── ai_search/, bluesky/, workflows/
│   │   └── view.php
│   ├── monitor/view.php
│   └── js/                          ← Web components + SPA JS
│
├── controller/
│   └── rnn_chat.php                 ← 28,064 lines, 77 SQLite3() constructors, 8 proc_open calls
│
├── federation/                      ← Multi-node federation framework
│   ├── coordinator.py               ← Work coordination
│   ├── mesh.py                      ← Network mesh management
│   ├── redis_bus.py                 ← Redis state bus
│   ├── replicator.py                ← Data replication
│   ├── s3_client.py                 ← S3/MinIO client
│   ├── ssh_tunnel_manager.py        ← SSH tunnel lifecycle
│   ├── bootstrap-node.sh            ← Node provisioner
│   └── FEDERATION.md
│
├── agno/                            ← Agno Agent Framework (cloned)
│   ├── Dockerfile                   ← python:3.12-slim + agno[os,ollama,milvus,searxng]
│   ├── entrypoint.py                ← FastAPI: 3 agents (research, coding, reasoning)
│   └── docker-compose.yml           ← srnn-agno on port 8040
│
├── ollama/                          ← Dockerized LLM inference
│   ├── docker-compose.yml           ← srnn-ollama on port 11434
│   └── models/                      ← Model storage (~147 GB, 11 models)
│
├── havod/                           ← Hovod video platform (cloned)
│   ├── docker-compose.yml
│   └── docker-compose.override.yml  ← Ports: MySQL 3307, Redis 6380, API 3002, Dash 3003
│
├── trustgraph/                      ← TrustGraph knowledge graph (cloned)
│   └── deploy/
│       ├── docker-compose.yaml      ← ~50 services (ports removed from base)
│       └── docker-compose.override.yml  ← UI 8870, Pulsar 8081, Grafana 3050
│
├── docker-compose.yml               ← Core infrastructure: etcd + MinIO + Milvus + srnn-api
├── .env                             ← Environment config
├── systemd/                         ← 25 systemd unit files
├── searxng/                         ← SearXNG fleet (20 instances, ports 8885-8904)
├── srnn_julia/                      ← Julia math kernels
├── srnn_lisp/                       ← SBCL symbolic reasoning
├── scripts/                         ← Utility scripts
├── migration_backups/               ← Pre-refactor backups
├── REFACTOR_PLAN.md                 ← This file
├── rnn_chat_README.md               ← Full system README
└── AI_INSTRUCTION.md                ← AI assistant context
```

### CMS Integration (live/)

```
/var/www/xavi/live/application/single_pages/rnn_chat/
├── view.php                         ← Entry point
├── data/                            ← CMS-managed (small chat.sqlite copy)
├── auth/                            ← JwtAuth.php (token issuer)
├── js/                              ← Frontend SPAs (7 dirs)
├── manager/                         ← 21 SPA panels
│   ├── _spa_shell.php
│   ├── agents/                      ← Agno management panel
│   ├── context_graph/               ← TrustGraph panel
│   ├── video/                       ← Hovod panel
│   ├── social/                      ← Social media management
│   └── (16 more panels)
├── monitor/
├── meta_object_api/
└── docs/
```

### Running Docker Infrastructure (104 containers)

| Stack | Containers | Key Ports | Status |
|-------|-----------|-----------|--------|
| **SRNN Core** (etcd, MinIO, Milvus) | 3 | 2379, 9000/9001, 19530 | etcd ✅, MinIO ✅, Milvus ⚠️ flaky |
| **Ollama** | 1 | 11434 | ✅ 11 models, ~147 GB |
| **Agno** | 1 | 8040 | ✅ 3 agents (research, coding, reasoning) |
| **TrustGraph** | ~50 | 8870, 8081, 8088, 3050, 6333, 9042 | ✅ Core up, monitoring restarting |
| **Hovod** | 5 | 3002, 3003, 3307, 6380 | ✅ All healthy |
| **SearXNG Fleet** | 40 | 8885-8904 | ✅ 20 instances + 20 Valkey |
| **Duotronics** | 4 | 8080, 8501, 8787 | ✅ |
| **Total** | **104** | | |

### Ollama Model Library (11 models, ~147 GB)

| Model | Size | Use Case |
|-------|------|----------|
| nomic-embed-text | 274 MB | Embedding generation |
| mistral:7b | 4.4 GB | General chat |
| qwen3:8b | 5.2 GB | Reasoning agent |
| llama3.1:8b | 4.9 GB | Research agent |
| phi4:14b | 9.1 GB | Code analysis |
| deepseek-coder-v2:16b | 8.9 GB | Coding agent |
| gemma3:27b | 17 GB | General purpose |
| glm-4.7-flash | 19 GB | Fast inference |
| codellama:34b | 19 GB | Code generation |
| qwen3:32b | 20 GB | Heavy reasoning |
| llama3.1:70b | 42 GB | Maximum capability |

### Known Issues

| Issue | Impact | Priority |
|-------|--------|----------|
| **Milvus health flapping** | querycoord/datacoord fail to connect after restart, recovers in 2-3 min | Medium |
| **TrustGraph monitoring** | loki, grafana, prometheus restarting (non-critical) | Low |
| **PHP controller: 77 SQLite3() + 8 proc_open** | Tight coupling remains — Phase 3 API proxy built but PHP not yet gutted | Medium — Phase 7 |
| **jwt_secret.key in data/** | Should be in db/.secrets/ | Low — Phase 7 |
| **Storyboard loop coverage** | All 8 loop types implemented (chrono, explore, thematic, social, storyboard, replay, contrastive, narrator) | ✅ Complete |
| **Social embedding backfill** | 71,579 Facebook + 427 Bluesky posts fully embedded (0 zero-vectors remaining) | ✅ Complete |
| **Node2 distributed proxy** | Ollama proxy container on node2 with SSH tunnels to main+resource; 14 models aggregated; LibreChat configured | ✅ Complete |

---

## 2. Target Architecture

Phases 0–5b are complete. The system is now a 3-node federated cluster with
Milvus as the authoritative vector store, 295,160 total entities (72,006 social
posts fully embedded), Redis Sentinel HA, and MinIO multi-site replication.
The remaining work is:

1. **Phase 6** (complete): Storyboard cognition ensemble — 31/31 steps done.
2. **Phase 13**: Rollout hardening + compatibility cleanup — centralized
   cheap-worker defaults, runtime diagnostics, rollout metrics, legacy parity
   test repair, and schema-tolerant meta-object extraction.
3. **Phase 7b**: Final cleanup — gut PHP controller, move JWT secret, JS URL
   audit, remove dead CMS paths.
4. **Phase 8**: Acceleration planes — Part II compression (TurboQuant/PolarQuant
   sidecar), conditional memory (Engram-style lookup), Part V audit tables,
   narrator split-memory, CPC pretraining experiments.

```
srnn_server/                         ← AFTER COMPLETION
├── srnn/                            ← Python backend (CANONICAL)
│   ├── meta_objects/                ← 51-file core: extractors, enrichment, vectors
│   └── cognition/                   ← 20-file recurrent cognition engine (7,600+ LOC)
│       ├── state.py                 ← CognitionState — 5 memory layers, ~30 fields
│       ├── phi.py                   ← PhiOperator — Φ(h_{t-1}, x_t) with SBCL delegation
│       ├── sbcl_bridge.py           ← SBCLPhiBridge — JSON-RPC subprocess + circuit breaker
│       ├── rnn_cell.py              ← RecurrentCell — gated memory (9 gate presets)
│       ├── loop.py                  ← CognitionLoop — 8 loop types, autonomous run()
│       ├── chronicle.py             ← ChronicleBuilder — mixed-source stream + edges
│       ├── meta_summary.py          ← MetaSummaryBuilder (social+discovery+web+story)
│       ├── witness.py               ← SemanticWitness — Duotronic polygon bridge
│       ├── claims.py                ← ClaimExtractor — regime/motif/social/prediction
│       ├── ranking.py               ← LoopRanker — 8-axis scorer (with witness_support)
│       ├── merge.py                 ← ClaimMerger — interference merge + Jaccard dedup
│       ├── synthesis.py             ← Synthesizer — English answers via cluster LLM
│       ├── persistence.py           ← Loop runs, traces, rankings, storyboards to SQLite
│       ├── diagnostics.py           ← Gate history, state drift, memory profiling
│       ├── packet.py                ← ChroniclePacket + PacketBuilder + binding_confidence
│       ├── social_milvus.py         ← Milvus accessor for social_facebook/bluesky
│       ├── milvus_store.py          ← Chain-state vector persistence to Milvus
│       ├── manager.py               ← CognitionManager — multi-loop orchestrator
│       └── __init__.py, __main__.py ← Package exports + CLI entry
├── xavi/                            ← Agno-based backend (app.py, agents, tools, daemon)
├── db/                              ← Milvus = primary, SQLite = read-only backup
├── api/                             ← FastAPI route modules (mounted in xavi/app.py)
├── federation/                      ← Multi-node coordination + Redis bus
├── agno/                            ← Agent orchestration (3 agents)
├── ollama/                          ← LLM inference (11 models, ~147 GB)
├── havod/                           ← Video platform (Hovod, 5 containers)
├── trustgraph/                      ← Knowledge graph (~50 containers)
├── single_page/                     ← Frontend SPA views
├── controller/
│   └── rnn_chat.php                 ← TO BE GUTTED: ~3K lines (auth + API proxy only)
└── docker-compose.yml               ← Profile-based: coordinator / resource / worker
```

---

## 3. Files Moved — Completed ✅

### Python Backend — Consolidated

All Python code now in `srnn_server/srnn/`. The 6 modules previously only in
`live/` have been moved:

| File | Status |
|------|--------|
| `meta_objects/` (51 files) | ✅ In `srnn/meta_objects/` |
| `bsky_cataloger.py` | ✅ In `srnn/` |
| `bulk_enrich.py` | ✅ In `srnn/` |
| `model_router.py` | ✅ In `srnn/` |
| `turbo_quant.py` | ✅ In `srnn/` |
| `meta_objects.py` (legacy) | ✅ In `srnn/` |

### Files Diffed and Merged

| File | Resolution |
|------|-----------|
| `cli.py` | Merged — kept more complete version |
| `config.py` | Merged — updated paths for new structure |
| `schema.py` | Merged — both versions combined |
| `daemon.py`, `session.py`, `shuffle.py` | Merged |
| `similarity.py`, `enricher.py`, `features.py` | Merged |
| `playlist.py`, `clusters.py`, `tier0.py` | Merged |
| `web_agent.py` | Merged |
| `duotronic/` (4 files) | Merged |

### Data Consolidated

| Source | Destination | Status |
|--------|------------|--------|
| SQLite databases | `srnn_server/db/` | ✅ All 10 DBs |
| etcd/MinIO/Milvus data | `srnn_server/db/{etcd,minio,milvus}_*` | ✅ |
| FAISS indices | `srnn_server/db/faiss_indices/` | ✅ |
| Music files (68 GB) | `srnn_server/data/music/` | ✅ |
| Social exports (37+ GB) | `srnn_server/data/social/` | ✅ |
| ML models | `srnn_server/data/models/` | ✅ |

---

## 4. Milvus Collection Design

### Why Milvus (not raw FAISS + SQLite)

| Requirement | SQLite | FAISS | Milvus |
|-------------|--------|-------|--------|
| Vector similarity search | ✗ | ✓ | ✓ |
| Metadata filtering | ✓ (SQL) | ✗ | ✓ (hybrid) |
| Multimodal (binary blobs) | ✗ (BLOB limit) | ✗ | ✓ (via MinIO) |
| Timestamps / ordering | ✓ | ✗ | ✓ |
| previous_object_id links | ✓ (FK) | ✗ | ✓ (field + filtered search) |
| Hierarchical relationships | ✓ (parent_id) | ✗ | ✓ (partition keys + fields) |
| Concurrent writers | ✗ (single-writer) | ✗ | ✓ |
| Self-hosted Docker | N/A | N/A | ✓ |

> **Note:** Qdrant was considered but requires AVX2. Xeon X5690 only has SSE4.2.
> Milvus confirmed with `KNOWHERE_SIMD_TYPE=sse4_2`.

### Collection Schemas (defined in `srnn/milvus_schema.py`)

#### `music_tracks` (from chat.sqlite — 506 MB)

```python
CollectionSchema(
    fields=[
        FieldSchema("track_id",  DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("video_id",  DataType.VARCHAR, max_length=64),
        FieldSchema("title",     DataType.VARCHAR, max_length=512),
        FieldSchema("artist",    DataType.VARCHAR, max_length=256),
        FieldSchema("album",     DataType.VARCHAR, max_length=256),
        FieldSchema("genre",     DataType.VARCHAR, max_length=128),
        FieldSchema("year",      DataType.INT32),
        FieldSchema("duration",  DataType.FLOAT),
        FieldSchema("file_path", DataType.VARCHAR, max_length=1024),
        FieldSchema("created_at",DataType.INT64),
        FieldSchema("updated_at",DataType.INT64),
        FieldSchema("tempo",     DataType.FLOAT),
        FieldSchema("key_name",  DataType.VARCHAR, max_length=8),
        FieldSchema("energy",    DataType.FLOAT),
        FieldSchema("loudness",  DataType.FLOAT),
        FieldSchema("spectral_centroid", DataType.FLOAT),
        FieldSchema("enrichment_level", DataType.INT32),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=384),
    ],
    description="Music library tracks with audio features and embeddings"
)
# Index: IVF_FLAT on embedding, scalar on video_id, artist, genre, year
```

#### `srnn_features` (from srnn.sqlite — 144 MB)

```python
CollectionSchema(
    fields=[
        FieldSchema("feature_id",    DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("track_number",  DataType.INT64),
        FieldSchema("lyrics",        DataType.VARCHAR, max_length=65535),
        FieldSchema("transcript",    DataType.VARCHAR, max_length=65535),
        FieldSchema("color_histogram", DataType.VARCHAR, max_length=4096),
        FieldSchema("detected_objects", DataType.VARCHAR, max_length=4096),
        FieldSchema("related_artists", DataType.VARCHAR, max_length=2048),
        FieldSchema("lyrics_embedding",  DataType.FLOAT_VECTOR, dim=384),
        FieldSchema("audio_embedding",   DataType.FLOAT_VECTOR, dim=384),
        FieldSchema("visual_embedding",  DataType.FLOAT_VECTOR, dim=384),
        FieldSchema("enrichment_level",  DataType.INT32),
        FieldSchema("updated_at",        DataType.INT64),
    ],
    description="SRNN feature vectors per track"
)
```

#### `srnn_connections` (from srnn.sqlite)

```python
CollectionSchema(
    fields=[
        FieldSchema("connection_id", DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("track_a",       DataType.INT64),
        FieldSchema("track_b",       DataType.INT64),
        FieldSchema("lyrics_sim",    DataType.FLOAT),
        FieldSchema("musical_sim",   DataType.FLOAT),
        FieldSchema("color_sim",     DataType.FLOAT),
        FieldSchema("visual_sim",    DataType.FLOAT),
        FieldSchema("artist_sim",    DataType.FLOAT),
        FieldSchema("title_sim",     DataType.FLOAT),
        FieldSchema("embedding_sim", DataType.FLOAT),
        FieldSchema("composite",     DataType.FLOAT),
        FieldSchema("reinforcement", DataType.FLOAT),
        FieldSchema("updated_at",    DataType.INT64),
    ],
    description="7-dimensional pairwise track similarities"
)
```

#### `meta_objects` (from meta_objects system)

```python
CollectionSchema(
    fields=[
        FieldSchema("meta_id",            DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("track_number",        DataType.INT64),
        FieldSchema("category",            DataType.VARCHAR, max_length=64),
        FieldSchema("label",               DataType.VARCHAR, max_length=256),
        FieldSchema("confidence",          DataType.FLOAT),
        FieldSchema("extractor",           DataType.VARCHAR, max_length=64),
        FieldSchema("previous_object_id",  DataType.INT64),
        FieldSchema("parent_id",           DataType.INT64),
        FieldSchema("depth",               DataType.INT32),
        FieldSchema("embedding",           DataType.FLOAT_VECTOR, dim=384),
        FieldSchema("metadata_json",       DataType.VARCHAR, max_length=65535),
        FieldSchema("created_at",          DataType.INT64),
    ],
    description="Meta-object recurrence graph with hierarchical relationships"
)
```

#### `dt_events` (from duotronic.sqlite — 235 MB)

```python
CollectionSchema(
    fields=[
        FieldSchema("event_id",    DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema("event_type",  DataType.VARCHAR, max_length=64),
        FieldSchema("track_number",DataType.INT64),
        FieldSchema("payload_json",DataType.VARCHAR, max_length=65535),
        FieldSchema("embedding",   DataType.FLOAT_VECTOR, dim=384),
        FieldSchema("created_at",  DataType.INT64),
    ],
    description="Duotronic event stream (decisions, stories, actions)"
)
```

#### Additional Collections

| Collection | Source | Key Fields |
|-----------|--------|------------|
| `shuffle_sessions` | srnn_shuffle_sessions | arrangement JSON, epoch, current_idx |
| `playback_log` | srnn_playback_log | track_number, source, listen_pct, timestamp |
| `decision_log` | srnn_decision_log | candidates_json, scores_json, reason, timestamp |
| `enrichment_queue` | srnn_enrichment_queue | track_number, priority, status, created_at |
| `playlists` | srnn_playlists + items | name, type, tracks_json, encoded_message |
| `discoveries` | srnn_discoveries | url, relevance, status, track_number |
| `media_items` | srnn_media_items | type, url, track_number, binary → MinIO |
| `web_archive` | srnn_web_archive | url, pdf_path → MinIO, extracted_text |
| `sear_cache` | sear_data.sqlite | query, results_json, ttl |
| `social_bluesky` | bsky_meta_chain | post_uri, meta_objects, previous_object_id |
| `srnn_social_chronicle` | facebook_data.sqlite + bluesky exports | platform, canonical_ts, text, linked_track_ids, motif packet |
| `chronicle_objects` | normalized mixed chronology | source_type, source_id, canonical_ts, object_ref, meta_summary |
| `chronicle_edges` | derived graph links | edge_type, src_object_id, dst_object_id, weight, provenance |
| `loop_runs` | cognition layer | loop_id, query_id, branch_id, config_json, score_json |
| `loop_traces` | cognition layer | loop_run_id, trace_json, claim_blocks_json, evidence_refs |
| `loop_rankings` | cognition layer | query_id, loop_run_id, relevance, coherence, evidence_score |
| `answer_artifacts` | cognition layer | query_id, short_answer, long_answer, outline_json |
| `brain_memory` | media_context.sqlite | content, semantic_tags, embedding, timestamp |
| `clusters` | srnn_clusters | cluster_id, coherence, centroid vector |
| `story_log` | srnn_story_log | narrative, mood, theme, track_number |

### MinIO Object Storage

| Bucket | Content | Status |
|--------|---------|--------|
| `srnn-music` | Audio files (68 GB) | Pending |
| `srnn-models` | Ollama model blobs (~147 GB) | Pending — Phase 5 |
| `srnn-web-archive` | PDFs, screenshots | Pending |
| `srnn-processing` | Frame cache, outputs | Pending |
| `srnn-social` | Social media data | Pending |
| `hovod-vod` | Hovod video files | ✅ Created |
| `xavi-databases` | Milvus snapshots for replication | Pending |

---

## 5. Docker Compose Setup

### Core Stack (`docker-compose.yml`)

| Service | Image | Container | Port | Status |
|---------|-------|-----------|------|--------|
| **etcd** | `quay.io/coreos/etcd:v3.5.16` | `srnn-etcd` | 127.0.0.1:2379 | ✅ |
| **MinIO** | `minio/minio:latest` | `srnn-minio` | 127.0.0.1:9000/9001 | ✅ |
| **Milvus** | `milvusdb/milvus:v2.5.6` | `srnn-milvus` | 127.0.0.1:19530 | ⚠️ Flaky |
| **srnn-api** | Built from `api/` | `srnn-api` | 127.0.0.1:8030 | Defined |

### Satellite Stacks

| Stack | Compose File | Status |
|-------|-------------|--------|
| **Ollama** | `ollama/docker-compose.yml` | ✅ 11 models |
| **Agno** | `agno/docker-compose.yml` | ✅ 3 agents |
| **Hovod** | `havod/docker-compose.yml` + override | ✅ 5 containers |
| **TrustGraph** | `trustgraph/deploy/docker-compose.yaml` + override | ✅ ~50 containers |

All stacks share the `srnn-net` external Docker network.

### Resource Budget (Intel Xeon X5690, 128 GB RAM, 24 threads)

| Service | CPU | RAM | Disk |
|---------|-----|-----|------|
| etcd | 1 | 512 MB | ~100 MB |
| MinIO | 1 | 1 GB | ~105 GB |
| Milvus | 4 | 8 GB | ~2 GB |
| Ollama | 8 | 48 GB | ~147 GB |
| Agno | 4 | 8 GB | — |
| TrustGraph | 4 | 8 GB | ~2 GB |
| Hovod | 2 | 2 GB | varies |
| SearXNG (20×) | 2 | 4 GB | minimal |
| srnn-api | 2 | 2 GB | — |
| **Total** | **~24** | **~82 GB** | ~256 GB |

~46 GB RAM remains for OS, CMS, systemd services, and burst.

### Docker Compose Profiles (multi-node)

| Profile | etcd | MinIO | Milvus | Ollama | Agno | srnn-api |
|---------|------|-------|--------|--------|------|----------|
| `coordinator` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `resource` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `worker` | ✗ | ✗ | ✗ | opt | ✓ | ✓ |

---

## 6. SQLite → Milvus Migration Path

### Phase 1: Infrastructure ✅ DONE

1. ✅ Docker Compose deployed (etcd + MinIO + Milvus)
2. ✅ Milvus schemas defined (`srnn/milvus_schema.py` — 20 collections)
3. ✅ Migration script scaffolded (`srnn/migrate.py`)
4. ✅ FastAPI application created (`api/`) with 7 route files
5. ✅ Ollama deployed with 11 models
6. ✅ Agno deployed with 3 agents
7. ✅ TrustGraph and Hovod integrated

### Phase 2: Populate Milvus — COMPLETE ✅

1. ✅ Milvus healthy on 19530 (fixed MinIO credential env var names)
2. ✅ Created 20 Milvus collections with IVF_FLAT indexes (COSINE, nlist=128)
3. ✅ Fixed `playback_log` schema — added required FLOAT_VECTOR field
4. ✅ Fixed `related_artists_json` VARCHAR limit (2048 → 8192)
5. ✅ Fixed `migrate.py` column mappings for all 20 tables:
   - `chat.sqlite`: `analysis` → `media_analysis`, column renames (artist→channel_title, etc.)
   - `srnn.sqlite`: `sim_*` prefix columns, `computed_at` timestamps
   - `duotronic.sqlite`: `content` → `payload`, `timestamp` → `created_at`
   - Text timestamps parsed via `_ts_to_epoch()` helper
6. ✅ Migrated all 20 collections — **223,581 total rows**:
   - `music_tracks`: 3,025 | `srnn_features`: 3,025 | `srnn_connections`: 78,863
   - `dt_events`: 76,772 | `dt_vectors`: 10,796 | `playback_log`: 8,351
   - `srnn_state`: 5,108 | `meta_objects`: 33,811 | `decision_log`: 2,119
   - `brain_memory`: 1,237 | `social_bluesky`: 427 | `discoveries`: 26
   - `playlists`: 12 | `clusters`: 4 | `enrichment_queue`: 3
   - `sear_cache`: 1 | `shuffle_sessions`: 1
   - `story_log`: 0 | `media_items`: 0 | `web_archive`: 0
7. ✅ Full verification passed — all row counts match SQLite ↔ Milvus

### Phase 2b: Embedding Generation — COMPLETE ✅

**Completed 2026-04-07** — 126,117 rows embedded across 10 collections in ~9.5 minutes.

1. ✅ Built embedding pipeline (`srnn/embed.py`) — Matryoshka truncation 768→384, L2-normalize
2. ✅ Deployed GPU Ollama on resource server (209.53.57.60) — P2000 + RTX 2070
3. ✅ Installed `nvidia-container-toolkit` on resource server for GPU Docker
4. ✅ SSH tunnel: coordinator:11435 → resource:11434 (GPU Ollama)
5. ✅ Generated embeddings for all 10 collections:
   - `music_tracks`: 3,025 (title+artist+genre+key → 384-dim)
   - `srnn_features`: 3,025 (lyrics+transcript → 384-dim)
   - `meta_objects`: 33,811 (category+label → 384-dim)
   - `dt_events`: 76,772 (event_type+payload → 384-dim)
   - `brain_memory`: 1,237 (content+semantic_tags → 384-dim)
   - `decision_log`: 2,119 (reason → 384-dim)
   - `social_bluesky`: 427 (text → 384-dim)
   - `playback_log`: 8,351 (source+track_number → 384-dim)
   - `discoveries`: 26, `playlists`: 12
6. ✅ Verified: dry-run shows 0 rows needing embeddings across all collections
7. ✅ Semantic search confirmed working (COSINE similarity, IVF_FLAT, nprobe=10)
8. ☐ Implement dual-write in `config.py` (deferred to Phase 3)
9. ☐ Switch vector search reads to Milvus (deferred to Phase 3)

**Performance comparison:**
- CPU-only (Xeon X5690, 20 CPUs): ~1.8 rows/sec (batch=32, 19.7s/batch)
- GPU (RTX 2070 via SSH tunnel): ~220 rows/sec (batch=128, 0.9s/batch) — **22x speedup**

**Key files:**
- `srnn/embed.py` — embedding pipeline with per-collection text strategies
- `ollama/docker-compose.yml` — CPU Ollama (20 CPUs)
- Resource server: `~/ollama-gpu/docker-compose.yml` — GPU Ollama (P2000 + RTX 2070)

### Phase 3: PHP → API Proxy

1. Build FastAPI endpoints for every PHP SQLite operation
2. Replace 77 `new \SQLite3(...)` calls with HTTP calls to FastAPI
3. Replace 9 `proc_open(python3 ...)` calls with API calls
4. Result: 28,066 → ~3,000 lines

#### Route → PHP Replacement Map

```
PHP exec("python3 -m srnn shuffle 50")    →  GET  /srnn/shuffle?length=50
PHP exec("python3 -m srnn next")          →  POST /srnn/session/next
PHP exec("python3 -m srnn connections 42")→  GET  /srnn/connections/42
PHP exec("python3 -m srnn enrich-batch")  →  POST /enrich/batch
PHP exec("python3 -m srnn dt-search")     →  GET  /dt/search
PHP exec("python3 -m srnn brain-chat")    →  POST /brain/chat
PHP new \SQLite3(chat.sqlite) SELECT ...  →  GET  /manager/tracks
PHP new \SQLite3(srnn.sqlite) INSERT ...  →  POST /manager/database/...
```

### Phase 4: Federation Deploy

1. Provision 3 new nodes (adding to existing 2)
2. Run `federation/bootstrap-node.sh`
3. Coordinator assigns capabilities by hardware
4. Milvus replication via `bulk_insert` from MinIO Parquet

### Phase 5: Cleanup

1. ~~Remove dead code from controller~~ ✅ api/main.py, api/auth.py, api/Dockerfile, .bak files removed
2. ~~Move Redis config to local~~ ✅ config.yaml updated: port 6379 (local)
3. Move `data/jwt_secret.key` → `db/.secrets/`
4. Verify all JS uses FastAPI URLs
5. Final `live/…/rnn_chat/`: only `view.php`, `js/`, `manager/`, `auth/`

### Phase 5b: Federation hardening — COMPLETE ✅

1. ✅ Redis Sentinel HA — 3 sentinels on Main (:26379-26381), quorum=2, FederationBus Sentinel-aware
2. ✅ MinIO multi-site replication — 3 sites (GPU-1 primary, Main + CPU-2 mirrors), mc mirror every 5min
3. ✅ Bootstrap auto-registers new nodes in config.yaml
4. ✅ Systemd tunnel services auto-created by bootstrap
5. ✅ Unified tunnel daemon (xavi-federation-tunnels.service) replaces per-node services
6. ✅ Redis 3-node master-replica topology (Main master, GPU-1 + CPU-2 replicas via reverse SSH tunnels)
7. ✅ CPU-2 sdb mounted (/mnt/xavi-s3, 232GB), MinIO installed + systemd enabled
8. ☐ Coordinator failover (hot standby on cpu-2) — deferred until 4th node available

---

## 7. Federation Architecture

### Current Mesh (3 nodes — live)

```
┌──────────────────────────┐  SSH tunnels  ┌──────────────────────────┐
│  COORDINATOR (main)      │◄════════════►│  RESOURCE (gpu-1)        │
│  Xeon X5690 / 128GB      │              │  Ryzen 5950X / 64GB      │
│  104 Docker containers   │              │  RTX 2070 / 10TB         │
│  xavi-api :8050          │              │                          │
│  srnn-brain :8031 (Lisp) │              │  GPU workers             │
│  Redis :6379 (local)     │              │  Model inference         │
│  etcd + MinIO + Milvus   │              │  Media processing        │
│  Ollama :11435 (proxy)   │              │                          │
│  SearXNG (20 instances)  │              │                          │
└──────────────┬───────────┘              └──────────────────────────┘
               │ SSH tunnels
               │
┌──────────────▼───────────┐
│  WORKER (cpu-2)          │
│  2x Xeon X5690 / 128GB   │
│  Ollama :11434 (5 models)│
│  SearXNG (5 instances)   │
└──────────────────────────┘
```

### Target: 5-Node Cluster

- **Node 1** (Coordinator): HP DL380 — orchestrates, CMS, SearXNG
- **Node 2** (Resource): GPU server — inference, media processing
- **Nodes 3-5** (Workers): New — specialized compute, distributed storage

### Port Allocation (per-node block)

```
Base = 18200 + node_index * 10:
  +0  GPU worker API      (18200, 18210, 18220...)
  +1  MinIO S3 API        (18201, 18211, 18221...)
  +2  MinIO Console       (18202, 18212, 18222...)
  +3  Redis               (18203, 18213, 18223...)
  +4  SRNN API (FastAPI)  (18204, 18214, 18224...)
  +5  Milvus gRPC         (18205, 18215, 18225...)
```

---

## 8. Agno Agent Orchestration

### Current Agents (srnn-agno:8040)

| Agent | Model | Purpose |
|-------|-------|---------|
| `research` | llama3.1:8b + SearXNG | Web research, fact gathering |
| `coding` | deepseek-coder-v2:16b | Code generation and analysis |
| `reasoning` | qwen3:8b | Logical reasoning, planning |

### Planned Agents

| Agent | Model | Capability |
|-------|-------|-----------|
| `knowledge` | gemma3:27b | TrustGraph integration, knowledge synthesis |
| `media` | phi4:14b | Music analysis, media processing |
| `enrichment` | mistral:7b | Web enrichment pipeline automation |
| `vision` | llama3.1:70b | Image analysis (YOLOv8 + LLM) |
| `orchestrator` | qwen3:32b | Multi-agent coordination |

### Agno → Milvus Integration (pending)

Agents currently have no persistent memory. Plan:
1. Connect via `agno.knowledge.Knowledge(vector_db=MilvusDb(...))`
2. Per-agent Milvus collections for context
3. Shared `brain_memory` collection for cross-agent knowledge

---

## 9. Architecture Notes

### FAISS Hot-Path Cache

Milvus = authoritative store. Local FAISS = read cache for shuffle daemon
(advances every 180s). Rebuild on daemon startup.

### Docker Compose Port Merge Gotcha

> Docker Compose `ports` arrays CONCATENATE between base and override — they
> don't replace. Base `8888:8888` + override `8870:8888` = BOTH published.
> **Fix:** Remove ports from base, define only in override.

### Ollama Healthcheck

`ollama/ollama` image has no `curl`. Use:
```yaml
healthcheck:
  test: ["CMD-SHELL", "ollama list > /dev/null 2>&1"]
```

### Backup Strategy

| Component | Method | Frequency |
|-----------|--------|-----------|
| Milvus | `milvus-backup` → MinIO | Daily |
| MinIO | `mc mirror` to peer | Continuous |
| etcd | `etcdctl snapshot save` | Hourly |
| SQLite (transition) | cp to migration_backups/ | Before migration |
| Music | rsync / MinIO mirror | Weekly |
| Config | git push | On change |

---

## 10. Implementation Order

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **Phase 0: Consolidate Python** | Single canonical `srnn/` package | ✅ Done |
| **Phase 0b: Data consolidation** | All DBs in `db/`, media in `data/` | ✅ Done |
| **Phase 1: Docker infrastructure** | etcd + MinIO + Milvus + Ollama + Agno + TG + Hovod | ✅ Done |
| **Phase 1b: FastAPI scaffolding** | 7 route files, auth, Dockerfile | ✅ Done |
| **Phase 1c: CMS SPA pages** | Manager panels for agents, video, context_graph | ✅ Done |
| **Phase 2: Milvus population** | Create collections, migrate SQLite, dual-write | ✅ Done |
| **Phase 2b: Embedding generation** | 295,160 entities embedded via GPU cluster (RTX 2070 + P2000, 3-node work-stealing) | ✅ Done |
| **Phase 3: PHP → API proxy** | FastAPI endpoints built, SrnnApiClient ready | ✅ Done (API built; PHP controller not yet gutted — see Phase 7) |
| **Phase 4: Architecture v2** | Agno backend + Hovod media + SRNN daemon + multi-grid | ✅ Done |
| **Phase 4b: Service consolidation** | Lisp brain :8031, Redis :6379, old API killed, dead code removed | ✅ Done |
| **Phase 5: Federation deploy** | 3-node cluster, Redis Sentinel HA, MinIO multi-site replication | ✅ Done |
| **Phase 5b: Federation hardening** | Sentinel (3×), MinIO mirror, unified tunnels, Redis replication | ✅ Done |
| **Phase 6: Cognition layer** | Storyboard cognition ensemble, eight-loop ranking, social chronology, English answer synthesis | **Complete** — 31/31 steps done; 20-file cognition module (7,600+ LOC); all loops, ranking, merge, synthesis, witness bridge, recurrent cell, witness sectors (K=8), loop-universe isolation, interference merge, q_t binding, SBCL phi_step (JSON-RPC bridge), enriched Redis meta exchange (genre/theme overlap, sibling consumption), source-type temporal binding (confidence-weighted interpolation) |
| **Phase 7: Contract & observability** | Chain contract, parity tests, diagnostic endpoints, dashboard widgets, agent tool wrappers | ✅ Complete |
| **Phase 7b: Cleanup** | Gut PHP controller (77 SQLite3→API), move JWT secret, JS URL audit, final live/ cleanup | Pending |
| **Phase 8: Acceleration** | Part II compression plane (TurboQuant sidecar), conditional memory (Engram lookup), Part V audit tables, narrator split-memory, CPC experiments | Planned |
| **Phase 9: Integration hardening** | Interference wiring, conflict detection, CPC/proposal stubs, integration tests, policy merge, JS/PHP migration pass 2 | ✅ Complete |
| **Phase 10: Cognition polish** | Skip coherence, cache decay, event-driven snapshots, trainable proposal network, documentation audit | ✅ Complete |
| **Phase 11: Two-level witness dynamics** | Part VI — recurrent witness-state `W̃_t`, update map `Ψ`, extended recurrence `Φ*`, branch-local `W̃_t^(ℓ)`, witness trajectory ranking (9-axis), contradiction gating, coherence drift, witness regime evidence, 29 new tests | ✅ Complete |
| **Phase 12: Cheap worker math & polygonal operators** | Part VII — revised chain semantics (coordinator/worker split), int8 quantized worker recurrence, Count-Min Sketch witness mass, FWHT rotation, shift-add decay, sparse residuals, binary signatures, shared sketch, Engram lookup memory, polygonal operator prototypes, evaluation gates | ✅ Complete |
| **Phase 13: Rollout hardening & compatibility cleanup** | Centralized cheap-worker defaults, runtime rollout diagnostics, SBCL parity suite repair, meta-object schema compatibility, targeted regression triage | **In Progress** |

---

## Phase 6 Revision — Storyboard Cognition Ensemble

The Phase 6 target is no longer just regime detection over a music playlist.
The target is a storyboard cognition system that runs multiple recurrent loops
over the same mixed chronology and then ranks and merges those loops into
English-facing answers.

### 6.0 Revised design rules

1. **Cognition is storyboard-first, not genre-first.** Regime labels should be
   derived from lyrics, recurring symbols, social references, discoveries, and
   linked web evidence before they fall back to genre buckets.
2. **The canonical chronicle is multimodal.** The daemon timeline remains the
   backbone, but cognition now consumes a mixed chronology spanning tracks,
   `srnn_social_chronicle`, `social_bluesky`, `discoveries`, `web_archive`,
   `story_log`, and related `dt_events`.
3. **Eight loops means eight takes.** Each loop is an independent recurrent pass
   over the same underlying chronicle with different traversal strategies,
   evidence windows, or retrieval emphasis. The replay loop was added as an
   eighth type for re-traversal of previously-ranked high-value segments.
4. **Answering happens above the loops.** A merge layer scores loop outputs for
   coherence, evidence density, novelty, temporal fit, and grounded
   expressiveness, then emits a summary or long-form statement in English.
5. **Social chronology is first-class evidence.** Bluesky and Facebook are not
   side logs. They provide timestamps, linked songs, repeated phrases, and
   real-world context that sharpen the storyboard chain.
6. **Base objects are the native cognition units.** Tracks, posts, discoveries,
   searches, story fragments, and daemon events are the effective "neurons" of
   the system; shared meta-objects, reinforced links, and chronology edges are
   the recurrent connective fabric between them.
7. **Loop ranking should be predictive, not purely descriptive.** Each loop should
   predict the next chronicle packet, score its residual, and be ranked by a
   blend of relevance, coherence, evidence density, recurrence support, and
   precision-weighted fit.
8. **Canonical cognition stays single-writer.** Multiple nodes may run shadow or
   speculative cognition loops, but only the coordinator-owned canonical loop
   commits chronology, reinforcement deltas, and authoritative `h_t` updates.

### 6.1 Implementation status (as of 2026-04-07)

| Component | File | Status |
|-----------|------|--------|
| `CognitionState` dataclass | `srnn/cognition/state.py` | ✅ Built — ~30 fields, 5 memory layers, `active_story_axes` dict |
| `MetaSummaryBuilder` | `srnn/cognition/meta_summary.py` | ✅ Built — social, discovery, web archive, story log enrichment; genre weight reduced to 0.35 |
| `PhiOperator` | `srnn/cognition/phi.py` | ✅ Built — story-axis accumulation, `STORY_AXIS_DECAY=0.94`, `_select_regime_label()` prefers story axes over genres |
| `CognitionLoop` | `srnn/cognition/loop.py` | ✅ Built — 8 loop types: chronological, exploratory, thematic, social, storyboard, replay, contrastive, narrator |
| Contrastive loop | `srnn/cognition/loop.py` | ✅ Implemented — under-explored / counter-reading traversal |
| Narrator/synthesis loop | `srnn/cognition/loop.py` | ✅ Implemented — cross-loop trace reader for integrated narration |
| Loop ranking service | `srnn/cognition/ranking.py` | ✅ Built — 7-axis scorer with precision-weighted predictive fit |
| Ranked-transfer merge | `srnn/cognition/merge.py` | ✅ Built — weighted dedup + multi-loop transfer |
| English answer synthesis | `srnn/cognition/synthesis.py` | ✅ Built — template + Ollama-backed short/long answers |
| Chronicle normalization | `srnn/cognition/chronicle.py` | ✅ Built — mixed-source chronicle objects and edge computation |
| Predictive-coding residuals | `srnn/cognition/phi.py`, `srnn/cognition/loop.py`, `srnn/cognition/rnn_cell.py` | ✅ Built — Phi + recurrent residual logging persisted into traces |
| Cognition systemd services | `systemd/` | ✅ Deployed on 3 nodes (main, gpu-1, cpu-2) |
| API surface | `xavi/app.py` | ✅ Mounted at `/xavi/brain/*` with state, loop-run, ranking, answer, storyboard, chronicle, social, and diagnostics endpoints |

### 6.1b Remaining implementation steps

- ✅ ~~Enrich `meta_summary` further with linked social post text, social meta-chain
   motifs, discoveries, web archive tags, and future `story_log` fragments.~~
   `MetaSummaryBuilder.build_for_source()` dispatches to per-type enrichment paths.
- ✅ ~~Make chain-state records fully source-agnostic so manual or non-track loop
   steps can persist social/discovery/web/story objects directly.~~
   `ChainStateRecord` now uses `source_id` + `source_type`; `srnn_chain_state`
   table has new columns with auto-migration and backfill; `phi_step()` and
   `CognitionLoop.step()` accept source_id/source_type; new endpoint
   `GET /meta/chains/source/{source_type}/{source_id}` for non-track lookups.
- ✅ ~~Tighten branch-safe loop execution~~ — `is_canonical` flag on loops,
   only coordinator `chrono-main` commits authoritative `h_t` (step 6.7.29).
- ✅ ~~Validate the SBCL system end-to-end~~ — JSON-RPC bridge with circuit
   breaker, tested Python↔SBCL phi_step round-trip (step 6.7.14).
- Add dashboard widgets and agent tool wrappers for rankings, storyboards,
   claim blocks, chronicle inspection, and predictive residuals (→ Phase 7).
- Freeze `CHAIN_CONTRACT.md` and `phi_packet.schema.json` (→ Phase 7).
- Build Python↔SBCL fixture-based parity tests (→ Phase 7).
- Add diagnostic endpoints: variance, coherence, regimes (→ Phase 7).

### 6.2 Eight-loop ensemble

1. **Chronological anchor loop** — preserves real sequence order.
2. **Exploratory loop** — prioritizes repeated phrases, imagery, and
   semantic callbacks via lyrics and motif traversal.
3. **Thematic loop** — clusters by story-axis theme and meta-object recurrence.
4. **Social resonance loop** — links songs to posts, reactions, and repeated
   self-description in social data.
5. **Storyboard loop** — follows storyboard arcs and discovery/search context.
6. **Replay loop** — re-traverses previously-ranked high-value segments with
   fresh state to surface missed connections.
7. **Contrastive loop** — searches for competing or counter-readings to reduce
   narrative collapse.
8. **Narrator loop** — proposes integrated prose over the other traces.

### 6.3 New persistence targets

- `srnn_social_chronicle`
- `chronicle_objects`  ✅
- `chronicle_edges`  ✅
- `loop_runs`  ✅
- `loop_traces`  ✅
- `loop_rankings`  ✅
- `answer_artifacts`  ✅
- `claim_blocks`  ✅
- `storyboards`  ✅

### 6.4 Ranking and merge layer

The loop ranker should score each loop on:

- query relevance,
- evidence density,
- internal coherence,
- temporal fit,
- recurrence support,
- novelty/diversity,
- grounded expressiveness,
- contradiction penalties.

The merge layer should not be pure winner-take-all. It should use a ranked
transfer strategy: once the strongest claim block is selected, redundant weight
from similar loops is transferred to the next compatible claim block so the
final answer preserves multiple valid perspectives.

### 6.5 Phase 6 deliverables (revised)

- `phi_step()` over mixed evidence packets, not track-only summaries.
- `meta_summary` packets carrying lyrics, social, discovery, and web evidence.
- 8 distributed cognition loops with strategy revision toward storyboard
  traversal.
- Response synthesis service that can turn loop traces into colorful but
  evidence-grounded English answers.
- Social chronology import path feeding `srnn_social_chronicle` and linked
  meta-object recurrence.
- Ranked merge service producing both short and long-form answers.
- Loop-trace APIs and dashboard inspection surfaces.
- **Part V extension deliverables:**
  - Witness-sector signatures on chronicle packets (`w_t`).
  - Loop-universe decomposition — each loop reads the canonical chronicle as
    an isolated branch-local universe.
  - Four-level architecture: canonical chronicle → witness-sector layer →
    loop-universe layer → ranking/merge layer.
  - Interference-style merge logic where loop traces compete and cooperate
    based on witness-sector support overlap.
  - Question/prompt context `q_t` wired into the loop-universe recurrence
    equation: `h_t^(i) = Φ_i(h_(t-1)^(i), p_t, q_t, u_t)`.

### 6.6 Suggested new endpoints

All cognition endpoints use the existing `/xavi/brain/` prefix (live router in
`xavi/app.py` line 602). The following additions are now live on the router:

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

### 6.7 Phase 6 concrete next steps (priority order)

The following sequence minimizes risk and builds each capability on top of the
last working piece:

| Step | Task | Depends on | Target file | Status |
|------|------|------------|-------------|--------|
| **6.7.1** | Build `chronicle_objects` normalizer | state.py, meta_summary.py | `srnn/cognition/chronicle.py` | ✅ |
| **6.7.2** | Write source adapters (track, social, discovery, web, story, event) | 6.7.1 | same file | ✅ |
| **6.7.3** | Build `chronicle_edges` computation from connections + meta-objects | 6.7.1 | same file | ✅ |
| **6.7.4** | Implement contrastive loop type | 6.7.1 | `srnn/cognition/loop.py` | ✅ |
| **6.7.5** | Implement narrator loop (reads other loop traces) | 6.7.4 | `srnn/cognition/loop.py` | ✅ |
| **6.7.6** | Build claim-block extractor | 6.7.5 | `srnn/cognition/claims.py` | ✅ |
| **6.7.7** | Build loop ranking scorer (7-axis + predictive fit) | 6.7.6 | `srnn/cognition/ranking.py` | ✅ |
| **6.7.8** | Build ranked-transfer merge layer | 6.7.7 | `srnn/cognition/merge.py` | ✅ |
| **6.7.9** | Build English answer synthesis (short + long-form) | 6.7.8 | `srnn/cognition/synthesis.py` | ✅ |
| **6.7.10** | Persist loop_runs, loop_traces, answer_artifacts | 6.7.9 | `srnn/cognition/persistence.py` | ✅ |
| **6.7.11** | Wire new endpoints into `/xavi/brain/` | 6.7.10 | `xavi/app.py`, `api/routes/brain.py` | ✅ |
| **6.7.12** | Add predictive-coding residual logging to loop traces | 6.7.7 | phi.py, loop.py | ✅ |
| **6.7.13** | Facebook → Milvus social_facebook import + chronicle adapter | 6.7.1 | `srnn/import_facebook_milvus.py`, `srnn/cognition/social_milvus.py`, `srnn/milvus_schema.py` | ✅ |
| **6.7.14** | Build SBCL `phi_step` equivalent | 6.7.1 | `srnn_lisp/src/phi.lisp`, `srnn_lisp/src/json-rpc.lisp`, `srnn_lisp/launch-rpc.lisp`, `srnn/cognition/sbcl_bridge.py`, `srnn/cognition/phi.py` | ✅ Done |
| **6.7.15** | Add `chain_state` Milvus collection | 6.7.14 | `srnn/milvus_schema.py` | ✅ |
| **6.7.16** | Build recurrent cell with gated memory (Part IV §7) | 6.7.3 | `srnn/cognition/rnn_cell.py` | ✅ |
| **6.7.17** | Build Duotronic semantic witness bridge (Part IV §13) | 6.7.16 | `srnn/cognition/witness.py` | ✅ |
| **6.7.18** | Build Redis meta-object exchange bus (Part IV §6.2) | 6.7.1 | `federation/redis_bus.py`, `srnn/cognition/loop.py`, `srnn/cognition/rnn_cell.py` | ✅ Done |
| **6.7.19** | Build temporal binding layer (social dates ↔ playlist) | 6.7.13 | `srnn/cognition/chronicle.py`, `srnn/cognition/packet.py` | ✅ Done |
| **6.7.20** | CognitionState layer 5: recurrent memory fields (Part IV §14.1) | 6.7.16 | `srnn/cognition/state.py` | ✅ |
| **6.7.21** | Source-agnostic chain state (source_id + source_type) | 6.7.1 | state.py, phi.py, loop.py, persistence.py, meta_summary.py, claims.py, diagnostics.py, milvus_store.py, app.py | ✅ |
| **6.7.22** | Rename duotronic → semantic_lattice; create MetaObjectBridge | 6.7.17 | `srnn/semantic_lattice/` (new package), `bridge.py`, `__init__.py` | ✅ |
| **6.7.23** | Semantic lattice API routes (`/semantic-lattice/*`) | 6.7.22 | `api/routes/semantic_lattice.py` — 10 endpoints: witness, overlap, object lattice, neighbors, encode, search, rebuild | ✅ |
| **6.7.24** | Integrate witness graph into meta-object pipeline (Phase 14) | 6.7.22 | `srnn/meta_objects/pipeline.py` — rebuild_witness_graph called after motif clusters | ✅ |
| **6.7.25** | Self-contained Docker container (Ubuntu 22.04 + Supervisor) | 6.7.22 | `docker/Dockerfile.srnn`, `docker/entrypoint.sh`, `docker/supervisord.conf`, `srnn/container_tunnels.py` | ✅ |
| **6.7.26** | Distributed cluster compute pool | 6.7.25 | `srnn/cluster.py` — 3-node pool (80 CPU, 304GB, 2 GPU), round-robin embed(), GPU-preference generate() | ✅ |
| | | | | |
| | **Part V extension — witness sectors & loop-universe decomposition** | | | |
| **6.7.27** | Add witness-sector signature `w_t` to `ChroniclePacket` | 6.7.17 | `srnn/cognition/packet.py`, `srnn/cognition/witness.py` — sparse recurrent sector markers `(w_t1, ..., w_tK)` on every packet; 8 default sectors, `WitnessSectorProjector`, auto-attach in `PacketBuilder` | ✅ |
| **6.7.28** | Implement witness-sector projection in loop traversal | 6.7.27 | `srnn/cognition/rnn_cell.py`, `srnn/cognition/loop.py`, `srnn/cognition/state.py` — witness_policy per gate preset, witness_bias injection into GRU/LSTM/contrastive, accumulation in loop state | ✅ |
| **6.7.29** | Add loop-universe branch isolation (branch-safe execution) | 6.7.28 | `srnn/cognition/loop.py`, `srnn/cognition/manager.py` — `is_canonical` flag, only coordinator `chrono-main` commits authoritative `h_t`; branch loops emit `branch_step` events | ✅ |
| **6.7.30** | Implement interference-style merge in ranking layer | 6.7.29 | `srnn/cognition/merge.py`, `srnn/cognition/ranking.py` — 8-axis scoring with `witness_support`, pairwise cosine interference (reinforcement > 0.6, cancellation < 0.2) | ✅ |
| **6.7.31** | Wire question/prompt context `q_t` into loop-universe recurrence | 6.7.30 | `srnn/cognition/state.py` (`active_query`), `srnn/cognition/phi.py` (query-axis boosting), `srnn/cognition/rnn_cell.py` (gate modulation), `srnn/cognition/loop.py` (`set_query()`, wiring through `step()`) | ✅ |

---

## Phase 7: Contract Discipline & Observability

> **Goal:** Freeze the cognition data contract, add Python↔SBCL parity tests,
> build diagnostic endpoints, and create dashboard/agent tool surfaces for the
> completed cognition engine.

### 7.0 Phase 7 concrete steps

| Step | Task | Depends on | Target file(s) | Status |
|------|------|------------|-----------------|--------|
| **7.1** | Freeze `CHAIN_CONTRACT.md` — naming conventions, required fields per cognition step, null/absent/zero rules, native vs export indexing | 6.7.31 | `docs/CHAIN_CONTRACT.md` | ✅ Done |
| **7.2** | Create `phi_packet.schema.json` — machine-readable JSON Schema for the cognition packet | 7.1 | `docs/phi_packet.schema.json` | ✅ Done |
| **7.3** | Build Python↔SBCL fixture-based parity tests — feed identical event sequences to both, assert equivalent state traces | 6.7.14 | `tests/test_sbcl_parity.py` | ✅ Done (33 pass, 3 xfail) |
| **7.4** | Add state reproducibility test — same seeds + same events → identical traces | 7.3 | `tests/test_sbcl_parity.py` | ✅ Done |
| **7.5** | Add diagnostic endpoints: `GET /xavi/meta/variance`, `/coherence`, `/regimes` | 6.7.31 | `api/routes/brain.py` or `xavi/app.py` | ✅ Done (already in xavi/app.py cognition_router) |
| **7.6** | Build Agno tool wrappers for cognition: explain-transition, compare-positions, regime-timeline, motif-drift | 7.5 | `xavi/tools/cognition.py` | ✅ Done |
| **7.7** | Build dashboard web components: `<xavi-cognition-state>`, `<xavi-loop-ranking>`, `<xavi-storyboard-viewer>`, `<xavi-chronicle-inspector>` | 7.5 | `single_page/js/` | ✅ Done |
| **7.8** | Add full predictive-packet fields to loop traces: `prediction_packet`, `prediction_error_packet`, `precision_weights`, `fit_score` | 7.5 | `srnn/cognition/loop.py`, `docs/phi_packet.schema.json`, `docs/CHAIN_CONTRACT.md` | ✅ Done |

### 7.0b Phase 7b — Final cleanup

| Step | Task | Target file(s) | Status |
|------|------|-----------------|--------|
| **7b.1** | Gut PHP controller: high-freq SQLite3() → API proxy (13 removed, 3 dead-coded; 64 remain in low-freq admin paths) | `controller/rnn_chat.php`, `xavi/app.py` | ✅ Done (pass 1) |
| **7b.2** | Move JWT secret from `data/` to `db/.secrets/` | `auth/JwtAuth.php` | ✅ Done |
| **7b.3** | JS URL audit — frontend routing verified | `single_page/js/`, `live/` | ✅ Done (audit) |
| **7b.4** | Remove dead CMS paths and legacy route stubs | `controller/rnn_chat.php`, `api/` | ✅ Done |

**7b.1 Details — Converted SQLite3 calls:**
- `session-state` (degraded + normal) → `/srnn/session/state` (3 SQLite3 calls removed)
- `pulse` → `/xavi/pulse` (2 calls removed)
- `pulse-dt` → `/xavi/pulse` + PHP encoding (2 calls removed)
- `media-streams` → `/xavi/pulse/media-streams` (1 call removed)
- `sear-data-stats` → `/xavi/sear-data/stats` (1 call removed)
- `brain-poll` → `/brain/poll/{sid}/{hash}` (1 call removed)
- `sear-data-add-topic` → `/xavi/sear-data/add-topic` (1 call removed)
- `media-capture` → `/xavi/dt/media-capture` (1 call removed)
- `pulse-dt-receive` → `/xavi/dt/pulse-receive` (1 call removed)
- `dt-bus-request` queue write → `/xavi/dt/bus-queue` (1 call removed)
- `monitor-activity` / `monitor-log-summary` / `pipeline-live` → `/xavi/monitor/*` (3 calls dead-coded)
- **New FastAPI endpoints created**: `pulse_router` (3), `sear_router` (2), `monitor_router` (3), `dt_write_router` (3) = 11 new endpoints
- **Remaining 64 calls**: admin-only DB browser, lyrics mining, social/Bluesky, DT bus SSE, brain memory — all low-frequency

**7b.3 Details — JS URL Audit:**
- Nginx already proxies `/xavi-api/` → `http://127.0.0.1:8050/` (FastAPI)
- 28 source JS files in `single_page/js/`, 106+ deployed files in `live/application/single_pages/`
- Most files use configurable URL pattern: `getAttribute() → window.*Global → '/rnn_chat/*' fallback`
- `xavi-api.js` and `cognition-panels.js` already use `/xavi-api/` and `/xavi/brain/` — no changes needed
- CMS routes (`/rnn_chat/srnn_api`, `/rnn_chat/manager_api`) still work as proxies to FastAPI
- Full migration to `/xavi-api/` blocked until all PHP handler actions have FastAPI equivalents
- **Action**: Set `window.srnnApiUrl`, `window.managerApiUrl` in HTML templates for progressive migration

**7b.4 Details — Dead Code Removal:**
- Removed 5 dead PHP methods (~390 lines): `_getMonitorLogSummary` (53 lines), `_getMonitorActivity` (220 lines), `_getPipelineLiveStatus` (110 lines), `_getTrackLabelMap` (orphaned by _getMonitorActivity), `_monitorManagerLogGroupCounts` (orphaned by _getMonitorLogSummary)
- Kept `_monitorFileSnapshot` and `_getMonitorRuntimeFiles` (still called from `manager_api`)
- All 8 legacy route modules in `api/routes/` retained for backward compatibility (PHP still calls `/srnn/*`, `/brain/*` etc. via SrnnApiClient)
- SQLite3 instantiation count: 61 remaining (down from 64 before removal, 77 originally)
- PHP controller: 27,012 lines (down from ~28K)

---

## Phase 8: Acceleration Planes (Planned)

> **Goal:** Implement Part II's three-plane model (compression + conditional
> memory) and Part V's audit/explainability persistence. These are post-v0
> optimizations that build on the stable cognition core.

### 8.0 Phase 8 concrete steps

| Step | Task | Paper ref | Target file(s) | Status |
|------|------|-----------|-----------------|--------|
| | **Plane B — Compression** | Part II §5.2 | | |
| **8.1** | TurboQuant/PolarQuant sidecar for vector search — compressed local ANN alongside authoritative Milvus | Part II §6.2 | `srnn/vector_sidecar.py`, `xavi/app.py`, `srnn/cognition/loop.py` | ✅ Done |
| **8.2** | Compressed vector replicas for federation node snapshots | Part II §6.5 | `federation/replicator.py` | Planned |
| **8.3** | Agent KV-cache compression experiments (llama.cpp TurboQuant fork) | Part II §6.4 | `ollama/` or separate eval surface | Planned |
| | **Plane C — Conditional memory** | Part II §5.3 | | |
| **8.4** | Engram-style deterministic lookup for static knowledge — lyric n-grams, motif bundles, track-sequence n-grams, witness templates | Part II §7.1–7.3 | `srnn/cognition/engram.py` (new) | ✅ Done |
| **8.5** | Integrate conditional memory `r_t` into Φ* recurrence | Part II §5.3 | `srnn/cognition/phi.py`, `srnn/cognition/rnn_cell.py` | ✅ Done (phi.py) |
| **8.5b** | Wire `r_t` vector through to rnn_cell gate modulation — cosine alignment with state boosts input gate, blends into proposal | Part II §7.1 | `srnn/cognition/phi.py`, `srnn/cognition/rnn_cell.py`, `srnn/cognition/loop.py` | ✅ Done |
| | **Part V audit & explainability** | Part V §8.2–8.5 | | |
| **8.6** | Add Part V persistence: `witness_signatures`, `witness_sector_defs`, `trace_interference`, `claim_conflicts`, `merge_decisions` tables | Part V §8.2 | `srnn/cognition/persistence.py` | ✅ Done |
| **8.6b** | Wire witness persistence — CognitionLoop.step() persists signatures; seed DEFAULT_SECTORS on init; EngramStore passed to PhiOperator | Part V §8.2 | `srnn/cognition/loop.py` | ✅ Done |
| **8.7** | Merge explainability — expose which claims survived, transferred, were suppressed, and which tensions retained | Part V §8.5 | `srnn/cognition/merge.py`, `srnn/cognition/synthesis.py` | ✅ Done |
| **8.8** | Formal loop traversal policies — each loop declares favored/suppressed sectors, min evidence density, contradiction tolerance, temporal span, source weights | Part V §8.3 | `srnn/cognition/loop.py` | ✅ Done |
| **8.8b** | Enforce policies in loop.step() — evidence gate, source weighting, policy-based meta_summary scaling | Part V §8.3 | `srnn/cognition/loop.py` | ✅ Done |
| | **Narrator & training** | Parts III–IV | | |
| **8.9** | Narrator LSTM split-memory — durable long-memory vs current narrative expression state | Part IV §9.8 | `srnn/cognition/rnn_cell.py`, `srnn/cognition/loop.py` | ✅ Done |
| **8.10** | CPC pretraining for chronicle encoders | Part I §13.3 | new module | Deferred (training infra) |
| **8.11** | Small learned proposal models for loop-local prediction | Part IV §15 | new module | Deferred (training infra) |
| | **Integration tests** | | | |
| **8.12** | Test coverage for rnn_cell, merge, witness/policy — 82 new tests across 3 files | — | `tests/test_rnn_cell.py`, `tests/test_merge.py`, `tests/test_witness_policy.py` | ✅ Done |

**8.1 Details — TurboQuant Sidecar:**
- **srnn/vector_sidecar.py** (new, ~350 lines): `VectorSidecar` class with Milvus export, compressed index build, search-with-fallback, recall validation
- **Configured collections**: `brain_memory`, `meta_objects`, `dt_events` (conservative start per §6.2)
- **NOT sidecar'd**: `music_tracks`, `clusters` (canonical identity-critical)
- **FastAPI endpoints** (`/xavi/sidecar/*`): status, load, search, validate, unload, reload-all
- **Cognition loop hook**: `compressed_candidates()` method added to `CognitionLoop` for 8.4/8.5 usage
- **Pre-existing**: `srnn/turbo_quant.py` (842 lines) — full TurboQuant engine already implemented
- **Test coverage**: 14 tests (all pass) in `tests/test_vector_sidecar.py`
- **Architecture**: Milvus = truth → sidecar = fast compressed read path → rerank on float if needed

### 8.4 + 8.5 Details (Engram + Conditional Memory r_t)

- **New module**: `srnn/cognition/engram.py` (~300 lines)
  - `EngramKey`: deterministic hash from (epoch, recent_tracks, motif_bundle, witness_family, story_axes)
  - `EngramRecord`: single retrieved memory with weight, payload, optional embedding
  - `EngramResult`: aggregation container; `.r_t` property computes weighted average vector
  - `EngramStore`: 3-tier retrieval (SQLite hash O(1) → sidecar ANN → Milvus float)
    - SQLite `engram_cache` table with weight boosting on hits, decay on prune
    - `store_motif_sequence()` for §7.2 track bigram/trigram patterns
    - `prune()` enforces min_weight and max_entries limits
  - `synthesize_key(state)`: builds key from CognitionState attributes
  - Memory types: `agent_knowledge`, `motif_sequence`, `lyric_ngram`, `event_pattern`, `witness_template`
- **phi.py integration**: Step 5.7 inserted between query-context boosting and energy tracking
  - `PhiOperator.__init__` accepts optional `engram_store` parameter
  - On each phi_step: synthesizes key → retrieves engram → stores result on `h_prev.engram_result`
  - Graceful degradation: if store is None or retrieval fails, step is skipped
- **state.py**: Added `engram_result: dict` field to `CognitionState` with to_dict/from_dict roundtrip
- **Observables**: `engram` key added to phi_step output (hit, source, n_records, latency_ms)
- **Test coverage**: 23 tests (all pass) in `tests/test_engram.py`
  - Key determinism/variation (5), Record vectors (2), Result r_t aggregation (3)
  - Store CRUD/prune/stats (9), PhiOperator integration (4)
- **rnn_cell.py**: Gate-level r_t injection deferred to 8.5b (requires live training data to tune gate biases)

### 8.6 Details (Part V Audit Tables)

- **5 new tables** added to `PART_V_AUDIT_SCHEMA` in `srnn/cognition/persistence.py`:
  1. `srnn_witness_signatures` — per-packet witness sector scores with dominant sector & confidence
  2. `srnn_witness_sector_defs` — catalog of sector gating rules (seeded from DEFAULT_SECTORS)
  3. `srnn_trace_interference` — per-loop-pair reinforcement/cancellation/sector-overlap records
  4. `srnn_claim_conflicts` — claim incompatibility records with cancellation energy & resolution
  5. `srnn_merge_decisions` — full merge audit trail: survived/suppressed/transferred/tension-retained
- **CognitionStore methods** (15 new): save/get for each table, plus `seed_default_sectors()`, `save_*_batch()`, `get_merge_audit()`
- **Schema auto-migration**: `_ensure_schema()` now executes both `PERSISTENCE_SCHEMA` + `PART_V_AUDIT_SCHEMA`
- **Test coverage**: 15 tests (all pass) in `tests/test_part_v_audit.py`
- **Integration ready**: Tables persist the transient output of existing `WitnessSignature`, `WitnessSector`, and `ClaimMerger._apply_interference()` — step 8.7 will wire the merge.py calls

### 8.7 Details (Merge Explainability)

- **merge.py**: Added `merge_with_audit()` → returns `(merged_claims, audit_decisions)` alongside the original `merge()` (kept for backward compat)
  - `_deduplicate_with_audit()`: tracks absorbed (suppressed) claims alongside survivors
  - Audit records each claim's fate: `survived` (in top_n), `suppressed` (deduplicated), `transferred` (below cutoff)
  - Records `original_weight`, `final_weight`, `weight_transfer`, `tension_retained`, interference detail
- **app.py pipeline**: `_run_cognition_answer_pipeline()` now calls `merge_with_audit()` and persists audit via `store.save_merge_decisions_batch()`
  - Graceful: if persist fails, logs warning and continues (answer pipeline not blocked)
- **No synthesis changes needed**: synthesis.py is stateless; audit data is orthogonal

### 8.8 Details (Loop Traversal Policies)

- **`TraversalPolicy` dataclass** added to `srnn/cognition/witness.py`:
  - 6 policy dimensions: `favored_sectors`, `suppressed_sectors`, `min_evidence_density`, `contradiction_tolerance`, `temporal_span`, `source_weights`
  - `witness_policy` property for backward compat with GATE_PRESETS
  - `admits(evidence_density)` gate check, `source_weight(source_type)` lookup
  - Serializable via `to_dict()`
- **`LOOP_POLICIES` registry**: 9 entries (chronological, exploratory, thematic, social, storyboard, replay, contrastive, narrator, default)
  - Aligned with existing `GATE_PRESETS` witness_policy values
  - Added min_evidence_density (0.0–0.4), contradiction_tolerance (0.1–1.0), temporal_span, source_weights per type
- **`get_traversal_policy(loop_type)`**: lookup helper with default fallback
- **CognitionLoop**: `self.policy = get_traversal_policy(loop_type)` set in `__init__`

### 8.9 Details (Narrator LSTM Split-Memory)

- **rnn_cell.py LSTM branch**: Replaced hardcoded `o_t = 0.7` with dynamic output gate computed from `evidence_quality`
  - Expression state now has its own recurrence: `e_new = f_expr * e_old + i_expr * cell_inject + synapse + witness`
  - Previous expression state `short_vec_in[j]` is preserved and used (was previously overwritten from cell state)
  - Separate gate params: `expression_forget_base=0.85`, `expression_input_base=0.35`, `output_gate_base=0.65`
- **GATE_PRESETS['narrator']**: Added 3 new fields for split-memory control
- **Result**: Durable memory (long_vec) retains facts with high `f_t=0.96`; expression state (short_vec) adapts tone with `f_expr=0.85`
- **Steps 8.10–8.11**: Deferred — CPC pretraining and learned proposal models require GPU training infrastructure

### 8.5b Details (r_t Gate Modulation)

- **phi.py Step 5.7**: Now computes `e_result.r_t` (weighted average embedding, 384-dim) and includes it in `h_prev.engram_result['r_t']` as a float list — previously only stored metadata (hit, source, n_records, latency_ms)
- **rnn_cell.py**: New engram gate modulation block after prediction error:
  - Extracts `r_t_vec` from `h_prev['engram_result']`
  - Computes cosine similarity between `r_t` and `short_vec` (current state direction)
  - Aligned recall (`r_t_signal > 0`) boosts input gate by `r_t_signal * 0.08` (memories aligned with current state get admitted faster)
  - Strong alignment (`r_t_signal > 0.3`) also boosts forget gate by `r_t_signal * 0.03` (retain context when memory confirms trajectory)
  - `r_t` blended into proposal vector at `min(r_t_signal * 0.15, 0.1)` blend ratio when alignment > 0.1
  - `cell_state['last_r_t_signal']` recorded for diagnostics
- **loop.py**: `engram_result` now passed in layer5 dict to rnn_cell; `r_t_signal` and `engram` emitted in observables
- **Test coverage**: 4 r_t tests in `tests/test_rnn_cell.py` (no engram, aligned hit, miss, orthogonal)

### 8.6b Details (Witness Persistence Wiring)

- **CognitionLoop.__init__**: Now constructs `EngramStore(self.db)` and passes to `PhiOperator(engram_store=...)` — engram retrieval activates automatically
- **CognitionLoop.__init__**: Now constructs `CognitionStore(self.db)` and calls `seed_default_sectors()` to populate `srnn_witness_sector_defs` on first run
- **CognitionLoop.step()**: After witness-sector accumulation, calls `self._cognition_store.save_witness_signature()` with `loop_run_id`, `step_index`, `track_number`, and `{dominant_sector, confidence, sector_scores}`
- **Graceful**: All new wiring wrapped in `try/except` — failures log at debug level and never block the step pipeline
- **Remaining unwired**: `save_trace_interference()` (needs merge layer changes), `save_claim_conflict()` (needs conflict detection logic)

### 8.8b Details (Policy Enforcement)

- **CognitionLoop.step()**: After building `meta_summary`, calls `self.policy.admits(evidence_density)` — returns early with `{'skipped': True, 'reason': 'policy_evidence_gate'}` if evidence_density < `min_evidence_density`
- **Source weighting**: Calls `self.policy.source_weight(source_type)` and scales `meta_summary['energy']`, `meta_summary['connection']`, `meta_summary['evidence_quality']` by the policy weight (e.g., social loop weights social sources 1.5x, tracks 0.8x)
- **Effect**: Replay loop (min_evidence_density=0.4) now actually skips low-evidence packets; exploratory loop (min=0.0) admits everything; thematic (min=0.3) gates mid-quality
- **Downstream**: `contradiction_tolerance` available on `self.policy` for merge layer to consume (currently unused by merge — future step)

### 8.12 Details (Test Coverage Expansion)

- **tests/test_rnn_cell.py** (30 tests): GRU update (6), LSTM split-memory (4), contrastive (2), engram r_t modulation (4), SynapticAccumulator (4), GateDiagnostics (2), prediction error (3), gate presets (3), multi-step (2)
- **tests/test_merge.py** (21 tests): basic merge (4), deduplication (3), merge_with_audit (4), interference (3), witness cosine (4), evidence absorption (3)
- **tests/test_witness_policy.py** (31 tests): TraversalPolicy (8), LOOP_POLICIES (5), get_traversal_policy (3), WitnessSignature (5), WitnessSectorProjector (5), SemanticWitness (5)
- **Total new**: 82 tests across 3 files; all pass alongside 52 existing tests = **134 total tests**

---

## Phase 9: Integration Hardening (✅ Complete)

> **Goal:** Complete the remaining unwired persistence calls, add integration
> smoke tests, and create stub modules for deferred training components.

### 9.0 Phase 9 concrete steps

| Step | Task | Paper ref | Target file(s) | Status |
|------|------|-----------|-----------------|--------|
| **9.1** | Wire `save_trace_interference()` — ClaimMerger emits interference records during `_apply_interference()` | Part V §5.5 | `srnn/cognition/merge.py`, `xavi/app.py` | ✅ Done |
| **9.2** | Wire `save_claim_conflict()` — build conflict detector that identifies contradictory claims over shared evidence | Part V §5.6 | `srnn/cognition/merge.py`, new detector module | ✅ Done |
| **9.3** | CPC pretraining stub module — `srnn/cognition/cpc.py` with `ContrastivePredictiveEncoder` class, forward pass spec, loss function signature | Part I §13.3 | `srnn/cognition/cpc.py` (new stub) | ✅ Done |
| **9.4** | Learned proposal model stub — `srnn/cognition/proposal_net.py` with `ProposalNetwork` class, input/output spec | Part IV §15 | `srnn/cognition/proposal_net.py` (new stub) | ✅ Done |
| **9.5** | Integration smoke test — wire CognitionLoop with mock DB, run 20 steps through phi→rnn_cell→witness pipeline, verify no crashes and all observables populated | — | `tests/test_integration_loop.py` | ✅ Done |
| **9.6** | Policy-aware merge — pass `contradiction_tolerance` from loop policies into `ClaimMerger._apply_interference()` cancellation threshold | Part V §8.3 | `srnn/cognition/merge.py`, `xavi/app.py` | ✅ Done |
| **9.7** | JS URL migration pass 2 — update remaining hardcoded API URLs in multi-grid JS components to use `window.srnnApiUrl` | — | `live/application/themes/*/js/*.js` | ✅ Done |
| **9.8** | PHP SQLite3 pass 2 — migrate `_srnnAiPlaylistGetData()` discovery queries to FastAPI discovery_router endpoints | — | `controller/single_pages/rnn_chat.php`, `xavi/app.py` | ✅ Done |

---

## Phase 10: Cognition Polish & Production Readiness (✅ Complete)

> **Goal:** Wire remaining cognition subsystems (skip coherence, cache decay, event-driven snapshots, trainable proposal network) and update all documentation to reflect actual implementation status.

### 10.0 Phase 10 concrete steps

| Step | Task | Paper ref | Target file(s) | Status |
|------|------|-----------|-----------------|--------|
| **10.1** | Wire skip coherence into `loop.step()` — when `connection_score < 0.15` (non-local jump), compute full pairwise `compute_skip_coherence()` and log `skip_coherence` + `skip_jump` in observables | Part III §4.7 | `srnn/cognition/loop.py` | ✅ Done |
| **10.2** | Synaptic cache temporal decay — apply `decay_factor = 0.95` to all existing cache entries before adding new ones; prune entries below `0.01`; hard cap at 50 | Part I §7.4 | `srnn/cognition/rnn_cell.py` | ✅ Done |
| **10.3** | Event-driven snapshots — trigger `_save_snapshot()` on regime shift or `prediction_error > 0.7` in addition to every 10th step | Part III §4.3 | `srnn/cognition/loop.py` | ✅ Done |
| **10.4** | ProposalNetwork trainable linear layer — dual-mode (heuristic / trainable); Xavier-init W and b; online gradient descent via `step()`; full state_dict serialization | Part IV §15 | `srnn/cognition/proposal_net.py` | ✅ Done |
| **10.5** | Update paper Appendix B checklist — audit all 19 items against codebase; 18/19 now checked (witness feature flag remaining) | — | `docs/SRNN_Cognition_Architecture_Paper_v4.md` | ✅ Done |
| **10.6** | Add Phase 10 to REFACTOR_PLAN_v5.md | — | `docs/REFACTOR_PLAN_v5.md` | ✅ Done |
| **10.7** | Tests — 10 new tests: 7 for ProposalNetwork trainable mode, 3 for synaptic cache decay; total suite 199/199 pass | — | `tests/test_proposal_net.py`, `tests/test_rnn_cell.py` | ✅ Done |

---

## Phase 11: Two-Level Witness Dynamics (Part VI)

> **Goal:** Promote the Duotronic digital witness from a static per-packet signature into a two-level design: an **object witness** `W_t` that canonically summarizes the current packet, and a **recurrent witness-state** `W̃_t` that carries temporal evidence across the chain. The witness gains its own recurrence map `Ψ`, then feeds into an extended recurrence `Φ*`. This preserves the existing architecture while giving the SRNN a mathematically explicit way to let witnesses participate in memory.

> **Paper reference:** SRNN Cognition Architecture, Part VI — Two-Level Witness Dynamics, Recurrent Witness-State, and Expanded Mathematical Capability (2026-04-08)

### 11.0 Core equations

- **Object witness:** `W_t = Γ(b_t, x_t, c_t)` — already implemented as `WitnessSignature` / `WitnessSectorProjector`
- **Recurrent witness-state:** `W̃_t = Ψ(W̃_{t-1}, W_t, h_{t-1}, b_t, x_t, u_t)` — **new**
- **Extended chain update:** `h_t = Φ*(h_{t-1}, b_t, x_t, u_t, W_t, W̃_t, r_t)` — **new**
- **Branch-local witness:** `W̃_t^(ℓ) = Ψ^(ℓ)(W̃_{t-1}^(ℓ), W_t, h_{t-1}^(ℓ), b_t, x_t, u_t)` — **new**
- **Witness-informed ranking:** `Score_ℓ = α·Rel + β·Coh + γ·Temp + δ·Rec + η·WTraj_ℓ + ζ·Expr`

### 11.1 Phase 11 concrete steps

| Step | Task | Paper ref | Target file(s) | Status |
|------|------|-----------|-----------------|--------|
| | **Phase VI-A — Formalize the two-level witness contract** | | | |
| **11.1** | Define `RecurrentWitnessState` dataclass — family carryover `family_mass[k]`, story axis evidence `story_axis[m]`, open callbacks `open_callbacks[j]`, sector trace `sector_trace[s]`, contradiction pressure, coherence drift, regime evidence | Part VI §4.2, §5 | `srnn/cognition/witness.py` | ✅ Done |
| **11.2** | Define `Ψ` update function — `witness_step(W̃_{t-1}, W_t, h_{t-1}, packet)` with family-specific decay (`λ_k`), callback accumulation (`ρ_j·cb + trigger - resolve`), sector confidence update, drift computation `D(Ŵ_t, W_t)` | Part VI §4.2, §5.1-5.5 | `srnn/cognition/witness.py` | ✅ Done |
| **11.3** | Add contract file `WITNESS_CONTRACT.md` — object witness schema, recurrent witness-state schema, update map `Ψ`, extended `Φ*`, canonical vs branch-local write rules | Part VI §10.A | `docs/WITNESS_CONTRACT.md` | ✅ Done |
| | **Phase VI-B — Minimal recurrent witness-state** | | | |
| **11.4** | Wire `Ψ` into `CognitionLoop.step()` — after `WitnessProject` computes `W_t`, call `witness_step()` to update branch-local `W̃_t^(ℓ)`, store on loop state | Part VI §4.3 | `srnn/cognition/loop.py` | ✅ Done |
| **11.5** | Add `RecurrentWitnessState` to `CognitionState` — serialize/deserialize in `to_dict()` / `from_dict()`, include in snapshots | Part VI §6.1 | `srnn/cognition/state.py` | ✅ Done |
| **11.6** | Extend `Φ*` — pass `W̃_t` into `RecurrentCell.step()` as additional input; witness-state contributes to gate functions alongside existing `witness_bias` | Part VI §4.3 Eq.18 | `srnn/cognition/rnn_cell.py`, `srnn/cognition/phi.py` | ✅ Done |
| **11.7** | Implement witness-side decay — family-specific decay rates (`λ_k` per witness family), fast lyrical echoes vs slow autobiographical motifs | Part VI §5.2 Eq.6 | `srnn/cognition/witness.py` | ✅ Done |
| **11.8** | Implement callback persistence — `cb_{t,j} = ρ_j · cb_{t-1,j} + trigger_{t,j} - resolve_{t,j}` tracked inside `RecurrentWitnessState` | Part VI §5.3 | `srnn/cognition/witness.py` | ✅ Done |
| **11.9** | Implement coherence drift — `drift_t = D(Ŵ_t, W_t)` using structured mismatch between expected and actual object witness | Part VI §5.5 Eq.9 | `srnn/cognition/witness.py` | ✅ Done |
| | **Phase VI-C — Integrate into loop ranking** | | | |
| **11.10** | Add `WTraj_ℓ` to `LoopRanker` — witness persistence score, callback resolution rate, drift control, trajectory support as new ranking axis | Part VI §11 | `srnn/cognition/ranking.py` | ✅ Done |
| **11.11** | Add witness regime evidence to regime scoring — `p(z_t | W̃_t, h_{t-1}) ∝ p(W_t | z_t) · p(z_t | z_{t-1})` as precision-weighted input | Part VI §5.4 Eq.8 | `srnn/cognition/phi.py` | ✅ Done |
| | **Phase VI-D — Expose inspectable outputs** | | | |
| **11.12** | Add witness-state logging fields to loop traces — `object_witness_id`, `witness_state_version`, `witness_decay_delta`, `witness_callback_delta`, `witness_regime_evidence`, `witness_drift_score`, `witness_support_score`, `witness_contradiction_score` | Part VI §6.3 | `srnn/cognition/loop.py`, `srnn/cognition/persistence.py` | ✅ Done |
| **11.13** | Add witness-state snapshot API routes — `GET /xavi/brain/diagnostics/recurrent-witness/{loop_id}` | Part VI §10.D | `xavi/app.py` | ✅ Done |
| **11.14** | Persist `RecurrentWitnessState` at checkpoints — canonical snapshots via `CognitionState.to_dict()` → snapshot pipeline | Part VI §6.1 | `srnn/cognition/state.py`, `srnn/cognition/loop.py` | ✅ Done |
| | **Phase VI-E — Tests and documentation** | | | |
| **11.15** | Tests for `RecurrentWitnessState` and `witness_step()` — 29 tests: decay, callback accumulation, drift computation, serialization roundtrip, branch isolation, boundary conditions, ranking integration | — | `tests/test_recurrent_witness.py` | ✅ Done |
| **11.16** | Integration tests — included in `test_recurrent_witness.py` (TestWitnessTrajectoryRanking, TestCognitionStateRecurrentWitness) | — | `tests/test_recurrent_witness.py` | ✅ Done |
| **11.17** | Update all paper cross-references and REFACTOR_PLAN | — | `docs/*` | ✅ Done |

### 11.2 Deferred extensions (behind feature flags, Phase VI-E)

These are available once the base two-level design is working but are not required for v1:

| Extension | Paper ref | Description |
|-----------|-----------|-------------|
| **CPC witness learning** | Part VI §7.1 | Train witness families to predict future chronicle packets via contrastive objective |
| **Continuous-time witness flow** | Part VI §7.2 | Neural CDE `dW̃_t = f_θ(W̃_t) dX_t` for irregular chronicle sampling |
| **Duration-aware witness sectors** | Part VI §7.3 | HSMM sector model `p(s_t, d_t | s_{t-1}, d_{t-1}, W̃_{t-1})` with explicit durations |
| **Switching witness-regime dynamics** | Part VI §7.4 | rSLDS-style `W̃_t = A_{z_t} W̃_{t-1} + B_{z_t} W_t + ε_t` with mode-specific update laws |
| **Precision-weighted witness error** | Part VI §7.5 | `e_t^(w) = Λ_t^{1/2} (W_t - Ŵ_t)` with confidence matrix |
| **Predictive-state witness surfaces** | Part VI §7.6 | PSR-style predictive witness (callback reappearance probability, sector persistence, motif recurrence horizon) |

---

## Phase 12: Cheap Worker Math & Polygonal Operators (Part VII)

> **Goal:** Implement Part VII's revised chain semantics — split the cognition plane into exact canonical coordinator commits and cheap approximate worker-loop recurrence. Add quantized worker paths, sketch-backed witness mass, compressed search sidecars, conditional memory tables, and polygonal operator prototypes. This preserves canonical correctness while making multi-loop cognition practical on commodity CPU and low-GPU nodes.

> **Paper reference:** SRNN Cognition Architecture, Part VII — Revised Chain Semantics, Cheap Worker Math, Polygonal Matrix Semantics, and Hardware-Agnostic Acceleration for the SRNN (2026-04-08)

### 12.0 Core development-phase semantics

- **Full state:** `S_t = (C_t, H_t^canon, W_t, W̃_t, B_t)`
- **Canonical commit:** `(C_t, H_t^canon) = Commit(C_{t-1}, H_{t-1}^canon, packet_t, validated_inputs_t)`
- **Witness update:** `(W_t, W̃_t) = WitnessUpdate(W_{t-1}, W̃_{t-1}, packet_t, H_{t-1}^canon)`
- **Worker branch:** `B_t = WorkerStep(B_{t-1}, packet_t, W_t, W̃_t, compressed_sidecars_t)`
- **Combined strategy:** TurboQuant (cheap candidate transport) + Engram (cheap lookup recall) + RecurrentWitnessState (cheap temporal accumulation)

### 12.1 Phase 12 concrete steps

| Step | Task | Paper ref | Target file(s) | Status |
|------|------|-----------|-----------------|--------|
| | **Phase VII-A — Finish Part VI contract and recurrent witness-state** | | | |
| **12.1** | Verify `WITNESS_CONTRACT.md` complete and consistent with implementation | Part VII §20.1 | `docs/WITNESS_CONTRACT.md` | ✅ Done (Phase 11) |
| **12.2** | Verify `RecurrentWitnessState` implemented | Part VII §20.2 | `srnn/cognition/witness.py` | ✅ Done (Phase 11) |
| **12.3** | Verify `Ψ` wired into `loop.py` | Part VII §20.3 | `srnn/cognition/loop.py` | ✅ Done (Phase 11) |
| **12.4** | Verify witness-state passed into `rnn_cell.py` and ranking | Part VII §20.4 | `srnn/cognition/rnn_cell.py`, `srnn/cognition/ranking.py` | ✅ Done (Phase 11) |
| | **Phase VII-B — Cheap worker math behind feature flags** | | | |
| **12.5** | Add int8 worker recurrence path — `Q_b,R` quantizer for branch-local hidden state, shadow recurrence `ĥ_t^(ℓ) = Q(Φ_worker(Q^{-1}(ĥ_{t-1}^(ℓ)), packet_t, witness_t))`, feature-flagged | Part VII §6 | `srnn/cognition/rnn_cell.py` | ✅ Done |
| **12.6** | Add Count-Min Sketch worker `family_mass` — sketch-backed alternative to dictionary-heavy mass tables, feature-flagged for worker loops only | Part VII §8 | `srnn/cognition/witness.py` | ✅ Done |
| **12.7** | Add sparse residual storage for worker loops — `TopK_τ(e)` thresholded precision-weighted residuals, approximate fit `F̂_i` | Part VII §9 | `srnn/cognition/loop.py`, `srnn/cognition/ranking.py` | ✅ Done |
| **12.8** | Add shift-add decay options for worker-side witness updates — `x ← x - (x >> k) + new` approximations for common λ values | Part VII §10 | `srnn/cognition/witness.py` | ✅ Done |
| | **Phase VII-C — Search sidecars and compressed retrieval** | | | |
| **12.9** | Add binary signature first-pass filter — Hamming distance / popcount prefilter for embeddings and witness summaries | Part VII §11 | `srnn/turbo_quant.py`, `srnn/vector_sidecar.py` | ✅ Done |
| **12.10** | Add FWHT sidecar experiments — `(1/√d) H_d D x` structured rotation for sidecar compression, replacing dense random rotation | Part VII §7 | `srnn/turbo_quant.py` | ✅ Done |
| **12.11** | Add candidate prefilter → float rerank pipeline — `binary prefilter → compressed sidecar candidates → float rerank → loop update` | Part VII §11.2 | `srnn/vector_sidecar.py`, `srnn/cognition/engram.py` | ✅ Done |
| | **Phase VII-D — Conditional memory** | | | |
| **12.12** | Add Engram-style memory tables — witness-family templates, lyric n-gram bundles, callback motifs, story fragments, social chain templates, chronicle-local symbolic packets | Part VII §17.2 | `srnn/cognition/engram.py` | ✅ Done |
| **12.13** | Add deterministic lookup keys — `r_t = Retrieve(k_t, M)` with keys derived from `(packet, W_t, W̃_t, query_context)` | Part VII §17.2 | `srnn/cognition/engram.py`, `srnn/cognition/loop.py`, `srnn/cognition/phi.py` | ✅ Done |
| | **Phase VII-E — Polygonal operator experiments** | | | |
| **12.14** | Implement `PolygonCell` dataclass and decode functions — `decode_scalar()`, `decode_dual()`, `apply_polygon_row()`, family-specific decoders | Part VII §16.5 | `srnn/cognition/polygon_ops.py` | ✅ Done |
| **12.15** | Benchmark polygonal operators — witness-family transition tables, gate banks, reinforcement adjacency, sidecar transforms vs dense/sparse/low-rank baselines | Part VII §16.4, §16.6 | `tests/test_polygon_ops.py` | ✅ Done |
| **12.16** | Integrate polygonal operators where beneficial — optional worker-side polygonal gate-bank path for recurrent witness bias, behind feature flag | Part VII §16.7 | `srnn/cognition/polygon_ops.py`, `srnn/cognition/rnn_cell.py`, `srnn/cognition/loop.py` | ✅ Done |
| | **Phase VII-F — Evaluation gates** | | | |
| **12.17** | Compare float vs cheap worker loops on ranking agreement — measure Kendall τ and top-k identity stability | Part VII §21.2 | `tests/test_worker_parity.py` | ✅ Done |
| **12.18** | Compare binary prefilter + compressed search vs float-only search on recall@k and answer quality | Part VII §21.3 | `tests/test_search_parity.py` | ✅ Done |
| **12.19** | Compare exact witness dicts vs sketch-backed witness-state on ranking stability | Part VII §21.2 | `tests/test_sketch_parity.py` | ✅ Done |
| **12.20** | Compare loop Kendall τ before and after quantized worker rollout | Part VII §20.20 | `tests/test_worker_parity.py` | ✅ Done |

### 12.2 Additional Part VII components (behind feature flags)

These are available once the base cheap-worker design is working:

| Extension | Paper ref | Description |
|-----------|-----------|-------------|
| **Shared sketch across loops** | Part VII §12 | Low-rank shared base `H_t` with loop-specific residuals `Δ_t^(ℓ)`: `h_t^(ℓ) ≈ W_ℓ H_t + Δ_t^(ℓ)` |
| **Hebbian synaptic plasticity** | Part VII §13 | Online `Δw_ij = η(x_i · x_j − γ w_ij)` update for `srnn_connections` weights |
| **Sinkhorn divergence coherence** | Part VII §14 | Geometry-aware trace coherence via entropic transport over witness sectors / story axes |
| **Nyström social kernels** | Part VII §15.1 | Low-rank kernel approximation for large social-post similarity |
| **Tensor-train trace compression** | Part VII §15.2 | Compressed trace representation for long replay storage and cross-node shipping |
| **OjaKV adaptive cache** | Part VII §18.2 | Online low-rank subspace adaptation for worker-side cache compression |

### 12.3 Canonical safety gates (Part VII §21)

Before deploying any cheap-math path to production:

1. No corruption of the coordinator commit ledger
2. No change in native/export null handling at the commit boundary
3. No silent coercion of unknown to zero
4. No loss of replayability for the canonical chain
5. Ranking agreement with float worker baseline (Kendall τ ≥ 0.85)
6. Stable top-k loop identity over representative chronicle windows
7. Bounded divergence in witness trajectory metrics
8. No catastrophic failure in long replay windows (≥ 1000 steps)
9. Candidate recall acceptable under compressed prefilter
10. Memory lookup improves story continuity or prompt economy

## Phase 13: Rollout Hardening & Compatibility Cleanup

> **Goal:** Convert Part VII from a feature-complete research slice into an operationally safe rollout. Centralize worker defaults, expose runtime diagnostics for branch-local approximations, repair legacy parity-suite blockers, and make meta-object extraction tolerant of older fixture schemas without weakening required contracts.

### 13.1 Phase 13 concrete steps

| Step | Task | Target file(s) | Status |
|------|------|----------------|--------|
| **13.1** | Centralize cheap-worker rollout defaults and env parsing helpers | `srnn/config.py` | ✅ Done |
| **13.2** | Wire rollout defaults into branch-local runtime flag resolution and emit per-step worker metrics | `srnn/cognition/loop.py` | ✅ Done |
| **13.3** | Add cheap-worker diagnostics API for rollout profile, quantization, sketch mode, and residual approximation drift | `srnn/cognition/diagnostics.py`, `xavi/app.py` | ✅ Done |
| **13.4** | Repair pre-existing SBCL parity suite collection blocker in state-hash serialization tests | `tests/test_sbcl_parity.py` | ✅ Done |
| **13.5** | Make bulk meta-object extraction schema-compatible with older/test fixtures while still hard-failing missing required columns | `srnn/meta_objects/extractors/__init__.py` | ✅ Done |
| **13.6** | Rerun targeted regression slices and record any residual failures for post-Phase-12 stabilization | `tests/test_sbcl_parity.py`, `tests/test_meta_objects.py`, `tests/test_meta_objects_snapshot.py` | ✅ Done (`test_meta_objects_snapshot.py` verified on reduced snapshot subset via `SRNN_META_OBJECTS_TEST_LIMIT=4`) |

### 13.2 Exit criteria

- Cheap-worker branch defaults come from one config surface instead of per-loop ad hoc env parsing.
- The cognition API exposes rollout diagnostics that let operators compare enabled worker features with quantization and approximation behavior.
- The SBCL parity suite collects again, so any remaining failures are behavioral rather than syntax corruption.
- Meta-object extraction works against both production schemas and reduced in-memory test schemas that omit optional sonic feature columns.

---

## Phase 4: Architecture v2 — Agno + Hovod + SRNN Daemon

> **Goal:** Replace the entire PHP+FastAPI proxy layer with a clean Agno-based
> backend. Port all 3,180 mp4 media files to Hovod (S3-backed). Make the SRNN
> a self-playing background daemon whose audience is the neural network itself,
> not humans. Convert the manager into pluggable multi-grid web components.

### 4.0 Design Principles

1. **The SRNN plays music to itself.** The playlist IS the time crystal — an
   infinite chronological loop (oldest → newest → wrap). Human listeners are
   incidental observers, not the target audience.
2. **The media walk IS cognition.** Each track advance propagates the RNN forward
   through the connection graph. Meta-object recurrence chains are the network's
   memory. The compound probability shuffle is the attention mechanism.
3. **Hovod hosts all media.** mp4 files move to S3, Hovod transcodes + serves
   HLS. The frontend iframes Hovod's embed player. No more direct file serving.
4. **Agno replaces FastAPI.** AgentOS auto-generates the API. Existing algorithms
   (shuffle, similarity, enrichment) become Agno tools. Milvus is the knowledge
   store. Sessions/memory are Agno-native.
5. **Multi-grid dashboard.** Manager pages become web components pluggable into
   the xavi-multi-grid panel system. Drag, resize, compose dashboards freely.
6. **Lisp stays.** The SBCL symbolic reasoning layer (srnn-brain.service,
   srnn-daemon.service) gets revived as Agno tools callable from the agent.

### 4.1 New Port Map

| Port | Service | Purpose |
|------|---------|---------|
| **8050** | **xavi-api** | Agno AgentOS — main API (replaces 8030 FastAPI) |
| **8051** | **xavi-daemon** | SRNN background DJ daemon (internal) |
| **8031** | **srnn-brain** | Common Lisp brain server (existing) |
| **3002** | **hovod-api** | Hovod video API (existing) |
| **3003** | **hovod-dash** | Hovod dashboard (existing) |
| **19530** | **milvus** | Vector database (existing) |
| **11434** | **ollama** | LLM inference (existing) |
| **8885-8904** | **searxng fleet** | Web search (existing) |
| **8870** | **trustgraph** | Knowledge graph UI (existing) |

### 4.2 New Directory Structure

```
srnn_server/
├── xavi/                            ← NEW: Agno-based backend
│   ├── __init__.py
│   ├── app.py                       ← AgentOS entrypoint (port 8050)
│   ├── agents/                      ← Agno Agent definitions
│   │   ├── __init__.py
│   │   ├── dj.py                    ← DJ Agent — playlist, shuffle, next-track
│   │   ├── enricher.py              ← Enrichment Agent — web research, tier processing
│   │   ├── curator.py               ← Curation Agent — meta-objects, chains, stories
│   │   ├── researcher.py            ← Research Agent — web search, discovery
│   │   └── social.py                ← Social Agent — Bluesky posting, engagement
│   ├── tools/                       ← Agno Tool wrappers around existing algorithms
│   │   ├── __init__.py
│   │   ├── shuffle.py               ← Wraps srnn/shuffle.py CompoundShuffle
│   │   ├── similarity.py            ← Wraps srnn/similarity.py (7-dim)
│   │   ├── enrichment.py            ← Wraps srnn/enricher.py SmartEnricher
│   │   ├── meta_objects.py          ← Wraps srnn/meta_objects/ pipeline
│   │   ├── playlist.py              ← Wraps srnn/playlist.py PlaylistBuilder
│   │   ├── searxng.py               ← SearXNG fleet search tool
│   │   ├── hovod.py                 ← Hovod API client (upload, transcode, embed)
│   │   ├── lisp.py                  ← SBCL brain RPC (port 8031)
│   │   ├── milvus_search.py         ← Direct Milvus queries
│   │   └── playback.py              ← Track control, stream URLs, Hovod embeds
│   ├── knowledge/                   ← Agno Knowledge bases (backed by Milvus)
│   │   ├── __init__.py
│   │   ├── tracks.py                ← Track features + metadata (srnn_features collection)
│   │   ├── connections.py           ← Similarity graph (srnn_connections collection)
│   │   ├── meta_objects.py          ← Meta-object instances + recurrence
│   │   ├── enrichment.py            ← Web enrichment data
│   │   └── social.py                ← Social engagement data
│   ├── daemon/                      ← SRNN Background DJ
│   │   ├── __init__.py
│   │   ├── loop.py                  ← Main daemon loop (infinite chronological walk)
│   │   ├── session.py               ← Global session state (wraps srnn/session.py)
│   │   ├── propagator.py            ← RNN forward propagation on each advance
│   │   ├── horizon.py               ← Dynamic horizon planning + quality kicks
│   │   └── api.py                   ← Internal FastAPI for daemon status (port 8051)
│   └── config.py                    ← Unified configuration
│
├── srnn/                            ← EXISTING: Core algorithms (kept, wrapped by tools)
│   ├── shuffle.py, session.py, similarity.py, enricher.py, ...
│   ├── meta_objects/                ← 51-file extractor pipeline
│   └── duotronic/                   ← Vector store + simulation
│
├── db/                              ← Milvus = PRIMARY, SQLite = read-only archive
├── data/music/                      ← 3,180 mp4 files (30 GB) → migrate to S3/Hovod
└── docker-compose.v2.yml            ← Updated compose with new services
```

### 4.3 SRNN Daemon — The Self-Playing Time Crystal

The daemon is the heart of the system. It plays music to itself, advancing
through the library chronologically and using the compound probability shuffle
to choose which connection to follow at each step.

```
┌──────────────────────────────────────────────────────────┐
│                    SRNN DAEMON LOOP                       │
│                                                          │
│  1. Load arrangement (chronological: oldest → newest)    │
│  2. Current track = arrangement[position]                │
│  3. Wait track.duration seconds                          │
│  4. Propagate RNN forward:                               │
│     a. Compute similarity to all neighbors               │
│     b. Apply compound probability (7-dim × age × cool)   │
│     c. Reinforce connection(prev, current, +0.005)       │
│     d. Update meta-object recurrence chains              │
│     e. Log to dt_events (duotronic timeline)             │
│  5. Advance position (wrap at end → epoch++)             │
│  6. Kick horizon quality (enrich upcoming tracks)        │
│  7. Replan dynamic horizon (meta-object threading)       │
│  8. Optional: share to Bluesky, discover new media       │
│  9. GOTO 2                                               │
│                                                          │
│  The playlist always loops: oldest → newest → oldest     │
│  The epoch counter tracks how many full cycles.          │
│  The connection reinforcement IS the learning.           │
│  The meta-object chains ARE the memory.                  │
└──────────────────────────────────────────────────────────┘
```

**Chronological ordering:**
- Base arrangement = all tracks ordered by `dt_events.id ASC` (chronological
  discovery order from duotronic.sqlite)
- Dynamic horizon replans 15 upcoming slots using meta-object selector +
  social engagement boost + quality tiers
- Locks the next 6 tracks (already enriched), replans slots 7–20
- Wraps at end of library → epoch increments → restarts from oldest

### 4.4 Hovod Media Migration

```
Current:  data/music/0001 - Artist _ Title.mp4  (3,180 files, 30 GB)
                    ↓
          S3 bucket (MinIO or external)
                    ↓
          Hovod ingest API → transcode to HLS (360p/720p/1080p)
                    ↓
Target:   Hovod serves HLS from S3, frontend iframes /embed/:playbackId
```

**Migration script** (`xavi/tools/hovod.py`):
1. For each mp4 in `data/music/`:
   - Extract track_number from filename prefix (e.g. "0469" from "0469 - ...")
   - Upload to Hovod via `POST /v1/assets` (direct upload or pre-signed S3 URL)
   - Store Hovod `asset_id` and `playback_id` in Milvus `music_tracks` collection
2. Hovod auto-transcodes to adaptive HLS
3. Frontend uses `<iframe src="hovod:3002/embed/:playbackId">` or raw HLS URL

**Playback in daemon**: The daemon doesn't need HLS — it just tracks position
and timing. Actual audio/video playback is optional (for human observers via
the multi-grid dashboard).

### 4.5 Agno Agent Definitions

#### DJ Agent (`xavi/agents/dj.py`)
```python
Agent(
    name="DJ",
    model=Ollama(id="qwen3:8b"),
    tools=[ShuffleTool, SimilarityTool, PlaybackTool, PlaylistTool],
    knowledge=tracks_knowledge,       # Milvus: srnn_features
    db=SqliteDb(db_file="db/agno.db"),
    instructions="""You are the SRNN DJ. You manage the infinite chronological
    playlist. When asked, explain why a track was chosen, what meta-object
    connections link it to neighbors, and what the current epoch/position is.
    You can generate playlists by keyword, theme, or acrostic encoding.""",
)
```

#### Enricher Agent (`xavi/agents/enricher.py`)
```python
Agent(
    name="Enricher",
    model=Ollama(id="qwen3:8b"),
    tools=[EnrichmentTool, SearXNGTool, MetaObjectTool, HovodTool],
    knowledge=enrichment_knowledge,   # Milvus: enrichment data
    instructions="""You enrich tracks with web data. For each track, search
    the SearXNG fleet, extract metadata (artist bio, album context, reviews),
    run meta-object extraction (14 extractors), and update the knowledge base.
    Tiers: web (basic metadata) → tier1 (lyrics+audio) → tier2 (visual+cultural)
    → tier3 (deep narrative+crossmodal).""",
)
```

#### Curator Agent (`xavi/agents/curator.py`)
```python
Agent(
    name="Curator",
    model=Ollama(id="qwen3:32b"),    # Heavier model for narrative reasoning
    tools=[MetaObjectTool, SimilarityTool, LispTool, PlaylistTool],
    knowledge=meta_object_knowledge,  # Milvus: meta_objects + recurrence
    instructions="""You curate the SRNN's understanding of its media library.
    You analyze meta-object recurrence chains, build narrative arcs across
    tracks, detect thematic clusters, and thread symbolic motifs through
    playlists. You use the Lisp brain for symbolic reasoning.""",
)
```

### 4.6 API Endpoints (Agno AgentOS auto-generates + custom routes)

#### Auto-generated by AgentOS (port 8050)
```
POST   /v1/agents/{agent_id}/runs          Chat with any agent
GET    /v1/agents/{agent_id}/sessions       List sessions
GET    /v1/sessions/{session_id}            Get session detail
GET    /v1/memory/{user_id}                 Get user memories
GET    /v1/knowledge/{kb_id}/search         Search knowledge base
WS     /v1/ws                               WebSocket for streaming
GET    /v1/health                            Health check
GET    /v1/metrics                           Prometheus metrics
```

#### Custom routes (mounted on same AgentOS app)
```
# Playback / Daemon
GET    /xavi/daemon/status                  Current track, position, epoch, timing
POST   /xavi/daemon/start                   Start/resume the daemon loop
POST   /xavi/daemon/stop                    Pause the daemon
GET    /xavi/daemon/history                 Recent playback log
GET    /xavi/daemon/arrangement             Current arrangement (full)
POST   /xavi/daemon/skip                    Skip to next track
POST   /xavi/daemon/seek/{track_number}     Jump to specific track

# Tracks / Library
GET    /xavi/tracks                         List tracks (paginated, filterable)
GET    /xavi/tracks/{tn}                    Track detail (features + meta-objects)
GET    /xavi/tracks/{tn}/connections         Similarity neighbors
GET    /xavi/tracks/{tn}/meta-objects       Meta-objects for track
GET    /xavi/tracks/{tn}/hovod              Hovod playback info (embed URL, HLS)
POST   /xavi/tracks/{tn}/enrich             Trigger enrichment

# Media / Hovod
GET    /xavi/media/stream/{tn}              Hovod HLS manifest URL for track
GET    /xavi/media/embed/{tn}               Hovod embed URL for iframing
GET    /xavi/media/thumbnail/{tn}           Track thumbnail
POST   /xavi/media/upload                   Upload new media → Hovod + index

# Playlists
GET    /xavi/playlists                      List all playlists
POST   /xavi/playlists                      Create playlist (keyword/theme/acrostic)
GET    /xavi/playlists/{id}                 Get playlist tracks
DELETE /xavi/playlists/{id}                 Delete playlist

# Meta-Objects
GET    /xavi/meta/stats                     Meta-object statistics
GET    /xavi/meta/chains/{tn}               Recurrence chains for track
GET    /xavi/meta/search?q=                 Search meta-objects
GET    /xavi/meta/diagnostics               System diagnostics
GET    /xavi/meta/models                    Registered models

# Enrichment
GET    /xavi/enrich/queue                   Enrichment queue status
POST   /xavi/enrich/batch                   Run batch enrichment
GET    /xavi/enrich/summary                 Library enrichment coverage

# Fleet / Infrastructure
GET    /xavi/fleet/status                   SearXNG fleet health
POST   /xavi/fleet/command                  Start/stop/restart fleet instances
GET    /xavi/system/stats                   System resource usage
GET    /xavi/system/docker                  Container status

# Dashboard State
GET    /xavi/dashboard/layouts              Saved multi-grid layouts
POST   /xavi/dashboard/layouts              Save layout
GET    /xavi/dashboard/widgets              Available widget catalog
```

### 4.7 Multi-Grid Dashboard Conversion

Each manager page becomes a **standalone web component** that can be plugged
into the xavi-multi-grid panel system:

| Current Manager Page | New Widget Tag | Grid Panel |
|---------------------|----------------|------------|
| `/manager/playing` | `<xavi-now-playing>` | Shows daemon state, current track, Hovod embed |
| `/manager/database` | `<xavi-data-browser>` | Generic DB table browser |
| `/manager/tracks` | `<xavi-track-list>` | Track list with search/filter |
| `/manager/fleet` | `<xavi-fleet-panel>` | SearXNG fleet status |
| `/manager/brain` | `<xavi-brain-panel>` | Brain state, enrichment |
| `/manager/brain_chain` | `<xavi-brain-chain>` | Chain reasoning workflows |
| `/manager/ai_search` | `<xavi-ai-search>` | AI-powered search |
| `/manager/bluesky` | `<xavi-bluesky-panel>` | Bluesky management |
| `/manager/social` | `<xavi-social-panel>` | Social media |
| `/manager/lyrics` | `<xavi-lyrics-panel>` | Lyrics browser |
| `/manager/logs` | `<xavi-logs-panel>` | Log viewer |
| `/manager/workflows` | `<xavi-workflows>` | Workflow management |
| `/manager/downloads` | `<xavi-downloads>` | Download queue |
| `/manager/stream_health` | `<xavi-stream-health>` | Stream monitoring |
| `/manager/agents` | `<xavi-agents-panel>` | Agno agent management |
| `/manager/video` | `<xavi-hovod-panel>` | Hovod video browser |
| `/manager/context_graph` | `<xavi-graph-panel>` | TrustGraph explorer |
| (new) | `<xavi-chat-panel>` | Chat with any Agno agent |
| (new) | `<xavi-timeline-panel>` | Chronological media timeline |
| (new) | `<xavi-similarity-graph>` | Force-directed connection graph |

Each widget:
1. Extends `HTMLElement` with Shadow DOM (existing pattern)
2. Accepts `api-base="http://localhost:8050"` attribute
3. Self-contained: fetches its own data from `/xavi/*` endpoints
4. Registered in `window.XAVI_MODULE_CONFIGS` for the multi-grid loader
5. Wrapped in a `GridObject` for drag/resize/snap (existing pattern)
6. State persisted to localStorage (existing pattern)

### 4.8 Implementation Order

| Step | Task | Depends On |
|------|------|------------|
| **4.8.1** | Install Agno + pymilvus in .venv | - |
| **4.8.2** | Scaffold `xavi/` directory with agents, tools, knowledge | 4.8.1 |
| **4.8.3** | Write tool wrappers for existing srnn/ modules | 4.8.2 |
| **4.8.4** | Write knowledge bases pointing at existing Milvus collections | 4.8.2 |
| **4.8.5** | Build AgentOS app.py with custom routes | 4.8.3, 4.8.4 |
| **4.8.6** | Build SRNN daemon loop (chronological walk) | 4.8.3 |
| **4.8.7** | Test daemon: verify it advances, reinforces, enriches | 4.8.6 |
| **4.8.8** | Write Hovod migration script | - |
| **4.8.9** | Run Hovod migration (3,180 mp4 → S3 → HLS) | 4.8.8 |
| **4.8.10** | Write Hovod tool (embed URLs, playback info) | 4.8.9 |
| **4.8.11** | Convert manager pages to standalone web components | - |
| **4.8.12** | Register widgets in multi-grid module system | 4.8.11 |
| **4.8.13** | Build `<xavi-now-playing>` with Hovod iframe | 4.8.10, 4.8.12 |
| **4.8.14** | Create systemd services for xavi-api + xavi-daemon | 4.8.5, 4.8.6 |
| **4.8.15** | Decommission old FastAPI (port 8030), PHP proxy | 4.8.14 |

---

## Appendix A: Created Files Inventory

### Infrastructure

| File | Purpose | Status |
|------|---------|--------|
| `docker-compose.yml` | Core: etcd + MinIO + Milvus + srnn-api | ✅ |
| `.env` / `.env.example` | Per-node env config | ✅ |
| `srnn/milvus_schema.py` | 20 collection schemas (IVF_FLAT, SSE4.2) | ✅ |
| `srnn/migrate.py` | SQLite → Milvus migration CLI | ✅ |
| `ollama/docker-compose.yml` | Ollama (port 11434, 8 CPU, 48GB) | ✅ |
| `agno/docker-compose.yml` | Agno (port 8040, 4 CPU, 8GB) | ✅ |
| `agno/Dockerfile` | python:3.12-slim + agno + openai | ✅ |
| `agno/entrypoint.py` | FastAPI with 3 agents | ✅ |

### FastAPI Application

| File | Endpoints | Status |
|------|-----------|--------|
| `api/main.py` | App setup, CORS, middleware | ✅ |
| `api/auth.py` | JWT (HS256, xavi.app) | ✅ |
| `api/Dockerfile` | Python 3.11 + ffmpeg | ✅ |
| `api/routes/srnn.py` | 22 — shuffle, connections, playlists | ✅ |
| `api/routes/manager.py` | 12 — db browser, tracks, fleet | ✅ |
| `api/routes/enrichment.py` | 14 — batch, queue, discovery | ✅ |
| `api/routes/duotronic.py` | 7 — search, encode, witness | ✅ |
| `api/routes/brain.py` | 8 — chat, history, play | ✅ |
| `api/routes/stream.py` | 3 — music, SSE, image proxy | ✅ |
| `api/routes/meta_objects.py` | 5 — get, extract, search | ✅ |

### CMS SPA Panels (in live/)

| Page | Embed | Status |
|------|-------|--------|
| `/manager/agents/` | Agno (8040) | ✅ |
| `/manager/video/` | Hovod Dashboard (3003) | ✅ |
| `/manager/context_graph/` | TrustGraph (8870) | ✅ |
| `/manager/social/` | Social media | ✅ |
| + 17 more panels | Various | ✅ |

### Federation

| File | Purpose | Status |
|------|---------|--------|
| `federation/coordinator.py` | Work coordination | ✅ |
| `federation/mesh.py` | Network mesh | ✅ |
| `federation/redis_bus.py` | Redis state bus | ✅ |
| `federation/replicator.py` | Data replication | ✅ |
| `federation/s3_client.py` | S3/MinIO client | ✅ |
| `federation/ssh_tunnel_manager.py` | SSH tunnels | ✅ |
| `federation/bootstrap-node.sh` | Node provisioner | ✅ |
