from __future__ import annotations

from typing import Any

from .crypto_primitives import shake256_hex

IDENTITY_ARG_KEYS = {
    "conversation_id",
    "chat_session_id",
    "conversation_source",
    "source_conversation_id",
    "continued_from_conversation_id",
}


def safe_value(value: Any, limit: int = 256) -> str:
    return str(value or "").strip().replace("\n", " ").replace("\r", " ")[:limit]


def schema_properties() -> dict[str, Any]:
    return {
        "conversation_id": {
            "type": "string",
            "description": "Durable per-chat identity. Reuse exactly the same value for every Xavi tool call in this conversation. Prefer '<source>:<native-id>' when a native id is actually available; otherwise generate one stable UUID-based value once per chat and keep reusing it.",
        },
        "conversation_source": {
            "type": "string",
            "description": "Origin client such as chatgpt, claude, gemini, vscode, librechat, or local-agent.",
        },
        "source_conversation_id": {
            "type": "string",
            "description": "Native source conversation/thread identifier when actually available. Do not invent one.",
        },
        "continued_from_conversation_id": {
            "type": "string",
            "description": "Optional durable conversation id this chat explicitly continues from.",
        },
    }


def infer_source(headers: Any, args: dict[str, Any]) -> str:
    explicit = safe_value(args.get("conversation_source") or headers.get("x-xavi-conversation-source"), 80)
    if explicit:
        return explicit.lower()
    joined = " ".join(str(headers.get(k) or "").lower() for k in ("origin", "user-agent", "x-xavi-agent-id"))
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
    return "mcp"


def resolve(headers: Any, args: dict[str, Any], transport_session_id: str) -> dict[str, str]:
    source = infer_source(headers, args)
    explicit = safe_value(args.get("conversation_id") or args.get("chat_session_id") or headers.get("x-xavi-conversation-id"))
    source_id = safe_value(args.get("source_conversation_id") or headers.get("x-xavi-source-conversation-id"))
    continued_from = safe_value(args.get("continued_from_conversation_id"))
    if explicit.upper() in {"NEW_SESSION", "NEW_CONVERSATION", "NEW_CHAT"}:
        explicit = ""
    if explicit:
        conversation_id = explicit if (":" in explicit or explicit.startswith("xc_")) else f"{source}:{explicit}"
    elif source_id:
        conversation_id = f"{source}:{source_id}"
    else:
        digest = shake256_hex(str(transport_session_id))[:24]
        conversation_id = f"{source}:mcp-session:{digest}"
    return {
        "conversation_id": conversation_id,
        "conversation_source": source,
        "source_conversation_id": source_id,
        "continued_from_conversation_id": continued_from,
    }


def strip(args: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in args.items() if key not in IDENTITY_ARG_KEYS}
