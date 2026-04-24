"""Schema-version plumbing and spec-target alignment checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from duotronic_ref.policy_shield import SHIELD, reset_shield
from duotronic_ref.replay import ReplayIdentity
from harness_lib import loader
from harness_lib.schema_versions import (
    ACTIVE_SPEC_TARGET,
    CURRENT_FIXTURE_SCHEMA_VERSION,
    fixture_pack_id_for,
    resolve_schema_snapshot,
)


ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.normative
def test_replay_identity_defaults_follow_selected_schema_version(schema_version: str) -> None:
    snapshot = resolve_schema_snapshot(schema_version)
    identity = ReplayIdentity(input_hash="abc", expected_normal_form_hash="def")
    assert identity.family_registry_version == snapshot["family_registry_version"]
    assert identity.geometry_registry_version == snapshot["geometry_registry_version"]
    assert identity.policy_shield_version == snapshot["policy_shield_version"]


@pytest.mark.normative
def test_policy_shield_reset_tracks_selected_schema_version(schema_version: str) -> None:
    snapshot = resolve_schema_snapshot(schema_version)
    reset_shield()
    assert SHIELD.version == snapshot["policy_shield_version"]


@pytest.mark.normative
def test_public_metadata_matches_active_spec_target() -> None:
    assert ACTIVE_SPEC_TARGET["dpfc"] == "dpfc-core@v5.8"
    assert ACTIVE_SPEC_TARGET["witness"] == "witness-contract@v10.8"
    assert ACTIVE_SPEC_TARGET["source_architecture"] == "source-architecture@v1.3"
    assert ACTIVE_SPEC_TARGET["meta_runtime"] == "meta-runtime-contract@v0.2"
    assert fixture_pack_id_for(CURRENT_FIXTURE_SCHEMA_VERSION) == ACTIVE_SPEC_TARGET["fixture_pack"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "DPFC v5.8" in readme
    assert "Witness Contract v10.8" in readme
    assert "conformance-fixtures@v1.2" in readme

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "DPFC v5.8" in pyproject
    assert "Witness Contract v10.8" in pyproject


@pytest.mark.normative
def test_fixture_manifest_matches_loader_selection(
    schema_version: str,
    target_schema_version: str | None,
) -> None:
    expected_sources = {path.name for path in (ROOT / "fixtures").glob("*.yaml")}
    observed_packs = loader.discover_packs(
        schema_version=schema_version,
        target_schema_version=target_schema_version,
    )
    observed_sources = {pack.source.name for pack in observed_packs if pack.source is not None}
    assert observed_sources == expected_sources
    assert observed_packs
    for pack in observed_packs:
        assert pack.schema_version == schema_version
        assert pack.target_schema_version == (target_schema_version or schema_version)


@pytest.mark.normative
def test_meta_fixture_packs_declare_explicit_schema_metadata(
    schema_version: str,
    target_schema_version: str | None,
) -> None:
    expected_sources = {path.name for path in (ROOT / "meta_fixtures").glob("*.yaml")}
    observed_packs = loader.discover_packs(
        ROOT / "meta_fixtures",
        schema_version=schema_version,
        target_schema_version=target_schema_version,
    )
    observed_sources = {pack.source.name for pack in observed_packs if pack.source is not None}
    assert observed_sources == expected_sources
    assert observed_packs
    for pack in observed_packs:
        assert pack.schema_version == schema_version
        assert pack.target_schema_version == (target_schema_version or schema_version)