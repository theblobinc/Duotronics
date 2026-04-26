"""Focused v1.5 Draft 2 research invariants.

These tests exercise the new v1.5 research surface directly so the
cluster and WG-RNN rules are checked independently of generic fixture
runner coverage.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.research
@pytest.mark.policy
def test_wgrnn_human_review_caps_write_and_blocks_promotion(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_wgrnn_policy_gates",
        {
            "witness_feature_vector": {
                "confidence_score": 0.93,
                "policy_allow_write": True,
                "policy_allow_promote": True,
                "human_review_required": True,
            },
            "policy": {"candidate_write_upper_bound": 0.1},
        },
    )
    assert observed["g_promote_after_clamp"] == 0.0
    assert observed["g_write_after_clamp"] == 0.1
    assert observed["stable_write_allowed"] is False


@pytest.mark.research
@pytest.mark.policy
def test_cluster_conflict_defaults_to_restricted_resolution(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_cluster_task_conflict",
        {
            "task_delegation_conflict": {
                "task_delegation_conflict_id": "tdc-overcommit-xeon-01",
                "conflict_type": "overcommit_cpu",
                "default_resolution": "least_loaded_node_gets_task",
            }
        },
    )
    assert observed["policy_mode"] == "restricted"
    assert observed["if_alternate_node_available"] == "reassign_lower_priority_or_second_task"
    assert observed["if_no_alternate_node"] == "queue_or_no_action"


@pytest.mark.research
@pytest.mark.policy
@pytest.mark.replay
def test_authority_bearing_cluster_frame_requires_s2(run_operation: Any) -> None:
    observed = run_operation(
        "validate_cluster_authority_frame",
        {
            "frame": {
                "direction": "downlink",
                "lane_id": 3,
                "lane_name": "command",
                "security_mode": "S1",
                "payload_kind": "TaskDelegationActionPayload",
                "authority_bearing": True,
            }
        },
    )
    assert observed["accepted"] is False
    assert observed["rejection_reason"] == "authority_bearing_s1_frame"


@pytest.mark.research
@pytest.mark.policy
@pytest.mark.replay
def test_node_hello_requires_s2_and_assigns_cluster_layout(run_operation: Any) -> None:
    accepted = run_operation(
        "evaluate_node_hello",
        {
            "node_hello": {
                "node_hello_id": "nh-node-xeon-03-001",
                "transport": {
                    "dbp_profile_id": "dbp-cluster-full-duplex-v1",
                    "supported_security_modes": ["S2"],
                },
            }
        },
    )
    rejected = run_operation(
        "evaluate_node_hello",
        {
            "node_hello": {
                "node_hello_id": "nh-bad-node-001",
                "transport": {
                    "dbp_profile_id": "dbp-cluster-full-duplex-v1",
                    "supported_security_modes": ["Open", "S1"],
                },
            }
        },
    )
    assert accepted["accepted"] is True
    assert accepted["admission_status"] == "restricted"
    assert accepted["lane_layout"] == "dbp-cluster-full-duplex-v1-layout-a"
    assert accepted["heartbeat_timeout_seconds"] == 30
    assert rejected["accepted"] is False
    assert rejected["rejection_reason"] == "unsupported_security"
    assert rejected["retry_allowed"] is False


@pytest.mark.research
@pytest.mark.policy
def test_cluster_learning_mode_blocks_profile_task_without_active_mode(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_cluster_learning_mode_gate",
        {
            "task_payload": {
                "task_type": "start_profile_learning",
                "policy": {"learning_mode_required": "active"},
            },
            "cluster_policy": {"cluster_learning_mode": "audit_only"},
        },
    )
    assert observed["action_allowed"] is False
    assert observed["reason"] == "cluster_learning_mode_insufficient"


@pytest.mark.research
@pytest.mark.policy
def test_least_loaded_node_selector_prefers_lowest_queue_pressure(run_operation: Any) -> None:
    observed = run_operation(
        "select_cluster_node_for_task",
        {
            "nodes": [
                {
                    "node_id": "node-xeon-01",
                    "effective_capacity_score": 0.59,
                    "effective_queue_pressure": 0.25,
                },
                {
                    "node_id": "node-xeon-02",
                    "effective_capacity_score": 0.61,
                    "effective_queue_pressure": 0.70,
                },
                {
                    "node_id": "node-xeon-03",
                    "effective_capacity_score": 0.58,
                    "effective_queue_pressure": 0.10,
                },
            ]
        },
    )
    assert observed["expected_selected_node"] == "node-xeon-03"
    assert observed["reason"] == "sufficient_capacity_lowest_queue_pressure"
