from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .evidence import sha256_ref


TASK_CAPABILITY_MAP = {
    "chat": ["chat", "text_generation"],
    "small_chat": ["chat", "text_generation"],
    "long_context": ["chat", "text_generation"],
    "code": ["code_generation", "code_agent", "tool_use", "chat"],
    "code_generation": ["code_generation", "code_agent", "chat"],
    "code_interpreter": ["code_execution", "code_interpreter"],
    "agent": ["code_agent", "tool_use", "chat"],
    "tool_use": ["tool_use", "code_agent", "chat"],
    "vision": ["vision", "multimodal", "document_ocr"],
    "document_ocr": ["document_ocr", "vision", "multimodal"],
    "image": ["image_generation"],
    "image_generation": ["image_generation"],
    "embedding": ["embeddings"],
    "embeddings": ["embeddings"],
    "rerank": ["rerank", "classification"],
    "classification": ["classification", "rerank"],
    "logic": ["logic", "formal_reasoning", "chat", "text_generation"],
    "witness_contract": ["logic", "formal_reasoning", "chat", "text_generation"],
}

CAPABILITY_WEIGHTS = {
    "code_agent": 34,
    "tool_use": 28,
    "code_generation": 26,
    "code_execution": 40,
    "code_interpreter": 38,
    "image_generation": 40,
    "vision": 32,
    "multimodal": 30,
    "document_ocr": 24,
    "embeddings": 36,
    "rerank": 32,
    "classification": 24,
    "chat": 14,
    "text_generation": 12,
    "logic": 30,
    "formal_reasoning": 30,
}

PROVIDER_WEIGHTS = {
    "ollama": 18,
    "llama_cpp": 16,
    "openai_compatible": 15,
    "transformers_js": 12,
    "stable_diffusion": 12,
    "comfyui": 12,
    "echo": -40,
}

REMOTE_MARKERS = ("host.containers.internal", "18205", "gpu", "remote")


@dataclass(frozen=True)
class InferenceRouteRequest:
    task: str = "chat"
    capability: str | None = None
    modalities: tuple[str, ...] = ()
    prefer_provider: str | None = None
    prefer_remote: bool = True
    needs_tools: bool = False
    needs_vision: bool = False
    require_live_backend: bool = False
    max_candidates: int = 8

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "InferenceRouteRequest":
        payload = payload or {}
        raw_modalities = payload.get("modalities") or []
        if isinstance(raw_modalities, str):
            raw_modalities = [raw_modalities]
        return cls(
            task=str(payload.get("task") or "chat"),
            capability=str(payload["capability"]) if payload.get("capability") else None,
            modalities=tuple(str(item) for item in raw_modalities if item),
            prefer_provider=str(payload["prefer_provider"]) if payload.get("prefer_provider") else None,
            prefer_remote=bool(payload.get("prefer_remote", True)),
            needs_tools=bool(payload.get("needs_tools", False)),
            needs_vision=bool(payload.get("needs_vision", False)),
            require_live_backend=bool(payload.get("require_live_backend", False)),
            max_candidates=max(1, min(int(payload.get("max_candidates", 8)), 32)),
        )


def _capabilities_for(req: InferenceRouteRequest) -> list[str]:
    if req.capability:
        base = [req.capability]
    else:
        base = list(TASK_CAPABILITY_MAP.get(req.task, TASK_CAPABILITY_MAP["chat"]))
    if req.needs_tools:
        base.extend(["tool_use", "code_agent"])
    if req.needs_vision:
        base.extend(["vision", "multimodal"])
    seen: set[str] = set()
    out: list[str] = []
    for item in base:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _is_remote(record: dict[str, Any]) -> bool:
    haystack = " ".join(str(record.get(k) or "") for k in ("name", "model", "base_url", "provider")).lower()
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        haystack += " " + " ".join(str(v).lower() for v in metadata.values() if isinstance(v, (str, int, float, bool)))
    return any(marker in haystack for marker in REMOTE_MARKERS)


def _backend_configured(backends: dict[str, Any], route_kind: str) -> bool:
    backend = backends.get(route_kind)
    return bool(isinstance(backend, dict) and backend.get("configured"))


def _score_model(record: dict[str, Any], req: InferenceRouteRequest, desired_caps: list[str]) -> dict[str, Any] | None:
    caps = {str(item) for item in record.get("capabilities") or []}
    mods = {str(item) for item in record.get("modalities") or []}
    if desired_caps and not (set(desired_caps) & caps):
        return None
    if req.modalities and not (set(req.modalities) <= mods):
        return None
    if req.needs_tools and not ({"tool_use", "code_agent"} & caps):
        return None
    if req.needs_vision and not ({"vision", "multimodal", "document_ocr"} & caps):
        return None

    provider = str(record.get("provider") or "unknown")
    score = PROVIDER_WEIGHTS.get(provider, 0)
    score += sum(CAPABILITY_WEIGHTS.get(cap, 4) for cap in set(desired_caps) & caps)
    if record.get("enabled", True):
        score += 12
    else:
        score -= 50
    if record.get("default"):
        score += 4
    if req.prefer_provider and provider == req.prefer_provider:
        score += 20
    remote = _is_remote(record)
    if req.prefer_remote and remote:
        score += 12
    if not req.prefer_remote and not remote:
        score += 6
    if provider == "echo":
        score -= 60

    return {
        "route_kind": "model",
        "name": record.get("name") or record.get("model"),
        "provider": provider,
        "model": record.get("model"),
        "endpoint_type": record.get("endpoint_type"),
        "capabilities": sorted(caps),
        "modalities": sorted(mods),
        "score": round(float(score), 2),
        "remote": remote,
        "enabled": bool(record.get("enabled", True)),
        "reason": "matched_model_capabilities",
    }


def _tool_candidates(report: dict[str, Any], req: InferenceRouteRequest, desired_caps: list[str]) -> list[dict[str, Any]]:
    backends = report.get("backends") or {}
    tool_contracts = report.get("tool_contracts") or {}
    out: list[dict[str, Any]] = []
    for name, contract in tool_contracts.items():
        caps = {str(item) for item in contract.get("capabilities") or []}
        if desired_caps and not (set(desired_caps) & caps):
            continue
        backend_env = list(contract.get("backend_env") or [])
        route_kind = "code_interpreter" if "code_interpreter" in caps else "image_generation" if "image_generation" in caps else "search"
        configured = _backend_configured(backends, route_kind)
        if req.require_live_backend and not configured:
            continue
        score = 35 + sum(CAPABILITY_WEIGHTS.get(cap, 4) for cap in set(desired_caps) & caps)
        if configured:
            score += 25
        out.append(
            {
                "route_kind": "tool",
                "name": name,
                "provider": route_kind,
                "capabilities": sorted(caps),
                "modalities": ["execution"] if "code_execution" in caps else ["image"] if "image_generation" in caps else ["text"],
                "score": round(float(score), 2),
                "backend_configured": configured,
                "backend_env": backend_env,
                "witness_type": contract.get("witness_type"),
                "observer_id": contract.get("observer_id"),
                "bounds": contract.get("bounds"),
                "reason": "matched_tool_contract",
            }
        )
    return out


def plan_inference_route(report: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    req = InferenceRouteRequest.from_payload(payload)
    desired_caps = _capabilities_for(req)
    models = report.get("models") or []
    candidates: list[dict[str, Any]] = []
    for model in models:
        if isinstance(model, dict):
            scored = _score_model(model, req, desired_caps)
            if scored:
                candidates.append(scored)
    candidates.extend(_tool_candidates(report, req, desired_caps))
    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    selected = candidates[0] if candidates else None
    warnings: list[str] = []
    if not candidates:
        warnings.append("no_matching_route")
    if selected and selected.get("route_kind") == "tool" and not selected.get("backend_configured", True):
        warnings.append("selected_tool_backend_not_configured")
    if selected and selected.get("provider") == "echo":
        warnings.append("selected_echo_fallback")
    result = {
        "schema_version": "inference-route-v1",
        "request": {
            "task": req.task,
            "capability": req.capability,
            "modalities": list(req.modalities),
            "prefer_provider": req.prefer_provider,
            "prefer_remote": req.prefer_remote,
            "needs_tools": req.needs_tools,
            "needs_vision": req.needs_vision,
            "require_live_backend": req.require_live_backend,
            "max_candidates": req.max_candidates,
        },
        "desired_capabilities": desired_caps,
        "selected": selected,
        "candidates": candidates[: req.max_candidates],
        "warnings": warnings,
    }
    result["route_digest"] = sha256_ref({k: v for k, v in result.items() if k != "route_digest"})
    return result
