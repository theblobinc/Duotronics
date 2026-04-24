"""Negative canary proving the harness rejects a broken external impl."""

from __future__ import annotations

import pytest

from duotronic_ref import audit, witness8
from harness_lib.dispatch import get_run_operation


@pytest.mark.normative
def test_broken_external_impl_absence_zero_collapse_is_rejected() -> None:
    audit.LEDGER.clear()
    run_operation = get_run_operation("harness_lib.canaries.broken_absence_zero_impl")
    decoded = run_operation(
        "decode_witness8",
        {
            "row": [0, 0, 0, 0, 0, 0, 0, 0],
            "profile_id": "witness8-minsafe@v1",
        },
    )
    with pytest.raises(AssertionError):
        witness8.assert_absence_zero_separation(decoded)
    assert audit.LEDGER.events(audit.EVT_ABSENCE_ZERO_COLLISION_ACCEPTED)