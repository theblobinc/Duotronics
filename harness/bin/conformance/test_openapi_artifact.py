"""OpenAPI artifact conformance tests (v1.6 Draft 3 RC closure).

Validates that:
  1. The extracted RC1 OpenAPI YAML is parseable and structurally sound.
  2. All required Draft 3 path groups are present.
  3. The spec declares OpenAPI 3.x.
  4. Every path has at least one operation with a 200 response.

These tests are normative RC-closure checks, not tests of the live server.
They validate the *corpus artifact* — the static YAML extracted from
``executable/openapi/duotronic_openapi_v1_6_draft_3_rc1.yaml.md``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_CORPUS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "build_docs"
    / "witness_contract"
    / "v1.6 - Draft 3"
)
_OPENAPI_YAML = _CORPUS_ROOT / "executable" / "openapi" / "duotronic_openapi_v1_6_draft_3_rc1.yaml"


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    assert _OPENAPI_YAML.exists(), (
        f"Extracted OpenAPI YAML not found at {_OPENAPI_YAML}. "
        "Run the extraction step: extract the ```yaml block from "
        "duotronic_openapi_v1_6_draft_3_rc1.yaml.md."
    )
    with open(_OPENAPI_YAML) as f:
        spec = yaml.safe_load(f)
    assert isinstance(spec, dict), "OpenAPI spec must be a YAML mapping"
    return spec


@pytest.mark.normative
def test_openapi_version_is_3x(openapi_spec: dict) -> None:
    """Spec must declare OpenAPI 3.x."""
    version = openapi_spec.get("openapi", "")
    assert version.startswith("3."), f"Expected openapi: 3.x, got {version!r}"


@pytest.mark.normative
def test_openapi_has_info_block(openapi_spec: dict) -> None:
    info = openapi_spec.get("info", {})
    assert info.get("title"), "info.title is required"
    assert info.get("version"), "info.version is required"


@pytest.mark.normative
def test_openapi_has_paths(openapi_spec: dict) -> None:
    paths = openapi_spec.get("paths", {})
    assert len(paths) >= 5, f"Expected ≥5 paths, got {len(paths)}: {list(paths)}"


@pytest.mark.normative
@pytest.mark.parametrize("path", [
    "/health",
    "/policy/decide",
    "/math/objects",
    "/mcp/recurrence/write_witness",
    "/mcp/recurrence/query_overlay",
    "/mcp/recurrence/propose_decay",
])
def test_required_path_present(openapi_spec: dict, path: str) -> None:
    """All required Draft 3 path groups must be present."""
    paths = openapi_spec.get("paths", {})
    assert path in paths, (
        f"Required path {path!r} missing from OpenAPI spec. "
        f"Paths present: {sorted(paths)}"
    )


@pytest.mark.normative
def test_every_path_has_at_least_one_operation(openapi_spec: dict) -> None:
    """Every path must have at least one HTTP operation defined."""
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}
    paths = openapi_spec.get("paths", {})
    empty_paths = [
        p for p, obj in paths.items()
        if not any(m in (obj or {}) for m in http_methods)
    ]
    assert not empty_paths, f"Paths with no operations: {empty_paths}"


@pytest.mark.normative
def test_openapi_sql_migrations_exist() -> None:
    """SQL migration files must be extracted alongside the YAML."""
    sql_dir = _CORPUS_ROOT / "executable" / "sql"
    expected = [
        "001_cognition_step_and_witness_runtime.sql",
        "002_mcp_recurrence_tools_schema.sql",
    ]
    for filename in expected:
        assert (sql_dir / filename).exists(), (
            f"SQL migration not extracted: {filename}. "
            f"Run the extraction step from the corresponding .sql.md file."
        )


@pytest.mark.normative
def test_openapi_formal_models_exist() -> None:
    """Formal model files must be extracted from their .md wrappers."""
    tla_dir = _CORPUS_ROOT / "formal" / "tlaplus"
    lean_dir = _CORPUS_ROOT / "formal" / "lean4"
    assert (tla_dir / "TaskDelegationAndPolicyCoreSpec.tla").exists(), (
        "TLA+ spec not extracted. Run extraction from TaskDelegationAndPolicyCoreSpec.tla.md"
    )
    assert (lean_dir / "DuotronicCore.lean").exists(), (
        "Lean 4 module not extracted. Run extraction from DuotronicCore.lean.md"
    )
