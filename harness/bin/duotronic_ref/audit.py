"""In-process audit ledger used by the harness CI invariants meta-test.

The ledger is reset per-test via the conftest fixture. Every conformance path
that could possibly violate one of the App-S §S.3 CI rules records an event
here. The meta-test (`conformance/test_ci_invariants.py`) inspects the ledger
at the end of the suite and fails if anything got through.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditEvent:
    kind: str
    detail: dict[str, Any] = field(default_factory=dict)


class AuditLedger:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: list[AuditEvent] = []

    def record(self, kind: str, **detail: Any) -> None:
        with self._lock:
            self._events.append(AuditEvent(kind=kind, detail=dict(detail)))

    def events(self, kind: str | None = None) -> list[AuditEvent]:
        with self._lock:
            if kind is None:
                return list(self._events)
            return [e for e in self._events if e.kind == kind]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


LEDGER = AuditLedger()


def record(kind: str, **detail: Any) -> None:
    LEDGER.record(kind, **detail)


# Canonical event kinds (App S §S.3, App O failure-code registry).
EVT_FAILED_FRAME_TO_TRUSTED_MEMORY = "failed_frame_to_trusted_memory"
EVT_ABSENCE_ZERO_COLLISION_ACCEPTED = "absence_zero_collision_accepted"
EVT_REPLAY_MISMATCH_UNMARKED = "replay_mismatch_unmarked"
EVT_REPLAY_MISMATCH_EXPECTED = "replay_mismatch_expected"
EVT_TRANSPORT_REJECTED = "transport_rejected"
EVT_BYPASS_TRANSITION = "bypass_transition"
EVT_MIGRATION_REJECTED = "migration_rejected"
EVT_RETENTION_NO_BASELINE = "retention_no_baseline"
