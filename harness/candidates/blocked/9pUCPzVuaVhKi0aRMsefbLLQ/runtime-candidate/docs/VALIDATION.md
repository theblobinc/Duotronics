# Validation performed for this packaged example

Local checks performed during packaging:

```bash
python -m compileall app
PYTHONPATH=app python -m pytest -q tests
```

Result: 3 unit tests passed.

Not performed in this environment:

- Podman compose startup
- PostgreSQL container migration smoke test
- Milvus profile startup
- Ollama/llama.cpp model inference
- MCP client integration through VS Code

Those require a host with Podman and network/image access.
