"""Transport state-machine fuzz / smoke."""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from harness_lib.fuzz_strategies import dbp_frames


@pytest.mark.normative
@pytest.mark.fuzz
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(case=dbp_frames())
def test_dbp_frame_never_writes_trusted_memory(case: tuple[str, dict[str, Any]], run_operation: Any) -> None:
    op, given = case
    out = run_operation(op, given)
    assert out["trusted_memory_write"] is False, (
        "Transport stage must NEVER write to trusted memory"
    )


@pytest.mark.normative
def test_unknown_payload_kind_fails_softly(run_operation: Any) -> None:
    out = run_operation(
        "ingress_frame",
        {
            "frame": {
                "shape_valid": True,
                "profile_id": "dbp-minsafe@v1",
                "integrity_check": "passed",
                "payload_kind": "made-up",
                "payload": {},
            }
        },
    )
    assert out["decoded"]["failure_code"] == "unknown_payload_kind"
