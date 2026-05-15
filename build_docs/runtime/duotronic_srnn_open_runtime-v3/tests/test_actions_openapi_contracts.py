from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_actions_api_module_exists():
    content = (ROOT / "app" / "duotronic_runtime" / "actions_api.py").read_text()
    assert "register_xavi_runtime_actions" in content
    assert '"/openapi.json"' in content
    assert '"/xavi-runtime/actions/openapi.json"' in content
    assert "repoCreateWorktree" in content
    assert "opsRuntimeRebuild" in content
    assert "runtimeRunInference" in content


def test_actions_api_is_registered_and_fastapi_openapi_moved():
    content = (ROOT / "app" / "duotronic_runtime" / "api.py").read_text()
    assert "from .actions_api import register_xavi_runtime_actions" in content
    assert "register_xavi_runtime_actions(app, kernel, settings)" in content
    assert 'openapi_url="/fastapi/openapi.json"' in content


def test_actions_schema_does_not_expose_raw_shell():
    content = (ROOT / "app" / "duotronic_runtime" / "actions_api.py").read_text()
    forbidden = [
        "shell=True",
        "raw_shell",
        "os.system",
        "subprocess.",
        "podman compose",
        "systemctl",
    ]
    for token in forbidden:
        assert token not in content


def test_actions_schema_has_bearer_auth():
    content = (ROOT / "app" / "duotronic_runtime" / "actions_api.py").read_text()
    assert "bearerAuth" in content
    assert '"scheme": "bearer"' in content
