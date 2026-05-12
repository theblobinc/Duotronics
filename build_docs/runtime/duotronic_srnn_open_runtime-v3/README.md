# Duotronic SRNN Runtime Host

A Podman-first, evidence-governed runtime host for Duotronic/SRNN corpora, WG-RNN cognition, model providers, formal truth observers, MCP tools, and gated self-development.

This package upgrades the original open runtime from a small reference sandbox into a fuller runtime scaffold:

- version-aware corpus loading through a Corpus ABI
- PostgreSQL witness/evidence store
- explicit Evidence Kernel and Non-Collapse Engine
- WG-RNN memory updates and NLA activation witnesses
- model gateway support for local echo, Ollama, and llama.cpp
- module registry for Ollama, llama.cpp, TLA+, Lean, Stable Diffusion, transformers.js, LibreChat, and future observers
- MCP stdio server for VS Code/custom agents
- FastAPI control plane and static browser UI
- formal observer wrappers for Lean and TLA+/TLC
- self-development planning that creates candidate work only; merge/deploy remain approval-gated
- Podman Compose profiles for core, models, vector, formal, media, UI, and MCP

## Important status

This is a packaged runtime scaffold, not a certification that every optional service is installed or production-approved. The core Python runtime and unit tests pass locally. Optional profiles require the relevant images, models, GPU drivers, and host resources.

## Quick start

```bash
cp .env.example .env
podman compose --env-file .env up --build postgres redis minio runtime
```

Open:

- UI: <http://127.0.0.1:8080>
- API health: <http://127.0.0.1:8080/health>
- OpenAPI: <http://127.0.0.1:8080/docs>

Run a cognition cycle:

```bash
curl -s -X POST http://127.0.0.1:8080/v1/run \
  -H 'content-type: application/json' \
  -d '{"prompt":"Explain whether a model output may become memory","steps":2,"requested_action":"memory_write"}' | python -m json.tool
```

Inspect the corpus mounted under `./corpus`:

```bash
curl -s http://127.0.0.1:8080/v1/corpus/inspect | python -m json.tool
curl -s http://127.0.0.1:8080/v1/corpus/plan | python -m json.tool
```

## Profiles

```bash
# MCP stdio service for local agents
podman compose --profile mcp --env-file .env up --build mcp

# Add local model providers
podman compose --profile models --env-file .env up --build

# Add Milvus vector stack
podman compose --profile vector --env-file .env up --build

# Add formal observer containers
podman compose --profile formal --env-file .env up --build

# Add media generation surface
podman compose --profile media --env-file .env up --build

# Add LibreChat UI surface
podman compose --profile ui --env-file .env up --build
```

## MCP usage

`.vscode/mcp.example.json` launches the stdio MCP server through Podman. Tools include:

- `runtime_health`
- `run_cognition`
- `submit_claim`
- `list_witnesses`
- `query_memory`
- `register_model`
- `module_capability_report`
- `module_health`
- `corpus_inspect`
- `corpus_ingest`
- `corpus_build_plan`
- `policy_explain`
- `formal_status`
- `self_development_plan`

## Corpus ABI

Mount any extracted corpus under `./corpus`. A manifest is recommended:

```json
{
  "corpus_id": "duotronic-example-corpus",
  "version": "v1.example",
  "schema_version": "corpus-abi-v1",
  "entrypoints": {
    "schemas": "schemas/",
    "policies": "policies/",
    "formal": "formal/",
    "conformance": "conformance/"
  }
}
```

If no manifest exists, the runtime derives a corpus reference from file hashes and records a warning instead of failing.

## Runtime principle

Models, encoders, tools, proof checkers, media generators, and UI surfaces are replaceable modules. The Evidence Kernel, policy gate, replay/corpus references, and Non-Collapse Engine are not bypassable.

## Validation

```bash
python -m pytest -q
```

Last packaged validation: `8 passed in 3.49s`.
