from __future__ import annotations

import unittest

from duotronic_runtime.session_delegation import (
    SESSION_DELEGATION_SCHEMA_SQL,
    SessionDelegationService,
    session_delegation_tool_manifest,
)


class SessionDelegationMultiAgentContracts(unittest.TestCase):
    def test_manifest_exposes_cross_session_collaboration_surface(self):
        tools = {tool["name"]: tool for tool in session_delegation_tool_manifest()}
        required = {
            "session.list",
            "session.send_message",
            "session.inbox",
            "session.acknowledge",
            "delegation.assign",
            "delegation.inbox",
            "delegation.update",
            "worker.register_wgrnn",
            "worker.wgrnn_tick",
        }
        self.assertTrue(required.issubset(tools), required - set(tools))

    def test_addressed_messages_are_durable_and_status_tracked(self):
        sql = SESSION_DELEGATION_SCHEMA_SQL
        self.assertIn("CREATE TABLE IF NOT EXISTS mcp_session_messages", sql)
        self.assertIn("sender_session_id TEXT NOT NULL", sql)
        self.assertIn("recipient_session_id TEXT NOT NULL", sql)
        self.assertIn("'queued','delivered','read','acknowledged','expired','cancelled'", sql)
        self.assertIn("mcp_session_messages_recipient_idx", sql)

    def test_delegations_preserve_lineage_and_worker_kind(self):
        sql = SESSION_DELEGATION_SCHEMA_SQL
        self.assertIn("CREATE TABLE IF NOT EXISTS mcp_delegations", sql)
        self.assertIn("parent_work_id UUID", sql)
        self.assertIn("delegator_session_id TEXT NOT NULL", sql)
        self.assertIn("delegate_session_id TEXT", sql)
        self.assertIn("'session','wgrnn','worker'", sql)
        self.assertIn("required_capabilities TEXT[]", sql)
        self.assertIn("resource_hints JSONB", sql)

    def test_worker_registry_and_tool_runs_are_persistent(self):
        sql = SESSION_DELEGATION_SCHEMA_SQL
        self.assertIn("CREATE TABLE IF NOT EXISTS mcp_worker_registry", sql)
        self.assertIn("session_id TEXT NOT NULL UNIQUE", sql)
        self.assertIn("allowed_tools TEXT[]", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS mcp_delegated_tool_runs", sql)
        self.assertIn("delegation_id UUID NOT NULL REFERENCES mcp_delegations", sql)
        self.assertIn("worker_id TEXT NOT NULL REFERENCES mcp_worker_registry", sql)

    def test_wgrnn_worker_has_stable_identity_and_safe_default_tools(self):
        self.assertEqual(SessionDelegationService.WGRNN_WORKER_ID, "worker:wgrnn-main")
        self.assertEqual(SessionDelegationService.WGRNN_SESSION_ID, "wgrnn:worker:main")
        default_tools = set(SessionDelegationService.DEFAULT_WGRNN_TOOLS)
        self.assertIn("runtime.health", default_tools)
        self.assertIn("runtime.models", default_tools)
        self.assertFalse(any(name.startswith("ops.") for name in default_tools))

    def test_inbox_and_status_views_remain_readable_without_delegation_mutation(self):
        tools = {tool["name"]: tool for tool in session_delegation_tool_manifest()}
        self.assertTrue(tools["session.list"].get("read_only"))
        self.assertTrue(tools["delegation.inbox"].get("read_only"))
        self.assertFalse(tools["session.send_message"].get("read_only"))
        self.assertFalse(tools["delegation.assign"].get("read_only"))
        self.assertFalse(tools["delegation.update"].get("read_only"))


if __name__ == "__main__":
    unittest.main()
