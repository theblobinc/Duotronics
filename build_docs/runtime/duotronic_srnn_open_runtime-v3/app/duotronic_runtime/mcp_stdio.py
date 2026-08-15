from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from .config import get_settings
from .runtime_kernel import RuntimeKernel

settings = get_settings()
kernel = RuntimeKernel(settings, initialize_schema=True)


def tool_schema(name: str, description: str, properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {"name": name, "description": description, "inputSchema": {"type": "object", "properties": properties or {}, "required": required or []}}


TOOLS = [
    tool_schema("runtime_health", "Return runtime health, corpus reference, modules, providers, and formal observer availability."),
    tool_schema("run_cognition", "Run prompt through model -> WG-RNN -> NLA -> policy -> evidence kernel -> Postgres.", {"prompt": {"type": "string"}, "requested_action": {"type": "string", "default": "observe"}, "steps": {"type": "integer", "default": 1}, "model_name": {"type": "string"}}, ["prompt"]),
    tool_schema("list_witnesses", "List recent witness records.", {"limit": {"type": "integer", "default": 10}}),
    tool_schema("submit_claim", "Submit an evidence claim to the runtime evidence store.", {"subject": {"type": "string"}, "predicate": {"type": "string"}, "object": {}, "claim_kind": {"type": "string"}, "force": {"type": "string"}}, ["subject", "predicate", "object"]),
    tool_schema("query_memory", "List recent WG-RNN memory cells.", {"limit": {"type": "integer", "default": 10}}),
    tool_schema("register_model", "Register a model provider in config/models.json.", {"name": {"type": "string"}, "provider": {"type": "string"}, "model": {"type": "string"}, "base_url": {"type": "string"}}, ["name", "provider"]),
    tool_schema("module_capability_report", "List runtime modules and their declared witness outputs."),
    tool_schema("module_health", "Check a registered module's health endpoint when enabled.", {"module_id": {"type": "string"}}, ["module_id"]),
    tool_schema("corpus_inspect", "Inspect the mounted corpus manifest, digest, files, and derived corpus reference."),
    tool_schema("corpus_ingest", "Scan mounted corpus markdown and store index/version candidate in PostgreSQL."),
    tool_schema("corpus_build_plan", "Generate a corpus activation and implementation plan."),
    tool_schema("policy_explain", "Explain runtime policy and non-collapse rules."),
    tool_schema("formal_status", "Report local availability of Lean, Lake, Java/TLC formal observer tools."),
    tool_schema("self_development_plan", "Create a gated worktree/test/review plan for runtime self-development.", {"task": {"type": "string"}, "repo_ref": {"type": "string"}}, ["task"]),
]


def text_result(obj: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(obj, indent=2, default=str)}]}


async def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "runtime_health":
        return text_result(kernel.health())
    if name == "run_cognition":
        result = await kernel.run_cognition(prompt=str(args.get("prompt", "")), requested_action=str(args.get("requested_action", "observe")), steps=int(args.get("steps", 1)), model_name=args.get("model_name"))
        return text_result(result)
    if name == "list_witnesses":
        limit = int(args.get("limit", 10))
        return text_result({"nla": kernel.store.fetch_recent("nla_activation_witnesses", limit), "generic": kernel.store.fetch_recent("evidence_witnesses", limit)})
    if name == "submit_claim":
        return text_result(kernel.submit_claim(args))
    if name == "query_memory":
        return text_result(kernel.store.fetch_recent("memory_cells", int(args.get("limit", 10))))
    if name == "register_model":
        return text_result(kernel.model_provider.registry.add(args))
    if name == "module_capability_report":
        return text_result(kernel.modules.capability_report())
    if name == "module_health":
        return text_result(await kernel.modules.health(str(args.get("module_id"))))
    if name == "corpus_inspect":
        return text_result(kernel.corpus_manager.inspect())
    if name == "corpus_ingest":
        docs = __import__("duotronic_runtime.corpus_agent", fromlist=["scan_corpus"]).scan_corpus(settings.corpus_dir)
        count = kernel.store.upsert_corpus_docs(docs)
        validation = kernel.corpus_manager.validate()
        if validation.get("inspection", {}).get("status") == "ok":
            kernel.store.upsert_corpus_version(validation["inspection"]["corpus_ref"], validation)
            kernel.store.insert_witness(validation["witness"])
        return text_result({"documents_ingested": count, "validation": validation})
    if name == "corpus_build_plan":
        return text_result(kernel.corpus_plan())
    if name == "policy_explain":
        return text_result(kernel.policy.explain())
    if name == "formal_status":
        return text_result(kernel.formal.status())
    if name == "self_development_plan":
        return text_result(kernel.self_development.plan(task=str(args.get("task", "")), repo_ref=str(args.get("repo_ref", "mounted-workspace"))))
    raise ValueError(f"unknown tool: {name}")


async def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    rid = req.get("id")
    try:
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}, "resources": {}}, "serverInfo": {"name": "duotronic-srnn-runtime-host", "version": "0.2.0"}}}
        if method == "notifications/initialized":
            return None
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
        if method == "tools/call":
            params = req.get("params") or {}
            result = await call_tool(str(params.get("name")), params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": rid, "result": result}
        if method == "resources/list":
            return {"jsonrpc": "2.0", "id": rid, "result": {"resources": [
                {"uri": "duotronic://policy", "name": "Policy explanation", "mimeType": "application/json"},
                {"uri": "duotronic://corpus/plan", "name": "Corpus build plan", "mimeType": "application/json"},
                {"uri": "duotronic://modules", "name": "Module capability report", "mimeType": "application/json"},
            ]}}
        if method == "resources/read":
            uri = (req.get("params") or {}).get("uri")
            if uri == "duotronic://policy":
                data = kernel.policy.explain()
            elif uri == "duotronic://modules":
                data = kernel.modules.capability_report()
            else:
                data = kernel.corpus_plan()
            return {"jsonrpc": "2.0", "id": rid, "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(data, indent=2, default=str)}]}}
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    except Exception as exc:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(exc)}}


async def main() -> None:
    kernel.migrate()
    for line in sys.stdin:
        if not line.strip():
            continue
        resp = await handle(json.loads(line))
        if resp is not None:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
