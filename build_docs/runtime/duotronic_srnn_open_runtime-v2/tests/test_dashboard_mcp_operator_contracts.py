from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_has_mcp_operator_panel():
    html = (ROOT / "app" / "duotronic_runtime" / "static" / "index.html").read_text()
    assert "Repo operator / MCP" in html
    assert 'id="mcp-key"' in html
    assert 'id="repo-worktree-id"' in html
    assert 'id="repo-patch"' in html
    assert 'id="repo-prepare-integration-btn"' in html
    assert 'id="repo-integrate-btn"' in html
    assert "Push/deploy are intentionally not exposed" in html


def test_dashboard_js_calls_mcp_repo_tools():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "xavi_mcp_api_key" in js
    assert "/xavi-runtime/mcp/call" in js
    assert "repo.create_worktree" in js
    assert "repo.apply_patch" in js
    assert "repo.run_tests" in js
    assert "repo.prepare_commit" in js
    assert "repo.commit" in js
    assert "repo.prepare_integration" in js
    assert "repo.integrate_commit" in js
    assert "repo.remove_worktree" in js


def test_dashboard_does_not_add_push_or_deploy_buttons():
    html = (ROOT / "app" / "duotronic_runtime" / "static" / "index.html").read_text()
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    forbidden = [
        "repo.push",
        "repo.deploy",
        "git push",
        "podman compose",
        "systemctl",
        'id="repo-push-btn"',
        'id="repo-deploy-btn"',
    ]
    for token in forbidden:
        assert token not in html
        assert token not in js
