from __future__ import annotations

from datetime import datetime, timezone

from duotronic_runtime.session_delegation import SessionDelegationService


class _Result:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class _Connection:
    def __init__(self):
        self.insert_sql = None
        self.insert_params = None
        self.committed = False

    def execute(self, sql, params=()):
        if "SELECT session_id FROM coordination_agent_sessions" in sql:
            return _Result({"session_id": params[0]})
        if "INSERT INTO mcp_session_messages" in sql:
            self.insert_sql = sql
            self.insert_params = params
            return _Result({
                "message_id": "00000000-0000-0000-0000-000000000001",
                "sender_session_id": params[0],
                "recipient_session_id": params[1],
                "expires_at": params[-1],
            })
        raise AssertionError(f"unexpected SQL: {sql}")

    def commit(self):
        self.committed = True


class _Connect:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


class _Store:
    def __init__(self):
        self.conn = _Connection()

    def connect(self):
        return _Connect(self.conn)


def _service():
    service = object.__new__(SessionDelegationService)
    service.store = _Store()
    service.kernel = None
    return service


def _base_args():
    return {
        "session_id": "session-a",
        "recipient_session_id": "session-b",
        "project_key": "xavi.app-backend",
        "message_type": "handoff",
        "subject": "Parallel work",
        "body": "Take the non-overlapping validation lane.",
        "payload": {"witnessed": True},
    }


def test_send_message_uses_single_typed_expiry_parameter_for_no_expiry():
    service = _service()
    result = service.send_message(_base_args())
    conn = service.store.conn

    assert conn.committed is True
    assert "CASE WHEN" not in conn.insert_sql
    assert "make_interval" not in conn.insert_sql
    assert conn.insert_sql.count("%s") == 10
    assert len(conn.insert_params) == 10
    assert conn.insert_params[-1] is None
    assert result["delivery"] == "durable-inbox"


def test_send_message_materializes_timezone_aware_expiry_before_insert():
    service = _service()
    args = _base_args() | {"expires_seconds": 120}
    service.send_message(args)
    expires_at = service.store.conn.insert_params[-1]

    assert isinstance(expires_at, datetime)
    assert expires_at.tzinfo is not None
    assert expires_at.utcoffset() == timezone.utc.utcoffset(expires_at)
