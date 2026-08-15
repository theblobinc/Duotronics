from __future__ import annotations

from typing import Any

from .evidence import EvidenceKernel, shake256_ref


class SelfDevelopmentController:
    """Witness-gated autonomous self-development planner.

    The controller may autonomously inspect, branch/worktree, patch, evaluate,
    commit, merge and deploy *operational candidates* when a separately produced
    RecursiveImprovementGateWitness authorizes the transition and a rollback
    reference exists. It never treats its own code, passing tests, or model
    judgment as theorem/release/authority promotion under the Witness Contract.
    """

    def __init__(self, observer_id: str = "self-development-controller") -> None:
        self.kernel = EvidenceKernel(observer_id=observer_id)

    def plan(self, task: str, repo_ref: str = "mounted-workspace") -> dict[str, Any]:
        steps = [
            "create isolated worktree or branch-scoped candidate",
            "inspect relevant docs, tests, configs, runtime state, prior trajectories, and witnesses",
            "retrieve reusable implementation patterns and provenance-bound source material",
            "write a bounded candidate patch",
            "run targeted tests, regression suites, replay checks, and environment evaluations",
            "emit SelfDevelopmentCandidateWitness and AutonomousEvaluationWitness",
            "verify rollback reference and witness chain",
            "request RecursiveImprovementGateWitness",
            "autonomously merge/deploy operational candidate only when the gate authorizes it",
            "observe post-deploy health and automatically rollback on regression",
            "convert the complete trajectory into candidate WG-RNN learning experience",
        ]
        payload = {
            "schema_version": "self-development-plan/v2",
            "mode": "witness-gated-autonomous",
            "task": task,
            "repo_ref": repo_ref,
            "task_digest": shake256_ref(task),
            "steps": steps,
            "allowed_without_per_turn_human_approval": [
                "inspect",
                "retrieve_context",
                "create_worktree",
                "patch_candidate",
                "test_candidate",
                "evaluate_candidate",
                "commit_candidate",
                "resource_schedule",
                "operational_merge_when_gate_allows",
                "operational_deploy_when_gate_allows",
                "rollback",
                "record_experience",
                "train_candidate_memory",
            ],
            "requires_independent_gate": [
                "changes_to_witness_verifier_or_policy_surfaces",
                "changes_to_evaluator_used_to_score_same_candidate",
                "destructive_or_irreversible_migration",
            ],
            "never_self_granted": [
                "theorem_authority",
                "release_authority",
                "witness_contract_authority_promotion",
                "audit_history_erasure",
                "credential_exfiltration",
            ],
            "non_collapse": {
                "self_patch_is_not_release_authority": True,
                "passing_tests_are_not_proof": True,
                "model_generated_code_is_not_authority": True,
                "operational_promotion_is_not_theorem_promotion": True,
            },
        }
        witness = self.kernel.witness("SelfDevelopmentPlanWitness", payload, force="propose")
        return {"plan": payload, "witness": witness}

    def execution_policy(self) -> dict[str, Any]:
        payload = {
            "schema_version": "self-development-execution-policy/v1",
            "autonomy": "continuous",
            "per_turn_human_approval": False,
            "operational_promotion": "allowed_when_recursive_gate_witness_allows",
            "automatic_rollback": True,
            "authority_promotion": "separate_external_contract_gate",
            "protected_surface_rule": "independent_validation_required",
            "self_evaluator_rule": "candidate_may_not_weaken_its_only_evaluator_and_count_that_as_validation",
        }
        payload["policy_digest"] = shake256_ref(payload)
        return payload

    def can_execute_operational_transition(self, gate: dict[str, Any]) -> dict[str, Any]:
        allowed = bool(gate.get("operational_promotion_allowed"))
        payload = {
            "schema_version": "self-development-transition-decision/v1",
            "allowed": allowed,
            "candidate_id": gate.get("candidate_id"),
            "evaluation_id": gate.get("evaluation_id"),
            "gate_witness_id": (gate.get("witness") or {}).get("witness_id") if isinstance(gate.get("witness"), dict) else gate.get("witness_id"),
            "reasons": list(gate.get("reasons") or []),
            "authority_promotion": False,
        }
        witness = self.kernel.witness(
            "SelfDevelopmentTransitionWitness",
            payload,
            force="authorize" if allowed else "refuse",
            status="recorded",
        )
        return {"decision": payload, "witness": witness}
