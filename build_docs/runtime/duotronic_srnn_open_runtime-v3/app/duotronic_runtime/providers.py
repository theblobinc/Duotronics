from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from .config import Settings
from .model_capabilities import enrich_model_record, is_chat_capable
from .prompting import DUOTRONIC_RUNTIME_SYSTEM_PROMPT, build_runtime_prompt
from .response_normalizer import extract_model_response
from .service_registry import ServiceRegistry


def expand_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value


class ModelRegistry:
    def __init__(self, path: Path, settings: Settings) -> None:
        self.path = path
        self.settings = settings
        service_registry_path = getattr(settings, "service_registry_path", None) or (Path(path).parent / "service_registry.json")
        self.service_registry = ServiceRegistry(Path(service_registry_path))
        self.records = self._load()
        self._ollama_cache: list[dict[str, Any]] = []
        self._ollama_cache_ts: float = 0.0
        self._openai_compatible_cache: list[dict[str, Any]] = []
        self._openai_compatible_cache_ts: float = 0.0
        self._OLLAMA_CACHE_TTL = 30.0
        self._OPENAI_COMPATIBLE_CACHE_TTL = 30.0

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return [enrich_model_record({"name": "sandbox-echo", "provider": "echo", "default": True, "enabled": True})]
        data = json.loads(self.path.read_text())
        out = []
        for record in data.get("models", []):
            rec = {k: expand_env(v) for k, v in record.items()}
            enabled_env = rec.get("enabled_env")
            if enabled_env:
                rec["enabled"] = os.environ.get(str(enabled_env), "false").lower() in {"1", "true", "yes", "on"}
            else:
                rec["enabled"] = bool(rec.get("enabled", True))
            out.append(enrich_model_record(self.service_registry.annotate_model(rec)))
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
        ]:
            if base and base not in candidates:
                candidates.append(base)

        data = None
        working_base = configured_base
        for base in candidates:
            try:
                timeout = httpx.Timeout(5.0, connect=2.0)
                with httpx.Client(timeout=timeout, trust_env=False) as client:
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
                enrich_model_record(
                    {
                        "name": runtime_name,
                        "provider": "ollama",
                        "model": tag,
                        "base_url": working_base,
                        "enabled": True,
                        "default": False,
                        "description": "Discovered from Ollama /api/tags",
                        "discovered": True,
                        "metadata": {"source": "ollama_tags", "raw": item},
                    }
                )
            )

        self._ollama_cache = discovered
        self._ollama_cache_ts = time.monotonic()
        return discovered

    def _discover_openai_compatible_models(self) -> list[dict[str, Any]]:
        """Return transient records from enabled OpenAI-compatible backends."""
        now = time.monotonic()
        if now - self._openai_compatible_cache_ts < self._OPENAI_COMPATIBLE_CACHE_TTL:
            return self._openai_compatible_cache

        providers: list[dict[str, Any]] = []
        if getattr(self.settings, "llama_cpp_enabled", False):
            providers.append(
                {
                    "provider": "llama_cpp",
                    "base_url": str(getattr(self.settings, "llama_cpp_base_url", "") or "").rstrip("/"),
                    "default_model": getattr(self.settings, "llama_cpp_default_model", "local-gguf"),
                }
            )

        discovered: list[dict[str, Any]] = []
        existing_names = {str(r.get("name") or "") for r in self.records}
        for provider in providers:
            base = provider.get("base_url") or ""
            if not base:
                continue
            models: list[dict[str, Any]] = []
            try:
                timeout = httpx.Timeout(5.0, connect=2.0)
                with httpx.Client(timeout=timeout) as client:
                    r = client.get(f"{base}/models")
                    r.raise_for_status()
                    data = r.json()
                    raw_models = data.get("data", data.get("models", [])) if isinstance(data, dict) else []
                    models = [item for item in raw_models if isinstance(item, dict)]
            except Exception:
                models = [{"id": provider.get("default_model"), "source": "configured_default_unprobed"}]

            for item in models:
                model_id = str(item.get("id") or item.get("name") or item.get("model") or provider.get("default_model") or "").strip()
                if not model_id:
                    continue
                runtime_name = f"{provider['provider']}:{model_id}"
                if runtime_name in existing_names:
                    continue
                discovered.append(
                    enrich_model_record(
                        {
                            "name": runtime_name,
                            "provider": provider["provider"],
                            "model": model_id,
                            "base_url": base,
                            "enabled": True,
                            "default": False,
                            "description": f"Discovered from {provider['provider']} OpenAI-compatible /v1/models",
                            "discovered": True,
                            "endpoint_type": "openai_v1",
                            "metadata": {"source": "openai_compatible_models", "raw": item},
                        }
                    )
                )

        self._openai_compatible_cache = discovered
        self._openai_compatible_cache_ts = time.monotonic()
        return discovered

    def list_models(self) -> list[dict[str, Any]]:
        records = list(self.records)
        existing_names = {str(r.get("name") or "") for r in records}
        for record in self._discover_ollama_models() + self._discover_openai_compatible_models():
            name = str(record.get("name") or "")
            if name and name not in existing_names:
                records.append(enrich_model_record(record))
                existing_names.add(name)
        return [enrich_model_record(self.service_registry.annotate_model(record)) for record in records]

    def _model_tag(self, record: dict[str, Any]) -> str:
        return str(record.get("model") or record.get("name") or "").strip()

    def _is_non_chat_model(self, record: dict[str, Any]) -> bool:
        tag = self._model_tag(record).lower()
        name = str(record.get("name") or "").lower()
        haystack = f"{name} {tag}"
        # Inventory can contain embeddings, image generators, runners, and custom
        # agent tags. Only advertise records that have an actual text/chat surface.
        if not is_chat_capable(record):
            return True
        non_chat_markers = ("embed", "embedding", "nomic-embed")
        if any(marker in haystack for marker in non_chat_markers):
            return True
        # Hide custom policy/code-completion Modelfile variants from generic chat
        # discovery. These tags are useful for agent tooling but produce poor
        # LibreChat output when selected as plain assistant models.
        custom_completion_markers = (
            "xavi-agent",
            "xavi-continue",
            "xavi-copilot-agent",
            "continue-autocomplete",
            "continue-background",
            "continue-agent",
            "continue-plan",
        )
        return any(marker in haystack for marker in custom_completion_markers)

    def _has_reachable_chat_backend(self, record: dict[str, Any]) -> bool:
        provider = str(record.get("provider") or "")
        if provider not in {"ollama", "llama_cpp", "openai_compatible", "openai"}:
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
            async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
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


def _ollama_failover_plan(
    settings: Settings,
    model: dict[str, Any],
    *,
    health_timeout_seconds: float = 1.5,
) -> dict[str, Any]:
    """Resolve configured Ollama failover aliases against commissioned live nodes.

    This is routing evidence, not proof of execution. Actual execution is only
    recorded after a request succeeds. Generic aliases without an explicit
    fallback chain remain single-route and do not pay a health-probe penalty.
    """
    requested = dict(model or {})
    requested_alias = str(requested.get("name") or requested.get("model") or "ollama").strip()
    metadata = requested.get("metadata") if isinstance(requested.get("metadata"), dict) else {}
    fallback_names = [
        str(item).strip()
        for item in (metadata.get("fallback_model_names") or [])
        if str(item).strip()
    ]
    registry = ModelRegistry(settings.model_registry_path, settings)
    service_registry = registry.service_registry
    configured = {
        str(item.get("name") or ""): item
        for item in registry.records
        if isinstance(item, dict) and str(item.get("name") or "")
    }

    ordered: list[dict[str, Any]] = [requested]
    preflight_attempts: list[dict[str, Any]] = []
    for fallback_name in fallback_names:
        fallback = configured.get(fallback_name)
        if fallback is None:
            preflight_attempts.append({
                "alias": fallback_name,
                "status": "skipped",
                "reason": "fallback_alias_not_configured",
            })
            continue
        if str(fallback.get("provider") or "") != "ollama" or not bool(fallback.get("enabled", True)):
            preflight_attempts.append({
                "alias": fallback_name,
                "status": "skipped",
                "reason": "fallback_alias_not_enabled_ollama",
            })
            continue
        ordered.append(dict(fallback))

    health: dict[str, Any] | None = None
    health_error: str | None = None
    if fallback_names:
        try:
            health = service_registry.service_health(
                service="ollama",
                timeout_seconds=max(0.2, min(float(health_timeout_seconds or 1.5), 5.0)),
            )
        except Exception as exc:
            health_error = exc.__class__.__name__

    health_by_node = {
        str(row.get("node_id") or ""): row
        for row in ((health or {}).get("observations") or [])
        if isinstance(row, dict) and str(row.get("node_id") or "")
    }
    routes: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for route_record in ordered:
        route_record = service_registry.annotate_model(route_record)
        base = str(route_record.get("base_url") or settings.ollama_host or "").strip().rstrip("/")
        model_name = str(route_record.get("model") or settings.ollama_default_model or "").strip()
        alias = str(route_record.get("name") or model_name or "ollama").strip()
        if not base or not model_name:
            preflight_attempts.append({"alias": alias, "status": "skipped", "reason": "missing_base_or_model"})
            continue

        owner = service_registry.endpoint_owner(base)
        node_id = str((route_record.get("metadata") or {}).get("node_id") or "").strip() or None
        if owner is not None:
            owner_node, _, _ = owner
            node_id = node_id or str(owner_node.get("id") or "").strip() or None

        live = health_by_node.get(node_id or "") if health is not None and node_id else None
        if health is not None and owner is not None:
            if live is None or not bool(live.get("healthy")):
                preflight_attempts.append({
                    "alias": alias,
                    "model": model_name,
                    "node_id": node_id,
                    "status": "skipped",
                    "reason": "ollama_service_unhealthy_or_unobserved",
                })
                continue
            observed_endpoint = str(live.get("endpoint") or "").strip().rstrip("/")
            if observed_endpoint:
                base = observed_endpoint

        key = (str(node_id or ""), model_name, base)
        if key in seen:
            continue
        seen.add(key)
        routes.append({
            "alias": alias,
            "model": model_name,
            "base_url": base,
            "node_id": node_id,
            "record": route_record,
            "health": live,
        })

    return {
        "schema_version": "ollama-failover-plan-v1",
        "requested_alias": requested_alias,
        "requested_model": str(requested.get("model") or settings.ollama_default_model or ""),
        "fallback_model_names": fallback_names,
        "routes": routes,
        "preflight_attempts": preflight_attempts,
        "service_health_digest": (health or {}).get("observation_digest"),
        "service_health_error": health_error,
    }


def _ollama_routing_result(plan: dict[str, Any], selected: dict[str, Any], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    requested_alias = str(plan.get("requested_alias") or "")
    selected_alias = str(selected.get("alias") or "")
    return {
        "schema_version": "ollama-routing-witness-v1",
        "requested_alias": requested_alias,
        "requested_model": plan.get("requested_model"),
        "selected_alias": selected_alias,
        "selected_model": selected.get("model"),
        "selected_node_id": selected.get("node_id"),
        "selected_base_url": selected.get("base_url"),
        "failover_used": bool(requested_alias and selected_alias and requested_alias != selected_alias),
        "attempts": attempts,
        "service_health_digest": plan.get("service_health_digest"),
        "service_health_error": plan.get("service_health_error"),
    }


def _ollama_retryable_status(response: httpx.Response) -> bool:
    status = int(response.status_code)
    if status >= 500 or status == 404:
        return True
    if status == 400:
        body = str(response.text or "").lower()
        return "model" in body and ("not found" in body or "does not exist" in body)
    return False


async def stream_ollama_generate(settings: Settings, *, prompt: str, model: dict[str, Any], options: dict[str, Any] | None = None, messages: list[dict[str, Any]] | None = None, tools: list[dict[str, Any]] | None = None) -> AsyncIterator[dict[str, Any]]:
    """Yield Ollama chat chunks with failover only before the first token.

    A dead/unavailable primary may be replaced by an explicitly configured
    fallback route before output begins. Once any chunk has been yielded, a later
    backend failure is terminal so responses from different models are never
    spliced together.
    """
    chat_messages = messages or [{"role": "user", "content": prompt}]
    interactive_timeout = float(getattr(settings, "ollama_timeout_seconds", 180.0))
    timeout = httpx.Timeout(
        connect=min(5.0, interactive_timeout),
        read=interactive_timeout,
        write=min(10.0, interactive_timeout),
        pool=min(5.0, interactive_timeout),
    )
    plan = _ollama_failover_plan(
        settings,
        model,
        health_timeout_seconds=min(1.5, max(0.2, interactive_timeout)),
    )
    attempts = list(plan.get("preflight_attempts") or [])
    last_error = "no_eligible_ollama_route"

    for route in plan.get("routes") or []:
        base = str(route.get("base_url") or "").rstrip("/")
        name = str(route.get("model") or "")
        alias = str(route.get("alias") or name)
        body: dict[str, Any] = {
            "model": name,
            "messages": chat_messages,
            "stream": True,
            "think": False,
            "options": options or {
                "temperature": 0.15,
                "top_p": 0.85,
                "repeat_penalty": 1.08,
            },
        }
        if tools:
            body["tools"] = tools
        yielded_any = False
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
                async with client.stream("POST", f"{base}/api/chat", json=body) as response:
                    if response.is_error:
                        body_text = (await response.aread()).decode("utf-8", errors="ignore")
                        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
                        attempts.append({
                            "alias": alias,
                            "model": name,
                            "node_id": route.get("node_id"),
                            "base_url": base,
                            "status": "http_error",
                            "status_code": int(response.status_code),
                            "latency_ms": latency_ms,
                        })
                        last_error = f"http_{int(response.status_code)}:{alias}:{name}:{base}"
                        retryable = int(response.status_code) >= 500 or int(response.status_code) == 404 or (
                            int(response.status_code) == 400
                            and "model" in body_text.lower()
                            and ("not found" in body_text.lower() or "does not exist" in body_text.lower())
                        )
                        if retryable:
                            continue
                        response.raise_for_status()

                    attempts.append({
                        "alias": alias,
                        "model": name,
                        "node_id": route.get("node_id"),
                        "base_url": base,
                        "status": "stream_started",
                        "status_code": int(response.status_code),
                        "latency_ms": round((time.perf_counter() - started) * 1000.0, 2),
                    })
                    routing = _ollama_routing_result(plan, route, attempts)
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except Exception:
                            continue
                        message = data.get("message") if isinstance(data, dict) else None
                        if isinstance(message, dict):
                            # Preserve token whitespace exactly; completed response
                            # normalization trims strings and would corrupt streaming.
                            text = str(message.get("content") or "")
                            reasoning = str(
                                message.get("thinking")
                                or message.get("reasoning")
                                or message.get("reasoning_content")
                                or ""
                            )
                        else:
                            text = str(data.get("response") or "")
                            reasoning = str(data.get("thinking") or data.get("reasoning") or "")
                        native_tool_calls = message.get("tool_calls") if isinstance(message, dict) else None
                        yielded_any = True
                        yield {
                            "raw": data,
                            "response_text": text,
                            "reasoning_text": reasoning,
                            "tool_calls": native_tool_calls or [],
                            "done": bool(data.get("done")),
                            "done_reason": data.get("done_reason"),
                            "model": name,
                            "provider_routing": routing,
                        }
                    return
        except httpx.TimeoutException as exc:
            if yielded_any:
                raise RuntimeError(f"ollama_stream_timeout_after_output:{name}:{base}") from exc
            last_error = f"timeout:{alias}:{name}:{base}"
            attempts.append({
                "alias": alias,
                "model": name,
                "node_id": route.get("node_id"),
                "base_url": base,
                "status": "timeout",
            })
            continue
        except httpx.HTTPStatusError as exc:
            if yielded_any:
                raise RuntimeError(f"ollama_stream_http_error_after_output:{name}:{base}:{exc.response.status_code}") from exc
            raise RuntimeError(f"ollama_stream_http_error:{name}:{base}:{exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            if yielded_any:
                raise RuntimeError(f"ollama_stream_transport_error_after_output:{name}:{base}:{exc.__class__.__name__}") from exc
            last_error = f"transport:{alias}:{name}:{base}:{exc.__class__.__name__}"
            attempts.append({
                "alias": alias,
                "model": name,
                "node_id": route.get("node_id"),
                "base_url": base,
                "status": "transport_error",
                "error": exc.__class__.__name__,
            })
            continue

    raise RuntimeError(f"ollama_stream_failover_exhausted:{plan.get('requested_alias')}:{last_error}")


async def complete_ollama_generate(settings: Settings, *, prompt: str, model: dict[str, Any], options: dict[str, Any] | None = None, messages: list[dict[str, Any]] | None = None, tools: list[dict[str, Any]] | None = None, timeout_seconds: float | None = None) -> dict[str, Any]:
    """Return one direct Ollama chat completion with witnessed LAN failover.

    Use Ollama /api/chat so models receive native chat-template structure. An
    explicit alias fallback chain may move execution to another commissioned,
    healthy Ollama node. The returned routing witness names the backend that
    actually answered; a planned route is never presented as execution fact.
    """
    chat_messages = messages or [{"role": "user", "content": prompt}]
    interactive_timeout = float(timeout_seconds) if timeout_seconds is not None else float(getattr(settings, "ollama_timeout_seconds", 180.0))
    timeout = httpx.Timeout(
        connect=min(5.0, interactive_timeout),
        read=interactive_timeout,
        write=min(10.0, interactive_timeout),
        pool=min(5.0, interactive_timeout),
    )
    plan = _ollama_failover_plan(
        settings,
        model,
        health_timeout_seconds=min(1.5, max(0.2, interactive_timeout)),
    )
    attempts = list(plan.get("preflight_attempts") or [])
    last_error = "no_eligible_ollama_route"

    for route in plan.get("routes") or []:
        base = str(route.get("base_url") or "").rstrip("/")
        name = str(route.get("model") or "")
        alias = str(route.get("alias") or name)
        body: dict[str, Any] = {
            "model": name,
            "messages": chat_messages,
            "stream": False,
            "think": False,
            "options": options or {
                "temperature": 0.15,
                "top_p": 0.85,
                "repeat_penalty": 1.08,
            },
        }
        if tools:
            body["tools"] = tools
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
                r = await client.post(f"{base}/api/chat", json=body)
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            if r.is_error:
                attempts.append({
                    "alias": alias,
                    "model": name,
                    "node_id": route.get("node_id"),
                    "base_url": base,
                    "status": "http_error",
                    "status_code": int(r.status_code),
                    "latency_ms": latency_ms,
                })
                last_error = f"http_{int(r.status_code)}:{alias}:{name}:{base}"
                if _ollama_retryable_status(r):
                    continue
                r.raise_for_status()
            data = r.json()
            attempts.append({
                "alias": alias,
                "model": name,
                "node_id": route.get("node_id"),
                "base_url": base,
                "status": "completed",
                "status_code": int(r.status_code),
                "latency_ms": latency_ms,
            })
        except httpx.TimeoutException:
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            last_error = f"timeout:{alias}:{name}:{base}"
            attempts.append({
                "alias": alias,
                "model": name,
                "node_id": route.get("node_id"),
                "base_url": base,
                "status": "timeout",
                "latency_ms": latency_ms,
            })
            continue
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"ollama_http_error:{name}:{base}:{exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            last_error = f"transport:{alias}:{name}:{base}:{exc.__class__.__name__}"
            attempts.append({
                "alias": alias,
                "model": name,
                "node_id": route.get("node_id"),
                "base_url": base,
                "status": "transport_error",
                "error": exc.__class__.__name__,
                "latency_ms": latency_ms,
            })
            continue

        normalized = extract_model_response(data)
        selected_record = dict(route.get("record") or model) | {"model": name, "base_url": base}
        routing = _ollama_routing_result(plan, route, attempts)
        return {
            "model": selected_record,
            "response_text": normalized["response_text"],
            "reasoning_text": normalized["reasoning_text"],
            "tool_calls": normalized["tool_calls"],
            "capabilities_observed": normalized["capabilities_observed"],
            "provider_native_fields": normalized["native_fields"],
            "provider_status": "ollama_direct_failover" if routing["failover_used"] else "ollama_direct",
            "provider_routing": routing,
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

    raise RuntimeError(f"ollama_failover_exhausted:{plan.get('requested_alias')}:{last_error}")
