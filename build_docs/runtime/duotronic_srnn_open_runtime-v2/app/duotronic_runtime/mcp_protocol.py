from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from .config import Settings
from .http_mcp import _call_tool, _require_mcp_key, _tool_manifest
from .runtime_kernel import RuntimeKernel


class McpJsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str = Field(..., min_length=1)
    params: dict[str, Any] | None = None


MCP_TEXT_MAX_CHARS = 24_000
MCP_STRUCTURED_MAX_CHARS = 48_000
MCP_STRUCTURED_PREVIEW_CHARS = 8_000


def _authorize(
    settings: Settings,
    authorization: str | None,
    x_xavi_mcp_key: str | None,
    x_api_key: str | None,
) -> None:
    # ChatGPT/App setups may use Authorization: Bearer, x-api-key, or a custom key header.
    _require_mcp_key(settings, authorization, x_xavi_mcp_key or x_api_key)


def _json_safe(value: Any) -> Any:
    """Convert runtime/tool results into JSON-serializable MCP payloads."""
    try:
        return jsonable_encoder(value)
    except Exception:
        return json.loads(json.dumps(value, default=str))


def _json_text(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, indent=indent)


def _clip_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False

    omitted = len(text) - max_chars
    suffix = (
        f"\n\n... [truncated {omitted} chars; "
        "narrow the MCP tool request with limit/filter arguments.]"
    )
    return text[:max_chars].rstrip() + suffix, True


def _jsonrpc_response(payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(_json_safe(payload))


def _jsonrpc_result(request_id: str | int | None, result: Any) -> JSONResponse:
    return _jsonrpc_response({"jsonrpc": "2.0", "id": request_id, "result": result})


def _jsonrpc_error(request_id: str | int | None, code: int, message: str, data: Any = None) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return _jsonrpc_response({"jsonrpc": "2.0", "id": request_id, "error": error})


def _mcp_tool_response(result: Any) -> dict[str, Any]:
    """Build a ChatGPT-safe MCP tools/call response."""
    safe_result = _json_safe(result)
    compact = _json_text(safe_result)
    pretty = _json_text(safe_result, indent=2)
    text, text_truncated = _clip_text(pretty, MCP_TEXT_MAX_CHARS)

    structured_content = safe_result
    structured_truncated = False

    if len(compact) > MCP_STRUCTURED_MAX_CHARS:
        preview, _ = _clip_text(compact, MCP_STRUCTURED_PREVIEW_CHARS)
        structured_content = {
            "truncated": True,
            "reason": "mcp_structured_content_too_large",
            "original_json_chars": len(compact),
            "preview": preview,
        }
        structured_truncated = True

    payload: dict[str, Any] = {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured_content,
        "isError": False,
    }

    if text_truncated or structured_truncated:
        payload["_meta"] = {
            "xaviRuntimeResponseTruncated": True,
            "originalJsonChars": len(compact),
            "textMaxChars": MCP_TEXT_MAX_CHARS,
            "structuredMaxChars": MCP_STRUCTURED_MAX_CHARS,
        }

    return payload


def _mcp_tools() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []

    for item in _tool_manifest():
        name = item.get("name")
        if not name:
            continue

        tools.append(
            {
                "name": name,
                "description": item.get("description", ""),
                "inputSchema": item.get(
                    "input_schema",
                    {"type": "object", "properties": {}, "additionalProperties": True},
                ),
            }
        )

    return tools


def _server_info() -> dict[str, Any]:
    return {
        "name": "xavi-runtime",
        "version": "0.2.0",
        "description": "Duotronic SRNN / Xavi Runtime MCP server with runtime, repo, and ops tools.",
    }


def register_real_mcp_protocol(app: FastAPI, kernel: RuntimeKernel, settings: Settings) -> None:
    async def handle_mcp(
        req: McpJsonRpcRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None, alias="x-api-key"),
    ) -> Response:
        try:
            _authorize(settings, authorization, x_xavi_mcp_key, x_api_key)
        except HTTPException as exc:
            return _jsonrpc_error(req.id, -32001, "Unauthorized", {"status_code": exc.status_code, "detail": exc.detail})

        params = req.params or {}
        method = req.method

        # JSON-RPC notifications have no id and should not produce a normal response.
        if method.startswith("notifications/"):
            return Response(status_code=202)

        if method == "initialize":
            return _jsonrpc_result(
                req.id,
                {
                    "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                    },
                    "serverInfo": _server_info(),
                    "instructions": (
                        "Use tools/list to discover Xavi Runtime tools. "
                        "Use tools/call with a tool name and arguments to operate the runtime, repo worktrees, and bounded ops."
                    ),
                },
            )

        if method == "ping":
            return _jsonrpc_result(req.id, {})

        if method == "tools/list":
            return _jsonrpc_result(req.id, {"tools": _mcp_tools()})

        if method == "tools/call":
            tool_name = str(params.get("name", "")).strip()
            arguments = params.get("arguments") or {}

            if not tool_name:
                return _jsonrpc_error(req.id, -32602, "tools/call requires params.name")

            if not isinstance(arguments, dict):
                return _jsonrpc_error(req.id, -32602, "tools/call params.arguments must be an object")

            try:
                result = await _call_tool(kernel, tool_name, arguments)
            except HTTPException as exc:
                return _jsonrpc_error(
                    req.id,
                    -32000,
                    "Tool call failed",
                    {"status_code": exc.status_code, "detail": exc.detail, "tool": tool_name},
                )
            except Exception as exc:
                return _jsonrpc_error(
                    req.id,
                    -32000,
                    "Tool call failed",
                    {"error": exc.__class__.__name__, "message": str(exc), "tool": tool_name},
                )

            return _jsonrpc_result(req.id, _mcp_tool_response(result))

        if method == "resources/list":
            return _jsonrpc_result(req.id, {"resources": []})

        return _jsonrpc_error(req.id, -32601, f"Method not found: {method}")

    async def mcp_get() -> PlainTextResponse:
        return PlainTextResponse(
            "Xavi Runtime MCP server. POST JSON-RPC here. Supported methods: initialize, tools/list, tools/call, ping."
        )

    # Primary ChatGPT MCP URL.
    app.add_api_route("/mcp", mcp_get, methods=["GET"], include_in_schema=False)
    app.add_api_route("/mcp", handle_mcp, methods=["POST"], include_in_schema=False)

    # Compatibility URL if you already tried the old base path.
    app.add_api_route("/xavi-runtime/mcp", mcp_get, methods=["GET"], include_in_schema=False)
    app.add_api_route("/xavi-runtime/mcp", handle_mcp, methods=["POST"], include_in_schema=False)
