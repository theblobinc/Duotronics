#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import queue
import re
import subprocess
import tempfile
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlsplit

from fastapi import Body, FastAPI, Request
from xavi_mcp_coordination import (
    classify_and_infer, conflict_summary, digest as coordination_digest,
    inject_identity as coordination_inject_identity, prioritize_tools as coordination_prioritize_tools,
    resolve_session as coordination_resolve_session, session_context as coordination_session_context,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "xavi-runtime-v3-dev-mcp"
SERVER_VERSION = "0.3.0-fastpath"

V3_DIR = Path(os.environ.get(
    "XAVI_OPS_RUNTIME_DIR",
    "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
)).resolve()

REPO_ROOT = Path(os.environ.get("XAVI_OPS_REPO_ROOT", "/var/www/xavi/Duotronics")).resolve()
OPS_URL = os.environ.get("XAVI_OPS_URL", "http://127.0.0.1:8091").replace("host.containers.internal", "127.0.0.1").rstrip("/")
OPS_KEY = os.environ.get("XAVI_OPS_API_KEY", "")
RUNTIME_MCP_KEY = os.environ.get("XAVI_MCP_API_KEY", "")
RUNTIME_URL = os.environ.get("XAVI_RUNTIME_URL", "http://127.0.0.1:8080").rstrip("/")
SESSION_SECRET = os.environ.get("XAVI_MCP_SESSION_SECRET") or OPS_KEY or RUNTIME_MCP_KEY or hashlib.sha256(str(V3_DIR).encode()).hexdigest()
SESSION_CLIENTS: dict[str, dict[str, Any]] = {}

# Fast-path tuning. These defaults keep coordination semantics while moving
# observational bookkeeping off the tool-call response path.
TOOLS_CACHE_TTL = max(1.0, float(os.environ.get("XAVI_MCP_TOOLS_CACHE_TTL", "15")))
COLLAB_REFRESH_TTL = max(1.0, float(os.environ.get("XAVI_MCP_COLLAB_REFRESH_TTL", "5")))
LEDGER_QUEUE_MAX = max(128, int(os.environ.get("XAVI_MCP_LEDGER_QUEUE_MAX", "4096")))
COLLAB_QUEUE_MAX = max(16, int(os.environ.get("XAVI_MCP_COLLAB_QUEUE_MAX", "256")))
PEER_SYNC_LIMIT = max(1, min(int(os.environ.get("XAVI_MCP_PEER_SYNC_LIMIT", "12")), 40))
RUN_FIXED_OUTPUT_BYTES = max(65536, min(int(os.environ.get("XAVI_MCP_RUN_FIXED_OUTPUT_BYTES", "1048576")), 16777216))

_HTTP_LOCAL = threading.local()
_RUNTIME_TOOLS_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_MERGED_TOOLS_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_TOOLS_CACHE_LOCK = threading.RLock()
_LEDGER_QUEUE: queue.Queue[tuple[Any, str, str, dict[str, Any], list[str] | None]] = queue.Queue(maxsize=LEDGER_QUEUE_MAX)
_LEDGER_WORKER_LOCK = threading.Lock()
_LEDGER_WORKER_STARTED = False
_COLLAB_QUEUE: queue.Queue[tuple[str, Any, str, dict[str, Any] | None]] = queue.Queue(maxsize=COLLAB_QUEUE_MAX)
_COLLAB_WORKER_LOCK = threading.Lock()
_COLLAB_WORKER_STARTED = False
_COLLAB_STATE_LOCK = threading.RLock()
_COLLAB_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_COLLAB_LAST_SCHEDULED: dict[str, float] = {}
_COLLAB_INFLIGHT: set[str] = set()

app = FastAPI(title="Xavi Runtime v3 Developer MCP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatgpt.com", "https://chat.openai.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "MCP-Protocol-Version", "Mcp-Session-Id", "X-Xavi-Agent-Id", "X-Xavi-Device-Id"],
    expose_headers=["Mcp-Session-Id"],
)

@app.middleware("http")
async def mcp_session_middleware(request: Request, call_next):
    session_id = coordination_resolve_session(request, SESSION_SECRET)
    request.state.xavi_session_id = session_id
    response = await call_next(request)
    response.headers["Mcp-Session-Id"] = session_id
    response.set_cookie("xavi_mcp_session", session_id, httponly=True, secure=True, samesite="lax", max_age=7 * 24 * 3600)
    return response

def rpc_result(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}

def rpc_error(req_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}

def _http_connection(base_url: str, timeout: float) -> tuple[http.client.HTTPConnection, str]:
    """Return a thread-local keep-alive connection and the base path.

    The adapter previously used urllib.request.urlopen for every RPC, which
    created a fresh connection each time. A thread-local HTTP/1.1 connection is
    safe for FastAPI's worker threads and automatically reconnects on failure.
    """
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"unsupported internal URL: {base_url}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    key = f"{parsed.scheme}://{parsed.hostname}:{port}"
    connections = getattr(_HTTP_LOCAL, "connections", None)
    if connections is None:
        connections = {}
        _HTTP_LOCAL.connections = connections
    conn = connections.get(key)
    if conn is None:
        cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        conn = cls(parsed.hostname, port, timeout=timeout)
        connections[key] = conn
    else:
        conn.timeout = timeout
        if getattr(conn, "sock", None) is not None:
            try:
                conn.sock.settimeout(timeout)
            except Exception:
                pass
    return conn, parsed.path.rstrip("/")


def _drop_http_connection(base_url: str) -> None:
    try:
        parsed = urlsplit(base_url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        key = f"{parsed.scheme}://{parsed.hostname}:{port}"
        connections = getattr(_HTTP_LOCAL, "connections", {})
        conn = connections.pop(key, None)
        if conn is not None:
            conn.close()
    except Exception:
        pass


def _http_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: Any = None,
    headers: dict[str, str] | None = None,
    timeout: float = 15,
) -> Any:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request_headers = dict(headers or {})
    if body is not None:
        request_headers.setdefault("content-type", "application/json")
        request_headers.setdefault("content-length", str(len(body)))
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            conn, base_path = _http_connection(base_url, timeout)
            target = (base_path + "/" + path.lstrip("/")) or "/"
            conn.request(method, target, body=body, headers=request_headers)
            response = conn.getresponse()
            raw = response.read()
            if response.will_close:
                _drop_http_connection(base_url)
            if not 200 <= response.status < 300:
                raise RuntimeError(f"HTTP {response.status} from {base_url}{target}: {raw[:500].decode(errors='replace')}")
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
        except (OSError, ConnectionError, http.client.HTTPException) as exc:
            last_error = exc
            _drop_http_connection(base_url)
            if attempt == 0:
                continue
            raise
    if last_error is not None:
        raise last_error
    raise RuntimeError("internal HTTP request failed")


def fetch_json(url: str, timeout: int = 15) -> Any:
    parsed = urlsplit(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return _http_json(base, path, timeout=timeout)


def runtime_mcp_rpc(method: str, params: dict[str, Any] | None = None, timeout: int = 30, auth_header: str | None = None, session_id: str | None = None, agent_id: str | None = None) -> dict[str, Any]:
    headers: dict[str, str] = {}
    if auth_header:
        headers["authorization"] = auth_header
    elif RUNTIME_MCP_KEY:
        headers["x-xavi-mcp-key"] = RUNTIME_MCP_KEY
    if session_id:
        headers["mcp-session-id"] = str(session_id)[:200]
    if agent_id:
        headers["x-xavi-agent-id"] = str(agent_id)[:200]
    result = _http_json(
        RUNTIME_URL,
        "/mcp",
        method="POST",
        payload={"jsonrpc": "2.0", "id": method, "method": method, "params": params or {}},
        headers=headers,
        timeout=timeout,
    )
    return result if isinstance(result, dict) else {}


def _runtime_health_reachable(timeout: float = 2.0) -> bool:
    try:
        _http_json(RUNTIME_URL, "/health", timeout=timeout)
        return True
    except Exception:
        return False

def _tools_cache_key(auth_header: str | None) -> str:
    if not auth_header:
        return "default"
    return hashlib.sha256(auth_header.encode("utf-8", errors="ignore")).hexdigest()[:16]


def runtime_mcp_tools(auth_header: str | None = None, *, force: bool = False) -> list[dict[str, Any]]:
    key = _tools_cache_key(auth_header)
    now = time.monotonic()
    stale: list[dict[str, Any]] | None = None
    with _TOOLS_CACHE_LOCK:
        cached = _RUNTIME_TOOLS_CACHE.get(key)
        if cached:
            stale = cached[1]
            if not force and now - cached[0] < TOOLS_CACHE_TTL:
                return cached[1]
    try:
        response = runtime_mcp_rpc("tools/list", {}, timeout=10, auth_header=auth_header)
        tools = response.get("result", {}).get("tools", [])
        if isinstance(tools, list):
            with _TOOLS_CACHE_LOCK:
                _RUNTIME_TOOLS_CACHE[key] = (now, tools)
                _MERGED_TOOLS_CACHE.pop(key, None)
            return tools
    except Exception:
        if stale is not None:
            return stale
    return stale or []


def merged_tools(auth_header: str | None = None) -> list[dict[str, Any]]:
    key = _tools_cache_key(auth_header)
    now = time.monotonic()
    with _TOOLS_CACHE_LOCK:
        cached = _MERGED_TOOLS_CACHE.get(key)
        if cached and now - cached[0] < TOOLS_CACHE_TTL:
            return cached[1]
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for tool in TOOLS + runtime_mcp_tools(auth_header):
        name = tool.get("name") if isinstance(tool, dict) else None
        if not name or name in seen:
            continue
        seen.add(name)
        normalized = dict(tool)
        if "input_schema" in normalized and "inputSchema" not in normalized:
            normalized["inputSchema"] = normalized.pop("input_schema")
        merged.append(normalized)
    merged = coordination_prioritize_tools(merged)
    with _TOOLS_CACHE_LOCK:
        _MERGED_TOOLS_CACHE[key] = (now, merged)
    return merged

def runtime_mcp_tool_call(name: str, args: dict[str, Any], auth_header: str | None = None) -> Any:
    session_id = str(args.get("session_id") or "").strip() if isinstance(args, dict) else ""
    agent_id = str(args.get("agent_id") or "").strip() if isinstance(args, dict) else ""
    response = runtime_mcp_rpc(
        "tools/call",
        {"name": name, "arguments": args},
        timeout=120,
        auth_header=auth_header,
        session_id=session_id or None,
        agent_id=agent_id or None,
    )
    if "error" in response:
        raise RuntimeError(json.dumps(response["error"], sort_keys=True))
    result = response.get("result", {})
    if isinstance(result, dict) and "structuredContent" in result:
        return result["structuredContent"]
    return result

def _ledger_digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


_LEDGER_SECRET_KEYS = re.compile(
    r"password|passwd|secret|token|api[_-]?key|authorization|cookie|credential|private[_-]?key|"
    r"database[_-]?url|connection[_-]?string|dsn|session[_-]?secret",
    re.I,
)
_LEDGER_ASSIGNMENT_SECRET = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|cookie|credential|private[_-]?key|"
    r"database[_-]?url|connection[_-]?string|dsn)\s*([=:])\s*([^\s,;]+)"
)
_LEDGER_BEARER = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]+")
_LEDGER_BASIC = re.compile(r"(?i)Basic\s+[A-Za-z0-9+/=]+")
_LEDGER_URL_CREDENTIALS = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^:/\s]+:)[^@/\s]+(@)")
_LEDGER_MAX_STRING = max(4096, min(int(os.environ.get("XAVI_MCP_LEDGER_MAX_STRING", "262144")), 1048576))
_LEDGER_MAX_ITEMS = max(20, min(int(os.environ.get("XAVI_MCP_LEDGER_MAX_ITEMS", "1000")), 5000))
_LEDGER_MAX_DEPTH = max(4, min(int(os.environ.get("XAVI_MCP_LEDGER_MAX_DEPTH", "16")), 32))


def _ledger_sanitize(value: Any, *, _depth: int = 0) -> Any:
    if _depth >= _LEDGER_MAX_DEPTH:
        return {"_truncated": True, "reason": "max_depth", "type": type(value).__name__}
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        items = list(value.items())
        path_context = " ".join(
            str(value.get(name) or "")
            for name in ("path", "file", "filename", "filepath", "target_path", "destination_path", "container_path")
        )
        path_lower = path_context.lower()
        tool_context = str(value.get("tool_name") or "").strip()
        sensitive_tool = tool_context in {"owner_memory_put", "owner_memory_get"}
        sensitive_container = sensitive_tool or bool(_LEDGER_SECRET_KEYS.search(path_context)) or any(
            marker in path_lower
            for marker in ("/.env", ".env.", "credential", "secret", "password", "passwd", "token", "private_key", "private-key")
        )
        for index, (key, item) in enumerate(items):
            if index >= _LEDGER_MAX_ITEMS:
                result["_truncated_items"] = len(items) - _LEDGER_MAX_ITEMS
                break
            name = str(key)
            if sensitive_container and name.lower() in {"content", "value", "data", "text", "body", "source", "args", "result"}:
                result[name] = {
                    "redacted": True,
                    "reason": "sensitive_container",
                    "digest": _ledger_digest(item),
                    "bytes": _ledger_size(item),
                }
            elif _LEDGER_SECRET_KEYS.search(name):
                result[name] = "REDACTED"
            else:
                result[name] = _ledger_sanitize(item, _depth=_depth + 1)
        return result
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        clean = [_ledger_sanitize(item, _depth=_depth + 1) for item in items[:_LEDGER_MAX_ITEMS]]
        if len(items) > _LEDGER_MAX_ITEMS:
            clean.append({"_truncated_items": len(items) - _LEDGER_MAX_ITEMS})
        return clean
    if isinstance(value, bytes):
        return {"type": "bytes", "length": len(value), "digest": _ledger_digest(value.hex())}
    if isinstance(value, str):
        text = _LEDGER_BEARER.sub("Bearer REDACTED", value)
        text = _LEDGER_BASIC.sub("Basic REDACTED", text)
        text = _LEDGER_ASSIGNMENT_SECRET.sub(lambda m: f"{m.group(1)}{m.group(2)}REDACTED", text)
        text = _LEDGER_URL_CREDENTIALS.sub(r"\1REDACTED\2", text)
        if len(text) > _LEDGER_MAX_STRING:
            return {
                "text": text[:_LEDGER_MAX_STRING],
                "_truncated_chars": len(text) - _LEDGER_MAX_STRING,
                "original_digest": _ledger_digest(value),
            }
        return text
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _ledger_sanitize(str(value), _depth=_depth + 1)


def _ledger_size(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, default=str).encode("utf-8"))


def _ledger_preview(value: Any, limit: int = 240) -> str:
    text = json.dumps(value, sort_keys=True, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + f"...[truncated {len(text) - limit} chars]"


def _ledger_session_context(request: Request) -> dict[str, str]:
    headers = request.headers
    explicit_session = (
        headers.get("x-xavi-session-id")
        or headers.get("x-mcp-session-id")
        or headers.get("mcp-session-id")
    )
    device_id = (
        headers.get("x-xavi-device-id")
        or headers.get("x-device-id")
        or headers.get("user-agent")
        or "unknown-device"
    )
    agent_id = headers.get("x-xavi-agent-id") or headers.get("x-agent-id") or "mcp-client"

    managed_session = str(getattr(request.state, "xavi_session_id", "") or "").strip()
    if managed_session:
        session_id = managed_session
    elif explicit_session:
        session_id = explicit_session.strip()
    else:
        fingerprint = _ledger_digest({
            "device_id": device_id,
            "agent_id": agent_id,
            "client": headers.get("user-agent", ""),
        }).split(":", 1)[1][:16]
        session_id = f"mcp-{agent_id}-{fingerprint}"

    return {
        "session_id": session_id[:160],
        "device_id_digest": _ledger_digest(device_id),
        "agent_id": agent_id[:120],
    }


def _request_snapshot(request: Request) -> Any:
    return SimpleNamespace(
        headers=dict(request.headers),
        state=SimpleNamespace(xavi_session_id=str(getattr(request.state, "xavi_session_id", "") or "")),
    )


def _ledger_enrich_content(content: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(content)
    if "args" in enriched:
        args = enriched.get("args")
        enriched.setdefault("args_digest", _ledger_digest(args))
        enriched.setdefault("args_preview", _ledger_preview(_ledger_sanitize(args)))
        enriched.setdefault("args_bytes", _ledger_size(args))
    if "result" in enriched:
        result = enriched.get("result")
        enriched.setdefault("result_digest", _ledger_digest(result))
        enriched.setdefault("result_preview", _ledger_preview(_ledger_sanitize(result)))
        enriched.setdefault("result_bytes", _ledger_size(result))
    return enriched


def _ledger_append_now(
    request: Any,
    event_type: str,
    actor: str,
    content: dict[str, Any],
    tags: list[str] | None = None,
) -> None:
    ctx = _ledger_session_context(request)
    enriched = _ledger_enrich_content(content if isinstance(content, dict) else {"value": content})
    runtime_mcp_tool_call(
        "runtime.session_append",
        {
            "session_id": ctx["session_id"],
            "event_type": event_type,
            "actor": actor,
            "content": {
                **_ledger_sanitize(enriched),
                "device_id_digest": ctx["device_id_digest"],
                "agent_id": ctx["agent_id"],
                "capture_mode": "sanitized_full_async",
                "original_content_bytes": _ledger_size(enriched),
            },
            "tags": sorted(set((tags or []) + ["mcp-auto-capture"])),
        },
        request.headers.get("authorization"),
    )


def _ledger_worker() -> None:
    while True:
        request, event_type, actor, content, tags = _LEDGER_QUEUE.get()
        try:
            _ledger_append_now(request, event_type, actor, content, tags)
        except Exception:
            pass
        finally:
            _LEDGER_QUEUE.task_done()


def _ensure_ledger_worker() -> None:
    global _LEDGER_WORKER_STARTED
    if _LEDGER_WORKER_STARTED:
        return
    with _LEDGER_WORKER_LOCK:
        if _LEDGER_WORKER_STARTED:
            return
        threading.Thread(target=_ledger_worker, name="xavi-mcp-ledger", daemon=True).start()
        _LEDGER_WORKER_STARTED = True


def _ledger_append_safe(
    *,
    request: Request,
    event_type: str,
    actor: str,
    content: dict[str, Any],
    tags: list[str] | None = None,
) -> None:
    if os.environ.get("XAVI_MCP_LEDGER_CAPTURE", "1").lower() in {"0", "false", "no"}:
        return
    snapshot = _request_snapshot(request)
    _ensure_ledger_worker()
    try:
        _LEDGER_QUEUE.put_nowait((snapshot, event_type, actor, content, tags))
    except queue.Full:
        # Preserve capture semantics under overload. This fallback is intentionally
        # synchronous only when the bounded queue is saturated.
        try:
            _ledger_append_now(snapshot, event_type, actor, content, tags)
        except Exception:
            pass


def _coordination_context(request: Request) -> dict[str, Any]:
    return coordination_session_context(request, SESSION_CLIENTS)

def _coordination_tool_call(request: Request, tool: str, args: dict[str, Any], timeout: int = 120) -> Any:
    context = _coordination_context(request)
    payload = coordination_inject_identity(args, context)
    response = runtime_mcp_rpc(
        "tools/call",
        {"name": tool, "arguments": payload},
        timeout=timeout,
        auth_header=request.headers.get("authorization"),
        session_id=context.get("session_id"),
        agent_id=context.get("agent_id"),
    )
    if "error" in response: raise RuntimeError(json.dumps(response["error"], sort_keys=True))
    result = response.get("result", {})
    if isinstance(result, dict) and "structuredContent" in result: return result["structuredContent"]
    if isinstance(result, dict) and isinstance(result.get("content"), list):
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text":
                try: return json.loads(item.get("text", ""))
                except Exception: continue
    return result

def _coordination_preflight(request: Request, name: str, args: dict[str, Any], tools: list[dict[str, Any]]) -> dict[str, Any] | None:
    info = classify_and_infer(name, args, tools, V3_DIR / "config/bounded_commands.json", REPO_ROOT, V3_DIR)
    if not info.get("mutating"): return None
    payload = {"project_key": info.get("project_key") or "xavi.app-backend", "title": info.get("title") or f"MCP: {name}", "objective": info.get("objective") or f"Automatic coordination for {name}", "resources": info.get("resources") or [f"tool:{name}"], "tool_name": name, "args_digest": coordination_digest(args), "lease_seconds": 1800, "plan": {"automatic": True, "tool_name": name, "command_name": info.get("command_name"), "resources": info.get("resources") or [f"tool:{name}"]}}
    result = _coordination_tool_call(request, "coordination.preflight", payload, timeout=60)
    result["_coordination_info"] = info
    return result

def _coordination_notice(gate: dict[str, Any] | None) -> dict[str, Any] | None:
    if not gate:
        return None
    work = gate.get("work") or {}
    info = gate.get("_coordination_info") or {}
    learning = gate.get("learning") or {}
    lessons = []
    for item in (learning.get("lessons") or [])[:4]:
        source = item.get("source_event") or {}
        retrieval = item.get("retrieval") or {}
        lessons.append({
            "event_type": source.get("event_type"),
            "summary": source.get("summary"),
            "trust_status": retrieval.get("trust_status") or source.get("trust_status"),
            "score": retrieval.get("score"),
            "suggestion": item.get("suggestion"),
        })
    claims = gate.get("claims") or []
    return {
        "work_id": str(work.get("work_id")) if work.get("work_id") else None,
        "project_key": work.get("project_key") or info.get("project_key"),
        "resources": info.get("resources") or [row.get("resource_key") for row in claims],
        "lease_expires_at": str(claims[0].get("expires_at")) if claims else None,
        "learning_namespace": learning.get("namespace"),
        "recurrent_lessons": lessons,
    }


_PEER_ADVERTISEMENT_CACHE: dict[str, str] = {}


def _peer_message_sync(request: Request, project_key: str) -> dict[str, Any]:
    """Acknowledge durable peer messages and reply once to substantive peer traffic."""
    current_session = str(_coordination_context(request).get("session_id") or "")
    if not current_session:
        return {"acknowledged": [], "responses": []}
    acknowledged: list[str] = []
    responses: list[str] = []
    inbox = _coordination_tool_call(
        request,
        "session.inbox",
        {"project_key": project_key, "limit": PEER_SYNC_LIMIT, "mark_read": True},
        timeout=30,
    )
    for message in (inbox.get("messages") or []) if isinstance(inbox, dict) else []:
        if not isinstance(message, dict):
            continue
        message_id = str(message.get("message_id") or "")
        sender = str(message.get("sender_session_id") or "")
        if not message_id:
            continue
        try:
            _coordination_tool_call(
                request,
                "session.acknowledge",
                {"message_id": message_id, "read": True},
                timeout=30,
            )
            acknowledged.append(message_id)
        except Exception:
            continue

        payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
        kind = str(payload.get("kind") or "")
        message_type = str(message.get("message_type") or "message")
        requires_response = bool(payload.get("requires_ack_response")) or kind == "work_advertisement" or message_type in {
            "message", "suggestion", "handoff", "request", "result"
        }
        if not sender or sender == current_session or kind in {"peer_ack", "work_ack"} or not requires_response:
            continue
        subject = str(message.get("subject") or message_type or "peer message")[:300]
        try:
            response = _coordination_tool_call(
                request,
                "session.send_message",
                {
                    "recipient_session_id": sender,
                    "project_key": str(message.get("project_key") or project_key),
                    "work_id": str(message.get("work_id")) if message.get("work_id") else None,
                    "delegation_id": str(message.get("delegation_id")) if message.get("delegation_id") else None,
                    "message_type": "system",
                    "subject": f"ACK: {subject}"[:500],
                    "body": f"ACK {message_id}: received {message_type} '{subject}'. This peer session has incorporated the message into its shared MCP context.",
                    "payload": {
                        "kind": "peer_ack",
                        "acknowledged_message_id": message_id,
                        "acknowledged_subject": subject,
                        "requires_ack_response": False,
                    },
                    "expires_seconds": 86400,
                },
                timeout=30,
            )
            response_id = str((response or {}).get("message_id") or "") if isinstance(response, dict) else ""
            if response_id:
                responses.append(response_id)
        except Exception:
            continue
    return {"acknowledged": acknowledged[-20:], "responses": responses[-20:]}


def _peer_advertise_work(
    request: Request,
    project_key: str,
    payload: dict[str, Any],
    current_activity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Advertise the current session's work to active peers without repeating an unchanged advertisement."""
    current_session = str(_coordination_context(request).get("session_id") or "")
    if not current_session:
        return {"activity_digest": None, "advertised_to": []}
    work_items = []
    for row in (payload.get("my_work") or [])[:8]:
        if not isinstance(row, dict):
            continue
        work_items.append({
            "work_id": str(row.get("work_id") or ""),
            "title": str(row.get("title") or "")[:500],
            "objective": str(row.get("objective") or "")[:2000],
            "status": str(row.get("status") or ""),
            "updated_at": str(row.get("updated_at") or ""),
            "resources": list((row.get("plan") or {}).get("resources") or [])[:20] if isinstance(row.get("plan"), dict) else [],
        })
    activity = {
        "session_id": current_session,
        "project_key": project_key,
        "current_activity": dict(current_activity or {}),
        "work_items": work_items,
    }
    activity_digest = coordination_digest(activity)
    summary_parts = []
    tool_name = str((current_activity or {}).get("tool_name") or "")
    if tool_name:
        summary_parts.append(f"tool={tool_name}")
    for row in work_items[:4]:
        summary_parts.append(f"{row.get('status')} work={row.get('work_id')} title={row.get('title')}")
    if not summary_parts:
        summary_parts.append("active MCP session with no registered work item yet")
    body = "Peer work advertisement.\n" + "\n".join(summary_parts)
    advertised_to: list[str] = []
    for peer in (payload.get("active_sessions") or [])[:12]:
        if not isinstance(peer, dict):
            continue
        peer_session = str(peer.get("session_id") or "")
        if not peer_session or peer_session == current_session or str(peer.get("status") or "") not in {"active", "idle"}:
            continue
        cache_key = f"{current_session}|{peer_session}|{project_key}"
        if _PEER_ADVERTISEMENT_CACHE.get(cache_key) == activity_digest:
            continue
        try:
            result = _coordination_tool_call(
                request,
                "session.send_message",
                {
                    "recipient_session_id": peer_session,
                    "project_key": project_key,
                    "work_id": work_items[0].get("work_id") if work_items and work_items[0].get("work_id") else None,
                    "message_type": "message",
                    "subject": "MCP work advertisement",
                    "body": body,
                    "payload": {
                        "kind": "work_advertisement",
                        "activity_digest": activity_digest,
                        "activity": activity,
                        "requires_ack_response": True,
                    },
                    "expires_seconds": 86400,
                },
                timeout=30,
            )
            if isinstance(result, dict) and result.get("message_id"):
                _PEER_ADVERTISEMENT_CACHE[cache_key] = activity_digest
                advertised_to.append(peer_session)
        except Exception:
            continue
    return {"activity_digest": activity_digest, "advertised_to": advertised_to}


def _collaboration_awareness(
    request: Request,
    project_key: str = "xavi.app-backend",
    current_activity: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    try:
        project_key = project_key or "xavi.app-backend"
        message_sync = _peer_message_sync(request, project_key)
        payload = _coordination_tool_call(
            request,
            "task.awareness",
            {"project_key": project_key, "limit": 12},
            timeout=30,
        )
        if not isinstance(payload, dict):
            return None
        current_session = _coordination_context(request).get("session_id")
        advertisement = _peer_advertise_work(request, project_key, payload, current_activity)
        return {
            "schema": "xavi-mcp-peer-awareness-compact/v2",
            "project_key": payload.get("project_key") or project_key,
            "current_session_id": current_session,
            "active_peers": [row for row in (payload.get("active_sessions") or []) if row.get("session_id") != current_session][:8],
            "observed_sessions": [row for row in (payload.get("observed_session_activity") or []) if row.get("session_id") != current_session][:8],
            "peer_work": (payload.get("peer_work") or [])[:8],
            "peer_resource_claims": (payload.get("peer_resource_claims") or [])[:12],
            "available_tasks": (payload.get("available_tasks") or [])[:8],
            "delegations": (payload.get("delegations") or [])[:8],
            "workers": (payload.get("workers") or [])[:8],
            "recent_session_messages": (payload.get("recent_session_messages") or [])[:6],
            "peer_message_sync": message_sync,
            "work_advertisement": advertisement,
            "action_hints": (payload.get("action_hints") or [])[:8],
            "awareness_text": payload.get("awareness_text") or "",
        }
    except Exception:
        return None



def _collaboration_summary(payload: dict[str, Any] | None, refreshed_at: float | None = None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    active = payload.get("active_peers") or []
    peer_work = payload.get("peer_work") or []
    tasks = payload.get("available_tasks") or []
    sync = payload.get("peer_message_sync") or {}
    advert = payload.get("work_advertisement") or {}
    return {
        "schema": "xavi-mcp-peer-awareness-summary/v1",
        "refreshed_age_ms": max(0, int((time.monotonic() - refreshed_at) * 1000)) if refreshed_at else None,
        "active_peer_count": len(active),
        "active_peers": [
            {
                "session_id": row.get("session_id"),
                "agent_id": row.get("agent_id"),
                "status": row.get("status"),
            }
            for row in active[:3] if isinstance(row, dict)
        ],
        "peer_work_count": len(peer_work),
        "peer_work": [
            {"work_id": row.get("work_id"), "title": row.get("title"), "status": row.get("status")}
            for row in peer_work[:3] if isinstance(row, dict)
        ],
        "available_task_count": len(tasks),
        "available_tasks": [
            {"task_id": row.get("task_id"), "title": row.get("title"), "priority": row.get("priority")}
            for row in tasks[:3] if isinstance(row, dict)
        ],
        "messages_acknowledged": len(sync.get("acknowledged") or []) if isinstance(sync, dict) else 0,
        "messages_replied": len(sync.get("responses") or []) if isinstance(sync, dict) else 0,
        "advertised_peer_count": len(advert.get("advertised_to") or []) if isinstance(advert, dict) else 0,
    }


def _collaboration_worker() -> None:
    while True:
        key, request, project_key, current_activity = _COLLAB_QUEUE.get()
        try:
            payload = _collaboration_awareness(request, project_key, current_activity)
            if isinstance(payload, dict):
                with _COLLAB_STATE_LOCK:
                    _COLLAB_CACHE[key] = (time.monotonic(), payload)
        except Exception:
            pass
        finally:
            with _COLLAB_STATE_LOCK:
                _COLLAB_INFLIGHT.discard(key)
            _COLLAB_QUEUE.task_done()


def _ensure_collaboration_worker() -> None:
    global _COLLAB_WORKER_STARTED
    if _COLLAB_WORKER_STARTED:
        return
    with _COLLAB_WORKER_LOCK:
        if _COLLAB_WORKER_STARTED:
            return
        threading.Thread(target=_collaboration_worker, name="xavi-mcp-collaboration", daemon=True).start()
        _COLLAB_WORKER_STARTED = True


def _schedule_collaboration_awareness(
    request: Request,
    project_key: str,
    current_activity: dict[str, Any] | None = None,
    *,
    force: bool = False,
) -> dict[str, Any] | None:
    snapshot = _request_snapshot(request)
    current_session = str(_coordination_context(snapshot).get("session_id") or "")
    key = f"{current_session}|{project_key or 'xavi.app-backend'}"
    now = time.monotonic()
    with _COLLAB_STATE_LOCK:
        cached = _COLLAB_CACHE.get(key)
        last = _COLLAB_LAST_SCHEDULED.get(key, 0.0)
        should_schedule = key not in _COLLAB_INFLIGHT and (force or now - last >= COLLAB_REFRESH_TTL)
        if should_schedule:
            _COLLAB_INFLIGHT.add(key)
            _COLLAB_LAST_SCHEDULED[key] = now
    if should_schedule:
        _ensure_collaboration_worker()
        try:
            _COLLAB_QUEUE.put_nowait((key, snapshot, project_key or "xavi.app-backend", dict(current_activity or {})))
        except queue.Full:
            with _COLLAB_STATE_LOCK:
                _COLLAB_INFLIGHT.discard(key)
    if cached:
        return _collaboration_summary(cached[1], cached[0])
    return None


def _coordination_job_link(job_id: str) -> Path | None:
    clean = str(job_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,160}", clean):
        return None
    root = (V3_DIR / "data/bounded_jobs").resolve()
    path = (root / clean / "coordination.json").resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def _coordination_finish(
    request: Request,
    *,
    project_key: str,
    work_id: str,
    status: str,
    summary: str,
) -> None:
    _coordination_tool_call(
        request,
        "coordination.finish",
        {
            "project_key": project_key or "xavi.app-backend",
            "work_id": work_id,
            "status": status,
            "summary": summary[:2000],
            "close_session": False,
        },
        timeout=30,
    )


def _coordination_record(request: Request, gate: dict[str, Any] | None, *, name: str, args: dict[str, Any], status: str, duration_ms: int, result: Any = None, error: str | None = None) -> None:
    try:
        # Read-only status/output calls do not run preflight. They can still close
        # the lease associated with a previously started asynchronous job.
        if gate is None:
            if name not in {"bounded_job_status", "bounded_job_output", "bounded_job_kill"}:
                return
            job_id = str((args or {}).get("job_id") or "")
            link_path = _coordination_job_link(job_id)
            if link_path is None or not link_path.is_file():
                return
            link = json.loads(link_path.read_text())
            result_status = str((result or {}).get("status") or "").lower() if isinstance(result, dict) else ""
            terminal = name == "bounded_job_kill" or status != "ok" or result_status in {"exited", "failed", "killed", "cancelled"}
            if not terminal:
                return
            returncode = (result or {}).get("returncode") if isinstance(result, dict) else None
            final_status = "completed" if status == "ok" and result_status == "exited" and returncode in {None, 0} else "failed"
            _coordination_finish(
                request,
                project_key=str(link.get("project_key") or "xavi.app-backend"),
                work_id=str(link["work_id"]),
                status=final_status,
                summary=f"Async job {job_id} {result_status or status}; returncode={returncode}",
            )
            link_path.unlink(missing_ok=True)
            return

        work = gate.get("work") or {}
        info = gate.get("_coordination_info") or {}
        project_key = str(info.get("project_key") or work.get("project_key") or "xavi.app-backend")
        work_id = str(work.get("work_id") or "")
        resources = info.get("resources") or []
        payload = {
            "project_key": project_key,
            "work_id": work_id or None,
            "event_type": "tool_succeeded" if status == "ok" else "tool_failed",
            "summary": f"{name} {status} in {duration_ms} ms",
            "resources": resources,
            "payload": {
                "tool_name": name,
                "status": status,
                "duration_ms": duration_ms,
                "args_digest": coordination_digest(args),
                "result_digest": coordination_digest(result) if status == "ok" else None,
                "error_digest": coordination_digest(error) if error else None,
            },
        }
        _coordination_tool_call(request, "coordination.event", payload, timeout=30)

        if name == "bounded_job_start" and status == "ok" and isinstance(result, dict) and result.get("job_id"):
            link_path = _coordination_job_link(str(result["job_id"]))
            if link_path is not None:
                link_path.parent.mkdir(parents=True, exist_ok=True)
                link_path.write_text(json.dumps({
                    "schema_version": 1,
                    "job_id": str(result["job_id"]),
                    "project_key": project_key,
                    "work_id": work_id,
                    "resources": resources,
                    "started_at": datetime.utcnow().isoformat() + "Z",
                }, indent=2, sort_keys=True) + "\n")
            return

        if work_id:
            _coordination_finish(
                request,
                project_key=project_key,
                work_id=work_id,
                status="completed" if status == "ok" else "failed",
                summary=f"{name} {status} in {duration_ms} ms",
            )
    except Exception:
        return

def call_ops(command: str, args: dict[str, Any] | None = None, timeout: int = 60) -> Any:
    result = _http_json(
        OPS_URL,
        "/call",
        method="POST",
        payload={"command": command, "args": args or {}},
        headers={"x-xavi-ops-key": OPS_KEY},
        timeout=timeout,
    )
    return result

def _read_capped_stream(stream: Any, limit: int) -> str:
    size = int(stream.tell())
    stream.seek(0)
    data = stream.read(min(size, limit))
    text = data.decode("utf-8", errors="replace") if isinstance(data, (bytes, bytearray)) else str(data)
    if size > limit:
        text += f"\n...[truncated {size - limit} bytes]"
    return text


def run_fixed(cmd: list[str], cwd: Path, timeout: int = 300) -> dict[str, Any]:
    started = time.monotonic()
    with tempfile.TemporaryFile(mode="w+b") as stdout_file, tempfile.TemporaryFile(mode="w+b") as stderr_file:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=stdout_file,
            stderr=stderr_file,
        )
        try:
            returncode = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
            raise
        return {
            "command": " ".join(cmd),
            "cwd": str(cwd),
            "returncode": returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout": _read_capped_stream(stdout_file, RUN_FIXED_OUTPUT_BYTES),
            "stderr": _read_capped_stream(stderr_file, RUN_FIXED_OUTPUT_BYTES),
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

def _ops_request_authorized(request: Request) -> bool:
    """Authenticate the privileged Developer/Ops MCP boundary.

    The public adapter port must fail closed. The token-path api.xavi.app Ops
    gateway injects Authorization: Bearer <XAVI_OPS_API_KEY>; direct callers
    may alternatively provide X-Xavi-Ops-Key. Never accept the runtime MCP key
    here because this adapter exposes host/repository mutation capabilities.
    """
    if not OPS_KEY:
        return False
    authorization = str(request.headers.get("authorization") or "").strip()
    if authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
        if supplied and hmac.compare_digest(supplied, OPS_KEY):
            return True
    supplied = str(request.headers.get("x-xavi-ops-key") or "").strip()
    return bool(supplied) and hmac.compare_digest(supplied, OPS_KEY)


@app.get("/")
async def health() -> dict[str, Any]:
    return {
        "name": SERVER_NAME,
        "version": SERVER_VERSION,
        "protocol": PROTOCOL_VERSION,
        "status": "running",
        "runtime_dir": str(V3_DIR),
        "mcp": "POST /",
        "fastpath": {
            "tools_cache_ttl_seconds": TOOLS_CACHE_TTL,
            "collaboration_refresh_ttl_seconds": COLLAB_REFRESH_TTL,
            "ledger_queue_depth": _LEDGER_QUEUE.qsize(),
            "collaboration_queue_depth": _COLLAB_QUEUE.qsize(),
        },
    }

@app.post("/")
def mcp_root(request: Request, body: Any = Body(...)) -> JSONResponse:
    if not _ops_request_authorized(request):
        return JSONResponse(
            rpc_error(None, -32001, "Unauthorized Xavi Ops MCP request."),
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
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
            session_id = str(getattr(request.state, "xavi_session_id", ""))
            SESSION_CLIENTS[session_id] = {"client_info": params.get("clientInfo") if isinstance(params.get("clientInfo"), dict) else {}, "protocol_version": params.get("protocolVersion"), "initialized_at_ms": int(time.time() * 1000)}
            return JSONResponse(rpc_result(req_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "logging": {},
                    "prompts": {"listChanged": False},
                    "resources": {"listChanged": False},
                    "tools": {"listChanged": False},
                },
                "serverInfo": {"name": SERVER_NAME, "title": "Xavi Runtime v3 Developer MCP", "version": SERVER_VERSION},
                "instructions": (
                    "Xavi is a persistent witnessed autonomous workspace. At the beginning of substantive work, recover relevant prior experience with runtime.transcript_search, runtime.session_index, runtime.session_search, or other Xavi memory tools when available. Mirror every visible system, developer, user, assistant, and tool turn that the client is permitted to forward through runtime.transcript_ingest using stable session/message/parent identifiers, attachment metadata, provenance tags, training_eligible, and redaction metadata. Do not invent or reconstruct hidden reasoning that the client does not actually possess. Treat the shared transcript and witness stream as continuation and self-training memory across Xavi-connected agents. Before planning or changing any Xavi backend resource, call coordination.begin. Read the returned shared plans, leases, recent changes, and conflicts. Mutating tools are automatically preflighted and blocked when another active agent owns an overlapping resource. Use coordination.event for decisions and progress, coordination.heartbeat for long work, and coordination.finish when done."
                ),
            }))

        if method == "initialized":
            return JSONResponse({})

        if method == "tools/list":
            return JSONResponse(rpc_result(req_id, {"tools": merged_tools(request.headers.get("authorization"))}))

        if method == "resources/list":
            return JSONResponse(rpc_result(req_id, {"resources": [{"uri": "xavi-coordination://board", "name": "Shared MCP coordination board", "mimeType": "application/json"}, {"uri": "xavi-coordination://recent", "name": "Recent cross-agent plans and changes", "mimeType": "application/json"}], "nextCursor": None}))

        if method == "resources/read":
            uri = str(params.get("uri") or "")
            if uri == "xavi-coordination://board": result = _coordination_tool_call(request, "coordination.status", {"project_key": "xavi.app-backend", "limit": 50}, timeout=30)
            elif uri == "xavi-coordination://recent": result = _coordination_tool_call(request, "coordination.search", {"project_key": "xavi.app-backend", "query": "change plan decision blocker deployment test", "limit": 40}, timeout=30)
            else: return JSONResponse(rpc_error(req_id, -32602, f"Unknown resource URI: {uri}"))
            return JSONResponse(rpc_result(req_id, {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(result, default=str)}]}))

        if method == "prompts/list":
            return JSONResponse(rpc_result(req_id, {"prompts": [{"name": "coordinate_backend_change", "description": "Start or resume Xavi backend work using the shared multi-agent coordination plane.", "arguments": [{"name": "objective", "description": "Concrete backend objective", "required": True}, {"name": "resources", "description": "Comma-separated paths, services, routes, or database objects", "required": False}]}]}))

        if method == "prompts/get":
            if params.get("name") != "coordinate_backend_change": return JSONResponse(rpc_error(req_id, -32602, "Unknown prompt"))
            prompt_args=params.get("arguments") or {};objective=str(prompt_args.get("objective") or "Describe the backend task");resources=str(prompt_args.get("resources") or "Identify affected resources")
            text=f"Call coordination.begin first with objective: {objective}. Candidate resources: {resources}. Read active work and conflicts, publish a plan, claim resources before editing, record decisions/tests/deployments, and finish or release leases."
            return JSONResponse(rpc_result(req_id, {"description": "Mandatory Xavi backend coordination workflow", "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}))

        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            if not isinstance(args, dict): return JSONResponse(rpc_error(req_id, -32602, "tools/call arguments must be an object"))
            tools_snapshot = merged_tools(request.headers.get("authorization"))
            if isinstance(name, str) and name.startswith(("coordination.", "session.", "delegation.", "worker.", "task.")): args = coordination_inject_identity(args, _coordination_context(request))
            started_ms = int(time.time() * 1000)
            coordination_gate = None
            _ledger_append_safe(
                request=request,
                event_type="mcp_call_start",
                actor="adapter",
                content={
                    "tool_name": name,
                    "request_id_digest": _ledger_digest(req_id),
                    "args": args,
                },
                tags=["mcp", "tool-call", str(name or "unknown")],
            )

            if name in DISABLED_TOOL_NAMES:
                return JSONResponse(rpc_error(req_id, -32001, f"Tool disabled because synchronous command execution hangs in ChatGPT: {name}. Use bounded_job_start/status/output/kill instead."))

            try:
                coordination_gate = _coordination_preflight(request, str(name or ""), args, tools_snapshot)
            except Exception as coordination_error:
                recovery_bypass = name == "restart_runtime_only" and not _runtime_health_reachable()
                if not recovery_bypass:
                    return JSONResponse(rpc_error(req_id, -32011, "Mutating MCP call refused because the shared coordination service is unavailable.", {"tool_name": name, "error": str(coordination_error)[:500]}))
                _ledger_append_safe(
                    request=request,
                    event_type="mcp_coordination_recovery_bypass",
                    actor="adapter",
                    content={
                        "tool_name": name,
                        "reason": "runtime_health_unreachable",
                        "coordination_error_digest": _ledger_digest(str(coordination_error)),
                        "status": "allowed_under_recovery_lock",
                    },
                    tags=["mcp", "coordination", "recovery", "restart-runtime-only"],
                )
                coordination_gate = None
            if coordination_gate is not None and not coordination_gate.get("allowed", False):
                data=conflict_summary(coordination_gate)
                _ledger_append_safe(request=request,event_type="mcp_coordination_conflict",actor="adapter",content={"tool_name":name,"conflicts_digest":_ledger_digest(data),"status":"blocked"},tags=["mcp","coordination","conflict",str(name or "unknown")])
                return JSONResponse(rpc_error(req_id,-32010,data["message"],data))

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
                    ["/bin/bash", "/home/tbi/xavi-coordinated-restart-runtime.sh", "Developer MCP restart_runtime_only requested"],
                    V3_DIR,
                    timeout=300,
                )

            elif name == "git_status":
                result = run_fixed(["git", "status", "--short"], REPO_ROOT, timeout=60)

            elif name == "git_diff_v3":
                result = run_fixed(["git", "diff", "--", str(V3_DIR.relative_to(REPO_ROOT))], REPO_ROOT, timeout=60)

            else:
                if isinstance(name, str) and name.startswith(("coordination.", "session.", "delegation.", "worker.", "task.")):
                    result = runtime_mcp_tool_call(name, args, request.headers.get("authorization"))
                elif isinstance(name, str) and name.startswith("runtime."):
                    result = runtime_mcp_tool_call(name, args, request.headers.get("authorization"))
                elif _EXT_HANDLE is not None:
                    handled, result = _EXT_HANDLE(name, args)
                    if not handled and isinstance(name, str) and (
                        name.startswith("repo.")
                        or name == "dev.apply_change_bundle"
                    ):
                        result = runtime_mcp_tool_call(name, args, request.headers.get("authorization"))
                    elif not handled and isinstance(name, str) and name.startswith("ops."):
                        result = call_ops(name, args, timeout=300)
                    elif not handled:
                        return JSONResponse(rpc_error(req_id, -32601, f"Unknown tool: {name}"))
                elif isinstance(name, str) and (
                    name.startswith("repo.")
                    or name == "dev.apply_change_bundle"
                ):
                    result = runtime_mcp_tool_call(name, args, request.headers.get("authorization"))
                elif isinstance(name, str) and name.startswith("ops."):
                    result = call_ops(name, args, timeout=300)
                else:
                    return JSONResponse(rpc_error(req_id, -32601, f"Unknown tool: {name}"))

            duration_ms = int(time.time() * 1000) - started_ms
            project_key = str((coordination_gate or {}).get("work", {}).get("project_key") or args.get("project_key") or "xavi.app-backend")
            collaboration = _schedule_collaboration_awareness(
                request,
                project_key,
                {"tool_name": str(name or ""), "status": "working"},
                force=coordination_gate is not None,
            )
            notice = _coordination_notice(coordination_gate)
            if isinstance(result, dict):
                result = dict(result)
                if collaboration is not None:
                    result["_collaboration"] = collaboration
                if notice is not None:
                    result["_coordination"] = notice
            _coordination_record(request, coordination_gate, name=str(name or ""), args=args, status="ok", duration_ms=duration_ms, result=result)
            _ledger_append_safe(
                request=request,
                event_type="mcp_call_result",
                actor="adapter",
                content={
                    "tool_name": name,
                    "request_id_digest": _ledger_digest(req_id),
                    "result": result,
                    "status": "ok",
                    "duration_ms": duration_ms,
                },
                tags=["mcp", "tool-result", str(name or "unknown")],
            )
            return JSONResponse(rpc_result(req_id, {
                "content": [{"type": "text", "text": _tool_text_content(result)}],
                "isError": False,
            }))

        return JSONResponse(rpc_error(req_id, -32601, f"Method not found: {method}"))

    except Exception as e:
        try:
            if method == "tools/call":
                duration_ms=int(time.time()*1000)-started_ms
                _coordination_record(request,locals().get("coordination_gate"),name=str(locals().get("name") or ""),args=locals().get("args") or {},status="error",duration_ms=duration_ms,error=str(e))
                _ledger_append_safe(request=request,event_type="mcp_call_result",actor="adapter",content={"tool_name":locals().get("name"),"status":"error","error_digest":_ledger_digest(str(e)),"error":str(e),"error_type":type(e).__name__,"duration_ms":duration_ms},tags=["mcp","tool-result","error",str(locals().get("name") or "unknown")])
        except Exception: pass
        return JSONResponse(rpc_error(req_id, -32000, str(e)))

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("XAVI_DEV_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("XAVI_DEV_MCP_PORT", "8092"))
    uvicorn.run(app, host=host, port=port)
