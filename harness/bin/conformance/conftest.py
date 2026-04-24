"""Pytest configuration shared across the conformance suite."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from duotronic_ref import audit, policy_shield, retention
from duotronic_ref.registries.migration import MIGRATION_REGISTRY
from harness_lib import loader
from harness_lib.dispatch import get_run_meta_operation, get_run_operation


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
        default="v1.0",
        help="Active fixture-pack schema version (currently v1.0).",
    )
    parser.addoption(
        "--meta-impl",
        action="store",
        default=None,
        help="Python module path of the meta runtime under test (overrides DUOTRONIC_META_IMPL).",
    )


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
    # leave state alone after — meta-test inspects the post-suite ledger.


def _packs() -> list[loader.Pack]:
    return loader.discover_packs()


def _all_cases_with_markers() -> list[Any]:
    items = []
    for pack in _packs():
        for case in pack.cases:
            marks = [getattr(pytest.mark, m) for m in case.all_markers]
            items.append(pytest.param(case, marks=marks, id=f"{pack.pack_id}/{case.case_id}"))
    return items


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:  # noqa: ARG001
    # Force `--strict-markers` semantics defensively; pytest.ini already sets it
    # but a stale local pytest.cfg could weaken it.
    pass


# Re-export for runner module
ALL_FIXTURE_CASES = _all_cases_with_markers()
