from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from Cryptodome.Hash import KMAC256

from .evidence import shake256_ref


DEFAULT_AGENT_URL = "http://192.168.123.10:8765"
DEFAULT_SECRET_FILE = "/run/secrets/xavi-sandbox-1-agent.key"
ALLOWED_ACTIONS = {
    "health",
    "containers",
    "images",
    "logs",
    "file_list",
    "file_put",
    "image_pull",
    "image_build",
    "container_run",
    "container_action",
    "container_exec",
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def _secret() -> bytes:
    path = Path(os.environ.get("XAVI_SANDBOX_AGENT_KEY_FILE", DEFAULT_SECRET_FILE))
    raw = path.read_text().strip()
    key = bytes.fromhex(raw)
    if len(key) < 32:
        raise RuntimeError("sandbox_agent_key_too_short")
    return key


def _agent_url() -> str:
    return str(os.environ.get("XAVI_SANDBOX_AGENT_URL") or DEFAULT_AGENT_URL).rstrip("/")


def _target(action: str, request: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    if action == "health":
        return "GET", "/health", None
    if action == "containers":
        return "GET", "/v1/containers", None
    if action == "images":
        return "GET", "/v1/images", None
    if action == "logs":
        name = str(request.get("name") or "").strip()
        tail = max(1, min(int(request.get("tail", 200)), 2000))
        if not name:
            raise ValueError("logs_requires_name")
        return "GET", "/v1/logs?" + urlencode({"name": name, "tail": tail}), None
    if action == "file_list":
        path = str(request.get("path") or "/srv/xavi/staging")
        return "GET", "/v1/files?" + urlencode({"path": path}), None
    post_map = {
        "file_put": "/v1/file/put",
        "image_pull": "/v1/image/pull",
        "image_build": "/v1/image/build",
        "container_run": "/v1/container/run",
        "container_action": "/v1/container/action",
        "container_exec": "/v1/container/exec",
    }
    if action in post_map:
        return "POST", post_map[action], request
    raise ValueError("sandbox_action_not_allowed")


def _sign(method: str, target: str, body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    message = (method + "\n" + target + "\n" + timestamp + "\n" + nonce + "\n").encode("utf-8") + body
    signature = KMAC256.new(
        key=_secret(),
        data=message,
        mac_len=32,
        custom=b"Xavi-Sandbox-Agent-v1",
    ).hexdigest()
    return {
        "X-Xavi-Timestamp": timestamp,
        "X-Xavi-Nonce": nonce,
        "X-Xavi-Signature": signature,
    }


@dataclass
class SandboxVMRuntime:
    kernel: Any

    def capability(self) -> dict[str, Any]:
        secret_path = Path(os.environ.get("XAVI_SANDBOX_AGENT_KEY_FILE", DEFAULT_SECRET_FILE))
        return {
            "schema_version": "xavi-sandbox-vm-capability/v1",
            "configured": secret_path.is_file(),
            "agent_url": _agent_url(),
            "vm": "xavi-sandbox-1",
            "management_ip": "192.168.123.10",
            "lan_ip": "10.77.0.10",
            "primary_node_fabric": "10.77.0.0/24",
            "control_plane": "management-only",
            "container_engine": "rootless-podman",
            "allowed_actions": sorted(ALLOWED_ACTIONS),
            "adjudication_authority": "wg-rnn",
            "guest_output_is_truth": False,
            "crypto": {"request_auth": "KMAC256", "audit_refs": "SHAKE256-512"},
        }

    async def execute(self, *, action: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        action = str(action or "").strip().lower()
        if action not in ALLOWED_ACTIONS:
            raise ValueError("sandbox_action_not_allowed")
        request = request if isinstance(request, dict) else {}
        method, target, payload = _target(action, request)
        body = b"" if payload is None else json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = _sign(method, target, body) if target.startswith("/v1/") else {}
        if body:
            headers["Content-Type"] = "application/json"
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(125.0, connect=5.0), trust_env=False) as client:
                response = await client.request(method, _agent_url() + target, content=body if method != "GET" else None, headers=headers)
                response.raise_for_status()
                agent_result = response.json()
            error = None
        except Exception as exc:
            agent_result = {"ok": False, "error": exc.__class__.__name__, "detail": str(exc)[:1000]}
            error = {"type": exc.__class__.__name__, "detail": str(exc)[:1000]}
        elapsed_ms = int((time.monotonic() - started) * 1000)

        guest_audit = agent_result.get("audit") if isinstance(agent_result, dict) and isinstance(agent_result.get("audit"), dict) else {}
        result = agent_result.get("result") if isinstance(agent_result, dict) and isinstance(agent_result.get("result"), dict) else {}
        witness_payload = {
            "schema_version": "xavi-sandbox-vm-operation/v1",
            "vm": "xavi-sandbox-1",
            "management_ip": "192.168.123.10",
            "lan_ip": "10.77.0.10",
            "action": action,
            "request_ref": shake256_ref(_canonical(request)),
            "request_keys": sorted(str(k) for k in request.keys()),
            "guest_audit": guest_audit,
            "guest_returncode": result.get("returncode"),
            "guest_stdout_ref": shake256_ref(str(result.get("stdout") or "")),
            "guest_stderr_ref": shake256_ref(str(result.get("stderr") or "")),
            "latency_ms": elapsed_ms,
            "observer_error": error,
            "adjudication_authority": "wg-rnn",
            "guest_output_is_truth": False,
            "created_at_ms": int(time.time() * 1000),
        }
        status = "executed" if bool(agent_result.get("ok")) else "observer_error"
        witness = self.kernel.evidence.witness("SandboxVMOperationWitness", witness_payload, force="observe", status=status)
        self.kernel.store.insert_witness(witness)
        return {
            "ok": bool(agent_result.get("ok")),
            "action": action,
            "vm": "xavi-sandbox-1",
            "result": result,
            "guest_audit": guest_audit,
            "observer_error": error,
            "witness": witness,
            "adjudication_authority": "wg-rnn",
            "guest_output_is_truth": False,
        }
