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
