from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class MoEBackendProfile:
    name: str
    label: str
    backend: str = "llama_cpp"
    base_url: str = ""
    health_endpoint: str = "/health"
    capabilities: list[str] = field(default_factory=list)
    ctx_size: int = 8192
    n_gpu_layers: str | int = "auto"
    n_cpu_moe: int | None = None
    cache_type_k: str = "q4_0"
    cache_type_v: str = "q4_0"
    kv_quant_recipe: str = "q4_0"
    attention_compression_mode: str = "kv_quant"
    prompt_compaction_mode: str = "none"
    parallel: int = 1
    requires_benchmark: bool = True
    experimental: bool = True
    timeout: float = 5.0
    healthy: bool = False
    status: str = "unknown"
    last_error: str = ""
    last_check: float = 0.0

    def runtime_form_fields(self) -> dict[str, str]:
        fields: dict[str, Any] = {
            "n_ctx": self.ctx_size,
            "n_gpu_layers": self.n_gpu_layers,
            "cache_type_k": self.cache_type_k,
            "cache_type_v": self.cache_type_v,
            "kv_quant_recipe": self.kv_quant_recipe,
            "attention_compression_mode": self.attention_compression_mode,
            "prompt_compaction_mode": self.prompt_compaction_mode,
            "parallel": self.parallel,
        }
        if self.n_cpu_moe is not None:
            fields["n_cpu_moe"] = self.n_cpu_moe
        return {k: str(v) for k, v in fields.items() if v is not None and str(v) != ""}

    def public(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "backend": self.backend,
            "base_url": self.base_url or None,
            "health_endpoint": self.health_endpoint,
            "capabilities": self.capabilities,
            "ctx_size": self.ctx_size,
            "runtime_form_fields": self.runtime_form_fields(),
            "requires_benchmark": self.requires_benchmark,
            "experimental": self.experimental,
            "healthy": self.healthy,
            "status": self.status,
            "last_error": self.last_error or None,
            "last_check": self.last_check,
        }


class MoERouter:
    def __init__(self) -> None:
        self.profiles: dict[str, MoEBackendProfile] = {
            "deepseek-coder-v2-lite-32k": MoEBackendProfile(
                name="deepseek-coder-v2-lite-32k",
                label="DeepSeek Coder V2 Lite MoE 32k candidate",
                capabilities=["moe", "coding", "code_agent", "long_context", "reasoning"],
                ctx_size=32768,
                n_gpu_layers="auto",
                n_cpu_moe=16,
                cache_type_k="q4_0",
                cache_type_v="q4_0",
                kv_quant_recipe="q4_0",
            ),
            "qwen3-14b-32k-hybrid": MoEBackendProfile(
                name="qwen3-14b-32k-hybrid",
                label="Qwen3 14B hybrid 32k candidate",
                capabilities=["reasoning", "plan", "long_context"],
                ctx_size=32768,
                n_gpu_layers="auto",
                n_cpu_moe=None,
                cache_type_k="q4_0",
                cache_type_v="q4_0",
                kv_quant_recipe="q4_0",
            ),
            "turboquant-sidecar": MoEBackendProfile(
                name="turboquant-sidecar",
                label="TurboQuant vector sidecar",
                backend="turboquant_sidecar",
                capabilities=["vector_compress", "sidecar_retrieval", "approximate_similarity"],
                ctx_size=0,
                cache_type_k="not_applicable",
                cache_type_v="not_applicable",
                kv_quant_recipe="turbo25_or_turbo35",
                attention_compression_mode="sidecar_vector_quant",
                requires_benchmark=False,
                experimental=False,
            ),
        }

    async def check_health(self, name: str, force: bool = False) -> dict[str, Any]:
        if name not in self.profiles:
            raise KeyError(name)
        profile = self.profiles[name]
        now = time.time()
        if not force and now - profile.last_check < 30:
            return profile.public()
        if not profile.base_url:
            profile.healthy = profile.backend == "turboquant_sidecar"
            profile.status = "local_sidecar" if profile.healthy else "unconfigured"
            profile.last_error = "" if profile.healthy else "base_url_not_configured"
            profile.last_check = now
            return profile.public()
        try:
            async with httpx.AsyncClient(timeout=profile.timeout) as client:
                resp = await client.get(profile.base_url.rstrip("/") + profile.health_endpoint)
            profile.healthy = resp.status_code == 200
            profile.status = "ok" if profile.healthy else f"http_{resp.status_code}"
            profile.last_error = "" if profile.healthy else resp.text[:200]
        except Exception as exc:
            profile.healthy = False
            profile.status = "offline"
            profile.last_error = str(exc)
        profile.last_check = now
        return profile.public()

    async def status(self, force: bool = False) -> dict[str, Any]:
        items = []
        for name in list(self.profiles):
            items.append(await self.check_health(name, force=force))
        return {"profiles": items, "healthy": [p["name"] for p in items if p["healthy"]]}

    def runtime_form_fields(self, name: str) -> dict[str, str]:
        if name not in self.profiles:
            raise KeyError(name)
        return self.profiles[name].runtime_form_fields()

    def route(self, capability: str, tokens_estimate: int = 2048, allow_experimental: bool = False) -> dict[str, Any]:
        candidates = []
        for profile in self.profiles.values():
            if capability not in profile.capabilities:
                continue
            if profile.experimental and not allow_experimental:
                continue
            if profile.ctx_size and tokens_estimate > profile.ctx_size:
                continue
            candidates.append(profile.public())
        candidates.sort(key=lambda p: (p.get("healthy", False), not p.get("requires_benchmark", True), p.get("ctx_size") or 0), reverse=True)
        return {"capability": capability, "tokens_estimate": tokens_estimate, "selected": candidates[0] if candidates else None, "candidates": candidates}
