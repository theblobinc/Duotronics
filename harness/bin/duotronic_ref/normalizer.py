"""Normalizer profile registry (Normalizer Profiles v1.0 §7).

Each normalizer is deterministic, version-pinned, and emits explicit failure
codes from §8. Per §6 they MUST NOT silently switch family identity, switch
schema version, or collapse token-free absence to numeric zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from . import audit
from .dpfc import REFL3, HEX6, EDO31, Family, canonical_storage, evaluate_family_word
from .witness8 import WITNESS8_FIELD_ORDER, decode_witness8


# §8 failure-code table.
NORMALIZER_FAILURE_CODES = {
    "unknown_family": "family_bypass",
    "schema_mismatch": "reject",
    "invalid_digit": "reject",
    "empty_family_word": "reject",
    "ambiguous_orbit": "family_bypass",
    "field_order_invalid": "reject",
    "absence_zero_collision": "full_bypass",
    "normalizer_timeout": "degraded",
}


_REGISTRY: dict[str, Family] = {f.family_id: f for f in (HEX6, REFL3, EDO31)}


def get_family(family_id: str | None) -> Family | None:
    if family_id is None:
        return None
    return _REGISTRY.get(family_id)


@dataclass(frozen=True)
class NormalizerProfile:
    normalizer_id: str
    normalizer_version: str
    input_schema: str
    output_schema: str
    ambiguity_policy: str
    canonical_selection_rule: str


PROFILES: dict[str, NormalizerProfile] = {
    "simple-bijective-word-normalizer@v1": NormalizerProfile(
        normalizer_id="simple-bijective-word-normalizer",
        normalizer_version="simple-bijective-word-normalizer@v1",
        input_schema="family-word-raw@v1",
        output_schema="dpfc-family-object@v5.8",
        ambiguity_policy="reject",
        canonical_selection_rule="ordinal_digit_sequence",
    ),
    "reflection-path-normalizer@v1": NormalizerProfile(
        normalizer_id="reflection-path-normalizer",
        normalizer_version="reflection-path-normalizer@v1",
        input_schema="reflection-path-raw@v1",
        output_schema="dpfc-family-object@v5.8",
        ambiguity_policy="select_canonical",
        canonical_selection_rule="lexicographically_smallest_reduced_path",
    ),
    "witness8-row-normalizer@v1": NormalizerProfile(
        normalizer_id="witness8-row-normalizer",
        normalizer_version="witness8-row-normalizer@v1",
        input_schema="witness8-row@v1",
        output_schema="witness8-decoded-state@v1",
        ambiguity_policy="reject",
        canonical_selection_rule="explicit_field_order",
    ),
}


def normalize_family_word(
    given: Mapping[str, Any],
    *,
    schema_version: str = "dpfc-family@v5.8",
) -> dict[str, Any]:
    family_id = given.get("family_id")
    family = get_family(family_id)
    if family is None:
        return {
            "failure_code": "unknown_family",
            "policy_action": NORMALIZER_FAILURE_CODES["unknown_family"],
            "lookup_allowed": False,
        }
    if family.schema_version != schema_version:
        return {
            "failure_code": "schema_mismatch",
            "policy_action": NORMALIZER_FAILURE_CODES["schema_mismatch"],
            "lookup_allowed": False,
        }
    word = list(given.get("word", []))
    if not word:
        return {
            "failure_code": "empty_family_word",
            "policy_action": NORMALIZER_FAILURE_CODES["empty_family_word"],
            "lookup_allowed": False,
        }
    for digit in word:
        if digit not in family.alphabet:
            return {
                "failure_code": "invalid_digit",
                "policy_action": NORMALIZER_FAILURE_CODES["invalid_digit"],
                "invalid_digit": digit,
                "lookup_allowed": False,
            }
    core_index = evaluate_family_word(word, family)
    return {
        "failure_code": None,
        "policy_action": "normal",
        "canonical_storage": canonical_storage(word, family),
        "core_magnitude": f"mu_{core_index}",
        "lookup_allowed": True,
        "normalizer_version": "simple-bijective-word-normalizer@v1",
    }


def normalize_reflection_path(
    given: Mapping[str, Any],
) -> dict[str, Any]:
    """Reduce a free reflection path to canonical form (paths over generators
    that square to identity). Empty after reduction is rejected as ambiguous."""
    raw = list(given.get("path", []))
    reduced: list[str] = []
    for token in raw:
        if reduced and reduced[-1] == token:
            reduced.pop()
        else:
            reduced.append(token)
    if not reduced:
        return {
            "failure_code": "empty_family_word",
            "policy_action": NORMALIZER_FAILURE_CODES["empty_family_word"],
            "lookup_allowed": False,
        }
    return {
        "failure_code": None,
        "policy_action": "normal",
        "reduced_path": reduced,
        "lookup_allowed": True,
        "normalizer_version": "reflection-path-normalizer@v1",
    }


def normalize_witness8_row(
    given: Mapping[str, Any],
    *,
    profile_declares_numeric_zero: bool = False,
) -> dict[str, Any]:
    row = given.get("witness8_row")
    declares = given.get("profile_declares_numeric_zero", profile_declares_numeric_zero)
    decoded = decode_witness8(row, profile_declares_numeric_zero=declares)
    decoded.setdefault("field_order_used", list(WITNESS8_FIELD_ORDER))
    decoded["normalizer_version"] = "witness8-row-normalizer@v1"
    if decoded.get("decode_status") == "present_invalid":
        decoded["failure_code"] = "field_order_invalid"
        decoded["policy_action"] = NORMALIZER_FAILURE_CODES["field_order_invalid"]
    return decoded


def run_reference_self_test() -> None:
    ok = normalize_family_word({"family_id": "hex6", "word": ["h1", "h4"]})
    assert ok["core_magnitude"] == "mu_10"
    assert ok["canonical_storage"].endswith("digits:1 4")
    bad = normalize_family_word({"family_id": "unknown", "word": []})
    assert bad["failure_code"] == "unknown_family"
    bad_digit = normalize_family_word({"family_id": "hex6", "word": ["h9"]})
    assert bad_digit["failure_code"] == "invalid_digit"


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("Normalizer reference self-test passed")
