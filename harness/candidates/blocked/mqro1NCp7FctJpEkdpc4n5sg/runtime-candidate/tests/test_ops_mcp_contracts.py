from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ops_agent_exists_and_has_allowlisted_commands():
    content = (ROOT / "ops_agent" / "xavi_ops_agent.py").read_text()
    assert "ALLOWED_COMMANDS" in content
    assert "ops.runtime_rebuild" in content
    assert "ops.runtime_restart" in content
    assert "ops.runtime_tests" in content
    assert "ops.git_push" in content
    assert "raw_shell_enabled" in content
    assert "False" in content


def test_ops_mcp_proxy_exists():
    content = (ROOT / "app" / "duotronic_runtime" / "ops_mcp.py").read_text()
    assert "XaviOpsTools" in content
    assert "ops_tool_manifest" in content
    assert "ops.runtime_rebuild" in content
    assert "xavi_ops_api_key" in content


def test_http_mcp_exposes_ops_tools():
    content = (ROOT / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert "ops_tool_manifest" in content
    assert "XaviOpsTools" in content
    assert 'tool.startswith("ops.")' in content


def test_ops_settings_exist():
    content = (ROOT / "app" / "duotronic_runtime" / "config.py").read_text()
    assert "XAVI_OPS_ENABLED" in content
    assert "XAVI_OPS_URL" in content
    assert "XAVI_OPS_API_KEY" in content


def test_ops_env_example_documents_settings():
    content = (ROOT / ".env.example").read_text()
    assert "XAVI_OPS_ENABLED" in content
    assert "XAVI_OPS_URL" in content
    assert "XAVI_OPS_API_KEY" in content


def test_ops_agent_systemd_unit_exists():
    content = (ROOT / "systemd" / "xavi-runtime-ops-agent.service").read_text()
    assert "Xavi Runtime Host Ops Agent" in content
    assert "EnvironmentFile=" in content
    assert "xavi_ops_agent" in content


def test_no_unrestricted_shell_endpoint():
    content = (ROOT / "ops_agent" / "xavi_ops_agent.py").read_text()
    forbidden = [
        "shell=True",
        "raw_shell",
        "subprocess.Popen",
        "os.system",
    ]
    for token in forbidden:
        if token == "raw_shell":
            assert "raw_shell_enabled" in content
        else:
            assert token not in content


def test_developer_ops_unrestricted_mode_and_direct_runtime_restart():
    root = Path(__file__).resolve().parents[1]
    adapter = (root / "ops_agent/xavi_dev_mcp_adapter.py").read_text()
    ops_agent = (root / "ops_agent/xavi_ops_agent.py").read_text()

    assert 'SERVER_VERSION = "0.3.3-dev-unrestricted"' in adapter
    assert '"XAVI_DEV_MCP_UNRESTRICTED", "1"' in adapter
    preflight = adapter.split('def _coordination_preflight(', 1)[1].split('def _coordination_notice', 1)[0]
    assert 'return None' in preflight
    assert 'coordination.preflight' not in preflight
    assert 'fetch_json(RUNTIME_URL + "/health", timeout=3)' in adapter
    assert '["systemctl", "--user", "restart", "xavi-duotronic-runtime.service"]' in adapter
    assert '["systemctl", "--user", "restart", "xavi-duotronic-runtime.service"]' in ops_agent

    runtime_unit = Path("/home/tbi/.config/systemd/user/xavi-duotronic-runtime.service").read_text()
    assert "Type=simple" in runtime_unit
    assert "xavi-core-stack-supervisor.sh runtime" in runtime_unit
    assert "Restart=always" in runtime_unit
    assert "KillMode=control-group" in runtime_unit


def test_runtime_mcp_dispatch_isolated_from_health_event_loop():
    root = Path(__file__).resolve().parents[1]
    protocol = (root / "app/duotronic_runtime/mcp_protocol.py").read_text()
    http_mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()
    api = (root / "app/duotronic_runtime/api.py").read_text()

    assert "async def _handle_mcp_inner(" in protocol
    assert "return await asyncio.to_thread(" in protocol
    assert "lambda: asyncio.run(" in protocol
    assert "async def _call_tool_offloop(" in http_mcp
    assert "asyncio.to_thread(lambda: asyncio.run(_call_tool(kernel, tool, args)))" in http_mcp
    assert "result = await _call_tool_offloop(kernel, req.tool, req.args)" in http_mcp
    assert 'async def health() -> dict[str, Any]:' in api


def test_health_is_lightweight_and_inventory_is_separate():
    root = Path(__file__).resolve().parents[1]
    kernel = (root / "app/duotronic_runtime/runtime_kernel.py").read_text()
    api = (root / "app/duotronic_runtime/api.py").read_text()
    http_mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()
    protocol = (root / "app/duotronic_runtime/mcp_protocol.py").read_text()
    adapter = (root / "ops_agent/xavi_dev_mcp_adapter.py").read_text()

    snapshot = kernel.split("self._health_snapshot = {", 1)[1].split("    def migrate", 1)[0]
    assert '"models_count"' in snapshot
    assert '"modules_count"' in snapshot
    assert '"models": self.model_provider.registry.list_models()' not in snapshot
    assert '"modules": self.modules.list()' not in snapshot
    assert '@app.get("/v1/models/registry")' in api
    assert 'if tool == "runtime.health":\n        return kernel.health()' in http_mcp
    assert '"runtime.health",' in protocol.split("_AUTO_CAPTURE_EXACT", 1)[1].split("}", 1)[0]
    assert '"runtime.health", "runtime.models", "runtime.modules"' in protocol
    assert 'RUNTIME_URL + "/v1/models/registry"' in adapter


def test_conversation_identity_is_first_class_and_training_scoped():
    root = Path(__file__).resolve().parents[1]
    adapter = (root / "ops_agent/xavi_dev_mcp_adapter.py").read_text()
    adapter_identity = (root / "ops_agent/xavi_conversation_identity.py").read_text()
    protocol = (root / "app/duotronic_runtime/mcp_protocol.py").read_text()
    runtime_identity = (root / "app/duotronic_runtime/conversation_identity.py").read_text()
    http_mcp = (root / "app/duotronic_runtime/http_mcp.py").read_text()
    autonomy = (root / "app/duotronic_runtime/autonomy_stack.py").read_text()

    assert "conversation_schema_properties" in adapter
    assert '"conversation_id"' in adapter_identity
    assert '"source_conversation_id"' in adapter_identity
    assert '"continued_from_conversation_id"' in adapter_identity
    assert '"transport-session-provisional"' in adapter_identity
    assert '"conversation_identity.sqlite3"' in adapter_identity
    assert '/datastore2/xavi/data/mcp_conversations' in adapter_identity
    assert 'ledger_session_id = str(sanitized.get("conversation_id") or ctx["session_id"])' in adapter
    assert '"transport_session_id": ctx["session_id"]' in adapter

    assert "conversation_schema_properties" in protocol
    assert "resolve_conversation" in protocol
    assert 'ledger_session_id = conversation.get("conversation_id") or context["session_id"]' in protocol
    assert 'arguments["session_id"] = conversation["conversation_id"]' in protocol
    assert '"conversation_id"' in runtime_identity

    assert '"required": ["role", "content"]' in http_mcp
    assert 'prompt="Observed durable conversation transcript turn: "' in http_mcp
    assert 'thread_id=f"conversation:{conversation_id}"' in http_mcp
    assert 'thread_id=(f"conversation:{str(payload.get(\'conversation_id\'))[:256]}"' in autonomy


def test_developer_ops_coordination_is_observability_not_gate():
    adapter = (ROOT / "ops_agent/xavi_dev_mcp_adapter.py").read_text()
    preflight = adapter.split('def _coordination_preflight(', 1)[1].split('def _coordination_notice', 1)[0]
    assert 'return None' in preflight
    assert 'coordination.preflight' not in preflight
    assert 'Mutating MCP call refused because the shared coordination service is unavailable.' in adapter
    # The old refusal branch remains unreachable compatibility code; preflight itself never produces a gate.
