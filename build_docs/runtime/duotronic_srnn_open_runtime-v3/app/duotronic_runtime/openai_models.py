from __future__ import annotations

from typing import Any, Protocol


class OpenAIModelRegistry(Protocol):
    def list_openai_chat_models(self) -> list[dict[str, Any]]: ...


WG_RNN_VIRTUAL_MODELS: tuple[dict[str, Any], ...] = (
    {
        "id": "wg-rnn:chat",
        "description": "Governed WG-RNN conversational mode with corpus grounding and candidate-memory witnesses.",
        "capabilities": ["chat", "streaming", "wgrnn", "corpus", "candidate_memory"],
        "modalities": ["text", "vision"],
    },
    {
        "id": "wg-rnn:runtime",
        "description": "WG-RNN runtime step mode for witnessed runtime observations.",
        "capabilities": ["chat", "streaming", "wgrnn", "observe"],
        "modalities": ["text"],
    },
    {
        "id": "wg-rnn:observe",
        "description": "WG-RNN observation mode for witnessed evidence updates.",
        "capabilities": ["chat", "streaming", "wgrnn", "observe"],
        "modalities": ["text"],
    },
    {
        "id": "wg-rnn:memory",
        "description": "WG-RNN candidate-memory write mode; it does not promote observations to truth authority.",
        "capabilities": ["chat", "streaming", "wgrnn", "candidate_memory"],
        "modalities": ["text"],
    },
)


def _clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return sorted({str(item).strip() for item in value if item is not None and str(item).strip()})


def _model_descriptor(
    model_id: str,
    *,
    owned_by: str,
    root: str,
    parent: str | None,
    source: str,
    provider: str,
    capabilities: Any = None,
    modalities: Any = None,
    description: str = "",
    default: bool = False,
    discovered: bool = False,
) -> dict[str, Any]:
    """Build a stable OpenAI model object with additive Xavi metadata.

    The top-level fields stay compatible with OpenAI-style clients. Extra Xavi
    metadata is deliberately namespaced and never includes backend URLs, API
    keys, environment values, or other deployment secrets.
    """
    return {
        "id": model_id,
        "object": "model",
        "created": 0,
        "owned_by": owned_by,
        "permission": [],
        "root": root,
        "parent": parent,
        "xavi": {
            "source": source,
            "provider": provider,
            "capabilities": _clean_string_list(capabilities),
            "modalities": _clean_string_list(modalities),
            "description": str(description or ""),
            "default": bool(default),
            "discovered": bool(discovered),
        },
    }


def _registry_descriptor(record: dict[str, Any]) -> dict[str, Any] | None:
    model_id = str(record.get("name") or record.get("model") or "").strip()
    if not model_id:
        return None
    provider = str(record.get("provider") or "xavi").strip() or "xavi"
    root = str(record.get("model") or model_id).strip() or model_id
    return _model_descriptor(
        model_id,
        owned_by=provider,
        root=root,
        parent=None,
        source="registry",
        provider=provider,
        capabilities=record.get("capabilities"),
        modalities=record.get("modalities"),
        description=str(record.get("description") or ""),
        default=bool(record.get("default")),
        discovered=bool(record.get("discovered")),
    )


def _ollama_raw_alias(record: dict[str, Any], primary_id: str) -> dict[str, Any] | None:
    if str(record.get("provider") or "") != "ollama" or not primary_id.startswith("ollama:"):
        return None
    raw_id = str(record.get("model") or primary_id.removeprefix("ollama:")).strip()
    if not raw_id or raw_id == primary_id:
        return None
    return _model_descriptor(
        raw_id,
        owned_by="ollama",
        root=raw_id,
        parent=primary_id,
        source="alias",
        provider="ollama",
        capabilities=record.get("capabilities"),
        modalities=record.get("modalities"),
        description=str(record.get("description") or ""),
        default=bool(record.get("default")),
        discovered=bool(record.get("discovered")),
    )


def _virtual_descriptor(record: dict[str, Any]) -> dict[str, Any]:
    model_id = str(record["id"])
    return _model_descriptor(
        model_id,
        owned_by="xavi-wg-rnn",
        root=model_id,
        parent=None,
        source="virtual",
        provider="wgrnn",
        capabilities=record.get("capabilities"),
        modalities=record.get("modalities"),
        description=str(record.get("description") or ""),
    )


def build_openai_model_catalog(registry: OpenAIModelRegistry) -> list[dict[str, Any]]:
    """Return a deterministic, de-duplicated OpenAI-compatible model catalog.

    Primary registry names win over convenience aliases. WG-RNN virtual modes
    are advertised first in a stable user-facing order, then physical/runtime
    model IDs are sorted case-insensitively for reproducible client menus.
    """
    records = [record for record in registry.list_openai_chat_models() if record.get("enabled", True)]

    primary: dict[str, dict[str, Any]] = {}
    primary_records: list[tuple[dict[str, Any], str]] = []
    for record in records:
        descriptor = _registry_descriptor(record)
        if descriptor is None:
            continue
        model_id = str(descriptor["id"])
        if model_id in primary:
            continue
        primary[model_id] = descriptor
        primary_records.append((record, model_id))

    aliases: dict[str, dict[str, Any]] = {}
    for record, primary_id in primary_records:
        alias = _ollama_raw_alias(record, primary_id)
        if alias is None:
            continue
        alias_id = str(alias["id"])
        if alias_id in primary or alias_id in aliases:
            continue
        aliases[alias_id] = alias

    virtual = [_virtual_descriptor(record) for record in WG_RNN_VIRTUAL_MODELS]
    virtual_ids = {str(item["id"]) for item in virtual}

    physical = [item for model_id, item in primary.items() if model_id not in virtual_ids]
    physical.extend(item for model_id, item in aliases.items() if model_id not in virtual_ids)
    physical.sort(key=lambda item: (str(item["id"]).casefold(), str(item["id"])))

    return virtual + physical


def build_openai_models_response(registry: OpenAIModelRegistry) -> dict[str, Any]:
    return {"object": "list", "data": build_openai_model_catalog(registry)}


def find_openai_model(registry: OpenAIModelRegistry, model_id: str) -> dict[str, Any] | None:
    requested = str(model_id or "").strip()
    if not requested:
        return None
    for model in build_openai_model_catalog(registry):
        if model.get("id") == requested:
            return model
    return None


def openai_model_not_found(model_id: str) -> dict[str, Any]:
    return {
        "error": {
            "message": f"The model '{model_id}' does not exist or is not available through this runtime.",
            "type": "invalid_request_error",
            "param": "model",
            "code": "model_not_found",
        }
    }
