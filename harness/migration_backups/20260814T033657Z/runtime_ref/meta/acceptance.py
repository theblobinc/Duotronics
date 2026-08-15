from __future__ import annotations

from typing import Callable

from .diagnostics import AcceptanceDecision, MetaDiagnostics, RejectionReason
from .witness import C_MIN, KAPPA_REJECTION, MetaRecurrentWitness


def accept_or_reject_meta(
    prev: MetaRecurrentWitness,
    candidate: MetaRecurrentWitness,
    diagnostics: MetaDiagnostics,
    replay_spec: dict,
    l5_policy: dict,
    *,
    shadow_objective_fn: Callable[[dict[str, float], dict, int], float] | None = None,
    delta_tol: float = 0.005,
    kappa: float = KAPPA_REJECTION,
) -> tuple[MetaRecurrentWitness, MetaDiagnostics]:
    reasons: list[RejectionReason] = []

    bundle_hash = l5_policy.get("objective_bundle_hash", "")
    if bundle_hash and diagnostics.objective_bundle_hash != bundle_hash:
        reasons.append(RejectionReason.STALE_OBJECTIVE_BUNDLE)

    replay_spec_hash = replay_spec.get("replay_spec_hash", "")
    if replay_spec_hash and diagnostics.replay_spec_hash != replay_spec_hash:
        reasons.append(RejectionReason.STALE_REPLAY_IDENTITY)

    replay_identity = replay_spec.get("replay_identity", replay_spec_hash)
    if diagnostics.replay_identity and replay_identity and diagnostics.replay_identity != replay_identity:
        reasons.append(RejectionReason.STALE_REPLAY_IDENTITY)

    if not diagnostics.sufficient_evidence:
        reasons.append(RejectionReason.LOW_EVIDENCE)

    if candidate.controller_confidence < C_MIN:
        reasons.append(RejectionReason.LOW_CONFIDENCE)

    if diagnostics.coverage_ratio <= 0 and diagnostics.eval_count > 0:
        reasons.append(RejectionReason.HARD_VIOLATION)

    approval_policy = l5_policy.get("approval_policy", {})
    if not approval_policy.get("l3_auto_apply", True):
        reasons.append(RejectionReason.POLICY_FREEZE)

    if shadow_objective_fn is not None and not reasons:
        try:
            previous_score = shadow_objective_fn(prev.to_theta(), replay_spec, diagnostics.seed)
            candidate_score = shadow_objective_fn(candidate.to_theta(), replay_spec, diagnostics.seed)
            if candidate_score < previous_score - delta_tol:
                reasons.append(RejectionReason.OBJECTIVE_REGRESSION)
        except Exception:
            reasons.append(RejectionReason.ESTIMATOR_FAILURE)

    if reasons:
        rejected = MetaRecurrentWitness.from_dict(prev.to_dict())
        rejected.relax_toward_base(kappa)
        rejected.rejected_updates = prev.rejected_updates + 1
        rejected.epoch_step_count = candidate.epoch_step_count
        diagnostics.acceptance_decision = AcceptanceDecision.REJECTED.value
        diagnostics.rejection_reasons = [reason.value for reason in reasons]
        return rejected, diagnostics

    candidate.accepted_updates = prev.accepted_updates + 1
    diagnostics.acceptance_decision = AcceptanceDecision.ACCEPTED.value
    diagnostics.rejection_reasons = []
    return candidate, diagnostics
