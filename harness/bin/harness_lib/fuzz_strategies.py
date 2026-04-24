"""Hypothesis strategies for the fuzz suite (Witness Contract App S §S.2).

Categories: family-word, witness8-row, dbp-frame, normalizer-input,
spectral-chord, replay-identity, policy-event. Each returns a hypothesis
strategy producing a `(op, given)` tuple suitable for `run_operation`.
"""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st

from duotronic_ref.dpfc import HEX6, REFL3, EDO31


FAMILIES = (HEX6, REFL3, EDO31)
FAMILY_IDS = tuple(f.family_id for f in FAMILIES)


def family_words() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    @st.composite
    def _build(draw: Any) -> tuple[str, dict[str, Any]]:
        family = draw(st.sampled_from(FAMILIES))
        word = draw(
            st.lists(st.sampled_from(family.alphabet), min_size=1, max_size=8)
        )
        return ("evaluate_family_word", {"family_id": family.family_id, "word": word})

    return _build()


def family_successors() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    @st.composite
    def _build(draw: Any) -> tuple[str, dict[str, Any]]:
        family = draw(st.sampled_from(FAMILIES))
        word = draw(
            st.lists(st.sampled_from(family.alphabet), min_size=1, max_size=6)
        )
        return ("family_successor", {"family_id": family.family_id, "word": word})

    return _build()


def witness8_rows() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    @st.composite
    def _build(draw: Any) -> tuple[str, dict[str, Any]]:
        row = draw(st.lists(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False), min_size=8, max_size=8))
        declares = draw(st.booleans())
        return (
            "decode_witness8",
            {"row": row, "profile_declares_numeric_zero": declares},
        )

    return _build()


def witness8_absences() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    """Strategy that always produces all-zero rows to exercise absence."""
    return st.just(("decode_witness8", {"row": [0.0] * 8}))


def dbp_frames() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    @st.composite
    def _build(draw: Any) -> tuple[str, dict[str, Any]]:
        profile = draw(st.sampled_from(["dbp-minsafe@v1", "dbp-strict@v1"]))
        shape_valid = draw(st.booleans())
        integrity = draw(st.sampled_from(["passed", "failed"]))
        seq = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=1024)))
        replay_seen = draw(st.booleans())
        frame = {
            "shape_valid": shape_valid,
            "profile_id": profile,
            "integrity_check": integrity,
            "sequence_number": seq,
            "replay_token_seen": replay_seen,
            "payload_kind": "witness8",
        }
        return ("dbp_ingress", {"frame": frame})

    return _build()


def policy_events() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    @st.composite
    def _build(draw: Any) -> tuple[str, dict[str, Any]]:
        event = draw(
            st.sampled_from(
                [
                    "ok",
                    "transport_rejected",
                    "schema_mismatch",
                    "family_bypass_required",
                    "absence_zero_collision_attempt",
                    "normalizer_failure",
                    "retention_baseline_unfrozen",
                    "policy_breach",
                ]
            )
        )
        return ("policy_decide", {"event": event})

    return _build()


def spectral_chords() -> st.SearchStrategy[tuple[str, dict[str, Any]]]:
    @st.composite
    def _build(draw: Any) -> tuple[str, dict[str, Any]]:
        modulus = draw(st.sampled_from([12, 19, 22, 31]))
        size = draw(st.integers(min_value=2, max_value=5))
        values = draw(
            st.lists(
                st.integers(min_value=0, max_value=modulus - 1),
                min_size=size,
                max_size=size,
                unique=True,
            )
        )
        transposition = draw(st.integers(min_value=-modulus + 1, max_value=modulus - 1))
        return (
            "transpose_and_measure_interval_retention",
            {"values": sorted(values), "transposition": transposition, "modulus": modulus},
        )

    return _build()


ALL_STRATEGIES = {
    "family_word": family_words(),
    "family_successor": family_successors(),
    "witness8_row": witness8_rows(),
    "witness8_absence": witness8_absences(),
    "dbp_frame": dbp_frames(),
    "policy_event": policy_events(),
    "spectral_chord": spectral_chords(),
}
