from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .config import Settings
from .runtime_kernel import RuntimeKernel
from .repo_mcp import XaviRepoTools, repo_resources, repo_tool_manifest
from .ops_mcp import XaviOpsTools, ops_tool_manifest


class McpCallRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


def _require_mcp_key(
    settings: Settings,
    authorization: str | None,
    x_xavi_mcp_key: str | None,
) -> None:
    if not settings.xavi_mcp_enabled:
        raise HTTPException(status_code=404, detail="xavi-runtime MCP is disabled")

    if not settings.xavi_mcp_api_key:
        raise HTTPException(status_code=503, detail="XAVI_MCP_API_KEY is not configured")

    expected = f"Bearer {settings.xavi_mcp_api_key}"
    if authorization == expected or x_xavi_mcp_key == settings.xavi_mcp_api_key:
        return

    raise HTTPException(status_code=401, detail="missing or invalid xavi-runtime MCP credential")


def _safe_limit(args: dict[str, Any], default: int = 20) -> int:
    try:
        value = int(args.get("limit", default))
    except Exception:
        value = default
    return max(1, min(value, 100))


def _tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "runtime.health",
            "description": "Return runtime health, corpus identity, profile status, model registry, module registry, and formal observer availability.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.models",
            "description": "List configured model providers and defaults.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.modules",
            "description": "List registered runtime modules and capabilities.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.memory",
            "description": "Read recent memory cell records.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.witnesses",
            "description": "Read recent NLA and generic evidence witnesses.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.evidence_witnesses",
            "description": "Read recent evidence witness envelopes.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.claims",
            "description": "Read recent evidence claims.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.audit",
            "description": "Read recent audit events.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.corpus",
            "description": "Inspect active mounted corpus metadata.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.policy",
            "description": "Explain active policy configuration.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.formal_status",
            "description": "Read Lean/Lake/TLA+ observer availability.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.run_inference",
            "description": "Run a prompt through the SRNN evidence pipeline. Restricted to respond/observe modes.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["prompt"],
                "properties": {
                    "prompt": {"type": "string", "minLength": 1},
                    "steps": {"type": "integer", "minimum": 1, "maximum": 16, "default": 1},
                    "requested_action": {"type": "string", "enum": ["respond", "observe"], "default": "respond"},
                    "model_name": {"type": ["string", "null"]},
                    "evidence_quality": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.72},
                },
            },
        },
        *repo_tool_manifest(),
        *ops_tool_manifest(),
    ]

def _resources() -> list[dict[str, str]]:
    return [
        {"uri": "xavi-runtime://health", "name": "Runtime health"},
        {"uri": "xavi-runtime://models", "name": "Model registry"},
        {"uri": "xavi-runtime://modules", "name": "Module registry"},
        {"uri": "xavi-runtime://memory", "name": "Recent memory"},
        {"uri": "xavi-runtime://witnesses", "name": "Recent witnesses"},
        {"uri": "xavi-runtime://claims", "name": "Recent claims"},
        {"uri": "xavi-runtime://audit", "name": "Recent audit events"},
        {"uri": "xavi-runtime://corpus", "name": "Corpus inspection"},
        {"uri": "xavi-runtime://policy", "name": "Policy explanation"},
        {"uri": "xavi-runtime://formal", "name": "Formal observer status"},
        *repo_resources(),
    ]


async def _call_tool(kernel: RuntimeKernel, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool == "runtime.health":
        kernel.migrate()
        return kernel.health()

    if tool == "runtime.models":
        return {"items": kernel.model_provider.registry.list_models()}

    if tool == "runtime.modules":
        return kernel.modules.capability_report()

    if tool == "runtime.memory":
        return {"items": kernel.store.fetch_recent("memory_cells", _safe_limit(args))}

    if tool == "runtime.witnesses":
        limit = _safe_limit(args)
        return {
            "items": kernel.store.fetch_recent("nla_activation_witnesses", limit),
            "generic": kernel.store.fetch_recent("evidence_witnesses", limit),
        }

    if tool == "runtime.evidence_witnesses":
        return {"items": kernel.store.fetch_recent("evidence_witnesses", _safe_limit(args))}

    if tool == "runtime.claims":
        return {"items": kernel.store.fetch_recent("evidence_claims", _safe_limit(args))}

    if tool == "runtime.audit":
        return {"items": kernel.store.fetch_recent("audit_events", _safe_limit(args))}

    if tool == "runtime.corpus":
        return kernel.corpus_manager.inspect()

    if tool == "runtime.policy":
        return kernel.policy.explain()

    if tool == "runtime.formal_status":
        return kernel.formal.status()

    if tool == "runtime.run_inference":
        prompt = str(args.get("prompt", "")).strip()
        if not prompt:
            raise HTTPException(status_code=422, detail="runtime.run_inference requires args.prompt")

        requested_action = str(args.get("requested_action", "respond"))
        if requested_action not in {"respond", "observe"}:
            raise HTTPException(
                status_code=403,
                detail="MCP runtime.run_inference is restricted to requested_action respond/observe",
            )

        try:
            return await kernel.run_cognition(
                prompt=prompt,
                steps=max(1, min(int(args.get("steps", 1)), 16)),
                requested_action=requested_action,
                model_name=args.get("model_name"),
                evidence_quality=float(args.get("evidence_quality", 0.72)),
            )
        except RuntimeError as exc:
            message = str(exc)
            if "timeout" in message:
                raise HTTPException(status_code=504, detail={"error": "model_provider_timeout", "message": message}) from exc
            if "ollama_" in message or "llama_cpp_" in message:
                raise HTTPException(status_code=502, detail={"error": "model_provider_error", "message": message}) from exc
            raise

    if tool.startswith("repo."):
        return await XaviRepoTools(kernel.settings).call(tool, args)

    if tool.startswith("ops."):
        return await XaviOpsTools(kernel.settings).call(tool, args)

    raise HTTPException(status_code=404, detail=f"unknown xavi-runtime MCP tool: {tool}")


async def _read_resource(kernel: RuntimeKernel, uri: str) -> dict[str, Any]:
    mapping: dict[str, tuple[str, dict[str, Any]]] = {
        "xavi-runtime://health": ("runtime.health", {}),
        "xavi-runtime://models": ("runtime.models", {}),
        "xavi-runtime://modules": ("runtime.modules", {}),
        "xavi-runtime://memory": ("runtime.memory", {"limit": 20}),
        "xavi-runtime://witnesses": ("runtime.witnesses", {"limit": 20}),
        "xavi-runtime://claims": ("runtime.claims", {"limit": 20}),
        "xavi-runtime://audit": ("runtime.audit", {"limit": 20}),
        "xavi-runtime://corpus": ("runtime.corpus", {}),
        "xavi-runtime://policy": ("runtime.policy", {}),
        "xavi-runtime://formal": ("runtime.formal_status", {}),
    }

    if uri == "xavi-runtime://repo/status":
        return {"uri": uri, "contents": await XaviRepoTools(kernel.settings).call("repo.status", {})}

    if uri == "xavi-runtime://repo/worktrees":
        return {"uri": uri, "contents": await XaviRepoTools(kernel.settings).call("repo.list_worktrees", {})}

    if uri not in mapping:
        raise HTTPException(status_code=404, detail=f"unknown xavi-runtime MCP resource: {uri}")

    tool, args = mapping[uri]
    return {"uri": uri, "contents": await _call_tool(kernel, tool, args)}


def register_xavi_runtime_mcp(app: FastAPI, kernel: RuntimeKernel, settings: Settings) -> None:
    async def mcp_health(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return {
            "status": "ok",
            "app": "xavi-runtime",
            "transport": "http",
            "enabled": settings.xavi_mcp_enabled,
            "tools": len(_tool_manifest()),
            "resources": len(_resources()),
        }

    async def mcp_tools(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return {"app": "xavi-runtime", "tools": _tool_manifest()}

    async def mcp_resources(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return {"app": "xavi-runtime", "resources": _resources()}

    async def mcp_resource_read(
        uri: str = Query(..., min_length=1),
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return await _read_resource(kernel, uri)

    async def mcp_call(
        req: McpCallRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        result = await _call_tool(kernel, req.tool, req.args)
        return {
            "app": "xavi-runtime",
            "request_id": req.request_id,
            "tool": req.tool,
            "result": result,
        }

    for prefix in ("/xavi-runtime/mcp", "/v1/mcp"):
        app.add_api_route(f"{prefix}/health", mcp_health, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/tools", mcp_tools, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/resources", mcp_resources, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/resources/read", mcp_resource_read, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/call", mcp_call, methods=["POST"], tags=["xavi-runtime-mcp"])
