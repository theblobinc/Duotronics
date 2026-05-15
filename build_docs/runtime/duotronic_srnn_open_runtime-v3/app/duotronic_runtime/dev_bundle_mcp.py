from __future__ import annotations

import re
import time
from typing import Any

from fastapi import HTTPException

from .config import Settings
from .ops_mcp import XaviOpsTools
from .repo_mcp import XaviRepoTools

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,96}$")
_SAFE_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,160}$")


def dev_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "dev.apply_change_bundle",
            "description": (
                "Apply a full development change bundle in one call: create worktree, apply patch, run tests, "
                "commit, integrate into local main, optionally push, report rebuild intent, and clean up."
            ),
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["patch", "message"],
                "properties": {
                    "patch": {"type": "string", "minLength": 1},
                    "message": {"type": "string", "minLength": 1},
                    "branch_name": {"type": ["string", "null"]},
                    "worktree_id": {"type": ["string", "null"]},
                    "base_ref": {"type": "string", "default": "HEAD"},
                    "target_branch": {"type": "string", "default": "main"},
                    "test_command": {"type": "string", "enum": ["runtime_pytest"], "default": "runtime_pytest"},
                    "test_timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 900, "default": 300},
                    "push": {"type": "boolean", "default": False},
                    "rebuild": {"type": "boolean", "default": False, "description": "Request a separate rebuild recommendation. Rebuild is not executed inline."},
                    "rebuild_models": {"type": "boolean", "default": True},
                    "cleanup": {"type": "boolean", "default": True},
                },
            },
        }
    ]


class XaviDevBundleTools:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo = XaviRepoTools(settings)
        self.ops = XaviOpsTools(settings)

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool != "dev.apply_change_bundle":
            raise HTTPException(status_code=404, detail=f"unknown dev MCP tool: {tool}")
        return await self.apply_change_bundle(args)

    def _safe_worktree_id(self, value: str) -> str:
        value = value.strip()
        if not _SAFE_ID.fullmatch(value):
            raise HTTPException(status_code=422, detail="unsafe worktree_id")
        return value

    def _safe_branch(self, value: str) -> str:
        value = value.strip()
        if not _SAFE_BRANCH.fullmatch(value):
            raise HTTPException(status_code=422, detail="unsafe branch_name")
        if value.startswith("/") or ".." in value or value.endswith("/"):
            raise HTTPException(status_code=422, detail="unsafe branch_name")
        return value

    def _slug(self, message: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", message.lower()).strip("-")
        return (slug or "xavi-change")[:48]

    async def _maybe_ops(self, name: str, enabled: bool, results: dict[str, Any], args: dict[str, Any] | None = None) -> None:
        if not enabled:
            results[name] = {"skipped": True}
            return
        results[name] = await self.ops.call(name, args or {})

    async def apply_change_bundle(self, args: dict[str, Any]) -> dict[str, Any]:
        patch = str(args.get("patch", ""))
        message = str(args.get("message", "")).strip()
        if not patch.strip():
            raise HTTPException(status_code=422, detail="patch is required")
        if not message:
            raise HTTPException(status_code=422, detail="message is required")

        stamp = int(time.time())
        slug = self._slug(message)
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id") or f"bundle-{slug}-{stamp}"))
        branch_name = self._safe_branch(str(args.get("branch_name") or f"xavi/bundle-{slug}-{stamp}"))
        base_ref = str(args.get("base_ref") or "HEAD").strip()
        target_branch = self._safe_branch(str(args.get("target_branch") or "main"))
        test_command = str(args.get("test_command") or "runtime_pytest")
        test_timeout_seconds = max(1, min(int(args.get("test_timeout_seconds", 300)), 900))
        cleanup = bool(args.get("cleanup", True))
        do_push = bool(args.get("push", False))
        do_rebuild = bool(args.get("rebuild", False))
        rebuild_models = bool(args.get("rebuild_models", True))

        results: dict[str, Any] = {
            "worktree_id": worktree_id,
            "branch_name": branch_name,
            "target_branch": target_branch,
            "message": message,
            "push_requested": do_push,
            "rebuild_requested": do_rebuild,
            "steps": {},
        }
        steps = results["steps"]

        created = False
        try:
            steps["create_worktree"] = self.repo.create_worktree(
                {"worktree_id": worktree_id, "branch_name": branch_name, "base_ref": base_ref}
            )
            created = True

            steps["apply_patch"] = self.repo.apply_patch({"worktree_id": worktree_id, "patch": patch})

            steps["run_tests_before_commit"] = self.repo.run_tests(
                {
                    "worktree_id": worktree_id,
                    "test_command": test_command,
                    "timeout_seconds": test_timeout_seconds,
                }
            )
            if not steps["run_tests_before_commit"].get("passed"):
                raise HTTPException(status_code=409, detail={"error": "tests_failed_before_commit", "result": steps["run_tests_before_commit"]})

            commit_approval = self.repo.prepare_commit({"worktree_id": worktree_id, "message": message})
            steps["prepare_commit"] = {k: v for k, v in commit_approval.items() if k != "approval_token"}

            commit_result = self.repo.commit(
                {
                    "worktree_id": worktree_id,
                    "message": message,
                    "approval_token": commit_approval["approval_token"],
                }
            )
            steps["commit"] = commit_result

            steps["run_tests_after_commit"] = self.repo.run_tests(
                {
                    "worktree_id": worktree_id,
                    "test_command": test_command,
                    "timeout_seconds": test_timeout_seconds,
                }
            )
            if not steps["run_tests_after_commit"].get("passed"):
                raise HTTPException(status_code=409, detail={"error": "tests_failed_after_commit", "result": steps["run_tests_after_commit"]})

            integration_approval = self.repo.prepare_integration(
                {"worktree_id": worktree_id, "message": message, "target_branch": target_branch}
            )
            steps["prepare_integration"] = {k: v for k, v in integration_approval.items() if k != "approval_token"}

            integration_result = self.repo.integrate_commit(
                {
                    "worktree_id": worktree_id,
                    "commit": commit_result["commit"],
                    "message": message,
                    "approval_token": integration_approval["approval_token"],
                    "target_branch": target_branch,
                    "expected_main_head": integration_approval["expected_main_head"],
                }
            )
            steps["integrate_commit"] = integration_result
            results["new_head"] = integration_result.get("new_head")

            await self._maybe_ops("ops.git_push", do_push, steps)

            # Never rebuild the runtime from inside this MCP request.
            # Rebuilding the same container that is serving the request cuts off
            # the HTTP connection and appears to ChatGPT as a 502/hang.
            # Return an explicit next action instead.
            rebuild_tool = "ops.runtime_rebuild_models" if rebuild_models else "ops.runtime_rebuild"
            results["rebuild_required"] = do_rebuild
            results["rebuild_tool"] = rebuild_tool if do_rebuild else None

            if do_rebuild:
                steps["ops.runtime_rebuild"] = {
                    "skipped": True,
                    "reason": "rebuilds are intentionally deferred outside dev.apply_change_bundle",
                    "next_tool": rebuild_tool,
                }
            else:
                steps["ops.runtime_rebuild"] = {
                    "skipped": True,
                    "reason": "not requested",
                }

            return results
        finally:
            if cleanup and created:
                try:
                    steps["remove_worktree"] = self.repo.remove_worktree({"worktree_id": worktree_id, "force": True})
                except Exception as exc:
                    steps["remove_worktree"] = {"error": exc.__class__.__name__, "message": str(exc)}
