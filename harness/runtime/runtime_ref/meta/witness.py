from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field

BASE_LAMBDAS: dict[str, float] = {
    "temporal_local": 0.90,
    "temporal_distant": 0.98,
    "high_density": 0.95,
    "social_anchored": 0.92,
    "callback_rich": 0.96,
    "cross_source": 0.93,
    "motif_recurrence": 0.97,
    "low_evidence": 0.85,
}
DEFAULT_LAMBDA = 0.94
BASE_RHO = 0.5

BETA_M = 0.9
G_MAX = 1.0

DELTA_MAX_LAMBDA = 0.03
DELTA_MAX_RHO = 0.15

C_MIN = 0.10
KAPPA_REJECTION = 0.05

EMA_REGIME = 0.95
EMA_SHADOW = 0.95
EMA_PREDICTION = 0.95


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_value = math.exp(-value)
        return 1.0 / (1.0 + exp_value)
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _lambda_bounds(base: float) -> tuple[float, float]:
    return max(0.70, base * 0.85), min(0.999, base * 1.10)


def _rho_bounds(base: float) -> tuple[float, float]:
    return 0.80 * base, min(0.999, 1.15 * base)


@dataclass
class MetaRecurrentWitness:
    log_decay_offset: dict[str, float] = field(default_factory=dict)
    callback_logit: float = 0.0
    meta_momentum: dict[str, float] = field(default_factory=dict)
    regime_posterior: dict[str, float] = field(
        default_factory=lambda: {
            "stable": 0.25,
            "shifting": 0.25,
            "fragmented": 0.25,
            "contradictory": 0.25,
        }
    )
    shadow_objective_ema: float = 0.0
    prediction_error_ema: float = 0.0
    controller_confidence: float = 0.0
    accepted_updates: int = 0
    rejected_updates: int = 0
    epoch_step_count: int = 0

    def effective_lambdas(self, base_lambdas: dict[str, float] | None = None) -> dict[str, float]:
        bases = base_lambdas or BASE_LAMBDAS
        result: dict[str, float] = {}
        for family, base in bases.items():
            raw = base * math.exp(self.log_decay_offset.get(family, 0.0))
            lower, upper = _lambda_bounds(base)
            result[family] = _clip(raw, lower, upper)
        return result

    def effective_rho(self, base_rho: float = BASE_RHO) -> float:
        raw = _sigmoid(self.callback_logit)
        lower, upper = _rho_bounds(base_rho)
        return _clip(raw, lower, upper)

    def update_regime_posterior(self, evidence: dict[str, float]) -> None:
        alpha = 1.0 - EMA_REGIME
        for regime, weight in evidence.items():
            previous = self.regime_posterior.get(regime, 0.0)
            self.regime_posterior[regime] = EMA_REGIME * previous + alpha * weight
        total = sum(self.regime_posterior.values())
        if total > 0:
            self.regime_posterior = {key: value / total for key, value in self.regime_posterior.items()}

    def update_shadow_objective(self, objective_value: float) -> None:
        alpha = 1.0 - EMA_SHADOW
        self.shadow_objective_ema = EMA_SHADOW * self.shadow_objective_ema + alpha * objective_value

    def update_prediction_error(self, error: float) -> None:
        alpha = 1.0 - EMA_PREDICTION
        self.prediction_error_ema = EMA_PREDICTION * self.prediction_error_ema + alpha * abs(error)

    def compute_confidence(
        self,
        sigma_j: float = 1.0,
        telemetry_coverage: float = 1.0,
        min_coverage: float = 0.5,
    ) -> float:
        if telemetry_coverage < min_coverage:
            self.controller_confidence = 0.0
            return 0.0
        raw = 1.0 - self.prediction_error_ema / (sigma_j + 1e-8)
        self.controller_confidence = _clip(raw, 0.0, 1.0)
        return self.controller_confidence

    def update_momentum(self, gradient: dict[str, float]) -> None:
        for coordinate, value in gradient.items():
            clipped = _clip(value, -G_MAX, G_MAX)
            previous = self.meta_momentum.get(coordinate, 0.0)
            self.meta_momentum[coordinate] = BETA_M * previous + (1 - BETA_M) * clipped

    def compute_candidate(
        self,
        gradient: dict[str, float],
        learning_rate: float = 1.0,
        l5_policy: dict | None = None,
    ) -> "MetaRecurrentWitness":
        candidate = copy.deepcopy(self)
        candidate.update_momentum(gradient)

        trust_region_policy = (l5_policy or {}).get("trust_region_policy", {})
        family_overrides = trust_region_policy.get("family_overrides", {})

        for family in set(self.log_decay_offset) | {key for key in gradient if key != "__callback__"}:
            momentum = candidate.meta_momentum.get(family, 0.0)
            delta = learning_rate * self.controller_confidence * momentum
            max_step = family_overrides.get(family, {}).get(
                "max_l3_log_decay_step",
                trust_region_policy.get("max_l3_log_decay_step", DELTA_MAX_LAMBDA),
            )
            delta = _clip(delta, -max_step, max_step)
            candidate.log_decay_offset[family] = self.log_decay_offset.get(family, 0.0) + delta

        if "__callback__" in gradient or "__callback__" in candidate.meta_momentum:
            momentum = candidate.meta_momentum.get("__callback__", 0.0)
            delta = learning_rate * self.controller_confidence * momentum
            max_step = trust_region_policy.get("max_l3_callback_logit_step", DELTA_MAX_RHO)
            candidate.callback_logit = self.callback_logit + _clip(delta, -max_step, max_step)

        candidate.epoch_step_count = self.epoch_step_count + 1
        return candidate

    def relax_toward_base(self, kappa: float = KAPPA_REJECTION) -> None:
        for family in list(self.log_decay_offset):
            self.log_decay_offset[family] *= 1.0 - kappa
        self.callback_logit *= 1.0 - kappa

    def is_null(self) -> bool:
        if self.controller_confidence > 0:
            return False
        if any(abs(value) > 1e-9 for value in self.log_decay_offset.values()):
            return False
        return abs(self.callback_logit) <= 1e-9

    def to_theta(self) -> dict[str, float]:
        theta = dict(self.log_decay_offset)
        theta["__callback__"] = self.callback_logit
        return theta

    def to_dict(self) -> dict:
        return {
            "log_decay_offset": {key: round(value, 6) for key, value in self.log_decay_offset.items()},
            "callback_logit": round(self.callback_logit, 6),
            "meta_momentum": {key: round(value, 6) for key, value in self.meta_momentum.items()},
            "regime_posterior": {key: round(value, 4) for key, value in self.regime_posterior.items()},
            "shadow_objective_ema": round(self.shadow_objective_ema, 6),
            "prediction_error_ema": round(self.prediction_error_ema, 6),
            "controller_confidence": round(self.controller_confidence, 4),
            "accepted_updates": self.accepted_updates,
            "rejected_updates": self.rejected_updates,
            "epoch_step_count": self.epoch_step_count,
        }

    @classmethod
    def from_dict(cls, payload: dict | None) -> "MetaRecurrentWitness":
        if not payload:
            return cls()
        return cls(
            log_decay_offset={key: float(value) for key, value in payload.get("log_decay_offset", {}).items()},
            callback_logit=float(payload.get("callback_logit", 0.0)),
            meta_momentum={key: float(value) for key, value in payload.get("meta_momentum", {}).items()},
            regime_posterior={key: float(value) for key, value in payload.get("regime_posterior", {}).items()},
            shadow_objective_ema=float(payload.get("shadow_objective_ema", 0.0)),
            prediction_error_ema=float(payload.get("prediction_error_ema", 0.0)),
            controller_confidence=float(payload.get("controller_confidence", 0.0)),
            accepted_updates=int(payload.get("accepted_updates", 0)),
            rejected_updates=int(payload.get("rejected_updates", 0)),
            epoch_step_count=int(payload.get("epoch_step_count", 0)),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)
