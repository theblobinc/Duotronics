from __future__ import annotations

import json
from typing import Any

from .evidence import sha256_ref
from .inference_router import plan_inference_route

INTENT_TASKS = {
    "chat": "chat",
    "answer": "chat",
    "code": "code_generation",
    "edit_code": "code_generation",
    "run_code": "code_interpreter",
    "vision": "vision",
    "ocr": "document_ocr",
    "image": "image_generation",
    "embed": "embeddings",
    "logic": "logic",
    "witness_contract": "witness_contract",
}


def classify_task(goal: str, intent: str = "logic") -> str:
    if intent in INTENT_TASKS:
        return INTENT_TASKS[intent]
    text = goal.lower()
    if "image" in text or "screenshot" in text or "ocr" in text:
        return "image_generation" if "generate" in text else "vision"
    if "embed" in text or "vector" in text:
        return "embeddings"
    if "run" in text or "interpreter" in text:
        return "code_interpreter"
    if "code" in text or "repo" in text or "patch" in text:
        return "code_generation"
    return "logic"


def plan_operation(report: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    goal = str(payload.get("goal") or payload.get("task") or "").strip()
    intent = str(payload.get("intent") or "logic")
    task = classify_task(goal, intent)
    route = plan_inference_route(
        report,
        {
            "task": task,
            "prefer_remote": bool(payload.get("prefer_remote", True)),
            "require_live_backend": bool(payload.get("require_live_backend", False)),
            "needs_tools": task in {"code_generation", "witness_contract"},
            "needs_vision": task in {"vision", "document_ocr"},
            "max_candidates": int(payload.get("max_candidates", 6)),
        },
    )
    steps = [
        {"id": "observe_goal", "kind": "observation", "read_only": True},
        {"id": "select_route", "kind": "route_selection", "read_only": True, "route_digest": route.get("route_digest")},
        {"id": "check_contract", "kind": "contract_check", "read_only": True, "selected": route.get("selected")},
        {"id": "return_plan", "kind": "plan_summary", "read_only": True},
    ]
    warnings = list(route.get("warnings") or [])
    if not goal:
        warnings.append("empty_goal")
    out = {
        "schema_version": "operation-plan-v1",
        "goal": goal,
        "intent": intent,
        "classified_task": task,
        "execution_mode": "planned_only",
        "route": route,
        "steps": steps,
        "expected_witnesses": ["OperationPlanWitness"],
        "warnings": sorted(set(warnings)),
    }
    out["plan_digest"] = sha256_ref(json.dumps(out, sort_keys=True, default=str))
    return out
