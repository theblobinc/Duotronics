from __future__ import annotations

try:
    from .xavi_crypto import shake256_hex, shake256_ref
except ImportError:
    from xavi_crypto import shake256_hex, shake256_ref

import json
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()

IDENTITY_ARG_KEYS = {
    "conversation_id",
    "chat_session_id",
    "conversation_source",
    "source_conversation_id",
    "continued_from_conversation_id",
}


def safe_value(value: Any, limit: int = 256) -> str:
    text = str(value or "").strip().replace("\n", " ").replace("\r", " ")
    return text[:limit]


def _digest(value: Any) -> str:
    return shake256_ref(str(value or ""))


def _store_dir(fallback_dir: Path) -> Path:
    primary = Path(os.environ.get("XAVI_CONVERSATION_DATA_DIR", "/datastore2/xavi/data/mcp_conversations"))
    for path in (primary, fallback_dir):
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write-probe"
            probe.write_text("ok")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir


def _connect(directory: Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(directory / "conversation_identity.sqlite3"), timeout=15.0)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            conversation_source TEXT NOT NULL,
            source_conversation_id TEXT,
            continued_from_conversation_id TEXT,
            binding_mode TEXT NOT NULL,
            identity_confidence TEXT NOT NULL,
            first_seen_ms INTEGER NOT NULL,
            last_seen_ms INTEGER NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_aliases (
            conversation_source TEXT NOT NULL,
            source_conversation_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            first_seen_ms INTEGER NOT NULL,
            last_seen_ms INTEGER NOT NULL,
            UNIQUE(conversation_source, source_conversation_id)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS transport_observations (
            observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at_ms INTEGER NOT NULL,
            conversation_id TEXT NOT NULL,
            conversation_source TEXT NOT NULL,
            source_conversation_id TEXT,
            continued_from_conversation_id TEXT,
            transport_session_id TEXT,
            transport_session_digest TEXT,
            binding_mode TEXT NOT NULL,
            identity_confidence TEXT NOT NULL,
            safe_transport_json TEXT NOT NULL
        )
        """
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_transport_observations_conversation ON transport_observations(conversation_id, recorded_at_ms)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_transport_observations_session ON transport_observations(transport_session_digest, recorded_at_ms)")
    return db


def _infer_source(request: Any, args: dict[str, Any]) -> str:
    headers = request.headers
    explicit = safe_value(args.get("conversation_source") or headers.get("x-xavi-conversation-source"), 80)
    if explicit:
        return explicit.lower()
    joined = " ".join(
        str(headers.get(key) or "").lower()
        for key in ("origin", "user-agent", "x-xavi-client-name", "x-xavi-agent-id")
    )
    if "codex" in joined:
        return "codex"
    if "chatgpt" in joined or "openai" in joined:
        return "chatgpt"
    if "claude" in joined or "anthropic" in joined:
        return "claude"
    if "gemini" in joined or "google" in joined:
        return "gemini"
    if "vscode" in joined or "visual studio code" in joined:
        return "vscode"
    if "librechat" in joined:
        return "librechat"
    return "mcp"


def _safe_transport(request: Any) -> dict[str, str]:
    headers = request.headers
    out: dict[str, str] = {}
    for key in ("origin", "user-agent", "mcp-protocol-version", "x-xavi-client-name", "x-xavi-agent-id"):
        value = headers.get(key)
        if value:
            out[key] = safe_value(value, 500)
    device = headers.get("x-xavi-device-id") or headers.get("x-device-id")
    if device:
        out["device-id-digest"] = _digest(device)
    return out


def _persist(directory: Path, record: dict[str, Any]) -> None:
    now_ms = int(record["recorded_at_ms"])
    with _LOCK:
        db = _connect(directory)
        try:
            db.execute(
                """
                INSERT INTO conversations (
                    conversation_id, conversation_source, source_conversation_id,
                    continued_from_conversation_id, binding_mode, identity_confidence,
                    first_seen_ms, last_seen_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    conversation_source=excluded.conversation_source,
                    source_conversation_id=COALESCE(excluded.source_conversation_id, conversations.source_conversation_id),
                    continued_from_conversation_id=COALESCE(excluded.continued_from_conversation_id, conversations.continued_from_conversation_id),
                    binding_mode=excluded.binding_mode,
                    identity_confidence=excluded.identity_confidence,
                    last_seen_ms=excluded.last_seen_ms
                """,
                (
                    record["conversation_id"],
                    record["conversation_source"],
                    record.get("source_conversation_id"),
                    record.get("continued_from_conversation_id"),
                    record["binding_mode"],
                    record["identity_confidence"],
                    now_ms,
                    now_ms,
                ),
            )
            if record.get("source_conversation_id"):
                db.execute(
                    """
                    INSERT INTO conversation_aliases (
                        conversation_source, source_conversation_id, conversation_id,
                        first_seen_ms, last_seen_ms
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(conversation_source, source_conversation_id) DO UPDATE SET
                        conversation_id=excluded.conversation_id,
                        last_seen_ms=excluded.last_seen_ms
                    """,
                    (
                        record["conversation_source"],
                        record["source_conversation_id"],
                        record["conversation_id"],
                        now_ms,
                        now_ms,
                    ),
                )
            db.execute(
                """
                INSERT INTO transport_observations (
                    recorded_at_ms, conversation_id, conversation_source,
                    source_conversation_id, continued_from_conversation_id,
                    transport_session_id, transport_session_digest,
                    binding_mode, identity_confidence, safe_transport_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_ms,
                    record["conversation_id"],
                    record["conversation_source"],
                    record.get("source_conversation_id"),
                    record.get("continued_from_conversation_id"),
                    record.get("transport_session_id"),
                    record.get("transport_session_digest"),
                    record["binding_mode"],
                    record["identity_confidence"],
                    json.dumps(record.get("safe_transport_headers") or {}, sort_keys=True, separators=(",", ":")),
                ),
            )
            db.commit()
        finally:
            db.close()
        with (directory / "conversation_identity.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def _resume_query_identity(args: dict[str, Any]) -> dict[str, str]:
    """Parse an explicit continuation handshake carried through a cached-schema search query.

    Cached MCP clients may not yet expose the conversation identity fields that the live
    tools/list schema advertises.  A search query beginning with ``xavi-resume `` may
    therefore carry a small JSON object containing only the normal identity keys.  The
    prefix is intentionally strict so ordinary searches containing conversation IDs do
    not accidentally rebind the transport.
    """
    query = str(args.get("query") or "").strip()
    prefix = "xavi-resume "
    if not query.startswith(prefix):
        return {}
    try:
        payload = json.loads(query[len(prefix):].strip())
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    out: dict[str, str] = {}
    for key in IDENTITY_ARG_KEYS:
        value = safe_value(payload.get(key))
        if value:
            out[key] = value
    return out


def _lookup_explicit_transport_binding(directory: Path, session_id: str) -> dict[str, str] | None:
    """Return the most recent explicit identity bound to this transport session."""
    if not session_id:
        return None
    digest = _digest(session_id)
    max_age_ms = max(60_000, int(os.environ.get("XAVI_CONVERSATION_TRANSPORT_BIND_TTL_MS", str(12 * 60 * 60 * 1000))))
    cutoff = int(time.time() * 1000) - max_age_ms
    with _LOCK:
        db = _connect(directory)
        try:
            row = db.execute(
                """
                SELECT conversation_id, conversation_source, source_conversation_id,
                       continued_from_conversation_id, recorded_at_ms
                FROM transport_observations
                WHERE transport_session_digest = ?
                  AND identity_confidence = 'explicit'
                  AND recorded_at_ms >= ?
                ORDER BY recorded_at_ms DESC, observation_id DESC
                LIMIT 1
                """,
                (digest, cutoff),
            ).fetchone()
        finally:
            db.close()
    if not row:
        return None
    return {
        "conversation_id": safe_value(row[0]),
        "conversation_source": safe_value(row[1], 80),
        "source_conversation_id": safe_value(row[2]),
        "continued_from_conversation_id": safe_value(row[3]),
    }


def resolve(request: Any, session_id: str, payload: dict[str, Any] | None, fallback_dir: Path) -> dict[str, str]:
    params = (payload or {}).get("params") if isinstance(payload, dict) else {}
    args = params.get("arguments") if isinstance(params, dict) else {}
    if not isinstance(args, dict):
        args = {}
    resume_identity = _resume_query_identity(args)
    if resume_identity:
        args = {**args, **resume_identity}
    headers = request.headers
    source = _infer_source(request, args)
    explicit = safe_value(args.get("conversation_id") or args.get("chat_session_id") or headers.get("x-xavi-conversation-id"))
    if explicit.upper() in {"NEW_SESSION", "NEW_CONVERSATION", "NEW_CHAT"}:
        explicit = ""
    source_id = safe_value(args.get("source_conversation_id") or headers.get("x-xavi-source-conversation-id"))
    continued_from = safe_value(args.get("continued_from_conversation_id"))

    if explicit:
        conversation_id = explicit if (":" in explicit or explicit.startswith("xc_")) else f"{source}:{explicit}"
        binding_mode = "payload-conversation-id"
        identity_confidence = "explicit"
    elif source_id:
        conversation_id = f"{source}:{source_id}"
        binding_mode = "source-native-id"
        identity_confidence = "explicit"
    elif (bound := _lookup_explicit_transport_binding(_store_dir(fallback_dir), session_id)):
        conversation_id = bound["conversation_id"]
        source = bound.get("conversation_source") or source
        source_id = bound.get("source_conversation_id") or source_id
        continued_from = bound.get("continued_from_conversation_id") or continued_from
        binding_mode = "transport-session-bound-explicit"
        identity_confidence = "explicit"
    else:
        # Transport identity is not authoritative conversation identity because a
        # client may reuse it across chats. It is still a useful compatibility
        # fallback for clients using cached schemas that cannot echo conversation_id
        # yet. Keep it deterministic across adapter workers/processes and mark it
        # explicitly provisional so a payload/native conversation id always wins.
        transport_digest = shake256_hex(str(session_id or "unknown"))[:24]
        conversation_id = f"{source}:transport:{transport_digest}"
        binding_mode = "transport-session-provisional"
        identity_confidence = "provisional"

    record = {
        "schema_version": 2,
        "recorded_at_ms": int(time.time() * 1000),
        "conversation_id": conversation_id,
        "conversation_source": source,
        "source_conversation_id": source_id or None,
        "continued_from_conversation_id": continued_from or None,
        "transport_session_id": safe_value(session_id, 200) or None,
        "transport_session_digest": _digest(session_id) if session_id else None,
        "binding_mode": binding_mode,
        "identity_confidence": identity_confidence,
        "safe_transport_headers": _safe_transport(request),
    }
    try:
        _persist(_store_dir(fallback_dir), record)
    except Exception:
        pass
    return {
        "conversation_id": conversation_id,
        "conversation_source": source,
        "source_conversation_id": source_id,
        "continued_from_conversation_id": continued_from,
        "binding_mode": binding_mode,
        "identity_confidence": identity_confidence,
    }


def from_request(request: Any) -> dict[str, str]:
    state = getattr(request, "state", None)
    return {
        "conversation_id": safe_value(getattr(state, "xavi_conversation_id", "")),
        "conversation_source": safe_value(getattr(state, "xavi_conversation_source", "mcp"), 80) or "mcp",
        "source_conversation_id": safe_value(getattr(state, "xavi_source_conversation_id", "")),
        "continued_from_conversation_id": safe_value(getattr(state, "xavi_continued_from_conversation_id", "")),
        "binding_mode": safe_value(getattr(state, "xavi_conversation_binding_mode", ""), 80),
        "identity_confidence": safe_value(getattr(state, "xavi_conversation_identity_confidence", ""), 80),
    }


def inject(args: dict[str, Any], request: Any) -> dict[str, Any]:
    clean = dict(args or {})
    for key, value in from_request(request).items():
        if value:
            clean[key] = value
    return clean


def schema_properties() -> dict[str, Any]:
    return {
        "chat_session_id": {
            "type": "string",
            "description": "Compatibility alias for conversation_id. Prefer conversation_id for new clients; keep the exact same value for all tool calls in one chat.",
        },
        "conversation_id": {
            "type": "string",
            "description": "Durable per-chat identity. Use one stable value for this chat and reuse it on every Xavi tool call. Prefer '<source>:<native-id>' when a native chat/thread id is actually available. Otherwise generate a UUID-based id once. If omitted on the first call, copy the exact _conversation.conversation_id returned by Xavi into all later calls in this chat.",
        },
        "conversation_source": {
            "type": "string",
            "description": "Origin client for this conversation, for example chatgpt, claude, gemini, vscode, librechat, or local-agent.",
        },
        "source_conversation_id": {
            "type": "string",
            "description": "Native conversation/thread identifier from the source client when it is actually available. Do not invent a source-native id.",
        },
        "continued_from_conversation_id": {
            "type": "string",
            "description": "Optional durable conversation id this chat explicitly continues from.",
        },
    }
