# MCP and agent usage

This project includes a minimal stdio MCP server so agents can operate the runtime through tools instead of raw shell commands.

## Example MCP server entry

```json
{
  "servers": {
    "duotronic-srnn-open-runtime": {
      "command": "podman",
      "args": ["compose", "--env-file", ".env", "run", "--rm", "-i", "mcp"],
      "env": {}
    }
  }
}
```

## Tool list

- `runtime_health`
- `run_cognition`
- `list_witnesses`
- `query_memory`
- `register_model`
- `corpus_ingest`
- `corpus_build_plan`
- `policy_explain`

## Sanitized VS Code agent pattern

Do not store passwords, sudo secrets, tokens, private keys, or production host material in agent files.

Use placeholders:

```yaml
---
name: duotronic-runtime-coder
description: Implementation agent for local Duotronic SRNN Open Runtime work.
argument-hint: coding task, runtime diagnostic, WG-RNN/NLA feature, MCP tool work, or Podman stack task. Secrets must be provided through environment variables or approved secret stores only.
tools:
  - vscode/*
  - execute/*
  - read/*
  - edit/*
  - search/*
  - playwright/*
  - mcp/duotronic-srnn-open-runtime/*
---

# Runtime Coder

Use Podman-first commands, create reviewable patches, run tests, avoid production mutation, and never persist secrets.
```
