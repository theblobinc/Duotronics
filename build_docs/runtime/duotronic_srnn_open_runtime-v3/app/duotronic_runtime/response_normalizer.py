from __future__ import annotations

import re
from typing import Any


REASONING_KEYS = (
    "thinking",
    "reasoning",
    "reasoning_content",
    "reasoningContent",
    "reasoning_details",
    "reasoningDetails",
    "reasoning_tokens",
    "thought",
    "thoughts",
    "chain_of_thought",
    "cot",
    "analysis",
)

CONTENT_KEYS = (
    "response",
    "content",
    "text",
    "message",
    "output_text",
    "final",
    "answer",
)

TOOL_KEYS = (
    "tool_calls",
    "toolCalls",
    "function_call",
    "functionCall",
)

REASONING_TAG_PATTERNS = (
    re.compile(r"<think>([\s\S]*?)</think>", re.IGNORECASE),
    re.compile(r"<thinking>([\s\S]*?)</thinking>", re.IGNORECASE),
    re.compile(r"<reasoning>([\s\S]*?)</reasoning>", re.IGNORECASE),
    re.compile(r":::thinking\s*([\s\S]*?)\s*:::", re.IGNORECASE),
)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            text = _stringify(item)
            if text:
                parts.append(text)
        return "\n".join(parts)
    if isinstance(value, dict):
        # Anthropic/OpenAI-style content blocks, e.g. {type: "text", text: "..."}
        block_type = str(value.get("type") or "").lower()
        if block_type in {"thinking", "reasoning", "reasoning_content"}:
            for key in ("thinking", "text", "content", "reasoning", "summary"):
                if key in value:
                    return _stringify(value[key])
        if block_type in {"text", "output_text"}:
            for key in ("text", "content"):
                if key in value:
                    return _stringify(value[key])
        for key in CONTENT_KEYS + REASONING_KEYS:
            if key in value and value[key] is not None:
                return _stringify(value[key])
        return ""
    return str(value)


def _append_unique(existing: str, addition: str) -> str:
    addition = (addition or "").strip()
    if not addition:
        return existing
    if addition in existing:
        return existing
    if not existing:
        return addition
    return existing.rstrip() + "\n\n" + addition


def _extract_tagged_reasoning(text: str) -> tuple[str, str]:
    """Return (visible_without_reasoning_tags, extracted_reasoning)."""
    visible = text or ""
    reasoning = ""
    for pattern in REASONING_TAG_PATTERNS:
        matches = pattern.findall(visible)
        for match in matches:
            reasoning = _append_unique(reasoning, match)
        visible = pattern.sub("", visible).strip()
    return visible, reasoning


def _extract_from_content_blocks(value: Any) -> tuple[str, str, list[Any]]:
    visible = ""
    reasoning = ""
    tool_calls: list[Any] = []
    if not isinstance(value, list):
        return visible, reasoning, tool_calls
    for block in value:
        if isinstance(block, str):
            clean, tagged = _extract_tagged_reasoning(block)
            visible = _append_unique(visible, clean)
            reasoning = _append_unique(reasoning, tagged)
            continue
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "").lower()
        if block_type in {"thinking", "reasoning", "reasoning_content"}:
            reasoning = _append_unique(reasoning, _stringify(block))
        elif block_type in {"tool_use", "tool_call", "function_call"}:
            tool_calls.append(block)
        else:
            clean, tagged = _extract_tagged_reasoning(_stringify(block))
            visible = _append_unique(visible, clean)
            reasoning = _append_unique(reasoning, tagged)
    return visible, reasoning, tool_calls


def _extract_message_like(data: dict[str, Any], native_fields: dict[str, Any]) -> tuple[str, str, list[Any]]:
    visible = ""
    reasoning = ""
    tool_calls: list[Any] = []

    content_value = data.get("content")
    if isinstance(content_value, list):
        v, r, t = _extract_from_content_blocks(content_value)
        visible = _append_unique(visible, v)
        reasoning = _append_unique(reasoning, r)
        tool_calls.extend(t)
        native_fields["content_blocks"] = content_value

    for key in CONTENT_KEYS:
        if key in data and data[key] is not None:
            if key == "content" and isinstance(data[key], list):
                continue
            clean, tagged = _extract_tagged_reasoning(_stringify(data[key]))
            visible = _append_unique(visible, clean)
            reasoning = _append_unique(reasoning, tagged)
            native_fields[key] = data[key]
            if visible:
                break

    for key in REASONING_KEYS:
        if key in data and data[key]:
            reasoning = _append_unique(reasoning, _stringify(data[key]))
            native_fields[key] = data[key]

    for key in TOOL_KEYS:
        if key in data and data[key]:
            value = data[key]
            tool_calls.extend(value if isinstance(value, list) else [value])
            native_fields[key] = value

    return visible, reasoning, tool_calls


def extract_model_response(raw: Any) -> dict[str, Any]:
    """Normalize provider-specific response/thinking/tool fields.

    Supports Ollama/Qwen-style `thinking`, OpenAI-compatible
    `reasoning_content`, DeepSeek/R1-style `<think>...</think>` text, and
    Anthropic-style content blocks.
    """
    data = raw if isinstance(raw, dict) else {}
    visible = ""
    reasoning = ""
    tool_calls: list[Any] = []
    native_fields: dict[str, Any] = {}

    v, r, t = _extract_message_like(data, native_fields)
    visible = _append_unique(visible, v)
    reasoning = _append_unique(reasoning, r)
    tool_calls.extend(t)

    choices = data.get("choices") if isinstance(data, dict) else None
    if isinstance(choices, list) and choices:
        choice = choices[0] if isinstance(choices[0], dict) else {}
        for container_key in ("message", "delta"):
            msg = choice.get(container_key, {})
            if isinstance(msg, dict):
                v, r, t = _extract_message_like(msg, native_fields)
                visible = _append_unique(visible, v)
                reasoning = _append_unique(reasoning, r)
                tool_calls.extend(t)

    # Some providers emit output as a list of blocks/items.
    output = data.get("output") if isinstance(data, dict) else None
    if isinstance(output, list):
        for item in output:
            if isinstance(item, dict):
                v, r, t = _extract_message_like(item, native_fields)
                visible = _append_unique(visible, v)
                reasoning = _append_unique(reasoning, r)
                tool_calls.extend(t)

    has_reasoning = bool(reasoning.strip())
    has_visible = bool(visible.strip())
    return {
        "response_text": visible or "",
        "reasoning_text": reasoning or "",
        "tool_calls": tool_calls,
        "capabilities_observed": {
            "has_visible_response": has_visible,
            "has_reasoning": has_reasoning,
            "has_tool_calls": bool(tool_calls),
            "reasoning_only": has_reasoning and not has_visible,
        },
        "native_fields": native_fields,
    }
