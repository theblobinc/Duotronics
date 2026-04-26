"""Focused v1.5 Draft 2 federation and handshake invariants."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.mark.research
@pytest.mark.replay
def test_cluster_replay_identity_binds_lane_direction(run_operation: Any) -> None:
    observed = run_operation(
        "evaluate_cluster_replay_direction_binding",
        {
            "payload_hash": "sha256:same-payload",
            "lane_layout_id": "dbp-cluster-full-duplex-v1-layout-a",
            "direction_a": "downlink",
            "direction_b": "uplink",
        },
    )
    assert observed["replay_digest_a"] != observed["replay_digest_b"]
    assert observed["replay_digest_a_equals_b"] is False
    assert observed["reason"] == "direction_is_identity_affecting"


@pytest.mark.research
@pytest.mark.policy
@pytest.mark.replay
def test_federation_handshake_requires_s2_for_authority_and_admission(run_operation: Any) -> None:
    frame = run_operation(
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
    assert frame["accepted"] is False
    assert frame["rejection_reason"] == "authority_bearing_s1_frame"
    assert accepted["accepted"] is True
    assert accepted["lane_layout"] == "dbp-cluster-full-duplex-v1-layout-a"
    assert rejected["accepted"] is False
    assert rejected["rejection_reason"] == "unsupported_security"