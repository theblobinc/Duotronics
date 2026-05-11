from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_real_mcp_protocol_module_exists():
    content = (ROOT / "app" / "duotronic_runtime" / "mcp_protocol.py").read_text()
    assert "register_real_mcp_protocol" in content
    assert 'method == "initialize"' in content
    assert 'method == "tools/list"' in content
    assert 'method == "tools/call"' in content
    assert '"/mcp"' in content
    assert '"/xavi-runtime/mcp"' in content


def test_real_mcp_protocol_is_registered():
    content = (ROOT / "app" / "duotronic_runtime" / "api.py").read_text()
    assert "from .mcp_protocol import register_real_mcp_protocol" in content
    assert "register_real_mcp_protocol(app, kernel, settings)" in content


def test_real_mcp_protocol_exposes_existing_tools():
    content = (ROOT / "app" / "duotronic_runtime" / "mcp_protocol.py").read_text()
    assert "_tool_manifest" in content
    assert "_call_tool" in content
    assert "structuredContent" in content
    assert "inputSchema" in content


def test_real_mcp_protocol_has_no_raw_shell():
    content = (ROOT / "app" / "duotronic_runtime" / "mcp_protocol.py").read_text()
    forbidden = [
        "shell=True",
        "subprocess.",
        "os.system",
        "podman compose",
        "systemctl",
    ]
    for token in forbidden:
        assert token not in content
