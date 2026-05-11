from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .config import Settings


_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,96}$")
_SAFE_BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,160}$")


def repo_tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "repo.status",
            "description": "Read git status, HEAD, branch, and configured repo/worktree roots.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "repo.list_worktrees",
            "description": "List git worktrees for the mounted repo.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "repo.create_worktree",
            "description": "Create an isolated git worktree and branch for proposed edits.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["branch_name"],
                "properties": {
                    "branch_name": {"type": "string"},
                    "base_ref": {"type": "string", "default": "HEAD"},
                    "worktree_id": {"type": ["string", "null"]},
                },
            },
        },
        {
            "name": "repo.apply_patch",
            "description": "Apply a unified diff to an isolated worktree after git apply --check.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["worktree_id", "patch"],
                "properties": {
                    "worktree_id": {"type": "string"},
                    "patch": {"type": "string"},
                },
            },
        },
        {
            "name": "repo.diff",
            "description": "Show git status and diff for an isolated worktree.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["worktree_id"],
                "properties": {"worktree_id": {"type": "string"}},
            },
        },
        {
            "name": "repo.run_tests",
            "description": "Run an allowlisted test command inside the isolated worktree.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["worktree_id"],
                "properties": {
                    "worktree_id": {"type": "string"},
                    "test_command": {"type": "string", "enum": ["runtime_pytest"], "default": "runtime_pytest"},
                    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 900, "default": 300},
                },
            },
        },
        {
            "name": "repo.prepare_commit",
            "description": "Generate an approval token bound to the current diff digest, message, and latest passing test.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["worktree_id", "message"],
                "properties": {
                    "worktree_id": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
        },
        {
            "name": "repo.commit",
            "description": "Commit isolated worktree changes only when a valid approval token is supplied.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["worktree_id", "message", "approval_token"],
                "properties": {
                    "worktree_id": {"type": "string"},
                    "message": {"type": "string"},
                    "approval_token": {"type": "string"},
                },
            },
        },
        {
            "name": "repo.remove_worktree",
            "description": "Remove an isolated worktree under the configured worktree root.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["worktree_id"],
                "properties": {
                    "worktree_id": {"type": "string"},
                    "force": {"type": "boolean", "default": False},
                },
            },
        },
    ]


def repo_resources() -> list[dict[str, str]]:
    return [
        {"uri": "xavi-runtime://repo/status", "name": "Repository status"},
        {"uri": "xavi-runtime://repo/worktrees", "name": "Repository worktrees"},
    ]


class XaviRepoTools:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo_root = Path(settings.xavi_repo_root).resolve()
        self.worktree_root = Path(settings.xavi_worktree_root).resolve()

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self._require_enabled()

        if tool == "repo.status":
            return self.status()

        if tool == "repo.list_worktrees":
            return self.list_worktrees()

        if tool == "repo.create_worktree":
            return self.create_worktree(args)

        if tool == "repo.apply_patch":
            return self.apply_patch(args)

        if tool == "repo.diff":
            return self.diff(args)

        if tool == "repo.run_tests":
            return self.run_tests(args)

        if tool == "repo.prepare_commit":
            return self.prepare_commit(args)

        if tool == "repo.commit":
            return self.commit(args)

        if tool == "repo.remove_worktree":
            return self.remove_worktree(args)

        raise HTTPException(status_code=404, detail=f"unknown repo MCP tool: {tool}")

    def _require_enabled(self) -> None:
        if not self.settings.xavi_mcp_repo_tools_enabled:
            raise HTTPException(status_code=404, detail="repo MCP tools are disabled")

        if not self.settings.xavi_repo_approval_secret:
            raise HTTPException(status_code=503, detail="XAVI_REPO_APPROVAL_SECRET is not configured")

        if not self.repo_root.exists():
            raise HTTPException(status_code=503, detail=f"repo root does not exist: {self.repo_root}")

        if not (self.repo_root / ".git").exists():
            raise HTTPException(status_code=503, detail=f"repo root is not a git repository: {self.repo_root}")

        self.worktree_root.mkdir(parents=True, exist_ok=True)
        self._mark_safe_directory(self.repo_root)

    def _mark_safe_directory(self, path: Path) -> None:
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def _run(
        self,
        cmd: list[str],
        *,
        cwd: Path | None = None,
        timeout: int = 120,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)

        proc = subprocess.run(
            cmd,
            cwd=str(cwd or self.repo_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=proc_env,
        )

        if check and proc.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "command": " ".join(shlex.quote(part) for part in cmd),
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-4000:],
                    "stderr": proc.stderr[-4000:],
                },
            )

        return proc

    def _safe_branch(self, branch: str) -> str:
        branch = branch.strip()
        if not _SAFE_BRANCH.fullmatch(branch):
            raise HTTPException(status_code=422, detail="unsafe branch_name")
        if branch.startswith("/") or ".." in branch or branch.endswith("/"):
            raise HTTPException(status_code=422, detail="unsafe branch_name")
        return branch

    def _safe_worktree_id(self, value: str) -> str:
        value = value.strip()
        if not _SAFE_ID.fullmatch(value):
            raise HTTPException(status_code=422, detail="unsafe worktree_id")
        return value

    def _default_worktree_id(self, branch_name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", branch_name).strip("-")
        stamp = int(time.time())
        candidate = f"{safe[:64]}-{stamp}"
        return self._safe_worktree_id(candidate)

    def _worktree_path(self, worktree_id: str) -> Path:
        safe_id = self._safe_worktree_id(worktree_id)
        path = (self.worktree_root / safe_id).resolve()
        if self.worktree_root not in path.parents and path != self.worktree_root:
            raise HTTPException(status_code=422, detail="worktree path escaped configured root")
        return path

    def _metadata_dir(self, worktree: Path) -> Path:
        path = worktree / ".xavi"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _diff_text(self, worktree: Path) -> str:
        return self._run(["git", "diff", "--"], cwd=worktree).stdout

    def _diff_digest(self, worktree: Path) -> str:
        return hashlib.sha256(self._diff_text(worktree).encode("utf-8")).hexdigest()

    def _approval_token(self, *, worktree_id: str, diff_digest: str, message: str) -> str:
        payload = f"{worktree_id}\n{diff_digest}\n{message}".encode("utf-8")
        secret = self.settings.xavi_repo_approval_secret.encode("utf-8")
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()

    def status(self) -> dict[str, Any]:
        self._mark_safe_directory(self.repo_root)
        branch = self._run(["git", "branch", "--show-current"]).stdout.strip()
        head = self._run(["git", "rev-parse", "HEAD"]).stdout.strip()
        status = self._run(["git", "status", "--short"]).stdout
        return {
            "repo_root": str(self.repo_root),
            "worktree_root": str(self.worktree_root),
            "branch": branch,
            "head": head,
            "status_short": status,
            "repo_tools_enabled": self.settings.xavi_mcp_repo_tools_enabled,
            "push_enabled": False,
            "direct_live_edit_enabled": False,
        }

    def list_worktrees(self) -> dict[str, Any]:
        raw = self._run(["git", "worktree", "list", "--porcelain"]).stdout
        return {"raw": raw}

    def create_worktree(self, args: dict[str, Any]) -> dict[str, Any]:
        branch_name = self._safe_branch(str(args.get("branch_name", "")))
        base_ref = str(args.get("base_ref") or "HEAD").strip()
        if not base_ref or len(base_ref) > 160:
            raise HTTPException(status_code=422, detail="invalid base_ref")

        worktree_id = args.get("worktree_id") or self._default_worktree_id(branch_name)
        worktree_path = self._worktree_path(str(worktree_id))

        if worktree_path.exists():
            raise HTTPException(status_code=409, detail=f"worktree already exists: {worktree_path}")

        self.worktree_root.mkdir(parents=True, exist_ok=True)
        proc = self._run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_ref],
            cwd=self.repo_root,
            timeout=180,
        )
        self._mark_safe_directory(worktree_path)

        return {
            "worktree_id": str(worktree_id),
            "branch_name": branch_name,
            "base_ref": base_ref,
            "path": str(worktree_path),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    def apply_patch(self, args: dict[str, Any]) -> dict[str, Any]:
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id", "")))
        patch = str(args.get("patch", ""))

        if not patch.strip():
            raise HTTPException(status_code=422, detail="patch is empty")
        if len(patch.encode("utf-8")) > 1_000_000:
            raise HTTPException(status_code=413, detail="patch is too large")

        worktree = self._worktree_path(worktree_id)
        if not worktree.exists():
            raise HTTPException(status_code=404, detail=f"unknown worktree: {worktree_id}")

        meta = self._metadata_dir(worktree)
        patch_path = meta / f"patch-{int(time.time())}.diff"
        patch_path.write_text(patch)

        self._run(["git", "apply", "--check", str(patch_path)], cwd=worktree, timeout=120)
        apply_proc = self._run(["git", "apply", str(patch_path)], cwd=worktree, timeout=120)

        return {
            "worktree_id": worktree_id,
            "patch_ref": str(patch_path),
            "diff_digest": self._diff_digest(worktree),
            "status_short": self._run(["git", "status", "--short"], cwd=worktree).stdout,
            "stdout": apply_proc.stdout,
            "stderr": apply_proc.stderr,
        }

    def diff(self, args: dict[str, Any]) -> dict[str, Any]:
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id", "")))
        worktree = self._worktree_path(worktree_id)

        if not worktree.exists():
            raise HTTPException(status_code=404, detail=f"unknown worktree: {worktree_id}")

        return {
            "worktree_id": worktree_id,
            "path": str(worktree),
            "status_short": self._run(["git", "status", "--short"], cwd=worktree).stdout,
            "diff_digest": self._diff_digest(worktree),
            "diff": self._diff_text(worktree),
        }

    def run_tests(self, args: dict[str, Any]) -> dict[str, Any]:
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id", "")))
        worktree = self._worktree_path(worktree_id)

        if not worktree.exists():
            raise HTTPException(status_code=404, detail=f"unknown worktree: {worktree_id}")

        command = str(args.get("test_command", "runtime_pytest"))
        timeout = max(1, min(int(args.get("timeout_seconds", 300)), 900))

        if command != "runtime_pytest":
            raise HTTPException(status_code=403, detail="test_command is not allowlisted")

        runtime_dir = worktree / "build_docs" / "runtime" / "duotronic_srnn_open_runtime-v2"
        if not runtime_dir.exists():
            raise HTTPException(status_code=404, detail=f"runtime dir missing in worktree: {runtime_dir}")

        env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
        proc = self._run(
            ["python", "-m", "pytest", "-q"],
            cwd=runtime_dir,
            timeout=timeout,
            check=False,
            env=env,
        )

        passed = proc.returncode == 0
        result = {
            "worktree_id": worktree_id,
            "test_command": command,
            "passed": passed,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-12000:],
            "stderr": proc.stderr[-12000:],
            "diff_digest": self._diff_digest(worktree),
            "created_at_ms": int(time.time() * 1000),
        }

        (self._metadata_dir(worktree) / "last_test.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    def prepare_commit(self, args: dict[str, Any]) -> dict[str, Any]:
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id", "")))
        message = str(args.get("message", "")).strip()
        if not message:
            raise HTTPException(status_code=422, detail="message is required")

        worktree = self._worktree_path(worktree_id)
        if not worktree.exists():
            raise HTTPException(status_code=404, detail=f"unknown worktree: {worktree_id}")

        test_path = self._metadata_dir(worktree) / "last_test.json"
        if not test_path.exists():
            raise HTTPException(status_code=403, detail="run repo.run_tests before preparing commit approval")

        last_test = json.loads(test_path.read_text())
        if not last_test.get("passed"):
            raise HTTPException(status_code=403, detail="latest test did not pass")

        diff_digest = self._diff_digest(worktree)
        if not diff_digest or diff_digest == hashlib.sha256(b"").hexdigest():
            raise HTTPException(status_code=422, detail="no diff to approve")

        if last_test.get("diff_digest") != diff_digest:
            raise HTTPException(status_code=409, detail="diff changed since latest test; rerun repo.run_tests")

        token = self._approval_token(worktree_id=worktree_id, diff_digest=diff_digest, message=message)
        approval = {
            "worktree_id": worktree_id,
            "message": message,
            "diff_digest": diff_digest,
            "approval_token": token,
            "created_at_ms": int(time.time() * 1000),
            "requires_human_copy_back": True,
            "push_enabled": False,
        }
        (self._metadata_dir(worktree) / "approval.json").write_text(json.dumps(approval, indent=2) + "\n")
        return approval

    def commit(self, args: dict[str, Any]) -> dict[str, Any]:
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id", "")))
        message = str(args.get("message", "")).strip()
        approval_token = str(args.get("approval_token", "")).strip()

        if not message:
            raise HTTPException(status_code=422, detail="message is required")
        if not approval_token:
            raise HTTPException(status_code=422, detail="approval_token is required")

        worktree = self._worktree_path(worktree_id)
        if not worktree.exists():
            raise HTTPException(status_code=404, detail=f"unknown worktree: {worktree_id}")

        diff_digest = self._diff_digest(worktree)
        expected = self._approval_token(worktree_id=worktree_id, diff_digest=diff_digest, message=message)
        if not hmac.compare_digest(approval_token, expected):
            raise HTTPException(status_code=403, detail="invalid approval token for current diff/message")

        status = self._run(["git", "status", "--short"], cwd=worktree).stdout
        if not status.strip():
            raise HTTPException(status_code=422, detail="no changes to commit")

        self._run(["git", "add", "-A"], cwd=worktree)
        commit_proc = self._run(["git", "commit", "-m", message], cwd=worktree, timeout=180)
        head = self._run(["git", "rev-parse", "HEAD"], cwd=worktree).stdout.strip()
        branch = self._run(["git", "branch", "--show-current"], cwd=worktree).stdout.strip()

        return {
            "worktree_id": worktree_id,
            "branch": branch,
            "commit": head,
            "message": message,
            "stdout": commit_proc.stdout,
            "stderr": commit_proc.stderr,
            "push_enabled": False,
            "next_step": "Review the worktree commit locally, then merge/sync manually from VS Code or CLI.",
        }

    def remove_worktree(self, args: dict[str, Any]) -> dict[str, Any]:
        worktree_id = self._safe_worktree_id(str(args.get("worktree_id", "")))
        force = bool(args.get("force", False))
        worktree = self._worktree_path(worktree_id)

        if not worktree.exists():
            return {"worktree_id": worktree_id, "removed": False, "reason": "already absent"}

        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(worktree))

        proc = self._run(cmd, cwd=self.repo_root, timeout=180)
        return {
            "worktree_id": worktree_id,
            "removed": True,
            "path": str(worktree),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
