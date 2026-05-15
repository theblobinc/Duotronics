from __future__ import annotations

from typing import Any

from .evidence import EvidenceKernel, sha256_ref


class SelfDevelopmentController:
    """Gated self-development planner.

    This component intentionally proposes worktree/test/commit candidates. It does not merge,
    deploy, approve secrets, or mutate production without an external approval witness.
    """

    def __init__(self, observer_id: str = "self-development-controller") -> None:
        self.kernel = EvidenceKernel(observer_id=observer_id)

    def plan(self, task: str, repo_ref: str = "mounted-workspace") -> dict[str, Any]:
        steps = [
            "create isolated worktree",
            "inspect relevant docs, tests, configs, and runtime state",
            "write a small reviewable patch",
            "run targeted tests and conformance checks",
            "emit SelfDevelopmentWitness with diff/test evidence",
            "create commit candidate only after validation",
            "require human/release approval before merge or deploy",
        ]
        payload = {
            "task": task,
            "repo_ref": repo_ref,
            "task_digest": sha256_ref(task),
            "steps": steps,
            "allowed_without_external_approval": ["inspect", "plan", "patch_candidate", "test_candidate"],
            "requires_external_approval": ["merge", "deploy", "secret_use", "production_mutation", "authority_promotion"],
            "non_collapse": {
                "self_patch_is_not_release": True,
                "passing_tests_are_not_proof": True,
                "model_generated_code_is_not_authority": True,
            },
        }
        witness = self.kernel.witness("SelfDevelopmentPlanWitness", payload, force="propose")
        return {"plan": payload, "witness": witness}
