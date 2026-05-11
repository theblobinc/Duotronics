# Runtime Host Architecture

The runtime host is a control plane, not a single monolithic model server.

```text
FastAPI / MCP / CLI
  -> RuntimeKernel
     -> CorpusManager
     -> EvidenceKernel
     -> PolicyEngine
     -> NonCollapseEngine
     -> ModelProvider / ModuleRegistry
     -> WG-RNN + NLA witness factory
     -> Store / PostgreSQL
     -> FormalObserverFleet
     -> SelfDevelopmentController
```

## Non-bypassable path

All serious actions should follow this path:

1. receive request
2. resolve active corpus reference
3. create input digests
4. invoke model/tool/observer module
5. emit witness
6. evaluate policy
7. evaluate non-collapse transition
8. persist witness before effect
9. return result with force/status labels

## Module classes

- `model_provider`: Ollama, llama.cpp, hosted model APIs
- `encoder`: transformers.js, Hugging Face embedding/rerank services
- `formal_observer`: TLA+/TLC, schema validators, replay conformance runners
- `proof_observer`: Lean/Lake proof checks
- `media_generator`: Stable Diffusion or other media tools
- `ui_surface`: LibreChat, web UI, VS Code custom agents
- `control_plane`: SRNN runtime kernel and MCP server

## Self-development law

Self-development may inspect, patch a candidate worktree, run tests, and propose commits. Merge, deploy, production mutation, secret use, and authority promotion require external approval witnesses.
