from __future__ import annotations

from duotronic_runtime.openai_models import (
    WG_RNN_VIRTUAL_MODELS,
    build_openai_model_catalog,
    build_openai_models_response,
    find_openai_model,
    openai_model_not_found,
)


class FakeRegistry:
    def __init__(self, records):
        self.records = records

    def list_openai_chat_models(self):
        return list(self.records)


def test_wgrnn_virtual_models_are_first_and_stable() -> None:
    registry = FakeRegistry(
        [
            {
                "name": "ollama:zeta:latest",
                "provider": "ollama",
                "model": "zeta:latest",
                "enabled": True,
            },
            {
                "name": "ollama:alpha:latest",
                "provider": "ollama",
                "model": "alpha:latest",
                "enabled": True,
            },
        ]
    )

    catalog = build_openai_model_catalog(registry)
    ids = [row["id"] for row in catalog]

    expected_virtual = [row["id"] for row in WG_RNN_VIRTUAL_MODELS]
    assert ids[: len(expected_virtual)] == expected_virtual
    assert ids[len(expected_virtual) :] == sorted(ids[len(expected_virtual) :], key=lambda value: (value.casefold(), value))


def test_primary_ids_win_over_ollama_raw_alias_collisions() -> None:
    registry = FakeRegistry(
        [
            {
                "name": "qwen:latest",
                "provider": "openai_compatible",
                "model": "qwen:latest",
                "enabled": True,
                "description": "explicit primary",
            },
            {
                "name": "ollama:qwen:latest",
                "provider": "ollama",
                "model": "qwen:latest",
                "enabled": True,
                "description": "ollama discovered",
            },
        ]
    )

    catalog = build_openai_model_catalog(registry)
    rows = [row for row in catalog if row["id"] == "qwen:latest"]

    assert len(rows) == 1
    assert rows[0]["xavi"]["source"] == "registry"
    assert rows[0]["xavi"]["provider"] == "openai_compatible"


def test_catalog_exposes_safe_metadata_without_backend_urls() -> None:
    registry = FakeRegistry(
        [
            {
                "name": "ollama:qwen2.5:7b",
                "provider": "ollama",
                "model": "qwen2.5:7b",
                "base_url": "http://secret-internal-host:11434",
                "api_key": "do-not-leak",
                "enabled": True,
                "default": True,
                "description": "test model",
                "capabilities": ["chat", "tool_use", "chat"],
                "modalities": ["text"],
                "discovered": True,
            }
        ]
    )

    payload = build_openai_models_response(registry)
    row = next(item for item in payload["data"] if item["id"] == "ollama:qwen2.5:7b")
    rendered = repr(row)

    assert payload["object"] == "list"
    assert row["object"] == "model"
    assert row["xavi"]["capabilities"] == ["chat", "tool_use"]
    assert row["xavi"]["default"] is True
    assert "secret-internal-host" not in rendered
    assert "do-not-leak" not in rendered


def test_model_lookup_supports_virtual_and_slash_ids() -> None:
    registry = FakeRegistry(
        [
            {
                "name": "vendor/model-name",
                "provider": "openai_compatible",
                "model": "vendor/model-name",
                "enabled": True,
            }
        ]
    )

    assert find_openai_model(registry, "wg-rnn:chat")["owned_by"] == "xavi-wg-rnn"
    assert find_openai_model(registry, "vendor/model-name")["id"] == "vendor/model-name"
    assert find_openai_model(registry, "missing-model") is None


def test_openai_model_not_found_shape() -> None:
    payload = openai_model_not_found("missing-model")

    assert payload["error"]["type"] == "invalid_request_error"
    assert payload["error"]["param"] == "model"
    assert payload["error"]["code"] == "model_not_found"
