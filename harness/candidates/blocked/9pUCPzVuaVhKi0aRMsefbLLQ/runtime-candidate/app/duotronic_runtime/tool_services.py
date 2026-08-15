from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import httpx

from .config import Settings
from .evidence import shake256_ref


@dataclass
class ToolRuntime:
    settings: Settings
    kernel: Any

    @property
    def data_dir(self) -> Path:
        path = self.settings.runtime_data_dir / "tools"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def artifact_dir(self) -> Path:
        path = self.data_dir / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def record_witness(self, witness_type: str, payload: dict[str, Any], *, status: str = "recorded", observer_id: str = "tool-runtime") -> dict[str, Any]:
        payload = {**payload, "observer_id": observer_id}
        witness = self.kernel.evidence.witness(witness_type, payload, force="observe", status=status)
        self.kernel.store.insert_witness(witness)
        return witness

    def write_artifact(self, data: bytes, suffix: str, media_type: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        digest = shake256_ref(data)
        artifact_id = "artifact_" + digest.split(":", 1)[1][:32]
        filename = artifact_id + suffix
        path = self.artifact_dir / filename
        if not path.exists():
            path.write_bytes(data)
        meta = {
            "artifact_id": artifact_id,
            "filename": filename,
            "path": str(path),
            "url": f"/v1/tools/artifacts/{artifact_id}",
            "media_type": media_type,
            "size_bytes": len(data),
            "digest": digest,
            "metadata": metadata or {},
            "created_at_ms": int(time.time() * 1000),
        }
        (self.artifact_dir / f"{artifact_id}.json").write_text(json.dumps(meta, indent=2))
        return meta

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        meta_path = self.artifact_dir / f"{artifact_id}.json"
        if not meta_path.exists():
            return None
        return json.loads(meta_path.read_text())

    def code_disabled(self, *, language: str, code: str) -> dict[str, Any]:
        contract = self.tool_contracts()["code_interpreter_execute"]
        payload = {
            "language": language,
            "code_digest": shake256_ref(code),
            "status": "requires_sandbox_backend",
            "message": "Code interpreter API is wired, but no hardened execution sandbox backend is configured yet.",
            "required_backend": contract["backend_env"][0],
            "sandbox": {"network": contract["bounds"].get("network", False), "host_access": contract["bounds"].get("host_access", False)},
            "created_at_ms": int(time.time() * 1000),
        }
        witness = self.record_witness(contract["witness_type"], payload, status=contract["fallback_status"], observer_id=contract["observer_id"])
        return {"ok": False, "error": contract["disabled_error"], "witness": witness, **payload}

    async def code_execute(self, *, language: str, code: str, timeout_seconds: int = 30, stdin: str = "") -> dict[str, Any]:
        endpoint = os.environ.get("CODE_INTERPRETER_URL", "")
        if not endpoint:
            return self.code_disabled(language=language, code=code)
        async with httpx.AsyncClient(timeout=max(1, min(int(timeout_seconds), 60)) + 5.0) as client:
            response = await client.post(endpoint.rstrip("/") + "/execute", json={"language": language, "code": code, "stdin": stdin, "timeout_seconds": timeout_seconds})
            response.raise_for_status()
            result = response.json()
        payload = {"language": language, "code_digest": shake256_ref(code), "backend": endpoint, "result": result, "created_at_ms": int(time.time() * 1000)}
        witness = self.record_witness("CodeExecutionWitness", payload, status="accepted" if result.get("ok") else "recorded", observer_id="code_interpreter.local")
        return {"ok": bool(result.get("ok")), "witness": witness, **payload}

    async def search_xavi(self, *, query: str, top_k: int = 5, engine: str = "xavi") -> dict[str, Any]:
        query = query.strip()
        top_k = max(1, min(int(top_k), 10))
        base_url = self.settings.xavi_search_url or os.environ.get("XAVI_SEARCH_URL") or os.environ.get("SEARCH_API_URL") or ""
        api_key = self.settings.xavi_search_api_key or os.environ.get("XAVI_SEARCH_API_KEY") or os.environ.get("SEARCH_API_KEY") or ""
        results: list[dict[str, Any]] = []
        errors: list[str] = []
        source = "fallback"
        if base_url:
            async with httpx.AsyncClient(timeout=20.0) as client:
                headers = {"accept": "application/json"}
                if api_key:
                    headers["authorization"] = "Bearer " + api_key
                urls = [
                    ("GET", f"{base_url.rstrip('/')}/search?q={quote_plus(query)}&limit={top_k}"),
                    ("GET", f"{base_url.rstrip('/')}/api/search?q={quote_plus(query)}&limit={top_k}"),
                    ("POST", f"{base_url.rstrip('/')}/search"),
                    ("POST", f"{base_url.rstrip('/')}/api/search"),
                ]
                for method, url in urls:
                    try:
                        r = await client.get(url, headers=headers) if method == "GET" else await client.post(url, headers=headers, json={"query": query, "top_k": top_k, "limit": top_k})
                        if r.status_code >= 400:
                            errors.append(f"{method} status={r.status_code}")
                            continue
                        data = r.json()
                        raw = data.get("results") or data.get("items") or data.get("data") or []
                        if isinstance(raw, dict):
                            raw = list(raw.values())
                        for item in raw[:top_k]:
                            if isinstance(item, dict):
                                results.append({
                                    "title": str(item.get("title") or item.get("name") or item.get("url") or "Untitled"),
                                    "url": str(item.get("url") or item.get("link") or ""),
                                    "snippet": str(item.get("snippet") or item.get("summary") or item.get("content") or "")[:2000],
                                    "source": str(item.get("source") or engine),
                                    "score": item.get("score"),
                                })
                        if results:
                            source = url
                            break
                    except Exception as exc:
                        errors.append(f"{method} {exc.__class__.__name__}")
        if not results:
            results = [{"title": "Xavi search engine not configured", "url": "", "snippet": "Set XAVI_SEARCH_URL or SEARCH_API_URL to enable live Xavi web search evidence.", "source": "runtime.fallback", "score": 0}]
        payload = {"query": query, "engine": engine, "source": source, "top_k": top_k, "results": results, "errors": errors, "retrieved_at_ms": int(time.time() * 1000), "results_digest": shake256_ref(json.dumps(results, sort_keys=True))}
        witness = self.record_witness("SearchResultWitness", payload, status="accepted" if source != "fallback" else "recorded", observer_id="search.xavi")
        return {"ok": True, "witness": witness, **payload}

    async def generate_image(self, *, prompt: str, size: str = "1024x1024", model: str | None = None, n: int = 1) -> dict[str, Any]:
        endpoint = self.settings.stable_diffusion_url or os.environ.get("STABLE_DIFFUSION_URL") or os.environ.get("IMAGE_GENERATION_URL") or ""
        n = max(1, min(int(n), 4))
        images: list[dict[str, Any]] = []
        errors: list[str] = []
        if endpoint:
            async with httpx.AsyncClient(timeout=120.0) as client:
                candidates = [(f"{endpoint.rstrip('/')}/sdapi/v1/txt2img", {"prompt": prompt, "batch_size": n}), (f"{endpoint.rstrip('/')}/v1/images/generations", {"prompt": prompt, "size": size, "model": model, "n": n})]
                for url, body in candidates:
                    try:
                        r = await client.post(url, json={k: v for k, v in body.items() if v is not None})
                        if r.status_code >= 400:
                            errors.append(f"status={r.status_code}")
                            continue
                        data = r.json()
                        raw_images = data.get("images") or []
                        if not raw_images and isinstance(data.get("data"), list):
                            raw_images = [x.get("b64_json") or x.get("url") for x in data["data"] if isinstance(x, dict)]
                        for item in raw_images[:n]:
                            if isinstance(item, str) and item.startswith("http"):
                                images.append({"url": item, "media_type": "image/remote", "digest": shake256_ref(item)})
                            elif isinstance(item, str):
                                data_bytes = base64.b64decode(item.split(",")[-1])
                                images.append(self.write_artifact(data_bytes, ".png", "image/png", {"prompt_digest": shake256_ref(prompt), "generator": url}))
                        if images:
                            break
                    except Exception as exc:
                        errors.append(exc.__class__.__name__)
        payload = {"prompt": prompt, "prompt_digest": shake256_ref(prompt), "size": size, "model": model, "n": n, "images": images, "errors": errors, "enabled": bool(endpoint), "created_at_ms": int(time.time() * 1000)}
        witness = self.record_witness("MediaGenerationWitness", payload, status="accepted" if images else "recorded", observer_id="image_generation.local")
        return {"ok": bool(images), "witness": witness, **payload}

    def tool_contracts(self) -> dict[str, dict[str, Any]]:
        return {
            "code_interpreter_execute": {
                "witness_type": "CodeExecutionWitness",
                "observer_id": "code_interpreter.local",
                "capabilities": ["artifact_output", "code_execution", "code_interpreter"],
                "backend_env": ["CODE_INTERPRETER_URL"],
                "bounds": {"timeout_seconds": {"minimum": 1, "maximum": 60}, "network": False, "host_access": False},
                "success_status": "accepted",
                "fallback_status": "recorded",
                "disabled_error": "code_interpreter_backend_not_configured",
            },
            "image_generate": {
                "witness_type": "MediaGenerationWitness",
                "observer_id": "image_generation.local",
                "capabilities": ["artifact_output", "image_generation"],
                "backend_env": ["STABLE_DIFFUSION_URL", "IMAGE_GENERATION_URL"],
                "bounds": {"n": {"minimum": 1, "maximum": 4}, "timeout_seconds": 120},
                "success_status": "accepted",
                "fallback_status": "recorded",
                "disabled_error": "image_generation_backend_not_configured",
            },
            "xavi_search_evidence": {
                "witness_type": "SearchResultWitness",
                "observer_id": "search.xavi",
                "capabilities": ["evidence_retrieval", "search"],
                "backend_env": ["XAVI_SEARCH_URL", "SEARCH_API_URL"],
                "bounds": {"top_k": {"minimum": 1, "maximum": 10}, "timeout_seconds": 20},
                "success_status": "accepted",
                "fallback_status": "recorded",
                "disabled_error": None,
            },
            "operation_plan": {
                "witness_type": "OperationPlanWitness",
                "observer_id": "operation_planner.local",
                "capabilities": ["logic", "operation_planning", "witness_contract"],
                "backend_env": [],
                "bounds": {"read_only": True, "execution_mode": "planned_only"},
                "success_status": "accepted",
                "fallback_status": "recorded",
                "disabled_error": None,
            },
        }

    def capability_report(self, models: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        models = models or []
        tools = self.openai_tools()

        normalized_models: list[dict[str, Any]] = []
        model_capabilities: dict[str, list[str]] = {}
        modalities: dict[str, list[str]] = {}
        providers: dict[str, int] = {}

        for model in models:
            name = str(model.get("name") or model.get("model") or "unknown").strip() or "unknown"
            provider = str(model.get("provider") or "unknown").strip() or "unknown"
            caps = sorted({str(item) for item in (model.get("capabilities") or []) if item})
            mods = sorted({str(item) for item in (model.get("modalities") or []) if item})
            providers[provider] = providers.get(provider, 0) + 1
            model_capabilities[name] = caps
            modalities[name] = mods
            normalized_models.append({**model, "name": name, "provider": provider, "capabilities": caps, "modalities": mods})

        tool_contracts = self.tool_contracts()
        tool_capabilities = {name: list(contract["capabilities"]) for name, contract in tool_contracts.items()}

        all_capabilities = sorted(
            {cap for caps in model_capabilities.values() for cap in caps} | {cap for caps in tool_capabilities.values() for cap in caps}
        )

        backends = {
            "code_interpreter": {"configured": bool(os.environ.get("CODE_INTERPRETER_URL", "")), "env": "CODE_INTERPRETER_URL"},
            "image_generation": {
                "configured": bool(self.settings.stable_diffusion_url or os.environ.get("STABLE_DIFFUSION_URL") or os.environ.get("IMAGE_GENERATION_URL")),
                "env": "STABLE_DIFFUSION_URL|IMAGE_GENERATION_URL",
            },
            "search": {
                "configured": bool(self.settings.xavi_search_url or os.environ.get("XAVI_SEARCH_URL") or os.environ.get("SEARCH_API_URL")),
                "env": "XAVI_SEARCH_URL|SEARCH_API_URL",
            },
        }

        payload = {
            "schema_version": "capabilities-v1",
            "models": normalized_models,
            "model_count": len(normalized_models),
            "providers": dict(sorted(providers.items(), key=lambda item: item[0])),
            "model_capabilities": model_capabilities,
            "modalities": modalities,
            "tools": tools,
            "tool_capabilities": tool_capabilities,
            "tool_contracts": self.tool_contracts(),
            "capabilities": all_capabilities,
            "backends": backends,
            "created_at_ms": int(time.time() * 1000),
        }

        digest_payload = {
            "schema_version": payload["schema_version"],
            "models": [{"name": m.get("name"), "provider": m.get("provider"), "capabilities": m.get("capabilities"), "modalities": m.get("modalities")} for m in normalized_models],
            "tool_capabilities": tool_capabilities,
            "backends": backends,
        }
        payload["capabilities_digest"] = shake256_ref(json.dumps(digest_payload, sort_keys=True, default=str))
        return payload

    def openai_tools(self) -> list[dict[str, Any]]:
        return [
            {"type": "function", "function": {"name": "xavi_search_evidence", "description": "Search the Xavi/web search engine and return evidence-backed search results with a witness.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "minimum": 1, "maximum": 10}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "code_interpreter_execute", "description": "Run Python through the configured code-interpreter sandbox and return stdout, stderr, artifacts, and a witness.", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 60}}, "required": ["code"]}}},
            {"type": "function", "function": {"name": "image_generate", "description": "Generate an image through the configured image backend and return artifact references with a witness.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "size": {"type": "string"}}, "required": ["prompt"]}}},
        ]
