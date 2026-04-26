from runtime_ref.api import run_meta_operation


def test_rho_kernel_hybrid_step_is_bounded_and_diagnostic() -> None:
    result = run_meta_operation(
        "step_rho_memory_kernel",
        {
            "trace": {"family": "motif_recurrence", "history": {"callback": [0.2, 0.4, 0.1]}},
            "deltas": {"callback": 0.3},
            "config": {"enabled": True, "scope": "worker", "memory_mode": "hybrid", "beta": 0.18},
        },
    )

    assert result["status"] == "accepted"
    assert result["updates"]["callback"] == 0.403441
    assert result["diagnostics"]["callback"]["decay"] == 0.56984


def test_rho_kernel_rejects_canonical_scope_without_promotion() -> None:
    result = run_meta_operation(
        "step_rho_memory_kernel",
        {
            "trace": {"history": {"callback": [0.2]}},
            "deltas": {"callback": 0.3},
            "config": {"enabled": True, "scope": "canonical", "memory_mode": "hybrid"},
        },
    )

    assert result["status"] == "rejected"
    assert "canonical_scope_requires_explicit_promotion" in result["failure_reasons"]
