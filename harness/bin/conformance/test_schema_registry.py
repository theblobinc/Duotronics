"""Schema-registry conformance suite — versioned IDs and compatibility checks.

Normative tests ensuring:
  1. All entries in SCHEMA_REGISTRY are resolvable by ID and version.
  2. All ACTIVE_SCHEMA_VERSIONS resolve in the registry without error.
  3. SUPPORTED_SCHEMA_SNAPSHOTS snapshots can all be resolved.
  4. Schema version normalization rejects unknown versions.
  5. Schema snapshot keys are internally consistent across snapshots.
  6. Versioned schema_version strings from the runtime APIs use the expected
     naming convention (e.g. rho-memory-step-result@v1).
  7. The WG-RNN replay-identity fixture carries the correct schema_version.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from duotronic_ref.registries.schema import SCHEMA_REGISTRY, SchemaEntry
from harness_lib.schema_versions import (
    ACTIVE_SCHEMA_VERSIONS,
    ACTIVE_NORMALIZER_VERSIONS,
    ACTIVE_TRANSPORT_PROFILES,
    CURRENT_FIXTURE_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_SNAPSHOTS,
    SPEC_TARGETS,
    normalize_fixture_schema_version,
    resolve_schema_snapshot,
    fixture_pack_id_for,
    spec_target_for,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FIXTURE_JSON = (
    Path(__file__).parents[3]
    / "build_docs"
    / "witness_contract"
    / "v1.6 - Draft 3"
    / "refs"
    / "examples"
    / "wgrnn_replay_identity_fixture_v1.json"
)


def _load_fixture() -> dict:
    with open(_FIXTURE_JSON, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# 1. SCHEMA_REGISTRY resolvability
# ---------------------------------------------------------------------------


def test_schema_registry_all_entries_are_resolvable():
    """Every entry in SCHEMA_REGISTRY can be retrieved by (schema_id, version)."""
    for entry in SCHEMA_REGISTRY.all():
        resolved = SCHEMA_REGISTRY.resolve(entry.schema_id, entry.version)
        assert resolved is entry


def test_schema_registry_unknown_id_raises():
    with pytest.raises(KeyError, match="unknown schema"):
        SCHEMA_REGISTRY.resolve("does-not-exist", "v1.0")


def test_schema_registry_unknown_version_raises():
    SCHEMA_REGISTRY.resolve("dpfc-core", "v1.0")  # known — must not raise
    with pytest.raises(KeyError, match="unknown schema"):
        SCHEMA_REGISTRY.resolve("dpfc-core", "v99.0")


def test_schema_registry_entries_have_required_fields():
    for entry in SCHEMA_REGISTRY.all():
        assert isinstance(entry, SchemaEntry)
        assert entry.schema_id
        assert entry.version.startswith("v")
        assert entry.owner
        assert entry.status in {"active", "deprecated", "retired"}


# ---------------------------------------------------------------------------
# 2. ACTIVE_SCHEMA_VERSIONS resolves in registry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("schema_id,version", list(ACTIVE_SCHEMA_VERSIONS.items()))
def test_active_schema_versions_all_resolve(schema_id: str, version: str):
    entry = SCHEMA_REGISTRY.resolve(schema_id, version)
    assert entry.status == "active", (
        f"{schema_id}@{version} is not active in the registry"
    )


def test_active_schema_versions_dict_is_nonempty():
    assert len(ACTIVE_SCHEMA_VERSIONS) >= 9


# ---------------------------------------------------------------------------
# 3. SUPPORTED_SCHEMA_SNAPSHOTS
# ---------------------------------------------------------------------------


def test_current_fixture_schema_version_is_supported():
    assert CURRENT_FIXTURE_SCHEMA_VERSION in SUPPORTED_SCHEMA_SNAPSHOTS


@pytest.mark.parametrize("snap_version", list(SUPPORTED_SCHEMA_SNAPSHOTS.keys()))
def test_schema_snapshot_has_required_keys(snap_version: str):
    snap = SUPPORTED_SCHEMA_SNAPSHOTS[snap_version]
    for key in ("family_registry_version", "geometry_registry_version", "policy_shield_version"):
        assert key in snap, f"snapshot {snap_version!r} missing key {key!r}"


@pytest.mark.parametrize("snap_version", list(SUPPORTED_SCHEMA_SNAPSHOTS.keys()))
def test_resolve_schema_snapshot_returns_correct_keys(snap_version: str):
    snap = resolve_schema_snapshot(snap_version)
    assert "family_registry_version" in snap
    assert "policy_shield_version" in snap


# ---------------------------------------------------------------------------
# 4. normalize_fixture_schema_version
# ---------------------------------------------------------------------------


def test_normalize_none_returns_current():
    assert normalize_fixture_schema_version(None) == CURRENT_FIXTURE_SCHEMA_VERSION


def test_normalize_with_prefix_strips_prefix():
    result = normalize_fixture_schema_version(f"conformance-fixtures@{CURRENT_FIXTURE_SCHEMA_VERSION}")
    assert result == CURRENT_FIXTURE_SCHEMA_VERSION


def test_normalize_unknown_version_raises():
    with pytest.raises(ValueError, match="unsupported schema version"):
        normalize_fixture_schema_version("v999.0")


def test_normalize_roundtrip_all_snapshots():
    for v in SUPPORTED_SCHEMA_SNAPSHOTS:
        assert normalize_fixture_schema_version(v) == v
        assert normalize_fixture_schema_version(f"conformance-fixtures@{v}") == v


# ---------------------------------------------------------------------------
# 5. fixture_pack_id_for / spec_target_for
# ---------------------------------------------------------------------------


def test_fixture_pack_id_for_default():
    pack = fixture_pack_id_for()
    assert pack.startswith("conformance-fixtures@")
    assert CURRENT_FIXTURE_SCHEMA_VERSION in pack


@pytest.mark.parametrize("snap_version", list(SUPPORTED_SCHEMA_SNAPSHOTS.keys()))
def test_fixture_pack_id_for_all_snapshots(snap_version: str):
    pack = fixture_pack_id_for(snap_version)
    assert pack == f"conformance-fixtures@{snap_version}"


@pytest.mark.parametrize("snap_version", list(SPEC_TARGETS.keys()))
def test_spec_target_for_contains_fixture_pack(snap_version: str):
    target = spec_target_for(snap_version)
    assert "fixture_pack" in target
    assert target["fixture_pack"].startswith("conformance-fixtures@")


# ---------------------------------------------------------------------------
# 6. Runtime schema_version string conventions
# ---------------------------------------------------------------------------


_KNOWN_RUNTIME_SCHEMA_IDS = [
    "rho-memory-step-result@v1",
    "learning-route-result@v1",
    "policy-shield-snapshot@v1",
    "policy-feasibility@v1",
    "policy-trust-region@v1",
    "promotion-budget-validation@v1",
    "approval-validation@v1",
    "meta-object-build-result@v1",
    "meta-object-instance@v1",
    "meta-object-assertion-bundle@v1",
    "meta-summary@v1",
]


@pytest.mark.parametrize("sid", _KNOWN_RUNTIME_SCHEMA_IDS)
def test_runtime_schema_ids_follow_naming_convention(sid: str):
    """schema_version strings must be <name>@v<n>."""
    assert "@v" in sid, f"schema_version {sid!r} missing @v<n> suffix"
    name, version_suffix = sid.rsplit("@", 1)
    assert name, "schema name must not be empty"
    assert version_suffix.startswith("v") and version_suffix[1:].isdigit(), (
        f"version suffix {version_suffix!r} must be vN"
    )


# ---------------------------------------------------------------------------
# 7. WG-RNN replay-identity fixture schema_version
# ---------------------------------------------------------------------------


def test_wgrnn_fixture_file_exists():
    assert _FIXTURE_JSON.is_file(), f"Fixture not found: {_FIXTURE_JSON}"


def test_wgrnn_fixture_schema_version():
    fixture = _load_fixture()
    assert fixture["schema_version"] == "wgrnn-replay-identity-fixture@v1"


def test_wgrnn_fixture_replay_identity_digest_matches_pinned():
    """Regression guard: digest must match what test_replay_identity_fixtures.py pins."""
    fixture = _load_fixture()
    digest = fixture["replay_identity"]["digest"]
    assert digest == "sha256:e8b4a26831ff931cc7ece463d63e421776b7ef101056f07b4ab9bed36ac54fcd"


def test_wgrnn_fixture_forward_pass_record_digest_matches_pinned():
    fixture = _load_fixture()
    det_digest = fixture["forward_pass_record"]["deterministic_digest"]
    assert det_digest == "sha256:e89651dc9375d1c3a5ba6a50dba459804d3d88d5a13d922e5ab95d952ba82d70"


def test_wgrnn_fixture_replay_identity_ref_matches_digest():
    """forward_pass_record.replay_identity_ref must equal replay_identity.digest."""
    fixture = _load_fixture()
    assert (
        fixture["forward_pass_record"]["replay_identity_ref"]
        == fixture["replay_identity"]["digest"]
    )


def test_wgrnn_fixture_required_top_level_keys():
    fixture = _load_fixture()
    for key in ("schema_version", "description", "cell_profile", "witness", "policy",
                "replay_identity", "forward_pass_record"):
        assert key in fixture, f"fixture missing top-level key {key!r}"


def test_wgrnn_fixture_cell_profile_dimensions_consistent():
    profile = _load_fixture()["cell_profile"]
    for dim in ("input_dim", "hidden_dim", "cell_dim", "slot_dim"):
        assert profile[dim] == 4
    assert profile["num_slots"] == 4
