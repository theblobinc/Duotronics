from __future__ import annotations

from pathlib import Path

from duotronic_runtime.inference_router import plan_inference_route


class FakeOllamaInventoryRegistry:
    def ollama_inventory(self, *, timeout_seconds: float = 2.0, health=None):
        return {
            "schema_version": "xavi-ollama-inventory-v1",
            "offline_only": True,
            "observed_at_ms": 123456,
            "service_health_digest": "shake256-512:health",
            "observation_digest": "shake256-512:inventory",
            "observations": [
                {
                    "node_id": "tbi-production-3",
                    "service": "ollama",
                    "endpoint": "http://10.77.0.2:11434",
                    "healthy": True,
                    "inventory_observed": True,
                    "models": ["some-other-model:latest"],
                    "model_count": 1,
                    "latency_ms": 3.5,
                    "status_code": 200,
                },
                {
                    "node_id": "tbi-production-4",
                    "service": "ollama",
                    "endpoint": "http://ollama:11434",
                    "healthy": True,
                    "inventory_observed": True,
                    "models": ["qwen2.5-coder:3b", "qwen2.5-coder:1.5b"],
                    "model_count": 2,
                    "latency_ms": 1.2,
                    "status_code": 200,
                },
            ],
        }


def _report():
    return {
        "models": [
            {
                "name": "prod3-static-winner",
                "provider": "ollama",
                "model": "qwen2.5-coder:3b",
                "base_url": "http://10.77.0.2:11434",
                "enabled": True,
                "default": True,
                "capabilities": ["chat", "text_generation"],
                "modalities": ["text"],
                "metadata": {
                    "node_id": "tbi-production-3",
                    "node_status": "commissioned",
                    "scheduler_eligible": True,
                    "transport": "dedicated-private-ethernet",
                    "lan_preferred": True,
                    "internet_required": False,
                    "service_name": "ollama",
                },
            },
            {
                "name": "prod4-live-fallback",
                "provider": "ollama",
                "model": "qwen2.5-coder:3b",
                "base_url": "http://ollama:11434",
                "enabled": True,
                "default": False,
                "capabilities": ["chat", "text_generation"],
                "modalities": ["text"],
                "metadata": {
                    "node_id": "tbi-production-4",
                    "node_status": "commissioned",
                    "scheduler_eligible": True,
                    "transport": "local-container-network",
                    "lan_preferred": True,
                    "internet_required": False,
                    "service_name": "ollama",
                },
            },
        ],
        "tool_contracts": {},
        "backends": {},
    }


def test_require_live_filters_healthy_node_without_requested_model():
    route = plan_inference_route(
        _report(),
        {"task": "chat", "prefer_remote": True, "require_live_backend": True},
        service_registry=FakeOllamaInventoryRegistry(),
    )

    assert route["selected"]["name"] == "prod4-live-fallback"
    assert route["selected"]["node_id"] == "tbi-production-4"
    assert route["selected"]["live_backend_healthy"] is True
    assert route["selected"]["live_inventory_observed"] is True
    assert route["selected"]["live_model_available"] is True
    assert route["selected"]["live_endpoint"] == "http://ollama:11434"
    assert "shake256-512:inventory" in route["selected"]["live_observation_digests"]
    excluded = next(item for item in route["live_exclusions"] if item["name"] == "prod3-static-winner")
    assert excluded["reason"] == "ollama_model_not_observed_installed"
    assert excluded["live_healthy"] is True
    assert excluded["model_available"] is False
    assert "live_model_candidates_filtered" in route["warnings"]


def test_require_live_without_observer_fails_closed_for_ollama_models():
    route = plan_inference_route(
        _report(),
        {"task": "chat", "require_live_backend": True},
    )

    assert route["selected"] is None
    assert route["live_backend_observation"]["available"] is False
    assert "live_backend_observer_unavailable" in route["warnings"]
    assert "live_model_candidates_filtered" in route["warnings"]
    assert "no_matching_route" in route["warnings"]


def test_static_routing_remains_backward_compatible_without_live_requirement():
    route = plan_inference_route(_report(), {"task": "chat", "prefer_remote": True})

    assert route["selected"]["name"] == "prod3-static-winner"
    assert route["live_backend_observation"] is None
    assert route["live_exclusions"] == []


def test_http_mcp_toolruntime_import_is_not_function_shadowed():
    root = Path(__file__).resolve().parents[1]
    source = (root / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert source.count("from .tool_services import ToolRuntime") == 1
    assert 'if tool == "runtime.autonomy_research":\n        from .tool_services import ToolRuntime' not in source
