"""Policy registry — surfaces the decision matrix as a queryable table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..policy_shield import DECISION_MATRIX, POLICY_MODES


@dataclass(frozen=True)
class PolicyEntry:
    event: str
    mode: str
    freeze_metrics: bool
    trust_status: str
    escalation_chain: tuple[str, ...]


class PolicyRegistry:
    def __init__(self) -> None:
        self._entries = {
            event: PolicyEntry(
                event=event,
                mode=spec["mode"],
                freeze_metrics=spec["freeze_metrics"],
                trust_status=spec["trust_status"],
                escalation_chain=tuple(spec["escalation_chain"]),
            )
            for event, spec in DECISION_MATRIX.items()
        }

    def resolve(self, event: str) -> PolicyEntry:
        try:
            return self._entries[event]
        except KeyError as exc:
            raise KeyError(f"unknown policy event {event}") from exc

    def modes(self) -> tuple[str, ...]:
        return POLICY_MODES

    def all(self) -> list[PolicyEntry]:
        return list(self._entries.values())


POLICY_REGISTRY = PolicyRegistry()
