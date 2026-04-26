import torch

from duotronic_wgrnn.cell import WGRNNCell
from duotronic_wgrnn.policy import WGRNNPolicy
from duotronic_wgrnn.witness import WitnessFeatureVector


def _cell() -> WGRNNCell:
    return WGRNNCell(input_dim=2, hidden_dim=2, cell_dim=2, slot_dim=2, num_slots=2)


def _witness(**overrides) -> WitnessFeatureVector:
    payload = {
        "witness_feature_vector_id": "wfv-clamp",
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


def _clamp(witness: WitnessFeatureVector, policy: WGRNNPolicy | None = None) -> tuple[float, float, float, float]:
    return _cell()._apply_policy_clamps(0.8, 0.7, 0.2, 0.9, witness, policy or WGRNNPolicy())


def test_policy_allow_write_false_blocks_write() -> None:
    assert _clamp(_witness(policy_allow_write=False))[0] == 0.0


def test_invalidation_blocks_write() -> None:
    assert _clamp(_witness(invalidation_score=0.95))[0] == 0.0


def test_low_replay_blocks_promotion() -> None:
    assert _clamp(_witness(replayability_score=0.1))[3] == 0.0


def test_contradiction_blocks_promotion() -> None:
    assert _clamp(_witness(contradiction_score=0.9))[3] == 0.0


def test_policy_allow_promote_false_blocks_promotion() -> None:
    assert _clamp(_witness(policy_allow_promote=False))[3] == 0.0


def test_high_novelty_low_confidence_forces_quarantine() -> None:
    assert _clamp(_witness(novelty_score=0.95, confidence_score=0.2))[2] == 1.0


def test_human_review_caps_write_and_blocks_promotion() -> None:
    g_write, _g_decay, _g_quarantine, g_promote = _clamp(_witness(human_review_required=True))
    assert g_write <= WGRNNPolicy().candidate_write_upper_bound
    assert g_promote == 0.0


def test_action_risk_blocks_write() -> None:
    assert _clamp(_witness(action_risk=0.95))[0] == 0.0


def test_transport_failure_blocks_write_and_promotion() -> None:
    g_write, _g_decay, _g_quarantine, g_promote = _clamp(_witness(transport_validated=False))
    assert g_write == 0.0
    assert g_promote == 0.0


def test_policy_validation_rejects_bad_threshold() -> None:
    policy = WGRNNPolicy(risk_limit=1.2)
    try:
        policy.validate_policy()
    except ValueError as exc:
        assert "risk_limit" in str(exc)
    else:
        raise AssertionError("bad threshold was accepted")


def test_no_gradient_threshold_mutation_surface() -> None:
    policy = WGRNNPolicy()
    before = policy.to_json_dict()
    _cell()._apply_policy_clamps(0.8, 0.7, 0.2, 0.9, _witness(), policy)
    assert policy.to_json_dict() == before
