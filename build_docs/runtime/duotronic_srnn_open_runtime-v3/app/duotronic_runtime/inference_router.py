from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .evidence import shake256_ref


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
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        if metadata.get("node_id"):
            return True
        if str(metadata.get("transport") or "") in {"dedicated-private-ethernet", "dedicated-private-ethernet-pending"}:
            return True
    haystack = " ".join(str(record.get(k) or "") for k in ("name", "model", "base_url", "provider")).lower()
    if isinstance(metadata, dict):
        haystack += " " + " ".join(str(v).lower() for v in metadata.values() if isinstance(v, (str, int, float, bool)))
    return any(marker in haystack for marker in REMOTE_MARKERS)


def _backend_configured(backends: dict[str, Any], route_kind: str) -> bool:
    backend = backends.get(route_kind)
    return bool(isinstance(backend, dict) and backend.get("configured"))


def _normalize_endpoint(value: Any) -> str:
    return str(value or "").strip().rstrip("/")


def _model_service_name(record: dict[str, Any]) -> str | None:
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    explicit = str(metadata.get("service_name") or "").strip()
    if explicit:
        return explicit
    return {
        "ollama": "ollama",
        "llama_cpp": "llama_cpp",
    }.get(str(record.get("provider") or ""))


def _observe_live_model_backends(
    report: dict[str, Any],
    req: InferenceRouteRequest,
    service_registry: Any | None,
) -> dict[str, Any] | None:
    if not req.require_live_backend:
        return None
    if service_registry is None:
        return {
            "schema_version": "inference-live-backends-v1",
            "required": True,
            "available": False,
            "offline_only": True,
            "services": [],
            "observations": [],
            "skipped": [],
            "observation_digests": [],
            "healthy_count": 0,
        }

    services = sorted(
        {
            service_name
            for model in (report.get("models") or [])
            if isinstance(model, dict)
            for service_name in [_model_service_name(model)]
            if service_name
        }
    )
    observations: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    digests: list[str] = []
    observed_at_ms: list[int] = []
    for service_name in services:
        if service_name == "ollama" and hasattr(service_registry, "ollama_inventory"):
            observed = service_registry.ollama_inventory(timeout_seconds=1.5)
            observations.extend(row for row in (observed.get("observations") or []) if isinstance(row, dict))
            digest = str(observed.get("observation_digest") or "")
            health_digest = str(observed.get("service_health_digest") or "")
            if digest:
                digests.append(digest)
            if health_digest and health_digest not in digests:
                digests.append(health_digest)
            if observed.get("observed_at_ms") is not None:
                observed_at_ms.append(int(observed["observed_at_ms"]))
            continue
        health = service_registry.service_health(service=service_name, timeout_seconds=1.5)
        observations.extend(row for row in (health.get("observations") or []) if isinstance(row, dict))
        skipped.extend(row for row in (health.get("skipped") or []) if isinstance(row, dict))
        digest = str(health.get("observation_digest") or "")
        if digest:
            digests.append(digest)
        if health.get("observed_at_ms") is not None:
            observed_at_ms.append(int(health["observed_at_ms"]))
    return {
        "schema_version": "inference-live-backends-v1",
        "required": True,
        "available": True,
        "offline_only": True,
        "services": services,
        "observed_at_ms": max(observed_at_ms) if observed_at_ms else None,
        "observations": observations,
        "skipped": skipped,
        "observation_digests": digests,
        "healthy_count": sum(1 for row in observations if row.get("healthy") is True),
    }


def _live_state_for_model(record: dict[str, Any], live_backends: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(live_backends, dict):
        return {"observed": False, "healthy": None}
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    wanted_node = str(metadata.get("node_id") or "").strip()
    wanted_service = _model_service_name(record)
    wanted_endpoint = _normalize_endpoint(record.get("base_url"))
    matches: list[dict[str, Any]] = []
    for row in live_backends.get("observations") or []:
        if not isinstance(row, dict):
            continue
        if wanted_service and str(row.get("service") or "") != wanted_service:
            continue
        row_node = str(row.get("node_id") or "").strip()
        row_endpoint = _normalize_endpoint(row.get("endpoint"))
        if wanted_node and row_node == wanted_node:
            matches.append(row)
        elif wanted_endpoint and row_endpoint == wanted_endpoint:
            matches.append(row)
    if not matches:
        return {
            "observed": False,
            "healthy": False,
            "node_id": wanted_node or None,
            "service": wanted_service,
            "endpoint": wanted_endpoint or None,
        }
    selected = next((row for row in matches if row.get("healthy") is True), matches[0])
    selected_service = str(selected.get("service") or wanted_service or "").strip() or None
    requested_model = str(record.get("model") or "").strip()
    inventory_observed = bool(selected.get("inventory_observed", False))
    installed_models = [str(item) for item in (selected.get("models") or [])]
    model_available: bool | None = None
    if selected_service == "ollama":
        model_available = bool(inventory_observed and requested_model and requested_model in installed_models)
    return {
        "observed": True,
        "healthy": bool(selected.get("healthy")),
        "node_id": selected.get("node_id") or wanted_node or None,
        "service": selected_service,
        "endpoint": selected.get("endpoint") or wanted_endpoint or None,
        "latency_ms": selected.get("latency_ms"),
        "status_code": selected.get("status_code"),
        "inventory_observed": inventory_observed,
        "model_available": model_available,
        "installed_model_count": int(selected.get("model_count") or len(installed_models)),
        "observation_digests": list(live_backends.get("observation_digests") or []),
    }


def _score_model(
    record: dict[str, Any],
    req: InferenceRouteRequest,
    desired_caps: list[str],
    *,
    live_state: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
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
    metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
    remote = _is_remote(record)
    scheduler_eligible = metadata.get("scheduler_eligible")
    lan_preferred = bool(metadata.get("lan_preferred", False))
    internet_required = metadata.get("internet_required")
    node_status = str(metadata.get("node_status") or "")
    if req.prefer_remote and remote:
        score += 12
    if not req.prefer_remote and not remote:
        score += 6
    if lan_preferred and scheduler_eligible is True and node_status == "commissioned":
        score += 18
    if internet_required is False:
        score += 6
    if scheduler_eligible is False:
        score -= 80
    if metadata.get("node_id") and node_status and node_status != "commissioned":
        score -= 20
    if provider == "echo":
        score -= 60
    live_state = dict(live_state or {})
    if live_state.get("healthy") is True:
        score += 24

    return {
        "route_kind": "model",
        "name": record.get("name") or record.get("model"),
        "provider": provider,
        "model": record.get("model"),
        "base_url": record.get("base_url"),
        "endpoint_type": record.get("endpoint_type"),
        "capabilities": sorted(caps),
        "modalities": sorted(mods),
        "score": round(float(score), 2),
        "remote": remote,
        "node_id": metadata.get("node_id") or live_state.get("node_id"),
        "node_status": node_status or None,
        "transport": metadata.get("transport"),
        "lan_preferred": lan_preferred,
        "internet_required": internet_required,
        "scheduler_eligible": scheduler_eligible,
        "enabled": bool(record.get("enabled", True)),
        "live_backend_observed": bool(live_state.get("observed", False)),
        "live_backend_healthy": live_state.get("healthy"),
        "live_service": live_state.get("service"),
        "live_endpoint": live_state.get("endpoint"),
        "live_latency_ms": live_state.get("latency_ms"),
        "live_status_code": live_state.get("status_code"),
        "live_inventory_observed": bool(live_state.get("inventory_observed", False)),
        "live_model_available": live_state.get("model_available"),
        "live_installed_model_count": live_state.get("installed_model_count"),
        "live_observation_digests": list(live_state.get("observation_digests") or []),
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


def plan_inference_route(
    report: dict[str, Any],
    payload: dict[str, Any] | None = None,
    *,
    service_registry: Any | None = None,
) -> dict[str, Any]:
    req = InferenceRouteRequest.from_payload(payload)
    desired_caps = _capabilities_for(req)
    models = report.get("models") or []
    live_backends = _observe_live_model_backends(report, req, service_registry)
    candidates: list[dict[str, Any]] = []
    live_exclusions: list[dict[str, Any]] = []
    for model in models:
        if not isinstance(model, dict):
            continue
        live_state = _live_state_for_model(model, live_backends)
        scored = _score_model(model, req, desired_caps, live_state=live_state)
        if not scored:
            continue
        service_name = _model_service_name(model)
        provider = str(model.get("provider") or "unknown")
        if req.require_live_backend and (service_name or provider == "echo"):
            live_ok = provider != "echo" and live_state.get("healthy") is True
            if service_name == "ollama":
                live_ok = live_ok and live_state.get("model_available") is True
            if not live_ok:
                if provider == "echo":
                    exclusion_reason = "echo_is_not_a_live_model_backend"
                elif live_state.get("healthy") is not True:
                    exclusion_reason = "live_backend_unhealthy_or_unobserved"
                elif service_name == "ollama" and live_state.get("model_available") is not True:
                    exclusion_reason = "ollama_model_not_observed_installed"
                else:
                    exclusion_reason = "live_backend_requirement_not_satisfied"
                live_exclusions.append(
                    {
                        "name": model.get("name") or model.get("model"),
                        "provider": provider,
                        "model": model.get("model"),
                        "node_id": (model.get("metadata") or {}).get("node_id") if isinstance(model.get("metadata"), dict) else None,
                        "service": service_name,
                        "base_url": model.get("base_url"),
                        "live_observed": bool(live_state.get("observed", False)),
                        "live_healthy": live_state.get("healthy"),
                        "inventory_observed": bool(live_state.get("inventory_observed", False)),
                        "model_available": live_state.get("model_available"),
                        "reason": exclusion_reason,
                    }
                )
                continue
        candidates.append(scored)
    candidates.extend(_tool_candidates(report, req, desired_caps))
    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    selected = candidates[0] if candidates else None
    warnings: list[str] = []
    if req.require_live_backend and isinstance(live_backends, dict) and not live_backends.get("available"):
        warnings.append("live_backend_observer_unavailable")
    if live_exclusions:
        warnings.append("live_model_candidates_filtered")
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
        "live_backend_observation": live_backends,
        "live_exclusions": live_exclusions[: req.max_candidates],
        "warnings": warnings,
    }
    result["route_digest"] = shake256_ref({k: v for k, v in result.items() if k != "route_digest"})
    return result
