from __future__ import annotations

from pathlib import Path

from duotronic_runtime.coordination import CoordinationService


def test_coordination_conflicts_are_exact_resource_only():
    assert CoordinationService._overlap_sql() == "resource_key=%s"


def test_generic_command_cwd_is_context_not_a_resource_claim():
    from xavi_mcp_coordination import _command_resources

    repo_root = Path("/var/www/xavi/Duotronics")
    command = {
        "argv": ["bash", "-lc", "printf 'hello\\n'"],
        "cwd": "/var/www/xavi",
    }
    assert _command_resources(command, repo_root) == []


def test_explicit_exact_file_resource_is_preserved():
    from xavi_mcp_coordination import _command_resources

    repo_root = Path("/var/www/xavi/Duotronics")
    command = {
        "argv": ["bash", "-lc", "printf done"],
        "cwd": "/var/www/xavi",
        "resources": ["path:/var/www/xavi/project/app/api.py"],
    }
    assert _command_resources(command, repo_root) == ["path:/var/www/xavi/project/app/api.py"]


def test_coordination_manifest_describes_parallel_file_awareness():
    from duotronic_runtime.coordination import coordination_tool_manifest

    claim = next(tool for tool in coordination_tool_manifest() if tool["name"] == "coordination.claim")
    description = claim["description"]
    assert "Exact-resource" in description
    assert "parent directories" in description
    assert "do not block parallel work" in description
