from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

V3_DIR = Path(os.environ.get(
    "XAVI_OPS_RUNTIME_DIR",
    "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
)).resolve()
REPO_ROOT = Path(os.environ.get("XAVI_OPS_REPO_ROOT", "/var/www/xavi/Duotronics")).resolve()
REGISTRY_PATH = V3_DIR / "config" / "bounded_commands.json"
MIKROTIK_VENV_PYTHON = Path("/var/www/xavi/vendor/mikrotik-mcp/.xavi-venv/bin/python")
MIKROTIK_BRIDGE = Path("/var/www/xavi/xavi-stack-manager/bin/xavi_mikrotik_bridge.py")
MIKROTIK_CWD = Path("/var/www/xavi/xavi-stack-manager")


def _trim(value: str, limit: int = 60000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n...[truncated {len(value) - limit} chars]"


def _bounded_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        n = int(value)
    except Exception:
        n = default
    return max(low, min(high, n))


def _run(argv: list[str], cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    started = datetime.utcnow()
    proc = subprocess.run(
        argv,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "argv": argv,
        "cwd": str(cwd or REPO_ROOT),
        "returncode": proc.returncode,
        "duration_ms": int((datetime.utcnow() - started).total_seconds() * 1000),
        "stdout": _trim(proc.stdout),
        "stderr": _trim(proc.stderr),
    }


def _fetch_json(url: str, timeout: int = 20) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


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


def _safe_path(raw: str) -> Path:
    roots = [
        REPO_ROOT,
        V3_DIR,
        Path("/var/www/xavi"),
        Path("/home/tbi"),
        Path("/etc/nginx"),
        Path("/etc/systemd/system"),
        Path("/etc/containers"),
    ]
    target = Path(raw).expanduser()
    if not target.is_absolute():
        target = REPO_ROOT / target
    target = target.resolve()
    for root in [r.resolve() for r in roots if r.exists()]:
        if target == root or target.is_relative_to(root):
            return target
    raise ValueError(f"path outside allowed roots: {target}")


def _model_name_ok(name: str) -> str:
    name = str(name or "").strip()
    if not name:
        raise ValueError("model name is required")
    allowed_prefixes = (
        "qwen2.5",
        "qwen2.5-coder",
        "qwen3",
        "qwen3-coder",
        "deepseek-coder",
        "deepseek-coder-v2",
        "llama3",
        "nomic-embed-text",
        "xavi-",
        "minicpm-v",
        "llava",
        "qwen2.5vl",
        "gemma",
        "starcoder2",
        "devstral",
        "codestral",
        "phi4",
        "mistral",
    )
    if not name.startswith(allowed_prefixes):
        raise ValueError(f"model name not allowlisted: {name}")
    return name


def ollama_copy_tag(args: dict[str, Any]) -> dict[str, Any]:
    port = str(args.get("port", "11434"))
    source = _model_name_ok(str(args.get("source", "")))
    destination = _model_name_ok(str(args.get("destination", "")))
    payload = {"source": source, "destination": destination}
    return {
        "port": port,
        "source": source,
        "destination": destination,
        "result": _post_json(_ollama_base(port) + "/api/copy", payload, 120),
    }


def ollama_create_tag(args: dict[str, Any]) -> dict[str, Any]:
    port = str(args.get("port", "11434"))
    name = _model_name_ok(str(args.get("name", "")))
    source = _model_name_ok(str(args.get("source", "")))
    system = str(args.get("system", "")).strip()
    parameters = args.get("parameters") or {}
    payload: dict[str, Any] = {
        "model": name,
        "from": source,
        "stream": False,
    }
    if system:
        payload["system"] = system
    if isinstance(parameters, dict) and parameters:
        payload["parameters"] = parameters
    return {
        "port": port,
        "name": name,
        "source": source,
        "result": _post_json(
            _ollama_base(port) + "/api/create",
            payload,
            _bounded_int(args.get("timeout"), 300, 30, 900),
        ),
    }


def vscode_router_policy_get(args: dict[str, Any]) -> dict[str, Any]:
    path = V3_DIR / "config" / "vscode_router_policy.json"
    if not path.exists():
        return {"path": str(path), "exists": False, "policy": None}
    return {"path": str(path), "exists": True, "policy": json.loads(path.read_text())}


def vscode_router_policy_set(args: dict[str, Any]) -> dict[str, Any]:
    path = V3_DIR / "config" / "vscode_router_policy.json"
    policy = args.get("policy") or {
        "default": "xavi-vscode-agent",
        "fallback": "xavi-vscode-fast",
        "rules": [
            {"when": "selection_or_small_edit", "model": "xavi-vscode-fast"},
            {"when": "single_file_edit", "model": "xavi-vscode-balanced"},
            {"when": "multi_file_or_refactor", "model": "xavi-vscode-agent"},
            {"when": "repo_wide_or_architecture", "model": "xavi-vscode-deep"},
            {"when": "custom_xavi_behavior", "model": "xavi-vscode-copilot"},
        ],
    }
    backup = None
    if path.exists():
        backup = path.with_name(path.name + ".backup-dev-mcp-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
        backup.write_text(path.read_text())
    path.write_text(json.dumps(policy, indent=2) + "\n")
    return {"path": str(path), "backup": str(backup) if backup else None, "policy": policy}


def model_benchmark(args: dict[str, Any]) -> dict[str, Any]:
    port = str(args.get("port", "11434"))
    model = _model_name_ok(str(args.get("model", "qwen2.5-coder:xavi-agent")))
    prompt = str(args.get("prompt", "Write one concise sentence about runtime routing."))
    runs = _bounded_int(args.get("runs"), 2, 1, 5)
    num_predict = _bounded_int(args.get("num_predict"), 96, 8, 512)
    timeout = _bounded_int(args.get("timeout"), 180, 30, 600)
    results = []
    for _ in range(runs):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": num_predict},
        }
        results.append(_post_json(_ollama_base(port) + "/api/generate", payload, timeout))
    return {"port": port, "model": model, "runs": results}


def _mikrotik_bridge_call(argv: list[str], timeout: int = 90) -> dict[str, Any]:
    if not MIKROTIK_VENV_PYTHON.exists():
        raise RuntimeError(f"MikroTik bridge venv missing: {MIKROTIK_VENV_PYTHON}")
    if not MIKROTIK_BRIDGE.exists():
        raise RuntimeError(f"MikroTik bridge missing: {MIKROTIK_BRIDGE}")
    result = _run([str(MIKROTIK_VENV_PYTHON), str(MIKROTIK_BRIDGE), *argv], cwd=MIKROTIK_CWD, timeout=timeout)
    try:
        payload = json.loads(result.get("stdout") or "{}")
    except Exception:
        payload = {"ok": False, "error": "MikroTik bridge returned invalid JSON", "stdout": _trim(result.get("stdout") or "", 8000)}
    if isinstance(payload, dict):
        payload.setdefault("bridge_returncode", result.get("returncode"))
        if result.get("stderr"):
            payload.setdefault("bridge_stderr", _trim(result.get("stderr") or "", 4000))
        return payload
    return {"ok": False, "error": "MikroTik bridge payload was not an object", "bridge_returncode": result.get("returncode")}


def mikrotik_router_health(args: dict[str, Any]) -> dict[str, Any]:
    return _mikrotik_bridge_call(["health"], timeout=30)


def mikrotik_router_trust_host_key(args: dict[str, Any]) -> dict[str, Any]:
    return _mikrotik_bridge_call(["trust-host-key"], timeout=30)


def mikrotik_router_inventory(args: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "identity", "resource", "routerboard", "interfaces", "ethernet", "bridges", "bridge_ports",
        "interface_lists", "interface_list_members", "ip_addresses", "ipv6_addresses", "routes_v4", "routes_v6",
        "services", "dns", "dns_static", "firewall_filter", "firewall_nat", "users", "ssh", "neighbors",
    }
    raw = args.get("sections") or []
    if not isinstance(raw, list):
        raise ValueError("sections must be an array")
    sections = [str(item) for item in raw]
    unknown = [item for item in sections if item not in allowed]
    if unknown:
        raise ValueError(f"unsupported MikroTik inventory sections: {unknown}")
    argv = ["inventory"]
    if sections:
        argv += ["--sections", ",".join(sections)]
    return _mikrotik_bridge_call(argv, timeout=90)


def mikrotik_router_export(args: dict[str, Any]) -> dict[str, Any]:
    label = str(args.get("label", "mcp-snapshot"))
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", label):
        raise ValueError("invalid export label")
    return _mikrotik_bridge_call(["export", "--label", label], timeout=60)


def mikrotik_router_safe_apply(args: dict[str, Any]) -> dict[str, Any]:
    action = str(args.get("action", ""))
    allowed = {
        "identity_set", "interface_comment_set", "ip_address_ensure", "dns_static_ensure",
        "dns_static_remove", "service_source_set", "rule_enabled_set",
    }
    if action not in allowed:
        raise ValueError(f"unsupported MikroTik safe action: {action}")
    params = args.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("params must be an object")
    return _mikrotik_bridge_call(["safe-apply", "--action", action, "--params-json", json.dumps(params, separators=(",", ":"))], timeout=120)


def remote_node_health(args: dict[str, Any]) -> dict[str, Any]:
    requested_port = str(args.get("port", "")).strip()
    model = _model_name_ok(str(args.get("model", "qwen2.5-coder:7b")))
    payload = {
        "model": model,
        "prompt": "Reply exactly: NODE_READY",
        "stream": False,
        "options": {"num_predict": 16},
    }
    if requested_port:
        candidates = [("explicit-local-port", _ollama_base(requested_port), requested_port)]
    else:
        candidates = [
            ("dedicated-private-ethernet", "http://10.77.0.2:11434", "11434"),
            ("ssh-tunnel-fallback", "http://127.0.0.1:18205", "18205"),
        ]
    errors: list[dict[str, str]] = []
    for transport, base_url, port in candidates:
        try:
            return {
                "transport": transport,
                "base_url": base_url,
                "port": port,
                "fallback_used": transport == "ssh-tunnel-fallback",
                "tags": _fetch_json(base_url + "/api/tags", timeout=20),
                "probe": _post_json(base_url + "/api/generate", payload, 120),
            }
        except Exception as exc:
            errors.append({"transport": transport, "base_url": base_url, "error": str(exc)[:500]})
    raise RuntimeError("remote_node_health_failed:" + json.dumps(errors, separators=(",", ":")))


def remote_host_health(args: dict[str, Any]) -> dict[str, Any]:
    node_id = str(args.get("node", "")).strip()
    config_path = Path("/var/www/xavi/xavi-stack-manager/config/stack.json")
    if not config_path.exists():
        raise RuntimeError("stack manager config missing")
    config = json.loads(config_path.read_text())
    spec = next((row for row in config.get("remote_nodes", []) if str(row.get("id")) == node_id), None)
    if spec is None:
        raise ValueError(f"unknown remote node: {node_id}")
    transport = spec.get("transport") or {}
    target = str(transport.get("private_ssh_target") or spec.get("ssh_target") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,255}", target):
        raise ValueError("invalid SSH target")
    connect_timeout = _bounded_int(transport.get("connect_timeout"), 6, 2, 15)
    script = r'''import json, os, shutil, socket, subprocess

def run(argv, timeout=5):
    try:
        p=subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)
        return {"rc":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip()[:300]}
    except Exception as exc:
        return {"rc":-1,"stdout":"","stderr":f"{type(exc).__name__}: {exc}"}

mem={}
try:
    for line in open("/proc/meminfo"):
        k,v=line.split(":",1); mem[k]=int(v.strip().split()[0])*1024
except Exception: pass
try: load=[float(x) for x in open("/proc/loadavg").read().split()[:3]]
except Exception: load=[]
engines={}
for name in ("podman","docker"):
    engines[name]={"installed":bool(shutil.which(name))}
    if engines[name]["installed"]:
        engines[name]["info_rc"]=run([name,"info"],5)["rc"]
libvirt={"installed":bool(shutil.which("virsh")),"domains":[]}
if libvirt["installed"]:
    r=run(["virsh","list","--all","--name"],6)
    if r["rc"]==0: libvirt["domains"]=[x for x in r["stdout"].splitlines() if x]
gpus=[]
if shutil.which("nvidia-smi"):
    r=run(["nvidia-smi","--query-gpu=name,memory.total,memory.free,utilization.gpu","--format=csv,noheader,nounits"],6)
    if r["rc"]==0: gpus=[x for x in r["stdout"].splitlines() if x]
print(json.dumps({"hostname":socket.gethostname(),"cpu":{"logical":os.cpu_count() or 1,"load":load},"memory":{"total_bytes":mem.get("MemTotal",0),"available_bytes":mem.get("MemAvailable",0)},"container_engines":engines,"libvirt":libvirt,"gpus":gpus,"nftables":{"installed":bool(shutil.which("nft"))},"addresses":run(["ip","-br","addr"],5)["stdout"]},sort_keys=True))'''
    result = _run([
        "ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={connect_timeout}",
        "-o", "ServerAliveInterval=5", target,
        "python3 -c " + shlex.quote(script),
    ], cwd=Path("/var/www/xavi"), timeout=max(18, connect_timeout + 14))
    payload: Any = None
    if result.get("returncode") == 0:
        try:
            payload = json.loads(result.get("stdout") or "")
        except Exception:
            payload = {"raw": (result.get("stdout") or "")[:1000]}
    return {
        "node": node_id,
        "title": spec.get("title"),
        "target": target,
        "reachable": result.get("returncode") == 0,
        "duration_ms": result.get("duration_ms"),
        "transport": transport,
        "roles": spec.get("roles") or [],
        "scheduler_eligible": spec.get("scheduler_eligible", True),
        "container_policy": spec.get("container_policy") or {},
        "observed": payload,
        "error": None if result.get("returncode") == 0 else ((result.get("stderr") or result.get("stdout") or "SSH probe failed").strip()[:1000]),
    }


def repo_index_snapshot(args: dict[str, Any]) -> dict[str, Any]:
    root = _safe_path(str(args.get("path", str(REPO_ROOT))))
    max_files = _bounded_int(args.get("max_files"), 8000, 100, 50000)
    skip = {".git", "node_modules", ".venv", "__pycache__", "data", ".pytest_cache", ".mypy_cache"}
    counts: dict[str, int] = {}
    total = 0
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            total += 1
            ext = Path(f).suffix or "<none>"
            counts[ext] = counts.get(ext, 0) + 1
            if total >= max_files:
                return {"root": str(root), "truncated": True, "files_seen": total, "extensions": counts}
    return {"root": str(root), "truncated": False, "files_seen": total, "extensions": counts}


def cpu_worker_policy_get(args: dict[str, Any]) -> dict[str, Any]:
    path = V3_DIR / "config" / "cpu_worker_policy.json"
    if not path.exists():
        return {"path": str(path), "exists": False, "policy": None}
    return {"path": str(path), "exists": True, "policy": json.loads(path.read_text())}


def cpu_worker_policy_set(args: dict[str, Any]) -> dict[str, Any]:
    path = V3_DIR / "config" / "cpu_worker_policy.json"
    policy = args.get("policy") or {
        "node": "tbi-production-3",
        "role": "ryzen-5950x-cpu-worker",
        "preferred_tasks": [
            "embedding",
            "repo_indexing",
            "reranking",
            "batch_summaries",
            "small_quantized_fallback",
        ],
        "ollama_url": "http://10.77.0.2:11434",
        "ollama_host": "10.77.0.2",
        "ollama_port": "11434",
        "fallback_ollama_url": "http://127.0.0.1:18205",
        "transport": "dedicated-private-ethernet",
        "notes": "Direct private Ollama is primary; localhost:18205 is rollback/fallback only.",
    }
    backup = None
    if path.exists():
        backup = path.with_name(path.name + ".backup-dev-mcp-" + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
        backup.write_text(path.read_text())
    path.write_text(json.dumps(policy, indent=2) + "\n")
    return {"path": str(path), "backup": str(backup) if backup else None, "policy": policy}


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"commands": {}}
    return json.loads(REGISTRY_PATH.read_text())


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n")


def bounded_command_creator(args: dict[str, Any]) -> dict[str, Any]:
    name = str(args.get("name", "")).strip()
    if not re.match(r"^[A-Za-z0-9_.-]{3,80}$", name):
        raise ValueError("name must be 3-80 chars of letters/numbers/underscore/dot/dash")
    argv = args.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
        raise ValueError("argv must be a non-empty list of strings")
    if len(argv) > 64:
        raise ValueError("argv too long")
    cwd = str(_safe_path(str(args.get("cwd", str(REPO_ROOT)))))
    timeout = _bounded_int(args.get("timeout"), 120, 1, 1800)
    resources = args.get("resources") or []
    if not isinstance(resources, list) or not all(isinstance(value, str) and value.strip() for value in resources):
        raise ValueError("resources must be an array of non-empty strings")
    resources = list(dict.fromkeys(value.strip()[:1200] for value in resources))[:100]
    mutating = args.get("mutating")
    if mutating is not None and not isinstance(mutating, bool):
        raise ValueError("mutating must be boolean when provided")
    project_key = str(args.get("project_key", "xavi.app-backend")).strip() or "xavi.app-backend"
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$", project_key):
        raise ValueError("invalid project_key")
    work_title = str(args.get("work_title", args.get("title", name))).strip()[:240]

    data = _load_registry()
    data.setdefault("commands", {})[name] = {
        "title": str(args.get("title", name)),
        "description": str(args.get("description", "Bounded runtime command.")),
        "argv": argv,
        "cwd": cwd,
        "timeout": timeout,
        "mutating": mutating,
        "resources": resources,
        "project_key": project_key,
        "work_title": work_title,
    }
    _save_registry(data)
    return {"ok": True, "path": str(REGISTRY_PATH), "name": name, "command": data["commands"][name]}


def bounded_command_list(args: dict[str, Any]) -> dict[str, Any]:
    data = _load_registry()
    commands = data.get("commands", {}) if isinstance(data, dict) else {}
    query = str(args.get("query", "")).strip().lower()
    limit = _bounded_int(args.get("limit"), 50, 1, 200)
    include_argv = bool(args.get("include_argv", False))

    items = []
    for name in sorted(commands):
        cmd = commands[name] or {}
        haystack = " ".join([
            name,
            str(cmd.get("title", "")),
            str(cmd.get("description", "")),
        ]).lower()
        if query and query not in haystack:
            continue
        item = {
            "name": name,
            "title": cmd.get("title", name),
            "description": cmd.get("description", ""),
            "cwd": cmd.get("cwd"),
            "timeout": cmd.get("timeout"),
            "mutating": cmd.get("mutating"),
            "resources": cmd.get("resources", []),
            "project_key": cmd.get("project_key", "xavi.app-backend"),
            "work_title": cmd.get("work_title", cmd.get("title", name)),
        }
        if include_argv:
            item["argv"] = cmd.get("argv", [])
        else:
            item["argv_count"] = len(cmd.get("argv", []) or [])
        items.append(item)
        if len(items) >= limit:
            break

    return {
        "path": str(REGISTRY_PATH),
        "count": len(commands),
        "returned": len(items),
        "truncated": len(items) < len([n for n, cmd in commands.items() if not query or query in " ".join([n, str((cmd or {}).get("title", "")), str((cmd or {}).get("description", ""))]).lower()]),
        "query": query or None,
        "include_argv": include_argv,
        "commands": items,
    }


def bounded_command_run(args: dict[str, Any]) -> dict[str, Any]:
    name = str(args.get("name", "")).strip()
    params = args.get("params") or {}
    data = _load_registry()
    cmd = data.get("commands", {}).get(name)
    if not cmd:
        raise ValueError(f"unknown bounded command: {name}")
    argv = []
    for token in cmd["argv"]:
        value = token
        for k, v in params.items():
            value = value.replace("{" + str(k) + "}", str(v))
        argv.append(value)
    cwd = _safe_path(cmd.get("cwd", str(REPO_ROOT)))
    timeout = _bounded_int(args.get("timeout", cmd.get("timeout", 120)), cmd.get("timeout", 120), 1, 1800)
    return {"name": name, "result": _run(argv, cwd, timeout)}


def _owner_memory_store():
    from xavi_owner_memory import OwnerMemory
    return OwnerMemory()


def owner_memory_put(args: dict[str, Any]) -> dict[str, Any]:
    return _owner_memory_store().put(args)


def owner_memory_get(args: dict[str, Any]) -> dict[str, Any]:
    return _owner_memory_store().get(args)


def owner_memory_search(args: dict[str, Any]) -> dict[str, Any]:
    return _owner_memory_store().search(args)


def owner_memory_list(args: dict[str, Any]) -> dict[str, Any]:
    return _owner_memory_store().list(args)


EXT_TOOLS = [
    {
        "name": "ollama_copy_tag",
        "title": "Ollama Copy Tag",
        "description": "Copy an allowlisted Ollama model tag on an allowlisted port.",
        "inputSchema": {
            "type": "object",
            "properties": {"port": {"type": "string"}, "source": {"type": "string"}, "destination": {"type": "string"}},
            "required": ["source", "destination"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ollama_create_tag",
        "title": "Ollama Create Tag",
        "description": "Create an allowlisted Ollama model tag from a base model with optional system prompt/parameters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "port": {"type": "string"},
                "name": {"type": "string"},
                "source": {"type": "string"},
                "system": {"type": "string"},
                "parameters": {"type": "object"},
                "timeout": {"type": "integer"},
            },
            "required": ["name", "source"],
            "additionalProperties": False,
        },
    },
    {
        "name": "vscode_router_policy_get",
        "title": "VS Code Router Policy Get",
        "description": "Read runtime v3 VS Code auto-router policy.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "vscode_router_policy_set",
        "title": "VS Code Router Policy Set",
        "description": "Write runtime v3 VS Code auto-router policy.",
        "inputSchema": {"type": "object", "properties": {"policy": {"type": "object"}}, "additionalProperties": False},
    },
    {
        "name": "model_benchmark",
        "title": "Model Benchmark",
        "description": "Run a small bounded Ollama benchmark probe.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "port": {"type": "string"},
                "model": {"type": "string"},
                "prompt": {"type": "string"},
                "runs": {"type": "integer"},
                "num_predict": {"type": "integer"},
                "timeout": {"type": "integer"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "remote_node_health",
        "title": "Remote Node Health",
        "description": "Probe the RTX Ollama node over dedicated private Ethernet first, with localhost:18205 SSH-tunnel fallback; an explicit port overrides automatic selection.",
        "inputSchema": {
            "type": "object",
            "properties": {"port": {"type": "string"}, "model": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "mikrotik_router_health",
        "title": "MikroTik Router Health",
        "description": "Check the pinned RB4011 RouterOS SSH management path using the dedicated Xavi key and return identity/resource status. Read-only.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "mikrotik_router_trust_host_key",
        "title": "MikroTik Trust Host Key",
        "description": "Fetch and pin the RB4011 SSH host key into Xavi's dedicated known-hosts file. Does not change RouterOS configuration.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "mikrotik_router_inventory",
        "title": "MikroTik Router Inventory",
        "description": "Read allowlisted RouterOS inventory sections such as interfaces, addresses, routes, DNS, services and firewall state. No arbitrary RouterOS command execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sections": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["identity", "resource", "routerboard", "interfaces", "ethernet", "bridges", "bridge_ports", "interface_lists", "interface_list_members", "ip_addresses", "ipv6_addresses", "routes_v4", "routes_v6", "services", "dns", "dns_static", "firewall_filter", "firewall_nat", "users", "ssh", "neighbors"]},
                    "maxItems": 21
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "mikrotik_router_export",
        "title": "MikroTik Router Export",
        "description": "Create a local sanitized RouterOS configuration export with SHA-256 for audit/rollback planning. Sensitive values are hidden/redacted.",
        "inputSchema": {"type": "object", "properties": {"label": {"type": "string", "pattern": "^[A-Za-z0-9_.-]{1,64}$"}}, "additionalProperties": False},
    },
    {
        "name": "mikrotik_router_safe_apply",
        "title": "MikroTik Router Safe Apply",
        "description": "Apply one predefined RouterOS mutation inside Safe Mode with sanitized pre/post exports; automatically roll back if the management session drops or RouterOS rejects the action. No raw command input.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["identity_set", "interface_comment_set", "ip_address_ensure", "dns_static_ensure", "dns_static_remove", "service_source_set", "rule_enabled_set"]},
                "params": {"type": "object"}
            },
            "required": ["action", "params"],
            "additionalProperties": False,
        },
    },
    {
        "name": "remote_host_health",
        "title": "Remote Host Health",
        "description": "Probe any registered Xavi remote host by node ID over its allowlisted SSH target and return bounded CPU, memory, container-engine, libvirt, GPU, nftables and address state; does not provide an arbitrary remote shell.",
        "inputSchema": {
            "type": "object",
            "properties": {"node": {"type": "string"}},
            "required": ["node"],
            "additionalProperties": False,
        },
    },
    {
        "name": "repo_index_snapshot",
        "title": "Repo Index Snapshot",
        "description": "Summarize repository file extensions for CPU/indexing planning.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "max_files": {"type": "integer"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "cpu_worker_policy_get",
        "title": "CPU Worker Policy Get",
        "description": "Read CPU worker policy for Ryzen 5950X/background tasks.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "cpu_worker_policy_set",
        "title": "CPU Worker Policy Set",
        "description": "Write CPU worker policy for Ryzen 5950X/background tasks.",
        "inputSchema": {"type": "object", "properties": {"policy": {"type": "object"}}, "additionalProperties": False},
    },
    {
        "name": "bounded_command_creator",
        "title": "Bounded Command Creator",
        "description": "Register a named argv-template command in config/bounded_commands.json.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "argv": {"type": "array", "items": {"type": "string"}},
                "cwd": {"type": "string"},
                "timeout": {"type": "integer"},
                "mutating": {"type": "boolean"},
                "resources": {"type": "array", "items": {"type": "string"}},
                "project_key": {"type": "string"},
                "work_title": {"type": "string"},
            },
            "required": ["name", "argv"],
            "additionalProperties": False,
        },
    },
    {
        "name": "bounded_command_list",
        "title": "Bounded Command List",
        "description": "List registered bounded commands with compact output by default.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "include_argv": {"type": "boolean"}
            },
            "additionalProperties": False
        },
    },
    {
        "name": "bounded_command_run",
        "title": "Bounded Command Run",
        "description": "Run a registered bounded command by name with optional placeholder params.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "params": {"type": "object"}, "timeout": {"type": "integer"}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
]

EXT_TOOLS.extend([
    {
        "name": "owner_memory_put",
        "title": "Owner Memory Put",
        "description": "Store or update owner knowledge, including restricted credentials/secrets, encrypted at rest. The normal MCP ledger records only metadata/digests for this tool. Restricted records default to recurrent-memory/retrieval/task-execution learning rather than parameter training.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "default": "owner"},
                "label": {"type": "string"},
                "kind": {"type": "string", "enum": ["secret","credential","fact","preference","identity","procedure","source","other"]},
                "value": {},
                "privacy_class": {"type": "string", "enum": ["public","internal","private","restricted"]},
                "retention_class": {"type": "string", "enum": ["ephemeral","bounded","audit","release","owner"]},
                "learning_modes": {"type": "array", "items": {"type": "string", "enum": ["recurrent_memory","retrieval","task_execution","parameter_training","heldout_eval"]}},
                "source": {"type": "object"},
                "metadata": {"type": "object"}
            },
            "required": ["label","value"],
            "additionalProperties": False
        }
    },
    {
        "name": "owner_memory_get",
        "title": "Owner Memory Get",
        "description": "Retrieve and decrypt one owner-knowledge item for autonomous Xavi/WG-RNN use. Plaintext is returned to the authenticated caller but excluded from ordinary MCP ledger payloads.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "knowledge_id": {"type": "string"},
                "namespace": {"type": "string", "default": "owner"},
                "label": {"type": "string"}
            },
            "additionalProperties": False
        }
    },
    {
        "name": "owner_memory_search",
        "title": "Owner Memory Search",
        "description": "Search owner-memory metadata and provenance without decrypting values.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "namespace": {"type": "string"},
                "kind": {"type": "string", "enum": ["secret","credential","fact","preference","identity","procedure","source","other"]},
                "privacy_class": {"type": "string", "enum": ["public","internal","private","restricted"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
            },
            "additionalProperties": False
        }
    },
    {
        "name": "owner_memory_list",
        "title": "Owner Memory List",
        "description": "List owner-memory metadata/provenance without decrypting values.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "kind": {"type": "string", "enum": ["secret","credential","fact","preference","identity","procedure","source","other"]},
                "privacy_class": {"type": "string", "enum": ["public","internal","private","restricted"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}
            },
            "additionalProperties": False
        }
    }
])

HANDLERS = {
    "ollama_copy_tag": ollama_copy_tag,
    "ollama_create_tag": ollama_create_tag,
    "vscode_router_policy_get": vscode_router_policy_get,
    "vscode_router_policy_set": vscode_router_policy_set,
    "model_benchmark": model_benchmark,
    "remote_node_health": remote_node_health,
    "mikrotik_router_health": mikrotik_router_health,
    "mikrotik_router_trust_host_key": mikrotik_router_trust_host_key,
    "mikrotik_router_inventory": mikrotik_router_inventory,
    "mikrotik_router_export": mikrotik_router_export,
    "mikrotik_router_safe_apply": mikrotik_router_safe_apply,
    "remote_host_health": remote_host_health,
    "repo_index_snapshot": repo_index_snapshot,
    "cpu_worker_policy_get": cpu_worker_policy_get,
    "cpu_worker_policy_set": cpu_worker_policy_set,
    "bounded_command_creator": bounded_command_creator,
    "bounded_command_list": bounded_command_list,
    "bounded_command_run": bounded_command_run,
    "owner_memory_put": owner_memory_put,
    "owner_memory_get": owner_memory_get,
    "owner_memory_search": owner_memory_search,
    "owner_memory_list": owner_memory_list,
}


def handle_ext_tool(name: str, args: dict[str, Any]) -> tuple[bool, Any]:
    handler = HANDLERS.get(name)
    if not handler:
        return False, None
    return True, handler(args or {})

# ---- Async bounded command jobs ----

import signal
import uuid

JOBS_DIR = V3_DIR / "data" / "bounded_jobs"


def _jobs_dir() -> Path:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    return JOBS_DIR


def _job_paths(job_id: str) -> dict[str, Path]:
    root = _jobs_dir() / job_id
    return {
        "root": root,
        "meta": root / "meta.json",
        "stdout": root / "stdout.log",
        "stderr": root / "stderr.log",
    }


def _read_job_meta(job_id: str) -> dict[str, Any]:
    paths = _job_paths(job_id)
    if not paths["meta"].exists():
        raise ValueError(f"unknown job_id: {job_id}")
    return json.loads(paths["meta"].read_text())


def _write_job_meta(job_id: str, meta: dict[str, Any]) -> None:
    paths = _job_paths(job_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["meta"].write_text(json.dumps(meta, indent=2) + "\n")


def _resolve_registered_command(name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    name = str(name or "").strip()
    params = params or {}
    data = _load_registry()
    cmd = data.get("commands", {}).get(name)
    if not cmd:
        raise ValueError(f"unknown bounded command: {name}")

    argv = []
    for token in cmd["argv"]:
        value = str(token)
        for k, v in params.items():
            value = value.replace("{" + str(k) + "}", str(v))
        argv.append(value)

    cwd = str(_safe_path(cmd.get("cwd", str(REPO_ROOT))))
    timeout = _bounded_int(cmd.get("timeout"), 120, 1, 1800)
    return {
        "name": name,
        "title": cmd.get("title", name),
        "description": cmd.get("description", ""),
        "argv": argv,
        "cwd": cwd,
        "timeout": timeout,
        "mutating": cmd.get("mutating"),
        "resources": cmd.get("resources", []),
        "project_key": cmd.get("project_key", "xavi.app-backend"),
        "work_title": cmd.get("work_title", cmd.get("title", name)),
    }



def _pid_alive_for_job(pid: int) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists():
            parts = stat.read_text(errors="replace").split()
            if len(parts) >= 3 and parts[2] == "Z":
                return False
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return False


def _write_job_meta_atomic(job_id: str, meta: dict[str, Any]) -> None:
    paths = _job_paths(job_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    tmp = paths["meta"].with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, indent=2) + "\n")
    tmp.replace(paths["meta"])


def _async_job_supervisor_code() -> str:
    return r"""
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

job_id = sys.argv[1]
jobs_dir = Path(os.environ["XAVI_BOUNDED_JOBS_DIR"])
paths = {
    "root": jobs_dir / job_id,
    "meta": jobs_dir / job_id / "meta.json",
    "stdout": jobs_dir / job_id / "stdout.log",
    "stderr": jobs_dir / job_id / "stderr.log",
}

child = None
finished = False

def utc_now():
    return datetime.utcnow().isoformat() + "Z"

def read_meta():
    return json.loads(paths["meta"].read_text())

def write_meta(meta):
    tmp = paths["meta"].with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, indent=2) + "\n")
    tmp.replace(paths["meta"])

def update_meta(**updates):
    meta = read_meta()
    meta.update(updates)
    write_meta(meta)
    return meta

def kill_child():
    global child
    if child is None:
        return
    try:
        os.killpg(os.getpgid(child.pid), signal.SIGTERM)
    except Exception:
        pass
    try:
        child.wait(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(child.pid), signal.SIGKILL)
        except Exception:
            pass

def handle_term(signum, frame):
    global finished
    if finished:
        return
    finished = True
    kill_child()
    try:
        update_meta(status="killed", returncode=-signal.SIGTERM, finished_at=utc_now())
    finally:
        raise SystemExit(128 + signal.SIGTERM)

signal.signal(signal.SIGTERM, handle_term)
signal.signal(signal.SIGINT, handle_term)

# Wait for parent to write supervisor pid/status after spawning us.
deadline = time.time() + 10
while time.time() < deadline:
    meta = read_meta()
    if meta.get("pid") and meta.get("status") == "running":
        break
    time.sleep(0.05)
else:
    meta = read_meta()

argv = meta["argv"]
cwd = meta["cwd"]
timeout = int(meta.get("timeout", 120))

try:
    with paths["stdout"].open("ab", buffering=0) as out, paths["stderr"].open("ab", buffering=0) as err:
        child = subprocess.Popen(
            argv,
            cwd=cwd,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
        update_meta(child_pid=child.pid, child_started_at=utc_now())

        try:
            rc = child.wait(timeout=timeout)
            finished = True
            status = "exited" if rc == 0 else "failed"
            update_meta(status=status, returncode=rc, finished_at=utc_now())
        except subprocess.TimeoutExpired:
            finished = True
            kill_child()
            update_meta(status="timeout_killed", returncode=-signal.SIGKILL, finished_at=utc_now())
except BaseException as e:
    if not finished:
        try:
            update_meta(status="supervisor_error", returncode=1, error=repr(e), finished_at=utc_now())
        except Exception:
            pass
    raise
"""

def bounded_job_start(args: dict[str, Any]) -> dict[str, Any]:
    command_name = str(args.get("name", "")).strip()
    params = args.get("params") or {}
    resolved = _resolve_registered_command(command_name, params)

    timeout = _bounded_int(args.get("timeout", resolved["timeout"]), resolved["timeout"], 1, 1800)
    job_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    paths = _job_paths(job_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["stdout"].write_bytes(b"")
    paths["stderr"].write_bytes(b"")

    meta = {
        "job_id": job_id,
        "name": command_name,
        "title": resolved["title"],
        "description": resolved["description"],
        "argv": resolved["argv"],
        "cwd": resolved["cwd"],
        "timeout": timeout,
        "pid": None,
        "child_pid": None,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "status": "starting",
        "returncode": None,
        "stdout_path": str(paths["stdout"]),
        "stderr_path": str(paths["stderr"]),
    }
    _write_job_meta_atomic(job_id, meta)

    py = V3_DIR / ".venv" / "bin" / "python"
    python_exe = str(py if py.exists() else "python3")
    env = os.environ.copy()
    env["XAVI_BOUNDED_JOBS_DIR"] = str(_jobs_dir())

    proc = subprocess.Popen(
        [python_exe, "-c", _async_job_supervisor_code(), job_id],
        cwd=str(V3_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    meta["pid"] = proc.pid
    meta["status"] = "running"
    meta["supervisor_pid"] = proc.pid
    _write_job_meta_atomic(job_id, meta)

    return {
        "ok": True,
        "job_id": job_id,
        "status": "running",
        "pid": proc.pid,
        "name": command_name,
        "stdout_path": str(paths["stdout"]),
        "stderr_path": str(paths["stderr"]),
    }


def bounded_job_status(args: dict[str, Any]) -> dict[str, Any]:
    job_id = str(args.get("job_id", "")).strip()
    meta = _read_job_meta(job_id)

    if meta.get("status") in {"starting", "running"}:
        pid = meta.get("pid")
        if pid is not None:
            pid = int(pid)
            still_running = _pid_alive_for_job(pid)

            started = datetime.fromisoformat(meta["started_at"].replace("Z", ""))
            elapsed = (datetime.utcnow() - started).total_seconds()
            timeout = int(meta.get("timeout", 120))

            if still_running and elapsed > timeout + 10:
                child_pid = meta.get("child_pid")
                if child_pid:
                    try:
                        os.killpg(os.getpgid(int(child_pid)), signal.SIGTERM)
                    except Exception:
                        pass
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except Exception:
                    pass
                meta["status"] = "timeout_killed"
                meta["returncode"] = -signal.SIGKILL
                meta["finished_at"] = datetime.utcnow().isoformat() + "Z"
                _write_job_meta_atomic(job_id, meta)
            elif not still_running:
                # Supervisor is gone. If it did not record a terminal state,
                # mark it explicitly instead of leaving it stuck as running.
                latest = _read_job_meta(job_id)
                if latest.get("status") in {"starting", "running"}:
                    latest["status"] = "orphaned"
                    latest["finished_at"] = datetime.utcnow().isoformat() + "Z"
                    _write_job_meta_atomic(job_id, latest)
                meta = latest

    return meta


def bounded_job_output(args: dict[str, Any]) -> dict[str, Any]:
    job_id = str(args.get("job_id", "")).strip()
    limit = _bounded_int(args.get("limit"), 60000, 1000, 250000)
    meta = bounded_job_status({"job_id": job_id})
    paths = _job_paths(job_id)

    stdout = paths["stdout"].read_text(errors="replace") if paths["stdout"].exists() else ""
    stderr = paths["stderr"].read_text(errors="replace") if paths["stderr"].exists() else ""

    return {
        "job_id": job_id,
        "status": meta.get("status"),
        "stdout": stdout[-limit:],
        "stderr": stderr[-limit:],
        "stdout_truncated": len(stdout) > limit,
        "stderr_truncated": len(stderr) > limit,
        "meta": meta,
    }


def bounded_job_kill(args: dict[str, Any]) -> dict[str, Any]:
    job_id = str(args.get("job_id", "")).strip()
    meta = _read_job_meta(job_id)
    pid = int(meta["pid"])

    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        killed = True
    except ProcessLookupError:
        killed = False

    meta["status"] = "killed" if killed else "not_running"
    meta["finished_at"] = datetime.utcnow().isoformat() + "Z"
    _write_job_meta(job_id, meta)

    return {"job_id": job_id, "killed": killed, "status": meta["status"]}


ASYNC_JOB_TOOLS = [
    {
        "name": "bounded_job_start",
        "title": "Bounded Job Start",
        "description": "Start a registered bounded command asynchronously and return a job id immediately.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "params": {"type": "object"},
                "timeout": {"type": "integer"}
            },
            "required": ["name"],
            "additionalProperties": False
        },
    },
    {
        "name": "bounded_job_status",
        "title": "Bounded Job Status",
        "description": "Check status for an async bounded command job.",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
            "additionalProperties": False
        },
    },
    {
        "name": "bounded_job_output",
        "title": "Bounded Job Output",
        "description": "Read bounded stdout/stderr for an async bounded command job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["job_id"],
            "additionalProperties": False
        },
    },
    {
        "name": "bounded_job_kill",
        "title": "Bounded Job Kill",
        "description": "Terminate an async bounded command job.",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
            "additionalProperties": False
        },
    },
]

# Remove the bad synchronous runner from extension tool list.
EXT_TOOLS[:] = [t for t in EXT_TOOLS if t.get("name") != "bounded_command_run"]
HANDLERS.pop("bounded_command_run", None)

EXT_TOOLS.extend(ASYNC_JOB_TOOLS)
HANDLERS.update({
    "bounded_job_start": bounded_job_start,
    "bounded_job_status": bounded_job_status,
    "bounded_job_output": bounded_job_output,
    "bounded_job_kill": bounded_job_kill,
})

# ---- End async bounded command jobs ----
