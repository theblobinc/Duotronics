"""Spectral / EDO properties."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings

from harness_lib.fuzz_strategies import spectral_chords


@pytest.mark.normative
@pytest.mark.fuzz
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(case=spectral_chords())
def test_transposition_preserves_interval_pattern(case: tuple[str, dict[str, Any]], run_operation: Any) -> None:
    op, given = case
    out = run_operation(op, given)
    assert out["before_pattern"] == out["after_pattern"], (
        "Transposition mod EDO must preserve the canonical interval pattern"
    )
    assert out["retention_score"] == 1.0
