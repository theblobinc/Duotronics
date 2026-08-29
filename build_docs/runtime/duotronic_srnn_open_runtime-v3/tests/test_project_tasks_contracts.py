from __future__ import annotations

import unittest

from duotronic_runtime.project_tasks import (
    PROJECT_TASK_SCHEMA_SQL,
    ProjectTaskService,
    TASK_KINDS,
    project_task_tool_manifest,
)


class SharedProjectTaskBoardContracts(unittest.TestCase):
    def test_schema_has_typed_backlog_and_atomic_claim_fields(self):
        sql = PROJECT_TASK_SCHEMA_SQL
        self.assertIn('CREATE TABLE IF NOT EXISTS coordination_tasks', sql)
        self.assertIn("'coding','functionality','ui','context'", sql)
        self.assertIn("'planned','ready','claimed','blocked','completed','cancelled'", sql)
        self.assertIn('depends_on UUID[]', sql)
        self.assertIn('required_capabilities TEXT[]', sql)
        self.assertIn('claimed_by_session_id TEXT', sql)
        self.assertIn('claim_token UUID', sql)
        self.assertIn('lease_expires_at TIMESTAMPTZ', sql)
        self.assertIn('coordination_tasks_project_queue_idx', sql)

    def test_manifest_exposes_collaborative_task_surface(self):
        tools = {item['name']: item for item in project_task_tool_manifest()}
        expected = {
            'task.list',
            'task.create',
            'task.claim_next',
            'task.renew',
            'task.update',
            'task.reopen',
            'task.awareness',
            'task.recurrent_context',
        }
        self.assertTrue(expected.issubset(tools), expected - set(tools))
        self.assertTrue(tools['task.list']['read_only'])
        self.assertTrue(tools['task.recurrent_context']['read_only'])
        self.assertFalse(tools['task.claim_next']['read_only'])

    def test_categories_are_the_requested_project_work_types(self):
        self.assertEqual(set(TASK_KINDS), {'coding', 'functionality', 'ui', 'context'})

    def test_recurrent_document_contains_collaboration_context(self):
        task = {
            'task_id': '00000000-0000-0000-0000-000000000001',
            'project_key': 'xavi.app-backend',
            'task_kind': 'ui',
            'title': 'Build task board UI',
            'objective': 'Expose shared work status to MCP agents and people.',
            'context': {'acceptance': ['claims visible', 'dependencies visible']},
            'resources': ['path:/var/www/xavi/example/ui'],
            'depends_on': ['00000000-0000-0000-0000-000000000002'],
            'required_capabilities': ['frontend'],
            'priority': 80,
            'status': 'ready',
            'claimed_by_agent_id': None,
            'claimed_by_session_id': None,
            'result': {},
        }
        doc = ProjectTaskService.recurrent_document(task)
        self.assertEqual(doc['task_kind'], 'ui')
        self.assertIn('shared-task-board', doc['tags'])
        self.assertIn('Task: Build task board UI', doc['text'])
        self.assertIn('claims visible', doc['text'])
        self.assertIn('path:/var/www/xavi/example/ui', doc['text'])

    def test_task_event_is_ready_for_coordination_learning_bridge(self):
        task = {
            'task_id': '00000000-0000-0000-0000-000000000003',
            'project_key': 'xavi.app-backend',
            'task_kind': 'coding',
            'title': 'Implement queue',
            'objective': 'Prevent duplicate work.',
            'context': {},
            'resources': ['path:/var/www/xavi/runtime/task.py'],
            'depends_on': [],
            'priority': 90,
            'status': 'claimed',
            'claimed_by_agent_id': 'agent:a',
            'claimed_by_session_id': 'session:a',
            'result': {},
            'work_id': None,
        }
        event = ProjectTaskService.event_document('claimed', task)
        self.assertEqual(event['event_type'], 'task.claimed')
        self.assertEqual(event['project_key'], 'xavi.app-backend')
        self.assertIn('recurrent_document', event['payload'])
        self.assertEqual(event['resources'], ['path:/var/www/xavi/runtime/task.py'])

    def test_claim_query_uses_skip_locked_and_dependency_gate(self):
        # Contract-level source check: atomic claim semantics must remain explicit.
        import inspect
        source = inspect.getsource(ProjectTaskService.claim_next)
        self.assertIn('FOR UPDATE SKIP LOCKED', source)
        self.assertIn("d.status <> 'completed'", source)
        self.assertIn("t.required_capabilities <@", source)
        self.assertIn("status='claimed'", source)

    def test_awareness_packet_contains_peer_work_and_next_action_context(self):
        import inspect
        source = inspect.getsource(ProjectTaskService.awareness)
        self.assertIn('coordination_agent_sessions', source)
        self.assertIn('session_transcript_events', source)
        self.assertIn('coordination_work_items', source)
        self.assertIn('coordination_resource_claims', source)
        self.assertIn('mcp_delegations', source)
        self.assertIn('mcp_worker_registry', source)
        self.assertIn("'peer_work'", source)
        self.assertIn("'available_tasks'", source)
        self.assertIn("'action_hints'", source)
        self.assertIn("'handle_delegation'", source)
        self.assertIn('addressed_delegations', source)
        self.assertIn('not available_tasks and not addressed_delegations', source)
        self.assertIn("status IN ('active','idle')", source)
        self.assertIn('JOIN coordination_agent_sessions s ON s.session_id=w.owner_session_id', source)
        self.assertIn("s.last_seen_at >= now() - (%s * interval '1 second')", source)
        self.assertIn('s.last_seen_at AS owner_last_seen_at', source)
        self.assertIn("'awareness_text'", source)


    def test_claim_next_can_atomically_filter_explicit_wgrnn_contract_and_allowlist(self):
        import inspect
        source = inspect.getsource(ProjectTaskService.claim_next)
        tools = {item['name']: item for item in project_task_tool_manifest()}
        schema = tools['task.claim_next']['input_schema']['properties']
        self.assertIn('allowed_tools', schema)
        self.assertIn('require_wgrnn_contract', schema)
        self.assertIn("context->'wgrnn_delegation'", source)
        self.assertIn("->>'tool_name'", source)
        self.assertIn('= ANY(%s::text[])', source)
        self.assertIn('FOR UPDATE SKIP LOCKED', source)
        self.assertIn('wgrnn_allowlist_empty', source)


    def test_blocked_update_releases_task_ownership_for_other_agents(self):
        import inspect
        source = inspect.getsource(ProjectTaskService.update)
        self.assertIn('claimed_by_session_id=NULL', source)
        self.assertIn('claim_token=NULL', source)
        self.assertIn("new_status == 'blocked'", source)

    def test_native_and_developer_mcp_auto_inject_peer_awareness(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        native = (root / 'app/duotronic_runtime/mcp_protocol.py').read_text()
        adapter = (root / 'ops_agent/xavi_dev_mcp_adapter.py').read_text()
        classifier = (root / 'ops_agent/xavi_mcp_coordination.py').read_text()
        self.assertIn('result["_collaboration"] = collaboration', native)
        self.assertIn('def _collaboration_awareness', adapter)
        self.assertIn('result["_collaboration"] = collaboration', adapter)
        self.assertIn('name.startswith(("coordination.","task."))', classifier)
        self.assertIn('startswith(("coordination.","task."))', classifier)
        self.assertIn('session_id=context.get("session_id")', adapter)
        self.assertIn('agent_id=context.get("agent_id")', adapter)

    def test_task_transitions_feed_coordination_learning_bridge(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        http_mcp = (root / 'app/duotronic_runtime/http_mcp.py').read_text()
        self.assertIn('task_result["coordination_event"] = CoordinationService', http_mcp)
        self.assertIn('"coordination.event", event_args', http_mcp)
        self.assertIn('event_args["session_id"] = args.get("session_id")', http_mcp)
        self.assertIn('event_args["agent_id"] = args.get("agent_id")', http_mcp)

    def test_developer_mcp_routes_task_tools_with_transport_identity(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        adapter = (root / 'ops_agent/xavi_dev_mcp_adapter.py').read_text()
        expected = '("coordination.", "session.", "delegation.", "worker.", "task.")'
        self.assertGreaterEqual(adapter.count(expected), 2)


if __name__ == '__main__':
    unittest.main()
