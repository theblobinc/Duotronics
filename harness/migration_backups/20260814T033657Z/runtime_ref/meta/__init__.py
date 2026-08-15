"""Core L3 meta-runtime primitives."""

from .acceptance import accept_or_reject_meta
from .diagnostics import AcceptanceDecision, MetaDiagnostics, RejectionReason
from .estimator import EstimatorResult, finite_difference_meta_estimator
from .replay import ShadowReplaySpec
from .witness import MetaRecurrentWitness

__all__ = [
    "AcceptanceDecision",
    "EstimatorResult",
    "MetaDiagnostics",
    "MetaRecurrentWitness",
    "RejectionReason",
    "ShadowReplaySpec",
    "accept_or_reject_meta",
    "finite_difference_meta_estimator",
]
