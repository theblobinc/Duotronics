"""Policy-driver fault injection.

The driver lets a test inject one of the documented Policy Shield
events into the dispatch path and verify the shield routes correctly.
This is mostly a thin wrapper around `policy_shield.SHIELD.decide` so
test authors can express fault scenarios as data, not code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from duotronic_ref import policy_shield


@dataclass
class FaultInjection:
    event: str
    context: dict[str, Any]
    expect_mode: str
    expect_freeze_metrics: bool
    expect_trust_status: str


def apply_injection(injection: FaultInjection) -> dict[str, Any]:
    decision = policy_shield.SHIELD.decide(event=injection.event, context=injection.context)
    failures: list[str] = []
    if decision["mode"] != injection.expect_mode:
        failures.append(f"mode: expected {injection.expect_mode} got {decision['mode']}")
    if decision["freeze_metrics"] != injection.expect_freeze_metrics:
        failures.append(
            f"freeze_metrics: expected {injection.expect_freeze_metrics} got {decision['freeze_metrics']}"
        )
    if decision["trust_status"] != injection.expect_trust_status:
        failures.append(
            f"trust_status: expected {injection.expect_trust_status} got {decision['trust_status']}"
        )
    decision["injection_failures"] = failures
    return decision
