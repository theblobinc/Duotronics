"""Expectation matching shared by fixture and trace runners."""

from __future__ import annotations

from typing import Any


def _resolve_path(observed: Any, path: str) -> tuple[bool, Any]:
    current = observed
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
            continue
        return False, None
    return True, current


def _containerize(actual: Any) -> Any:
    if isinstance(actual, (list, str, dict, tuple, set)):
        return actual
    return [actual]


def check_expectation_errors(observed: Any, expect: dict[str, Any]) -> list[str]:
    """Return a list of deterministic expectation failures; empty means pass."""
    errors: list[str] = []

    if "equals" in expect:
        for key, value in expect["equals"].items():
            exists, actual = _resolve_path(observed, key)
            if not exists or actual != value:
                errors.append(f"equals.{key}: expected {value!r} got {actual!r}")

    if "contains" in expect:
        for key, value in expect["contains"].items():
            exists, actual = _resolve_path(observed, key)
            if not exists or value not in _containerize(actual):
                errors.append(f"contains.{key}: {value!r} not found in {actual!r}")

    if "matches" in expect:
        for key, value in expect["matches"].items():
            exists, actual = _resolve_path(observed, key)
            if not exists or actual != value:
                errors.append(f"matches.{key}: expected {value!r} got {actual!r}")

    if "key_exists" in expect:
        for key in expect["key_exists"]:
            exists, _ = _resolve_path(observed, key)
            if not exists:
                errors.append(f"missing key {key!r}")

    if "key_truthy" in expect:
        for key in expect["key_truthy"]:
            exists, actual = _resolve_path(observed, key)
            if not exists or not actual:
                errors.append(f"key {key!r} not truthy: {actual!r}")

    if "key_falsy" in expect:
        for key in expect["key_falsy"]:
            exists, actual = _resolve_path(observed, key)
            if not exists or actual:
                errors.append(f"key {key!r} not falsy: {actual!r}")

    return errors