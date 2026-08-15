from __future__ import annotations

import json
import os
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ops_agent" / "xavi_dev_mcp_adapter.py"
OPS_AGENT = ROOT / "ops_agent" / "xavi_ops_agent.py"
API = ROOT / "app" / "duotronic_runtime" / "api.py"
HTTP_MCP = ROOT / "app" / "duotronic_runtime" / "http_mcp.py"
MCP_PROTOCOL = ROOT / "app" / "duotronic_runtime" / "mcp_protocol.py"
KERNEL = ROOT / "app" / "duotronic_runtime" / "runtime_kernel.py"
RUNTIME_UNIT = Path.home() / ".config" / "systemd" / "user" / "xavi-duotronic-runtime.service"
CACHE = ROOT / "data" / "cache" / "runtime_mcp_tools.json"


def env_value(name: str) -> str:
    path = ROOT / ".env"
    if not path.exists():
        return ""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


class FastPathStandaloneSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = ADAPTER.read_text()
        cls.ops_agent = OPS_AGENT.read_text()
        cls.api = API.read_text()
        cls.http_mcp = HTTP_MCP.read_text()
        cls.protocol = MCP_PROTOCOL.read_text()
        cls.kernel = KERNEL.read_text()

    def test_development_unrestricted_contract(self) -> None:
        self.assertIn('SERVER_VERSION = "0.3.3-dev-unrestricted"', self.adapter)
        self.assertIn('"XAVI_DEV_MCP_UNRESTRICTED", "1"', self.adapter)
        self.assertIn("if DEV_OPS_UNRESTRICTED:\n        return None", self.adapter)
        # Privileged network boundary remains authenticated even while internal
        # coordination/security vetoes are disabled for development.
        self.assertIn("def _ops_request_authorized", self.adapter)
        self.assertIn("hmac.compare_digest(supplied, OPS_KEY)", self.adapter)

    def test_schema_fast_path_and_persisted_cache(self) -> None:
        for token in (
            "TOOLS_CACHE_TTL",
            "TOOLS_REFRESH_TIMEOUT",
            "_schedule_runtime_tools_refresh",
            "_RUNTIME_TOOLS_CACHE",
            "_MERGED_TOOLS_CACHE",
            "TOOLS_CACHE_PATH",
            "_save_runtime_tools_disk_cache",
            "_load_runtime_tools_disk_cache",
        ):
            self.assertIn(token, self.adapter)
        if CACHE.exists():
            payload = json.loads(CACHE.read_text())
            self.assertGreater(len(payload.get("tools") or []), 0)

    def test_deferred_bookkeeping_and_bounded_subprocess_capture(self) -> None:
        for token in (
            "_LEDGER_QUEUE",
            "_COLLAB_QUEUE",
            "_COORD_EVENT_QUEUE",
            "tempfile.TemporaryFile()",
            "RUN_FIXED_OUTPUT_BYTES",
            "_read_capped_temp",
        ):
            self.assertIn(token, self.adapter)

    def test_host_status_has_ttl_cache(self) -> None:
        self.assertIn('cached = getattr(tool_host_status, "_cache", None)', self.adapter)
        self.assertIn("now - cached[0] < 3.0", self.adapter)
        self.assertIn('result["cache_age_ms"]', self.adapter)
        self.assertIn('"cache_ttl_seconds": 3', self.adapter)

    def test_runtime_lifecycle_is_independent_of_adapter_cgroup(self) -> None:
        self.assertTrue(RUNTIME_UNIT.exists(), RUNTIME_UNIT)
        unit = RUNTIME_UNIT.read_text()
        self.assertIn("RemainAfterExit=yes", unit)
        self.assertIn("restart_runtime_only.sh", unit)
        self.assertIn("KillMode=control-group", unit)
        service_cmd = '["systemctl", "--user", "restart", "xavi-duotronic-runtime.service"]'
        self.assertIn(service_cmd, self.adapter)
        self.assertIn(service_cmd, self.ops_agent)

    def test_mcp_work_is_offloop_and_health_is_lightweight(self) -> None:
        self.assertIn("async def _handle_mcp_inner(", self.protocol)
        self.assertIn("return await asyncio.to_thread(", self.protocol)
        self.assertIn("lambda: asyncio.run(", self.protocol)
        self.assertIn("async def _call_tool_offloop(", self.http_mcp)
        self.assertIn("asyncio.to_thread(lambda: asyncio.run(_call_tool(kernel, tool, args)))", self.http_mcp)
        self.assertIn('async def health() -> dict[str, Any]:', self.api)
        snapshot = self.kernel.split("self._health_snapshot = {", 1)[1].split("    def migrate", 1)[0]
        self.assertIn('"models_count"', snapshot)
        self.assertIn('"modules_count"', snapshot)
        self.assertNotIn('"models": self.model_provider.registry.list_models()', snapshot)
        self.assertNotIn('"modules": self.modules.list()', snapshot)
        self.assertIn('@app.get("/v1/models/registry")', self.api)

    def test_operational_health_probes_do_not_train_or_query_collaboration(self) -> None:
        capture = self.protocol.split("_AUTO_CAPTURE_EXACT", 1)[1].split("}", 1)[0]
        for name in ("runtime.health", "runtime.models", "runtime.modules"):
            self.assertIn(f'"{name}"', capture)
        self.assertIn('tool_name not in {"task.awareness", "runtime.health", "runtime.models", "runtime.modules"}', self.protocol)
        self.assertIn('if tool == "runtime.health":\n        return kernel.health()', self.http_mcp)

    def test_live_authenticated_tools_list_if_adapter_is_running(self) -> None:
        key = os.environ.get("XAVI_OPS_API_KEY") or env_value("XAVI_OPS_API_KEY")
        if not key:
            self.skipTest("XAVI_OPS_API_KEY unavailable")
        body = json.dumps({"jsonrpc": "2.0", "id": "smoke", "method": "tools/list", "params": {}}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8092/",
            data=body,
            headers={"content-type": "application/json", "x-xavi-ops-key": key},
            method="POST",
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode())
        except Exception as exc:
            self.skipTest(f"live adapter unavailable: {exc}")
        elapsed = time.monotonic() - started
        tools = (payload.get("result") or {}).get("tools") or []
        self.assertGreater(len(tools), 0)
        self.assertLess(elapsed, 5.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
