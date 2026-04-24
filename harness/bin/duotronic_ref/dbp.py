"""DBP frame ingress (Transport Profiles §5, §7).

Implements the transport state machine: shape → profile → integrity → replay
→ payload extraction → semantic decoder gate. A failed transition produces a
defined rejected/bypass state and never reaches authoritative memory.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import audit


TRANSPORT_STATES = (
    "received",
    "shape_checked",
    "profile_resolved",
    "integrity_checked",
    "replay_checked",
    "payload_extracted",
    "semantic_decoder_allowed",
    "canonicalization_candidate",
)


KNOWN_DBP_PROFILES = {
    "dbp-minsafe@v1": {"requires_integrity": True, "requires_sequence": False},
    "dbp-strict@v1": {"requires_integrity": True, "requires_sequence": True},
}


def _reject(state: str, code: str, **extra: Any) -> dict[str, Any]:
    audit.record(audit.EVT_TRANSPORT_REJECTED, state=state, code=code, **extra)
    out = {
        "semantic_decode_allowed": False,
        "witness8_decode_allowed": False,
        "normal_form_key_constructed": False,
        "trusted_memory_write": False,
        "audit_state": "rejected_untrusted_optional",
        "failure_code": code,
        "policy_mode": "transport_bypass",
        "state_reached": state,
    }
    out.update(extra)
    return out


def validate_dbp_frame(frame: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(frame, Mapping):
        return _reject("received", "frame_shape_invalid")
    if not frame.get("shape_valid", False):
        return _reject("received", "frame_shape_invalid")
    profile_id = frame.get("profile_id")
    profile = KNOWN_DBP_PROFILES.get(profile_id)
    if profile is None:
        return _reject(
            "shape_checked",
            "unknown_transport_profile",
            profile_id=profile_id,
        )
    integrity = frame.get("integrity_check")
    if profile["requires_integrity"] and integrity != "passed":
        return _reject(
            "profile_resolved",
            "transport_integrity_failed",
            profile_id=profile_id,
        )
    if profile["requires_sequence"]:
        seq = frame.get("sequence_number")
        if seq is None:
            return _reject(
                "integrity_checked",
                "transport_sequence_missing",
                profile_id=profile_id,
            )
    if frame.get("replay_token_seen"):
        return _reject(
            "integrity_checked",
            "transport_replay_window",
            profile_id=profile_id,
        )
    return {
        "semantic_decode_allowed": True,
        "witness8_decode_allowed": True,
        "trusted_memory_write": False,  # not until canonicalization
        "audit_state": "transport_validated",
        "failure_code": None,
        "policy_mode": "normal",
        "state_reached": "semantic_decoder_allowed",
        "profile_id": profile_id,
        "payload_kind": frame.get("payload_kind"),
    }


# Backwards-compatible alias used by Witness Contract App I.
ingress_dbp_frame = validate_dbp_frame


def run_reference_self_test() -> None:
    bad_shape = validate_dbp_frame({"shape_valid": False})
    assert bad_shape["failure_code"] == "frame_shape_invalid"
    bad_integrity = validate_dbp_frame(
        {"shape_valid": True, "profile_id": "dbp-minsafe@v1", "integrity_check": "failed"}
    )
    assert bad_integrity["failure_code"] == "transport_integrity_failed"
    ok = validate_dbp_frame(
        {
            "shape_valid": True,
            "profile_id": "dbp-minsafe@v1",
            "integrity_check": "passed",
            "payload_kind": "witness8",
        }
    )
    assert ok["semantic_decode_allowed"] is True


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("DBP reference self-test passed")
