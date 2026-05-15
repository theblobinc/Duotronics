from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TIER_SCORE = {
    "fast_tiny": 100,
    "pure_gpu": 70,
    "vision": 65,
    "specialized": 60,
    "hybrid": 68,
    "moe_candidate": 45,
    "cpu_heavy": 25,
}

KV_POLICY_SCORE = {
    "f16": 100,
    "q8_0": 90,
    "q4_0": 70,
    "turboquant_3_5bit": 40,
    "turboquant_2_5bit": 20,
    "backend_default": 65,
    "not_applicable": 100,
}


@dataclass(frozen=True)
class RoutePreviewRequest:
    task: str = "small_chat"
    capability: str | None = None
    tokens_estimate: int = 2048
    needs_tools: bool = False
    needs_vision: bool = False
    prefer_backend: str | None = None
    allow_experimental: bool = False
    slow_mode: bool = False


class ModelOrchestrator:
    """Read-only model/backend/KV policy planner.

    This does not download, load, unload, or mutate model state. It centralizes
    catalog metadata so the runtime, MCP tools, and UI can agree on capabilities,
    backend preference, hardware tiers, KV-cache policy, and safe route previews.
    """

    def __init__(self, manifest_path: Path | None = None, runtime_models: list[dict[str, Any]] | None = None) -> None:
        self.manifest_path = manifest_path
        self.runtime_models = runtime_models or []
        self.manifest = self._load_manifest(manifest_path)

    def _load_manifest(self, manifest_path: Path | None) -> dict[str, Any]:
        if not manifest_path or not manifest_path.exists():
            return {
                "schema_version": "model-orchestrator.v1",
                "hardware_profiles": {},
                "kv_policies": {},
                "routing_policies": {"default": {}},
                "models": {},
                "warnings": [f"manifest_missing:{manifest_path}" if manifest_path else "manifest_missing"],
            }
        try:
            return json.loads(manifest_path.read_text())
        except Exception as exc:
            return {
                "schema_version": "model-orchestrator.v1",
                "hardware_profiles": {},
                "kv_policies": {},
                "routing_policies": {"default": {}},
                "models": {},
                "warnings": [f"manifest_invalid:{exc}"],
            }

    def _installed_tags(self) -> set[str]:
        tags: set[str] = set()
        for record in self.runtime_models:
            for value in (record.get("model"), record.get("name")):
                if value:
                    tags.add(str(value).replace("ollama:", ""))
        return tags

    def catalog(self) -> dict[str, Any]:
        installed = self._installed_tags()
        models = []
        for model_id, model in self.manifest.get("models", {}).items():
            storage = model.get("storage", {}) if isinstance(model, dict) else {}
            ollama_tag = storage.get("ollama_tag") or model_id
            model = dict(model)
            model["id"] = model_id
            model["installed"] = bool(ollama_tag in installed or model_id in installed)
            model["desired"] = bool(storage.get("desired"))
            model["available_backends"] = self._available_backends(model)
            models.append(model)
        return {
            "schema_version": self.manifest.get("schema_version"),
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "hardware_profiles": self.manifest.get("hardware_profiles", {}),
            "kv_policies": self.manifest.get("kv_policies", {}),
            "routing_policies": self.manifest.get("routing_policies", {}),
            "models": sorted(models, key=lambda item: (item.get("tier", ""), item.get("label", item.get("id", "")))),
            "installed_runtime_tags": sorted(installed),
            "warnings": self.manifest.get("warnings", []),
        }

    def capabilities(self) -> dict[str, Any]:
        buckets: dict[str, list[str]] = {}
        for model_id, model in self.manifest.get("models", {}).items():
            for capability in model.get("capabilities", []):
                buckets.setdefault(str(capability), []).append(model_id)
        return {key: sorted(value) for key, value in sorted(buckets.items())}

    def kv_policy_matrix(self) -> dict[str, Any]:
        matrix = {}
        for model_id, model in self.manifest.get("models", {}).items():
            profiles = model.get("serving_profiles", {})
            matrix[model_id] = {
                name: {
                    "kv_policy": profile.get("kv_policy", "backend_default"),
                    "ctx_size": profile.get("ctx_size"),
                    "backend": profile.get("backend"),
                    "enabled": profile.get("enabled", True),
                    "requires_benchmark": profile.get("requires_benchmark", False),
                }
                for name, profile in profiles.items()
            }
        return matrix

    def route_preview(self, request: RoutePreviewRequest | dict[str, Any]) -> dict[str, Any]:
        if isinstance(request, dict):
            req = RoutePreviewRequest(**{k: v for k, v in request.items() if k in RoutePreviewRequest.__dataclass_fields__})
        else:
            req = request
        routing = self.manifest.get("routing_policies", {}).get("default", {})
        policy = routing.get(req.task, {})
        capability = req.capability or policy.get("capability") or "chat"
        accepted_capabilities = list(policy.get("accepted_capabilities", [capability]))
        if req.capability and req.capability not in accepted_capabilities:
            accepted_capabilities.append(req.capability)
        tier_preference = list(policy.get("tier_preference", []))
        requested_kv = policy.get("kv_policy") or "q8_0"
        if req.tokens_estimate >= 16000 and requested_kv in {"f16", "q8_0", "backend_default"}:
            requested_kv = "q4_0"
        if req.tokens_estimate >= 32000 and req.allow_experimental:
            requested_kv = "turboquant_3_5bit"

        candidates = self._candidate_models(capability=capability, accepted_capabilities=accepted_capabilities, req=req, tier_preference=tier_preference)
        scored = [self._score_candidate(model_id, model, req, tier_preference, requested_kv) for model_id, model in candidates]
        scored.sort(key=lambda item: item["score"], reverse=True)
        best = scored[0] if scored else None
        return {
            "request": req.__dict__,
            "policy": policy,
            "selected": best,
            "candidates": scored[:8],
            "warnings": self._route_warnings(req, best, requested_kv),
        }

    def _candidate_models(self, *, capability: str, accepted_capabilities: list[str], req: RoutePreviewRequest, tier_preference: list[str]) -> list[tuple[str, dict[str, Any]]]:
        out: list[tuple[str, dict[str, Any]]] = []
        for model_id, model in self.manifest.get("models", {}).items():
            caps = set(model.get("capabilities", []))
            if not (set(accepted_capabilities) & caps):
                continue
            if req.needs_tools and not ({"agent", "code_agent", "tool_use"} & caps):
                continue
            if req.needs_vision and not ({"vision", "document_ocr", "multimodal"} & caps):
                continue
            if not req.slow_mode and model.get("tier") == "cpu_heavy":
                continue
            out.append((model_id, model))
        if not out and tier_preference:
            for model_id, model in self.manifest.get("models", {}).items():
                if model.get("tier") in tier_preference:
                    out.append((model_id, model))
        return out

    def _score_candidate(self, model_id: str, model: dict[str, Any], req: RoutePreviewRequest, tier_preference: list[str], requested_kv: str) -> dict[str, Any]:
        profiles = model.get("serving_profiles", {})
        profile_name, profile = self._select_profile(profiles, req, requested_kv)
        tier = str(model.get("tier", ""))
        score = TIER_SCORE.get(tier, 40)
        if tier in tier_preference:
            score += max(0, 45 - 8 * tier_preference.index(tier))
        elif tier_preference:
            score -= 18
        backend = profile.get("backend") if profile else None
        if req.prefer_backend and backend == req.prefer_backend:
            score += 12
        kv_policy = profile.get("kv_policy", "backend_default") if profile else "backend_default"
        score += KV_POLICY_SCORE.get(kv_policy, 50) / 10
        if req.tokens_estimate and profile and profile.get("ctx_size"):
            ctx = int(profile.get("ctx_size") or 0)
            if ctx >= req.tokens_estimate:
                score += 10
            else:
                score -= 25
        if profile and profile.get("enabled", True) is False:
            score -= 100
        if profile and profile.get("requires_benchmark"):
            score -= 8
        return {
            "model_id": model_id,
            "label": model.get("label", model_id),
            "tier": tier,
            "capabilities": model.get("capabilities", []),
            "profile": profile_name,
            "backend": backend,
            "kv_policy": kv_policy,
            "ctx_size": profile.get("ctx_size") if profile else None,
            "parallel": profile.get("parallel") if profile else None,
            "score": round(score, 2),
            "requires_benchmark": bool(profile and profile.get("requires_benchmark")),
            "experimental": bool(kv_policy.startswith("turboquant") or (profile and profile.get("backend") == "experimental")),
        }

    def _select_profile(self, profiles: dict[str, Any], req: RoutePreviewRequest, requested_kv: str) -> tuple[str | None, dict[str, Any]]:
        if not profiles:
            return None, {}

        def allowed_profile(item: tuple[str, dict[str, Any]]) -> bool:
            _name, profile = item
            if profile.get("enabled", True) is False and not req.allow_experimental:
                return False
            if profile.get("experimental") and not req.allow_experimental:
                # 32k candidates are allowed in route preview even without experimental
                # when they are the only way to satisfy the requested context, but
                # TurboQuant/backend-missing profiles stay gated.
                if str(profile.get("kv_policy", "")).startswith("turboquant") or profile.get("backend") == "experimental":
                    return False
            return True

        enabled = {k: v for k, v in profiles.items() if allowed_profile((k, v))}
        pool = enabled or profiles
        token_need = int(req.tokens_estimate or 0)

        def profile_score(item: tuple[str, dict[str, Any]]) -> tuple[int, int, int, int, int]:
            _name, profile = item
            ctx = int(profile.get("ctx_size") or 0)
            fits = 1 if ctx >= token_need else 0
            kv_match = 1 if profile.get("kv_policy") == requested_kv else 0
            backend_match = 1 if (not req.prefer_backend or profile.get("backend") == req.prefer_backend) else 0
            stable = 0 if profile.get("requires_benchmark") else 1
            # Prefer the smallest context that fits, to avoid needlessly selecting huge profiles.
            size_penalty = -ctx if fits else ctx
            return (fits, kv_match, backend_match, stable, size_penalty)

        name, profile = max(pool.items(), key=profile_score)
        return name, profile

    def _available_backends(self, model: dict[str, Any]) -> list[str]:
        return list(dict.fromkeys([p.get("backend") for p in model.get("serving_profiles", {}).values() if p.get("backend")]))

    def _route_warnings(self, req: RoutePreviewRequest, best: dict[str, Any] | None, requested_kv: str) -> list[str]:
        warnings: list[str] = []
        if not best:
            warnings.append("no_candidate_model_for_requested_capability")
            return warnings
        if best.get("experimental") and not req.allow_experimental:
            warnings.append("experimental_profile_selected_without_explicit_experimental_flag")
        if best.get("requires_benchmark"):
            warnings.append("selected_profile_requires_benchmark_before_promotion")
        if best.get("ctx_size") and int(best["ctx_size"]) >= 32768:
            warnings.append("long_32k_profile_should_be_treated_as_candidate_until_benchmarked")
        if str(best.get("kv_policy", "")).startswith("turboquant"):
            warnings.append("turboquant_is_research_candidate_and_not_enabled_in_current_backends")
        if best.get("tier") in {"hybrid", "cpu_heavy"}:
            warnings.append("hybrid_or_cpu_heavy_route_should_force_parallel_1_and_user_visible_slow_mode")
        if req.tokens_estimate and best.get("ctx_size") and int(best["ctx_size"]) < req.tokens_estimate:
            warnings.append("selected_profile_context_is_smaller_than_estimated_tokens")
        if requested_kv == "q4_0":
            warnings.append("q4_kv_requires_quality_smoke_tests_for_code_tool_and_retrieval_tasks")
        return warnings
