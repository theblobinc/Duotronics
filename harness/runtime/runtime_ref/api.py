from __future__ import annotations

from typing import Any, Callable

from runtime_ref.architecture.manager import ArchitecturalWitness
from runtime_ref.architecture.review import ApprovalRecord, ArchitectureReviewBundle
from runtime_ref.architecture.state_migration import StateMigrationPlan
from runtime_ref.meta.acceptance import accept_or_reject_meta
from runtime_ref.meta.diagnostics import MetaDiagnostics
from runtime_ref.meta.replay import ShadowReplaySpec
from runtime_ref.meta.witness import MetaRecurrentWitness
from runtime_ref.meta_objects.normalization import (
    build_meta_object_instance as _build_meta_object_instance,
    canonicalize_meta_bundle as _canonicalize_meta_bundle,
    compute_meta_summary as _compute_meta_summary,
    normalize_meta_object as _normalize_meta_object,
)
from runtime_ref.policy.constraints import PolicyShieldSnapshot


def _status(valid: bool) -> str:
    return "accepted" if valid else "rejected"


def _objective_function_factory(target_theta: dict[str, float] | None) -> Callable[[dict[str, float], dict, int], float]:
    target_theta = target_theta or {}

    def objective(theta: dict[str, float], replay_spec: dict, seed: int) -> float:
        del replay_spec, seed
        keys = set(theta) | set(target_theta)
        penalty = sum((float(theta.get(key, 0.0)) - float(target_theta.get(key, 0.0))) ** 2 for key in keys)
        return 1.0 - penalty

    return objective


def build_meta_object_instance(given: dict[str, Any]) -> dict:
    return _build_meta_object_instance(given)


def normalize_meta_object(given: dict[str, Any]) -> dict:
    normalized = _normalize_meta_object(given)
    return {
        "schema_version": "normalize-meta-object-result@v1",
        "status": "ok",
        "normalized": normalized,
        "diagnostics": {"canonical_digest": normalized["canonical_digest"]},
        "failure_reasons": [],
    }


def canonicalize_meta_bundle(given: dict[str, Any]) -> dict:
    bundle = _canonicalize_meta_bundle(given)
    return {
        "schema_version": "canonicalize-meta-bundle-result@v1",
        "status": "ok",
        "bundle": bundle,
        "diagnostics": {"bundle_hash": bundle["bundle_hash"]},
        "failure_reasons": [],
    }


def compute_meta_summary(given: dict[str, Any]) -> dict:
    summary = _compute_meta_summary(given)
    return {
        "schema_version": "compute-meta-summary-result@v1",
        "status": "ok",
        "summary": summary,
        "diagnostics": {"bundle_hash": summary["bundle_hash"]},
        "failure_reasons": [],
    }


def run_l3_acceptance(given: dict[str, Any]) -> dict:
    previous = MetaRecurrentWitness.from_dict(given.get("previous_witness"))
    candidate = MetaRecurrentWitness.from_dict(given.get("candidate_witness"))
    diagnostics = MetaDiagnostics.from_dict(given.get("diagnostics", {}))
    replay_spec = ShadowReplaySpec.from_dict(given.get("replay_spec", {}))
    policy = PolicyShieldSnapshot.from_dict(given.get("policy_shield", {}))
    objective_fn = _objective_function_factory(given.get("objective_target_theta")) if given.get("objective_target_theta") is not None else None

    witness, diagnostics_out = accept_or_reject_meta(
        previous,
        candidate,
        diagnostics,
        replay_spec.to_dict(),
        policy.to_dict(),
        shadow_objective_fn=objective_fn,
    )
    accepted = diagnostics_out.acceptance_decision == "accepted"
    return {
        "schema_version": "l3-acceptance-result@v1",
        "status": _status(accepted),
        "witness": witness.to_dict(),
        "diagnostics": diagnostics_out.to_dict(),
        "failure_reasons": diagnostics_out.rejection_reasons,
    }


def validate_replay_spec(given: dict[str, Any]) -> dict:
    replay_spec = ShadowReplaySpec.from_dict(given.get("replay_spec", given))
    policy = PolicyShieldSnapshot.from_dict(given.get("policy_shield", {}))
    validation = replay_spec.validate_coverage(policy.shadow_replay_policy)
    failure_reasons = list(validation["issues"])
    if replay_spec.objective_bundle_hash and not policy.is_bundle_fresh(replay_spec.objective_bundle_hash):
        failure_reasons.append("stale_objective_bundle")
    return {
        "schema_version": "replay-spec-validation-result@v1",
        "status": _status(not failure_reasons),
        "valid": not failure_reasons,
        "diagnostics": validation,
        "failure_reasons": failure_reasons,
        "replay_spec": replay_spec.to_dict(),
    }


def evaluate_policy_constraints(given: dict[str, Any]) -> dict:
    policy = PolicyShieldSnapshot.from_dict(given.get("policy_shield", given.get("policy", {})))
    state_snapshot = given.get("state_snapshot", {})
    proposal = given.get("proposal")
    approval = given.get("approval")
    current_budget = int(given.get("current_budget", 1))
    feasibility = policy.check_feasibility(state_snapshot)
    budget_validation = policy.validate_promotion_budget(current_budget)
    diagnostics = {
        "feasibility": feasibility,
        "promotion_budget": budget_validation,
        "bundle_fresh": policy.is_bundle_fresh(given.get("artifact_bundle_hash", policy.objective_bundle_hash)),
    }
    failure_reasons = list(feasibility["violations"])
    if not budget_validation["valid"]:
        failure_reasons.append("promotion_budget_invalid")

    if proposal is not None:
        diagnostics["operator_approval_required"] = policy.requires_operator_approval(proposal)
        diagnostics["risk_tier"] = str(policy.requires_operator_approval(proposal)).lower()

    if approval is not None and proposal is not None:
        approval_validation = policy.validate_approval(approval, proposal.get("proposal_hash", ""), proposal.get("objective_bundle_hash", ""))
        diagnostics["approval_validation"] = approval_validation
        if not approval_validation["valid"]:
            failure_reasons.extend(approval_validation["reasons"])

    return {
        "schema_version": "policy-constraint-evaluation@v1",
        "status": _status(not failure_reasons),
        "diagnostics": diagnostics,
        "failure_reasons": failure_reasons,
        "policy_shield": policy.to_dict(),
    }


def propose_architectural_change(given: dict[str, Any]) -> dict:
    witness = ArchitecturalWitness.from_dict(given.get("architectural_witness", {}))
    policy = PolicyShieldSnapshot.from_dict(given.get("policy_shield", {}))
    replay_spec = ShadowReplaySpec.from_dict(given.get("replay_spec", {}))
    proposal_type = given.get("proposal_type", "gate_mix")

    if proposal_type == "enable_family":
        proposal = witness.propose_enable_family(given["family_id"], policy, replay_spec_hash=replay_spec.replay_spec_hash)
    elif proposal_type == "prune_family":
        proposal = witness.propose_prune_family(given["family_id"], policy, replay_spec_hash=replay_spec.replay_spec_hash)
    elif proposal_type == "gate_mix":
        proposal = witness.propose_gate_mix(
            given.get("gate_name", "lookup_gate"),
            given.get("field_name", "bias"),
            float(given.get("delta", 0.0)),
            policy,
            replay_spec_hash=replay_spec.replay_spec_hash,
        )
    else:
        return {
            "schema_version": "architecture-proposal-result@v1",
            "status": "rejected",
            "diagnostics": {},
            "failure_reasons": [f"unsupported_proposal_type:{proposal_type}"],
        }

    migration_plan = None
    if given.get("migration_plan"):
        migration_plan = StateMigrationPlan.from_dict(given["migration_plan"])

    review_bundle = ArchitectureReviewBundle(
        proposal_id=proposal.proposal_id,
        proposal_hash=proposal.proposal_hash,
        parent_generation=proposal.parent_generation,
        candidate_generation=proposal.candidate_generation,
        structured_diff=list(proposal.mutations),
        risk_tier=proposal.risk_tier,
        objective_bundle_hash=proposal.objective_bundle_hash,
        replay_spec_hash=proposal.replay_spec_hash,
        migration_plan_ref=migration_plan.plan_id if migration_plan else None,
        rollback_snapshot_id=given.get("rollback_snapshot_id", ""),
        rollback_restore_verified=bool(given.get("rollback_restore_verified", False)),
    )

    failure_reasons: list[str] = []
    if proposal.requires_schema_migration and migration_plan is None:
        failure_reasons.append("migration_plan_missing")

    return {
        "schema_version": "architecture-proposal-result@v1",
        "status": "ok" if not failure_reasons else "rejected",
        "proposal": proposal.to_dict(),
        "review_bundle": review_bundle.to_dict(),
        "migration_plan": migration_plan.to_dict() if migration_plan else None,
        "diagnostics": {"candidate_queue_size": len(witness.candidate_queue)},
        "failure_reasons": failure_reasons,
    }


def dry_run_state_migration(given: dict[str, Any]) -> dict:
    migration_plan = StateMigrationPlan.from_dict(given.get("migration_plan", given.get("plan", {})))
    report = migration_plan.dry_run(given.get("state_snapshot", {}))
    failure_reasons = list(report.get("errors", []))
    if not report.get("rollback_compatible", True):
        failure_reasons.append("rollback_incompatible")
    return {
        "schema_version": "state-migration-operation@v1",
        "status": _status(report.get("success", False) and not failure_reasons),
        "report": report,
        "migration_plan": migration_plan.to_dict(),
        "failure_reasons": failure_reasons,
    }


def evaluate_meta_retention(given: dict[str, Any]) -> dict:
    reference_bundle = _canonicalize_meta_bundle(given.get("reference_bundle", {}))
    observed_bundle = _canonicalize_meta_bundle(given.get("observed_bundle", {}))
    reference_hashes = {assertion["canonical_digest"] for assertion in reference_bundle["assertions"]}
    observed_hashes = {assertion["canonical_digest"] for assertion in observed_bundle["assertions"]}
    preserved = sorted(reference_hashes & observed_hashes)
    missing = sorted(reference_hashes - observed_hashes)
    retention_ratio = len(preserved) / max(len(reference_hashes), 1)
    minimum_ratio = float(given.get("minimum_retention_ratio", 0.5))
    failure_reasons = [] if retention_ratio >= minimum_ratio else ["retention_below_threshold"]
    return {
        "schema_version": "meta-retention-result@v1",
        "status": _status(not failure_reasons),
        "retention_ratio": round(retention_ratio, 4),
        "diagnostics": {
            "reference_bundle_hash": reference_bundle["bundle_hash"],
            "observed_bundle_hash": observed_bundle["bundle_hash"],
            "preserved_assertions": preserved,
            "missing_assertions": missing,
        },
        "failure_reasons": failure_reasons,
    }


def step_meta_memory_cell(given: dict[str, Any]) -> dict:
    witness = MetaRecurrentWitness.from_dict(given.get("previous_witness"))
    candidate, diagnostics = witness.step_memory_cell(
        given.get("observation", {}),
        witness_features=given.get("witness_features", {}),
        policy=given.get("policy", {}),
        learning_rate=float(given.get("learning_rate", 1.0)),
    )
    accepted = bool(diagnostics["learning_applied"])
    return {
        "schema_version": "meta-memory-cell-step@v1",
        "status": _status(accepted),
        "witness": candidate.to_dict(),
        "diagnostics": diagnostics,
        "failure_reasons": list(diagnostics["failure_reasons"]),
    }


_OPERATIONS = {
    "build_meta_object_instance": build_meta_object_instance,
    "normalize_meta_object": normalize_meta_object,
    "canonicalize_meta_bundle": canonicalize_meta_bundle,
    "compute_meta_summary": compute_meta_summary,
    "run_l3_acceptance": run_l3_acceptance,
    "validate_replay_spec": validate_replay_spec,
    "evaluate_policy_constraints": evaluate_policy_constraints,
    "propose_architectural_change": propose_architectural_change,
    "dry_run_state_migration": dry_run_state_migration,
    "evaluate_meta_retention": evaluate_meta_retention,
    "step_meta_memory_cell": step_meta_memory_cell,
}


def run_meta_operation(op_name: str, given: dict[str, Any]) -> dict:
    operation = _OPERATIONS.get(op_name)
    if operation is None:
        return {
            "schema_version": "meta-operation-result@v1",
            "status": "rejected",
            "failure_reasons": [f"unknown_operation:{op_name}"],
            "diagnostics": {"known_operations": sorted(_OPERATIONS)},
        }
    return operation(given)
