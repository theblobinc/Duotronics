"""Focused v1.5 Draft 2 cluster scheduling and task-authority invariants."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.research
@pytest.mark.policy
def test_gpu_task_avoids_cpu_only_node(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_cluster_node_schedulability",
        {
            "task_payload": {
                "task_type": "run_model_inference",
                "required_resources": {"gpu_bytes": 4_000_000_000},
            },
            "candidate_node": {"node_id": "node-xeon-01", "gpu_free_bytes": 0},
        },
    )
    assert observed["schedulable"] is False
    assert observed["reason"] == "gpu_requirement_not_met"


@pytest.mark.research
@pytest.mark.policy
def test_transport_failure_zeroes_task_outcome_authority(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_task_outcome_transport_authority",
        {
            "task_outcome_witness": {"normalizer_confidence": 0.92, "J_t": 3},
            "transport": {"dbp_s2_valid": False},
        },
    )
    assert observed["eta_t"] == 0.0
    assert observed["authority"] == 0.0
    assert observed["reason"] == "transport_failed"


@pytest.mark.research
@pytest.mark.policy
def test_transport_valid_task_outcome_respects_l5_limit(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_task_outcome_transport_authority",
        {
            "task_outcome_witness": {
                "normalizer_confidence": 0.92,
                "J_t": 3,
                "h_J_t": 0.80,
            },
            "transport": {"dbp_s2_valid": True},
            "policy": {"l5_limit": 0.70},
        },
    )
    assert observed["eta_t_before_policy"] == 0.736
    assert observed["eta_t_after_policy"] == 0.7
    assert observed["authority"] == 0.7