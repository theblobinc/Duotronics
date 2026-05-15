# Open source notes

Before publishing:

1. Replace demo passwords in `.env.example` with generated placeholders if desired.
2. Confirm no real hosts, tokens, passwords, SSH paths, or private customer data are committed.
3. Add your chosen license.
4. Run `python -m compileall app` and `PYTHONPATH=app python -m pytest -q tests`.
5. Test `podman compose --env-file .env up --build postgres runtime` on Linux and Windows.
6. Decide whether Milvus/Ollama/llama.cpp profiles are documented as optional or officially supported.

## Suggested repo positioning

> A Podman-first reference runtime for witness-bearing SRNN/WG-RNN cognition loops, Natural Language Activation witnesses, PostgreSQL persistence, model-provider adapters, and MCP-driven agent operations.
