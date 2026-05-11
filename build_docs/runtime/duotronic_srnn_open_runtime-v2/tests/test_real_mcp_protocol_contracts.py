from datetime import datetime, timezone
import json

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



def test_jsonrpc_result_serializes_datetime_payloads():
    from duotronic_runtime.mcp_protocol import _jsonrpc_result

    response = _jsonrpc_result("dt", {"created_at": datetime(2026, 5, 11, tzinfo=timezone.utc)})
    payload = json.loads(response.body)

    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == "dt"
    assert payload["result"]["created_at"].startswith("2026-05-11T00:00:00")


def test_mcp_tool_response_bounds_large_payloads():
    from duotronic_runtime.mcp_protocol import MCP_TEXT_MAX_CHARS, _mcp_tool_response

    payload = _mcp_tool_response({"items": [{"body": "x" * (MCP_TEXT_MAX_CHARS + 5_000)}]})

    assert payload["_meta"]["xaviRuntimeResponseTruncated"] is True
    assert len(payload["content"][0]["text"]) <= MCP_TEXT_MAX_CHARS + 160


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
