"""Schema registry — pins canonical-storage schema versions per DPFC App H.

Each entry contains: schema_id, version, owner, status. Lookups are
strict — unknown ids/versions raise. Used by the canonicalizer for the
`canonical_storage` field's `schema_version:Y` slot.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaEntry:
    schema_id: str
    version: str
    owner: str
    status: str  # active | deprecated | retired


class SchemaRegistry:
    def __init__(self, entries: list[SchemaEntry]) -> None:
        self._entries = {(e.schema_id, e.version): e for e in entries}

    def resolve(self, schema_id: str, version: str) -> SchemaEntry:
        try:
            return self._entries[(schema_id, version)]
        except KeyError as exc:
            raise KeyError(f"unknown schema {schema_id}@{version}") from exc

    def all(self) -> list[SchemaEntry]:
        return list(self._entries.values())


# Verbatim from DPFC App H §H.6 schema-registry baseline.
SCHEMA_REGISTRY = SchemaRegistry(
    [
        SchemaEntry("dpfc-core", "v1.0", "duotronic", "active"),
        SchemaEntry("witness-runtime", "v1.0", "duotronic", "active"),
        SchemaEntry("dbp-frame", "v1.0", "duotronic", "active"),
        SchemaEntry("wsb2-row", "v1.0", "duotronic", "active"),
        SchemaEntry("witness8-row", "v1.0", "duotronic", "active"),
        SchemaEntry("normalizer-profile", "v1.0", "duotronic", "active"),
        SchemaEntry("retention-baseline", "v1.0", "duotronic", "active"),
        SchemaEntry("policy-shield", "v1.0", "duotronic", "active"),
        SchemaEntry("migration-plan", "v1.0", "duotronic", "active"),
    ]
)
