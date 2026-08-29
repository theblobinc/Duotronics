from __future__ import annotations

from pathlib import Path

from duotronic_runtime.config import Settings
from duotronic_runtime.providers import ModelRegistry, _ollama_failover_plan
from duotronic_runtime.service_registry import ServiceRegistry


ROOT = Path(__file__).resolve().parents[1]


def _settings() -> Settings:
    return Settings(
        model_registry_path=ROOT / "config/models.json",
        service_registry_path=ROOT / "config/service_registry.json",
        ollama_enabled=False,
    )


def _configured(registry: ModelRegistry, name: str):
    return next(row for row in registry.records if row.get("name") == name)


def test_wgrnn_primary_has_distinct_same_host_fallback():
    registry = ModelRegistry(ROOT / "config/models.json", _settings())
    primary = _configured(registry, "wgrnn-chat-coordinator")
    local = _configured(registry, "wgrnn-chat-local-fallback")

    assert primary["base_url"] == "http://10.77.0.2:11434"
    assert primary["metadata"]["node_id"] == "tbi-production-3"
    assert "wgrnn-chat-local-fallback" in primary["metadata"]["fallback_model_names"]
    assert local["base_url"] == "http://ollama:11434"
    assert local["model"] == "qwen2.5-coder:3b"
    assert local["metadata"]["node_id"] == "tbi-production-4"


def test_failover_plan_skips_dead_prod3_and_selects_live_prod4(monkeypatch):
    settings = _settings()
    registry = ModelRegistry(ROOT / "config/models.json", settings)
    primary = _configured(registry, "wgrnn-chat-coordinator")

    def fake_health(self, **kwargs):
        return {
            "schema_version": "xavi-service-health-v1",
            "observations": [
                {
                    "node_id": "tbi-production-3",
                    "service": "ollama",
                    "healthy": False,
                    "reachable": False,
                    "endpoint": None,
                },
                {
                    "node_id": "tbi-production-4",
                    "service": "ollama",
                    "healthy": True,
                    "reachable": True,
                    "endpoint": "http://ollama:11434",
                    "status_code": 200,
                },
            ],
            "observation_digest": "service-health_test",
        }

    monkeypatch.setattr(ServiceRegistry, "service_health", fake_health)
    plan = _ollama_failover_plan(settings, primary)

    assert [row["alias"] for row in plan["routes"]] == ["wgrnn-chat-local-fallback"]
    selected = plan["routes"][0]
    assert selected["node_id"] == "tbi-production-4"
    assert selected["model"] == "qwen2.5-coder:3b"
    assert selected["base_url"] == "http://ollama:11434"
    assert plan["service_health_digest"] == "service-health_test"
    skipped = {(row.get("alias"), row.get("reason")) for row in plan["preflight_attempts"]}
    assert ("wgrnn-chat-coordinator", "ollama_service_unhealthy_or_unobserved") in skipped
    assert ("wgrnn-chat-starcoder-fallback", "ollama_service_unhealthy_or_unobserved") in skipped


def test_generic_ollama_alias_does_not_probe_cluster_without_fallback(monkeypatch):
    settings = _settings()
    registry = ModelRegistry(ROOT / "config/models.json", settings)
    local = _configured(registry, "xavi-vscode-balanced")

    def fail_if_called(self, **kwargs):
        raise AssertionError("generic single-route alias must not trigger cluster health probing")

    monkeypatch.setattr(ServiceRegistry, "service_health", fail_if_called)
    plan = _ollama_failover_plan(settings, local)
    assert len(plan["routes"]) == 1
    assert plan["routes"][0]["base_url"] == "http://ollama:11434"
    assert plan["service_health_digest"] is None


def test_provider_internal_http_does_not_inherit_environment_proxies():
    source = (ROOT / "app/duotronic_runtime/providers.py").read_text()
    assert "http://host.containers.internal:11434" not in source
    assert "httpx.AsyncClient(timeout=timeout, trust_env=False)" in source
    assert "httpx.Client(timeout=timeout, trust_env=False)" in source


def test_nonstreaming_tools_are_sent_in_ollama_json_body():
    source = (ROOT / "app/duotronic_runtime/providers.py").read_text()
    assert 'body["tools"] = tools' in source
    assert '**({"tools": tools} if tools else {}),' not in source


def test_stream_failover_is_forbidden_after_output_begins():
    source = (ROOT / "app/duotronic_runtime/providers.py").read_text()
    assert "ollama_stream_timeout_after_output" in source
    assert "ollama_stream_transport_error_after_output" in source
    assert "Once any chunk has been yielded" in source
