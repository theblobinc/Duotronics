from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_http_mcp_module_exists():
    content = (ROOT / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert "register_xavi_runtime_mcp" in content
    assert "runtime.health" in content
    assert "runtime.models" in content
    assert "runtime.modules" in content
    assert "runtime.memory" in content
    assert "runtime.witnesses" in content
    assert "runtime.policy" in content
    assert "runtime.corpus" in content
    assert "runtime.run_inference" in content


def test_http_mcp_is_registered_in_api():
    content = (ROOT / "app" / "duotronic_runtime" / "api.py").read_text()
    assert "from .http_mcp import register_xavi_runtime_mcp" in content
    assert "register_xavi_runtime_mcp(app, kernel, settings)" in content


def test_http_mcp_settings_exist():
    content = (ROOT / "app" / "duotronic_runtime" / "config.py").read_text()
    assert "XAVI_MCP_ENABLED" in content
    assert "XAVI_MCP_API_KEY" in content


def test_http_mcp_env_example_documents_settings():
    content = (ROOT / ".env.example").read_text()
    assert "XAVI_MCP_ENABLED" in content
    assert "XAVI_MCP_API_KEY" in content


def test_http_mcp_has_no_repo_edit_tools_yet():
    content = (ROOT / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    forbidden = [
        "repo.apply_patch",
        "repo.commit",
        "repo.push",
        "repo.merge",
        "git commit",
        "git push",
    ]
    for token in forbidden:
        assert token not in content
