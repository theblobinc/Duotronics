from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from duotronic_runtime.mcp_protocol import _json_compatible
from duotronic_runtime.tool_services import ToolRuntime


class FakeEvidence:
    def witness(self, witness_type, payload, force="observe", status="recorded"):
        return {
            "witness_id": f"witness_{witness_type}",
            "witness_type": witness_type,
            "payload": payload,
            "force": force,
            "status": status,
            "observer_id": "fake-kernel",
        }


class FakeStore:
    def __init__(self):
        self.witnesses = []

    def insert_witness(self, witness):
        self.witnesses.append(witness)


class FakeKernel:
    def __init__(self):
        self.evidence = FakeEvidence()
        self.store = FakeStore()


def make_runtime(tmp_path, **overrides):
    settings = SimpleNamespace(
        runtime_data_dir=tmp_path,
        xavi_search_url="",
        xavi_search_api_key="",
        stable_diffusion_url="",
        **overrides,
    )
    kernel = FakeKernel()
    return ToolRuntime(settings=settings, kernel=kernel), kernel


def test_openai_tools_manifest_exposes_expected_tools(tmp_path):
    runtime, _kernel = make_runtime(tmp_path)

    tools = runtime.openai_tools()
    names = {tool["function"]["name"] for tool in tools}

    assert names == {"xavi_search_evidence", "code_interpreter_execute", "image_generate"}
    for tool in tools:
        assert tool["type"] == "function"
        assert tool["function"]["parameters"]["type"] == "object"


def test_code_execute_without_backend_returns_witnessed_disabled_result(tmp_path, monkeypatch):
    monkeypatch.delenv("CODE_INTERPRETER_URL", raising=False)
    runtime, kernel = make_runtime(tmp_path)

    result = asyncio.run(runtime.code_execute(language="python", code="print(2 + 2)"))

    assert result["ok"] is False
    assert result["error"] == "code_interpreter_backend_not_configured"
    assert result["witness"]["witness_type"] == "CodeExecutionWitness"
    assert kernel.store.witnesses[-1]["payload"]["required_backend"] == "CODE_INTERPRETER_URL"


def test_search_without_backend_returns_witnessed_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("XAVI_SEARCH_URL", raising=False)
    monkeypatch.delenv("SEARCH_API_URL", raising=False)
    runtime, kernel = make_runtime(tmp_path)

    result = asyncio.run(runtime.search_xavi(query="runtime tools", top_k=2))

    assert result["ok"] is True
    assert result["source"] == "fallback"
    assert result["witness"]["witness_type"] == "SearchResultWitness"
    assert result["results"][0]["source"] == "runtime.fallback"
    assert kernel.store.witnesses[-1]["status"] == "recorded"


def test_image_generation_without_backend_is_witnessed_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("STABLE_DIFFUSION_URL", raising=False)
    monkeypatch.delenv("IMAGE_GENERATION_URL", raising=False)
    runtime, kernel = make_runtime(tmp_path)

    result = asyncio.run(runtime.generate_image(prompt="small blue square", n=3))

    assert result["ok"] is False
    assert result["enabled"] is False
    assert result["images"] == []
    assert result["witness"]["witness_type"] == "MediaGenerationWitness"
    assert kernel.store.witnesses[-1]["status"] == "recorded"


def test_artifact_write_and_lookup_round_trip(tmp_path):
    runtime, _kernel = make_runtime(tmp_path)

    meta = runtime.write_artifact(b"artifact-bytes", ".txt", "text/plain", {"purpose": "test"})
    loaded = runtime.get_artifact(meta["artifact_id"])

    assert loaded is not None
    assert loaded["artifact_id"] == meta["artifact_id"]
    assert loaded["media_type"] == "text/plain"
    assert loaded["metadata"] == {"purpose": "test"}


def test_mcp_json_compatible_converts_datetime_for_structured_content():
    value = {"updated_at": datetime(2026, 5, 17, 1, 2, 3, tzinfo=timezone.utc)}

    converted = _json_compatible(value)

    assert converted == {"updated_at": "2026-05-17 01:02:03+00:00"}


def test_capability_report_combines_model_and_tool_capabilities(tmp_path):
    runtime, _kernel = make_runtime(tmp_path)
    models = [
        {
            "name": "ollama:qwen2.5-coder:3b",
            "provider": "ollama",
            "capabilities": ["chat", "code_generation"],
            "modalities": ["text"],
        },
        {
            "name": "ollama:nomic-embed-text:latest",
            "provider": "ollama",
            "capabilities": ["embeddings"],
            "modalities": ["embedding"],
        },
    ]

    report = runtime.capability_report(models=models)

    assert report["schema_version"] == "capabilities-v1"
    assert report["model_count"] == 2
    assert report["providers"] == {"ollama": 2}
    assert "code_generation" in report["capabilities"]
    assert "code_execution" in report["capabilities"]
    assert "image_generation" in report["capabilities"]
    assert report["model_capabilities"]["ollama:qwen2.5-coder:3b"] == ["chat", "code_generation"]
    assert report["modalities"]["ollama:nomic-embed-text:latest"] == ["embedding"]
    assert report["tool_capabilities"]["code_interpreter_execute"] == ["artifact_output", "code_execution", "code_interpreter"]
    assert report["tool_contracts"]["code_interpreter_execute"]["witness_type"] == "CodeExecutionWitness"
    assert report["backends"]["code_interpreter"]["env"] == "CODE_INTERPRETER_URL"
    assert report["capabilities_digest"].startswith("duoid:shake256-512:")


def test_openai_tools_have_matching_witness_contracts(tmp_path):
    runtime, _kernel = make_runtime(tmp_path)

    tool_names = {tool["function"]["name"] for tool in runtime.openai_tools()}
    contracts = runtime.tool_contracts()

    assert tool_names <= set(contracts)
    assert "operation_plan" not in tool_names
    for name, contract in contracts.items():
        assert contract["witness_type"].endswith("Witness")
        assert contract["observer_id"]
        assert contract["capabilities"] == sorted(contract["capabilities"])
        assert contract["success_status"] == "accepted"
        assert contract["fallback_status"] == "recorded"


def test_capability_report_includes_tool_contracts(tmp_path):
    runtime, _kernel = make_runtime(tmp_path)

    report = runtime.capability_report(models=[])

    assert "tool_contracts" in report
    assert report["tool_contracts"]["code_interpreter_execute"]["witness_type"] == "CodeExecutionWitness"
    assert report["tool_contracts"]["image_generate"]["witness_type"] == "MediaGenerationWitness"
    assert report["tool_contracts"]["xavi_search_evidence"]["witness_type"] == "SearchResultWitness"
    assert report["tool_contracts"]["operation_plan"]["witness_type"] == "OperationPlanWitness"
    assert "operation_planning" in report["tool_capabilities"]["operation_plan"]


def test_capability_report_digest_is_stable_with_tool_contracts(tmp_path):
    runtime, _kernel = make_runtime(tmp_path)
    models = [
        {
            "name": "ollama:qwen2.5-coder:3b",
            "provider": "ollama",
            "capabilities": ["code_generation", "chat"],
            "modalities": ["text"],
        }
    ]

    first = runtime.capability_report(models=models)
    second = runtime.capability_report(models=models)

    assert first["capabilities_digest"] == second["capabilities_digest"]
    assert first["tool_contracts"] == second["tool_contracts"]
