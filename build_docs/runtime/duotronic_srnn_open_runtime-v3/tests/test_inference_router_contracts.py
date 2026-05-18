from __future__ import annotations

from duotronic_runtime.inference_router import plan_inference_route


def sample_report():
    return {
        "models": [
            {
                "name": "ollama-default",
                "provider": "ollama",
                "model": "llama3.2:1b",
                "enabled": True,
                "default": True,
                "endpoint_type": "ollama_api",
                "capabilities": ["chat", "text_generation"],
                "modalities": ["text"],
            },
            {
                "name": "ollama:qwen2.5-coder:7b",
                "provider": "ollama",
                "model": "qwen2.5-coder:7b",
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
            {
                "name": "ollama:nomic-embed-text:latest",
                "provider": "ollama",
                "model": "nomic-embed-text:latest",
                "enabled": True,
                "endpoint_type": "ollama_api",
                "capabilities": ["embeddings"],
                "modalities": ["embedding"],
            },
        ],
        "tool_contracts": {
            "code_interpreter_execute": {
                "witness_type": "CodeExecutionWitness",
                "observer_id": "code_interpreter.local",
                "capabilities": ["artifact_output", "code_execution", "code_interpreter"],
                "backend_env": ["CODE_INTERPRETER_URL"],
                "bounds": {"timeout_seconds": {"minimum": 1, "maximum": 60}, "network": False, "host_access": False},
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
            "code_interpreter": {"configured": True, "env": "CODE_INTERPRETER_URL"},
            "image_generation": {"configured": False, "env": "STABLE_DIFFUSION_URL|IMAGE_GENERATION_URL"},
        },
    }


def test_routes_code_generation_to_code_capable_model():
    route = plan_inference_route(sample_report(), {"task": "code_generation", "needs_tools": True})

    assert route["schema_version"] == "inference-route-v1"
    assert route["selected"]["route_kind"] == "model"
    assert route["selected"]["name"] == "ollama:qwen2.5-coder:7b"
    assert "code_generation" in route["selected"]["capabilities"]
    assert route["route_digest"].startswith("sha256:")


def test_routes_code_interpreter_to_witnessed_tool_contract():
    route = plan_inference_route(sample_report(), {"task": "code_interpreter", "require_live_backend": True})

    assert route["selected"]["route_kind"] == "tool"
    assert route["selected"]["name"] == "code_interpreter_execute"
    assert route["selected"]["backend_configured"] is True
    assert route["selected"]["witness_type"] == "CodeExecutionWitness"


def test_routes_image_generation_to_image_tool_even_when_backend_missing():
    route = plan_inference_route(sample_report(), {"task": "image_generation"})

    assert route["selected"]["route_kind"] == "tool"
    assert route["selected"]["name"] == "image_generate"
    assert route["selected"]["backend_configured"] is False
    assert "selected_tool_backend_not_configured" in route["warnings"]


def test_can_require_live_backend_for_image_generation():
    route = plan_inference_route(sample_report(), {"task": "image_generation", "require_live_backend": True})

    assert route["selected"] is None
    assert "no_matching_route" in route["warnings"]


def test_routes_vision_to_multimodal_model():
    route = plan_inference_route(sample_report(), {"task": "vision", "needs_vision": True})

    assert route["selected"]["name"] == "ollama:qwen2.5vl:7b"
    assert "vision" in route["selected"]["modalities"]


def test_routes_embeddings_to_embedding_model():
    route = plan_inference_route(sample_report(), {"task": "embeddings", "modalities": ["embedding"]})

    assert route["selected"]["name"] == "ollama:nomic-embed-text:latest"
    assert route["selected"]["modalities"] == ["embedding"]
