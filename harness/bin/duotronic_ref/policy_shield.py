"""Policy Shield (Witness Contract App L) — L5 5-state machine.

States: normal | degraded | family_bypass | transport_bypass |
        lookup_bypass | full_bypass

The shield routes incoming events through a deterministic decision matrix
and returns a `policy_decision` that downstream stages must respect. All
transitions to non-`normal` modes are recorded into the audit ledger as
`policy_bypass_transition` events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import audit


POLICY_MODES = (
    "normal",
    "degraded",
    "family_bypass",
    "transport_bypass",
    "lookup_bypass",
    "full_bypass",
)

# Decision matrix from Witness App L §4. Maps an upstream failure code or
# event class to the policy mode that the shield must enter for the
# affected request. `escalation_chain` lists the strict mode escalation
# path; `freeze_metrics` is True iff the mode forces retention metrics to
# be frozen at the prior baseline (no new sampling allowed).
DECISION_MATRIX: dict[str, dict[str, Any]] = {
    "transport_rejected": {
        "mode": "transport_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("transport_bypass", "full_bypass"),
        "trust_status": "untrusted_until_replay",
    },
    "schema_mismatch": {
        "mode": "family_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("family_bypass", "lookup_bypass", "full_bypass"),
        "trust_status": "needs_migration_or_bypass",
    },
    "family_bypass_required": {
        "mode": "family_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("family_bypass", "lookup_bypass", "full_bypass"),
        "trust_status": "needs_migration_or_bypass",
    },
    "malformed_reject": {
        "mode": "transport_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("transport_bypass", "full_bypass"),
        "trust_status": "rejected",
    },
    "absence_zero_collision_attempt": {
        "mode": "lookup_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("lookup_bypass", "full_bypass"),
        "trust_status": "untrusted",
    },
    "normalizer_failure": {
        "mode": "lookup_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("lookup_bypass", "full_bypass"),
        "trust_status": "untrusted",
    },
    "retention_baseline_unfrozen": {
        "mode": "degraded",
        "freeze_metrics": True,
        "escalation_chain": ("degraded", "full_bypass"),
        "trust_status": "degraded",
    },
    "policy_breach": {
        "mode": "full_bypass",
        "freeze_metrics": True,
        "escalation_chain": ("full_bypass",),
        "trust_status": "rejected",
    },
}


@dataclass
class PolicyShield:
    """Shield instance. The default mode is `normal` and the shield
    transitions per-request only; persistent escalation is the caller's
    responsibility (the shield records every transition to the ledger)."""

    version: str = "policy-shield@v1.0"
    state: str = "normal"
    last_decisions: list[dict[str, Any]] = field(default_factory=list)

    def decide(self, *, event: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if event not in DECISION_MATRIX and event != "ok":
            decision = {
                "policy_decision": "rejected",
                "mode": "full_bypass",
                "trust_status": "rejected",
                "freeze_metrics": True,
                "reason": f"unknown_event:{event}",
            }
            audit.record(
                audit.EVT_BYPASS_TRANSITION,
                from_state=self.state,
                to_state="full_bypass",
                event=event,
            )
            self.state = "full_bypass"
            self.last_decisions.append(decision)
            return decision

        if event == "ok":
            decision = {
                "policy_decision": "accept",
                "mode": "normal",
                "trust_status": "trusted",
                "freeze_metrics": False,
            }
            self.last_decisions.append(decision)
            return decision

        spec = DECISION_MATRIX[event]
        new_state = spec["mode"]
        if new_state != self.state:
            audit.record(
                audit.EVT_BYPASS_TRANSITION,
                from_state=self.state,
                to_state=new_state,
                event=event,
                context=context or {},
            )
        self.state = new_state
        decision = {
            "policy_decision": "bypass" if new_state != "normal" else "accept",
            "mode": new_state,
            "trust_status": spec["trust_status"],
            "freeze_metrics": spec["freeze_metrics"],
            "escalation_chain": list(spec["escalation_chain"]),
            "reason": event,
        }
        self.last_decisions.append(decision)
        return decision


SHIELD = PolicyShield()


def reset_shield() -> None:
    SHIELD.state = "normal"
    SHIELD.last_decisions.clear()


def run_reference_self_test() -> None:
    reset_shield()
    d = SHIELD.decide(event="schema_mismatch")
    assert d["mode"] == "family_bypass"
    assert d["freeze_metrics"] is True
    d2 = SHIELD.decide(event="absence_zero_collision_attempt")
    assert d2["mode"] == "lookup_bypass"
    d3 = SHIELD.decide(event="ok")
    assert d3["mode"] == "normal"
    reset_shield()


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("Policy shield reference self-test passed")
