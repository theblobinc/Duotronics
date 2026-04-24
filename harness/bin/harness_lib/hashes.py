"""Canonical hashing for replay identity (BLAKE2b over canonical CBOR)."""

from __future__ import annotations

from typing import Any

from duotronic_ref.replay import (  # re-export for convenience
    blake2b_hex,
    canonical_cbor,
    input_hash,
    normal_form_hash,
)


__all__ = ["blake2b_hex", "canonical_cbor", "input_hash", "normal_form_hash", "hash_pair"]


def hash_pair(input_obj: Any, normal_form_obj: Any) -> dict[str, str]:
    return {
        "input_hash": input_hash(input_obj),
        "expected_normal_form_hash": normal_form_hash(normal_form_obj),
    }
