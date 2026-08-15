# SRNN Server Source Review Integration — 2026-04-30

**Status:** reference with normative incorporation points  
**Scope:** Latest observed SRNN backend changes that must be documented in v1.6 Draft 2.

## 1. Backend architecture decision

v1.6 follows the SRNN architecture decision:

- Python/FastAPI is the current transition implementation.
- Rust remains a major final runtime/control-plane candidate.
- Lisp/SBCL is admitted as a symbolic specialist through a JSON-RPC subprocess bridge with circuit breaker.
- Julia is admitted as an isolated math-kernel surface.
- PHP is transitional and must not own final backend authority.
- PostgreSQL is the planned canonical transactional store.
- Milvus is the vector/semantic index.
- Redis is ephemeral coordination/cache/pubsub/meta-object exchange.
- SQLite is legacy and must not appear in new code paths.

## 2. Identity oracle adapters

The v1.6 corpus documents identity oracle adapters for structured temporal witness payloads. These adapters close the queue-to-witness loop without requiring heavyweight ML models. They accept already-structured payloads from MCP tools, sidecars, or external workers and persist them through the WG-RNN witness services.

Recognized adapters include world state, agent action, reward outcome, video frame, object tracking, optical flow, temporal action, audio segment, music feature, sound event, speech transcript, speech synthesis, projection, prediction error, cross-modal binding, audio-visual sync, speech-action binding, and oracle consensus.

## 3. Multimodal ingest service

The v1.6 corpus documents the multimodal ingest service as a backend ingestion surface for RTSP/WebRTC/CV/audio workers. It validates frame witness payloads, computes temporal deltas, and forwards normalized witness frames to MCP `minecraft_ingest_multimodal_witness`.

Required payload families:

- video frame;
- object track;
- motion field;
- temporal action;
- audio segment;
- sound event;
- speech transcript;
- speech synthesis;
- world state;
- agent action;
- projection;
- oracle truth;
- cross-modal binding.

## 4. Minecraft MCP and action tools

The corpus recognizes Minecraft bridge tools for collect, attack, follow, stop follow, look-at, and multimodal witness ingest. All action tools are external-action or DB-write surfaces and must remain policy-gated.

## 5. Task queue witness IDs

The corpus now requires job workers to copy witness event IDs from oracle results into job success records when the oracle result payload supplies `witness_event_id`. The default job input payload must also carry loop ID, node ID, oracle job ID, input artifact ref, and replay identity ref.

## 6. Temporal meta objects

Temporal meta objects are part of task queue witness data in v1.6. Runtime witnesses must preserve source clock, canonical time, observed time, ingest time, binding confidence, and replay identity.

## 7. Documentation impact

Every relevant v1.5 file has a v1.6 carry-forward wrapper and is subject to the universal backend patch. The specific runtime details above are referenced by the Witness Contract, WG-RNN contract, distributed task delegation contract, schema registry, policy shield, interpreter plan, and conformance fixtures.
