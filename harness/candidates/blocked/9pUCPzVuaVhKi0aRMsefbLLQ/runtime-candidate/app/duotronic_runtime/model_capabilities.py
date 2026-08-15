from __future__ import annotations

from typing import Any


TEXT_CAPABILITIES = {"chat", "text_generation"}
CODE_CAPABILITIES = {"code_generation", "code_agent", "tool_use", "autocomplete"}
VISION_CAPABILITIES = {"vision", "multimodal", "document_ocr"}
IMAGE_CAPABILITIES = {"image_generation", "image_editing"}
EMBEDDING_CAPABILITIES = {"embeddings", "embedding"}
RERANK_CAPABILITIES = {"rerank", "classification"}
RUNNER_CAPABILITIES = {"code_execution", "code_interpreter", "sandbox_runner"}


def _tokens(record: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("name", "model", "provider", "description", "endpoint_type"):
        value = record.get(key)
        if value:
            values.append(str(value))
    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        for value in metadata.values():
            if isinstance(value, (str, int, float, bool)):
                values.append(str(value))
            elif isinstance(value, list):
                values.extend(str(item) for item in value if isinstance(item, (str, int, float, bool)))
    return " ".join(values).lower()


def infer_capabilities(record: dict[str, Any]) -> list[str]:
    """Infer broad runtime capabilities without making network calls.

    The inference is intentionally conservative and additive: explicit
    capabilities always win, while provider/model-name hints fill gaps for
    discovered records from backends like Ollama, llama.cpp, transformers.js,
    image generators, and code runners.
    """
    explicit = record.get("capabilities") or []
    caps = {str(item) for item in explicit if item}
    provider = str(record.get("provider") or "").lower()
    haystack = _tokens(record)

    if provider in {"ollama", "llama_cpp", "openai_compatible", "openai", "echo"}:
        caps |= TEXT_CAPABILITIES
    if provider in {"stable_diffusion", "comfyui", "automatic1111", "image_generation"}:
        caps |= IMAGE_CAPABILITIES
    if provider in {"transformers_js", "transformers.js"}:
        caps |= {"embeddings", "classification", "rerank"}
    if provider in {"code_interpreter", "code_runner", "sandbox_runner"}:
        caps |= RUNNER_CAPABILITIES

    if any(marker in haystack for marker in ("embed", "embedding", "nomic-embed", "bge", "e5-")):
        caps -= TEXT_CAPABILITIES
        caps |= {"embeddings"}
    if any(marker in haystack for marker in ("rerank", "cross-encoder", "classifier", "classification")):
        caps |= RERANK_CAPABILITIES
    if any(marker in haystack for marker in ("vision", "vl", "llava", "minicpm-v", "qwen2.5vl", "multimodal")):
        caps |= VISION_CAPABILITIES | {"chat"}
    if any(marker in haystack for marker in ("coder", "code", "autocomplete", "continue", "copilot")):
        caps |= CODE_CAPABILITIES
    if any(marker in haystack for marker in ("agent", "tool", "function_call", "function-call")):
        caps |= {"tool_use", "code_agent"}
    if any(marker in haystack for marker in ("stable-diffusion", "sdxl", "comfyui", "txt2img", "image_generation")):
        caps |= IMAGE_CAPABILITIES

    return sorted(caps)


def infer_modalities(capabilities: list[str] | set[str]) -> list[str]:
    caps = set(capabilities)
    modalities: set[str] = set()
    if caps & (TEXT_CAPABILITIES | CODE_CAPABILITIES):
        modalities.add("text")
    if caps & VISION_CAPABILITIES:
        modalities.add("vision")
    if caps & IMAGE_CAPABILITIES:
        modalities.add("image")
    if caps & EMBEDDING_CAPABILITIES:
        modalities.add("embedding")
    if caps & RERANK_CAPABILITIES:
        modalities.add("classification")
    if caps & RUNNER_CAPABILITIES:
        modalities.add("execution")
    return sorted(modalities)


def infer_endpoint_type(record: dict[str, Any]) -> str:
    explicit = record.get("endpoint_type")
    if explicit:
        return str(explicit)
    provider = str(record.get("provider") or "").lower()
    if provider == "ollama":
        return "ollama_api"
    if provider in {"llama_cpp", "openai", "openai_compatible"}:
        return "openai_v1"
    if provider in {"stable_diffusion", "automatic1111"}:
        return "automatic1111_api"
    if provider == "comfyui":
        return "comfyui_api"
    if provider in {"transformers_js", "transformers.js"}:
        return "transformers_js_http"
    if provider in {"code_interpreter", "code_runner", "sandbox_runner"}:
        return "code_runner_http"
    return provider or "unknown"


def is_chat_capable(record: dict[str, Any]) -> bool:
    caps = set(record.get("capabilities") or infer_capabilities(record))
    if caps & EMBEDDING_CAPABILITIES and not caps & TEXT_CAPABILITIES:
        return False
    if caps & IMAGE_CAPABILITIES and not caps & TEXT_CAPABILITIES:
        return False
    if caps & RUNNER_CAPABILITIES and not caps & TEXT_CAPABILITIES:
        return False
    return bool(caps & TEXT_CAPABILITIES)


def enrich_model_record(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    out["endpoint_type"] = infer_endpoint_type(out)
    capabilities = infer_capabilities(out)
    out["capabilities"] = capabilities
    out["modalities"] = infer_modalities(capabilities)
    out.setdefault("tool_surface", "model")
    return out
