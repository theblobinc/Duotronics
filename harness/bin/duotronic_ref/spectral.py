"""Spectral & EDO reference impl (Witness Contract App K).

Ported faithfully from §K.12.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, log2
from typing import Any, Mapping


def cents_of_ratio(ratio: str) -> float:
    return 1200.0 * log2(float(Fraction(ratio)))


def approximate_ratio_in_edo(ratio: str, steps: int) -> dict[str, Any]:
    just_cents = cents_of_ratio(ratio)
    nearest = round(steps * log2(float(Fraction(ratio))))
    edo_cents = 1200.0 * nearest / steps
    return {
        "nearest_step": nearest,
        "edostep": f"{nearest}\\{steps}",
        "just_cents": just_cents,
        "edo_cents": edo_cents,
        "error_cents": edo_cents - just_cents,
    }


def infer_missing_fundamental(components_hz: list[int]) -> dict[str, Any]:
    if not components_hz:
        return {"inference_type": "none", "trust_status": "rejected"}
    base = components_hz[0]
    for value in components_hz[1:]:
        base = gcd(base, value)
    if base < min(components_hz):
        pattern = [value // base for value in components_hz]
        return {
            "inferred_fundamental_hz": base,
            "evidence_pattern": pattern,
            "inference_type": "missing_fundamental",
            "trust_status": "conditional",
            "observed_as_fundamental": base in components_hz,
        }
    return {
        "inferred_fundamental_hz": base,
        "inference_type": "observed_fundamental",
        "trust_status": "conditional",
        "observed_as_fundamental": True,
    }


def transpose_mod(values: list[int], transposition: int, modulus: int) -> list[int]:
    return [(value + transposition) % modulus for value in values]


def interval_pattern(values: list[int], modulus: int) -> list[int]:
    return [
        ((values[(i + 1) % len(values)] - values[i]) % modulus)
        for i in range(len(values))
    ]


def transpose_retention(
    values: list[int], transposition: int, modulus: int
) -> dict[str, Any]:
    before = interval_pattern(values, modulus)
    after_values = transpose_mod(values, transposition, modulus)
    after = interval_pattern(after_values, modulus)
    return {
        "transposed_chord_external_steps": after_values,
        "before_pattern": before,
        "after_pattern": after,
        "preserved": ["internal_step_distances", "family_id", "modulus"],
        "expected_loss": ["absolute_root_unless_metadata_preserved"],
        "retention_score": 1.0 if before == after else 0.0,
    }


def validate_fourier_provenance(witness: Mapping[str, Any]) -> dict[str, Any]:
    required = ["sample_rate_hz", "window_function", "partials"]
    missing = [field for field in required if not witness.get(field)]
    if missing:
        return {
            "authoritative_memory_allowed": False,
            "audit_retention_allowed": True,
            "failure_code": "missing_fourier_provenance",
            "missing": missing,
        }
    return {"authoritative_memory_allowed": True, "failure_code": None}


def enharmonic_collapse_policy(
    source_family: str, target_family: str, left_step: int, right_step: int
) -> dict[str, Any]:
    if source_family == "edo31" and target_family == "edo12" and left_step != right_step:
        return {
            "collapse_allowed": "only_with_expected_loss",
            "expected_loss": [
                "spelling_identity",
                "voice_leading_microstate",
                "harmonic_function_hint",
            ],
            "alert_if_loss_undeclared": True,
        }
    return {"collapse_allowed": True, "expected_loss": []}


def temperament_error_witness(ratio: str, target_family: str) -> dict[str, Any]:
    if not target_family.startswith("edo"):
        return {"failure_code": "unsupported_target_family"}
    steps = int(target_family[3:])
    approx = approximate_ratio_in_edo(ratio, steps)
    error = approx["error_cents"]
    return {
        "nearest_step": f"{approx['nearest_step']}\\{steps}",
        "error_cents_approx": error,
        "preservation_class": "approximate_preserve",
    }


def run_spectral_edo_self_test() -> None:
    missing = infer_missing_fundamental([200, 300, 400, 500])
    assert missing["inferred_fundamental_hz"] == 100
    assert missing["inference_type"] == "missing_fundamental"
    retention = transpose_retention([0, 11, 18], 5, 31)
    assert retention["transposed_chord_external_steps"] == [5, 16, 23]
    assert retention["retention_score"] == 1.0
    assert approximate_ratio_in_edo("5/4", 31)["nearest_step"] == 10
    bad = validate_fourier_provenance({"partials": [{"frequency_hz": 200, "amplitude": 0.8}], "sample_rate_hz": None, "window_function": None})
    assert bad["authoritative_memory_allowed"] is False
    collapse = enharmonic_collapse_policy("edo31", "edo12", 2, 3)
    assert collapse["collapse_allowed"] == "only_with_expected_loss"


if __name__ == "__main__":  # pragma: no cover
    run_spectral_edo_self_test()
    print("Spectral/EDO reference self-test passed")
