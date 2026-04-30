# Duotronic Policy Shield Guide v1 8 — v1.6 upgraded carry-forward

**Status:** upgraded carry-forward draft  
**Supersedes / carries forward:** `refs/duotronic_policy_shield_guide_v1_8.md` from v1.5 Draft 2  
**Version:** v1.6-draft-1 compatibility rewrite  
**Document kind:** v1.5 coverage-preserving Markdown document upgraded to the v1.6 backend and mathematical canon

This file is intentionally retained so the v1.6 corpus does not lose any v1.5 Draft 2 document coverage. Its original scope remains active unless a v1.6 owning document explicitly supersedes it.

## v1.6 active status

Policy Shield now gates code execution, proof acceptance, conjecture promotion, external mathematical source ingestion, runtime task delegation, multimodal ingestion, Minecraft action tools, and language-runtime bridges.

## v1.6 backend binding

> **Status tag:** normative unless this file explicitly marks a section as reference or research.

This v1.6 upgrade binds the carried-forward v1.5 Draft 2 concern to the new SRNN backend direction:

1. **Canonical transactional authority:** PostgreSQL-compatible durable store, with DBP v2 object envelopes for portable replay.
2. **Semantic and vector retrieval:** Milvus-compatible vector index, used only for retrieval and ranking, not as durable truth.
3. **Ephemeral coordination:** Redis-compatible coordination, cache, pub/sub, queue hints, and meta-object exchange; no canonical truth may depend solely on Redis.
4. **Transition runtime:** Python/FastAPI remains the active reference implementation surface during migration.
5. **Final control-plane candidate:** Rust remains the major final-runtime/control-plane candidate and must be treated as a target-neutral authority boundary.
6. **Symbolic specialist runtime:** Lisp/SBCL is admitted through a JSON-RPC subprocess bridge with circuit breaker, deterministic input/output envelopes, and parity fixtures.
7. **Mathematical kernel runtime:** Julia is admitted as an isolated math-kernel surface; it must not own witness authority, policy authority, or durable canonical identity.
8. **Interpreter runtime:** Python, Julia, and Lisp execution results enter the corpus as `InterpreterRunWitness` objects and are never accepted as proof merely because code ran.
9. **Legacy role:** PHP remains transitional frontend/proxy glue only and may not own new backend contracts, canonical writes, worker orchestration, or runtime control.

## v1.6 mathematical canon binding

This file now participates in the v1.6 Mathematical Canon. The active rule is:

```text
mathematical expression / object / proof / computation / observation
-> domain profile
-> validation
-> canonical object identity
-> theorem/conjecture/computation status witness
-> bridge and preservation claims
-> interpreter or proof-checker witness where applicable
-> policy gate
-> replay record
```

A witness may cover any mathematical area, but coverage is not truth. The witness records domain, object identity, claim status, evidence, proof references, computation traces, and replay constraints.

## v1.6 Langlands integration binding

The Langlands integration is no longer a side profile. It is a first-class domain of the Mathematical Canon. Objects such as number fields, local fields, adeles, ideles, reductive groups, dual groups, automorphic representations, Galois representations, L-functions, Euler factors, Hecke eigenpackets, trace formula artifacts, sheaf-theoretic objects, and functorial transfer candidates must be represented through the same canonical object and witness gates as every other mathematical domain.

Unproved Langlands conjectures remain `conjectural`. The corpus may canonize their representation, dependencies, evidence, and computational witnesses; it must not mark open conjectures as theorems without a proof witness accepted by the configured proof authority.

## v1.6 SRNN runtime binding

This file also binds to the SRNN runtime updates reviewed for 2026-04-30:

1. Temporal meta objects are carried inside task queue witness data.
2. Oracle results may persist `witness_event_id` back into job success records.
3. Structured identity oracle adapters close the queue-to-witness loop for already-structured payloads without requiring heavyweight ML models.
4. Multimodal witness ingestion supports video, audio, image, CV, sensor, and fused payloads through strict schema validation and temporal delta enrichment.
5. Minecraft/MCP action tools and external perception ingestion are policy-gated action or DB-write surfaces, not uncontrolled authority.
6. Video, object-track, visual-action, audio-segment, sound-event, speech-transcript, speech-synthesis, world-state, agent-action, projection, oracle-truth, and cross-modal lanes are recognized witness families.

## Migration requirements

A runtime, harness, or documentation generator that used the v1.5 version of this file must now record:

1. v1.5 source document path;
2. v1.6 replacement document path;
3. backend binding decision;
4. schema or object IDs touched;
5. replay impact;
6. migration fixtures;
7. policy decision for runtime use;
8. whether the object is math-domain, runtime-domain, governance-domain, or research-domain.

## Backward compatibility

Historical v1.5 references remain valid for replay. New writes must prefer v1.6 object names and backend envelopes. A v1.5 object may be read in compatibility mode if it is wrapped in a `CorpusMigrationWitness` and its authority scope is pinned.
