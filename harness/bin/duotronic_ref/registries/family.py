"""Family registry (DPFC App H §H.3 — Reflective baseline registry)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyEntry:
    family_id: str
    base: int
    digit_alphabet: tuple[str, ...]
    is_bijective_base: bool
    notes: str = ""


class FamilyRegistry:
    def __init__(self, entries: list[FamilyEntry]) -> None:
        self._entries = {e.family_id: e for e in entries}

    def resolve(self, family_id: str) -> FamilyEntry:
        try:
            return self._entries[family_id]
        except KeyError as exc:
            raise KeyError(f"unknown family {family_id}") from exc

    def all(self) -> list[FamilyEntry]:
        return list(self._entries.values())


FAMILY_REGISTRY = FamilyRegistry(
    [
        FamilyEntry(
            family_id="hex6",
            base=6,
            digit_alphabet=("h1", "h2", "h3", "h4", "h5", "h6"),
            is_bijective_base=True,
            notes="Hex-aligned bijective-base-6 reflective family.",
        ),
        FamilyEntry(
            family_id="refl3",
            base=3,
            digit_alphabet=("r1", "r2", "r3"),
            is_bijective_base=True,
            notes="3-fold reflective baseline family.",
        ),
        FamilyEntry(
            family_id="edo31",
            base=31,
            digit_alphabet=tuple(f"e{i}" for i in range(1, 32)),
            is_bijective_base=True,
            notes="31-EDO spectral-aligned reflective family.",
        ),
    ]
)
