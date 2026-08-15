from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from duotronic_runtime.providers import ModelRegistry


def test_registry_resolves_plain_ollama_tag_to_discovered_record(tmp_path: Path) -> None:
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        '{"models": [{"name": "ollama-default", "provider": "ollama", "model": "llama3.2:1b", "enabled": true, "default": true}]}'
    )
    settings = SimpleNamespace(ollama_enabled=True, ollama_host="http://ollama:11434")
    registry = ModelRegistry(registry_path, settings)  # type: ignore[arg-type]
    registry._ollama_cache = [
        {
            "name": "ollama:mistral:7b",
            "provider": "ollama",
            "model": "mistral:7b",
            "base_url": "http://ollama:11434",
            "enabled": True,
            "default": False,
            "discovered": True,
        }
    ]
    registry._ollama_cache_ts = 10**12

    record = registry.get("mistral:7b")

    assert record["name"] == "ollama:mistral:7b"
    assert record["model"] == "mistral:7b"


def test_openai_chat_models_hide_non_chat_and_unreachable_aliases(tmp_path: Path) -> None:
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        '{"models": ['
        '{"name": "xavi-vscode-deep", "provider": "ollama", "model": "qwen2.5-coder:7b", "base_url": "http://host.containers.internal:11434", "enabled": true},'
        '{"name": "ollama-default", "provider": "ollama", "model": "llama3.2:1b", "base_url": "http://ollama:11434", "enabled": true, "default": true},'
        '{"name": "sandbox-echo", "provider": "echo", "enabled": true}'
        ']}'
    )
    settings = SimpleNamespace(ollama_enabled=True, ollama_host="http://ollama:11434")
    registry = ModelRegistry(registry_path, settings)  # type: ignore[arg-type]
    registry._ollama_cache = [
        {"name": "ollama:qwen2.5-coder:7b", "provider": "ollama", "model": "qwen2.5-coder:7b", "base_url": "http://ollama:11434", "enabled": True, "discovered": True},
        {"name": "ollama:nomic-embed-text:latest", "provider": "ollama", "model": "nomic-embed-text:latest", "base_url": "http://ollama:11434", "enabled": True, "discovered": True},
    ]
    registry._ollama_cache_ts = 10**12

    names = {r["name"] for r in registry.list_openai_chat_models()}

    assert "ollama-default" in names
    assert "ollama:qwen2.5-coder:7b" in names
    assert "xavi-vscode-deep" not in names
    assert "ollama:nomic-embed-text:latest" not in names
    assert "sandbox-echo" not in names


def test_raw_tag_prefers_reachable_discovered_ollama_over_dead_alias(tmp_path: Path) -> None:
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        '{"models": ['
        '{"name": "xavi-vscode-deep", "provider": "ollama", "model": "qwen2.5-coder:7b", "base_url": "http://host.containers.internal:11434", "enabled": true},'
        '{"name": "ollama-default", "provider": "ollama", "model": "llama3.2:1b", "base_url": "http://ollama:11434", "enabled": true, "default": true}'
        ']}'
    )
    settings = SimpleNamespace(ollama_enabled=True, ollama_host="http://ollama:11434")
    registry = ModelRegistry(registry_path, settings)  # type: ignore[arg-type]
    registry._ollama_cache = [
        {"name": "ollama:qwen2.5-coder:7b", "provider": "ollama", "model": "qwen2.5-coder:7b", "base_url": "http://ollama:11434", "enabled": True, "discovered": True},
    ]
    registry._ollama_cache_ts = 10**12

    record = registry.get("qwen2.5-coder:7b")

    assert record["name"] == "ollama:qwen2.5-coder:7b"
    assert record["base_url"] == "http://ollama:11434"


def test_openai_chat_models_hide_custom_xavi_completion_tags(tmp_path: Path) -> None:
    registry_path = tmp_path / "models.json"
    registry_path.write_text('{"models": [{"name": "ollama-default", "provider": "ollama", "model": "llama3.2:1b", "base_url": "http://ollama:11434", "enabled": true, "default": true}]}')
    settings = SimpleNamespace(ollama_enabled=True, ollama_host="http://ollama:11434")
    registry = ModelRegistry(registry_path, settings)  # type: ignore[arg-type]
    registry._ollama_cache = [
        {"name": "ollama:qwen3:4b", "provider": "ollama", "model": "qwen3:4b", "base_url": "http://ollama:11434", "enabled": True, "discovered": True},
        {"name": "ollama:qwen2.5-coder:xavi-continue-agent", "provider": "ollama", "model": "qwen2.5-coder:xavi-continue-agent", "base_url": "http://ollama:11434", "enabled": True, "discovered": True},
        {"name": "ollama:xavi-copilot-agent:latest", "provider": "ollama", "model": "xavi-copilot-agent:latest", "base_url": "http://ollama:11434", "enabled": True, "discovered": True},
    ]
    registry._ollama_cache_ts = 10**12

    names = {r["name"] for r in registry.list_openai_chat_models()}

    assert "ollama:qwen3:4b" in names
    assert "ollama:qwen2.5-coder:xavi-continue-agent" not in names
    assert "ollama:xavi-copilot-agent:latest" not in names
