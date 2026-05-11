from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repo_mcp_module_exists_and_is_gated():
    content = (ROOT / "app" / "duotronic_runtime" / "repo_mcp.py").read_text()
    assert "XaviRepoTools" in content
    assert "xavi_mcp_repo_tools_enabled" in content
    assert "xavi_repo_approval_secret" in content
    assert "approval_token" in content
    assert "repo.create_worktree" in content
    assert "repo.apply_patch" in content
    assert "repo.run_tests" in content
    assert "repo.prepare_commit" in content
    assert "repo.commit" in content


def test_repo_mcp_has_no_push_or_deploy_tool():
    content = (ROOT / "app" / "duotronic_runtime" / "repo_mcp.py").read_text()
    forbidden = [
        '"repo.push"',
        '"repo.deploy"',
        '"repo.merge"',
        "git push",
        "podman compose",
        "systemctl",
    ]
    for token in forbidden:
        assert token not in content


def test_http_mcp_exposes_repo_tools():
    content = (ROOT / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert "repo_tool_manifest" in content
    assert "repo_resources" in content
    assert "XaviRepoTools" in content
    assert 'tool.startswith("repo.")' in content


def test_repo_mcp_settings_exist():
    content = (ROOT / "app" / "duotronic_runtime" / "config.py").read_text()
    assert "XAVI_MCP_REPO_TOOLS_ENABLED" in content
    assert "XAVI_REPO_ROOT" in content
    assert "XAVI_WORKTREE_ROOT" in content
    assert "XAVI_REPO_APPROVAL_SECRET" in content


def test_containerfile_installs_git():
    content = (ROOT / "Containerfile").read_text()
    assert " git" in content


def test_compose_mounts_repo_for_runtime():
    content = (ROOT / "compose.yaml").read_text()
    assert "/workspace/Duotronics" in content
    assert "XAVI_REPO_ROOT" in content
    assert "XAVI_WORKTREE_ROOT" in content


def test_env_example_documents_repo_mcp_settings():
    content = (ROOT / ".env.example").read_text()
    assert "XAVI_MCP_REPO_TOOLS_ENABLED" in content
    assert "XAVI_REPO_ROOT" in content
    assert "XAVI_WORKTREE_ROOT" in content
    assert "XAVI_REPO_APPROVAL_SECRET" in content
