from __future__ import annotations

import asyncio
import json
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
from .coordination import CoordinationService, coordination_tool_manifest
from .session_delegation import SessionDelegationService, session_delegation_tool_manifest
from .project_tasks import ProjectTaskService, project_task_tool_manifest


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


def _autonomy_tool_manifest() -> list[dict[str, Any]]:
    return [
        {"name": "runtime.autonomy_status", "description": "Return the witnessed WG-RNN autonomous learning/self-development stack status and provenance.", "read_only": True, "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "runtime.autonomy_continuation", "description": "Return durable cross-session continuation context from the hash-chained ledger and evaluated trajectories.", "read_only": True, "input_schema": {"type": "object", "required": ["session_id"], "properties": {"session_id": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 80}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_build_trajectory", "description": "Convert a witnessed session event range into an evaluated experience trajectory and candidate WG-RNN learning update.", "read_only": False, "input_schema": {"type": "object", "required": ["session_id"], "properties": {"session_id": {"type": "string", "minLength": 1}, "start_sequence": {"type": ["integer", "null"], "minimum": 1}, "end_sequence": {"type": ["integer", "null"], "minimum": 1}, "outcome": {"type": "object", "default": {}}, "evaluator": {"type": "string", "default": "xavi-autonomy"}, "learn": {"type": "boolean", "default": True}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_ingest_artifact", "description": "Register a file/media artifact with SHA-256 provenance and optionally index derived transcript/text/records for retrieval and training.", "read_only": False, "input_schema": {"type": "object", "required": ["path", "source_kind"], "properties": {"path": {"type": "string", "minLength": 1}, "source_kind": {"type": "string", "minLength": 1}, "derived_text": {"type": ["string", "null"]}, "derived_records": {"type": "array", "items": {"type": "object"}, "default": []}, "metadata": {"type": "object", "default": {}}, "training_eligible": {"type": "boolean", "default": True}, "session_id": {"type": "string", "default": "media-ingest"}}, "additionalProperties": False}},
        {"name": "runtime.datalake_observe", "description": "Record one witnessed observation derived from a file/media artifact in the WG-RNN data lake, optionally contributing a correlated claim observation to consensus.", "read_only": False, "input_schema": {"type": "object", "required": ["artifact_id","source_path","source_digest","observation_kind","statement"], "properties": {"artifact_id":{"type":"string"},"source_path":{"type":"string"},"source_digest":{"type":"string"},"observation_kind":{"type":"string"},"statement":{"type":"string"},"confidence":{"type":"number","minimum":0,"maximum":1,"default":0.7},"observer_id":{"type":"string","default":"wgrnn-datalake"},"observer_kind":{"type":"string","default":"derived_observer"},"independence_group":{"type":["string","null"]},"epistemic_class":{"type":"string","default":"machine_derived"},"metadata":{"type":"object","default":{}},"claim":{"type":["object","null"]},"session_id":{"type":"string","default":"datalake-ingest"}}, "additionalProperties": False}},
        {"name": "runtime.datalake_pattern", "description": "Record a witnessed cross-artifact recurrence, chronology, duplicate, semantic, or multimodal pattern found in the WG-RNN data lake.", "read_only": False, "input_schema": {"type": "object", "required": ["pattern_kind","statement","members"], "properties": {"pattern_kind":{"type":"string"},"statement":{"type":"string"},"members":{"type":"array","items":{"type":"object"}},"confidence":{"type":"number","minimum":0,"maximum":1,"default":0.7},"observer_id":{"type":"string","default":"wgrnn-pattern-engine"},"metadata":{"type":"object","default":{}},"session_id":{"type":"string","default":"datalake-patterns"}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_record_evaluation", "description": "Record witnessed candidate evaluation checks and deterministic Duotronic score projection.", "read_only": False, "input_schema": {"type": "object", "required": ["candidate_id", "checks", "evaluator"], "properties": {"candidate_id": {"type": "string", "minLength": 1}, "checks": {"type": "array", "minItems": 1, "items": {"type": "object"}}, "evaluator": {"type": "string", "minLength": 1}, "environment": {"type": "object", "default": {}}, "session_id": {"type": "string", "default": "autonomous-evaluation"}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_register_candidate", "description": "Register a self-development code candidate with diff, rollback and provenance witnesses.", "read_only": False, "input_schema": {"type": "object", "required": ["objective", "repo_ref", "parent_ref", "diff_digest", "changed_paths"], "properties": {"objective": {"type": "string"}, "repo_ref": {"type": "string"}, "parent_ref": {"type": "string"}, "diff_digest": {"type": "string"}, "changed_paths": {"type": "array", "items": {"type": "string"}}, "rollback_ref": {"type": ["string", "null"]}, "metadata": {"type": "object", "default": {}}, "session_id": {"type": "string", "default": "self-development"}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_promotion_gate", "description": "Evaluate a witnessed recursive-improvement candidate for autonomous operational promotion while keeping theorem/release authority separate.", "read_only": False, "input_schema": {"type": "object", "required": ["candidate", "evaluation", "rollback_ready", "witness_chain_verified"], "properties": {"candidate": {"type": "object"}, "evaluation": {"type": "object"}, "rollback_ready": {"type": "boolean"}, "witness_chain_verified": {"type": "boolean"}, "independent_validation": {"type": "boolean", "default": False}, "authority_witness": {"type": ["string", "null"]}, "session_id": {"type": "string", "default": "self-development"}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_resource_snapshot", "description": "Record a witnessed compute/resource snapshot for any Xavi-connected node.", "read_only": False, "input_schema": {"type": "object", "required": ["node_id", "resources"], "properties": {"node_id": {"type": "string"}, "resources": {"type": "object"}, "services": {"type": "object", "default": {}}, "transport": {"type": "object", "default": {}}, "session_id": {"type": "string", "default": "resource-pool"}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_schedule", "description": "Select available Xavi node resources for a task using witnessed capability snapshots and positive bijective ranking.", "read_only": True, "input_schema": {"type": "object", "properties": {"requirements": {"type": "object", "default": {}}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_build_training_corpus", "description": "Build a reproducible JSONL training corpus from training-eligible witnessed session events with secret capability references rather than credential plaintext.", "read_only": False, "input_schema": {"type": "object", "properties": {"session_ids": {"type": ["array", "null"], "items": {"type": "string"}}, "include_failures": {"type": "boolean", "default": True}, "session_id": {"type": "string", "default": "training-pipeline"}}, "additionalProperties": False}},
        {"name": "runtime.experiment_next", "description": "Select or create WG-RNN's next self-directed falsifiable experiment from unresolved evidence/consensus. This may create an experiment plan but never promotes truth.", "read_only": False, "input_schema": {"type": "object", "properties": {"session_id": {"type": "string", "default": "wg-rnn:self-experimentation"}}, "additionalProperties": False}},
        {"name": "runtime.experiment_propose", "description": "Propose a witnessed WG-RNN self-experiment over a structured candidate claim. Chats, models, search, documents, sensors and benchmarks are peer observer sources.", "read_only": False, "input_schema": {"type": "object", "required": ["subject", "predicate", "object"], "properties": {"subject": {"type": "string", "minLength": 1}, "predicate": {"type": "string", "minLength": 1}, "object": {}, "question": {"type": ["string", "null"]}, "hypothesis": {"type": ["string", "null"]}, "experiment_kind": {"type": "string", "default": "observer_consensus"}, "falsification": {"type": ["string", "null"]}, "observer_plan": {"type": "array", "items": {"type": "string"}}, "minimum_independent_groups": {"type": "integer", "minimum": 1, "maximum": 32, "default": 3}, "min_support_ratio": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.75}, "max_contradiction_ratio": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.20}, "priority": {"type": "integer", "minimum": 0, "maximum": 100, "default": 50}, "origin": {"type": "string", "default": "wg-rnn:self"}, "metadata": {"type": "object", "default": {}}, "session_id": {"type": "string", "default": "wg-rnn:self-experimentation"}}, "additionalProperties": False}},
        {"name": "runtime.experiment_observe", "description": "Record one experiment observation/measurement from an independent truth observer and update claim consensus. Repeated correlated observers must share an independence_group.", "read_only": False, "input_schema": {"type": "object", "required": ["experiment_id", "observer_id", "observer_kind", "independence_group", "stance", "confidence"], "properties": {"experiment_id": {"type": "string", "minLength": 1}, "observer_id": {"type": "string", "minLength": 1}, "observer_kind": {"type": "string", "minLength": 1}, "independence_group": {"type": "string", "minLength": 1}, "stance": {"type": "string", "enum": ["support", "contradict", "uncertain"]}, "confidence": {"type": "number", "minimum": 0, "maximum": 1}, "observation": {"type": ["string", "null"]}, "source_ref": {"type": ["string", "null"]}, "evidence_refs": {"type": "array", "items": {"type": "string"}, "default": []}, "measurement": {"type": "object", "default": {}}, "session_id": {"type": "string", "default": "wg-rnn:self-experimentation"}}, "additionalProperties": False}},
        {"name": "runtime.experiment_complete", "description": "Evaluate a WG-RNN self-experiment against its falsification/quorum rules. Produces supported/disputed/inconclusive/needs-more-evidence status but performs no truth promotion.", "read_only": False, "input_schema": {"type": "object", "required": ["experiment_id"], "properties": {"experiment_id": {"type": "string", "minLength": 1}, "session_id": {"type": "string", "default": "wg-rnn:self-experimentation"}}, "additionalProperties": False}},
        {"name": "runtime.experiments", "description": "List recent WG-RNN self-experiments and their latest result states.", "read_only": True, "input_schema": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50}, "status": {"type": ["string", "null"]}}, "additionalProperties": False}},
        {"name": "runtime.autonomy_secret_capabilities", "description": "List rotatable private capability references known to WG-RNN. This never returns secret plaintext.", "read_only": True, "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "runtime.self_development_policy", "description": "Return the witness-gated autonomous self-development execution policy.", "read_only": True, "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    ]


def _tool_manifest() -> list[dict[str, Any]]:
    return [
        *coordination_tool_manifest(),
        *session_delegation_tool_manifest(),
        *project_task_tool_manifest(),
        *_autonomy_tool_manifest(),
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
            "name": "runtime.transcript_ingest",
            "description": "Ingest a complete sanitized chat/message turn into the hash-chained JSONL and PostgreSQL transcript stores.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["role", "content"],
                "properties": {
                    "session_id": {"type": "string", "minLength": 1},
                    "role": {"type": "string", "enum": ["system", "user", "assistant", "tool", "developer", "unknown"]},
                    "content": {},
                    "actor": {"type": "string", "default": "mcp-client"},
                    "message_id": {"type": ["string", "null"]},
                    "parent_message_id": {"type": ["string", "null"]},
                    "created_at_ms": {"type": ["integer", "null"]},
                    "metadata": {"type": "object", "default": {}},
                    "attachments": {"type": "array", "default": []},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                    "training_eligible": {"type": "boolean", "default": True},
                    "redaction": {"type": "object", "default": {}},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.transcript_search",
            "description": "Search authoritative PostgreSQL transcript events.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": ["string", "null"]},
                    "session_id": {"type": ["string", "null"]},
                    "event_type": {"type": ["string", "null"]},
                    "actor": {"type": ["string", "null"]},
                    "tag": {"type": ["string", "null"]},
                    "training_eligible": {"type": ["boolean", "null"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 20},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.source_begin",
            "description": "Begin an atomic source-code index generation for a repository.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["generation_id", "repository_id"],
                "properties": {
                    "generation_id": {"type": "string", "minLength": 1},
                    "repository_id": {"type": "string", "minLength": 1},
                    "root_path": {"type": ["string", "null"]},
                    "commit_id": {"type": ["string", "null"]},
                    "metadata": {"type": "object", "default": {}},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.source_upsert",
            "description": "Upsert source-code chunks into a staging source generation.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["documents"],
                "properties": {
                    "documents": {"type": "array", "minItems": 1, "maxItems": 100, "items": {"type": "object"}},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.source_finalize",
            "description": "Atomically promote or fail a staged source-code index generation.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["generation_id"],
                "properties": {
                    "generation_id": {"type": "string", "minLength": 1},
                    "status": {"type": "string", "enum": ["completed", "failed"], "default": "completed"},
                    "keep_generations": {"type": "integer", "minimum": 1, "maximum": 10, "default": 2},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.source_search",
            "description": "Search the latest completed source-code indexes.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "repository_id": {"type": ["string", "null"]},
                    "path_prefix": {"type": ["string", "null"]},
                    "training_eligible": {"type": ["boolean", "null"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "preview_chars": {"type": "integer", "minimum": 120, "maximum": 2000, "default": 500},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "runtime.source_get",
            "description": "Retrieve one indexed source chunk in bounded character slices.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "required": ["repository_id", "path"],
                "properties": {
                    "repository_id": {"type": "string", "minLength": 1},
                    "path": {"type": "string", "minLength": 1},
                    "chunk_index": {"type": "integer", "minimum": 0, "default": 0},
                    "generation_id": {"type": ["string", "null"]},
                    "offset": {"type": "integer", "minimum": 0, "default": 0},
                    "max_chars": {"type": "integer", "minimum": 256, "maximum": 10000, "default": 8000}
                },
                "additionalProperties": False
            }
        },
        {
            "name": "runtime.source_status",
            "description": "List current source-code index generations by repository.",
            "read_only": True,
            "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
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
            "name": "runtime.consensus_observe",
            "description": "Submit one independent observer report for a candidate claim. Observer output is evidence, not truth; correlated sources should share an independence_group.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["subject", "predicate", "object", "observer_id"],
                "properties": {
                    "subject": {"type": "string", "minLength": 1},
                    "predicate": {"type": "string", "minLength": 1},
                    "object": {},
                    "observer_id": {"type": "string", "minLength": 1},
                    "observer_kind": {"type": "string", "default": "unknown"},
                    "independence_group": {"type": ["string", "null"]},
                    "stance": {"type": "string", "enum": ["support", "contradict", "uncertain"], "default": "support"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5},
                    "source_ref": {"type": ["string", "null"]},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}, "default": []},
                    "payload": {"type": "object", "default": {}},
                },
            },
        },
        {
            "name": "runtime.consensus_evaluate",
            "description": "Re-evaluate a candidate claim using the latest report per observer and independence-group quorum rules. This can recommend promotion but never promotes automatically.",
            "read_only": False,
            "input_schema": {
                "type": "object",
                "required": ["claim_key"],
                "properties": {
                    "claim_key": {"type": "string", "minLength": 1},
                    "min_independent_groups": {"type": "integer", "minimum": 1, "maximum": 32, "default": 3},
                    "min_support_ratio": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.75},
                    "min_support_weight": {"type": "number", "minimum": 0, "maximum": 32, "default": 1.8},
                    "max_contradiction_ratio": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.20},
                },
            },
        },
        {
            "name": "runtime.consensus_claims",
            "description": "Read recent observer-consensus states and promotion recommendations.",
            "read_only": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                    "promotion_recommended": {"type": ["boolean", "null"]},
                },
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
        {"uri": "xavi-runtime://coordination", "name": "Shared MCP coordination board"},
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
    if tool.startswith(("session.", "delegation.", "worker.")):
        kernel.migrate()
        return await SessionDelegationService(kernel).call(tool, args)

    if tool.startswith("task."):
        kernel.migrate()
        task_result = ProjectTaskService(kernel.store).dispatch(tool, args)
        task_event = task_result.get("event") if isinstance(task_result, dict) else None
        if isinstance(task_event, dict):
            event_args = dict(task_event)
            event_args["session_id"] = args.get("session_id")
            event_args["agent_id"] = args.get("agent_id")
            task_result = dict(task_result)
            task_result["coordination_event"] = CoordinationService(kernel.store, kernel=kernel).dispatch(
                "coordination.event", event_args
            )
        return task_result

    if tool.startswith("coordination."):
        kernel.migrate()
        return CoordinationService(kernel.store, kernel=kernel).dispatch(tool, args)

    if tool == "runtime.health":
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

    if tool == "runtime.autonomy_status":
        return kernel.autonomy.status()

    if tool == "runtime.autonomy_continuation":
        return kernel.autonomy.continuation_context(
            session_id=str(args.get("session_id") or "default"),
            limit=max(1, min(int(args.get("limit", 80)), 200)),
        )

    if tool == "runtime.autonomy_build_trajectory":
        return kernel.autonomy.build_trajectory(
            session_id=str(args.get("session_id") or "default"),
            start_sequence=args.get("start_sequence"),
            end_sequence=args.get("end_sequence"),
            outcome=args.get("outcome") if isinstance(args.get("outcome"), dict) else {},
            evaluator=str(args.get("evaluator") or "xavi-autonomy"),
            learn=bool(args.get("learn", True)),
        )

    if tool == "runtime.experiment_next":
        return kernel.autonomy.next_experiment(
            session_id=str(args.get("session_id") or "wg-rnn:self-experimentation"),
        )

    if tool == "runtime.experiment_propose":
        return kernel.autonomy.propose_experiment(
            subject=str(args.get("subject") or ""),
            predicate=str(args.get("predicate") or ""),
            object_value=args.get("object"),
            question=args.get("question"),
            hypothesis=args.get("hypothesis"),
            experiment_kind=str(args.get("experiment_kind") or "observer_consensus"),
            falsification=args.get("falsification"),
            observer_plan=[str(x) for x in (args.get("observer_plan") or [])] if isinstance(args.get("observer_plan"), list) else None,
            minimum_independent_groups=max(1, min(int(args.get("minimum_independent_groups", 3)), 32)),
            min_support_ratio=max(0.0, min(float(args.get("min_support_ratio", 0.75)), 1.0)),
            max_contradiction_ratio=max(0.0, min(float(args.get("max_contradiction_ratio", 0.20)), 1.0)),
            priority=max(0, min(int(args.get("priority", 50)), 100)),
            origin=str(args.get("origin") or "wg-rnn:self"),
            metadata=args.get("metadata") if isinstance(args.get("metadata"), dict) else {},
            session_id=str(args.get("session_id") or "wg-rnn:self-experimentation"),
        )

    if tool == "runtime.experiment_observe":
        return kernel.autonomy.experiment_observe(
            experiment_id=str(args.get("experiment_id") or ""),
            observer_id=str(args.get("observer_id") or ""),
            observer_kind=str(args.get("observer_kind") or "unknown"),
            independence_group=str(args.get("independence_group") or args.get("observer_id") or "unknown"),
            stance=str(args.get("stance") or "uncertain"),
            confidence=float(args.get("confidence", 0.5)),
            observation=args.get("observation"),
            source_ref=args.get("source_ref"),
            evidence_refs=[str(x) for x in (args.get("evidence_refs") or [])],
            measurement=args.get("measurement") if isinstance(args.get("measurement"), dict) else {},
            session_id=str(args.get("session_id") or "wg-rnn:self-experimentation"),
        )

    if tool == "runtime.experiment_complete":
        return kernel.autonomy.complete_experiment(
            experiment_id=str(args.get("experiment_id") or ""),
            session_id=str(args.get("session_id") or "wg-rnn:self-experimentation"),
        )

    if tool == "runtime.experiments":
        return kernel.autonomy.list_experiments(
            limit=max(1, min(int(args.get("limit", 50)), 200)),
            status=str(args.get("status")) if args.get("status") else None,
        )

    if tool == "runtime.autonomy_ingest_artifact":
        return kernel.autonomy.ingest_artifact(
            path=str(args.get("path") or ""),
            source_kind=str(args.get("source_kind") or "artifact"),
            derived_text=args.get("derived_text"),
            derived_records=args.get("derived_records") if isinstance(args.get("derived_records"), list) else [],
            metadata=args.get("metadata") if isinstance(args.get("metadata"), dict) else {},
            training_eligible=bool(args.get("training_eligible", True)),
            session_id=str(args.get("session_id") or "media-ingest"),
        )

    if tool == "runtime.datalake_observe":
        return kernel.autonomy.record_datalake_observation(
            artifact_id=str(args.get("artifact_id") or ""), source_path=str(args.get("source_path") or ""),
            source_digest=str(args.get("source_digest") or ""), observation_kind=str(args.get("observation_kind") or "observation"),
            statement=str(args.get("statement") or ""), confidence=float(args.get("confidence",0.7)),
            observer_id=str(args.get("observer_id") or "wgrnn-datalake"), observer_kind=str(args.get("observer_kind") or "derived_observer"),
            independence_group=args.get("independence_group"), epistemic_class=str(args.get("epistemic_class") or "machine_derived"),
            metadata=args.get("metadata") if isinstance(args.get("metadata"),dict) else {},
            claim=args.get("claim") if isinstance(args.get("claim"),dict) else None, session_id=str(args.get("session_id") or "datalake-ingest"),
        )

    if tool == "runtime.datalake_pattern":
        return kernel.autonomy.record_datalake_pattern(
            pattern_kind=str(args.get("pattern_kind") or "pattern"), statement=str(args.get("statement") or ""),
            members=args.get("members") if isinstance(args.get("members"),list) else [], confidence=float(args.get("confidence",0.7)),
            observer_id=str(args.get("observer_id") or "wgrnn-pattern-engine"),
            metadata=args.get("metadata") if isinstance(args.get("metadata"),dict) else {}, session_id=str(args.get("session_id") or "datalake-patterns"),
        )

    if tool == "runtime.autonomy_record_evaluation":
        checks = args.get("checks")
        if not isinstance(checks, list) or not checks:
            raise HTTPException(status_code=422, detail="runtime.autonomy_record_evaluation requires nonempty checks")
        return kernel.autonomy.record_evaluation(
            candidate_id=str(args.get("candidate_id") or ""),
            checks=checks,
            evaluator=str(args.get("evaluator") or "xavi-autonomy"),
            environment=args.get("environment") if isinstance(args.get("environment"), dict) else {},
            session_id=str(args.get("session_id") or "autonomous-evaluation"),
        )

    if tool == "runtime.autonomy_register_candidate":
        return kernel.autonomy.register_candidate(
            objective=str(args.get("objective") or ""),
            repo_ref=str(args.get("repo_ref") or ""),
            parent_ref=str(args.get("parent_ref") or ""),
            diff_digest=str(args.get("diff_digest") or ""),
            changed_paths=[str(x) for x in (args.get("changed_paths") or [])],
            rollback_ref=args.get("rollback_ref"),
            session_id=str(args.get("session_id") or "self-development"),
            metadata=args.get("metadata") if isinstance(args.get("metadata"), dict) else {},
        )

    if tool == "runtime.autonomy_promotion_gate":
        return kernel.autonomy.promotion_gate(
            candidate=args.get("candidate") if isinstance(args.get("candidate"), dict) else {},
            evaluation=args.get("evaluation") if isinstance(args.get("evaluation"), dict) else {},
            rollback_ready=bool(args.get("rollback_ready", False)),
            witness_chain_verified=bool(args.get("witness_chain_verified", False)),
            independent_validation=bool(args.get("independent_validation", False)),
            authority_witness=args.get("authority_witness"),
            session_id=str(args.get("session_id") or "self-development"),
        )

    if tool == "runtime.autonomy_resource_snapshot":
        return kernel.autonomy.record_resource_snapshot(
            node_id=str(args.get("node_id") or "unknown"),
            resources=args.get("resources") if isinstance(args.get("resources"), dict) else {},
            services=args.get("services") if isinstance(args.get("services"), dict) else {},
            transport=args.get("transport") if isinstance(args.get("transport"), dict) else {},
            session_id=str(args.get("session_id") or "resource-pool"),
        )

    if tool == "runtime.autonomy_schedule":
        return kernel.autonomy.schedule_task(
            requirements=args.get("requirements") if isinstance(args.get("requirements"), dict) else {},
        )

    if tool == "runtime.autonomy_build_training_corpus":
        session_ids = args.get("session_ids")
        return kernel.autonomy.build_training_corpus(
            session_ids=[str(x) for x in session_ids] if isinstance(session_ids, list) else None,
            include_failures=bool(args.get("include_failures", True)),
            session_id=str(args.get("session_id") or "training-pipeline"),
        )

    if tool == "runtime.autonomy_secret_capabilities":
        return kernel.autonomy.secrets.list()

    if tool == "runtime.self_development_policy":
        return kernel.self_development.execution_policy()

    if tool == "runtime.transcript_ingest":
        from .session_ledger import SessionLedger

        role = str(args.get("role") or "unknown")
        session_id = str(args.get("session_id") or "default")
        actor = str(args.get("actor") or role or "mcp-client")
        metadata = args.get("metadata") if isinstance(args.get("metadata"), dict) else {}
        attachments = args.get("attachments") if isinstance(args.get("attachments"), list) else []
        redaction = args.get("redaction") if isinstance(args.get("redaction"), dict) else {}
        training_eligible = bool(args.get("training_eligible", True))
        event = SessionLedger(store=kernel.store).append(
            session_id=session_id,
            event_type="chat_message",
            actor=actor,
            content={
                "role": role,
                "message_id": args.get("message_id"),
                "parent_message_id": args.get("parent_message_id"),
                "content": args.get("content"),
                "metadata": metadata,
                "attachments": attachments,
            },
            tags=sorted(set(["chat", "transcript", role] + (args.get("tags") if isinstance(args.get("tags"), list) else []))),
            created_at_ms=args.get("created_at_ms"),
            training_eligible=training_eligible,
            redaction=redaction,
        )
        recurrent_learning = None
        if training_eligible:
            try:
                conversation_id = str(metadata.get("conversation_id") or session_id)[:256]
                conversation_source = str(metadata.get("conversation_source") or "mcp")[:80]
                if redaction:
                    observation = {
                        "conversation_id": conversation_id,
                        "conversation_source": conversation_source,
                        "role": role,
                        "actor": actor,
                        "message_id": args.get("message_id"),
                        "event_digest": event.get("event_digest"),
                        "redaction_present": True,
                    }
                else:
                    observation = {
                        "conversation_id": conversation_id,
                        "conversation_source": conversation_source,
                        "role": role,
                        "actor": actor,
                        "message_id": args.get("message_id"),
                        "parent_message_id": args.get("parent_message_id"),
                        "content": args.get("content"),
                        "attachments": attachments,
                        "event_digest": event.get("event_digest"),
                    }
                observed_text = json.dumps(observation, sort_keys=True, default=str)
                if len(observed_text) > 16000:
                    observed_text = observed_text[:16000] + "...[bounded]"
                recurrent_learning = kernel.wgrnn.step(
                    prompt="Observed durable conversation transcript turn: " + observed_text,
                    response_text="",
                    requested_action="observe",
                    evidence_quality=0.82,
                    user_id=f"conversation-source:{conversation_source}",
                    agent_id=actor[:256],
                    thread_id=f"conversation:{conversation_id}",
                    tags=["conversation-transcript", "candidate-training", f"role:{role}", f"conversation-source:{conversation_source}"],
                ).get("memory_update")
            except Exception as exc:
                recurrent_learning = {"status": "error", "error": exc.__class__.__name__}
        return {**event, "recurrent_learning": recurrent_learning}

    if tool == "runtime.transcript_search":
        return kernel.store.search_session_events(
            query=args.get("query"),
            session_id=args.get("session_id"),
            event_type=args.get("event_type"),
            actor=args.get("actor"),
            tag=args.get("tag"),
            training_eligible=args.get("training_eligible"),
            limit=min(max(int(args.get("limit", 20)), 1), 200),
        )

    if tool == "runtime.source_begin":
        return kernel.store.begin_source_generation(
            generation_id=str(args["generation_id"]),
            repository_id=str(args["repository_id"]),
            root_path=args.get("root_path"),
            commit_id=args.get("commit_id"),
            metadata=args.get("metadata") if isinstance(args.get("metadata"), dict) else {},
        )

    if tool == "runtime.source_upsert":
        docs = args.get("documents")
        if not isinstance(docs, list) or not docs:
            raise HTTPException(status_code=422, detail="runtime.source_upsert requires documents")
        return kernel.store.upsert_source_documents(docs)

    if tool == "runtime.source_finalize":
        return kernel.store.finalize_source_generation(
            generation_id=str(args["generation_id"]),
            status=str(args.get("status", "completed")),
            keep_generations=min(max(int(args.get("keep_generations", 2)), 1), 10),
        )

    if tool == "runtime.source_search":
        return kernel.store.search_source_documents(
            query=str(args.get("query") or ""),
            repository_id=args.get("repository_id"),
            path_prefix=args.get("path_prefix"),
            training_eligible=args.get("training_eligible"),
            limit=_safe_limit(args),
            preview_chars=min(max(int(args.get("preview_chars", 500)), 120), 2000),
        )

    if tool == "runtime.source_get":
        return kernel.store.get_source_document(
            repository_id=str(args.get("repository_id") or ""),
            path=str(args.get("path") or ""),
            chunk_index=max(int(args.get("chunk_index", 0)), 0),
            generation_id=args.get("generation_id"),
            offset=max(int(args.get("offset", 0)), 0),
            max_chars=min(max(int(args.get("max_chars", 8000)), 256), 10000),
        )

    if tool == "runtime.source_status":
        return kernel.store.source_index_status()

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

    if tool == "runtime.consensus_observe":
        return kernel.consensus.observe(
            subject=str(args.get("subject") or ""),
            predicate=str(args.get("predicate") or ""),
            object_value=args.get("object"),
            observer_id=str(args.get("observer_id") or ""),
            observer_kind=str(args.get("observer_kind") or "unknown"),
            independence_group=args.get("independence_group"),
            stance=str(args.get("stance") or "support"),
            confidence=float(args.get("confidence", 0.5)),
            source_ref=args.get("source_ref"),
            evidence_refs=list(args.get("evidence_refs") or []),
            payload=args.get("payload") if isinstance(args.get("payload"), dict) else {},
        )

    if tool == "runtime.consensus_evaluate":
        claim_key = str(args.get("claim_key") or "").strip()
        if not claim_key:
            raise HTTPException(status_code=422, detail="runtime.consensus_evaluate requires args.claim_key")
        return kernel.consensus.evaluate(
            claim_key=claim_key,
            min_independent_groups=max(1, min(int(args.get("min_independent_groups", 3)), 32)),
            min_support_ratio=max(0.0, min(float(args.get("min_support_ratio", 0.75)), 1.0)),
            min_support_weight=max(0.0, min(float(args.get("min_support_weight", 1.8)), 32.0)),
            max_contradiction_ratio=max(0.0, min(float(args.get("max_contradiction_ratio", 0.20)), 1.0)),
        )

    if tool == "runtime.consensus_claims":
        promotion_recommended = args.get("promotion_recommended")
        return {
            "schema_version": "observer-consensus-v1",
            "items": kernel.consensus.recent(
                limit=max(1, min(int(args.get("limit", 50)), 200)),
                promotion_recommended=promotion_recommended if isinstance(promotion_recommended, bool) else None,
            ),
        }

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


async def _call_tool_offloop(kernel: RuntimeKernel, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run mixed sync/async MCP tool work outside Uvicorn's main event loop."""
    return await asyncio.to_thread(lambda: asyncio.run(_call_tool(kernel, tool, args)))


async def _read_resource(kernel: RuntimeKernel, uri: str) -> dict[str, Any]:
    mapping: dict[str, tuple[str, dict[str, Any]]] = {
        "xavi-runtime://coordination": ("coordination.status", {"project_key": "xavi.app-backend", "limit": 30}),
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
    return {"uri": uri, "contents": await _call_tool_offloop(kernel, tool, args)}


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
        result = await _call_tool_offloop(kernel, req.tool, req.args)
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
