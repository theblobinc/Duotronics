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


def test_native_mcp_collaboration_context_defaults_to_include_and_supports_authenticated_omit():
    content = (ROOT / "app" / "duotronic_runtime" / "mcp_protocol.py").read_text()
    assert 'x-xavi-collaboration-context' in content
    assert '_COLLABORATION_OMIT_VALUES = {"omit", "none", "off", "false", "0"}' in content
    assert '_include_collaboration_context(request)' in content
    assert 'if _include_collaboration_context(request) and tool_name not in' in content
    # Authorization remains at the route entry before tools/call/header handling.
    assert content.index('_authorize(settings, authorization, x_xavi_mcp_key, x_api_key)') < content.index('if method == "tools/call"')


def test_session_delegation_service_is_cached_per_runtime_kernel():
    content = (ROOT / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert 'def _session_delegation_service(kernel: RuntimeKernel)' in content
    assert 'getattr(kernel, "_session_delegation_service", None)' in content
    assert 'setattr(kernel, "_session_delegation_service", service)' in content
    assert 'return await _session_delegation_service(kernel).call(tool, args)' in content
    assert 'return await SessionDelegationService(kernel).call(tool, args)' not in content


def test_native_mcp_auto_capture_defaults_on_and_authenticated_service_may_omit_wrapper():
    content = (ROOT / "app" / "duotronic_runtime" / "mcp_protocol.py").read_text()
    assert 'x-xavi-auto-capture' in content
    assert 'def _include_auto_capture(request: Request)' in content
    assert 'capture = _capture_tool(tool_name) and _include_auto_capture(request)' in content
    assert content.index('_authorize(settings, authorization, x_xavi_mcp_key, x_api_key)') < content.index('if method == "tools/call"')
