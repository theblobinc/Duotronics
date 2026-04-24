"""Property-based tests for DPFC core (DPFC v5.6 §28).

Verifies the algebraic properties that every implementation must satisfy.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from duotronic_ref.dpfc import HEX6, REFL3, EDO31


FAMILIES = (HEX6, REFL3, EDO31)


@pytest.mark.normative
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(data=st.data())
def test_evaluate_inverse_round_trip(run_operation: Any, data: Any) -> None:
    family = data.draw(st.sampled_from(FAMILIES))
    word = data.draw(st.lists(st.sampled_from(family.alphabet), min_size=1, max_size=8))
    value = run_operation(
        "evaluate_family_word", {"family_id": family.family_id, "word": word}
    )["value"]
    encoded = run_operation(
        "encode_core_to_family", {"family_id": family.family_id, "core_index": value}
    )["word"]
    assert encoded == word, "Φ_F⁻¹∘Φ_F must be the identity on canonical words"


@pytest.mark.normative
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(data=st.data())
def test_successor_increments_value(run_operation: Any, data: Any) -> None:
    family = data.draw(st.sampled_from(FAMILIES))
    word = data.draw(st.lists(st.sampled_from(family.alphabet), min_size=1, max_size=6))
    succ = run_operation(
        "family_successor", {"family_id": family.family_id, "word": word}
    )["successor"]
    a = run_operation("evaluate_family_word", {"family_id": family.family_id, "word": word})["value"]
    b = run_operation("evaluate_family_word", {"family_id": family.family_id, "word": succ})["value"]
    assert b == a + 1, "successor must add exactly one to the core magnitude"


@pytest.mark.normative
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(data=st.data())
def test_conversion_preserves_core_magnitude(run_operation: Any, data: Any) -> None:
    src = data.draw(st.sampled_from(FAMILIES))
    tgt = data.draw(st.sampled_from(FAMILIES))
    word = data.draw(st.lists(st.sampled_from(src.alphabet), min_size=1, max_size=6))
    out = run_operation(
        "family_conversion",
        {"word": word, "source_family": src.family_id, "target_family": tgt.family_id},
    )
    assert out["source_core_magnitude"] == out["target_core_magnitude"], (
        "convert_family must preserve the core magnitude µ_n"
    )


@pytest.mark.normative
@settings(max_examples=100)
@given(a=st.integers(min_value=1, max_value=2_000), b=st.integers(min_value=1, max_value=2_000))
def test_exported_nonneg_correction_is_a_plus_b_plus_1(run_operation: Any, a: int, b: int) -> None:
    out = run_operation(
        "exported_nonnegative_add_with_correction", {"left": a, "right": b}
    )
    expected = (a - 1) + (b - 1) + 1
    assert out["value"] == expected, "App F: exported_nonneg_add must include +1 affine correction"


@pytest.mark.normative
def test_without_correction_must_flag_policy_mismatch(run_operation: Any) -> None:
    out = run_operation(
        "exported_nonnegative_add_without_correction", {"left": 2, "right": 3}
    )
    assert out["failure_code"] == "export_policy_mismatch"
    assert out["trusted_arithmetic_use"] is False
    assert out["required_correction"] == 1
