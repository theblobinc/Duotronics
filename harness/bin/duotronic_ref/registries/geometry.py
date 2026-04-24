"""Geometry registry (DPFC App H §H.4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeometryEntry:
    geometry_id: str
    family_id: str
    n_sides: int
    chirality: str  # left | right | achiral
    notes: str = ""


class GeometryRegistry:
    def __init__(self, entries: list[GeometryEntry]) -> None:
        self._entries = {e.geometry_id: e for e in entries}

    def resolve(self, geometry_id: str) -> GeometryEntry:
        try:
            return self._entries[geometry_id]
        except KeyError as exc:
            raise KeyError(f"unknown geometry {geometry_id}") from exc

    def all(self) -> list[GeometryEntry]:
        return list(self._entries.values())


GEOMETRY_REGISTRY = GeometryRegistry(
    [
        GeometryEntry("hex6.regular", "hex6", 6, "achiral"),
        GeometryEntry("refl3.regular", "refl3", 3, "achiral"),
        GeometryEntry("edo31.cyclic", "edo31", 31, "achiral"),
    ]
)
