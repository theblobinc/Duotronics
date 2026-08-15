from __future__ import annotations

import json
import os
import shlex
import urllib.parse
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


REPO_ROOT = Path(os.environ.get("XAVI_OPS_REPO_ROOT", "/var/www/xavi/Duotronics")).resolve()
RUNTIME_DIR = Path(os.environ.get(
    "XAVI_OPS_RUNTIME_DIR",
    "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
)).resolve()
OPS_API_KEY = os.environ.get("XAVI_OPS_API_KEY", "")
MAX_OUTPUT = int(os.environ.get("XAVI_OPS_MAX_OUTPUT", "20000"))

V3_OLLAMA_PROXY_URL = os.environ.get("XAVI_OPS_V3_OLLAMA_PROXY_URL", "http://127.0.0.1:11434").rstrip("/")
V3_OLLAMA_PROBE_PORTS = tuple(
    part.strip()
    for part in os.environ.get("XAVI_OPS_V3_OLLAMA_PROBE_PORTS", "11434,11435,11436").split(",")
    if part.strip()
)


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


def _read_capped_file(handle: Any, limit: int = MAX_OUTPUT) -> str:
    handle.flush()
    size = handle.tell()
    if size <= 0:
        return ""
    if size <= limit:
        handle.seek(0)
        return handle.read().decode("utf-8", errors="replace")
    half = max(1, limit // 2)
    handle.seek(0)
    head = handle.read(half).decode("utf-8", errors="replace")
    handle.seek(max(0, size - half))
    tail = handle.read(half).decode("utf-8", errors="replace")
    return head + f"\n...[truncated {size - (half * 2)} bytes]...\n" + tail


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

    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=stdout_file,
                stderr=stderr_file,
                env=proc_env,
                start_new_session=True,
                timeout=timeout,
                check=False,
            )
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = 124

        result = {
            "command": " ".join(shlex.quote(part) for part in cmd),
            "cwd": str(cwd),
            "returncode": returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout": _read_capped_file(stdout_file),
            "stderr": _read_capped_file(stderr_file),
            "timed_out": timed_out,
        }

    if check and result["returncode"] != 0:
        raise HTTPException(status_code=400, detail=result)
    return result

def runtime_env() -> dict[str, str]:
    return {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}


def curl_read(url: str, *, timeout: int = 5) -> dict[str, Any]:
    return run_cmd(["curl", "-fsS", "--max-time", str(timeout), url], cwd=RUNTIME_DIR, timeout=timeout + 5)


def service_state(service: str) -> dict[str, Any]:
    return {
        "active": run_cmd(["systemctl", "is-active", service], cwd=RUNTIME_DIR, timeout=30),
        "enabled": run_cmd(["systemctl", "is-enabled", service], cwd=RUNTIME_DIR, timeout=30),
    }


def v3_ollama_ports() -> dict[str, Any]:
    probes: dict[str, Any] = {}
    for port in V3_OLLAMA_PROBE_PORTS:
        base = f"http://127.0.0.1:{port}"
        probe: dict[str, Any] = {"api_tags": curl_read(f"{base}/api/tags", timeout=10)}
        if port in {"11434", "11435"}:
            probe["proxy_status"] = curl_read(f"{base}/_proxy/status", timeout=10)
        probes[port] = probe
    return {"proxy_url": V3_OLLAMA_PROXY_URL, "probe_ports": list(V3_OLLAMA_PROBE_PORTS), "probes": probes}


def sanitized_runtime_env() -> dict[str, Any]:
    env_path = RUNTIME_DIR / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return {"path": str(env_path), "exists": False, "values": values}
    interesting = ("OLLAMA", "MODEL", "XAVI", "RUNTIME", "V3", "SRNN", "WG_RNN")
    secret_words = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASS")
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if not any(part in key.upper() for part in interesting):
            continue
        values[key] = "<redacted>" if any(part in key.upper() for part in secret_words) else value
    return {"path": str(env_path), "exists": True, "values": values}



# ---- Runtime v3 maintenance helpers added by MCP bootstrap ----

def _v3_runtime_dir() -> Path:
    return Path(os.environ.get(
        "XAVI_OPS_RUNTIME_DIR",
        "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
    )).resolve()


def _v3_repo_root() -> Path:
    return Path(os.environ.get("XAVI_OPS_REPO_ROOT", "/var/www/xavi/Duotronics")).resolve()


def _v3_backup(path: Path) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.name}.backup-mcp-{stamp}-{os.getpid()}")
    backup_path.write_text(path.read_text())
    return backup_path


def _v3_safe_file(relative_path: str) -> Path:
    root = _v3_runtime_dir()
    rel = str(relative_path or "").strip().lstrip("/")
    if not rel:
        raise HTTPException(status_code=400, detail="path is required")
    target = (root / rel).resolve()
    if not target.is_relative_to(root):
        raise HTTPException(status_code=400, detail="path escapes runtime v3 root")
    allowed_suffixes = {".json", ".py", ".yaml", ".yml", ".toml", ".md", ".txt"}
    if target.suffix not in allowed_suffixes:
        raise HTTPException(status_code=400, detail=f"file suffix not allowlisted: {target.suffix}")
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"file not found: {rel}")
    return target


def v3_git_status() -> dict[str, Any]:
    return run_cmd(["git", "status", "--short"], cwd=_v3_repo_root(), timeout=60)


def v3_git_diff() -> dict[str, Any]:
    return run_cmd(["git", "diff", "--", str(_v3_runtime_dir().relative_to(_v3_repo_root()))], cwd=_v3_repo_root(), timeout=60)


def v3_rebuild_runtime_image() -> dict[str, Any]:
    return run_cmd(
        ["podman", "build", "-f", "./Containerfile", "-t", "localhost/duotronic-srnn-runtime-host:v3", "."],
        cwd=_v3_runtime_dir(),
        timeout=900,
    )


def v3_restart_runtime_only() -> dict[str, Any]:
    return run_cmd(
        ["systemctl", "--user", "restart", "xavi-duotronic-runtime.service"],
        cwd=_v3_runtime_dir(),
        timeout=300,
    )


def v3_apply_text_replace(args: dict[str, Any]) -> dict[str, Any]:
    target = _v3_safe_file(str(args.get("path", "")))
    old = str(args.get("old", ""))
    new = str(args.get("new", ""))
    count = int(args.get("count", 1))
    dry_run = bool(args.get("dry_run", False))

    if not old:
        raise HTTPException(status_code=400, detail="old text is required")
    if count < 1:
        raise HTTPException(status_code=400, detail="count must be >= 1")

    text = target.read_text()
    occurrences = text.count(old)

    expected = args.get("expected_occurrences")
    if expected is not None and occurrences != int(expected):
        raise HTTPException(
            status_code=409,
            detail=f"expected {expected} occurrences, found {occurrences}",
        )
    if occurrences == 0:
        raise HTTPException(status_code=404, detail="old text not found")

    result = {
        "path": str(target),
        "occurrences": occurrences,
        "replaced": min(count, occurrences),
        "dry_run": dry_run,
        "backup": None,
    }

    if not dry_run:
        backup = _v3_backup(target)
        target.write_text(text.replace(old, new, count))
        result["backup"] = str(backup)

    return result


def v3_apply_vscode_model_aliases() -> dict[str, Any]:
    path = _v3_runtime_dir() / "config" / "models.json"
    data = json.loads(path.read_text())
    models = data.setdefault("models", [])

    aliases = [
        {
            "name": "xavi-vscode-fast",
            "provider": "ollama",
            "model": "qwen2.5-coder:1.5b",
            "base_url": "http://ollama:11434",
            "enabled_env": "OLLAMA_ENABLED",
            "default": False,
            "description": "Fast VS Code coding route for small edits, explanations, and fallback on the local runtime Ollama path.",
            "metadata": {
                "xavi_role": "vscode_fast",
                "hardware_tier": "local_fast",
                "recommended_for": ["selection_explain", "small_edit", "fallback"],
            },
        },
        {
            "name": "xavi-vscode-balanced",
            "provider": "ollama",
            "model": "qwen2.5-coder:3b",
            "base_url": "http://ollama:11434",
            "enabled_env": "OLLAMA_ENABLED",
            "default": False,
            "description": "Balanced VS Code coding route for normal file edits on the local runtime Ollama path.",
            "metadata": {
                "xavi_role": "vscode_balanced",
                "hardware_tier": "local_balanced",
                "recommended_for": ["single_file_edit", "code_review", "chat"],
            },
        },
        {
            "name": "xavi-vscode-agent",
            "provider": "ollama",
            "model": "qwen2.5-coder:xavi-agent",
            "base_url": "http://host.containers.internal:11434",
            "enabled_env": "OLLAMA_ENABLED",
            "default": False,
            "description": "Primary VS Code agent route through the host Ollama tool proxy / remote GPU mesh.",
            "metadata": {
                "xavi_role": "vscode_agent",
                "hardware_tier": "gpu_mesh",
                "recommended_for": ["multi_file_edit", "agent_chat", "refactor"],
            },
        },
        {
            "name": "xavi-vscode-deep",
            "provider": "ollama",
            "model": "qwen2.5-coder:7b",
            "base_url": "http://host.containers.internal:11434",
            "enabled_env": "OLLAMA_ENABLED",
            "default": False,
            "description": "Deep VS Code reasoning route for repo-wide planning and larger code context through the host Ollama tool proxy / remote GPU mesh.",
            "metadata": {
                "xavi_role": "vscode_deep",
                "hardware_tier": "remote_gpu_or_cpu",
                "recommended_for": ["repo_reasoning", "architecture", "long_context_planning"],
            },
        },
        {
            "name": "xavi-vscode-copilot",
            "provider": "ollama",
            "model": "xavi-copilot-agent:latest",
            "base_url": "http://host.containers.internal:11434",
            "enabled_env": "OLLAMA_ENABLED",
            "default": False,
            "description": "Custom Xavi copilot route through the host Ollama tool proxy / remote GPU mesh.",
            "metadata": {
                "xavi_role": "vscode_copilot",
                "hardware_tier": "gpu_mesh",
                "recommended_for": ["copilot_chat", "custom_xavi_behavior", "tool_augmented_agent"],
            },
        },
    ]

    def upsert(record: dict[str, Any]) -> None:
        for i, existing in enumerate(models):
            if existing.get("name") == record["name"]:
                models[i] = record
                return
        models.append(record)

    backup = _v3_backup(path)
    for alias in aliases:
        upsert(alias)

    path.write_text(json.dumps(data, indent=2) + "\n")

    return {
        "path": str(path),
        "backup": str(backup),
        "aliases": [{"name": a["name"], "model": a["model"], "base_url": a["base_url"]} for a in aliases],
    }

# ---- End runtime v3 maintenance helpers ----


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
        {"name": "ops.v3_server_snapshot", "description": "Read runtime v3 containers, ports, services, runtime health, and Ollama proxy state.", "danger": "low"},
        {"name": "ops.v3_ollama_ports", "description": "Probe runtime v3 host Ollama/proxy ports with /api/tags.", "danger": "low"},
        {"name": "ops.v3_ollama_proxy_status", "description": "Read runtime v3 Ollama proxy /_proxy/status.", "danger": "low"},
        {"name": "ops.v3_ollama_proxy_tags", "description": "Read runtime v3 Ollama proxy /api/tags.", "danger": "low"},
        {"name": "ops.v3_model_route_probe", "description": "Probe runtime v3 Ollama proxy routing for a model.", "danger": "low"},
        {"name": "ops.v3_runtime_env", "description": "Read sanitized runtime v3 Ollama/model env configuration.", "danger": "low"},
        {"name": "ops.v3_apply_vscode_model_aliases", "description": "Apply stable runtime v3 VS Code model aliases.", "danger": "medium"},
        {"name": "ops.v3_apply_text_replace", "description": "Safely replace text in an allowlisted runtime v3 file with backup.", "danger": "medium"},
        {"name": "ops.v3_rebuild_runtime_image", "description": "Build the runtime v3 container image only.", "danger": "high"},
        {"name": "ops.v3_restart_runtime_only", "description": "Recreate only the runtime v3 container.", "danger": "high"},
        {"name": "ops.v3_git_status", "description": "Show git status for the Duotronics repo.", "danger": "low"},
        {"name": "ops.v3_git_diff", "description": "Show git diff for runtime v3 changes.", "danger": "low"},
        {"name": "ops.nginx_status", "description": "Read nginx active/enabled status.", "danger": "low"},
        {"name": "ops.nginx_test", "description": "Run nginx configuration test.", "danger": "low"},
        {"name": "ops.nginx_reload", "description": "Validate config, then reload nginx.", "danger": "medium"},
        {"name": "ops.nginx_restart", "description": "Validate config, then restart nginx.", "danger": "high"},
        {"name": "ops.nginx_start", "description": "Start nginx and verify active status.", "danger": "medium"},
        {"name": "ops.allowed_command", "description": "Run one named allowlisted command.", "danger": "varies"},
    ]


ALLOWED_COMMANDS: dict[str, dict[str, Any]] = {
    "v3_apply_vscode_model_aliases": {
        "cmd": ["/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/.venv/bin/python", "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/ops_agent/v3_maintenance/apply_vscode_model_aliases.py"],
        "cwd": Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3"),
        "timeout": 60,
    },
    "v3_rebuild_runtime_image": {
        "cmd": ["podman", "build", "-f", "./Containerfile", "-t", "localhost/duotronic-srnn-runtime-host:v3", "."],
        "cwd": Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3"),
        "timeout": 900,
    },
    "v3_restart_runtime_only": {
        "cmd": ["systemctl", "--user", "restart", "xavi-duotronic-runtime.service"],
        "cwd": Path("/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3"),
        "timeout": 300,
    },
    "v3_git_status": {
        "cmd": ["git", "status", "--short"],
        "cwd": Path("/var/www/xavi/Duotronics"),
        "timeout": 60,
    },
    "v3_git_diff": {
        "cmd": ["git", "diff", "--", "build_docs/runtime/duotronic_srnn_open_runtime-v3"],
        "cwd": Path("/var/www/xavi/Duotronics"),
        "timeout": 60,
    },
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


ALLOWED_COMMANDS.update({
    "nginx_status": {
        "cmd": ["/usr/bin/bash", "-lc", "/usr/bin/systemctl is-active nginx; /usr/bin/systemctl is-enabled nginx"],
        "cwd": REPO_ROOT,
        "timeout": 30,
    },
    "nginx_test": {
        "cmd": ["/usr/bin/sudo", "-n", "/usr/sbin/nginx", "-t"],
        "cwd": REPO_ROOT,
        "timeout": 30,
    },
    "nginx_reload": {
        "cmd": ["/usr/bin/bash", "-lc", "set -euo pipefail; sudo -n /usr/sbin/nginx -t; sudo -n /usr/bin/systemctl reload nginx; /usr/bin/systemctl is-active nginx"],
        "cwd": REPO_ROOT,
        "timeout": 45,
    },
    "nginx_restart": {
        "cmd": ["/usr/bin/bash", "-lc", "set -euo pipefail; sudo -n /usr/sbin/nginx -t; sudo -n /usr/bin/systemctl restart nginx; /usr/bin/systemctl is-active nginx"],
        "cwd": REPO_ROOT,
        "timeout": 60,
    },
    "nginx_start": {
        "cmd": ["/usr/bin/bash", "-lc", "set -euo pipefail; sudo -n /usr/bin/systemctl start nginx; /usr/bin/systemctl is-active nginx"],
        "cwd": REPO_ROOT,
        "timeout": 45,
    },
})


app = FastAPI(title="Xavi Runtime Host Ops Agent", version="0.1.0")


@app.get("/health")
def health(authorization: str | None = Header(default=None), x_xavi_ops_key: str | None = Header(default=None)) -> dict[str, Any]:
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
def commands(authorization: str | None = Header(default=None), x_xavi_ops_key: str | None = Header(default=None)) -> dict[str, Any]:
    require_ops_key(authorization, x_xavi_ops_key)
    return {"commands": command_manifest(), "raw_shell_enabled": False}


@app.post("/call")
def call(req: OpsCallRequest, authorization: str | None = Header(default=None), x_xavi_ops_key: str | None = Header(default=None)) -> dict[str, Any]:
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
        return {"result": run_cmd([
            ".venv/bin/python",
            "-m",
            "pytest",
            "-q",
            "tests/test_client_profiles_contracts.py",
            "tests/test_session_ledger_contracts.py",
            "tests/test_operation_planner_contracts.py",
            "tests/test_inference_router_contracts.py",
            "tests/test_tool_runtime_contracts.py",
            "tests/test_ops_mcp_contracts.py",
        ], cwd=RUNTIME_DIR, timeout=900, env=runtime_env())}

    if command == "ops.runtime_ps":
        return {"result": run_cmd(["podman", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"], cwd=RUNTIME_DIR, timeout=60)}

    if command == "ops.runtime_logs":
        tail = str(max(1, min(int(args.get("tail", 120)), 1000)))
        return {"result": run_cmd(["podman", "logs", f"--tail={tail}", "duotronic-runtime"], cwd=RUNTIME_DIR, timeout=60)}

    if command == "ops.runtime_health":
        return {
            "result": {
                "local": curl_read("http://127.0.0.1:8080/health", timeout=5),
                "public": curl_read("https://dev.xavi.app/health", timeout=5),
            }
        }

    if command == "ops.v3_ollama_ports":
        return {"result": v3_ollama_ports()}

    if command == "ops.v3_ollama_proxy_status":
        return {"result": curl_read(f"{V3_OLLAMA_PROXY_URL}/_proxy/status", timeout=10)}

    if command == "ops.v3_ollama_proxy_tags":
        return {"result": curl_read(f"{V3_OLLAMA_PROXY_URL}/api/tags", timeout=10)}

    if command == "ops.v3_model_route_probe":
        model = str(args.get("model", "qwen2.5-coder:3b")).strip()
        encoded_model = urllib.parse.quote(model, safe=":-._")
        return {
            "result": {
                "model": model,
                "route_probe": curl_read(f"{V3_OLLAMA_PROXY_URL}/_proxy/route_probe?model={encoded_model}", timeout=10),
                "tags": curl_read(f"{V3_OLLAMA_PROXY_URL}/api/tags", timeout=10),
            }
        }

    if command == "ops.v3_runtime_env":
        return {"result": sanitized_runtime_env()}

    if command == "ops.v3_server_snapshot":
        return {
            "result": {
                "repo_root": str(REPO_ROOT),
                "runtime_dir": str(RUNTIME_DIR),
                "ollama_proxy_url": V3_OLLAMA_PROXY_URL,
                "podman_ps": run_cmd(["podman", "ps", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"], cwd=RUNTIME_DIR, timeout=60),
                "listening_ports": run_cmd(["ss", "-ltnp"], cwd=RUNTIME_DIR, timeout=30),
                "runtime_health_local": run_cmd(["curl", "-fsS", "--max-time", "10", "http://127.0.0.1:8080/health"], cwd=RUNTIME_DIR, timeout=15),
                "runtime_env": sanitized_runtime_env(),
                "services": {
                    "xavi-runtime-ops-agent.service": service_state("xavi-runtime-ops-agent.service"),
                    "xavi-ollama-tool-proxy.service": service_state("xavi-ollama-tool-proxy.service"),
                    "xavi-ollama-proxy.service": service_state("xavi-ollama-proxy.service"),
                },
                "ollama_ports": v3_ollama_ports(),
            }
        }

    if command == "ops.v3_apply_vscode_model_aliases":
        return {"result": v3_apply_vscode_model_aliases()}

    if command == "ops.v3_apply_text_replace":
        return {"result": v3_apply_text_replace(args)}

    if command == "ops.v3_rebuild_runtime_image":
        return {"result": v3_rebuild_runtime_image()}

    if command == "ops.v3_restart_runtime_only":
        return {"result": v3_restart_runtime_only()}

    if command == "ops.v3_git_status":
        return {"result": v3_git_status()}

    if command == "ops.v3_git_diff":
        return {"result": v3_git_diff()}

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

    if command.startswith("ops.nginx_"):
        name = command.removeprefix("ops.")
        if name not in ALLOWED_COMMANDS:
            raise HTTPException(status_code=404, detail=f"unknown nginx ops command: {name}")
        spec = ALLOWED_COMMANDS[name]
        return {
            "result": run_cmd(
                list(spec["cmd"]),
                cwd=Path(spec["cwd"]),
                timeout=int(spec.get("timeout", 300)),
                env=spec.get("env"),
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
