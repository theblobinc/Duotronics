from __future__ import annotations

from duotronic_runtime.operation_planner import classify_task, plan_operation


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
            },
            "image_generate": {
                "witness_type": "MediaGenerationWitness",
                "observer_id": "image_generation.local",
                "capabilities": ["artifact_output", "image_generation"],
                "backend_env": ["STABLE_DIFFUSION_URL", "IMAGE_GENERATION_URL"],
                "bounds": {"n": {"minimum": 1, "maximum": 4}},
            },
        },
        "backends": {
            "code_interpreter": {"configured": True},
            "image_generation": {"configured": False},
        },
    }


def test_classify_task_from_intent_and_goal_text():
    assert classify_task("please patch this repo", "other") == "code_generation"
    assert classify_task("run this pytest", "other") == "code_interpreter"
    assert classify_task("generate an image", "other") == "image_generation"
    assert classify_task("OCR this screenshot", "other") == "vision"
    assert classify_task("anything", "witness_contract") == "witness_contract"


def test_operation_plan_is_read_only_and_routes_code_goal():
    plan = plan_operation(sample_report(), {"goal": "patch the backend route planner", "intent": "code"})

    assert plan["schema_version"] == "operation-plan-v1"
    assert plan["execution_mode"] == "planned_only"
    assert plan["classified_task"] == "code_generation"
    assert plan["route"]["selected"]["name"] == "xavi-vscode-agent"
    assert all(step["read_only"] for step in plan["steps"])
    assert plan["expected_witnesses"] == ["OperationPlanWitness"]
    assert plan["plan_digest"].startswith("sha256:")


def test_operation_plan_can_select_witnessed_tool_route():
    plan = plan_operation(sample_report(), {"goal": "run a small python check", "intent": "run_code", "require_live_backend": True})

    assert plan["classified_task"] == "code_interpreter"
    assert plan["route"]["selected"]["route_kind"] == "tool"
    assert plan["route"]["selected"]["name"] == "code_interpreter_execute"
    assert plan["route"]["selected"]["witness_type"] == "CodeExecutionWitness"


def test_operation_plan_digest_is_stable():
    payload = {"goal": "explain the witness contract", "intent": "logic"}
    first = plan_operation(sample_report(), payload)
    second = plan_operation(sample_report(), payload)

    assert first["plan_digest"] == second["plan_digest"]


def test_operation_plan_http_and_mcp_surface_names_are_wired():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    api = (root / "app/duotronic_runtime/api.py").read_text()
    mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()

    assert 'class OperationPlanRequestModel' in api
    assert '@app.post("/v1/operations/plan")' in api
    assert 'from .operation_planner import plan_operation' in api
    assert '"name": "runtime.operation_plan"' in mcp
    assert 'if tool == "runtime.operation_plan"' in mcp
    assert 'return plan_operation(report, args)' in mcp
