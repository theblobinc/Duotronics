# Architecture

This reference runtime mirrors the SRNN/Duotronic shape without requiring the private deployment:

```text
Prompt / model event
  -> model provider registry
  -> WG-RNN recurrent memory shim
  -> activation capture
  -> NLA activation verbalizer
  -> NLA activation reconstructor
  -> fidelity gate
  -> policy gate
  -> PostgreSQL witness store
  -> UI / CLI / MCP / audit surfaces
```

## Services

- `runtime`: FastAPI app, static UI, CLI, and runtime logic.
- `postgres`: canonical transactional store. No SQLite is used.
- `mcp`: same image, stdio server mode for VS Code / MCP clients.
- `ollama`: optional local model server.
- `llama-cpp`: optional OpenAI-compatible llama.cpp server.
- `milvus`: optional vector DB stack with etcd and MinIO.

## Why PostgreSQL

The corpus treats witness transitions, policy decisions, replay identity, and memory cell lifecycle as transactional state. PostgreSQL gives us stable migrations, JSONB evidence payloads, constraints, and audit rows without relying on local file DB semantics.

## Milvus boundary

Milvus is optional because the witness contract should work before vector search is available. When enabled, witness vectors can be mirrored into Milvus for semantic recall; PostgreSQL remains canonical.

## Model boundary

Model output is a source observation, not truth. Ollama and llama.cpp providers are interchangeable backends behind the same model registry shape.
