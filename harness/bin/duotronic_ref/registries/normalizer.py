"""Normalizer registry (Witness Contract Normalizer §7)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizerEntry:
    normalizer_id: str
    version: str
    target_family: str | None
    description: str
    has_migration_plan: bool


class NormalizerRegistry:
    def __init__(self, entries: list[NormalizerEntry]) -> None:
        self._entries = {(e.normalizer_id, e.version): e for e in entries}

    def resolve(self, normalizer_id: str, version: str) -> NormalizerEntry:
        try:
            return self._entries[(normalizer_id, version)]
        except KeyError as exc:
            raise KeyError(f"unknown normalizer {normalizer_id}@{version}") from exc

    def has(self, normalizer_id: str, version: str) -> bool:
        return (normalizer_id, version) in self._entries

    def all(self) -> list[NormalizerEntry]:
        return list(self._entries.values())


NORMALIZER_REGISTRY = NormalizerRegistry(
    [
        NormalizerEntry(
            normalizer_id="simple-bijective-word-normalizer",
            version="v1",
            target_family=None,
            description="Identity-on-canonical bijective word normalizer.",
            has_migration_plan=True,
        ),
        NormalizerEntry(
            normalizer_id="reflection-path-normalizer",
            version="v1",
            target_family=None,
            description="Free-reduction normalizer for reflection paths.",
            has_migration_plan=True,
        ),
        NormalizerEntry(
            normalizer_id="witness8-row-normalizer",
            version="v1",
            target_family=None,
            description="Profile-aware Witness8 row canonicalizer.",
            has_migration_plan=True,
        ),
    ]
)
