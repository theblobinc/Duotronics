from __future__ import annotations

from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
ADAPTER = RUNTIME_ROOT / "ops_agent" / "xavi_dev_mcp_adapter.py"
OPS_AGENT = RUNTIME_ROOT / "ops_agent" / "xavi_ops_agent.py"
LOW_LEVEL = RUNTIME_ROOT / "ops_agent" / "v3_maintenance" / "restart_runtime_only.sh"
WRAPPER = Path("/home/tbi/xavi-coordinated-restart-runtime.sh")
ORCHESTRATOR = Path("/home/tbi/xavi-agent-orchestrator.py")


def test_developer_mcp_restart_routes_through_coordination_wrapper() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    assert '["/bin/bash", "/home/tbi/xavi-coordinated-restart-runtime.sh", "Developer MCP restart_runtime_only requested"]' in text


def test_native_ops_restart_routes_through_coordination_wrapper() -> None:
    text = OPS_AGENT.read_text(encoding="utf-8")
    assert 'script = Path("/home/tbi/xavi-coordinated-restart-runtime.sh")' in text
    assert '"cmd": ["/bin/bash", "/home/tbi/xavi-coordinated-restart-runtime.sh", "Native Ops allowed-command runtime restart requested"]' in text


def test_low_level_restart_remains_separate_recovery_primitive() -> None:
    assert LOW_LEVEL.exists()
    low = LOW_LEVEL.read_text(encoding="utf-8")
    assert "podman rm -f duotronic-runtime" in low
    assert "xavi-agent-orchestrator.py" not in low


def test_wrapper_is_fail_closed_and_resource_aware() -> None:
    wrapper = WRAPPER.read_text(encoding="utf-8")
    for resource in (
        "service:xavi-runtime",
        "container:duotronic-runtime",
        "port:127.0.0.1:8080",
        "path:/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
    ):
        assert resource in wrapper
    assert "drain barrier not satisfied; restart deferred" in wrapper
    assert "exit 75" in wrapper
    assert 'notice+=(--resource "$resource")' in wrapper
    assert 'healthy --operation "$OPERATION"' in wrapper
    assert 'failed --operation "$OPERATION"' in wrapper


def test_orchestrator_knows_disruption_lifecycle_and_alternate_work() -> None:
    text = ORCHESTRATOR.read_text(encoding="utf-8")
    for phase in ("draining", "restarting", "healthy", "failed", "cancelled"):
        assert phase in text
    assert "switch to unrelated available work" in text
    assert "blocking_claims" in text
