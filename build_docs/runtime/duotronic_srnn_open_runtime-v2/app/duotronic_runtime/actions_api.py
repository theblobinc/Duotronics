from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from .config import Settings
from .http_mcp import _call_tool, _require_mcp_key
from .runtime_kernel import RuntimeKernel


class ActionsMcpCallRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class WorktreeRequest(BaseModel):
    worktree_id: str
    branch_name: str | None = None
    base_ref: str = "HEAD"


class PatchRequest(BaseModel):
    worktree_id: str
    patch: str


class WorktreeOnlyRequest(BaseModel):
    worktree_id: str


class TestRequest(BaseModel):
    worktree_id: str
    test_command: str = "runtime_pytest"
    timeout_seconds: int = 300


class CommitRequest(BaseModel):
    worktree_id: str
    message: str
    approval_token: str | None = None


class IntegrationRequest(BaseModel):
    worktree_id: str
    message: str
    target_branch: str = "main"


class IntegrateCommitRequest(BaseModel):
    worktree_id: str
    commit: str
    message: str
    approval_token: str
    target_branch: str = "main"
    expected_main_head: str


class OpsLogsRequest(BaseModel):
    tail: int = 120


class AllowedCommandRequest(BaseModel):
    name: str


class RunInferenceRequest(BaseModel):
    prompt: str
    steps: int = 1
    requested_action: str = "respond"
    model_name: str | None = None
    evidence_quality: float = 0.72


def _auth(settings: Settings, authorization: str | None, x_xavi_mcp_key: str | None) -> None:
    _require_mcp_key(settings, authorization, x_xavi_mcp_key)


async def _tool(kernel: RuntimeKernel, tool: str, args: dict[str, Any], request_id: str | None = None) -> dict[str, Any]:
    result = await _call_tool(kernel, tool, args)
    return {
        "app": "xavi-runtime-actions",
        "request_id": request_id,
        "tool": tool,
        "result": result,
    }


def _schema() -> dict[str, Any]:
    empty_body = {
        "required": False,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {},
                }
            }
        },
    }

    worktree_body = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["worktree_id"],
                    "properties": {
                        "worktree_id": {"type": "string"},
                    },
                    "additionalProperties": False,
                }
            }
        },
    }

    response_200 = {
        "description": "Successful response",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "additionalProperties": True,
                }
            }
        },
    }

    def post(path_summary: str, operation_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "post": {
                "summary": path_summary,
                "operationId": operation_id,
                "security": [{"bearerAuth": []}],
                "requestBody": body,
                "responses": {
                    "200": response_200,
                    "401": {"description": "Unauthorized"},
                    "422": {"description": "Validation error"},
                },
            }
        }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Xavi Runtime Actions",
            "version": "0.1.0",
            "description": "Small action-safe interface for Xavi Runtime MCP, repo, and ops tools.",
        },
        "servers": [{"url": "https://dev.xavi.app"}],
        "paths": {
            "/xavi-runtime/actions/health": {
                "get": {
                    "summary": "Check runtime health",
                    "operationId": "runtimeHealth",
                    "security": [{"bearerAuth": []}],
                    "responses": {"200": response_200, "401": {"description": "Unauthorized"}},
                }
            },
            "/xavi-runtime/actions/mcp/call": post(
                "Call one MCP tool by name",
                "mcpCall",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["tool"],
                                "properties": {
                                    "tool": {"type": "string"},
                                    "args": {"type": "object", "additionalProperties": True},
                                    "request_id": {"type": "string"},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/run-inference": post(
                "Run inference through the runtime evidence pipeline",
                "runtimeRunInference",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["prompt"],
                                "properties": {
                                    "prompt": {"type": "string"},
                                    "steps": {"type": "integer", "minimum": 1, "maximum": 16, "default": 1},
                                    "requested_action": {"type": "string", "enum": ["respond", "observe"], "default": "respond"},
                                    "model_name": {"type": "string"},
                                    "evidence_quality": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.72},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/repo/status": post("Read repository status", "repoStatus", empty_body),
            "/xavi-runtime/actions/repo/list-worktrees": post("List repository worktrees", "repoListWorktrees", empty_body),
            "/xavi-runtime/actions/repo/create-worktree": post(
                "Create an isolated worktree",
                "repoCreateWorktree",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["worktree_id", "branch_name"],
                                "properties": {
                                    "worktree_id": {"type": "string"},
                                    "branch_name": {"type": "string"},
                                    "base_ref": {"type": "string", "default": "HEAD"},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/repo/apply-patch": post(
                "Apply a unified diff to a worktree",
                "repoApplyPatch",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["worktree_id", "patch"],
                                "properties": {
                                    "worktree_id": {"type": "string"},
                                    "patch": {"type": "string"},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/repo/diff": post("Show worktree diff", "repoDiff", worktree_body),
            "/xavi-runtime/actions/repo/run-tests": post(
                "Run allowlisted tests in a worktree",
                "repoRunTests",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["worktree_id"],
                                "properties": {
                                    "worktree_id": {"type": "string"},
                                    "test_command": {"type": "string", "default": "runtime_pytest"},
                                    "timeout_seconds": {"type": "integer", "default": 300},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/repo/prepare-commit": post(
                "Prepare commit approval",
                "repoPrepareCommit",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["worktree_id", "message"],
                                "properties": {
                                    "worktree_id": {"type": "string"},
                                    "message": {"type": "string"},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/repo/commit": post(
                "Commit approved worktree changes",
                "repoCommit",
                {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["worktree_id", "message", "approval_token"],
                                "properties": {
                                    "worktree_id": {"type": "string"},
                                    "message": {"type": "string"},
                                    "approval_token": {"type": "string"},
                                },
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/ops/git-status": post("Read git status", "opsGitStatus", empty_body),
            "/xavi-runtime/actions/ops/runtime-health": post("Check runtime health through ops agent", "opsRuntimeHealth", empty_body),
            "/xavi-runtime/actions/ops/runtime-tests": post("Run runtime tests through ops agent", "opsRuntimeTests", empty_body),
            "/xavi-runtime/actions/ops/runtime-ps": post("Show runtime containers", "opsRuntimePs", empty_body),
            "/xavi-runtime/actions/ops/runtime-logs": post(
                "Read runtime logs",
                "opsRuntimeLogs",
                {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"tail": {"type": "integer", "default": 120}},
                                "additionalProperties": False,
                            }
                        }
                    },
                },
            ),
            "/xavi-runtime/actions/ops/runtime-rebuild": post("Rebuild runtime", "opsRuntimeRebuild", empty_body),
            "/xavi-runtime/actions/ops/runtime-restart": post("Restart runtime", "opsRuntimeRestart", empty_body),
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            }
        },
    }


def register_xavi_runtime_actions(app: FastAPI, kernel: RuntimeKernel, settings: Settings) -> None:
    @app.get("/openapi.json", include_in_schema=False)
    @app.get("/xavi-runtime/actions/openapi.json", include_in_schema=False)
    def actions_openapi() -> JSONResponse:
        return JSONResponse(_schema())

    @app.get("/xavi-runtime/actions/privacy", include_in_schema=False)
    def actions_privacy() -> PlainTextResponse:
        return PlainTextResponse(
            "Xavi Runtime Actions are self-hosted runtime operations for the user's own server. "
            "Requests are authenticated with a bearer token and are processed by the configured Xavi runtime."
        )

    @app.get("/xavi-runtime/actions/health", include_in_schema=False)
    async def runtime_health(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "runtime.health", {}, "actions-runtime-health")

    @app.post("/xavi-runtime/actions/mcp/call", include_in_schema=False)
    async def mcp_call(
        req: ActionsMcpCallRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, req.tool, req.args, req.request_id)

    @app.post("/xavi-runtime/actions/run-inference", include_in_schema=False)
    async def run_inference(
        req: RunInferenceRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "runtime.run_inference", req.model_dump(exclude_none=True), "actions-run-inference")

    @app.post("/xavi-runtime/actions/repo/status", include_in_schema=False)
    async def repo_status(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.status", {}, "actions-repo-status")

    @app.post("/xavi-runtime/actions/repo/list-worktrees", include_in_schema=False)
    async def repo_list_worktrees(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.list_worktrees", {}, "actions-repo-worktrees")

    @app.post("/xavi-runtime/actions/repo/create-worktree", include_in_schema=False)
    async def repo_create_worktree(
        req: WorktreeRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        args = req.model_dump(exclude_none=True)
        return await _tool(kernel, "repo.create_worktree", args, "actions-repo-create-worktree")

    @app.post("/xavi-runtime/actions/repo/apply-patch", include_in_schema=False)
    async def repo_apply_patch(
        req: PatchRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.apply_patch", req.model_dump(), "actions-repo-apply-patch")

    @app.post("/xavi-runtime/actions/repo/diff", include_in_schema=False)
    async def repo_diff(
        req: WorktreeOnlyRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.diff", req.model_dump(), "actions-repo-diff")

    @app.post("/xavi-runtime/actions/repo/run-tests", include_in_schema=False)
    async def repo_run_tests(
        req: TestRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.run_tests", req.model_dump(), "actions-repo-run-tests")

    @app.post("/xavi-runtime/actions/repo/prepare-commit", include_in_schema=False)
    async def repo_prepare_commit(
        req: CommitRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.prepare_commit", {"worktree_id": req.worktree_id, "message": req.message}, "actions-repo-prepare-commit")

    @app.post("/xavi-runtime/actions/repo/commit", include_in_schema=False)
    async def repo_commit(
        req: CommitRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.commit", req.model_dump(), "actions-repo-commit")

    @app.post("/xavi-runtime/actions/repo/prepare-integration", include_in_schema=False)
    async def repo_prepare_integration(
        req: IntegrationRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.prepare_integration", req.model_dump(), "actions-repo-prepare-integration")

    @app.post("/xavi-runtime/actions/repo/integrate-commit", include_in_schema=False)
    async def repo_integrate_commit(
        req: IntegrateCommitRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, "repo.integrate_commit", req.model_dump(), "actions-repo-integrate-commit")

    async def call_ops(tool: str, args: dict[str, Any], authorization: str | None, x_xavi_mcp_key: str | None) -> dict[str, Any]:
        _auth(settings, authorization, x_xavi_mcp_key)
        return await _tool(kernel, tool, args, f"actions-{tool}")

    @app.post("/xavi-runtime/actions/ops/git-status", include_in_schema=False)
    async def ops_git_status(authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.git_status", {}, authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/runtime-health", include_in_schema=False)
    async def ops_runtime_health(authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.runtime_health", {}, authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/runtime-tests", include_in_schema=False)
    async def ops_runtime_tests(authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.runtime_tests", {}, authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/runtime-ps", include_in_schema=False)
    async def ops_runtime_ps(authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.runtime_ps", {}, authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/runtime-logs", include_in_schema=False)
    async def ops_runtime_logs(req: OpsLogsRequest, authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.runtime_logs", req.model_dump(), authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/runtime-rebuild", include_in_schema=False)
    async def ops_runtime_rebuild(authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.runtime_rebuild", {}, authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/runtime-restart", include_in_schema=False)
    async def ops_runtime_restart(authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.runtime_restart", {}, authorization, x_xavi_mcp_key)

    @app.post("/xavi-runtime/actions/ops/allowed-command", include_in_schema=False)
    async def ops_allowed_command(req: AllowedCommandRequest, authorization: str | None = Header(default=None), x_xavi_mcp_key: str | None = Header(default=None)) -> dict[str, Any]:
        return await call_ops("ops.allowed_command", req.model_dump(), authorization, x_xavi_mcp_key)
