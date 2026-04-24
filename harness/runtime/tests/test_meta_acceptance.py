from runtime_ref.meta.acceptance import accept_or_reject_meta
from runtime_ref.meta.diagnostics import AcceptanceDecision, MetaDiagnostics
from runtime_ref.meta.replay import ShadowReplaySpec
from runtime_ref.meta.witness import MetaRecurrentWitness


def _policy() -> dict:
    return {
        "objective_bundle_hash": "bundle-1",
        "approval_policy": {"l3_auto_apply": True},
        "trust_region_policy": {},
    }


def test_accepts_fresh_candidate_with_evidence() -> None:
    previous = MetaRecurrentWitness(controller_confidence=0.0)
    candidate = previous.compute_candidate({"temporal_local": 0.1, "__callback__": 0.2}, l5_policy=_policy())
    candidate.controller_confidence = 0.6
    replay_spec = ShadowReplaySpec(
        sequence_ids=[f"seq-{index}" for index in range(40)],
        slice_boundaries=[[0, 1024], [1024, 2056]],
        objective_bundle_hash="bundle-1",
    )
    diagnostics = MetaDiagnostics(
        epoch_step_count=1,
        objective_bundle_hash="bundle-1",
        replay_spec_hash=replay_spec.replay_spec_hash,
        replay_identity=replay_spec.replay_identity,
        sufficient_evidence=True,
        coverage_ratio=0.75,
        eval_count=5,
        controller_confidence=candidate.controller_confidence,
    )

    accepted, diagnostic = accept_or_reject_meta(
        previous,
        candidate,
        diagnostics,
        replay_spec.to_dict(),
        _policy(),
    )

    assert diagnostic.acceptance_decision == AcceptanceDecision.ACCEPTED.value
    assert accepted.accepted_updates == 1


def test_rejects_stale_replay_identity() -> None:
    previous = MetaRecurrentWitness(log_decay_offset={"temporal_local": 0.2})
    candidate = MetaRecurrentWitness.from_dict(previous.to_dict())
    candidate.controller_confidence = 0.7
    candidate.epoch_step_count = 2
    replay_spec = ShadowReplaySpec(objective_bundle_hash="bundle-1", sequence_ids=["seq-1"])
    diagnostics = MetaDiagnostics(
        epoch_step_count=2,
        objective_bundle_hash="bundle-1",
        replay_spec_hash="sha256:stale0000000000",
        replay_identity="sha256:stale0000000000:bundle-1",
        sufficient_evidence=True,
        coverage_ratio=0.8,
        eval_count=3,
    )

    rejected, diagnostic = accept_or_reject_meta(
        previous,
        candidate,
        diagnostics,
        replay_spec.to_dict(),
        _policy(),
    )

    assert diagnostic.acceptance_decision == AcceptanceDecision.REJECTED.value
    assert "stale_replay_identity" in diagnostic.rejection_reasons
    assert rejected.rejected_updates == 1


def test_rejects_stale_bundle_low_evidence_and_policy_freeze() -> None:
    previous = MetaRecurrentWitness(log_decay_offset={"temporal_local": 0.4}, callback_logit=0.3)
    candidate = MetaRecurrentWitness.from_dict(previous.to_dict())
    candidate.controller_confidence = 0.02
    candidate.epoch_step_count = 3
    replay_spec = ShadowReplaySpec(objective_bundle_hash="bundle-1", sequence_ids=["seq-1"])
    diagnostics = MetaDiagnostics(
        epoch_step_count=3,
        objective_bundle_hash="bundle-stale",
        replay_spec_hash=replay_spec.replay_spec_hash,
        replay_identity=replay_spec.replay_identity,
        sufficient_evidence=False,
        coverage_ratio=0.0,
        eval_count=1,
    )
    policy = {
        "objective_bundle_hash": "bundle-1",
        "approval_policy": {"l3_auto_apply": False},
    }

    rejected, diagnostic = accept_or_reject_meta(previous, candidate, diagnostics, replay_spec.to_dict(), policy)

    assert diagnostic.acceptance_decision == AcceptanceDecision.REJECTED.value
    assert set(diagnostic.rejection_reasons) >= {
        "stale_objective_bundle",
        "low_evidence",
        "low_confidence",
        "hard_violation",
        "policy_freeze",
    }
    assert rejected.log_decay_offset["temporal_local"] < previous.log_decay_offset["temporal_local"]
