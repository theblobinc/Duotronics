from __future__ import annotations
import unittest
from ops_agent.xavi_mcp_identity import identity_trace, new_chat_identity, new_delegation, new_resource_lease, valid_session_id

class MCPIdentityDelegationTests(unittest.TestCase):
    def setUp(self): self.secret = "test-secret-not-production"

    def test_distinct_chats_get_distinct_sessions_and_connections(self):
        a = new_chat_identity(secret=self.secret, client_name="ChatGPT", device_id="desktop-A")
        b = new_chat_identity(secret=self.secret, client_name="ChatGPT", device_id="desktop-A")
        self.assertEqual(a.agent_id, b.agent_id)
        self.assertNotEqual(a.session_id, b.session_id)
        self.assertNotEqual(a.connection_id, b.connection_id)
        self.assertTrue(valid_session_id(a.session_id, self.secret))

    def test_reconnect_resumes_session_but_rotates_connection(self):
        first = new_chat_identity(secret=self.secret, client_name="ChatGPT", device_id="desktop-A")
        second = new_chat_identity(secret=self.secret, client_name="ChatGPT", device_id="desktop-A", candidate_session_id=first.session_id)
        self.assertTrue(second.resumed)
        self.assertEqual(first.session_id, second.session_id)
        self.assertEqual(first.agent_id, second.agent_id)
        self.assertNotEqual(first.connection_id, second.connection_id)

    def test_delegation_records_lineage_and_capabilities(self):
        parent = new_chat_identity(secret=self.secret, client_name="ChatGPT", device_id="desktop-A")
        child = new_chat_identity(secret=self.secret, client_name="ChatGPT", device_id="desktop-A")
        d = new_delegation(delegator_session_id=parent.session_id, delegate_session_id=child.session_id, objective="Implement a non-overlapping test lane", parent_work_id="work_parent", required_capabilities=["python", "tests", "python"], resource_hints={"cpu_threads": 4, "memory_mb": 2048})
        self.assertEqual(d.required_capabilities, ("python", "tests"))
        self.assertTrue(d.work_id.startswith("work_"))
        self.assertTrue(d.delegation_id.startswith("dlg_"))

    def test_resource_lease_describes_gpu_allocation(self):
        ident = new_chat_identity(secret=self.secret, client_name="ChatGPT")
        d = new_delegation(delegator_session_id=ident.session_id, objective="GPU validation")
        gpu = new_resource_lease(work_id=d.work_id, session_id=ident.session_id, resource_type="gpu", resource_id="rtx2070", quantity=1, unit="device", ttl_seconds=60, exclusive=True)
        self.assertEqual(gpu.resource_type, "gpu")
        self.assertTrue(gpu.exclusive)

    def test_trace_binds_chat_work_and_delegation(self):
        ident = new_chat_identity(secret=self.secret, client_name="ChatGPT")
        d = new_delegation(delegator_session_id=ident.session_id, objective="Trace me")
        trace = identity_trace(ident, work_id=d.work_id, delegation_id=d.delegation_id)
        self.assertEqual(trace["session_id"], ident.session_id)
        self.assertTrue(trace["trace_digest"].startswith("sha256:"))

if __name__ == "__main__": unittest.main()
