from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

from .witness import BASE_LAMBDAS, DELTA_MAX_LAMBDA, DELTA_MAX_RHO, MetaRecurrentWitness

P_MAX = 8
H_SWEEP = 10
N_VALID_MIN = 2
U_MIN = 0.05


@dataclass
class EstimatorResult:
    schema_version: str = "meta-estimator-result@v1"
    gradient_estimate: dict[str, float] = field(default_factory=dict)
    eval_count: int = 0
    replay_spec_hash: str = ""
    replay_identity: str = ""
    objective_version: str = ""
    objective_hash: str = ""
    reducer_version: str = ""
    metric_bundle_hash: str = ""
    objective_bundle_hash: str = ""
    coverage_ratio: float = 0.0
    objective_dispersion: float = 0.0
    sufficient_evidence: bool = False
    active_coordinates: list[str] = field(default_factory=list)
    seed: int = 0

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "gradient_estimate": dict(self.gradient_estimate),
            "eval_count": self.eval_count,
            "replay_spec_hash": self.replay_spec_hash,
            "replay_identity": self.replay_identity,
            "objective_version": self.objective_version,
            "objective_hash": self.objective_hash,
            "reducer_version": self.reducer_version,
            "metric_bundle_hash": self.metric_bundle_hash,
            "objective_bundle_hash": self.objective_bundle_hash,
            "coverage_ratio": round(self.coverage_ratio, 4),
            "objective_dispersion": round(self.objective_dispersion, 6),
            "sufficient_evidence": self.sufficient_evidence,
            "active_coordinates": list(self.active_coordinates),
            "seed": self.seed,
        }


def finite_difference_meta_estimator(
    controller: MetaRecurrentWitness,
    theta: dict[str, float],
    shadow_objective_fn: Callable[[dict[str, float], dict, int], float],
    replay_spec: dict,
    l5_policy: dict,
    *,
    seed: int = 0,
    family_usage: dict[str, float] | None = None,
    epoch_step: int = 0,
) -> EstimatorResult:
    family_usage = family_usage or {}
    trust_region_policy = l5_policy.get("trust_region_policy", {})
    family_overrides = trust_region_policy.get("family_overrides", {})

    is_sweep = epoch_step > 0 and epoch_step % H_SWEEP == 0
    eligible: list[str] = []
    for coordinate in theta:
        if coordinate == "__callback__":
            eligible.append(coordinate)
            continue
        if family_usage.get(coordinate, 0.0) >= U_MIN or is_sweep:
            eligible.append(coordinate)

    if len(eligible) > P_MAX:
        eligible.sort(key=lambda coordinate: family_usage.get(coordinate, float("inf")), reverse=True)
        eligible = eligible[:P_MAX]

    epsilon_lambda: dict[str, float] = {}
    for family in eligible:
        if family == "__callback__":
            continue
        max_step = family_overrides.get(family, {}).get(
            "max_l3_log_decay_step",
            trust_region_policy.get("max_l3_log_decay_step", DELTA_MAX_LAMBDA),
        )
        epsilon_lambda[family] = min(0.01, 0.25 * max_step)
    epsilon_rho = min(0.05, 0.25 * trust_region_policy.get("max_l3_callback_logit_step", DELTA_MAX_RHO))

    try:
        incumbent = shadow_objective_fn(theta, replay_spec, seed)
    except Exception:
        return EstimatorResult(
            replay_spec_hash=replay_spec.get("replay_spec_hash", ""),
            replay_identity=replay_spec.get("replay_identity", ""),
            objective_bundle_hash=l5_policy.get("objective_bundle_hash", replay_spec.get("objective_bundle_hash", "")),
            seed=seed,
            sufficient_evidence=False,
        )

    gradient: dict[str, float] = {}
    plus_values: list[float] = []
    minus_values: list[float] = []
    eval_count = 1

    for coordinate in eligible:
        epsilon = epsilon_rho if coordinate == "__callback__" else epsilon_lambda.get(coordinate, 0.01)
        if epsilon <= 1e-12:
            gradient[coordinate] = 0.0
            continue
        theta_plus = dict(theta)
        theta_minus = dict(theta)
        theta_plus[coordinate] = theta.get(coordinate, 0.0) + epsilon
        theta_minus[coordinate] = theta.get(coordinate, 0.0) - epsilon
        try:
            plus_value = shadow_objective_fn(theta_plus, replay_spec, seed)
            minus_value = shadow_objective_fn(theta_minus, replay_spec, seed)
            gradient[coordinate] = (plus_value - minus_value) / (2.0 * epsilon)
            plus_values.append(plus_value)
            minus_values.append(minus_value)
            eval_count += 2
        except Exception:
            gradient[coordinate] = 0.0

    valid_count = len(plus_values)
    all_values = [incumbent] + plus_values + minus_values
    mean_value = sum(all_values) / len(all_values)
    dispersion = math.sqrt(sum((value - mean_value) ** 2 for value in all_values) / len(all_values))

    total_coordinates = len(BASE_LAMBDAS) + 1
    coverage = len(eligible) / max(total_coordinates, 1)

    return EstimatorResult(
        gradient_estimate=gradient,
        eval_count=eval_count,
        replay_spec_hash=replay_spec.get("replay_spec_hash", ""),
        replay_identity=replay_spec.get("replay_identity", ""),
        objective_version=l5_policy.get("objective_version", ""),
        objective_hash=l5_policy.get("objective_hash", ""),
        reducer_version=l5_policy.get("reducer_version", ""),
        metric_bundle_hash=l5_policy.get("metric_bundle_hash", ""),
        objective_bundle_hash=l5_policy.get("objective_bundle_hash", replay_spec.get("objective_bundle_hash", "")),
        coverage_ratio=coverage,
        objective_dispersion=dispersion,
        sufficient_evidence=valid_count >= N_VALID_MIN,
        active_coordinates=eligible,
        seed=seed,
    )
