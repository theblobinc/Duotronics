from __future__ import annotations

from dataclasses import dataclass, field
from math import log
from typing import Mapping


PLASTIC_RHO = 1.324717957244746
RHO_INV_1 = 1.0 / PLASTIC_RHO
RHO_INV_2 = RHO_INV_1**2
RHO_INV_3 = RHO_INV_1**3
RHO_INV_4 = RHO_INV_1**4

RHO_DECAY_LADDER: dict[str, float] = {
    "long": RHO_INV_1,
    "medium": RHO_INV_2,
    "short": RHO_INV_3,
    "fast": RHO_INV_4,
}

DEFAULT_FAMILY_DECAYS: dict[str, str] = {
    "callback_rich": "long",
    "motif_recurrence": "medium",
    "novelty": "fast",
    "low_evidence": "fast",
}


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def rho_decay_for_family(family: str, default: str = "medium") -> float:
    tier = DEFAULT_FAMILY_DECAYS.get(family, default)
    return RHO_DECAY_LADDER.get(tier, RHO_DECAY_LADDER["medium"])


def rho_ema_update(previous: float, delta: float, decay: float) -> float:
    return decay * previous + delta


def padovan_delayed_update(
    t_minus_2: float,
    t_minus_3: float,
    delta: float,
    alpha: float = 1.0,
) -> float:
    bounded_alpha = _clip(alpha, 0.0, 1.0)
    return bounded_alpha * RHO_INV_3 * (t_minus_2 + t_minus_3) + delta


def hybrid_rho_padovan_update(
    t_minus_1: float,
    t_minus_2: float,
    t_minus_3: float,
    delta: float,
    decay: float,
    beta: float,
) -> float:
    bounded_decay = _clip(decay, 0.0, RHO_INV_1)
    bounded_beta = _clip(beta, 0.0, 1.0 - bounded_decay)
    return bounded_decay * t_minus_1 + bounded_beta * RHO_INV_3 * (t_minus_2 + t_minus_3) + delta


def expected_witness_from_history(w1: Mapping[str, float], w2: Mapping[str, float]) -> dict[str, float]:
    keys = set(w1) | set(w2)
    return {
        key: (RHO_INV_1 * float(w1.get(key, 0.0)) + RHO_INV_2 * float(w2.get(key, 0.0))) / PLASTIC_RHO
        for key in keys
    }


def rho_bucket(value: float, *, floor: float = 1e-9) -> int:
    magnitude = max(abs(value), floor)
    return int(log(magnitude, PLASTIC_RHO))


def rho_threshold_tier(score: float) -> str:
    bounded = _clip(score, 0.0, 1.0)
    if bounded >= RHO_INV_1:
        return "long"
    if bounded >= RHO_INV_2:
        return "medium"
    if bounded >= RHO_INV_3:
        return "short"
    return "fast"


@dataclass(frozen=True)
class RhoKernelConfig:
    enabled: bool = False
    scope: str = "worker"
    memory_mode: str = "hybrid"
    alpha: float = 0.85
    beta: float = 0.25
    trace_depth: int = 3
    diagnostics: bool = True
    persist_fields: bool = False

    @classmethod
    def from_dict(cls, payload: Mapping[str, object] | None) -> "RhoKernelConfig":
        payload = payload or {}
        return cls(
            enabled=bool(payload.get("enabled", False)),
            scope=str(payload.get("scope", "worker")),
            memory_mode=str(payload.get("memory_mode", "hybrid")),
            alpha=float(payload.get("alpha", 0.85)),
            beta=float(payload.get("beta", 0.25)),
            trace_depth=int(payload.get("trace_depth", 3)),
            diagnostics=bool(payload.get("diagnostics", True)),
            persist_fields=bool(payload.get("persist_fields", False)),
        )

    def failure_reasons(self) -> list[str]:
        reasons: list[str] = []
        if not self.enabled:
            reasons.append("rho_kernel_disabled")
        if self.scope == "canonical":
            reasons.append("canonical_scope_requires_explicit_promotion")
        if self.memory_mode not in {"ema", "rho_ladder", "padovan_delayed", "hybrid"}:
            reasons.append("unsupported_rho_memory_mode")
        return reasons


@dataclass
class RhoPadovanTrace:
    family: str = "motif_recurrence"
    history: dict[str, list[float]] = field(default_factory=dict)

    def step(
        self,
        deltas: Mapping[str, float],
        config: RhoKernelConfig,
        *,
        decay_tier: str | None = None,
    ) -> dict:
        reasons = config.failure_reasons()
        decay = RHO_DECAY_LADDER.get(decay_tier or DEFAULT_FAMILY_DECAYS.get(self.family, "medium"), RHO_DECAY_LADDER["medium"])
        updates: dict[str, float] = {}
        diagnostics: dict[str, dict[str, float]] = {}

        if reasons:
            return {
                "schema_version": "rho-memory-step-result@v1",
                "status": "rejected",
                "updates": updates,
                "history": {key: list(values) for key, values in self.history.items()},
                "diagnostics": diagnostics,
                "failure_reasons": reasons,
            }

        for coordinate, delta_value in deltas.items():
            prior = list(self.history.get(coordinate, []))
            t_minus_1 = prior[-1] if len(prior) >= 1 else 0.0
            t_minus_2 = prior[-2] if len(prior) >= 2 else 0.0
            t_minus_3 = prior[-3] if len(prior) >= 3 else 0.0
            delta = float(delta_value)
            if config.memory_mode in {"ema", "rho_ladder"}:
                updated = rho_ema_update(t_minus_1, delta, decay)
            elif config.memory_mode == "padovan_delayed":
                updated = padovan_delayed_update(t_minus_2, t_minus_3, delta, config.alpha)
            else:
                updated = hybrid_rho_padovan_update(t_minus_1, t_minus_2, t_minus_3, delta, decay, config.beta)
            rounded = round(updated, 6)
            updates[coordinate] = rounded
            next_history = (prior + [updated])[-max(1, config.trace_depth) :]
            self.history[coordinate] = next_history
            diagnostics[coordinate] = {
                "decay": round(decay, 6),
                "beta": round(_clip(config.beta, 0.0, 1.0 - _clip(decay, 0.0, RHO_INV_1)), 6),
                "t_minus_1": round(t_minus_1, 6),
                "t_minus_2": round(t_minus_2, 6),
                "t_minus_3": round(t_minus_3, 6),
            }

        return {
            "schema_version": "rho-memory-step-result@v1",
            "status": "accepted",
            "updates": updates,
            "history": {key: [round(value, 6) for value in values] for key, values in self.history.items()},
            "diagnostics": diagnostics,
            "failure_reasons": [],
        }
