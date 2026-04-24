"""Witness-runtime properties: absence vs numeric-zero MUST stay separated."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


@pytest.mark.normative
def test_absence_never_decodes_as_numeric_zero(run_operation: Any) -> None:
    out = run_operation("decode_witness8", {"row": [0] * 8})
    assert out["decode_status"] == "token_free_absent"
    assert out["numeric_zero_inferred"] is False
    assert out["normal_form_key_constructed"] is False
    assert out["trusted_for_lookup"] is False


@pytest.mark.normative
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    row=st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=8,
        max_size=8,
    )
)
def test_witness8_decoder_never_collapses_absence(run_operation: Any, row: list[float]) -> None:
    out = run_operation("decode_witness8", {"row": row})
    if all(v == 0 for v in row):
        assert out["decode_status"] == "token_free_absent"
        assert out["numeric_zero_inferred"] is False
    else:
        assert out["decode_status"] != "token_free_absent"


@pytest.mark.normative
def test_canonicalize_unknown_family_routes_to_family_bypass(run_operation: Any) -> None:
    out = run_operation(
        "canonicalize_witness_key_bundle",
        {"bundle": {"family_id": "no-such", "digits": []}},
    )
    assert out["canonicalization_result"] == "family_bypass_required"
    assert out["lookup_allowed"] is False
