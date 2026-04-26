from runtime_ref.api import run_meta_operation
from runtime_ref.meta.witness import MetaRecurrentWitness


def test_meta_memory_cell_step_learns_bounded_state() -> None:
    previous = MetaRecurrentWitness(controller_confidence=0.8, memory_cell_state={"tempo": 0.2})

    result = run_meta_operation(
        "step_meta_memory_cell",
        {
            "previous_witness": previous.to_dict(),
            "observation": {"tempo": 0.9, "energy": 0.4},
            "witness_features": {
                "confidence_score": 0.9,
                "replayability_score": 0.95,
                "policy_allow_write": True,
                "transport_validated": True,
            },
            "policy": {"min_confidence": 0.3, "max_memory_cell_step": 0.25},
        },
    )

    assert result["status"] == "accepted"
    assert result["diagnostics"]["write_gate"] > 0.0
    assert set(result["diagnostics"]["updated_coordinates"]) == {"tempo", "energy"}
    assert result["witness"]["memory_cell_state"]["tempo"] == 0.45
    assert result["witness"]["memory_cell_state"]["energy"] == 0.25


def test_meta_memory_cell_step_blocks_learning_when_transport_fails() -> None:
    previous = MetaRecurrentWitness(controller_confidence=0.8, memory_cell_state={"tempo": 0.2})

    result = run_meta_operation(
        "step_meta_memory_cell",
        {
            "previous_witness": previous.to_dict(),
            "observation": {"tempo": 0.9},
            "witness_features": {
                "confidence_score": 0.9,
                "policy_allow_write": True,
                "transport_validated": False,
            },
        },
    )

    assert result["status"] == "rejected"
    assert "transport_not_validated" in result["failure_reasons"]
    assert result["witness"]["memory_cell_state"]["tempo"] == 0.2