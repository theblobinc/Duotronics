"""Deliberately broken external implementation used as a negative canary.

This module violates the Witness8 absence/zero separation rule so the
harness can prove that an external implementation crossing the plugin
seam is still caught by the safety invariants.
"""

from __future__ import annotations

from typing import Any, Mapping

from duotronic_ref.api import run_operation as reference_run_operation


def run_operation(op_name: str, given: Mapping[str, Any]) -> dict[str, Any]:
    if op_name == "decode_witness8" and list(given.get("row", [])) == [0] * 8:
        return {
            "decode_status": "token_free_absent",
            "numeric_zero_inferred": True,
            "profile_id": given.get("profile_id", "witness8-minsafe@v1"),
        }
    return reference_run_operation(op_name, given)