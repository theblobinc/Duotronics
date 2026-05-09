# Duotronic MCP Stdio Principal Policy

**Status:** Research specification draft  
**Version:** stdio-principal-policy@v1.0  
**Document kind:** Security and runtime policy  
**Primary purpose:** Define how stdio MCP sessions map to principals and scopes.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Purpose

Stdio MCP sessions are local process attachments. They may be trusted differently from remote HTTP MCP sessions, but they must not become implicit root authority.

## 2. Principal mapping

A runtime may use an environment variable such as `MCP_STDIO_PRINCIPAL` to choose a default principal when no request principal is active.

Reference mapping:

| Value | Principal type | Scopes |
|---|---|---|
| `local_admin` or `admin` | local_admin | `mcp:read`, `mcp:write`, `mcp:ops-request`, `mcp:admin`, `mcp:audit`, `mcp:minecraft-action` |
| `writer` or `chatgpt_user` | chatgpt_user | `mcp:read`, `mcp:write`, `mcp:ops-request`, `mcp:minecraft-action` |
| `node` or `wg_rnn_node` | wg_rnn_node | `mcp:read`, `mcp:ops-limited` |
| unset | anonymous | `mcp:read` |

## 3. Hard rules

1. Stdio principal selection must be logged in capability diagnostics.
2. Remote transport must not inherit stdio principal defaults.
3. Admin-capable stdio sessions should be limited to local development or explicitly approved operator environments.
4. Any mutating operation still emits audit and policy records.

## 4. Failure behavior

Unknown principal values must fail closed to anonymous or a configured safe default.
