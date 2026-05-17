from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from .config import Settings
from .prompting import DUOTRONIC_RUNTIME_SYSTEM_PROMPT, build_runtime_prompt
from .response_normalizer import extract_model_response


def expand_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value


class ModelRegistry:
    def __init__(self, path: Path, settings: Settings) -> None:
        self.path = path
        self.settings = settings
        self.records = self._load()
        self._ollama_cache: list[dict[str, Any]] = []
        self._ollama_cache_ts: float = 0.0
        self._OLLAMA_CACHE_TTL = 30.0

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
        now = time.monotonic()
        if now - self._ollama_cache_ts < self._OLLAMA_CACHE_TTL:
            return self._ollama_cache
        configured_base = str(getattr(self.settings, "ollama_host", "") or "").rstrip("/")
        candidates = []
        for base in [
            configured_base,
            "http://ollama:11434",
            "http://host.containers.internal:11434",
        ]:
            if base and base not in candidates:
                candidates.append(base)

        data = None
        working_base = configured_base
        for base in candidates:
            try:
                timeout = httpx.Timeout(5.0, connect=2.0)
                with httpx.Client(timeout=timeout) as client:
                    r = client.get(f"{base}/api/tags")
                    r.raise_for_status()
                    data = r.json()
                    working_base = base
                    break
            except Exception:
                continue

        if data is None:
            self._ollama_cache = []
            self._ollama_cache_ts = time.monotonic()
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
                    "base_url": working_base,
                    "enabled": True,
                    "default": False,
                    "description": "Discovered from Ollama /api/tags",
                    "discovered": True,
                }
            )

        self._ollama_cache = discovered
        self._ollama_cache_ts = time.monotonic()
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

    def _model_tag(self, record: dict[str, Any]) -> str:
        return str(record.get("model") or record.get("name") or "").strip()

    def _is_non_chat_model(self, record: dict[str, Any]) -> bool:
        tag = self._model_tag(record).lower()
        name = str(record.get("name") or "").lower()
        haystack = f"{name} {tag}"
        # Ollama exposes embedding-only models through /api/tags. They are valid
        # inventory entries but should not be advertised to OpenAI chat clients.
        non_chat_markers = ("embed", "embedding", "nomic-embed")
        return any(marker in haystack for marker in non_chat_markers)

    def _has_reachable_chat_backend(self, record: dict[str, Any]) -> bool:
        provider = str(record.get("provider") or "")
        if provider != "ollama":
            return False
        base = str(record.get("base_url") or self.settings.ollama_host or "")
        # In the runtime container this backend is currently unreachable and
        # produces immediate ConnectError responses. Do not advertise those aliases
        # to LibreChat; keep explicit calls possible for debugging.
        if "host.containers.internal" in base:
            return False
        return True

    def is_openai_chat_visible(self, record: dict[str, Any]) -> bool:
        if not record.get("enabled", True):
            return False
        if self._is_non_chat_model(record):
            return False
        return self._has_reachable_chat_backend(record)

    def list_openai_chat_models(self) -> list[dict[str, Any]]:
        """Return model records safe to advertise from OpenAI /v1/models.

        This is intentionally stricter than list_models(): inventory may include
        echo providers, embedding models, disabled models, and aliases pointing at
        unreachable development backends. Those records are useful for ops but make
        OpenAI-compatible clients select broken models.
        """
        visible: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in self.list_models():
            if not self.is_openai_chat_visible(record):
                continue
            name = str(record.get("name") or "")
            if name and name not in seen:
                visible.append(record)
                seen.add(name)
        return visible

    def get(self, name: str | None = None) -> dict[str, Any]:
        enabled = [r for r in self.list_models() if r.get("enabled", True)]
        if name:
            requested = str(name)
            # Exact runtime names always win, except raw Ollama tags are handled
            # below so a configured Xavi alias cannot shadow a discovered direct
            # Ollama model with the same underlying tag.
            if requested.startswith("ollama:"):
                for r in enabled:
                    if r.get("name") == requested:
                        return r
            else:
                prefixed = f"ollama:{requested}"
                # Prefer the discovered direct local Ollama record first.
                for r in enabled:
                    if r.get("name") == prefixed and self.is_openai_chat_visible(r):
                        return r
                # Then exact configured alias names.
                for r in enabled:
                    if r.get("name") == requested:
                        return r
                # Finally, model tag matches, preferring reachable chat backends.
                for r in enabled:
                    if self._model_tag(r) == requested and self.is_openai_chat_visible(r):
                        return r
                for r in enabled:
                    if self._model_tag(r) == requested:
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
        normalized = extract_model_response(data)
        return {
            "model": model | {"model": name},
            "response_text": normalized["response_text"],
            "reasoning_text": normalized["reasoning_text"],
            "tool_calls": normalized["tool_calls"],
            "capabilities_observed": normalized["capabilities_observed"],
            "provider_native_fields": normalized["native_fields"],
            "provider_status": "ollama",
            "provider_metrics": {
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "prompt_eval_duration": data.get("prompt_eval_duration"),
                "eval_count": data.get("eval_count"),
                "eval_duration": data.get("eval_duration"),
                "done_reason": data.get("done_reason"),
            },
        }

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
        normalized = extract_model_response(data)
        return {
            "model": model | {"model": name},
            "response_text": normalized["response_text"],
            "reasoning_text": normalized["reasoning_text"],
            "tool_calls": normalized["tool_calls"],
            "capabilities_observed": normalized["capabilities_observed"],
            "provider_native_fields": normalized["native_fields"],
            "provider_status": "llama_cpp",
        }


async def stream_ollama_generate(settings: Settings, *, prompt: str, model: dict[str, Any], options: dict[str, Any] | None = None) -> AsyncIterator[dict[str, Any]]:
    """Yield normalized chunks from Ollama /api/generate streaming JSON lines."""
    base = model.get("base_url") or settings.ollama_host
    name = model.get("model") or settings.ollama_default_model
    timeout = httpx.Timeout(
        connect=10.0,
        read=float(getattr(settings, "ollama_timeout_seconds", 180.0)),
        write=30.0,
        pool=10.0,
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            f"{str(base).rstrip('/')}/api/generate",
            json={
                "model": name,
                "prompt": prompt,
                "system": DUOTRONIC_RUNTIME_SYSTEM_PROMPT,
                "stream": True,
                "options": options or {
                    "temperature": 0.15,
                    "top_p": 0.85,
                    "repeat_penalty": 1.08,
                },
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                normalized = extract_model_response(data)
                yield {
                    "raw": data,
                    "response_text": normalized["response_text"],
                    "reasoning_text": normalized["reasoning_text"],
                    "done": bool(data.get("done")),
                    "done_reason": data.get("done_reason"),
                    "model": name,
                }


async def complete_ollama_generate(settings: Settings, *, prompt: str, model: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return one direct Ollama completion for OpenAI-v1-compatible clients.

    This intentionally avoids the Duotronic runtime prompt wrapper. LibreChat and
    other OpenAI-compatible clients expect /v1/chat/completions to behave like a
    plain model gateway unless they pick an explicit Xavi/WG-RNN model.
    """
    base = model.get("base_url") or settings.ollama_host
    name = model.get("model") or settings.ollama_default_model
    timeout = httpx.Timeout(
        connect=10.0,
        read=float(getattr(settings, "ollama_timeout_seconds", 180.0)),
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
                    "stream": False,
                    "options": options or {
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
    normalized = extract_model_response(data)
    return {
        "model": model | {"model": name},
        "response_text": normalized["response_text"],
        "reasoning_text": normalized["reasoning_text"],
        "tool_calls": normalized["tool_calls"],
        "capabilities_observed": normalized["capabilities_observed"],
        "provider_native_fields": normalized["native_fields"],
        "provider_status": "ollama_direct",
        "provider_metrics": {
            "total_duration": data.get("total_duration"),
            "load_duration": data.get("load_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "prompt_eval_duration": data.get("prompt_eval_duration"),
            "eval_count": data.get("eval_count"),
            "eval_duration": data.get("eval_duration"),
            "done_reason": data.get("done_reason"),
        },
    }
