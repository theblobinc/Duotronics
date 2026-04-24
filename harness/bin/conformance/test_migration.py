"""Migration property tests — registry must reject identity-affecting bumps
that arrive without a registered plan."""

from __future__ import annotations

from typing import Any

import pytest

from duotronic_ref import audit
from duotronic_ref.registries.migration import MIGRATION_REGISTRY, MigrationPlan


@pytest.mark.migration
def test_unregistered_bump_is_rejected(run_operation: Any) -> None:
    out = run_operation(
        "migration_resolve_plan",
        {
            "component": "normalizer",
            "from_version": "simple-bijective-word-normalizer@v1",
            "to_version": "simple-bijective-word-normalizer@v2",
        },
    )
    assert out["resolved"] is False
    assert out["failure_code"] == "missing_migration_plan"
    assert audit.LEDGER.events("migration_rejected"), (
        "missing migration plan must record a `migration_rejected` audit event"
    )


@pytest.mark.migration
def test_registered_bump_resolves(run_operation: Any) -> None:
    run_operation(
        "register_migration_plan",
        {
            "plan_id": "plan.normalizer.v1_to_v2.bijective",
            "component": "normalizer",
            "from_version": "simple-bijective-word-normalizer@v1",
            "to_version": "simple-bijective-word-normalizer@v2",
            "strategy": "bijective",
        },
    )
    out = run_operation(
        "migration_resolve_plan",
        {
            "component": "normalizer",
            "from_version": "simple-bijective-word-normalizer@v1",
            "to_version": "simple-bijective-word-normalizer@v2",
        },
    )
    assert out["resolved"] is True
    assert out["plan_id"] == "plan.normalizer.v1_to_v2.bijective"
    # cleanup so the unregistered-bump test stays correct under any test order
    MIGRATION_REGISTRY._plans.pop(  # noqa: SLF001
        ("normalizer", "simple-bijective-word-normalizer@v1", "simple-bijective-word-normalizer@v2"),
        None,
    )
