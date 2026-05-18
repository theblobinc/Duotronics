from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, Header, HTTPException
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


def _authorize(
    settings: Settings,
    authorization: str | None,
    x_xavi_mcp_key: str | None,
    x_api_key: str | None,
) -> None:
    # ChatGPT/App setups may use Authorization: Bearer, x-api-key, or a custom key header.
    _require_mcp_key(settings, authorization, x_xavi_mcp_key or x_api_key)


def _json_compatible(value: Any) -> Any:
    """Return a JSON-compatible copy of values from tool/runtime internals.

    Some runtime stores return datetime/Path-like values. JSON-RPC responses must not
    pass those raw objects through structuredContent, otherwise Starlette's
    JSONResponse fails while rendering an otherwise successful tool result.
    """
    return json.loads(json.dumps(value, default=str))


def _jsonrpc_result(request_id: str | int | None, result: Any) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": _json_compatible(result)})


def _jsonrpc_error(request_id: str | int | None, code: int, message: str, data: Any = None) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = _json_compatible(data)
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "error": error})


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

            text = json.dumps(result, indent=2, sort_keys=True, default=str)
            return _jsonrpc_result(
                req.id,
                {
                    "content": [{"type": "text", "text": text}],
                    "structuredContent": result,
                    "isError": False,
                },
            )

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
