from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


REPO_ROOT = Path(os.environ.get("XAVI_OPS_REPO_ROOT", "/var/www/xavi/Duotronics")).resolve()
RUNTIME_DIR = Path(os.environ.get(
    "XAVI_OPS_RUNTIME_DIR",
    "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v2",
)).resolve()
OPS_API_KEY = os.environ.get("XAVI_OPS_API_KEY", "")
MAX_OUTPUT = int(os.environ.get("XAVI_OPS_MAX_OUTPUT", "20000"))


class OpsCallRequest(BaseModel):
    command: str = Field(..., min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


def require_ops_key(authorization: str | None, x_xavi_ops_key: str | None) -> None:
    if not OPS_API_KEY:
        raise HTTPException(status_code=503, detail="XAVI_OPS_API_KEY is not configured")

    expected = f"Bearer {OPS_API_KEY}"
    if authorization == expected or x_xavi_ops_key == OPS_API_KEY:
        return

    raise HTTPException(status_code=401, detail="missing or invalid ops credential")


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path,
    timeout: int = 300,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        env=proc_env,
    )

    result = {
        "command": " ".join(shlex.quote(part) for part in cmd),
        "cwd": str(cwd),
        "returncode": proc.returncode,
        "duration_ms": int((time.time() - started) * 1000),
        "stdout": proc.stdout[-MAX_OUTPUT:],
        "stderr": proc.stderr[-MAX_OUTPUT:],
    }

    if check and proc.returncode != 0:
        raise HTTPException(status_code=400, detail=result)

    return result


def runtime_env() -> dict[str, str]:
    return {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}


def command_manifest() -> list[dict[str, Any]]:
    return [
        {"name": "ops.health", "description": "Check host ops agent status.", "danger": "low"},
        {"name": "ops.git_status", "description": "Run git status/rev-parse/ls-remote.", "danger": "low"},
        {"name": "ops.git_pull", "description": "Pull origin main in repo root.", "danger": "medium"},
        {"name": "ops.git_push", "description": "Push local main to origin.", "danger": "medium"},
        {"name": "ops.runtime_tests", "description": "Run runtime pytest suite.", "danger": "medium"},
        {"name": "ops.runtime_ps", "description": "Show podman containers.", "danger": "low"},
        {"name": "ops.runtime_logs", "description": "Show duotronic-runtime logs.", "danger": "low"},
        {"name": "ops.runtime_health", "description": "Curl local and public runtime health.", "danger": "low"},
        {"name": "ops.runtime_restart", "description": "Restart duotronic-runtime container.", "danger": "high"},
        {"name": "ops.runtime_rebuild", "description": "Rebuild and restart runtime service through podman compose.", "danger": "high"},
        {"name": "ops.runtime_rebuild_models", "description": "Rebuild/restart runtime with COMPOSE_PROFILES=models.", "danger": "high"},
        {"name": "ops.allowed_command", "description": "Run one named allowlisted command.", "danger": "varies"},
    ]


ALLOWED_COMMANDS: dict[str, dict[str, Any]] = {
    "runtime_pytest": {
        "cmd": [".venv/bin/python", "-m", "pytest", "-q"],
        "cwd": RUNTIME_DIR,
        "timeout": 900,
        "env": runtime_env(),
    },
    "runtime_health_public": {
        "cmd": ["curl", "-fsS", "https://dev.xavi.app/health"],
        "cwd": RUNTIME_DIR,
        "timeout": 60,
    },
    "runtime_health_local": {
        "cmd": ["curl", "-fsS", "http://127.0.0.1:8080/health"],
        "cwd": RUNTIME_DIR,
        "timeout": 60,
    },
    "podman_ps": {
        "cmd": ["podman", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"],
        "cwd": RUNTIME_DIR,
        "timeout": 60,
    },
}


app = FastAPI(title="Xavi Runtime Host Ops Agent", version="0.1.0")


@app.get("/health")
async def health(authorization: str | None = Header(default=None), x_xavi_ops_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_ops_key(authorization, x_xavi_ops_key)
    return {
        "status": "ok",
        "agent": "xavi-runtime-host-ops",
        "repo_root": str(REPO_ROOT),
        "runtime_dir": str(RUNTIME_DIR),
        "commands": len(command_manifest()),
        "raw_shell_enabled": False,
    }


@app.get("/commands")
async def commands(authorization: str | None = Header(default=None), x_xavi_ops_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_ops_key(authorization, x_xavi_ops_key)
    return {"commands": command_manifest(), "raw_shell_enabled": False}


@app.post("/call")
async def call(req: OpsCallRequest, authorization: str | None = Header(default=None), x_xavi_ops_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_ops_key(authorization, x_xavi_ops_key)

    command = req.command
    args = req.args or {}

    if command == "ops.health":
        return {"result": {"status": "ok", "agent": "xavi-runtime-host-ops", "raw_shell_enabled": False}}

    if command == "ops.git_status":
        return {
            "result": {
                "rev_parse": run_cmd(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, timeout=60),
                "status": run_cmd(["git", "status", "--short"], cwd=REPO_ROOT, timeout=60),
                "remote": run_cmd(["git", "ls-remote", "origin", "main"], cwd=REPO_ROOT, timeout=60),
            }
        }

    if command == "ops.git_pull":
        return {"result": run_cmd(["git", "pull", "--ff-only", "origin", "main"], cwd=REPO_ROOT, timeout=180)}

    if command == "ops.git_push":
        return {"result": run_cmd(["git", "push", "origin", "main"], cwd=REPO_ROOT, timeout=180)}

    if command == "ops.runtime_tests":
        return {"result": run_cmd([".venv/bin/python", "-m", "pytest", "-q"], cwd=RUNTIME_DIR, timeout=900, env=runtime_env())}

    if command == "ops.runtime_ps":
        return {"result": run_cmd(["podman", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"], cwd=RUNTIME_DIR, timeout=60)}

    if command == "ops.runtime_logs":
        tail = str(max(1, min(int(args.get("tail", 120)), 1000)))
        return {"result": run_cmd(["podman", "logs", f"--tail={tail}", "duotronic-runtime"], cwd=RUNTIME_DIR, timeout=60)}

    if command == "ops.runtime_health":
        return {
            "result": {
                "local": run_cmd(["curl", "-fsS", "http://127.0.0.1:8080/health"], cwd=RUNTIME_DIR, timeout=60),
                "public": run_cmd(["curl", "-fsS", "https://dev.xavi.app/health"], cwd=RUNTIME_DIR, timeout=60),
            }
        }

    if command == "ops.runtime_restart":
        return {
            "result": {
                "rm": run_cmd(["podman", "rm", "-f", "duotronic-runtime"], cwd=RUNTIME_DIR, timeout=120),
                "up": run_cmd(["podman", "compose", "--env-file", ".env", "up", "-d", "runtime"], cwd=RUNTIME_DIR, timeout=600),
            }
        }

    if command == "ops.runtime_rebuild":
        return {
            "result": run_cmd(
                ["podman", "compose", "--env-file", ".env", "up", "-d", "--build", "runtime"],
                cwd=RUNTIME_DIR,
                timeout=1200,
            )
        }

    if command == "ops.runtime_rebuild_models":
        return {
            "result": run_cmd(
                ["podman", "compose", "--env-file", ".env", "up", "-d", "--build", "runtime"],
                cwd=RUNTIME_DIR,
                timeout=1200,
                env={"COMPOSE_PROFILES": "models"},
            )
        }

    if command == "ops.allowed_command":
        name = str(args.get("name", "")).strip()
        if name not in ALLOWED_COMMANDS:
            raise HTTPException(status_code=404, detail=f"unknown allowed command: {name}")
        spec = ALLOWED_COMMANDS[name]
        return {
            "result": run_cmd(
                list(spec["cmd"]),
                cwd=Path(spec["cwd"]),
                timeout=int(spec.get("timeout", 300)),
                env=spec.get("env"),
            )
        }

    raise HTTPException(status_code=404, detail=f"unknown ops command: {command}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("XAVI_OPS_HOST", "127.0.0.1"), port=int(os.environ.get("XAVI_OPS_PORT", "8091")))
