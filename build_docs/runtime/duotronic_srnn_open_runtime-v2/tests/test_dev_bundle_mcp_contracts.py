from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dev_bundle_module_exists_and_exposes_tool():
    content = (ROOT / "app" / "duotronic_runtime" / "dev_bundle_mcp.py").read_text()
    assert "XaviDevBundleTools" in content
    assert "dev_tool_manifest" in content
    assert "dev.apply_change_bundle" in content
    assert "create_worktree" in content
    assert "apply_patch" in content
    assert "run_tests" in content
    assert "prepare_commit" in content
    assert "prepare_integration" in content
    assert "integrate_commit" in content


def test_dev_bundle_is_wired_into_http_mcp():
    content = (ROOT / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert "from .dev_bundle_mcp import XaviDevBundleTools, dev_tool_manifest" in content
    assert "*dev_tool_manifest()" in content
    assert 'tool.startswith("dev.")' in content


def test_dev_bundle_supports_push_and_rebuild_flags_without_raw_shell():
    content = (ROOT / "app" / "duotronic_runtime" / "dev_bundle_mcp.py").read_text()
    assert "ops.git_push" in content
    assert "ops.runtime_rebuild" in content or "ops.runtime_rebuild_models" in content
    forbidden = ["shell=True", "os.system", "subprocess.", "podman compose", "systemctl"]
    for token in forbidden:
        assert token not in content


def test_dev_bundle_schema_has_single_bundle_shape():
    content = (ROOT / "app" / "duotronic_runtime" / "dev_bundle_mcp.py").read_text()
    for token in ["patch", "message", "push", "rebuild", "cleanup", "test_timeout_seconds"]:
        assert token in content
