#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "xavi-runtime-v3-dev-mcp"
SERVER_VERSION = "0.1.0"

V3_DIR = Path(os.environ.get(
    "XAVI_OPS_RUNTIME_DIR",
    "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
)).resolve()

REPO_ROOT = Path(os.environ.get("XAVI_OPS_REPO_ROOT", "/var/www/xavi/Duotronics")).resolve()
OPS_URL = os.environ.get("XAVI_OPS_URL", "http://127.0.0.1:8091").replace("host.containers.internal", "127.0.0.1").rstrip("/")
OPS_KEY = os.environ.get("XAVI_OPS_API_KEY", "")
RUNTIME_URL = os.environ.get("XAVI_RUNTIME_URL", "http://127.0.0.1:8080").rstrip("/")

app = FastAPI(title="Xavi Runtime v3 Developer MCP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com", "https://chat.openai.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "MCP-Protocol-Version"],
)

def rpc_result(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

def rpc_error(req_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}

def fetch_json(url: str, timeout: int = 15) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def runtime_mcp_rpc(method: str, params: dict[str, Any] | None = None, timeout: int = 30, auth_header: str | None = None) -> dict[str, Any]:
    payload = json.dumps({"jsonrpc": "2.0", "id": method, "method": method, "params": params or {}}).encode()
    headers = {"content-type": "application/json"}
    if auth_header:
        headers["authorization"] = auth_header
    req = urllib.request.Request(
        RUNTIME_URL + "/mcp",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def runtime_mcp_tools(auth_header: str | None = None) -> list[dict[str, Any]]:
    try:
        response = runtime_mcp_rpc("tools/list", {}, timeout=10, auth_header=auth_header)
        tools = response.get("result", {}).get("tools", [])
        if isinstance(tools, list):
            return tools
    except Exception:
        return []
    return []


def merged_tools(auth_header: str | None = None) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for tool in TOOLS + runtime_mcp_tools(auth_header):
        name = tool.get("name") if isinstance(tool, dict) else None
        if not name or name in seen:
            continue
        seen.add(name)
        normalized = dict(tool)
        # Adapter uses MCP inputSchema; runtime uses inputSchema too via mcp_protocol.
        if "input_schema" in normalized and "inputSchema" not in normalized:
            normalized["inputSchema"] = normalized.pop("input_schema")
        merged.append(normalized)
    return merged


def runtime_mcp_tool_call(name: str, args: dict[str, Any], auth_header: str | None = None) -> Any:
    response = runtime_mcp_rpc("tools/call", {"name": name, "arguments": args}, timeout=120, auth_header=auth_header)
    if "error" in response:
        raise RuntimeError(json.dumps(response["error"], sort_keys=True))
    result = response.get("result", {})
    if isinstance(result, dict) and "structuredContent" in result:
        return result["structuredContent"]
    return result

def call_ops(command: str, args: dict[str, Any] | None = None, timeout: int = 60) -> Any:
    payload = json.dumps({"command": command, "args": args or {}}).encode()
    req = urllib.request.Request(
        OPS_URL + "/call",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-xavi-ops-key": OPS_KEY,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def run_fixed(cmd: list[str], cwd: Path, timeout: int = 300) -> dict[str, Any]:
    started = datetime.utcnow()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd),
        "returncode": proc.returncode,
        "duration_ms": int((datetime.utcnow() - started).total_seconds() * 1000),
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }

def apply_vscode_aliases() -> dict[str, Any]:
    path = V3_DIR / "config" / "models.json"
    data = json.loads(path.read_text())
    models = data.setdefault("models", [])

    aliases = [
        ("xavi-vscode-fast", "qwen2.5-coder:1.5b", "http://ollama:11434", "local_fast", "selection_explain,small_edit,fallback"),
        ("xavi-vscode-balanced", "qwen2.5-coder:3b", "http://ollama:11434", "local_balanced", "single_file_edit,code_review,chat"),
        ("xavi-vscode-agent", "qwen2.5-coder:xavi-agent", "http://host.containers.internal:11434", "gpu_mesh", "multi_file_edit,agent_chat,refactor"),
        ("xavi-vscode-deep", "qwen2.5-coder:7b", "http://host.containers.internal:11434", "remote_gpu_or_cpu", "repo_reasoning,architecture,long_context_planning"),
        ("xavi-vscode-copilot", "xavi-copilot-agent:latest", "http://host.containers.internal:11434", "gpu_mesh", "copilot_chat,custom_xavi_behavior,tool_augmented_agent"),
    ]

    backup = path.with_name(path.name + ".backup-dev-mcp-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
    backup.write_text(path.read_text())

    def upsert(record: dict[str, Any]) -> None:
        for i, item in enumerate(models):
            if item.get("name") == record["name"]:
                models[i] = record
                return
        models.append(record)

    for name, model, base_url, tier, recommended in aliases:
        upsert({
            "name": name,
            "provider": "ollama",
            "model": model,
            "base_url": base_url,
            "enabled_env": "OLLAMA_ENABLED",
            "default": False,
            "description": f"VS Code model alias for {name}.",
            "metadata": {
                "xavi_role": name.replace("xavi-", "").replace("-", "_"),
                "hardware_tier": tier,
                "recommended_for": recommended.split(","),
            },
        })

    path.write_text(json.dumps(data, indent=2) + "\n")

    return {
        "ok": True,
        "path": str(path),
        "backup": str(backup),
        "aliases": [
            {"name": name, "model": model, "base_url": base_url}
            for name, model, base_url, _, _ in aliases
        ],
    }


def _dev_allowed_roots() -> list[Path]:
    roots = [
        REPO_ROOT,
        V3_DIR,
        Path("/var/www/xavi"),
        Path("/home/tbi"),
        Path("/etc/nginx"),
        Path("/etc/caddy"),
        Path("/etc/systemd/system"),
        Path("/etc/containers"),
    ]
    return [r.resolve() for r in roots if r.exists()]


def _safe_dev_path(raw: str) -> Path:
    target = Path(raw).expanduser()
    if not target.is_absolute():
        target = (REPO_ROOT / target)
    target = target.resolve()
    for root in _dev_allowed_roots():
        try:
            if target == root or target.is_relative_to(root):
                return target
        except AttributeError:
            if str(target).startswith(str(root) + "/") or target == root:
                return target
    raise ValueError(f"path is outside allowed roots: {target}")


def _trim_output(value: str, limit: int = 60000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"


def _tool_text_content(result: Any) -> str:
    """Serialize tool results with a hard cap to avoid freezing ChatGPT's tool-call UI."""
    limit = _bounded_int(os.environ.get("XAVI_DEV_MCP_MAX_CONTENT_CHARS"), 12000, 2000, 60000)
    text = json.dumps(result, indent=2, default=str)
    if len(text) <= limit:
        return text
    preview = text[:limit]
    return json.dumps({
        "_truncated": True,
        "original_chars": len(text),
        "returned_chars": limit,
        "preview": preview,
        "note": "Output was capped by xavi_dev_mcp_adapter to keep the ChatGPT tool-call/status UI responsive. Use a narrower tool, smaller tail/limit, or targeted read for full details."
    }, indent=2)


def dev_rpc(args: dict[str, Any]) -> dict[str, Any]:
    action = str(args.get("action", "")).strip()

    if action == "list_dir":
        path = _safe_dev_path(str(args.get("path", ".")))
        entries = []
        for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            st = child.stat()
            entries.append({
                "name": child.name,
                "path": str(child),
                "type": "dir" if child.is_dir() else "file",
                "size": st.st_size,
            })
        return {"action": action, "path": str(path), "entries": entries}

    if action == "read_file":
        path = _safe_dev_path(str(args["path"]))
        limit = min(int(args.get("limit", 60000)), 250000)
        text = path.read_text(errors="replace")
        return {
            "action": action,
            "path": str(path),
            "size": len(text),
            "content": text[:limit],
            "truncated": len(text) > limit,
        }

    if action == "write_file":
        path = _safe_dev_path(str(args["path"]))
        content = str(args.get("content", ""))
        backup = None
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and bool(args.get("backup", True)):
            backup = path.with_name(path.name + ".backup-dev-rpc-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
            backup.write_text(path.read_text(errors="replace"))
        path.write_text(content)
        return {"action": action, "path": str(path), "bytes": len(content), "backup": str(backup) if backup else None}

    if action == "append_file":
        path = _safe_dev_path(str(args["path"]))
        content = str(args.get("content", ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(content)
        return {"action": action, "path": str(path), "bytes_appended": len(content)}

    if action == "replace_text":
        path = _safe_dev_path(str(args["path"]))
        old = str(args.get("old", ""))
        new = str(args.get("new", ""))
        count = int(args.get("count", 1))
        if not old:
            raise ValueError("old text is required")
        text = path.read_text(errors="replace")
        occurrences = text.count(old)
        expected = args.get("expected_occurrences")
        if expected is not None and occurrences != int(expected):
            raise ValueError(f"expected {expected} occurrences, found {occurrences}")
        if occurrences == 0:
            raise ValueError("old text not found")
        backup = path.with_name(path.name + ".backup-dev-rpc-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
        backup.write_text(text)
        path.write_text(text.replace(old, new, count))
        return {"action": action, "path": str(path), "occurrences": occurrences, "replaced": min(count, occurrences), "backup": str(backup)}

    if action == "shell_exec":
        raise ValueError("dev_rpc shell_exec is disabled; use bounded_job_start/status/output/kill with a registered bounded command instead.")

    raise ValueError(f"unknown dev_rpc action: {action}")


# ---- Bounded runtime/node tools ----

def _bounded_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        n = int(value)
    except Exception:
        n = default
    return max(low, min(high, n))


def _run_text(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    result = run_fixed(cmd, cwd or REPO_ROOT, timeout=timeout)
    result["stdout"] = _trim_output(result.get("stdout", ""))
    result["stderr"] = _trim_output(result.get("stderr", ""))
    return result


def _post_json(url: str, payload: dict[str, Any], timeout: int = 120) -> Any:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        text = r.read().decode()
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}


def _ollama_base(port: str) -> str:
    port = str(port or "11434").strip()
    allowed = {"11434", "11436", "18205"}
    if port not in allowed:
        raise ValueError(f"unsupported ollama port: {port}")
    return f"http://127.0.0.1:{port}"


def tool_host_status(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "podman": _run_text(["podman", "ps", "-a", "--format", "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}"], REPO_ROOT, 60),
        "ports": _run_text(["ss", "-ltnp"], REPO_ROOT, 60),
        "disk": _run_text(["df", "-h", "/", "/var/www/xavi"], REPO_ROOT, 60),
    }


def tool_runtime_containers(args: dict[str, Any]) -> dict[str, Any]:
    return _run_text(["podman", "ps", "-a", "--format", "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}"], REPO_ROOT, 60)


def tool_runtime_tail(args: dict[str, Any]) -> dict[str, Any]:
    tail = _bounded_int(args.get("tail"), 160, 1, 2000)
    return _run_text(["podman", "logs", f"--tail={tail}", "duotronic-runtime"], V3_DIR, 120)


def tool_adapter_tail(args: dict[str, Any]) -> dict[str, Any]:
    tail = _bounded_int(args.get("tail"), 160, 1, 2000)
    path = V3_DIR / "data" / "logs" / "xavi_dev_mcp_adapter.log"
    if not path.exists():
        return {"path": str(path), "exists": False, "content": ""}
    lines = path.read_text(errors="replace").splitlines()
    return {"path": str(path), "exists": True, "content": "\n".join(lines[-tail:])}


def tool_repo_overview(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": _run_text(["git", "status", "--short"], REPO_ROOT, 60),
        "branch": _run_text(["git", "branch", "--show-current"], REPO_ROOT, 60),
        "recent": _run_text(["git", "log", "-12", "--oneline", "--decorate"], REPO_ROOT, 60),
    }


def tool_repo_diff_all(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "stat": _run_text(["git", "diff", "--stat"], REPO_ROOT, 60),
        "v3": _run_text(["git", "diff", "--", str(V3_DIR.relative_to(REPO_ROOT))], REPO_ROOT, 60),
    }


def tool_runtime_test_contracts(args: dict[str, Any]) -> dict[str, Any]:
    timeout = _bounded_int(args.get("timeout"), 300, 30, 900)
    py = V3_DIR / ".venv" / "bin" / "python"
    if py.exists():
        return _run_text([str(py), "-m", "pytest", "-q", "tests/test_ops_mcp_contracts.py"], V3_DIR, timeout)
    return _run_text(["python3", "-m", "pytest", "-q", "tests/test_ops_mcp_contracts.py"], V3_DIR, timeout)


def tool_nginx_dev_config(args: dict[str, Any]) -> dict[str, Any]:
    path = Path("/etc/nginx/sites-enabled/dev.xavi.app.conf")
    return {"path": str(path), "content": path.read_text(errors="replace")}


def tool_service_status(args: dict[str, Any]) -> dict[str, Any]:
    service = str(args.get("service", "nginx")).strip()
    allowed = {
        "nginx",
        "xavi-runtime-ops-agent.service",
        "xavi-ollama-tool-proxy.service",
        "xavi-ollama-proxy.service",
    }
    if service not in allowed:
        raise ValueError(f"unsupported service: {service}")
    return {
        "service": service,
        "active": _run_text(["systemctl", "is-active", service], REPO_ROOT, 30),
        "enabled": _run_text(["systemctl", "is-enabled", service], REPO_ROOT, 30),
    }


def tool_ollama_inventory(args: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for port in ["11434", "11436", "18205"]:
        base = _ollama_base(port)
        try:
            out[port] = fetch_json(base + "/api/tags", timeout=20)
        except Exception as e:
            out[port] = {"error": str(e)}
    return out


def tool_ollama_probe(args: dict[str, Any]) -> dict[str, Any]:
    port = str(args.get("port", "11434"))
    model = str(args.get("model", "qwen2.5-coder:xavi-agent"))
    prompt = str(args.get("prompt", "Reply with READY and the model name."))
    timeout = _bounded_int(args.get("timeout"), 120, 10, 300)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 64},
    }
    return {
        "port": port,
        "model": model,
        "result": _post_json(_ollama_base(port) + "/api/generate", payload, timeout),
    }


def tool_ollama_pull(args: dict[str, Any]) -> dict[str, Any]:
    port = str(args.get("port", "11436"))
    model = str(args.get("model", "")).strip()
    if not model:
        raise ValueError("model is required")

    allowed_prefixes = (
        "qwen2.5",
        "qwen2.5-coder",
        "qwen3",
        "qwen3-coder",
        "deepseek-coder",
        "deepseek-coder-v2",
        "llama3",
        "gemma",
        "starcoder2",
        "devstral",
        "codestral",
        "phi4",
        "mistral",
        "nomic-embed-text",
    )
    if not model.startswith(allowed_prefixes):
        raise ValueError(f"model not allowlisted for pull: {model}")

    timeout = _bounded_int(args.get("timeout"), 900, 60, 1800)
    payload = {"name": model, "stream": False}
    return {
        "port": port,
        "model": model,
        "result": _post_json(_ollama_base(port) + "/api/pull", payload, timeout),
    }

# ---- End bounded runtime/node tools ----

TOOLS = [
    {
        "name": "search",
        "title": "Search",
        "description": "Search Xavi runtime v3 operational resources and model aliases.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "fetch",
        "title": "Fetch",
        "description": "Fetch a known Xavi runtime v3 resource by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "runtime_health",
        "title": "Runtime Health",
        "description": "Read runtime v3 health.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "runtime_models",
        "title": "Runtime Models",
        "description": "Read runtime v3 model registry.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "ops_allowed_command",
        "title": "Ops Allowed Command",
        "description": "Run a named allowlisted v3 host ops command.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "apply_vscode_model_aliases",
        "title": "Apply VS Code Model Aliases",
        "description": "Apply stable runtime v3 VS Code model aliases directly to config/models.json.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "rebuild_runtime_image",
        "title": "Rebuild Runtime Image",
        "description": "Build the runtime v3 container image only.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "restart_runtime_only",
        "title": "Restart Runtime Only",
        "description": "Recreate only the runtime v3 container using the v3 helper script.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "git_status",
        "title": "Git Status",
        "description": "Show git status for the Duotronics repo.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "git_diff_v3",
        "title": "Git Diff v3",
        "description": "Show git diff for runtime v3 files.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]



TOOLS.append({
    "name": "host_status",
    "title": "Host Status",
    "description": "Read bounded host status: containers, listening ports, and disk usage.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
})

TOOLS.append({
    "name": "runtime_containers",
    "title": "Runtime Containers",
    "description": "List Podman containers for the runtime host.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
})

TOOLS.append({
    "name": "runtime_tail",
    "title": "Runtime Tail",
    "description": "Read recent duotronic-runtime container logs.",
    "inputSchema": {
        "type": "object",
        "properties": {"tail": {"type": "integer"}},
        "additionalProperties": False
    }
})

TOOLS.append({
    "name": "adapter_tail",
    "title": "Adapter Tail",
    "description": "Read recent Developer MCP adapter logs.",
    "inputSchema": {
        "type": "object",
        "properties": {"tail": {"type": "integer"}},
        "additionalProperties": False
    }
})

TOOLS.append({
    "name": "repo_overview",
    "title": "Repo Overview",
    "description": "Read git status, current branch, and recent commits.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
})

TOOLS.append({
    "name": "repo_diff_all",
    "title": "Repo Diff All",
    "description": "Read git diff stat and runtime v3 diff.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
})

TOOLS.append({
    "name": "runtime_test_contracts",
    "title": "Runtime Contract Tests",
    "description": "Run the runtime v3 MCP contract pytest suite.",
    "inputSchema": {
        "type": "object",
        "properties": {"timeout": {"type": "integer"}},
        "additionalProperties": False
    }
})

TOOLS.append({
    "name": "nginx_dev_config",
    "title": "Nginx Dev Config",
    "description": "Read dev.xavi.app nginx config.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
})

TOOLS.append({
    "name": "service_status",
    "title": "Service Status",
    "description": "Read systemd status for allowlisted runtime-related services.",
    "inputSchema": {
        "type": "object",
        "properties": {"service": {"type": "string"}},
        "additionalProperties": False
    }
})

TOOLS.append({
    "name": "ollama_inventory",
    "title": "Ollama Inventory",
    "description": "Read Ollama /api/tags on ports 11434, 11436, and 18205.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}
})

TOOLS.append({
    "name": "ollama_probe",
    "title": "Ollama Probe",
    "description": "Run a bounded non-streaming Ollama generate probe on an allowlisted port.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "port": {"type": "string"},
            "model": {"type": "string"},
            "prompt": {"type": "string"},
            "timeout": {"type": "integer"}
        },
        "additionalProperties": False
    }
})

TOOLS.append({
    "name": "ollama_pull",
    "title": "Ollama Pull",
    "description": "Pull an allowlisted Ollama model to an allowlisted runtime port.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "port": {"type": "string"},
            "model": {"type": "string"},
            "timeout": {"type": "integer"}
        },
        "required": ["model"],
        "additionalProperties": False
    }
})


TOOLS.append({
    "name": "shell_exec",
    "title": "Shell Exec",
    "description": "Run a shell command in an allowed Xavi development root.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "cwd": {"type": "string"},
            "command": {"type": "string"},
            "timeout": {"type": "integer"}
        },
        "required": ["command"],
        "additionalProperties": False
    }
})

TOOLS.append({
    "name": "dev_rpc",
    "title": "Developer RPC",
    "description": "Read, write, patch, list, and run shell commands in allowed Xavi development roots.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list_dir", "read_file", "write_file", "append_file", "replace_text", "shell_exec"]
            },
            "path": {"type": "string"},
            "cwd": {"type": "string"},
            "command": {"type": "string"},
            "content": {"type": "string"},
            "old": {"type": "string"},
            "new": {"type": "string"},
            "count": {"type": "integer"},
            "limit": {"type": "integer"},
            "timeout": {"type": "integer"},
            "backup": {"type": "boolean"},
            "expected_occurrences": {"type": "integer"}
        },
        "required": ["action"],
        "additionalProperties": True
    }
})


# ---- Optional extension tools loaded from ops_agent/xavi_mcp_bounded_ext.py ----
try:
    from xavi_mcp_bounded_ext import EXT_TOOLS, handle_ext_tool as _EXT_HANDLE
    TOOLS.extend(EXT_TOOLS)
    EXTENSION_LOAD_ERROR = None
except Exception as e:
    _EXT_HANDLE = None
    EXTENSION_LOAD_ERROR = str(e)


# ---- Disable synchronous command execution tools that hang in ChatGPT ----
DISABLED_TOOL_NAMES = {"shell_exec", "bounded_command_run"}

TOOLS[:] = [t for t in TOOLS if t.get("name") not in DISABLED_TOOL_NAMES]

for _tool in TOOLS:
    if _tool.get("name") == "dev_rpc":
        try:
            enum = _tool["inputSchema"]["properties"]["action"]["enum"]
            _tool["inputSchema"]["properties"]["action"]["enum"] = [
                x for x in enum if x != "shell_exec"
            ]
            _tool["description"] = "Read, write, patch, and list files in allowed Xavi development roots."
        except Exception:
            pass
# ---- End disabled synchronous tools ----

@app.get("/")
async def health() -> dict[str, Any]:
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocol": PROTOCOL_VERSION,
        "status": "running",
        "runtime_dir": str(V3_DIR),
        "mcp": "POST /",
    }

@app.post("/")
async def mcp_root(request: Request) -> JSONResponse:
    body = await request.json()
    if not isinstance(body, dict):
        return JSONResponse(rpc_error(None, -32600, "Invalid JSON-RPC request"), status_code=400)

    method = body.get("method")
    params = body.get("params") or {}
    req_id = body.get("id")
    is_notification = "id" not in body

    try:
        if is_notification:
            if method == "initialized":
                return Response(status_code=202)
            # Per MCP Streamable HTTP, JSON-RPC notifications do not receive a JSON-RPC response.
            return Response(status_code=202)

        if method == "initialize":
            return JSONResponse(rpc_result(req_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "logging": {},
                    "prompts": {"listChanged": False},
                    "resources": {"listChanged": False},
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "title": "Xavi Runtime v3 Developer MCP",
                    "version": SERVER_VERSION,
                },
            }))

        if method == "initialized":
            return JSONResponse({})

        if method == "tools/list":
            return JSONResponse(rpc_result(req_id, {"tools": merged_tools(request.headers.get("authorization"))}))

        if method == "resources/list":
            return JSONResponse(rpc_result(req_id, {"resources": [], "nextCursor": None}))

        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}

            if name in DISABLED_TOOL_NAMES:
                return JSONResponse(rpc_error(
                    req_id,
                    -32001,
                    f"Tool disabled because synchronous command execution hangs in ChatGPT: {name}. Use bounded_job_start/status/output/kill instead."
                ))

            if name == "search":
                q = args.get("query", "")
                result = [
                    {"id": "runtime.health", "title": "Runtime health", "content": f"Runtime v3 health for query: {q}"},
                    {"id": "runtime.models", "title": "Runtime models", "content": "Configured and discovered runtime v3 models"},
                    {"id": "ops.commands", "title": "Ops commands", "content": "Allowlisted host ops commands"},
                ]

            elif name == "fetch":
                rid = args.get("id")
                if rid == "runtime.health":
                    result = fetch_json(RUNTIME_URL + "/health")
                elif rid == "runtime.models":
                    result = fetch_json(RUNTIME_URL + "/health").get("models", [])
                elif rid == "ops.commands":
                    result = call_ops("ops.commands")
                else:
                    result = {"id": rid, "error": "unknown resource id"}

            elif name == "host_status":
                result = tool_host_status(args)

            elif name == "runtime_containers":
                result = tool_runtime_containers(args)

            elif name == "runtime_tail":
                result = tool_runtime_tail(args)

            elif name == "adapter_tail":
                result = tool_adapter_tail(args)

            elif name == "repo_overview":
                result = tool_repo_overview(args)

            elif name == "repo_diff_all":
                result = tool_repo_diff_all(args)

            elif name == "runtime_test_contracts":
                result = tool_runtime_test_contracts(args)

            elif name == "nginx_dev_config":
                result = tool_nginx_dev_config(args)

            elif name == "service_status":
                result = tool_service_status(args)

            elif name == "ollama_inventory":
                result = tool_ollama_inventory(args)

            elif name == "ollama_probe":
                result = tool_ollama_probe(args)

            elif name == "ollama_pull":
                result = tool_ollama_pull(args)

            elif name == "shell_exec":
                cwd = _safe_dev_path(str(args.get("cwd", str(REPO_ROOT))))
                command = str(args["command"])
                timeout = min(int(args.get("timeout", 120)), 900)
                result = run_fixed(["/bin/bash", "-lc", command], cwd, timeout=timeout)
                result["stdout"] = _trim_output(result.get("stdout", ""))
                result["stderr"] = _trim_output(result.get("stderr", ""))

            elif name == "dev_rpc":
                result = dev_rpc(args)

            elif name == "runtime_health":
                result = fetch_json(RUNTIME_URL + "/health")

            elif name == "runtime_models":
                result = fetch_json(RUNTIME_URL + "/health").get("models", [])

            elif name == "ops_allowed_command":
                result = call_ops("ops.allowed_command", {"name": args["name"]}, timeout=900)

            elif name == "apply_vscode_model_aliases":
                result = apply_vscode_aliases()

            elif name == "rebuild_runtime_image":
                result = run_fixed(
                    ["podman", "build", "-f", "./Containerfile", "-t", "localhost/duotronic-srnn-runtime-host:v3", "."],
                    V3_DIR,
                    timeout=900,
                )

            elif name == "restart_runtime_only":
                result = run_fixed(
                    [str(V3_DIR / "ops_agent/v3_maintenance/restart_runtime_only.sh")],
                    V3_DIR,
                    timeout=180,
                )

            elif name == "git_status":
                result = run_fixed(["git", "status", "--short"], REPO_ROOT, timeout=60)

            elif name == "git_diff_v3":
                result = run_fixed(["git", "diff", "--", str(V3_DIR.relative_to(REPO_ROOT))], REPO_ROOT, timeout=60)

            else:
                if isinstance(name, str) and name.startswith("runtime."):
                    result = runtime_mcp_tool_call(name, args, request.headers.get("authorization"))
                elif _EXT_HANDLE is not None:
                    handled, result = _EXT_HANDLE(name, args)
                    if not handled:
                        return JSONResponse(rpc_error(req_id, -32601, f"Unknown tool: {name}"))
                else:
                    return JSONResponse(rpc_error(req_id, -32601, f"Unknown tool: {name}"))

            return JSONResponse(rpc_result(req_id, {
                "content": [{"type": "text", "text": _tool_text_content(result)}],
                "isError": False,
            }))

        return JSONResponse(rpc_error(req_id, -32601, f"Method not found: {method}"))

    except Exception as e:
        return JSONResponse(rpc_error(req_id, -32000, str(e)))

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("XAVI_DEV_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("XAVI_DEV_MCP_PORT", "8092"))
    uvicorn.run(app, host=host, port=port)
