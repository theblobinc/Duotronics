"""Focused v1.5 Draft 2 cognition research invariants."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.research
@pytest.mark.policy
def test_rho_kernel_worker_scope_is_diagnostic_only(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_rho_memory_kernel",
        {
            "trace": {"family": "motif_recurrence", "history": {"callback": [0.2, 0.4, 0.1]}},
            "deltas": {"callback": 0.3},
            "config": {"enabled": True, "scope": "worker", "memory_mode": "hybrid", "beta": 0.18},
        },
    )
    assert observed["status"] == "accepted"
    assert observed["authoritative"] is False
    assert observed["updates"]["callback"] == 0.403441


@pytest.mark.research
@pytest.mark.policy
def test_rho_kernel_canonical_scope_is_rejected_without_promotion(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_rho_memory_kernel",
        {
            "trace": {"history": {"callback": [0.2]}},
            "deltas": {"callback": 0.3},
            "config": {"enabled": True, "scope": "canonical", "memory_mode": "hybrid"},
        },
    )
    assert observed["status"] == "rejected"
    assert "canonical_scope_requires_explicit_promotion" in observed["failure_reasons"]


@pytest.mark.research
@pytest.mark.policy
def test_learning_router_keeps_tensor_views_distinct(run_operation: Any) -> None:
    observed = run_operation(
        "route_learning_view",
        {
            "concept_id": "tensor",
            "learner_intent": "programming",
            "learner_assertion": "a tensor is just an array",
        },
    )
    assert observed["status"] == "accepted"
    assert observed["selected_view_id"] == "tensor_computational_array"
    assert "array_representation_requires_basis_or_coordinate_choice" in observed["formal_guardrails"]
    assert "tensor_array_to_geometric" in observed["bridge_ids"]
    assert observed["diagnostics"]["answer_must_declare_bridge"] is True
