"""WSB2 sparse-row ingress (Transport Profiles §6).

A WSB2 row carries one or more sparse lanes. An inactive lane is *absence*,
NOT numeric zero (Transport §6). Active lanes carry a Witness8 payload that
must still be decoded under the Witness8 explicit field order.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import audit
from .witness8 import decode_witness8


def decode_wsb2_rows(
    payload: Mapping[str, Any],
    *,
    profile_declares_numeric_zero: bool = False,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"failure_code": "wsb2_payload_invalid", "trusted_for_lookup": False}
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return {"failure_code": "wsb2_payload_missing_rows", "trusted_for_lookup": False}

    decoded: list[dict[str, Any]] = []
    for entry in rows:
        if not isinstance(entry, Mapping):
            return {"failure_code": "wsb2_row_invalid", "trusted_for_lookup": False}
        active = entry.get("active", True)
        lane = entry.get("lane")
        if not active:
            decoded.append(
                {
                    "lane": lane,
                    "presence_status": "structurally_absent",
                    "decode_status": "lane_inactive",
                    "trusted_for_lookup": False,
                }
            )
            continue
        witness = entry.get("witness8")
        if witness is None:
            return {
                "failure_code": "wsb2_active_lane_missing_witness8",
                "trusted_for_lookup": False,
            }
        result = decode_witness8(
            witness, profile_declares_numeric_zero=profile_declares_numeric_zero
        )
        result["lane"] = lane
        decoded.append(result)

    return {
        "failure_code": None,
        "rows": decoded,
        "trusted_for_lookup": "only_after_canonicalization",
    }


def run_reference_self_test() -> None:
    out = decode_wsb2_rows(
        {
            "rows": [
                {"lane": 1, "active": False},
                {
                    "lane": 2,
                    "active": True,
                    "witness8": [0.25, 0.6, 1.0, 0.5, 1.0, 0.25, 1.0, 1.0],
                },
            ]
        }
    )
    assert out["failure_code"] is None
    assert out["rows"][0]["presence_status"] == "structurally_absent"
    assert out["rows"][1]["decode_status"] == "decoded_lossy"


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("WSB2 reference self-test passed")
