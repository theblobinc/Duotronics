"""Replay-identity properties."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


@pytest.mark.normative
@pytest.mark.replay
def test_canonical_hash_is_key_order_independent(run_operation: Any) -> None:
    a = run_operation(
        "replay_compute_normal_form_hash",
        {"object": {"family_id": "hex6", "digits": ["h1", "h4"]}},
    )["normal_form_hash"]
    b = run_operation(
        "replay_compute_normal_form_hash",
        {"object": {"digits": ["h1", "h4"], "family_id": "hex6"}},
    )["normal_form_hash"]
    assert a == b


@pytest.mark.normative
@pytest.mark.replay
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(values=st.lists(st.integers(min_value=1, max_value=6), min_size=1, max_size=8))
def test_hash_change_when_value_changes(run_operation: Any, values: list[int]) -> None:
    a = run_operation(
        "replay_compute_normal_form_hash", {"object": {"k": values}}
    )["normal_form_hash"]
    b = run_operation(
        "replay_compute_normal_form_hash", {"object": {"k": values + [99]}}
    )["normal_form_hash"]
    assert a != b
