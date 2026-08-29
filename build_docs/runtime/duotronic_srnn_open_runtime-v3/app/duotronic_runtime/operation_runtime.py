from __future__ import annotations

import time
from typing import Any

from .evidence import shake256_ref
from .operation_planner import plan_operation


def plan_operation_witnessed(tools_runtime: Any, payload: dict[str, Any] | None = None, *, models: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return a read-only operation plan and record an OperationPlanWitness.

    This is the runtime-OS boundary: callers get a deterministic plan while the
    runtime records a compact witness of the decision, selected route, and
    warnings. It does not execute tools or mutate repo/server state.
    """
    model_records = models if models is not None else tools_runtime.kernel.model_provider.registry.list_models()
    report = tools_runtime.capability_report(models=model_records)
    plan = plan_operation(report, payload or {}, service_registry=tools_runtime.kernel.service_registry)
    route = plan.get("route") or {}
    witness_payload = {
        "plan_digest": plan.get("plan_digest"),
        "goal_digest": shake256_ref(str(plan.get("goal") or "")),
        "intent": plan.get("intent"),
        "classified_task": plan.get("classified_task"),
        "execution_mode": plan.get("execution_mode"),
        "route_digest": route.get("route_digest"),
        "selected_route": route.get("selected"),
        "warnings": plan.get("warnings", []),
        "created_at_ms": int(time.time() * 1000),
    }
    witness = tools_runtime.record_witness(
        "OperationPlanWitness",
        witness_payload,
        status="accepted",
        observer_id="operation_planner.local",
    )
    return {"ok": True, "witness": witness, **plan}
