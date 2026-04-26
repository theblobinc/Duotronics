"""Schema version pins shared between the reference impl and the harness.

If you bump any pinned version, you MUST also (a) ship a migration plan
and (b) update the replay-identity snapshots, otherwise both the
migration suite and the replay suite will fail.
"""

from __future__ import annotations

import os

ACTIVE_SCHEMA_VERSIONS: dict[str, str] = {
    "dpfc-core": "v1.0",
    "witness-runtime": "v1.0",
    "dbp-frame": "v1.0",
    "wsb2-row": "v1.0",
    "witness8-row": "v1.0",
    "normalizer-profile": "v1.0",
    "retention-baseline": "v1.0",
    "policy-shield": "v1.0",
    "migration-plan": "v1.0",
}

ACTIVE_NORMALIZER_VERSIONS: dict[str, str] = {
    "simple-bijective-word-normalizer": "v1",
    "reflection-path-normalizer": "v1",
    "witness8-row-normalizer": "v1",
}

ACTIVE_TRANSPORT_PROFILES: dict[str, str] = {
    "dbp-minsafe": "v1",
    "dbp-strict": "v1",
    "dbp-cluster-full-duplex-v1": "v1",
}

CURRENT_FIXTURE_SCHEMA_VERSION = "v1.2"

SUPPORTED_SCHEMA_SNAPSHOTS: dict[str, dict[str, str]] = {
    "v1.0": {
        "family_registry_version": "family-registry@v1.0",
        "geometry_registry_version": "geometry-registry@v1.0",
        "policy_shield_version": "policy-shield@v1.0",
    },
    "v1.2": {
        "family_registry_version": "family-registry@v1.2",
        "geometry_registry_version": "geometry-registry@v1.0",
        "policy_shield_version": "policy-shield@v1.2",
    },
    "v1.5-draft-2": {
        "family_registry_version": "family-registry@v1.4",
        "geometry_registry_version": "geometry-registry@v1.0",
        "policy_shield_version": "policy-shield@v1.8",
    },
}

SPEC_TARGETS: dict[str, dict[str, str]] = {
    "v1.2": {
        "dpfc": "dpfc-core@v5.8",
        "witness": "witness-contract@v10.8",
        "source_architecture": "source-architecture@v1.3",
        "fixture_pack": "conformance-fixtures@v1.2",
        "meta_runtime": "meta-runtime-contract@v0.2",
    },
    "v1.5-draft-2": {
        "dpfc": "dpfc-core@v5.15",
        "witness": "witness-contract@v10.16",
        "source_architecture": "source-architecture@v1.7",
        "fixture_pack": "conformance-fixtures@v1.5-draft-2",
        "meta_runtime": "meta-runtime-contract@v0.5",
    },
}


def normalize_fixture_schema_version(value: str | None) -> str:
    if value is None:
        return CURRENT_FIXTURE_SCHEMA_VERSION
    normalized = value.strip()
    if normalized.startswith("conformance-fixtures@"):
        normalized = normalized.split("@", 1)[1]
    if normalized not in SUPPORTED_SCHEMA_SNAPSHOTS:
        raise ValueError(
            f"unsupported schema version {value!r}; expected one of {sorted(SUPPORTED_SCHEMA_SNAPSHOTS)}"
        )
    return normalized


def fixture_pack_id_for(schema_version: str | None = None) -> str:
    normalized = normalize_fixture_schema_version(schema_version)
    return f"conformance-fixtures@{normalized}"


def spec_target_for(schema_version: str | None = None) -> dict[str, str]:
    normalized = normalize_fixture_schema_version(schema_version)
    spec_target = dict(SPEC_TARGETS[normalized])
    spec_target["fixture_pack"] = fixture_pack_id_for(normalized)
    return spec_target


def resolve_schema_snapshot(schema_version: str | None = None) -> dict[str, str]:
    selected = schema_version or os.environ.get("DUOTRONIC_SCHEMA_VERSION")
    normalized = normalize_fixture_schema_version(selected)
    return dict(SUPPORTED_SCHEMA_SNAPSHOTS[normalized])


ACTIVE_SPEC_TARGET = spec_target_for(CURRENT_FIXTURE_SCHEMA_VERSION)


ACTIVE_FAMILY_REGISTRY_VERSION = resolve_schema_snapshot()["family_registry_version"]
ACTIVE_GEOMETRY_REGISTRY_VERSION = resolve_schema_snapshot()["geometry_registry_version"]
ACTIVE_POLICY_SHIELD_VERSION = resolve_schema_snapshot()["policy_shield_version"]
ACTIVE_FLOATING_POINT_PROFILE = "ieee754-double"
