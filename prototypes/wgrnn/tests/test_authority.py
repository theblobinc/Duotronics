import pytest

from duotronic_wgrnn.witness import WitnessFeatureVector


def _witness(**overrides) -> WitnessFeatureVector:
    payload = {
        "witness_feature_vector_id": "wfv-test",
        "confidence_score": 0.9,
        "profile_requested_authority": 0.8,
        "normalizer_confidence": 0.7,
        "policy_limit": 0.6,
        "transport_validated": True,
        "canonicalization_validated": True,
    }
    payload.update(overrides)
    return WitnessFeatureVector(**payload)


def test_transport_failure_zeroes_authority() -> None:
    assert _witness(transport_validated=False).compute_authority() == 0.0


def test_canonicalization_failure_zeroes_authority() -> None:
    assert _witness(canonicalization_validated=False).compute_authority() == 0.0


def test_authority_is_minimum_validated_input() -> None:
    assert _witness().compute_authority() == 0.6


def test_score_bounds_are_enforced() -> None:
    with pytest.raises(ValueError):
        _witness(confidence_score=1.2).validate_bounds()
