from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def classify_risk(proposal: dict, approval_policy: dict) -> RiskTier:
    risk_tiers = approval_policy.get("risk_tiers", {})
    low_cfg = risk_tiers.get("low", {})
    medium_cfg = risk_tiers.get("medium", {})

    requires_migration = proposal.get("requires_schema_migration", False)
    memory_delta = abs(float(proposal.get("memory_mb_delta", 0)))
    adapter_delta = abs(float(proposal.get("adapter_rank_delta", 0)))
    has_shape_change = proposal.get("has_shape_change", False)
    has_semantic_change = proposal.get("has_semantic_family_change", False)
    has_trust_override = proposal.get("trust_region_override", False)
    degraded_coverage = proposal.get("degraded_coverage_review", False)

    if any(
        [
            requires_migration,
            has_shape_change,
            has_semantic_change,
            has_trust_override,
            degraded_coverage,
            memory_delta >= medium_cfg.get("max_memory_mb_delta", 25),
        ]
    ):
        return RiskTier.HIGH

    if any(
        [
            proposal.get("type") in {"prune_family", "enable_family", "disable_family"},
            adapter_delta > low_cfg.get("max_adapter_rank_delta", 2),
            memory_delta >= low_cfg.get("max_memory_mb_delta", 5),
        ]
    ):
        return RiskTier.MEDIUM

    return RiskTier.LOW


@dataclass
class PolicyShieldSnapshot:
    schema_version: str = "policy-shield-snapshot@v1"
    primary_objective: str = "meta_runtime_stability"
    objective_version: str = "meta_runtime_stability@v1"
    objective_hash: str = "sha256:meta-objective"
    reducer_version: str = "meta-reducer@v1"
    metric_bundle_hash: str = "sha256:meta-metrics"
    hard_constraints: dict = field(
        default_factory=lambda: {
            "max_families": 20,
            "max_memory_mb": 512,
            "max_step_time_ms": 50,
            "state_schema_compatibility": True,
        }
    )
    invariant_set: list[str] = field(
        default_factory=lambda: [
            "no_silent_coercion",
            "family_mass_bounded",
            "step_count_monotonic",
        ]
    )
    approval_policy: dict = field(
        default_factory=lambda: {
            "l3_auto_apply": True,
            "medium_risk_auto_approve": False,
            "high_risk_requires_operator_approval": True,
            "risk_tiers": {
                "low": {"max_adapter_rank_delta": 2, "max_memory_mb_delta": 5},
                "medium": {"max_adapter_rank_delta": 8, "max_memory_mb_delta": 25},
                "high": {"requires_human": True},
            },
        }
    )
    trust_region_policy: dict = field(
        default_factory=lambda: {
            "max_l3_log_decay_step": 0.03,
            "max_l3_callback_logit_step": 0.15,
            "family_overrides": {"low_evidence": {"max_l3_log_decay_step": 0.05}},
        }
    )
    promotion_budget_policy: dict = field(
        default_factory=lambda: {
            "base_budget": 1,
            "max_budget": 3,
            "positive_windows_required": 2,
            "delta_health": 0.02,
            "rollback_rate_ceiling": 0.05,
        }
    )
    shadow_replay_policy: dict = field(
        default_factory=lambda: {
            "min_sequences": 32,
            "min_steps": 2048,
            "recent_fraction": 0.50,
            "balanced_fraction": 0.30,
            "stress_fraction": 0.10,
        }
    )
    violation_policy: dict = field(
        default_factory=lambda: {
            "on_hard_violation": "rollback_and_freeze_l4",
            "on_repeated_l3_rejection": "decay_to_base",
        }
    )

    @property
    def objective_bundle_hash(self) -> str:
        payload = json.dumps(
            [
                self.primary_objective,
                self.objective_version,
                self.objective_hash,
                self.reducer_version,
                self.metric_bundle_hash,
            ],
            sort_keys=True,
        )
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:16]

    def check_hard_constraints(self, state: dict) -> list[str]:
        violations: list[str] = []
        active_families = int(state.get("active_family_count", 0))
        if active_families > self.hard_constraints.get("max_families", 20):
            violations.append(f"active_family_count>{self.hard_constraints['max_families']}")

        memory_mb = float(state.get("memory_mb", 0))
        if memory_mb > self.hard_constraints.get("max_memory_mb", 512):
            violations.append(f"memory_mb>{self.hard_constraints['max_memory_mb']}")

        step_time_ms = float(state.get("step_time_ms", 0))
        if step_time_ms > self.hard_constraints.get("max_step_time_ms", 50):
            violations.append(f"step_time_ms>{self.hard_constraints['max_step_time_ms']}")

        if self.hard_constraints.get("state_schema_compatibility") and state.get("schema_incompatible"):
            violations.append("state_schema_compatibility")
        return violations

    def check_invariants(self, state: dict) -> list[str]:
        violations: list[str] = []
        if "no_silent_coercion" in self.invariant_set and state.get("silent_coercion_detected"):
            violations.append("no_silent_coercion")
        if "family_mass_bounded" in self.invariant_set:
            for family, mass in state.get("family_masses", {}).items():
                if float(mass) < 0 or float(mass) > 1e6:
                    violations.append(f"family_mass_bounded:{family}")
        if "step_count_monotonic" in self.invariant_set and state.get("step_count_decreased"):
            violations.append("step_count_monotonic")
        return violations

    def check_feasibility(self, state: dict) -> dict:
        violations = self.check_hard_constraints(state) + self.check_invariants(state)
        return {
            "schema_version": "policy-feasibility@v1",
            "feasible": not violations,
            "violations": violations,
        }

    def validate_l3_trust_region(self, family: str, log_decay_delta: float, callback_logit_delta: float) -> dict:
        overrides = self.trust_region_policy.get("family_overrides", {}).get(family, {})
        max_log = overrides.get("max_l3_log_decay_step", self.trust_region_policy.get("max_l3_log_decay_step", 0.03))
        max_callback = self.trust_region_policy.get("max_l3_callback_logit_step", 0.15)
        clamped_log = max(-max_log, min(log_decay_delta, max_log))
        clamped_callback = max(-max_callback, min(callback_logit_delta, max_callback))
        return {
            "schema_version": "policy-trust-region@v1",
            "within": abs(log_decay_delta) <= max_log + 1e-9 and abs(callback_logit_delta) <= max_callback + 1e-9,
            "clamped_log_decay": clamped_log,
            "clamped_callback_logit": clamped_callback,
        }

    def validate_promotion_budget(self, current_budget: int) -> dict:
        base_budget = int(self.promotion_budget_policy.get("base_budget", 1))
        max_budget = int(self.promotion_budget_policy.get("max_budget", 3))
        clamped = max(base_budget, min(current_budget, max_budget))
        return {
            "schema_version": "promotion-budget-validation@v1",
            "valid": base_budget <= current_budget <= max_budget,
            "clamped": clamped,
            "base": base_budget,
            "max": max_budget,
        }

    def requires_operator_approval(self, proposal: dict) -> bool:
        risk_tier = classify_risk(proposal, self.approval_policy)
        if risk_tier is RiskTier.HIGH:
            return self.approval_policy.get("high_risk_requires_operator_approval", True)
        if risk_tier is RiskTier.MEDIUM:
            return not self.approval_policy.get("medium_risk_auto_approve", False)
        return False

    def validate_approval(self, approval: dict, proposal_hash: str, objective_bundle_hash: str) -> dict:
        reasons: list[str] = []
        if approval.get("proposal_hash") != proposal_hash:
            reasons.append("proposal_hash_mismatch")
        if approval.get("objective_bundle_hash") != objective_bundle_hash:
            reasons.append("objective_bundle_hash_mismatch")
        if approval.get("decision") not in {"approved", "approved_with_conditions"}:
            reasons.append("decision_not_approved")
        return {
            "schema_version": "approval-validation@v1",
            "valid": not reasons,
            "reasons": reasons,
        }

    def dispatch_violation(self, violation_type: str) -> str:
        if violation_type == "hard_violation":
            return self.violation_policy.get("on_hard_violation", "rollback_and_freeze_l4")
        if violation_type == "repeated_l3_rejection":
            return self.violation_policy.get("on_repeated_l3_rejection", "decay_to_base")
        return "log_and_monitor"

    def is_bundle_fresh(self, artifact_bundle_hash: str) -> bool:
        return artifact_bundle_hash == self.objective_bundle_hash

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "primary_objective": self.primary_objective,
            "objective_version": self.objective_version,
            "objective_hash": self.objective_hash,
            "reducer_version": self.reducer_version,
            "metric_bundle_hash": self.metric_bundle_hash,
            "objective_bundle_hash": self.objective_bundle_hash,
            "hard_constraints": self.hard_constraints,
            "invariant_set": list(self.invariant_set),
            "approval_policy": self.approval_policy,
            "trust_region_policy": self.trust_region_policy,
            "promotion_budget_policy": self.promotion_budget_policy,
            "shadow_replay_policy": self.shadow_replay_policy,
            "violation_policy": self.violation_policy,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "PolicyShieldSnapshot":
        if not payload:
            return cls()
        return cls(**{key: value for key, value in payload.items() if key in cls.__dataclass_fields__})
