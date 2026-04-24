"""Witness8 row decoder (Witness Contract App I + Transport Profiles §3-4).

Implements the eight-field ordered decoder, the `token_free_absent` vs
`present_zero_value` vs `present_invalid` discrimination, and profile-flag
handling.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import audit


WITNESS8_FIELD_ORDER: tuple[str, ...] = (
    "value_norm",
    "n_sides_norm",
    "center_on",
    "activation_density",
    "kind_flag",
    "band_position",
    "parity",
    "degeneracy",
)


def _coerce(values: Any) -> tuple[list[Any] | None, str | None]:
    if isinstance(values, Mapping):
        return [values.get(field, 0) for field in WITNESS8_FIELD_ORDER], None
    if isinstance(values, (list, tuple)):
        return list(values), None
    return None, "row_not_iterable"


def decode_witness8(
    row: Any,
    *,
    profile_id: str = "witness8-minsafe@v1",
    profile_declares_numeric_zero: bool = False,
) -> dict[str, Any]:
    values, err = _coerce(row)
    if values is None:
        return {
            "decode_status": "present_invalid",
            "trusted_for_lookup": False,
            "normal_form_key_constructed": False,
            "failure_code": err or "row_invalid",
            "profile_id": profile_id,
        }
    if len(values) != 8:
        return {
            "decode_status": "present_invalid",
            "trusted_for_lookup": False,
            "normal_form_key_constructed": False,
            "failure_code": "field_order_invalid",
            "profile_id": profile_id,
        }
    if all(v == 0 for v in values):
        # token-free absence (Transport §4)
        return {
            "decode_status": "token_free_absent",
            "presence_status": "structurally_absent",
            "numeric_zero_inferred": False,
            "normal_form_key_constructed": False,
            "trusted_for_lookup": False,
            "field_order_used": list(WITNESS8_FIELD_ORDER),
            "profile_id": profile_id,
        }
    if profile_declares_numeric_zero and values[0] == 0:
        return {
            "decode_status": "decoded_exact",
            "presence_status": "present_zero_value",
            "token_free_absent": False,
            "numeric_zero_inferred": True,
            "trusted_for_lookup": "only_after_canonicalization",
            "field_order_used": list(WITNESS8_FIELD_ORDER),
            "profile_id": profile_id,
        }
    return {
        "decode_status": "decoded_lossy",
        "presence_status": "present_nonzero_value",
        "trusted_for_lookup": "only_after_canonicalization",
        "field_order_used": list(WITNESS8_FIELD_ORDER),
        "profile_id": profile_id,
    }


def assert_absence_zero_separation(decoded: Mapping[str, Any]) -> None:
    """Raise if a decoder collapses absence onto numeric zero."""
    if (
        decoded.get("decode_status") == "token_free_absent"
        and decoded.get("numeric_zero_inferred") is True
    ):
        audit.record(audit.EVT_ABSENCE_ZERO_COLLISION_ACCEPTED, decoded=dict(decoded))
        raise AssertionError("absence_zero_collision: absence decoded as numeric zero")


def run_reference_self_test() -> None:
    assert decode_witness8([0] * 8)["decode_status"] == "token_free_absent"
    shuffled = {
        "degeneracy": 1.0,
        "parity": 1.0,
        "band_position": 0.5,
        "kind_flag": 1.0,
        "activation_density": 0.125,
        "center_on": 1.0,
        "n_sides_norm": 0.6,
        "value_norm": 0.0,
    }
    out = decode_witness8(shuffled, profile_declares_numeric_zero=True)
    assert out["presence_status"] == "present_zero_value"
    bad = decode_witness8([1, 2, 3])
    assert bad["decode_status"] == "present_invalid"


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("Witness8 reference self-test passed")
