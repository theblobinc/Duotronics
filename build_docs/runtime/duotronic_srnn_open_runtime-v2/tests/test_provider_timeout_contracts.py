from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_provider_timeout_settings_exist():
    config = (ROOT / "app" / "duotronic_runtime" / "config.py").read_text()
    assert "OLLAMA_TIMEOUT_SECONDS" in config
    assert "LLAMA_CPP_TIMEOUT_SECONDS" in config


def test_provider_errors_are_mapped_by_api():
    api = (ROOT / "app" / "duotronic_runtime" / "api.py").read_text()
    assert "model_provider_timeout" in api
    assert "status_code=504" in api
    assert "model_provider_error" in api
    assert "status_code=502" in api


def test_ollama_provider_uses_configurable_timeout():
    providers = (ROOT / "app" / "duotronic_runtime" / "providers.py").read_text()
    assert "ollama_timeout_seconds" in providers
    assert "httpx.Timeout" in providers
    assert "ollama_timeout" in providers
