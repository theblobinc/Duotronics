from __future__ import annotations

from copy import deepcopy
from typing import Any


_CLIENT_PROFILES: dict[str, dict[str, Any]] = {
    "librechat.default": {
        "surface": "librechat",
        "description": "Default LibreChat text conversation route.",
        "route": {"task": "chat", "prefer_remote": True, "max_candidates": 6},
        "operation": {"intent": "chat", "prefer_remote": True, "max_candidates": 6},
    },
    "librechat.code": {
        "surface": "librechat",
        "description": "LibreChat code-generation and tool-use route.",
        "route": {"task": "code_generation", "needs_tools": True, "prefer_remote": True, "max_candidates": 6},
        "operation": {"intent": "code", "prefer_remote": True, "max_candidates": 6},
    },
    "librechat.vision": {
        "surface": "librechat",
        "description": "LibreChat multimodal or OCR route.",
        "route": {"task": "vision", "needs_vision": True, "prefer_remote": True, "max_candidates": 6},
        "operation": {"intent": "vision", "prefer_remote": True, "max_candidates": 6},
    },
    "openclaw.agent": {
        "surface": "openclaw",
        "description": "OpenClaw agentic code route with tool-capable models.",
        "route": {"task": "code_generation", "needs_tools": True, "prefer_remote": True, "max_candidates": 6},
        "operation": {"intent": "code", "prefer_remote": True, "max_candidates": 6},
    },
    "openclaw.execute": {
        "surface": "openclaw",
        "description": "OpenClaw witnessed code-interpreter route; requires a live backend when requested.",
        "route": {"task": "code_interpreter", "require_live_backend": True, "prefer_remote": True, "max_candidates": 6},
        "operation": {"intent": "run_code", "require_live_backend": True, "prefer_remote": True, "max_candidates": 6},
    },
    "openclaw.plan": {
        "surface": "openclaw",
        "description": "OpenClaw read-only planning route for repo and architecture work.",
        "route": {"task": "logic", "prefer_remote": True, "max_candidates": 6},
        "operation": {"intent": "logic", "prefer_remote": True, "max_candidates": 6},
    },
}


def client_profiles() -> dict[str, dict[str, Any]]:
    return deepcopy(_CLIENT_PROFILES)


def profile_payload(name: str, *, mode: str = "route", overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    profiles = client_profiles()
    if name not in profiles:
        raise KeyError(f"unknown client profile: {name}")
    profile = profiles[name]
    if mode not in {"route", "operation"}:
        raise ValueError("mode must be 'route' or 'operation'")
    payload = dict(profile[mode])
    if overrides:
        payload.update({k: v for k, v in overrides.items() if v is not None})
    return payload
