from runtime_ref.api import run_meta_operation


def test_learning_router_preserves_tensor_guardrail() -> None:
    result = run_meta_operation(
        "route_learning_view",
        {
            "concept_id": "tensor",
            "learner_intent": "programming",
            "learner_assertion": "a tensor is just an array",
        },
    )

    assert result["status"] == "accepted"
    assert result["selected_view_id"] == "tensor_computational_array"
    assert "array_representation_requires_basis_or_coordinate_choice" in result["formal_guardrails"]
    assert "tensor_array_to_geometric" in result["bridge_ids"]
    assert result["misconception_warnings"]
