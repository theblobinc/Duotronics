from __future__ import annotations

import pytest

from duotronic_runtime.client_profiles import client_profiles, profile_payload
from duotronic_runtime.inference_router import plan_inference_route
from duotronic_runtime.operation_planner import plan_operation


def sample_report():
    return {
        "models": [
            {
                "name": "xavi-vscode-agent",
                "provider": "ollama",
                "model": "qwen2.5-coder:xavi-agent",
                "enabled": True,
                "endpoint_type": "ollama_api",
                "capabilities": ["chat", "text_generation", "code_generation", "code_agent", "tool_use"],
                "modalities": ["text"],
                "metadata": {"hardware_tier": "gpu_mesh"},
            },
            {
                "name": "ollama:qwen2.5vl:7b",
                "provider": "ollama",
                "model": "qwen2.5vl:7b",
                "enabled": True,
                "endpoint_type": "ollama_api",
                "capabilities": ["chat", "text_generation", "vision", "multimodal", "document_ocr"],
                "modalities": ["text", "vision"],
            },
        ],
        "tool_contracts": {
            "code_interpreter_execute": {
                "witness_type": "CodeExecutionWitness",
                "observer_id": "code_interpreter.local",
                "capabilities": ["artifact_output", "code_execution", "code_interpreter"],
                "backend_env": ["CODE_INTERPRETER_URL"],
                "bounds": {"timeout_seconds": {"minimum": 1, "maximum": 60}},
            }
        },
        "backends": {"code_interpreter": {"configured": True}},
    }


def test_profiles_include_librechat_and_openclaw_surfaces():
    profiles = client_profiles()

    assert "librechat.default" in profiles
    assert "librechat.code" in profiles
    assert "openclaw.agent" in profiles
    assert "openclaw.execute" in profiles
    assert profiles["librechat.code"]["surface"] == "librechat"
    assert profiles["openclaw.agent"]["surface"] == "openclaw"


def test_profile_payload_returns_copies_and_allows_overrides():
    first = profile_payload("openclaw.agent", overrides={"max_candidates": 2})
    second = profile_payload("openclaw.agent")

    assert first["max_candidates"] == 2
    assert second["max_candidates"] == 6
    assert first["task"] == "code_generation"
    assert first["needs_tools"] is True


def test_route_profiles_are_accepted_by_inference_router():
    report = sample_report()

    code_route = plan_inference_route(report, profile_payload("openclaw.agent"))
    vision_route = plan_inference_route(report, profile_payload("librechat.vision"))
    execute_route = plan_inference_route(report, profile_payload("openclaw.execute"))

    assert code_route["selected"]["name"] == "xavi-vscode-agent"
    assert vision_route["selected"]["name"] == "ollama:qwen2.5vl:7b"
    assert execute_route["selected"]["name"] == "code_interpreter_execute"


def test_operation_profiles_are_accepted_by_operation_planner():
    payload = profile_payload("openclaw.plan", mode="operation", overrides={"goal": "plan a repo patch"})
    plan = plan_operation(sample_report(), payload)

    assert plan["schema_version"] == "operation-plan-v1"
    assert plan["execution_mode"] == "planned_only"
    assert plan["route"]["selected"]["name"] == "xavi-vscode-agent"


def test_unknown_profile_and_mode_are_rejected():
    with pytest.raises(KeyError):
        profile_payload("missing.profile")
    with pytest.raises(ValueError):
        profile_payload("openclaw.agent", mode="missing")


def test_client_profiles_http_surface_is_wired():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    api = (root / "app/duotronic_runtime/api.py").read_text()

    assert '@app.get("/v1/client-profiles")' in api
    assert 'from .client_profiles import client_profiles' in api
    assert '"schema_version": "client-profiles-v1"' in api
    assert '"profiles": client_profiles()' in api


def test_client_profiles_mcp_surface_is_wired():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()

    assert '"name": "runtime.client_profiles"' in mcp
    assert '"description": "List stable client route profiles for LibreChat and OpenClaw."' in mcp
    assert '"additionalProperties": False' in mcp
    assert 'if tool == "runtime.client_profiles"' in mcp
    assert 'from .client_profiles import client_profiles' in mcp
    assert '"schema_version": "client-profiles-v1"' in mcp
    assert '"profiles": client_profiles()' in mcp
