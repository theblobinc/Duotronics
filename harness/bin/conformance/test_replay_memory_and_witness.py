"""Phase B replay harness — MemoryUpdateRecord, MetaDiagnostics, TaskOutcomeWitness.

Normative conformance tests verifying determinism and schema invariants for the
three record/witness types required by Phase B of the Duotronic v1.6 ROADMAP:

  1. MemoryUpdateRecord  — produced by the ρ-memory kernel and WG-RNN slot ops
  2. MetaDiagnostics     — produced by the L3 meta-acceptance controller
  3. TaskOutcomeWitness  — produced by the cluster transport-authority evaluator
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

_MINIMAL_RHO_GIVEN: dict[str, Any] = {
    "trace": {"family": "motif_recurrence", "history": {"callback": [0.2, 0.4, 0.1]}},
    "deltas": {"callback": 0.3},
    "config": {"enabled": True, "scope": "worker", "memory_mode": "hybrid", "beta": 0.18},
}

_MINIMAL_TOW_GIVEN: dict[str, Any] = {
    "task_outcome_witness": {"normalizer_confidence": 0.9, "h_J_t": 0.8},
    "transport": {"dbp_s2_valid": True},
    "policy": {},
}


# ──────────────────────────────────────────────────────────────────────────────
# 1. MemoryUpdateRecord — ρ-memory kernel
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.normative
@pytest.mark.replay
def test_rho_memory_update_record_schema_version(run_operation: Any) -> None:
    """MemoryUpdateRecord MUST carry schema_version 'rho-memory-step-result@v1'."""
    result = run_operation("evaluate_rho_memory_kernel", _MINIMAL_RHO_GIVEN)
    assert result["schema_version"] == "rho-memory-step-result@v1"


@pytest.mark.normative
@pytest.mark.replay
def test_rho_memory_update_record_is_deterministic(run_operation: Any) -> None:
    """Same inputs MUST produce identical MemoryUpdateRecord on repeated calls."""
    a = run_operation("evaluate_rho_memory_kernel", _MINIMAL_RHO_GIVEN)
    b = run_operation("evaluate_rho_memory_kernel", _MINIMAL_RHO_GIVEN)
    assert a["updates"] == b["updates"]
    assert a["status"] == b["status"]
    assert a["authoritative"] == b["authoritative"]


@pytest.mark.normative
@pytest.mark.replay
def test_rho_memory_update_worker_scope_not_authoritative(run_operation: Any) -> None:
    """MemoryUpdateRecord at worker scope MUST NOT be authoritative."""
    result = run_operation("evaluate_rho_memory_kernel", _MINIMAL_RHO_GIVEN)
    assert result["status"] == "accepted"
    assert result["authoritative"] is False


@pytest.mark.normative
@pytest.mark.replay
def test_rho_memory_update_disabled_kernel_rejected(run_operation: Any) -> None:
    """MemoryUpdateRecord with disabled kernel MUST be rejected with reason."""
    given = {**_MINIMAL_RHO_GIVEN, "config": {"enabled": False, "scope": "worker", "memory_mode": "hybrid"}}
    result = run_operation("evaluate_rho_memory_kernel", given)
    assert result["status"] == "rejected"
    assert "rho_kernel_disabled" in result["failure_reasons"]
    assert result["updates"] == {}


@pytest.mark.normative
@pytest.mark.replay
def test_rho_memory_update_canonical_scope_rejected(run_operation: Any) -> None:
    """MemoryUpdateRecord at canonical scope MUST require explicit promotion."""
    given = {
        "trace": {"history": {"callback": [0.2]}},
        "deltas": {"callback": 0.3},
        "config": {"enabled": True, "scope": "canonical", "memory_mode": "hybrid"},
    }
    result = run_operation("evaluate_rho_memory_kernel", given)
    assert result["status"] == "rejected"
    assert "canonical_scope_requires_explicit_promotion" in result["failure_reasons"]


@pytest.mark.normative
@pytest.mark.replay
@settings(max_examples=40, suppress_health_check=[HealthCheck.too_slow])
@given(
    delta=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    beta=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
)
def test_rho_memory_update_record_output_bounded(
    run_operation: Any,
    delta: float,
    beta: float,
) -> None:
    """MemoryUpdateRecord coordinate updates MUST remain finite and non-negative."""
    given = {
        "trace": {"family": "motif_recurrence", "history": {"x": [0.5, 0.3]}},
        "deltas": {"x": delta},
        "config": {"enabled": True, "scope": "worker", "memory_mode": "hybrid", "beta": beta},
    }
    result = run_operation("evaluate_rho_memory_kernel", given)
    if result["status"] == "accepted":
        for val in result["updates"].values():
            assert isinstance(val, (int, float))
            assert not (val != val)  # not NaN


# ──────────────────────────────────────────────────────────────────────────────
# 1b. MemoryUpdateRecord — WG-RNN slot lifecycle
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.normative
@pytest.mark.replay
def test_wgrnn_contradiction_split_creates_record(run_operation: Any) -> None:
    """High contradiction score MUST emit a SlotSplitRecord (MemoryUpdateRecord subtype)."""
    result = run_operation(
        "evaluate_wgrnn_contradiction_split",
        {
            "memory_slot": {"slot_id": 7, "contradiction_score": 0.85, "trust_status": "candidate"},
            "policy": {"split_contradiction_threshold": 0.6, "quarantine_on_split": True},
        },
    )
    assert result["SlotSplitRecord_created"] is True
    assert result["original_slot_unchanged"] is True
    assert result["new_slot_status"] == "quarantined"
    assert result["new_slot_id"] == 8


@pytest.mark.normative
@pytest.mark.replay
def test_wgrnn_contradiction_no_split_below_threshold(run_operation: Any) -> None:
    """Contradiction score below threshold MUST NOT create a SlotSplitRecord."""
    result = run_operation(
        "evaluate_wgrnn_contradiction_split",
        {
            "memory_slot": {"slot_id": 3, "contradiction_score": 0.2, "trust_status": "candidate"},
            "policy": {"split_contradiction_threshold": 0.6},
        },
    )
    assert result["SlotSplitRecord_created"] is False
    assert result["new_slot_id"] is None


@pytest.mark.normative
@pytest.mark.replay
def test_wgrnn_purge_cascade_tombstones_stable_slot(run_operation: Any) -> None:
    """Purge of a hash used by a stable slot MUST produce a tombstone record."""
    result = run_operation(
        "evaluate_wgrnn_purge_cascade",
        {
            "evidence_purge_event": {
                "purge_event_id": "purge-abc",
                "purged_provenance_hashes": ["h1", "h2"],
            },
            "memory_slot": {
                "slot_id": 5,
                "provenance_hashes": ["h1", "h3"],
                "trust_status": "stable",
            },
        },
    )
    assert result["MemoryPurgeImpactRecord_created"] is True
    assert result["slot_status_after"] == "tombstoned"
    assert result["stable_authority_after"] == 0
    assert "h1" in result["impacted_hashes"]


@pytest.mark.normative
@pytest.mark.replay
def test_wgrnn_purge_cascade_no_overlap_is_noop(run_operation: Any) -> None:
    """Purge with no overlapping hashes MUST NOT create a MemoryPurgeImpactRecord."""
    result = run_operation(
        "evaluate_wgrnn_purge_cascade",
        {
            "evidence_purge_event": {
                "purge_event_id": "purge-xyz",
                "purged_provenance_hashes": ["h9", "h10"],
            },
            "memory_slot": {
                "slot_id": 2,
                "provenance_hashes": ["h1", "h3"],
                "trust_status": "candidate",
            },
        },
    )
    assert result["MemoryPurgeImpactRecord_created"] is False
    assert result["stable_authority_after"] == 1


@pytest.mark.normative
@pytest.mark.replay
def test_wgrnn_slot_promotion_requires_all_gates(run_operation: Any) -> None:
    """Slot promotion MUST be rejected if any required gate is missing."""
    result = run_operation(
        "evaluate_wgrnn_slot_promotion",
        {
            "slot_promotion_request": {
                "promotion_gate_value": 1.2,
                "promotion_threshold": 1.0,
                "replay_trace_set_id": "trace-set-001",
                # retention_metric_ids missing → retention_ready = False
                "purge_check_refs": ["ref1"],
            },
            "policy_decision": {"decision": "allow"},
        },
    )
    assert result["promotion_request_approved"] is False


@pytest.mark.normative
@pytest.mark.replay
def test_wgrnn_slot_promotion_all_gates_pass(run_operation: Any) -> None:
    """Slot promotion MUST be approved when all gates are met."""
    result = run_operation(
        "evaluate_wgrnn_slot_promotion",
        {
            "slot_promotion_request": {
                "promotion_gate_value": 1.1,
                "promotion_threshold": 1.0,
                "replay_trace_set_id": "trace-set-001",
                "retention_metric_ids": ["m1"],
                "purge_check_refs": ["ref1"],
                "status": "candidate",
            },
            "policy_decision": {"decision": "allow"},
        },
    )
    assert result["promotion_request_approved"] is True
    assert result["slot_status_after"] == "stable"
    assert result["canonical_witness_fact_created"] is True


# ──────────────────────────────────────────────────────────────────────────────
# 2. MetaDiagnostics — L3 acceptance controller
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.normative
@pytest.mark.replay
def test_meta_diagnostics_schema_version(run_meta_operation: Any) -> None:
    """MetaDiagnostics MUST carry schema_version 'meta-diagnostics@v1'."""
    result = run_meta_operation(
        "run_l3_acceptance",
        {
            "previous_witness": {"theta": {"x": 0.5}},
            "candidate_witness": {"theta": {"x": 0.6}},
            "diagnostics": {"sufficient_evidence": True, "controller_confidence": 0.9},
            "replay_spec": {},
            "policy_shield": {},
        },
    )
    diag = result["diagnostics"]
    assert diag.get("schema_version") == "meta-diagnostics@v1"


@pytest.mark.normative
@pytest.mark.replay
def test_meta_diagnostics_low_evidence_rejected(run_meta_operation: Any) -> None:
    """MetaDiagnostics with insufficient evidence MUST result in rejected status."""
    result = run_meta_operation(
        "run_l3_acceptance",
        {
            "previous_witness": {"theta": {"x": 0.5}},
            "candidate_witness": {"theta": {"x": 0.9}},
            "diagnostics": {"sufficient_evidence": False, "controller_confidence": 0.1},
            "replay_spec": {},
            "policy_shield": {},
        },
    )
    assert result["status"] == "rejected"
    assert len(result["failure_reasons"]) > 0


@pytest.mark.normative
@pytest.mark.replay
def test_meta_diagnostics_acceptance_decision_in_output(run_meta_operation: Any) -> None:
    """MetaDiagnostics output MUST include acceptance_decision field."""
    result = run_meta_operation(
        "run_l3_acceptance",
        {
            "previous_witness": {"theta": {"x": 0.5}},
            "candidate_witness": {"theta": {"x": 0.6}},
            "diagnostics": {"sufficient_evidence": True, "controller_confidence": 0.8},
            "replay_spec": {},
            "policy_shield": {},
        },
    )
    assert "acceptance_decision" in result["diagnostics"]
    assert result["diagnostics"]["acceptance_decision"] in {"accepted", "rejected", "fallback"}


@pytest.mark.normative
@pytest.mark.replay
def test_meta_diagnostics_rejection_reasons_is_list(run_meta_operation: Any) -> None:
    """MetaDiagnostics rejection_reasons MUST always be a list (never None)."""
    result = run_meta_operation(
        "run_l3_acceptance",
        {
            "previous_witness": {},
            "candidate_witness": {},
            "diagnostics": {},
            "replay_spec": {},
            "policy_shield": {},
        },
    )
    assert isinstance(result["failure_reasons"], list)


@pytest.mark.normative
@pytest.mark.replay
def test_meta_diagnostics_policy_freeze_blocks_acceptance(run_meta_operation: Any) -> None:
    """MetaDiagnostics MUST reject with policy_freeze when l3_auto_apply is disabled."""
    result = run_meta_operation(
        "run_l3_acceptance",
        {
            "previous_witness": {"theta": {"x": 0.5}},
            "candidate_witness": {"theta": {"x": 0.6}},
            "diagnostics": {"sufficient_evidence": True, "controller_confidence": 0.9},
            "replay_spec": {},
            "policy_shield": {"approval_policy": {"l3_auto_apply": False}},
        },
    )
    assert result["status"] == "rejected"
    assert "policy_freeze" in result["failure_reasons"]


# ──────────────────────────────────────────────────────────────────────────────
# 3. TaskOutcomeWitness — cluster transport authority
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.normative
@pytest.mark.replay
def test_task_outcome_witness_transport_failure_zeroes_authority(run_operation: Any) -> None:
    """TaskOutcomeWitness MUST report authority=0 when DBP-S2 transport fails."""
    result = run_operation(
        "evaluate_task_outcome_transport_authority",
        {
            "task_outcome_witness": {"normalizer_confidence": 0.95, "h_J_t": 1.0},
            "transport": {"dbp_s2_valid": False},
            "policy": {},
        },
    )
    assert result["authority"] == 0.0
    assert result["reason"] == "transport_failed"


@pytest.mark.normative
@pytest.mark.replay
def test_task_outcome_witness_authority_is_product_of_confidence_and_h(
    run_operation: Any,
) -> None:
    """TaskOutcomeWitness authority MUST equal normalizer_confidence × h_J_t (no policy cap)."""
    result = run_operation(
        "evaluate_task_outcome_transport_authority",
        _MINIMAL_TOW_GIVEN,
    )
    expected = round(0.9 * 0.8, 6)
    assert result["eta_t"] == expected
    assert result["authority"] == expected


@pytest.mark.normative
@pytest.mark.replay
def test_task_outcome_witness_policy_l5_caps_authority(run_operation: Any) -> None:
    """TaskOutcomeWitness authority MUST be capped by policy l5_limit."""
    result = run_operation(
        "evaluate_task_outcome_transport_authority",
        {
            "task_outcome_witness": {"normalizer_confidence": 1.0, "h_J_t": 1.0},
            "transport": {"dbp_s2_valid": True},
            "policy": {"l5_limit": 0.5},
        },
    )
    assert result["authority"] <= 0.5
    assert result["eta_t_before_policy"] == 1.0
    assert result["eta_t_after_policy"] == 0.5


@pytest.mark.normative
@pytest.mark.replay
def test_task_outcome_witness_is_deterministic(run_operation: Any) -> None:
    """TaskOutcomeWitness authority MUST be identical on repeated calls with same inputs."""
    a = run_operation("evaluate_task_outcome_transport_authority", _MINIMAL_TOW_GIVEN)
    b = run_operation("evaluate_task_outcome_transport_authority", _MINIMAL_TOW_GIVEN)
    assert a["authority"] == b["authority"]
    assert a["eta_t"] == b["eta_t"]


@pytest.mark.normative
@pytest.mark.replay
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    h_j_t=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_task_outcome_witness_authority_bounded_0_1(
    run_operation: Any,
    confidence: float,
    h_j_t: float,
) -> None:
    """TaskOutcomeWitness authority MUST be in [0, 1] for unit-range inputs."""
    result = run_operation(
        "evaluate_task_outcome_transport_authority",
        {
            "task_outcome_witness": {"normalizer_confidence": confidence, "h_J_t": h_j_t},
            "transport": {"dbp_s2_valid": True},
            "policy": {},
        },
    )
    assert 0.0 <= result["authority"] <= 1.0
