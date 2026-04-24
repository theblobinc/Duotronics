"""Canonicalizer & normal-form key bundle (Witness Contract App I §I.2).

Constructs the witness key bundle, computes the normal-form (BLAKE2b over
canonical CBOR) hash, and emits explicit failure codes when canonicalization
fails.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import audit
from .dpfc import canonical_storage, evaluate_family_word
from .normalizer import get_family


def canonicalize_witness_key_bundle(raw_bundle: Mapping[str, Any]) -> dict[str, Any]:
    family_id = raw_bundle.get("family_id")
    family = get_family(family_id)
    if family is None:
        return {
            "canonicalization_result": "family_bypass_required",
            "failure_code": "unknown_family",
            "lookup_allowed": False,
            "trust_status": "rejected",
            "policy_mode": "family_bypass",
        }
    declared_schema = raw_bundle.get("family_schema_version")
    if declared_schema and declared_schema != family.schema_version:
        return {
            "canonicalization_result": "schema_mismatch",
            "failure_code": "schema_mismatch",
            "lookup_allowed": False,
            "trust_status": "rejected",
            "policy_mode": "degraded",
        }
    word = list(raw_bundle.get("digits", []))
    if not word:
        return {
            "canonicalization_result": "malformed_reject",
            "failure_code": "empty_family_word",
            "lookup_allowed": False,
            "trust_status": "rejected",
        }
    for digit in word:
        if digit not in family.alphabet:
            return {
                "canonicalization_result": "malformed_reject",
                "failure_code": "invalid_digit",
                "invalid_digit": digit,
                "lookup_allowed": False,
                "trust_status": "rejected",
            }
    core_index = evaluate_family_word(word, family)
    storage = canonical_storage(word, family)
    return {
        "canonicalization_result": "canonical_success",
        "canonical_storage": storage,
        "core_magnitude": f"mu_{core_index}",
        "lookup_allowed": True,
        "trust_status": "canonicalized",
        "policy_mode": "normal",
        "family_id": family.family_id,
        "family_schema_version": family.schema_version,
        "digit_ordinals": [family.ordinal(d) for d in word],
    }


def run_reference_self_test() -> None:
    ok = canonicalize_witness_key_bundle(
        {"family_id": "hex6", "family_schema_version": "dpfc-family@v5.8", "digits": ["h1", "h4"]}
    )
    assert ok["core_magnitude"] == "mu_10"
    bad = canonicalize_witness_key_bundle({"family_id": "no-such", "digits": []})
    assert bad["failure_code"] == "unknown_family"


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("Canonicalizer reference self-test passed")
