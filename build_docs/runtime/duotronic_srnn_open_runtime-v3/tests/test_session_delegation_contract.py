from __future__ import annotations

from pathlib import Path
import unittest

from duotronic_runtime.session_delegation import (
    SESSION_DELEGATION_SCHEMA_SQL,
    SessionDelegationService,
    session_delegation_tool_manifest,
)


class SessionDelegationContractTests(unittest.TestCase):
    def test_manifest_exposes_addressable_session_and_delegation_tools(self):
        names = {item["name"] for item in session_delegation_tool_manifest()}
        self.assertEqual(
            names,
            {
                "session.list",
                "session.send_message",
                "session.inbox",
                "session.acknowledge",
                "delegation.assign",
                "delegation.inbox",
                "delegation.update",
                "worker.register_wgrnn",
                "worker.wgrnn_tick",
            },
        )

    def test_schema_has_durable_mailbox_delegation_worker_and_run_tables(self):
        for table in (
            "mcp_session_messages",
            "mcp_delegations",
            "mcp_worker_registry",
            "mcp_delegated_tool_runs",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", SESSION_DELEGATION_SCHEMA_SQL)

    def test_wgrnn_default_tools_are_safe(self):
        for name in SessionDelegationService.DEFAULT_WGRNN_TOOLS:
            self.assertTrue(SessionDelegationService._safe_wgrnn_tool(name), name)
        self.assertFalse(SessionDelegationService._safe_wgrnn_tool("repo.apply_patch"))
        self.assertFalse(SessionDelegationService._safe_wgrnn_tool("ops.allowed_command"))
        self.assertFalse(SessionDelegationService._safe_wgrnn_tool("runtime.transcript_ingest"))
        self.assertFalse(SessionDelegationService._safe_wgrnn_tool("coordination.claim"))

    def test_native_mcp_binds_sender_identity(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "app/duotronic_runtime/mcp_protocol.py").read_text()
        self.assertIn("tool_name.startswith(", text)
        for prefix in ('"session."', '"delegation."', '"worker."'):
            self.assertIn(prefix, text)
        self.assertIn('arguments["session_id"] = context["session_id"]', text)
        self.assertIn('arguments["agent_id"] = context["agent_id"]', text)

    def test_developer_adapter_forwards_and_binds_new_tools(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "ops_agent/xavi_dev_mcp_adapter.py").read_text()
        prefixes = '("coordination.", "session.", "delegation.", "worker.", "task.")'
        self.assertGreaterEqual(text.count(prefixes), 2)
        self.assertIn("coordination_inject_identity(args, _coordination_context(request))", text)

    def test_normal_store_migration_installs_delegation_schema(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "app/duotronic_runtime/db.py").read_text()
        self.assertIn("from .session_delegation import SESSION_DELEGATION_SCHEMA_SQL", text)
        self.assertIn("conn.execute(SESSION_DELEGATION_SCHEMA_SQL)", text)

    def test_session_message_expiry_parameters_are_typed_for_postgres(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "app/duotronic_runtime/session_delegation.py").read_text()
        self.assertIn("datetime.now(timezone.utc) + timedelta(seconds=seconds)", text)
        self.assertIn("VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", text)
        self.assertNotIn("CASE WHEN %s::integer IS NULL", text)
        self.assertNotIn("make_interval(secs => %s::integer)", text)


if __name__ == "__main__":
    unittest.main()


def test_http_mcp_caches_session_delegation_service_source_contract():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    content = (root / "app" / "duotronic_runtime" / "http_mcp.py").read_text()
    assert 'service = getattr(kernel, "_session_delegation_service", None)' in content
    assert 'service = SessionDelegationService(kernel)' in content
    assert 'setattr(kernel, "_session_delegation_service", service)' in content


def test_delegation_digest_uses_imported_shake256_ref():
    from duotronic_runtime.session_delegation import _digest
    digest = _digest({"status": "completed", "result": {"schema_version": "xavi-node-pressure-v1"}})
    assert isinstance(digest, str)
    assert digest.startswith("shake256-512:") or digest.startswith("duoid:shake256-512:")


def test_wgrnn_tick_source_digests_successful_results_before_completion():
    runtime_root = Path(__file__).resolve().parents[1]
    content = (runtime_root / "app" / "duotronic_runtime" / "session_delegation.py").read_text()
    assert 'from .crypto_primitives import shake256_ref' in content
    assert 'result_digest = _digest(safe_result)' in content
    assert '"result_digest": _digest(safe_result)' in content
