from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from .config import Settings


def ops_tool_manifest() -> list[dict[str, Any]]:
    return [
        {"name": "ops.health", "description": "Check host ops agent health.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.commands", "description": "List available host ops commands.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.git_status", "description": "Read git status, HEAD, and origin/main.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.git_pull", "description": "Pull origin main with fast-forward only.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.git_push", "description": "Push local main to origin.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.runtime_tests", "description": "Run runtime pytest suite.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.runtime_ps", "description": "Show runtime podman containers.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.runtime_logs", "description": "Read duotronic-runtime logs.", "read_only": True, "input_schema": {"type": "object", "properties": {"tail": {"type": "integer", "default": 120}}}},
        {"name": "ops.runtime_health", "description": "Check local and public runtime health.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.runtime_restart", "description": "Restart the runtime container.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.runtime_rebuild", "description": "Rebuild and restart the runtime container.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.runtime_rebuild_models", "description": "Rebuild and restart runtime with models profile.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_server_snapshot", "description": "Read runtime v3 containers, ports, service state, runtime health, and Ollama proxy state.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_ollama_ports", "description": "Probe runtime v3 host Ollama/proxy ports with /api/tags.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_ollama_proxy_status", "description": "Read runtime v3 Ollama proxy status endpoint.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_ollama_proxy_tags", "description": "Read runtime v3 Ollama proxy aggregate model tags.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_model_route_probe", "description": "Probe which runtime v3 Ollama proxy route would handle a model, when supported by the proxy.", "read_only": True, "input_schema": {"type": "object", "properties": {"model": {"type": "string", "default": "qwen2.5-coder:3b"}}}},
        {"name": "ops.v3_runtime_env", "description": "Read sanitized runtime v3 Ollama/model env configuration.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_apply_vscode_model_aliases", "description": "Apply stable runtime v3 VS Code model aliases to config/models.json.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_apply_text_replace", "description": "Safely replace text in an allowlisted file under runtime v3, with backup.", "read_only": False, "input_schema": {"type": "object", "required": ["path", "old", "new"], "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}, "expected_occurrences": {"type": "integer"}, "count": {"type": "integer", "default": 1}, "dry_run": {"type": "boolean", "default": false}}}},
        {"name": "ops.v3_rebuild_runtime_image", "description": "Build the runtime v3 container image only.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_restart_runtime_only", "description": "Recreate only the runtime v3 container using the v3 run spec.", "read_only": False, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_git_status", "description": "Show git status for the Duotronics repo.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.v3_git_diff", "description": "Show git diff for runtime v3 changes.", "read_only": True, "input_schema": {"type": "object", "properties": {}}},
        {"name": "ops.allowed_command", "description": "Run a named allowlisted host command.", "read_only": False, "input_schema": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}},
    ]


class XaviOpsTools:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _require_enabled(self) -> None:
        if not self.settings.xavi_ops_enabled:
            raise HTTPException(status_code=404, detail="ops MCP tools are disabled")
        if not self.settings.xavi_ops_api_key:
            raise HTTPException(status_code=503, detail="XAVI_OPS_API_KEY is not configured")

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self._require_enabled()

        headers = {"authorization": f"Bearer {self.settings.xavi_ops_api_key}"}
        base = self.settings.xavi_ops_url.rstrip("/")

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=1200.0, write=30.0, pool=5.0)) as client:
                if tool == "ops.health":
                    response = await client.get(f"{base}/health", headers=headers)
                elif tool == "ops.commands":
                    response = await client.get(f"{base}/commands", headers=headers)
                else:
                    response = await client.post(f"{base}/call", headers=headers, json={"command": tool, "args": args})
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"ops agent transport error: {exc.__class__.__name__}") from exc
