"""Schema version pins shared between the reference impl and the harness.

If you bump any pinned version, you MUST also (a) ship a migration plan
and (b) update the replay-identity snapshots, otherwise both the
migration suite and the replay suite will fail.
"""

from __future__ import annotations

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
}

ACTIVE_FAMILY_REGISTRY_VERSION = "family-registry@v1.0"
ACTIVE_GEOMETRY_REGISTRY_VERSION = "geometry-registry@v1.0"
ACTIVE_POLICY_SHIELD_VERSION = "policy-shield@v1.0"
ACTIVE_FLOATING_POINT_PROFILE = "ieee754-double"
