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
    assert "ops.v3_server_snapshot" in content
    assert "ops.v3_ollama_ports" in content
    assert "ops.v3_ollama_proxy_status" in content
    assert "False" in content


def test_ops_mcp_proxy_exists():
    content = (ROOT / "app" / "duotronic_runtime" / "ops_mcp.py").read_text()
    assert "XaviOpsTools" in content
    assert "ops_tool_manifest" in content
    assert "ops.runtime_rebuild" in content
    assert "xavi_ops_api_key" in content
    assert "ops.v3_server_snapshot" in content
    assert "ops.v3_ollama_ports" in content


def test_ops_agent_v3_observability_settings_exist():
    content = (ROOT / "ops_agent" / "xavi_ops_agent.py").read_text()
    assert "XAVI_OPS_V3_OLLAMA_PROXY_URL" in content
    assert "XAVI_OPS_V3_OLLAMA_PROBE_PORTS" in content
    assert "sanitized_runtime_env" in content


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
