from runtime_ref.api import run_meta_operation
from runtime_ref.architecture.review import ApprovalRecord, ArchitectureReviewBundle
from runtime_ref.architecture.state_migration import StateMigrationPlan
from runtime_ref.policy.constraints import PolicyShieldSnapshot
from runtime_ref.state import RuntimeState


def test_policy_constraints_report_hard_violations() -> None:
    result = run_meta_operation(
        "evaluate_policy_constraints",
        {
            "state_snapshot": {
                "active_family_count": 99,
                "memory_mb": 900,
                "step_time_ms": 75,
                "silent_coercion_detected": True,
            }
        },
    )

    assert result["status"] == "rejected"
    assert "active_family_count>20" in result["failure_reasons"]
    assert "memory_mb>512" in result["failure_reasons"]
    assert "step_time_ms>50" in result["failure_reasons"]
    assert "no_silent_coercion" in result["failure_reasons"]


def test_architecture_proposal_supports_enable_prune_and_gate_mix() -> None:
    enable_result = run_meta_operation(
        "propose_architectural_change",
        {"proposal_type": "enable_family", "family_id": "cross_source"},
    )
    prune_result = run_meta_operation(
        "propose_architectural_change",
        {"proposal_type": "prune_family", "family_id": "low_evidence"},
    )
    gate_result = run_meta_operation(
        "propose_architectural_change",
        {"proposal_type": "gate_mix", "gate_name": "lookup_gate", "field_name": "bias", "delta": 0.1},
    )

    assert enable_result["proposal"]["proposal_type"] == "enable_family"
    assert prune_result["proposal"]["proposal_type"] == "prune_family"
    assert gate_result["proposal"]["proposal_type"] == "gate_mix"


def test_state_migration_supports_defaulting_and_drop_field() -> None:
    plan = StateMigrationPlan(
        from_generation=1,
        to_generation=2,
        from_schema_version="runtime-state@v1",
        to_schema_version="runtime-state@v2",
        new_fields=["new_counter"],
        defaulting_rules={"new_counter": 0},
        dropped_fields=["old_field"],
    )

    report = plan.dry_run({"old_field": "legacy", "stable": True})
    assert report["success"] is True
    assert report["migrated_state"]["new_counter"] == 0
    assert "old_field" not in report["migrated_state"]


def test_state_migration_public_api_exposes_dry_run() -> None:
    result = run_meta_operation(
        "dry_run_state_migration",
        {
            "migration_plan": {
                "from_generation": 1,
                "to_generation": 2,
                "from_schema_version": "runtime-state@v1",
                "to_schema_version": "runtime-state@v2",
                "new_fields": ["new_counter"],
                "defaulting_rules": {"new_counter": 0},
                "dropped_fields": ["old_field"],
            },
            "state_snapshot": {"old_field": "legacy", "stable": True},
        },
    )

    assert result["status"] == "accepted"
    assert result["report"]["migrated_state"]["new_counter"] == 0
    assert result["failure_reasons"] == []


def test_review_bundle_and_approval_record_round_trip() -> None:
    bundle = ArchitectureReviewBundle(
        proposal_id="delta-1",
        proposal_hash="sha256:abc",
        parent_generation=1,
        candidate_generation=2,
        structured_diff=[{"type": "enable_family", "family_id": "cross_source"}],
        risk_tier="medium",
        objective_bundle_hash="bundle-1",
    )
    approval = ApprovalRecord(
        bundle_id=bundle.bundle_id,
        proposal_hash="sha256:abc",
        risk_tier="medium",
        objective_bundle_hash="bundle-1",
        approver_id="operator-1",
        decision="approved",
    )

    assert ArchitectureReviewBundle.from_dict(bundle.to_dict()).to_dict() == bundle.to_dict()
    assert ApprovalRecord.from_dict(approval.to_dict()).is_approved is True


def test_validate_replay_spec_and_retention_api() -> None:
    policy = PolicyShieldSnapshot()
    replay_result = run_meta_operation(
        "validate_replay_spec",
        {
            "policy_shield": policy.to_dict(),
            "replay_spec": {
                "sequence_ids": [f"seq-{index}" for index in range(32)],
                "slice_boundaries": [[0, 2048]],
                "objective_bundle_hash": policy.objective_bundle_hash,
            },
        },
    )
    retention_result = run_meta_operation(
        "evaluate_meta_retention",
        {
            "minimum_retention_ratio": 0.5,
            "reference_bundle": {
                "bundle_id": "reference",
                "assertions": [
                    {"object_id": "1", "type_name": "scene", "canonical_name": "Night", "category": "scene", "confidence": 0.9},
                    {"object_id": "2", "type_name": "motif", "canonical_name": "Echo", "category": "motif", "confidence": 0.7},
                ],
            },
            "observed_bundle": {
                "bundle_id": "observed",
                "assertions": [
                    {"object_id": "1", "type_name": "scene", "canonical_name": "Night", "category": "scene", "confidence": 0.9},
                ],
            },
        },
    )

    assert replay_result["status"] == "accepted"
    assert retention_result["status"] == "accepted"
    assert retention_result["retention_ratio"] == 0.5


def test_runtime_state_and_operation_dispatch_round_trip() -> None:
    state = RuntimeState()
    state.l1_witness_summary = {"family_id": "hex6"}
    round_tripped = RuntimeState.from_dict(state.to_dict())
    assert round_tripped.to_dict()["l1_witness_summary"]["family_id"] == "hex6"

    build_result = run_meta_operation(
        "build_meta_object_instance",
        {
            "object_id": "obj-1",
            "type_name": "motif",
            "canonical_name": "Return",
            "category": "motif",
            "confidence": 0.8,
        },
    )
    assert build_result["status"] == "ok"
