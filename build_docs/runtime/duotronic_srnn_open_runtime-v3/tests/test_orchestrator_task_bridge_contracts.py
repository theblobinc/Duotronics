from __future__ import annotations

import importlib.util
from pathlib import Path


ORCHESTRATOR = Path("/home/tbi/xavi-agent-orchestrator.py")


def _load():
    spec = importlib.util.spec_from_file_location("xavi_agent_orchestrator_bridge_test", ORCHESTRATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _context():
    return {
        "workers": [{
            "worker_id": "worker:wgrnn-main",
            "status": "idle",
            "capabilities": ["analysis", "coordination"],
            "allowed_tools": ["runtime.node_pressure", "runtime.service_candidates"],
        }],
        "wgrnn_delegations": [],
    }


def test_native_tool_envelope_is_unwrapped():
    mod = _load()
    mod._rpc = lambda *a, **k: {
        "content": [{"type": "text", "text": '{"_conversation":{},"result":{"value":7},"_collaboration":{}}'}]
    }
    assert mod.call("runtime.health") == {"value": 7}


def test_context_digest_uses_shake256_512_not_sha256():
    source = ORCHESTRATOR.read_text()
    assert '"shake256-512:" + hashlib.shake_256(encoded).hexdigest(64)' in source
    assert '"sha256:" + hashlib.sha256(encoded).hexdigest()' not in source


def test_bridge_claims_only_explicit_allowlisted_contract_and_completes_matching_run():
    mod = _load()
    calls = []

    task = {
        "task_id": "11111111-1111-4111-8111-111111111111",
        "task_kind": "functionality",
        "title": "Observe pressure",
        "objective": "Observe LAN node pressure",
        "priority": 70,
        "required_capabilities": ["analysis"],
        "work_id": None,
        "context": {
            "wgrnn_delegation": {
                "tool_name": "runtime.node_pressure",
                "tool_args": {"timeout_seconds": 0.5},
                "resource_hints": {
                    "role": "gpu-inference",
                    "service": "ollama",
                    "prefer_gpu": True,
                    "require_live": True,
                },
            }
        },
    }

    def fake_call(name, args=None, timeout=30.0):
        args = args or {}
        calls.append((name, args, timeout))
        if name == "task.claim_next":
            assert args["require_wgrnn_contract"] is True
            assert args["allowed_tools"] == ["runtime.node_pressure", "runtime.service_candidates"]
            assert args["capabilities"] == ["analysis", "coordination"]
            return {"task": task, "claim_token": "claim-token-1", "expired_claims_requeued": 0}
        if name == "delegation.assign":
            assert args["tool_name"] == "runtime.node_pressure"
            assert args["resource_hints"]["task_id"] == task["task_id"]
            assert args["resource_hints"]["task_claim_token"] == "claim-token-1"
            assert args["payload"]["task_bridge"]["claim_token"] == "claim-token-1"
            return {
                "delegation_id": "22222222-2222-4222-8222-222222222222",
                "work_id": "33333333-3333-4333-8333-333333333333",
                "resource_hints": {
                    "scheduler": {
                        "selected": {"node_id": "tbi-production-3"},
                        "pressure_observation_digest": "node-pressure_test",
                    }
                },
            }
        if name == "worker.wgrnn_tick":
            return {"processed": [{
                "delegation_id": "22222222-2222-4222-8222-222222222222",
                "status": "completed",
                "result_digest": "shake256-512:abc",
                "learning": {"witnessed": True, "trajectory_id": "trajectory-1"},
                "scheduler": {
                    "selected": {"node_id": "tbi-production-3"},
                    "pressure_observation_digest": "node-pressure_test",
                },
            }]}
        if name == "task.update":
            assert args["status"] == "completed"
            assert args["claim_token"] == "claim-token-1"
            assert args["work_id"] == "33333333-3333-4333-8333-333333333333"
            assert args["result"]["delegation_id"] == "22222222-2222-4222-8222-222222222222"
            assert args["result"]["selected_node_id"] == "tbi-production-3"
            assert args["result"]["pressure_observation_digest"] == "node-pressure_test"
            return {"task": {**task, "status": "completed"}}
        raise AssertionError(name)

    mod.call = fake_call
    result = mod.bridge_ready_task_to_wgrnn(_context())
    assert result["status"] == "completed"
    assert [name for name, _, _ in calls] == ["task.claim_next", "delegation.assign", "worker.wgrnn_tick", "task.update"]


def test_bridge_releases_defensively_if_claimed_tool_is_not_currently_allowed():
    mod = _load()
    updates = []
    bad_task = {
        "task_id": "44444444-4444-4444-8444-444444444444",
        "task_kind": "context",
        "title": "Bad contract",
        "objective": "Should never execute",
        "priority": 10,
        "required_capabilities": [],
        "context": {"wgrnn_delegation": {"tool_name": "runtime.forbidden"}},
    }

    def fake_call(name, args=None, timeout=30.0):
        args = args or {}
        if name == "task.claim_next":
            return {"task": bad_task, "claim_token": "claim-token-2"}
        if name == "task.update":
            updates.append(args)
            return {"task": {**bad_task, "status": "ready"}}
        raise AssertionError(f"unexpected execution call: {name}")

    mod.call = fake_call
    result = mod.bridge_ready_task_to_wgrnn(_context())
    assert result["status"] == "released"
    assert result["reason"] == "tool_not_in_wgrnn_allowlist"
    assert updates and updates[0]["status"] == "ready"


def test_bridge_does_not_claim_when_worker_already_has_delegation():
    mod = _load()
    mod.call = lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not claim"))
    context = _context()
    context["wgrnn_delegations"] = [{"delegation_id": "busy"}]
    result = mod.bridge_ready_task_to_wgrnn(context)
    assert result["status"] == "skipped"
    assert result["reason"] == "worker_queue_not_empty"


def test_orchestrator_requests_compact_native_mcp_responses():
    content = ORCHESTRATOR.read_text()
    assert '"x-xavi-collaboration-context": "omit"' in content
    assert '"x-xavi-mcp-key": key' in content


def test_orchestrator_omits_redundant_generic_mcp_auto_capture():
    content = ORCHESTRATOR.read_text()
    assert '"x-xavi-auto-capture": "omit"' in content
    assert '"x-xavi-collaboration-context": "omit"' in content
    assert '"x-xavi-mcp-key": key' in content


def test_orchestrator_does_not_override_governed_wgrnn_scheduling_capabilities():
    content = ORCHESTRATOR.read_text()
    assert '"capabilities": ["coordination-observation"' not in content
    assert '"orchestrator_features": ["coordination-observation"' in content
    assert 'worker.register_wgrnn' in content
