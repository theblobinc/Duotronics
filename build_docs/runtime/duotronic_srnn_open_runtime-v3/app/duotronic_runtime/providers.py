from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

from .config import Settings
from .prompting import DUOTRONIC_RUNTIME_SYSTEM_PROMPT, build_runtime_prompt


def expand_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value


class ModelRegistry:
    def __init__(self, path: Path, settings: Settings) -> None:
        self.path = path
        self.settings = settings
        self.records = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return [{"name": "sandbox-echo", "provider": "echo", "default": True, "enabled": True}]
        data = json.loads(self.path.read_text())
        out = []
        for record in data.get("models", []):
            rec = {k: expand_env(v) for k, v in record.items()}
            enabled_env = rec.get("enabled_env")
            if enabled_env:
                rec["enabled"] = os.environ.get(str(enabled_env), "false").lower() in {"1", "true", "yes", "on"}
            else:
                rec["enabled"] = bool(rec.get("enabled", True))
            out.append(rec)
        return out

    def _discover_ollama_models(self) -> list[dict[str, Any]]:
        """Return transient model records for models currently installed in Ollama."""
        if not getattr(self.settings, "ollama_enabled", False):
            return []

        base = str(getattr(self.settings, "ollama_host", "") or "").rstrip("/")
        if not base:
            return []

        try:
            timeout = httpx.Timeout(5.0, connect=2.0)
            with httpx.Client(timeout=timeout) as client:
                r = client.get(f"{base}/api/tags")
                r.raise_for_status()
                data = r.json()
        except Exception:
            return []

        discovered: list[dict[str, Any]] = []
        existing_names = {str(r.get("name") or "") for r in self.records}

        for item in data.get("models", []):
            if not isinstance(item, dict):
                continue
            tag = str(item.get("name") or item.get("model") or "").strip()
            if not tag:
                continue

            runtime_name = f"ollama:{tag}"
            if runtime_name in existing_names:
                continue

            discovered.append(
                {
                    "name": runtime_name,
                    "provider": "ollama",
                    "model": tag,
                    "base_url": base,
                    "enabled": True,
                    "default": False,
                    "description": "Discovered from Ollama /api/tags",
                    "discovered": True,
                }
            )

        return discovered

    def list_models(self) -> list[dict[str, Any]]:
        records = list(self.records)
        existing_names = {str(r.get("name") or "") for r in records}
        for record in self._discover_ollama_models():
            name = str(record.get("name") or "")
            if name and name not in existing_names:
                records.append(record)
                existing_names.add(name)
        return records

    def get(self, name: str | None = None) -> dict[str, Any]:
        enabled = [r for r in self.list_models() if r.get("enabled", True)]
        if name:
            for r in enabled:
                if r.get("name") == name:
                    return r
        for r in enabled:
            if r.get("default"):
                return r
        return enabled[0] if enabled else {"name": "sandbox-echo", "provider": "echo", "default": True}

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        record = dict(record)
        if not record.get("name") or not record.get("provider"):
            raise ValueError("model record requires name and provider")
        self.records = [r for r in self.records if r.get("name") != record["name"]] + [record]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"models": self.records}, indent=2))
        return record


class ModelProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.registry = ModelRegistry(settings.model_registry_path, settings)

    async def complete(self, *, prompt: str, model_name: str | None = None) -> dict[str, Any]:
        model = self.registry.get(model_name)
        provider = model.get("provider", "echo")
        runtime_prompt = build_runtime_prompt(
            prompt,
            runtime_context={
                "node_id": self.settings.node_id,
                "runtime_mode": self.settings.wg_rnn_runtime_mode,
                "policy_mode": self.settings.nla_policy_mode,
            },
        )
        if provider == "ollama":
            return await self._ollama(runtime_prompt, model)
        if provider == "llama_cpp":
            return await self._llama_cpp(runtime_prompt, model)
        return self._echo(runtime_prompt, model)

    def _echo(self, prompt: str, model: dict[str, Any]) -> dict[str, Any]:
        response = (
            "Sandbox model response: I will treat the prompt as evidence input, "
            "not as authority. Prompt digest length=" + str(len(prompt)) + "."
        )
        return {"model": model, "response_text": response, "provider_status": "local_echo"}

    async def _ollama(self, prompt: str, model: dict[str, Any]) -> dict[str, Any]:
        base = model.get("base_url") or self.settings.ollama_host
        name = model.get("model") or self.settings.ollama_default_model
        timeout = httpx.Timeout(
            connect=10.0,
            read=float(getattr(self.settings, "ollama_timeout_seconds", 180.0)),
            write=30.0,
            pool=10.0,
        )
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    f"{base.rstrip('/')}/api/generate",
                    json={
                        "model": name,
                        "prompt": prompt,
                        "system": DUOTRONIC_RUNTIME_SYSTEM_PROMPT,
                        "stream": False,
                        "options": {
                            "temperature": 0.15,
                            "top_p": 0.85,
                            "repeat_penalty": 1.08,
                        },
                    },
                )
                r.raise_for_status()
                data = r.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"ollama_timeout:{name}:{base}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"ollama_http_error:{name}:{base}:{exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"ollama_transport_error:{name}:{base}:{exc.__class__.__name__}") from exc
        return {"model": model | {"model": name}, "response_text": data.get("response", ""), "provider_status": "ollama"}

    async def _llama_cpp(self, prompt: str, model: dict[str, Any]) -> dict[str, Any]:
        base = model.get("base_url") or self.settings.llama_cpp_base_url
        name = model.get("model") or self.settings.llama_cpp_default_model
        body = {
            "model": name,
            "messages": [
                {"role": "system", "content": DUOTRONIC_RUNTIME_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.15,
            "top_p": 0.85,
        }
        timeout = httpx.Timeout(
            connect=10.0,
            read=float(getattr(self.settings, "llama_cpp_timeout_seconds", 180.0)),
            write=30.0,
            pool=10.0,
        )
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(f"{base.rstrip('/')}/chat/completions", json=body)
                r.raise_for_status()
                data = r.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"llama_cpp_timeout:{name}:{base}") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"llama_cpp_http_error:{name}:{base}:{exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"llama_cpp_transport_error:{name}:{base}:{exc.__class__.__name__}") from exc
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"model": model | {"model": name}, "response_text": content, "provider_status": "llama_cpp"}
