from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_BROWSER_ROOT = Path(os.environ.get("XAVI_BROWSER_RUNTIME_ROOT", "/var/www/xavi/tools/browser-runtime"))
_BROWSER_DATA = Path(os.environ.get("XAVI_BROWSER_DATA_ROOT", "/datastore2/xavi/data/browser-tests"))
_DRIVER = _BROWSER_ROOT / "xavi-browser-test.js"
_NODE = os.environ.get("XAVI_BROWSER_NODE", "/usr/bin/node")
_WORKER_URL = os.environ.get("XAVI_BROWSER_WORKER_URL", "http://10.77.0.1:8767/run").strip()
_WORKER_KEY_FILE = Path(os.environ.get("XAVI_BROWSER_WORKER_KEY_FILE", "/run/secrets/xavi-browser-worker.key"))


def _clamp(value: Any, lo: int, hi: int, default: int) -> int:
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def _local_available() -> bool:
    return _DRIVER.is_file() and Path(_NODE).is_file()


def _worker_key() -> str:
    try:
        return _WORKER_KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def capability() -> dict[str, Any]:
    local = _local_available()
    worker_key_present = bool(_worker_key())
    return {
        "schema_version": "xavi-browser-runtime-v1",
        "available": bool(local or (_WORKER_URL and worker_key_present)),
        "execution_modes": {
            "local": local,
            "lan_worker": bool(_WORKER_URL and worker_key_present),
        },
        "root": str(_BROWSER_ROOT),
        "driver": str(_DRIVER),
        "browser_store": str(_BROWSER_ROOT / "browsers"),
        "engines": ["chromium", "firefox"],
        "screenshots_root": str(_BROWSER_DATA),
        "worker_url": _WORKER_URL if worker_key_present else None,
    }


def _run_via_worker(args: dict[str, Any], process_timeout: int) -> dict[str, Any]:
    key = _worker_key()
    if not _WORKER_URL or not key:
        return {**capability(), "schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser worker unavailable"}
    body = json.dumps(args, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        _WORKER_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=process_timeout) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser worker response too large"}
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict):
                payload.setdefault("execution_mode", "lan_worker")
                return payload
            return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser worker returned non-object JSON"}
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", errors="replace")
        return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": f"browser worker HTTP {exc.code}", "detail": detail}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": f"browser worker request failed: {exc}"}


def _run_local(args: dict[str, Any], process_timeout: int) -> dict[str, Any]:
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(_BROWSER_ROOT / "browsers")
    _BROWSER_DATA.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [_NODE, str(_DRIVER)],
            input=json.dumps(args, separators=(",", ":")),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(_BROWSER_ROOT),
            env=env,
            timeout=process_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser test timed out", "timeout_seconds": process_timeout}
    except OSError as exc:
        return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": f"browser runtime launch failed: {exc}"}

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        payload = {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser runtime returned invalid JSON", "stdout": stdout[-8000:]}
    if not isinstance(payload, dict):
        payload = {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser runtime returned non-object JSON"}
    payload.setdefault("schema_version", "xavi-browser-test-v1")
    payload["returncode"] = proc.returncode
    payload["execution_mode"] = "local"
    if stderr:
        payload["stderr"] = stderr[-8000:]
    if proc.returncode != 0:
        payload["ok"] = False
    return payload


def run_browser_test(arguments: dict[str, Any]) -> dict[str, Any]:
    args = dict(arguments or {})
    # Transport/session identity fields are not browser-driver input.
    for key in ("conversation_id", "conversation_source", "source_conversation_id", "continued_from_conversation_id", "chat_session_id"):
        args.pop(key, None)
    url = str(args.get("url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "url must be an absolute http/https URL"}

    browser = str(args.get("browser") or "both").lower()
    if browser not in {"chromium", "firefox", "both"}:
        return {"schema_version": "xavi-browser-test-v1", "ok": False, "error": "browser must be chromium, firefox, or both"}
    args["browser"] = browser
    timeout_ms = _clamp(args.get("timeout_ms"), 1000, 120000, 20000)
    args["timeout_ms"] = timeout_ms
    args["body_text_limit"] = _clamp(args.get("body_text_limit"), 0, 50000, 12000)
    args["actions"] = args.get("actions")[:50] if isinstance(args.get("actions"), list) else []
    args["assertions"] = args.get("assertions")[:50] if isinstance(args.get("assertions"), list) else []
    args["cookies"] = args.get("cookies")[:50] if isinstance(args.get("cookies"), list) else []
    engine_count = 2 if browser == "both" else 1
    process_timeout = min(270, max(15, int(timeout_ms / 1000) * engine_count + 45))

    if _local_available():
        return _run_local(args, process_timeout)
    return _run_via_worker(args, process_timeout)
