"""Phase C: Policy clamp veto path validated against a local shield runtime stub.

The ShieldStub independently mirrors the WGRNNPolicy veto conditions, verifying
that the clamp logic is consistent with a policy-authority boundary. This is a
structural conformance test — both the cell's _apply_policy_clamps and the stub
must agree on veto outcomes for all covered scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.witness import WitnessFeatureVector


@dataclass(frozen=True)
class ShieldStub:
    """Minimal policy shield stub that mirrors WGRNNPolicy veto conditions.

    This stub encodes the write and promote gate veto logic independently
    from the cell implementation so the two can be compared structurally.
    """

    risk_limit: float = 0.75
    threshold_invalidate: float = 0.80
    max_contradiction: float = 0.70
    min_replay: float = 0.50
    require_transport: bool = True

    def write_vetoed(self, witness: WitnessFeatureVector) -> bool:
        if self.require_transport and not witness.transport_validated:
            return True
        if witness.action_risk > self.risk_limit:
            return True
        if witness.invalidation_score > self.threshold_invalidate:
            return True
        if not witness.policy_allow_write:
            return True
        return False

    def promote_vetoed(self, witness: WitnessFeatureVector) -> bool:
        if self.require_transport and not witness.transport_validated:
            return True
        if witness.contradiction_score > self.max_contradiction:
            return True
        if witness.replayability_score < self.min_replay:
            return True
        if not witness.policy_allow_promote:
            return True
        return False


def _cell() -> WGRNNCell:
    return WGRNNCell(input_dim=2, hidden_dim=2, cell_dim=2, slot_dim=2, num_slots=2)


def _witness(**overrides) -> WitnessFeatureVector:
    payload = {
        "witness_feature_vector_id": "wfv-shield",
        "confidence_score": 0.9,
        "contradiction_score": 0.1,
        "novelty_score": 0.1,
        "replayability_score": 0.9,
        "action_risk": 0.1,
        "policy_allow_write": True,
        "policy_allow_promote": True,
        "profile_requested_authority": 0.8,
        "normalizer_confidence": 0.9,
        "policy_limit": 0.7,
        "transport_validated": True,
        "canonicalization_validated": True,
    }
    payload.update(overrides)
    return WitnessFeatureVector(**payload)


@pytest.mark.parametrize("override,expected_write_vetoed", [
    ({"action_risk": 0.95}, True),
    ({"invalidation_score": 0.90}, True),
    ({"policy_allow_write": False}, True),
    ({"transport_validated": False}, True),
    ({}, False),
])
def test_shield_stub_write_veto_consistent_with_policy_clamp(
    override: dict, expected_write_vetoed: bool
) -> None:
    """ShieldStub.write_vetoed must agree with WGRNNPolicy clamping g_write to 0."""
    policy = WGRNNPolicy()
    stub = ShieldStub(
        risk_limit=policy.risk_limit,
        threshold_invalidate=policy.threshold_invalidate,
    )
    witness = _witness(**override)
    g_write, _g_decay, _g_quarantine, _g_promote = _cell()._apply_policy_clamps(
        0.8, 0.7, 0.2, 0.9, witness, policy
    )
    assert stub.write_vetoed(witness) == expected_write_vetoed
    if expected_write_vetoed:
        assert g_write == 0.0


@pytest.mark.parametrize("override,expected_promote_vetoed", [
    ({"replayability_score": 0.1}, True),
    ({"contradiction_score": 0.9}, True),
    ({"policy_allow_promote": False}, True),
    ({"transport_validated": False}, True),
    ({}, False),
])
def test_shield_stub_promote_veto_consistent_with_policy_clamp(
    override: dict, expected_promote_vetoed: bool
) -> None:
    """ShieldStub.promote_vetoed must agree with WGRNNPolicy clamping g_promote to 0."""
    policy = WGRNNPolicy()
    stub = ShieldStub(
        max_contradiction=policy.max_contradiction,
        min_replay=policy.min_replay,
    )
    witness = _witness(**override)
    _g_write, _g_decay, _g_quarantine, g_promote = _cell()._apply_policy_clamps(
        0.8, 0.7, 0.2, 0.9, witness, policy
    )
    assert stub.promote_vetoed(witness) == expected_promote_vetoed
    if expected_promote_vetoed:
        assert g_promote == 0.0


def test_shield_stub_is_immutable() -> None:
    """ShieldStub MUST be immutable — it models a fixed policy snapshot."""
    stub = ShieldStub()
    with pytest.raises((TypeError, AttributeError)):
        stub.risk_limit = 0.0  # type: ignore[misc]


def test_shield_stub_and_clamp_agree_for_clean_witness() -> None:
    """A clean witness (no flags) MUST NOT be vetoed by either stub or clamp."""
    policy = WGRNNPolicy()
    stub = ShieldStub(risk_limit=policy.risk_limit, threshold_invalidate=policy.threshold_invalidate)
    witness = _witness()
    g_write, _g_decay, _g_quarantine, g_promote = _cell()._apply_policy_clamps(
        0.8, 0.7, 0.2, 0.9, witness, policy
    )
    assert not stub.write_vetoed(witness)
    assert not stub.promote_vetoed(witness)
    assert g_write > 0.0


def test_shield_stub_thresholds_mirror_policy_defaults() -> None:
    """Default ShieldStub thresholds MUST match WGRNNPolicy defaults."""
    policy = WGRNNPolicy()
    stub = ShieldStub()
    assert stub.risk_limit == policy.risk_limit
    assert stub.threshold_invalidate == policy.threshold_invalidate
    assert stub.max_contradiction == policy.max_contradiction
    assert stub.min_replay == policy.min_replay
