from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from .evidence import EvidenceKernel, shake256_ref


def expand_env(value: Any) -> Any:
    if isinstance(value, str):
        out = value
        for key, env_value in os.environ.items():
            out = out.replace("${" + key + "}", env_value)
        return out
    return value


@dataclass(frozen=True)
class RuntimeModule:
    id: str
    kind: str
    profile: str = "core"
    endpoint: str | None = None
    image: str | None = None
    command: list[str] | None = None
    capabilities: list[str] | None = None
    evidence_outputs: list[str] | None = None
    enabled: bool = True
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "profile": self.profile,
            "endpoint": self.endpoint,
            "image": self.image,
            "command": self.command or [],
            "capabilities": self.capabilities or [],
            "evidence_outputs": self.evidence_outputs or [],
            "enabled": self.enabled,
            "metadata": self.metadata or {},
        }


DEFAULT_MODULES = [
    RuntimeModule(id="runtime.kernel", kind="control_plane", profile="core", capabilities=["evidence", "policy", "non_collapse", "mcp"], evidence_outputs=["WitnessEnvelope", "PolicyDecision"]),
    RuntimeModule(id="ollama.local", kind="model_provider", profile="models", endpoint="http://ollama:11434", capabilities=["text_generation", "embeddings"], evidence_outputs=["ModelOutputWitness", "EmbeddingWitness"], enabled=False),
    RuntimeModule(id="llama_cpp.local", kind="model_provider", profile="models", endpoint="http://llama-cpp:8080/v1", capabilities=["openai_chat_completion"], evidence_outputs=["ModelOutputWitness"], enabled=False),
    RuntimeModule(id="tlaplus.tlc", kind="formal_observer", profile="formal", image="localhost/duotronic-tlaplus:latest", capabilities=["model_check"], evidence_outputs=["TLAObserverWitness"], enabled=False),
    RuntimeModule(id="lean4.local", kind="proof_observer", profile="formal", image="localhost/duotronic-lean4:latest", capabilities=["proof_check"], evidence_outputs=["LeanProofWitness"], enabled=False),
    RuntimeModule(id="stable_diffusion.local", kind="media_generator", profile="media", endpoint="http://stable-diffusion:7860", capabilities=["image_generation"], evidence_outputs=["MediaGenerationWitness"], enabled=False),
    RuntimeModule(id="transformers_js.local", kind="encoder", profile="encoders", endpoint="http://transformers-js:8090", capabilities=["embedding", "classification"], evidence_outputs=["EmbeddingWitness"], enabled=False),
    RuntimeModule(id="librechat.surface", kind="ui_surface", profile="ui", endpoint="http://librechat:3080", capabilities=["chat_ui"], evidence_outputs=["ConversationSurfaceWitness"], enabled=False),
]


class ModuleRegistry:
    def __init__(self, path: Path | None = None, observer_id: str = "module-registry") -> None:
        self.path = path
        self.observer_id = observer_id
        self.kernel = EvidenceKernel(observer_id=observer_id)
        self.modules = self._load()

    def _load(self) -> list[RuntimeModule]:
        if not self.path or not self.path.exists():
            return DEFAULT_MODULES
        data = json.loads(self.path.read_text())
        out: list[RuntimeModule] = []
        for raw in data.get("modules", []):
            expanded = {k: expand_env(v) for k, v in raw.items()}
            enabled_env = expanded.get("enabled_env")
            if enabled_env:
                expanded["enabled"] = str(os.environ.get(str(enabled_env), "false")).lower() in {"1", "true", "yes", "on"}
            out.append(RuntimeModule(**{k: expanded[k] for k in RuntimeModule.__dataclass_fields__.keys() if k in expanded}))
        return out or DEFAULT_MODULES

    def list(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        modules = self.modules
        if enabled_only:
            modules = [m for m in modules if m.enabled]
        return [m.to_dict() for m in modules]

    def get(self, module_id: str) -> RuntimeModule:
        for module in self.modules:
            if module.id == module_id:
                return module
        raise KeyError(f"unknown module: {module_id}")

    def capability_report(self) -> dict[str, Any]:
        modules = self.list()
        witness = self.kernel.witness("ModuleCapabilityReportWitness", {"module_count": len(modules), "modules_digest": shake256_ref(modules), "modules": modules}, force="observe")
        return {"modules": modules, "witness": witness}

    async def health(self, module_id: str) -> dict[str, Any]:
        module = self.get(module_id)
        status = "disabled" if not module.enabled else "unknown"
        detail: dict[str, Any] = {}
        if module.enabled and module.endpoint:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(module.endpoint.rstrip("/") + "/health")
                status = "ok" if response.status_code < 500 else "degraded"
                detail = {"http_status": response.status_code, "body_preview": response.text[:300]}
            except Exception as exc:
                status = "unreachable"
                detail = {"error": str(exc)}
        witness = self.kernel.witness("ModuleHealthWitness", {"module": module.to_dict(), "status": status, "detail": detail}, force="observe", status="accepted" if status == "ok" else "recorded")
        return {"module": module.to_dict(), "status": status, "detail": detail, "witness": witness}
