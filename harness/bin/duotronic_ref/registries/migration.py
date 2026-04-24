"""Migration registry (Migration Guide §3 + §4).

Every version bump that affects identity must ship with a migration plan
that pins from/to versions, the conversion strategy, and a snapshot of
the replay-identity expectations. Missing or stale plans are detectable
and produce `migration_rejected` audit events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .. import audit


@dataclass(frozen=True)
class MigrationPlan:
    plan_id: str
    from_version: str
    to_version: str
    component: str  # normalizer | family | transport | schema
    strategy: str  # bijective | lossy | rebaseline-required | breaking
    requires_replay_pin_update: bool
    notes: str = ""


class MigrationRegistry:
    def __init__(self, plans: list[MigrationPlan]) -> None:
        self._plans: dict[tuple[str, str, str], MigrationPlan] = {
            (p.component, p.from_version, p.to_version): p for p in plans
        }

    def has_plan(self, *, component: str, from_version: str, to_version: str) -> bool:
        return (component, from_version, to_version) in self._plans

    def resolve(self, *, component: str, from_version: str, to_version: str) -> MigrationPlan:
        key = (component, from_version, to_version)
        if key not in self._plans:
            audit.record(
                audit.EVT_MIGRATION_REJECTED,
                component=component,
                from_version=from_version,
                to_version=to_version,
                reason="missing_migration_plan",
            )
            raise KeyError(
                f"missing migration plan for {component} {from_version}->{to_version}"
            )
        return self._plans[key]

    def register(self, plan: MigrationPlan) -> None:
        self._plans[(plan.component, plan.from_version, plan.to_version)] = plan

    def all(self) -> list[MigrationPlan]:
        return list(self._plans.values())


# Baseline registry: empty for v1 (all entries at v1.0), but available
# for any forward bumps. Negative-injection tests register a v2 entry
# WITHOUT a plan and assert resolve() raises.
MIGRATION_REGISTRY = MigrationRegistry([])
