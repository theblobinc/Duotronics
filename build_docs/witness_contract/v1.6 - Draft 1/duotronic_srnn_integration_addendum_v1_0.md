# Duotronic SRNN Integration Addendum v1.0

**Status:** reference draft with normative implementation requirements  
**Version:** srnn-integration@v1.0  
**Source review date:** 2026-04-30

---

## 1. Purpose

This addendum records the implementation patterns from the latest `srnn_server` work that must be carried into the v1.6 corpus.

---

## 2. Adopted SRNN patterns

### 2.1 Meta-object recurrence generalization

The `srnn.meta_objects` package is treated as a reference implementation pattern for generalized mathematical witnesses:

1. extract recurring symbolic units from artifacts;
2. canonicalize type names and aliases;
3. persist typed instances with provenance;
4. build recurrence chains and edges;
5. expose symbolic similarity and query APIs;
6. use recurrence as a selection and reasoning signal.

v1.6 generalizes this from media tracks to all mathematical artifacts.

### 2.2 Self-referential selector pattern

The 5-step selector becomes a general pattern for mathematical search and interpreter planning:

```text
active context extraction (Python)
-> symbolic expansion (Lisp)
-> vector candidate scoring (Julia)
-> narrative / structural reranking (Lisp)
-> final blending (Julia or Python fallback)
```

For mathematics, replace tracks with theorem objects, definitions, proof fragments, examples, counterexamples, and Langlands correspondences.

### 2.3 Identity oracle adapter pattern

The identity oracle adapters are adopted as the canonical bridge for already-structured external payloads.

They close the queue-to-witness loop without requiring heavyweight ML models. A structured payload from an MCP tool, sidecar, interpreter, or external worker can become a witness through an identity adapter, preserving `oracle_id`, `witness_event_id`, replay identity, confidence, and source refs.

### 2.4 Multimodal witness ingest pattern

The FastAPI multimodal ingest service is adopted as a general `ingest -> validate -> enrich -> forward -> witness` pattern.

For v1.6 math, analogous ingest services may accept:

1. LaTeX fragments;
2. proof assistant files;
3. notebooks;
4. diagrams;
5. scanned pages;
6. computation outputs;
7. formal database entries;
8. videos or lectures.

The required pattern is schema validation before witness forwarding.

### 2.5 Temporal and cross-modal witness families

v1.6 adopts witness families for:

1. video frame;
2. object track;
3. visual action;
4. audio segment;
5. sound event;
6. speech transcript;
7. speech synthesis;
8. world state;
9. agent action;
10. projection;
11. oracle truth;
12. cross-modal binding.

For mathematics, these become examples of modality-specific evidence, not truth by themselves.

### 2.6 Task queue event-id persistence

The worker pattern that persists `witness_event_id` from oracle results is required for v1.6. Any interpreter or oracle job that creates a witness must return a witness event ID into the job record.

### 2.7 External action policy pattern

Minecraft MCP action tools are treated as the reference pattern for external actions:

1. each action is scoped;
2. approval may be required;
3. action payloads become world/action witnesses;
4. action and outcome records remain separate;
5. external action ability does not imply semantic authority.

The code interpreter must follow the same rule: execution is an action; results are witnesses.

---

## 3. Runtime and storage alignment

v1.6 adopts these implementation-facing roles:

| Layer | Adopted role |
|---|---|
| Python/FastAPI | transition implementation, API, glue, fallbacks |
| Lisp/SBCL | symbolic specialist through JSON-RPC/subprocess bridge |
| Julia | math kernels and numeric graph computation |
| Rust | major candidate for future final control plane |
| PHP | legacy shell only, no final backend authority |
| PostgreSQL | planned canonical transactional store |
| Milvus | semantic/vector index only |
| Redis | ephemeral cache/pubsub/coordination |
| SQLite | legacy compatibility unless explicitly sandboxed |

---

## 4. Requirements for v1.6 implementers

1. No interpreter job may finish without a replay record.
2. No oracle job may drop witness event IDs.
3. No math claim may be promoted from computation alone unless a proof profile allows it.
4. No Lisp or Julia path may block the system without fallback or bypass policy.
5. No external action may execute without a policy gate.
6. No vector similarity result may become canonical identity without a normalizer.
7. No legacy store may be treated as final truth unless migrated to the canonical store.

---

## 5. Migration targets

1. Convert meta-object ontology into `MathematicalDomainRegistry` and `MathObjectTypeRegistry`.
2. Convert recurrence edges into general `MathDependencyEdge` and `MathAnalogyEdge` records.
3. Convert the selector pipeline into `MathSearchPlanner`.
4. Convert identity oracle adapters into `MathStructuredPayloadOracle`.
5. Convert multimodal ingest to `MathArtifactIngestService`.
6. Convert task witness IDs into required fields for all interpreter/oracle jobs.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
