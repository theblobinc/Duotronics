from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from .config import Settings
from .http_mcp import _call_tool, _read_resource, _require_mcp_key, _resources, _tool_manifest
from .runtime_kernel import RuntimeKernel
from .autonomy_stack import sanitize_training_value
from .conversation_identity import resolve as resolve_conversation, schema_properties as conversation_schema_properties, strip as strip_conversation_args


_AUTO_CAPTURE_EXACT = {
    # Operational liveness/inventory probes are not training events.
    "runtime.health",
    "runtime.models",
    "runtime.modules",
    "runtime.session_append",
    "runtime.session_index",
    "runtime.session_search",
    "runtime.session_find",
    "runtime.session_tail",
    "runtime.session_summary",
    "runtime.session_verify",
    "runtime.transcript_ingest",
    "runtime.transcript_search",
}


def _capture_tool(tool_name: str) -> bool:
    return tool_name not in _AUTO_CAPTURE_EXACT and not tool_name.startswith("runtime.autonomy_")


def _mcp_session_context(request: Request) -> dict[str, str]:
    headers = request.headers
    explicit = headers.get("x-xavi-session-id") or headers.get("x-mcp-session-id") or headers.get("mcp-session-id")
    agent_id = headers.get("x-xavi-agent-id") or headers.get("x-agent-id") or "mcp-client"
    device = headers.get("x-xavi-device-id") or headers.get("x-device-id") or headers.get("user-agent") or "unknown-device"
    if explicit:
        session_id = explicit.strip()
    else:
        seed = json.dumps({"agent": agent_id, "device": device, "client": headers.get("user-agent", "")}, sort_keys=True)
        session_id = "runtime-mcp-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return {"session_id": session_id[:160], "agent_id": agent_id[:120], "device_digest": "sha256:" + hashlib.sha256(device.encode("utf-8")).hexdigest()}


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

        schema = item.get(
            "input_schema",
            {"type": "object", "properties": {}, "additionalProperties": True},
        )
        if isinstance(schema, dict) and schema.get("type") == "object":
            schema = dict(schema)
            properties = dict(schema.get("properties") or {})
            for identity_name, identity_schema in conversation_schema_properties().items():
                properties.setdefault(identity_name, identity_schema)
            schema["properties"] = properties
        tools.append(
            {
                "name": name,
                "description": item.get("description", ""),
                "inputSchema": schema,
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
    async def _handle_mcp_inner(
        req: McpJsonRpcRequest,
        request: Request,
        authorization: str | None = None,
        x_xavi_mcp_key: str | None = None,
        x_api_key: str | None = None,
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
                        "Use resources/list and resources/read for runtime and Concrete CMS skill resources. "
                        "Use tools/call with a tool name and arguments to operate the runtime, repo worktrees, and bounded ops. "
                        "For every tool call in one chat, provide the same durable conversation_id and conversation_source. Prefer a real source-native id when the client exposes one; otherwise generate one stable UUID-based id once for that chat and keep reusing it. Never reuse one conversation_id across unrelated chats. "
                        "When transcript access exists, use runtime.transcript_ingest under the same conversation identity for real user/assistant turns; never fabricate unseen transcript content. "
                        "At the beginning of substantive work, inspect session.inbox and delegation.inbox, acknowledge addressed messages when handled, and consult any _collaboration peer-awareness/task-backlog context before choosing work. "
                        "Use session.send_message for peer handoffs and delegation.assign for suitable session/WG-RNN work instead of duplicating active peer tasks; use task.claim_next for unclaimed backlog work."
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

            context = _mcp_session_context(request)
            conversation = resolve_conversation(request.headers, arguments, context["session_id"])
            if tool_name in {"runtime.transcript_ingest", "runtime.transcript_search"}:
                arguments = dict(arguments)
                arguments["session_id"] = conversation["conversation_id"]
                if tool_name == "runtime.transcript_ingest":
                    metadata = dict(arguments.get("metadata") or {}) if isinstance(arguments.get("metadata"), dict) else {}
                    metadata.setdefault("conversation_id", conversation["conversation_id"])
                    metadata.setdefault("conversation_source", conversation["conversation_source"])
                    if conversation.get("source_conversation_id"):
                        metadata.setdefault("source_conversation_id", conversation["source_conversation_id"])
                    if conversation.get("continued_from_conversation_id"):
                        metadata.setdefault("continued_from_conversation_id", conversation["continued_from_conversation_id"])
                    arguments["metadata"] = metadata
            arguments = strip_conversation_args(arguments)
            if tool_name.startswith(("session.", "delegation.", "worker.", "task.")):
                # Session/delegation authority is transport-bound. Never trust caller-supplied
                # sender identity for cross-agent messaging or delegated work.
                arguments = dict(arguments)
                arguments["session_id"] = context["session_id"]
                arguments["agent_id"] = context["agent_id"]
                arguments["client_name"] = "native-mcp"
            ledger_session_id = conversation.get("conversation_id") or context["session_id"]
            capture = _capture_tool(tool_name)
            started_ms = int(time.time() * 1000)
            start_event = None
            if capture:
                start_event = kernel.autonomy.record_event(
                    session_id=ledger_session_id,
                    event_type="mcp_call_start",
                    actor=context["agent_id"],
                    content={
                        "tool_name": tool_name,
                        "request_id": req.id,
                        "arguments": sanitize_training_value(arguments),
                        "arguments_digest": "sha256:" + hashlib.sha256(json.dumps(arguments, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
                        "device_digest": context["device_digest"],
                        **conversation,
                        "transport": "native-mcp-jsonrpc",
                    },
                    tags=["mcp", "tool-call", tool_name],
                )

            try:
                result = await _call_tool(kernel, tool_name, arguments)
                if tool_name not in {"task.awareness", "runtime.health", "runtime.models", "runtime.modules"}:
                    try:
                        from .project_tasks import ProjectTaskService
                        kernel.migrate()
                        collaboration = ProjectTaskService(kernel.store).compact_awareness({
                            "project_key": arguments.get("project_key") or "xavi.app-backend",
                            "session_id": context["session_id"],
                            "agent_id": context["agent_id"],
                            "limit": 12,
                        })
                        if isinstance(result, dict):
                            result = dict(result)
                            result["_collaboration"] = collaboration
                    except Exception:
                        # Awareness is advisory context; never turn a successful primary
                        # tool call into a failure because the awareness projection failed.
                        pass
            except HTTPException as exc:
                if capture and start_event is not None:
                    error_event = kernel.autonomy.record_event(
                        session_id=ledger_session_id,
                        event_type="mcp_call_error",
                        actor="xavi-runtime",
                        content={
                            "tool_name": tool_name,
                            "request_id": req.id,
                            "status_code": exc.status_code,
                            "detail": sanitize_training_value(exc.detail),
                            "duration_ms": int(time.time() * 1000) - started_ms,
                            **conversation,
                        },
                        tags=["mcp", "tool-error", tool_name],
                    )
                    try:
                        kernel.autonomy.build_trajectory(
                            session_id=ledger_session_id,
                            start_sequence=int(start_event["sequence"]),
                            end_sequence=int(error_event["sequence"]),
                            outcome={"success": False, "score": 0.0, "error": "HTTPException"},
                            evaluator="native-mcp-boundary",
                            learn=True,
                        )
                    except Exception:
                        pass
                return _jsonrpc_error(
                    req.id,
                    -32000,
                    "Tool call failed",
                    {"status_code": exc.status_code, "detail": exc.detail, "tool": tool_name},
                )
            except Exception as exc:
                if capture and start_event is not None:
                    error_event = kernel.autonomy.record_event(
                        session_id=ledger_session_id,
                        event_type="mcp_call_error",
                        actor="xavi-runtime",
                        content={
                            "tool_name": tool_name,
                            "request_id": req.id,
                            "error": exc.__class__.__name__,
                            "message": sanitize_training_value(str(exc)),
                            "duration_ms": int(time.time() * 1000) - started_ms,
                        },
                        tags=["mcp", "tool-error", tool_name],
                    )
                    try:
                        kernel.autonomy.build_trajectory(
                            session_id=ledger_session_id,
                            start_sequence=int(start_event["sequence"]),
                            end_sequence=int(error_event["sequence"]),
                            outcome={"success": False, "score": 0.0, "error": exc.__class__.__name__},
                            evaluator="native-mcp-boundary",
                            learn=True,
                        )
                    except Exception:
                        pass
                return _jsonrpc_error(
                    req.id,
                    -32000,
                    "Tool call failed",
                    {"error": exc.__class__.__name__, "message": str(exc), "tool": tool_name},
                )

            if capture and start_event is not None:
                result_event = kernel.autonomy.record_event(
                    session_id=ledger_session_id,
                    event_type="mcp_call_result",
                    actor="xavi-runtime",
                    content={
                        "tool_name": tool_name,
                        "request_id": req.id,
                        "result": sanitize_training_value(result),
                        "result_digest": "sha256:" + hashlib.sha256(json.dumps(result, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
                        "duration_ms": int(time.time() * 1000) - started_ms,
                        **conversation,
                    },
                    tags=["mcp", "tool-result", tool_name],
                )
                try:
                    kernel.autonomy.build_trajectory(
                        session_id=ledger_session_id,
                        start_sequence=int(start_event["sequence"]),
                        end_sequence=int(result_event["sequence"]),
                        outcome={"success": True, "score": 1.0},
                        evaluator="native-mcp-boundary",
                        learn=True,
                    )
                except Exception:
                    pass

            text = json.dumps({"_conversation": conversation, "result": result}, indent=2, sort_keys=True, default=str)
            return _jsonrpc_result(
                req.id,
                {
                    "content": [{"type": "text", "text": text}],
                    "structuredContent": result,
                    "isError": False,
                },
            )

        if method == "resources/list":
            resources = [
                {
                    "uri": item["uri"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "mimeType": item.get("mimeType", "application/json"),
                }
                for item in _resources(kernel)
            ]
            return _jsonrpc_result(req.id, {"resources": resources})

        if method == "resources/read":
            uri = str(params.get("uri", "")).strip()
            if not uri:
                return _jsonrpc_error(req.id, -32602, "resources/read requires params.uri")
            try:
                resource = await _read_resource(kernel, uri)
            except HTTPException as exc:
                return _jsonrpc_error(req.id, -32002, "Resource read failed", {"status_code": exc.status_code, "detail": exc.detail, "uri": uri})
            contents = resource.get("contents")
            mime_type = str(resource.get("mimeType") or "application/json")
            text = contents if isinstance(contents, str) else json.dumps(contents, indent=2, sort_keys=True, default=str)
            return _jsonrpc_result(req.id, {"contents": [{"uri": uri, "mimeType": mime_type, "text": text}]})

        return _jsonrpc_error(req.id, -32601, f"Method not found: {method}")

    async def handle_mcp(
        req: McpJsonRpcRequest,
        request: Request,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None, alias="x-api-key"),
    ) -> Response:
        # Native MCP dispatch performs synchronous DB/WG-RNN/autonomy work in
        # addition to async provider calls. Isolate the whole request from the
        # Uvicorn event loop so /health remains responsive under MCP load.
        return await asyncio.to_thread(
            lambda: asyncio.run(
                _handle_mcp_inner(
                    req,
                    request,
                    authorization,
                    x_xavi_mcp_key,
                    x_api_key,
                )
            )
        )

    async def mcp_get() -> PlainTextResponse:
        return PlainTextResponse(
            "Xavi Runtime MCP server. POST JSON-RPC here. Supported methods: initialize, tools/list, tools/call, resources/list, resources/read, ping."
        )

    # Primary ChatGPT MCP URL.
    app.add_api_route("/mcp", mcp_get, methods=["GET"], include_in_schema=False)
    app.add_api_route("/mcp", handle_mcp, methods=["POST"], include_in_schema=False)

    # Compatibility URL if you already tried the old base path.
    app.add_api_route("/xavi-runtime/mcp", mcp_get, methods=["GET"], include_in_schema=False)
    app.add_api_route("/xavi-runtime/mcp", handle_mcp, methods=["POST"], include_in_schema=False)
