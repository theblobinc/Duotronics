from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .config import Settings
from .runtime_kernel import RuntimeKernel
from .fusion_center_mcp import call_fusion_tool, fusion_resources, fusion_tool_manifest, read_fusion_resource
from .skill_mcp import call_skill_tool, read_skill_resource, skill_resources, skill_tool_manifest
from .tool_services import ToolRuntime
from .repo_mcp import XaviRepoTools, repo_resources, repo_tool_manifest
from .ops_mcp import XaviOpsTools, ops_tool_manifest
from .dev_bundle_mcp import XaviDevBundleTools, dev_tool_manifest


class McpCallRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


def _require_mcp_key(
    settings: Settings,
    authorization: str | None,
    x_xavi_mcp_key: str | None,
) -> None:
    if not settings.xavi_mcp_enabled:
        raise HTTPException(status_code=404, detail="xavi-runtime MCP is disabled")

    if not settings.xavi_mcp_api_key:
        raise HTTPException(status_code=503, detail="XAVI_MCP_API_KEY is not configured")

    expected = f"Bearer {settings.xavi_mcp_api_key}"
    if authorization == expected or x_xavi_mcp_key == settings.xavi_mcp_api_key:
        return

    raise HTTPException(status_code=401, detail="missing or invalid xavi-runtime MCP credential")


def _safe_limit(args: dict[str, Any], default: int = 20) -> int:
    try:
        value = int(args.get("limit", default))
    except Exception:
        value = default
    return max(1, min(value, 100))


def _tool_manifest() -> list[dict[str, Any]]:
    return [
        {
            "name": "runtime.health",
            "description": "Return runtime health, corpus identity, profile status, model registry, module registry, and formal observer availability.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.models",
            "description": "List configured model providers and defaults.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.capabilities",
            "description": "Return normalized model, provider, tool, modality, and backend capability inventory.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.client_profiles",
            "description": "List stable client route profiles for LibreChat and OpenClaw.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "runtime.client_profile_route",
            "description": "Resolve a named client profile into a read-only inference route.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["profile"],
                "properties": {
                    "profile": {"type": "string", "minLength": 1},
                    "overrides": {"type": "object", "default": {}},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.client_profile_operation",
            "description": "Resolve a named client profile into a witnessed read-only operation plan.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["profile"],
                "properties": {
                    "profile": {"type": "string", "minLength": 1},
                    "overrides": {"type": "object", "default": {}},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.inference_route",
            "description": "Plan a read-only model/tool route for a requested inference task or capability.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "default": "chat"},
                    "capability": {"type": ["string", "null"]},
                    "modalities": {"type": "array", "items": {"type": "string"}, "default": []},
                    "prefer_provider": {"type": ["string", "null"]},
                    "prefer_remote": {"type": "boolean", "default": True},
                    "needs_tools": {"type": "boolean", "default": False},
                    "needs_vision": {"type": "boolean", "default": False},
                    "require_live_backend": {"type": "boolean", "default": False},
                    "max_candidates": {"type": "integer", "minimum": 1, "maximum": 32, "default": 8},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.operation_plan",
            "description": "Plan a read-only logical runtime operation from a goal and intent.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "minLength": 1},
                    "intent": {"type": "string", "default": "logic"},
                    "constraints": {"type": "array", "items": {"type": "string"}, "default": []},
                    "prefer_remote": {"type": "boolean", "default": True},
                    "require_live_backend": {"type": "boolean", "default": False},
                    "max_candidates": {"type": "integer", "minimum": 1, "maximum": 32, "default": 6},
                },
                "required": ["goal"],
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_index",
            "description": "List runtime session ledger sessions and latest digests.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_append",
            "description": "Append an event to the hash-chained runtime session ledger.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["session_id", "event_type", "actor"],
                "properties": {
                    "session_id": {"type": "string", "minLength": 1},
                    "event_type": {"type": "string", "minLength": 1},
                    "actor": {"type": "string", "minLength": 1},
                    "content": {"type": "object", "default": {}},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                    "witness_id": {"type": ["string", "null"]},
                    "supersedes": {"type": "array", "items": {"type": "string"}, "default": []},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_search",
            "description": "Search compact runtime session ledger records by session, tag, event type, actor, tool, or text.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": ["string", "null"]},
                    "query": {"type": ["string", "null"]},
                    "event_type": {"type": ["string", "null"]},
                    "actor": {"type": ["string", "null"]},
                    "tag": {"type": ["string", "null"]},
                    "tool_name": {"type": ["string", "null"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_find",
            "description": "Alias for runtime.session_search.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": ["string", "null"]},
                    "query": {"type": ["string", "null"]},
                    "event_type": {"type": ["string", "null"]},
                    "actor": {"type": ["string", "null"]},
                    "tag": {"type": ["string", "null"]},
                    "tool_name": {"type": ["string", "null"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_tail",
            "description": "Read recent events from a runtime session ledger.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["session_id"],
                "properties": {
                    "session_id": {"type": "string", "minLength": 1},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_summary",
            "description": "Summarize a runtime session ledger.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["session_id"],
                "properties": {"session_id": {"type": "string", "minLength": 1}},
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.session_verify",
            "description": "Verify runtime session ledger hash-chain integrity.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["session_id"],
                "properties": {"session_id": {"type": "string", "minLength": 1}},
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.modules",
            "description": "List registered runtime modules and capabilities.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.memory",
            "description": "Read recent memory cell records.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.witnesses",
            "description": "Read recent NLA and generic evidence witnesses.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.evidence_witnesses",
            "description": "Read recent evidence witness envelopes.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.claims",
            "description": "Read recent evidence claims.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.audit",
            "description": "Read recent audit events.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 100}},
            },
        },
        {
            "name": "runtime.corpus",
            "description": "Inspect active mounted corpus metadata.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.policy",
            "description": "Explain active policy configuration.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.formal_status",
            "description": "Read Lean/Lake/TLA+ observer availability.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "runtime.run_inference",
            "description": "Run a prompt through the SRNN evidence pipeline. Restricted to respond/observe modes.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["prompt"],
                "properties": {
                    "prompt": {"type": "string", "minLength": 1},
                    "steps": {"type": "integer", "minimum": 1, "maximum": 16, "default": 1},
                    "requested_action": {"type": "string", "enum": ["respond", "observe"], "default": "respond"},
                    "model_name": {"type": ["string", "null"]},
                    "evidence_quality": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.72},
                },
            },
        },

        {
            "name": "runtime.wgrnn_status",
            "description": "Inspect WG-RNN recurrent state summary for a namespace.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": ["string", "null"]},
                    "agent_id": {"type": ["string", "null"]},
                    "thread_id": {"type": ["string", "null"]},
                    "include_slots": {"type": "boolean", "default": False},
                },
            },
        },
        {
            "name": "runtime.wgrnn_inspect",
            "description": "Inspect WG-RNN slots, optionally filtered by trust status.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": ["string", "null"]},
                    "agent_id": {"type": ["string", "null"]},
                    "thread_id": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"], "enum": ["empty", "candidate", "quarantine", "promoted", "rejected", None]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 512, "default": 128},
                },
            },
        },
        {
            "name": "runtime.wgrnn_retrieve",
            "description": "Retrieve nearest WG-RNN memory slots for a namespace/query.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 64, "default": 8},
                    "include_empty": {"type": "boolean", "default": False},
                    "user_id": {"type": ["string", "null"]},
                    "agent_id": {"type": ["string", "null"]},
                    "thread_id": {"type": ["string", "null"]},
                },
            },
        },
        {
            "name": "runtime.wgrnn_step",
            "description": "Create a witnessed WG-RNN observation/memory step for a namespace.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["prompt"],
                "properties": {
                    "prompt": {"type": "string", "minLength": 1},
                    "response_text": {"type": "string", "default": ""},
                    "requested_action": {"type": "string", "enum": ["observe", "memory_write", "promote_witness", "external_action"], "default": "observe"},
                    "evidence_quality": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.72},
                    "user_id": {"type": ["string", "null"]},
                    "agent_id": {"type": ["string", "null"]},
                    "thread_id": {"type": ["string", "null"]},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                },
            },
        },
        {
            "name": "runtime.wgrnn_promote",
            "description": "Promote a WG-RNN candidate/quarantined slot and write a witness.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["slot_id"], "properties": {"slot_id": {"type": "integer", "minimum": 0}, "reason": {"type": "string", "default": "manual_promote"}, "user_id": {"type": ["string", "null"]}, "agent_id": {"type": ["string", "null"]}, "thread_id": {"type": ["string", "null"]}}},
        },
        {
            "name": "runtime.wgrnn_reject",
            "description": "Reject a WG-RNN slot and write a witness.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["slot_id"], "properties": {"slot_id": {"type": "integer", "minimum": 0}, "reason": {"type": "string", "default": "manual_reject"}, "user_id": {"type": ["string", "null"]}, "agent_id": {"type": ["string", "null"]}, "thread_id": {"type": ["string", "null"]}}},
        },
        {
            "name": "runtime.wgrnn_quarantine",
            "description": "Quarantine a WG-RNN slot and write a witness.",
            "read_only": False,
            "input_schema": {"type": "object", "required": ["slot_id"], "properties": {"slot_id": {"type": "integer", "minimum": 0}, "reason": {"type": "string", "default": "manual_quarantine"}, "user_id": {"type": ["string", "null"]}, "agent_id": {"type": ["string", "null"]}, "thread_id": {"type": ["string", "null"]}}},
        },
        {
            "name": "runtime.wgrnn_ledger",
            "description": "Read WG-RNN ledger tail for a namespace.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50}, "user_id": {"type": ["string", "null"]}, "agent_id": {"type": ["string", "null"]}, "thread_id": {"type": ["string", "null"]}}},
        },
        {
            "name": "runtime.wgrnn_replay_verify",
            "description": "Verify WG-RNN ledger hash-chain replay integrity for a namespace and write a verification witness.",
            "read_only": False,
            "input_schema": {"type": "object", "properties": {"user_id": {"type": ["string", "null"]}, "agent_id": {"type": ["string", "null"]}, "thread_id": {"type": ["string", "null"]}}},
        },
        *fusion_tool_manifest(),
        *skill_tool_manifest(),
        *repo_tool_manifest(),
        *ops_tool_manifest(),
        *dev_tool_manifest(),
    ]


def _resources(kernel: RuntimeKernel | None = None) -> list[dict[str, str]]:
    return [
        {"uri": "xavi-runtime://health", "name": "Runtime health"},
        {"uri": "xavi-runtime://models", "name": "Model registry"},
        {"uri": "xavi-runtime://modules", "name": "Module registry"},
        {"uri": "xavi-runtime://memory", "name": "Recent memory"},
        {"uri": "xavi-runtime://witnesses", "name": "Recent witnesses"},
        {"uri": "xavi-runtime://claims", "name": "Recent claims"},
        {"uri": "xavi-runtime://audit", "name": "Recent audit events"},
        {"uri": "xavi-runtime://corpus", "name": "Corpus inspection"},
        {"uri": "xavi-runtime://policy", "name": "Policy explanation"},
        {"uri": "xavi-runtime://formal", "name": "Formal observer status"},
        {"uri": "xavi-runtime://wgrnn", "name": "WG-RNN state and slots"},
        *fusion_resources(),
        *skill_resources(kernel.settings.corpus_dir if kernel else None),
        *repo_resources(),
    ]


async def _call_tool(kernel: RuntimeKernel, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool == "runtime.health":
        kernel.migrate()
        return kernel.health()

    if tool == "runtime.models":
        return {"items": kernel.model_provider.registry.list_models()}

    if tool == "runtime.capabilities":
        tools_runtime = ToolRuntime(settings=kernel.settings, kernel=kernel)
        return tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())

    if tool == "runtime.client_profiles":
        from .client_profiles import client_profiles

        return {"schema_version": "client-profiles-v1", "profiles": client_profiles()}

    if tool == "runtime.client_profile_route":
        from .client_profiles import profile_payload
        from .inference_router import plan_inference_route

        profile = str(args.get("profile", "")).strip()
        overrides = args.get("overrides") or {}
        payload = profile_payload(profile, mode="route", overrides=overrides)
        tools_runtime = ToolRuntime(settings=kernel.settings, kernel=kernel)
        report = tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())
        route = plan_inference_route(report, payload)
        return {"schema_version": "client-profile-route-v1", "profile": profile, "payload": payload, "route": route}

    if tool == "runtime.client_profile_operation":
        from .client_profiles import profile_payload
        from .operation_runtime import plan_operation_witnessed

        profile = str(args.get("profile", "")).strip()
        overrides = args.get("overrides") or {}
        payload = profile_payload(profile, mode="operation", overrides=overrides)
        if not payload.get("goal"):
            payload["goal"] = f"Plan runtime operation for profile {profile}"
        tools_runtime = ToolRuntime(settings=kernel.settings, kernel=kernel)
        plan = plan_operation_witnessed(
            tools_runtime,
            payload,
            models=kernel.model_provider.registry.list_models(),
        )
        return {"schema_version": "client-profile-operation-v1", "profile": profile, "payload": payload, "plan": plan}

    if tool == "runtime.inference_route":
        from .inference_router import plan_inference_route

        tools_runtime = ToolRuntime(settings=kernel.settings, kernel=kernel)
        report = tools_runtime.capability_report(models=kernel.model_provider.registry.list_models())
        return plan_inference_route(report, args)

    if tool == "runtime.operation_plan":
        from .operation_runtime import plan_operation_witnessed

        tools_runtime = ToolRuntime(settings=kernel.settings, kernel=kernel)
        return plan_operation_witnessed(
            tools_runtime,
            args,
            models=kernel.model_provider.registry.list_models(),
        )

    if tool == "runtime.modules":
        return kernel.modules.capability_report()

    if tool == "runtime.session_index":
        from .session_ledger import SessionLedger

        return SessionLedger().index()

    if tool == "runtime.session_append":
        from .session_ledger import SessionLedger

        ledger = SessionLedger()
        return ledger.append(
            session_id=str(args.get("session_id", "default")),
            event_type=str(args.get("event_type", "event")),
            actor=str(args.get("actor", "unknown")),
            content=args.get("content") if isinstance(args.get("content"), dict) else {},
            tags=args.get("tags") if isinstance(args.get("tags"), list) else [],
            witness_id=args.get("witness_id"),
            supersedes=args.get("supersedes") if isinstance(args.get("supersedes"), list) else [],
        )

    if tool in {"runtime.session_search", "runtime.session_find"}:
        from .session_ledger import SessionLedger

        return SessionLedger().search(
            session_id=args.get("session_id"),
            query=args.get("query"),
            event_type=args.get("event_type"),
            actor=args.get("actor"),
            tag=args.get("tag"),
            tool_name=args.get("tool_name"),
            limit=_safe_limit(args, default=20),
        )

    if tool == "runtime.session_tail":
        from .session_ledger import SessionLedger

        ledger = SessionLedger()
        return ledger.tail(
            session_id=str(args.get("session_id", "default")),
            limit=_safe_limit(args, default=20),
        )

    if tool == "runtime.session_summary":
        from .session_ledger import SessionLedger

        ledger = SessionLedger()
        return ledger.summary(session_id=str(args.get("session_id", "default")))

    if tool == "runtime.session_verify":
        from .session_ledger import SessionLedger

        ledger = SessionLedger()
        return ledger.verify(session_id=str(args.get("session_id", "default")))

    if tool == "runtime.memory":
        return {"items": kernel.store.fetch_recent("memory_cells", _safe_limit(args))}

    if tool == "runtime.witnesses":
        limit = _safe_limit(args)
        return {
            "items": kernel.store.fetch_recent("nla_activation_witnesses", limit),
            "generic": kernel.store.fetch_recent("evidence_witnesses", limit),
        }

    if tool == "runtime.evidence_witnesses":
        return {"items": kernel.store.fetch_recent("evidence_witnesses", _safe_limit(args))}

    if tool == "runtime.claims":
        return {"items": kernel.store.fetch_recent("evidence_claims", _safe_limit(args))}

    if tool == "runtime.audit":
        return {"items": kernel.store.fetch_recent("audit_events", _safe_limit(args))}

    if tool == "runtime.corpus":
        return kernel.corpus_manager.inspect()

    if tool == "runtime.policy":
        return kernel.policy.explain()

    if tool == "runtime.formal_status":
        return kernel.formal.status()


    if tool == "runtime.wgrnn_status":
        return kernel.wgrnn.snapshot(
            include_slots=bool(args.get("include_slots", False)),
            user_id=args.get("user_id"),
            agent_id=args.get("agent_id"),
            thread_id=args.get("thread_id"),
        )

    if tool == "runtime.wgrnn_inspect":
        snapshot = kernel.wgrnn.snapshot(
            include_slots=False,
            user_id=args.get("user_id"),
            agent_id=args.get("agent_id"),
            thread_id=args.get("thread_id"),
        )
        return {
            "snapshot": snapshot,
            "slots": kernel.wgrnn.inspect_slots(status=args.get("status"), limit=_safe_limit(args, 128)),
        }

    if tool == "runtime.wgrnn_retrieve":
        query = str(args.get("query", "")).strip()
        if not query:
            raise HTTPException(status_code=422, detail="runtime.wgrnn_retrieve requires args.query")
        return kernel.wgrnn.retrieve(
            query,
            top_k=max(1, min(int(args.get("top_k", 8)), 64)),
            include_empty=bool(args.get("include_empty", False)),
            user_id=args.get("user_id"),
            agent_id=args.get("agent_id"),
            thread_id=args.get("thread_id"),
        )

    if tool == "runtime.wgrnn_step":
        prompt = str(args.get("prompt", "")).strip()
        if not prompt:
            raise HTTPException(status_code=422, detail="runtime.wgrnn_step requires args.prompt")
        return kernel.wgrnn_step_witnessed(
            prompt=prompt,
            response_text=str(args.get("response_text", "")),
            requested_action=str(args.get("requested_action", "observe")),
            evidence_quality=float(args.get("evidence_quality", 0.72)),
            user_id=args.get("user_id"),
            agent_id=args.get("agent_id"),
            thread_id=args.get("thread_id"),
            tags=list(args.get("tags", [])),
        )

    if tool == "runtime.wgrnn_promote":
        return kernel.wgrnn_promote_witnessed(slot_id=int(args["slot_id"]), reason=str(args.get("reason", "manual_promote")), user_id=args.get("user_id"), agent_id=args.get("agent_id"), thread_id=args.get("thread_id"))

    if tool == "runtime.wgrnn_reject":
        return kernel.wgrnn_reject_witnessed(slot_id=int(args["slot_id"]), reason=str(args.get("reason", "manual_reject")), user_id=args.get("user_id"), agent_id=args.get("agent_id"), thread_id=args.get("thread_id"))

    if tool == "runtime.wgrnn_quarantine":
        return kernel.wgrnn_quarantine_witnessed(slot_id=int(args["slot_id"]), reason=str(args.get("reason", "manual_quarantine")), user_id=args.get("user_id"), agent_id=args.get("agent_id"), thread_id=args.get("thread_id"))

    if tool == "runtime.wgrnn_ledger":
        return kernel.wgrnn.ledger_tail(limit=max(1, min(int(args.get("limit", 50)), 500)), user_id=args.get("user_id"), agent_id=args.get("agent_id"), thread_id=args.get("thread_id"))

    if tool == "runtime.wgrnn_replay_verify":
        return kernel.wgrnn_replay_verify_witnessed(user_id=args.get("user_id"), agent_id=args.get("agent_id"), thread_id=args.get("thread_id"))

    if tool == "runtime.run_inference":
        prompt = str(args.get("prompt", "")).strip()
        if not prompt:
            raise HTTPException(status_code=422, detail="runtime.run_inference requires args.prompt")

        requested_action = str(args.get("requested_action", "respond"))
        if requested_action not in {"respond", "observe"}:
            raise HTTPException(
                status_code=403,
                detail="MCP runtime.run_inference is restricted to requested_action respond/observe",
            )

        try:
            return await kernel.run_cognition(
                prompt=prompt,
                steps=max(1, min(int(args.get("steps", 1)), 16)),
                requested_action=requested_action,
                model_name=args.get("model_name"),
                evidence_quality=float(args.get("evidence_quality", 0.72)),
            )
        except RuntimeError as exc:
            message = str(exc)
            if "timeout" in message:
                raise HTTPException(status_code=504, detail={"error": "model_provider_timeout", "message": message}) from exc
            if "ollama_" in message or "llama_cpp_" in message:
                raise HTTPException(status_code=502, detail={"error": "model_provider_error", "message": message}) from exc
            raise

    if tool.startswith("fusion.") or tool in {"search_news", "fetch_rss_news", "detect_thermal_anomalies", "check_connectivity", "check_traffic_metrics", "get_outages", "search_internet", "search_leaks", "list_osint_channels", "search_telegram", "get_channel_info", "check_ioc", "get_threat_pulse", "search_threats"}:
        return await call_fusion_tool(tool, args)

    if tool.startswith("skills.") or tool.startswith("runtime.skills_"):
        return await call_skill_tool(kernel.settings.corpus_dir, tool, args)

    if tool.startswith("repo."):
        return await XaviRepoTools(kernel.settings).call(tool, args)

    if tool.startswith("ops."):
        return await XaviOpsTools(kernel.settings).call(tool, args)

    if tool.startswith("dev."):
        return await XaviDevBundleTools(kernel.settings).call(tool, args)

    raise HTTPException(status_code=404, detail=f"unknown xavi-runtime MCP tool: {tool}")


async def _read_resource(kernel: RuntimeKernel, uri: str) -> dict[str, Any]:
    mapping: dict[str, tuple[str, dict[str, Any]]] = {
        "xavi-runtime://health": ("runtime.health", {}),
        "xavi-runtime://models": ("runtime.models", {}),
        "xavi-runtime://modules": ("runtime.modules", {}),
        "xavi-runtime://memory": ("runtime.memory", {"limit": 20}),
        "xavi-runtime://witnesses": ("runtime.witnesses", {"limit": 20}),
        "xavi-runtime://claims": ("runtime.claims", {"limit": 20}),
        "xavi-runtime://audit": ("runtime.audit", {"limit": 20}),
        "xavi-runtime://corpus": ("runtime.corpus", {}),
        "xavi-runtime://policy": ("runtime.policy", {}),
        "xavi-runtime://formal": ("runtime.formal_status", {}),
        "xavi-runtime://wgrnn": ("runtime.wgrnn_status", {"include_slots": True}),
    }

    fusion_resource = await read_fusion_resource(uri)
    if fusion_resource is not None:
        return fusion_resource

    skill_resource = await read_skill_resource(kernel.settings.corpus_dir, uri)
    if skill_resource is not None:
        return skill_resource

    if uri == "xavi-runtime://repo/status":
        return {"uri": uri, "contents": await XaviRepoTools(kernel.settings).call("repo.status", {})}

    if uri == "xavi-runtime://repo/worktrees":
        return {"uri": uri, "contents": await XaviRepoTools(kernel.settings).call("repo.list_worktrees", {})}

    if uri not in mapping:
        raise HTTPException(status_code=404, detail=f"unknown xavi-runtime MCP resource: {uri}")

    tool, args = mapping[uri]
    return {"uri": uri, "contents": await _call_tool(kernel, tool, args)}


def register_xavi_runtime_mcp(app: FastAPI, kernel: RuntimeKernel, settings: Settings) -> None:
    async def mcp_health(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return {
            "status": "ok",
            "app": "xavi-runtime",
            "transport": "http",
            "enabled": settings.xavi_mcp_enabled,
            "tools": len(_tool_manifest()),
            "resources": len(_resources(kernel)),
        }

    async def mcp_tools(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return {"app": "xavi-runtime", "tools": _tool_manifest()}

    async def mcp_resources(
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return {"app": "xavi-runtime", "resources": _resources(kernel)}

    async def mcp_resource_read(
        uri: str = Query(..., min_length=1),
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        return await _read_resource(kernel, uri)

    async def mcp_call(
        req: McpCallRequest,
        authorization: str | None = Header(default=None),
        x_xavi_mcp_key: str | None = Header(default=None),
    ) -> dict[str, Any]:
        _require_mcp_key(settings, authorization, x_xavi_mcp_key)
        result = await _call_tool(kernel, req.tool, req.args)
        return {
            "app": "xavi-runtime",
            "request_id": req.request_id,
            "tool": req.tool,
            "result": result,
        }

    for prefix in ("/xavi-runtime/mcp", "/v1/mcp"):
        app.add_api_route(f"{prefix}/health", mcp_health, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/tools", mcp_tools, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/resources", mcp_resources, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/resources/read", mcp_resource_read, methods=["GET"], tags=["xavi-runtime-mcp"])
        app.add_api_route(f"{prefix}/call", mcp_call, methods=["POST"], tags=["xavi-runtime-mcp"])
