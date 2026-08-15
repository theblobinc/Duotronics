from __future__ import annotations

from typing import Any


def normalize_provenance(provenance: dict[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    provenance = provenance or {}
    normalized_items = []
    for key, value in sorted(provenance.items()):
        if isinstance(value, list):
            normalized_value = tuple(sorted(str(item).strip() for item in value))
        elif isinstance(value, dict):
            normalized_value = tuple((child_key, value[child_key]) for child_key in sorted(value))
        else:
            normalized_value = value
        normalized_items.append((str(key).strip().lower(), normalized_value))
    return tuple(normalized_items)
