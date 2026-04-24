"""Retention metrics (Witness Contract App R + Retention Strategy doc §6).

Each metric has a frozen baseline. New samples may only be added when
policy is `normal`; degraded/bypass modes freeze the baseline. Lack of
baseline produces a `retention_baseline_unfrozen` audit event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import audit


@dataclass(frozen=True)
class RetentionMetricSpec:
    metric_id: str
    version: str
    description: str
    baseline_required: bool
    frozen_on_bypass: bool


# Baselines are the verbatim metric set required by Retention §6.
RETENTION_METRICS: dict[str, RetentionMetricSpec] = {
    m.metric_id: m
    for m in (
        RetentionMetricSpec(
            metric_id="shuffled_lookup_retention",
            version="v1.0",
            description=(
                "Fraction of canonicalised lookups that survive a deterministic "
                "shuffle of the input lane order without changing the canonical key."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
        RetentionMetricSpec(
            metric_id="malformed_frame_retention",
            version="v1.0",
            description=(
                "Fraction of malformed frames that are correctly rejected at the "
                "transport boundary without producing trusted memory."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
        RetentionMetricSpec(
            metric_id="schema_mismatch_retention",
            version="v1.0",
            description=(
                "Fraction of schema-mismatch events that route to family_bypass "
                "with a recoverable migration plan."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
        RetentionMetricSpec(
            metric_id="transpose_interval_retention",
            version="v1.0",
            description=(
                "Fraction of canonical interval patterns preserved after "
                "transposition modulo EDO size (Witness App K.12)."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
        RetentionMetricSpec(
            metric_id="enharmonic_retention",
            version="v1.0",
            description=(
                "Fraction of enharmonic pairs whose canonical key is preserved "
                "under the documented collapse policy."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
        RetentionMetricSpec(
            metric_id="absence_zero_separation_retention",
            version="v1.0",
            description=(
                "Fraction of token-free-absent rows that remain disambiguated "
                "from numeric-zero presence at the lookup boundary."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
        RetentionMetricSpec(
            metric_id="replay_identity_retention",
            version="v1.0",
            description=(
                "Fraction of pinned replay identities that re-execute to the "
                "same expected_normal_form_hash."
            ),
            baseline_required=True,
            frozen_on_bypass=True,
        ),
    )
}


@dataclass
class RetentionLedger:
    baselines: dict[str, dict[str, Any]] = field(default_factory=dict)

    def freeze_baseline(self, metric_id: str, *, value: float, sample_count: int, profile: str) -> None:
        if metric_id not in RETENTION_METRICS:
            raise KeyError(f"unknown retention metric: {metric_id}")
        self.baselines[metric_id] = {
            "value": value,
            "sample_count": sample_count,
            "profile": profile,
            "frozen": True,
        }

    def get_baseline(self, metric_id: str) -> dict[str, Any] | None:
        return self.baselines.get(metric_id)

    def record_sample(self, *, metric_id: str, value: float, policy_mode: str) -> dict[str, Any]:
        spec = RETENTION_METRICS.get(metric_id)
        if spec is None:
            raise KeyError(f"unknown retention metric: {metric_id}")
        baseline = self.baselines.get(metric_id)
        if baseline is None and spec.baseline_required:
            audit.record(audit.EVT_RETENTION_NO_BASELINE, metric_id=metric_id)
            return {
                "accepted": False,
                "reason": "retention_baseline_unfrozen",
                "metric_id": metric_id,
            }
        if policy_mode != "normal" and spec.frozen_on_bypass:
            return {
                "accepted": False,
                "reason": "frozen_on_bypass",
                "metric_id": metric_id,
                "policy_mode": policy_mode,
            }
        return {"accepted": True, "metric_id": metric_id, "value": value}


LEDGER = RetentionLedger()


def seed_default_baselines() -> None:
    """Seed default-profile baselines so the harness has a known anchor."""
    for metric_id in RETENTION_METRICS:
        LEDGER.freeze_baseline(
            metric_id,
            value=1.0,
            sample_count=1024,
            profile="reference-default",
        )


def run_reference_self_test() -> None:
    LEDGER.baselines.clear()
    res = LEDGER.record_sample(
        metric_id="shuffled_lookup_retention",
        value=0.99,
        policy_mode="normal",
    )
    assert res["accepted"] is False, "must reject without baseline"
    assert res["reason"] == "retention_baseline_unfrozen"
    seed_default_baselines()
    res2 = LEDGER.record_sample(
        metric_id="shuffled_lookup_retention",
        value=0.99,
        policy_mode="normal",
    )
    assert res2["accepted"] is True
    res3 = LEDGER.record_sample(
        metric_id="shuffled_lookup_retention",
        value=0.99,
        policy_mode="lookup_bypass",
    )
    assert res3["accepted"] is False
    assert res3["reason"] == "frozen_on_bypass"


if __name__ == "__main__":  # pragma: no cover
    run_reference_self_test()
    print("Retention reference self-test passed")
