"""Root pytest configuration for the Duotronic harness."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from duotronic_ref import audit, policy_shield, retention
from duotronic_ref.registries.migration import MIGRATION_REGISTRY
from harness_lib import loader, schema_versions
from harness_lib.dispatch import get_run_meta_operation, get_run_operation


ROOT = Path(__file__).resolve().parent
META_FIXTURES_DIR = ROOT / "meta_fixtures"
GOLDEN_TRACES_DIR = ROOT / "golden_traces"
META_GOLDEN_TRACES_DIR = ROOT / "meta_golden_traces"
REPORT_PATH = Path(os.environ.get("DUOTRONIC_REPORT_PATH", str(ROOT / "conformance_report.json")))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--impl",
        action="store",
        default=None,
        help="Python module path of the implementation under test (overrides DUOTRONIC_IMPL).",
    )
    parser.addoption(
        "--schema-version",
        action="store",
        default=schema_versions.CURRENT_FIXTURE_SCHEMA_VERSION,
        help=(
            "Active fixture-pack schema version / registry snapshot "
            f"(default {schema_versions.CURRENT_FIXTURE_SCHEMA_VERSION})."
        ),
    )
    parser.addoption(
        "--target-schema-version",
        action="store",
        default=None,
        help=(
            "Optional target schema version for migration/replay runs. "
            "When omitted, the active schema version is also the target."
        ),
    )
    parser.addoption(
        "--meta-impl",
        action="store",
        default=None,
        help="Python module path of the meta runtime under test (overrides DUOTRONIC_META_IMPL).",
    )


def _selected_schema_version(config: pytest.Config) -> str:
    return schema_versions.normalize_fixture_schema_version(config.getoption("--schema-version"))


def _selected_target_schema_version(config: pytest.Config) -> str | None:
    raw = config.getoption("--target-schema-version")
    if raw in (None, ""):
        return None
    return schema_versions.normalize_fixture_schema_version(raw)


def _selected_target_schema_version_or_current(config: pytest.Config) -> str:
    return _selected_target_schema_version(config) or _selected_schema_version(config)


def _discover_fixture_packs(config: pytest.Config, directory: Path | None = None) -> list[loader.Pack]:
    return loader.discover_packs(
        directory,
        schema_version=_selected_schema_version(config),
        target_schema_version=_selected_target_schema_version(config),
    )


def _parametrize_cases(
    packs: list[loader.Pack],
    *,
    include_meta_runtime: bool,
) -> list[Any]:
    items: list[Any] = []
    for pack in packs:
        for fixture_case in pack.cases:
            marks = [getattr(pytest.mark, marker) for marker in fixture_case.all_markers]
            if include_meta_runtime:
                marks = [pytest.mark.meta_runtime, *marks]
            items.append(
                pytest.param(
                    fixture_case,
                    marks=marks,
                    id=f"{pack.pack_id}/{fixture_case.case_id}",
                )
            )
    return items


def _pack_domain(pack: loader.Pack, directory: Path) -> str:
    if directory == META_FIXTURES_DIR or pack.pack_id.startswith("meta-"):
        return "meta-runtime"
    pack_id = pack.pack_id.lower()
    if "dpfc" in pack_id:
        return "dpfc-core"
    if "witness" in pack_id:
        return "witness-runtime"
    if "transport" in pack_id or "dbp" in pack_id or "wsb2" in pack_id:
        return "transport"
    if "policy" in pack_id:
        return "policy"
    if "migration" in pack_id or "replay" in pack_id:
        return "migration-replay"
    if "retention" in pack_id:
        return "retention"
    if "normalizer" in pack_id:
        return "normalizer"
    if "family" in pack_id:
        return "family-registry"
    if "schema" in pack_id:
        return "schema-registry"
    if "spectral" in pack_id:
        return "spectral"
    return "other"


def _coverage_matrix(config: pytest.Config) -> dict[str, Any]:
    matrix: dict[str, dict[str, Any]] = {}
    for directory in (loader.FIXTURES_DIR, META_FIXTURES_DIR):
        for pack in _discover_fixture_packs(config, directory):
            domain = _pack_domain(pack, directory)
            entry = matrix.setdefault(domain, {"pack_count": 0, "case_count": 0, "markers": Counter()})
            entry["pack_count"] += 1
            entry["case_count"] += len(pack.cases)
            if directory == META_FIXTURES_DIR:
                entry["markers"]["meta_runtime"] += len(pack.cases)
            for fixture_case in pack.cases:
                for marker in fixture_case.all_markers:
                    entry["markers"][marker] += 1
    serializable: dict[str, Any] = {}
    for domain, payload in sorted(matrix.items()):
        serializable[domain] = {
            "pack_count": payload["pack_count"],
            "case_count": payload["case_count"],
            "markers": dict(sorted(payload["markers"].items())),
        }
    return serializable


def _artifact_counts() -> dict[str, int]:
    return {
        "fixture_packs": len(list(loader.FIXTURES_DIR.glob("*.yaml"))),
        "golden_traces": len(list(GOLDEN_TRACES_DIR.glob("*.yaml"))),
        "meta_fixture_packs": len(list(META_FIXTURES_DIR.glob("*.yaml"))),
        "meta_golden_traces": len(list(META_GOLDEN_TRACES_DIR.glob("*.yaml"))),
    }


@pytest.fixture(scope="session")
def impl_name(request: pytest.FixtureRequest) -> str | None:
    cli = request.config.getoption("--impl")
    if cli:
        os.environ["DUOTRONIC_IMPL"] = cli
        return cli
    return os.environ.get("DUOTRONIC_IMPL")


@pytest.fixture(scope="session")
def meta_impl_name(request: pytest.FixtureRequest) -> str | None:
    cli = request.config.getoption("--meta-impl")
    if cli:
        os.environ["DUOTRONIC_META_IMPL"] = cli
        return cli
    return os.environ.get("DUOTRONIC_META_IMPL")


@pytest.fixture(scope="session")
def schema_version(request: pytest.FixtureRequest) -> str:
    return _selected_schema_version(request.config)


@pytest.fixture(scope="session")
def target_schema_version(request: pytest.FixtureRequest) -> str | None:
    return _selected_target_schema_version(request.config)


@pytest.fixture(scope="session", autouse=True)
def _schema_version_environment(
    schema_version: str,
    target_schema_version: str | None,
) -> Any:
    old_schema = os.environ.get("DUOTRONIC_SCHEMA_VERSION")
    old_target = os.environ.get("DUOTRONIC_TARGET_SCHEMA_VERSION")
    os.environ["DUOTRONIC_SCHEMA_VERSION"] = schema_version
    os.environ["DUOTRONIC_TARGET_SCHEMA_VERSION"] = target_schema_version or schema_version
    yield
    if old_schema is None:
        os.environ.pop("DUOTRONIC_SCHEMA_VERSION", None)
    else:
        os.environ["DUOTRONIC_SCHEMA_VERSION"] = old_schema
    if old_target is None:
        os.environ.pop("DUOTRONIC_TARGET_SCHEMA_VERSION", None)
    else:
        os.environ["DUOTRONIC_TARGET_SCHEMA_VERSION"] = old_target


@pytest.fixture(scope="session")
def run_operation(impl_name: str | None) -> Any:
    return get_run_operation(impl_name)


@pytest.fixture(scope="session")
def run_meta_operation(meta_impl_name: str | None) -> Any:
    return get_run_meta_operation(meta_impl_name)


@pytest.fixture(autouse=True)
def _reset_state() -> Any:
    """Reset audit ledger, policy shield, and retention ledger before each test
    so cross-test interactions cannot mask regressions."""
    audit.LEDGER.clear()
    policy_shield.reset_shield()
    retention.LEDGER.baselines.clear()
    retention.seed_default_baselines()
    MIGRATION_REGISTRY._plans.clear()  # noqa: SLF001
    yield


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "case" in metafunc.fixturenames:
        packs = _discover_fixture_packs(metafunc.config)
        params = _parametrize_cases(packs, include_meta_runtime=False)
        if not params:
            raise pytest.UsageError(
                "no fixture packs matched "
                f"--schema-version={_selected_schema_version(metafunc.config)}"
            )
        metafunc.parametrize("case", params)
    if "meta_case" in metafunc.fixturenames:
        packs = _discover_fixture_packs(metafunc.config, META_FIXTURES_DIR)
        params = _parametrize_cases(packs, include_meta_runtime=True)
        if not params:
            raise pytest.UsageError(
                "no meta fixture packs matched "
                f"--schema-version={_selected_schema_version(metafunc.config)}"
            )
        metafunc.parametrize("meta_case", params)


def pytest_report_header(config: pytest.Config) -> list[str]:
    schema_version = _selected_schema_version(config)
    target_schema_version = _selected_target_schema_version_or_current(config)
    return [
        (
            "spec target: "
            f"{schema_versions.ACTIVE_SPEC_TARGET['dpfc']} | "
            f"{schema_versions.ACTIVE_SPEC_TARGET['witness']} | "
            f"{schema_versions.ACTIVE_SPEC_TARGET['source_architecture']} | "
            f"{schema_versions.ACTIVE_SPEC_TARGET['fixture_pack']} | "
            f"{schema_versions.ACTIVE_SPEC_TARGET['meta_runtime']}"
        ),
        (
            "schema selection: "
            f"source={schema_version} ({schema_versions.resolve_schema_snapshot(schema_version)['family_registry_version']}) "
            f"target={target_schema_version}"
        ),
        (
            "impls: "
            f"duotronic={config.getoption('--impl') or os.environ.get('DUOTRONIC_IMPL', 'duotronic_ref.api')} | "
            f"meta={config.getoption('--meta-impl') or os.environ.get('DUOTRONIC_META_IMPL', 'runtime_ref.api')}"
        ),
        f"report: {REPORT_PATH.name}",
    ]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    pass


def pytest_terminal_summary(
    terminalreporter: Any,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    summary_keys = (
        "passed",
        "failed",
        "error",
        "skipped",
        "xfailed",
        "xpassed",
        "deselected",
        "warnings",
    )
    summary = {
        key: len(terminalreporter.stats.get(key, []))
        for key in summary_keys
        if terminalreporter.stats.get(key)
    }
    report = {
        "report_schema": "conformance-report@v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "exitstatus": exitstatus,
        "selection": {
            "schema_version": _selected_schema_version(config),
            "target_schema_version": _selected_target_schema_version_or_current(config),
            "impl": config.getoption("--impl") or os.environ.get("DUOTRONIC_IMPL", "duotronic_ref.api"),
            "meta_impl": config.getoption("--meta-impl") or os.environ.get("DUOTRONIC_META_IMPL", "runtime_ref.api"),
        },
        "spec_target": dict(schema_versions.ACTIVE_SPEC_TARGET),
        "artifact_counts": _artifact_counts(),
        "coverage_matrix": _coverage_matrix(config),
        "summary": summary,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")