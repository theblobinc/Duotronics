from __future__ import annotations

import json
from pathlib import Path

from duotronic_runtime.config import Settings
from duotronic_runtime.providers import ModelRegistry
from duotronic_runtime.service_registry import ServiceRegistry


ROOT = Path(__file__).resolve().parents[1]


def test_live_service_registry_is_offline_lan_first_and_gates_vm1():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    report = registry.report()

    assert report["offline_only"] is True
    assert report["network"]["backend_cidr"] == "10.77.0.0/24"
    assert report["network"]["internet_required"] is False

    prod3 = registry.node("tbi-production-3")
    assert prod3 is not None
    assert prod3["status"] == "commissioned"
    assert prod3["scheduler_eligible"] is True
    assert prod3["transport"]["private_ipv4"] == "10.77.0.2/24"
    assert prod3["services"]["ollama"]["primary_url"] == "http://10.77.0.2:11434"
    assert prod3["services"]["ollama"]["internet_required"] is False

    vm1 = registry.node("vm1")
    assert vm1 is not None
    assert vm1["status"] == "pending-private-address"
    assert vm1["scheduler_eligible"] is False
    assert vm1["declared_scheduler_eligible"] is True
    assert vm1["transport"]["private_ipv4"] is None
    assert vm1["management"]["bootstrap_ipv4"] == "209.53.57.58"
    assert vm1["transport"]["public_transport_role"] == "bootstrap-management-only"


def test_registry_annotates_private_ollama_models_without_ip_heuristics():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    record = registry.annotate_model(
        {
            "name": "wgrnn-chat-coordinator",
            "provider": "ollama",
            "model": "qwen2.5-coder:xavi-coordinator",
            "base_url": "http://10.77.0.2:11434",
            "metadata": {"xavi_role": "wgrnn_chat_primary"},
        }
    )
    metadata = record["metadata"]
    assert metadata["node_id"] == "tbi-production-3"
    assert metadata["node_status"] == "commissioned"
    assert metadata["scheduler_eligible"] is True
    assert metadata["transport"] == "dedicated-private-ethernet"
    assert metadata["lan_preferred"] is True
    assert metadata["internet_required"] is False


def test_model_registry_inherits_service_node_metadata(tmp_path):
    service_path = tmp_path / "services.json"
    service_path.write_text((ROOT / "config/service_registry.json").read_text())
    models_path = tmp_path / "models.json"
    models_path.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "name": "lan-test",
                        "provider": "ollama",
                        "model": "qwen2.5-coder:1.5b",
                        "base_url": "http://10.77.0.2:11434",
                        "enabled": True,
                    }
                ]
            }
        )
    )
    settings = Settings(model_registry_path=models_path, service_registry_path=service_path, ollama_enabled=False)
    registry = ModelRegistry(models_path, settings)
    record = registry.get("lan-test")
    assert record["metadata"]["node_id"] == "tbi-production-3"
    assert record["metadata"]["scheduler_eligible"] is True
    assert record["metadata"]["lan_preferred"] is True


def test_mcp_and_worker_expose_registry_as_read_only_observation():
    mcp = (ROOT / "app/duotronic_runtime/http_mcp.py").read_text()
    protocol = (ROOT / "app/duotronic_runtime/mcp_protocol.py").read_text()
    delegation = (ROOT / "app/duotronic_runtime/session_delegation.py").read_text()

    assert '"name": "runtime.service_registry"' in mcp
    assert 'return kernel.service_registry.report()' in mcp
    assert '"runtime.service_registry"' in protocol
    assert '"runtime.service_registry"' in delegation


def test_scheduler_candidates_use_commissioning_gate_and_prefer_gpu():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    result = registry.scheduler_candidates(role="wgrnn-worker", prefer_gpu=True, limit=8)
    assert result["offline_only"] is True
    assert result["candidates"]
    assert result["candidates"][0]["node_id"] == "tbi-production-3"
    assert result["candidates"][0]["transport"] == "dedicated-private-ethernet"
    assert result["candidates"][0]["internet_required"] is False
    vm1 = next(row for row in result["excluded"] if row["node_id"] == "vm1")
    assert "not_commissioned" in vm1["reasons"]
    assert "scheduler_ineligible" in vm1["reasons"]


def test_scheduler_does_not_use_vm1_capacity_before_private_commissioning():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    result = registry.scheduler_candidates(role="cpu-inference", minimum_memory_gib=64, limit=8)
    assert result["count"] == 1
    assert result["candidates"][0]["node_id"] == "tbi-production-4"
    vm1 = next(row for row in result["excluded"] if row["node_id"] == "vm1")
    assert "not_commissioned" in vm1["reasons"]
    assert "scheduler_ineligible" in vm1["reasons"]


def test_service_candidates_are_exposed_to_rest_and_mcp():
    api = (ROOT / "app/duotronic_runtime/api.py").read_text()
    mcp = (ROOT / "app/duotronic_runtime/http_mcp.py").read_text()
    delegation = (ROOT / "app/duotronic_runtime/session_delegation.py").read_text()
    protocol = (ROOT / "app/duotronic_runtime/mcp_protocol.py").read_text()

    assert '@app.get("/v1/runtime/service-registry")' in api
    assert '@app.get("/v1/runtime/service-candidates")' in api
    assert '"name": "runtime.service_candidates"' in mcp
    assert 'kernel.service_registry.scheduler_candidates(' in mcp
    assert '"runtime.service_candidates"' in delegation
    assert '"runtime.service_candidates"' in protocol


def test_local_coordinator_capacity_and_cpu_scheduler_are_observed():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    prod4 = registry.node("tbi-production-4")
    assert prod4 is not None
    assert prod4["capacity"]["logical_cpu_threads"] == 24
    assert prod4["capacity"]["memory_bytes"] == 135157612544
    assert prod4["capacity"]["gpus"][0]["name"] == "NVIDIA Quadro P2000"
    assert "cpu-inference" in prod4["roles"]

    result = registry.scheduler_candidates(role="cpu-inference", minimum_memory_gib=64, limit=8)
    assert result["candidates"]
    assert result["candidates"][0]["node_id"] == "tbi-production-4"
    vm1 = next(row for row in result["excluded"] if row["node_id"] == "vm1")
    assert "not_commissioned" in vm1["reasons"]
    assert "scheduler_ineligible" in vm1["reasons"]


def test_gpu_scheduler_keeps_rtx2070_as_preferred_accelerator():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    result = registry.scheduler_candidates(role="gpu-inference", prefer_gpu=True, limit=8)
    assert [row["node_id"] for row in result["candidates"][:2]] == ["tbi-production-3", "tbi-production-4"]
    assert result["candidates"][0]["score"] > result["candidates"][1]["score"]


def test_node_pin_never_bypasses_vm1_commissioning_gate():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    blocked = registry.scheduler_candidates(node_id="vm1", limit=8)
    assert blocked["count"] == 0
    vm1 = next(row for row in blocked["excluded"] if row["node_id"] == "vm1")
    assert "not_commissioned" in vm1["reasons"]
    assert "scheduler_ineligible" in vm1["reasons"]

    prod3 = registry.scheduler_candidates(node_id="tbi-production-3", service="ollama", limit=8)
    assert prod3["count"] == 1
    assert prod3["candidates"][0]["node_id"] == "tbi-production-3"
    assert prod3["candidates"][0]["service_endpoint"] == "http://10.77.0.2:11434"


def test_local_ollama_container_endpoint_is_owned_by_prod4():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    annotated = registry.annotate_model({
        "name": "local-test",
        "provider": "ollama",
        "model": "qwen2.5-coder:1.5b",
        "base_url": "http://ollama:11434",
        "metadata": {},
    })
    assert annotated["metadata"]["node_id"] == "tbi-production-4"
    assert annotated["metadata"]["scheduler_eligible"] is True
    assert annotated["metadata"]["internet_required"] is False


def test_service_candidate_api_accepts_memory_alias_and_node_pin():
    api = (ROOT / "app/duotronic_runtime/api.py").read_text()
    mcp = (ROOT / "app/duotronic_runtime/http_mcp.py").read_text()
    assert "min_memory_gib: float | None = None" in api
    assert "node_id: str | None = None" in api
    assert '"min_memory_gib": {"type": ["number", "null"]' in mcp
    assert '"node_id": {"type": ["string", "null"]}' in mcp


def test_delegation_resource_hints_resolve_only_commissioned_lan_nodes():
    from types import SimpleNamespace
    from fastapi import HTTPException
    from duotronic_runtime.session_delegation import SessionDelegationService

    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    service = object.__new__(SessionDelegationService)
    service.kernel = SimpleNamespace(service_registry=registry)

    resolved = service._resolve_resource_hints({
        "backend_role": "wgrnn-worker",
        "prefer_gpu": True,
        "require_backend": True,
    })
    scheduler = resolved["scheduler"]
    assert scheduler["offline_only"] is True
    assert scheduler["selected"]["node_id"] == "tbi-production-3"
    assert scheduler["registry_digest"]

    try:
        service._resolve_resource_hints({"node_id": "vm1", "require_backend": True})
    except HTTPException as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("vm1 must remain unavailable until privately commissioned")


def test_delegated_learning_binds_scheduler_decision_without_claiming_execution():
    from duotronic_runtime.delegation_learning import normalize_delegated_run, events_for_delegated_run

    run = {
        "delegation_id": "delegation-1",
        "run_id": "run-1",
        "work_id": "work-1",
        "project_key": "xavi.app-backend",
        "objective": "inspect local topology",
        "tool_name": "runtime.service_registry",
        "tool_args": {},
        "status": "completed",
        "result": {"ok": True},
        "resource_hints": {
            "scheduler": {
                "registry_digest": "registry-test",
                "status": "selected",
                "offline_only": True,
                "filters": {"prefer_gpu": True},
                "selected": {"node_id": "tbi-production-3", "score": 99.0},
            }
        },
    }
    experience = normalize_delegated_run(run, ordinal=1)
    assert experience["scheduler"]["selected_node_id"] == "tbi-production-3"
    assert experience["scheduler_digest"]
    events = events_for_delegated_run(run, ordinal=1)
    assert all(event["content"]["selected_node_id"] == "tbi-production-3" for event in events)
    assert all("backend:tbi-production-3" in event["tags"] for event in events)


def test_service_health_probes_only_configured_offline_services(monkeypatch):
    import duotronic_runtime.service_registry as service_registry_module

    calls = []
    client_kwargs = {}

    class FakeResponse:
        status_code = 200

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            calls.append(url)
            return FakeResponse()

    def fake_client(*args, **kwargs):
        client_kwargs.update(kwargs)
        return FakeClient()

    monkeypatch.setattr(service_registry_module.httpx, "Client", fake_client)
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    result = registry.service_health(service="ollama", timeout_seconds=1.0)

    assert result["schema_version"] == "xavi-service-health-v1"
    assert result["offline_only"] is True
    assert result["healthy_count"] == 2
    assert result["observation_count"] == 2
    assert result["observation_digest"]
    assert client_kwargs["trust_env"] is False
    assert any(url.startswith("http://ollama:11434/api/tags") for url in calls)
    assert any(url.startswith("http://10.77.0.2:11434/api/tags") for url in calls)
    assert all("209.53.57.58" not in url for url in calls)
    vm1 = next(row for row in result["skipped"] if row["node_id"] == "vm1")
    assert vm1["reason"] == "not_scheduler_ready"


def test_require_live_filters_static_candidates_by_current_service_health(monkeypatch):
    registry = ServiceRegistry(ROOT / "config/service_registry.json")

    def fake_health(**kwargs):
        return {
            "schema_version": "xavi-service-health-v1",
            "observation_digest": "health-test",
            "observations": [
                {"node_id": "tbi-production-3", "service": "ollama", "healthy": False, "reachable": False},
                {"node_id": "tbi-production-4", "service": "ollama", "healthy": True, "reachable": True},
            ],
        }

    monkeypatch.setattr(registry, "service_health", fake_health)
    result = registry.scheduler_candidates(service="ollama", prefer_gpu=True, require_live=True, limit=8)
    assert result["filters"]["require_live"] is True
    assert result["live_observation"]["observation_digest"] == "health-test"
    assert [row["node_id"] for row in result["candidates"]] == ["tbi-production-4"]
    prod3 = next(row for row in result["excluded"] if row["node_id"] == "tbi-production-3")
    assert "service_unhealthy_or_unobserved" in prod3["reasons"]


def test_require_live_without_named_service_fails_closed_as_no_candidates():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    result = registry.scheduler_candidates(role="wgrnn-worker", require_live=True, limit=8)
    assert result["count"] == 0
    assert result["candidates"] == []
    assert any("live_probe_requires_service" in row["reasons"] for row in result["excluded"])


def test_service_health_is_exposed_but_excluded_from_training_capture():
    api = (ROOT / "app/duotronic_runtime/api.py").read_text()
    mcp = (ROOT / "app/duotronic_runtime/http_mcp.py").read_text()
    protocol = (ROOT / "app/duotronic_runtime/mcp_protocol.py").read_text()
    delegation = (ROOT / "app/duotronic_runtime/session_delegation.py").read_text()

    assert '@app.get("/v1/runtime/service-health")' in api
    assert '"name": "runtime.service_health"' in mcp
    assert 'return kernel.service_registry.service_health(' in mcp
    capture = protocol.split("_AUTO_CAPTURE_EXACT", 1)[1].split("}", 1)[0]
    assert '"runtime.service_health"' in capture
    assert '"runtime.service_health"' in delegation
    assert '"require_live"' in mcp


def test_same_host_scheduler_advertises_runtime_internal_service_endpoint():
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    result = registry.scheduler_candidates(node_id="tbi-production-4", service="ollama", limit=2)
    assert result["count"] == 1
    candidate = result["candidates"][0]
    assert candidate["service_endpoint"] == "http://ollama:11434"
    assert candidate["service_host_endpoint"] == "http://127.0.0.1:11436"
    assert candidate["service_endpoint_scope"] == "runtime-internal"


def test_live_scheduler_advertises_exact_observed_endpoint(monkeypatch):
    registry = ServiceRegistry(ROOT / "config/service_registry.json")

    def fake_health(**kwargs):
        return {
            "schema_version": "xavi-service-health-v1",
            "offline_only": True,
            "observations": [
                {
                    "node_id": "tbi-production-4",
                    "service": "ollama",
                    "healthy": True,
                    "reachable": True,
                    "endpoint": "http://ollama:11434",
                    "status_code": 200,
                    "latency_ms": 1.0,
                }
            ],
            "skipped": [],
            "observation_digest": "service-health_test",
        }

    monkeypatch.setattr(registry, "service_health", fake_health)
    result = registry.scheduler_candidates(
        node_id="tbi-production-4",
        service="ollama",
        require_live=True,
        limit=2,
    )
    assert result["count"] == 1
    candidate = result["candidates"][0]
    assert candidate["service_endpoint"] == "http://ollama:11434"
    assert candidate["service_endpoint_scope"] == "observed-live"
    assert candidate["live_health"]["healthy"] is True


def test_node_pressure_combines_private_host_and_ollama_observations(monkeypatch):
    import httpx
    registry = ServiceRegistry(ROOT / "config/service_registry.json")

    def fake_get(self, url, *args, **kwargs):
        request = httpx.Request("GET", str(url))
        if str(url).endswith("/v1/metrics"):
            return httpx.Response(200, request=request, json={
                "schema_version": "xavi-node-metrics-v1",
                "node_id": "tbi-production-3",
                "observed_at_ms": 123,
                "cpu": {"load1_per_thread": 0.5},
                "memory": {"used_ratio": 0.5, "total_bytes": 64 * 1024**3, "available_bytes": 32 * 1024**3},
                "gpus": [{"memory_total_mib": 8192, "memory_used_mib": 4096, "utilization_gpu_percent": 50}],
            })
        if str(url).endswith("/api/ps"):
            return httpx.Response(200, request=request, json={"models": [{"name": "model:test", "size": 5_000_000_000, "size_vram": 4 * 1024**3}]})
        raise AssertionError(url)

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    result = registry.node_pressure(node_id="tbi-production-3", timeout_seconds=0.2)
    assert result["offline_only"] is True
    assert result["authority"] == "observation-only"
    row = result["observations"][0]
    assert row["host_metrics"]["observed"] is True
    assert row["ollama_process"]["observed"] is True
    assert 0.45 <= row["pressure"] <= 0.55
    assert row["confidence"] == 1.0
    assert row["observation_digest"].startswith("node-pressure-observation_")


def test_scheduler_pressure_penalty_is_bounded_and_not_authority(monkeypatch):
    registry = ServiceRegistry(ROOT / "config/service_registry.json")
    monkeypatch.setattr(registry, "node_pressure", lambda **kwargs: {
        "schema_version": "xavi-node-pressure-v1",
        "observation_digest": "node-pressure_test",
        "observations": [{
            "node_id": "tbi-production-3", "observed": True, "pressure": 0.8,
            "confidence": 0.2, "observation_digest": "node-pressure-observation_test",
        }],
    })
    result = registry.scheduler_candidates(node_id="tbi-production-3", service="ollama", observe_pressure=True, limit=4)
    row = result["candidates"][0]
    assert row["pressure_observed"] is True
    assert row["pressure_penalty"] == 28.0
    assert row["score"] == row["base_score"] - 28.0
    assert row["pressure_confidence"] == 0.2


def test_node_pressure_is_exposed_to_rest_mcp_and_worker_policy():
    api = (ROOT / "app/duotronic_runtime/api.py").read_text()
    mcp = (ROOT / "app/duotronic_runtime/http_mcp.py").read_text()
    delegation = (ROOT / "app/duotronic_runtime/session_delegation.py").read_text()
    protocol = (ROOT / "app/duotronic_runtime/mcp_protocol.py").read_text()
    assert '@app.get("/v1/runtime/node-pressure")' in api
    assert '"name": "runtime.node_pressure"' in mcp
    assert 'kernel.service_registry.node_pressure(' in mcp
    assert '"runtime.node_pressure"' in delegation
    assert '"runtime.node_pressure"' in protocol
    assert 'observe_pressure=True' in delegation
