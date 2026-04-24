"""Policy-shield property tests."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings

from harness_lib.fuzz_strategies import policy_events


@pytest.mark.normative
@pytest.mark.fuzz
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(case=policy_events())
def test_policy_shield_modes_are_documented(case: tuple[str, dict[str, Any]], run_operation: Any) -> None:
    op, given = case
    out = run_operation(op, given)
    valid_modes = {
        "normal",
        "degraded",
        "family_bypass",
        "transport_bypass",
        "lookup_bypass",
        "full_bypass",
    }
    assert out["mode"] in valid_modes
