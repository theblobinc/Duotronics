#!/usr/bin/env python3
from __future__ import annotations

import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

import cache_audit
import cache_audit_services
import proof_authority as authority


class AuditAuthorityLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.governance = Ed25519PrivateKey.generate()
        self.old = Ed25519PrivateKey.generate()
        self.current = Ed25519PrivateKey.generate()

    def registry(self, current_status: str = "active") -> dict:
        return authority.sign_record({
            "schema_version": "cache_audit_signing_registry/v1",
            "registry_id": "cache:audit:registry:1",
            "governance_key_id": "governance:key:1",
            "created_at": "2026-08-01T12:00:00Z",
            "keys": [
                {
                    "key_id": "cache:audit:key:old", "principal_id": "cache:audit:worker",
                    "public_key_base64url": authority.public_key_raw_b64url(self.old.public_key()),
                    "authorization_scope": "cache_audit_record_signing", "status": "retired",
                    "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2026-08-01T00:00:00Z",
                    "status_changed_at": "2026-07-31T23:59:59Z", "rotation_predecessor_key_id": None,
                },
                {
                    "key_id": "cache:audit:key:current", "principal_id": "cache:audit:worker",
                    "public_key_base64url": authority.public_key_raw_b64url(self.current.public_key()),
                    "authorization_scope": "cache_audit_record_signing", "status": current_status,
                    "valid_from": "2026-08-01T00:00:00Z", "valid_until": None,
                    "status_changed_at": "2026-08-01T00:00:00Z",
                    "rotation_predecessor_key_id": "cache:audit:key:old",
                },
            ],
        }, self.governance)

    def test_registry_preserves_historical_keys_and_governs_active_selection(self):
        digest, records, keys = cache_audit.validate_governed_signing_registry(
            self.registry(), self.governance.public_key(), schema_validator=self.validator,
            surface="cache_audit_signing_registry", required_scope="cache_audit_record_signing",
            evaluated_at=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(set(keys), {"cache:audit:key:old", "cache:audit:key:current"})
        evidence = cache_audit.key_validity_evidence(
            registry_sha256=digest, record=records["cache:audit:key:current"],
            evaluated_at=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        )
        self.validator.validate("cache_audit_key_validity_evidence", evidence)
        self.assertEqual(evidence["decision"], "active_time_valid_rotation_valid")

    def test_revoked_current_key_cannot_receive_active_validity_decision(self):
        with self.assertRaisesRegex(RuntimeError, "exactly one active key"):
            cache_audit.validate_governed_signing_registry(
                self.registry(current_status="revoked"), self.governance.public_key(),
                schema_validator=self.validator, surface="cache_audit_signing_registry",
                required_scope="cache_audit_record_signing",
                evaluated_at=datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
            )


class ExternalAnchorAndPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.anchor_key = Ed25519PrivateKey.generate()
        self.request_key = Ed25519PrivateKey.generate()
        self.namespace = "cache:audit:anchor:integration"
        self.anchor_registry_sha256 = "a" * 64
        self.anchor_registry_records = {
            "cache:audit:anchor:key": {
                "key_id": "cache:audit:anchor:key", "principal_id": "cache:audit:anchor:principal",
                "public_key_base64url": authority.public_key_raw_b64url(self.anchor_key.public_key()),
                "authorization_scope": "cache_audit_monotonic_anchor_signing", "status": "active",
                "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
                "status_changed_at": "2026-01-01T00:00:00Z", "rotation_predecessor_key_id": None,
            }
        }

    def tearDown(self):
        self.temporary.cleanup()

    def test_privileged_file_anchor_round_trip_over_unix_socket(self):
        ledger = self.root / "anchor" / "ledger.jsonl"
        store = cache_audit_services.FileBackedMonotonicAnchorStore(
            ledger, self.anchor_key, key_id="cache:audit:anchor:key",
            signer_principal_id="cache:audit:anchor:principal",
            anchor_registry_sha256=self.anchor_registry_sha256,
            anchor_registry_records=self.anchor_registry_records,
            schema_validator=self.validator, provision=True,
            clock=lambda: datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        )
        socket_path = self.root / "anchor-service" / "anchor.sock"
        server = cache_audit_services.AuditAnchorServer(
            socket_path, store, schema_validator=self.validator,
            publisher_uid=os.getuid(), publisher_gid=os.getgid(),
            publisher_principal_id="cache:audit:publisher",
            request_verification_keys={"publisher:request:key": self.request_key.public_key()},
            socket_uid=os.getuid(), socket_gid=os.getgid(),
        )
        thread = threading.Thread(target=server.server.serve_forever, daemon=True)
        thread.start()
        try:
            client = cache_audit.UnixSocketAuditAnchorClient(
                socket_path, anchor_namespace=self.namespace,
                verification_keys_by_id={"cache:audit:anchor:key": self.anchor_key.public_key()},
                anchor_registry_sha256=self.anchor_registry_sha256,
                anchor_registry_records=self.anchor_registry_records,
                schema_validator=self.validator,
                request_signing_key=self.request_key,
                request_signer_key_id="publisher:request:key",
                peer_principal_id="cache:audit:publisher",
                expected_socket_uid=os.getuid(), expected_socket_gid=os.getgid(),
            )
            unsigned = {
                "schema_version": "cache_audit_anchor_state/v2",
                "anchor_namespace": self.namespace, "anchor_epoch": 0,
                "segment_id": "cache:audit:segment:0001", "sequence": 0,
                "tail_record_sha256": None, "segment_status": "open",
                "previous_sealed_segment_tail_sha256": None,
                "transition_authorization_sha256": "b" * 64,
                "audit_signing_registry_sha256": "c" * 64,
                "anchor_registry_sha256": self.anchor_registry_sha256,
                "previous_anchor_state_sha256": None,
                "updated_at": "2026-08-01T12:00:00Z",
            }
            state = client.compare_and_swap(None, unsigned)
            self.assertTrue(authority.verify_record(state, self.anchor_key.public_key()))
            self.assertEqual(client.read(), state)
            self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
            self.assertFalse(store.authoritative)
        finally:
            server.server.close_and_unlink()
            thread.join(timeout=2)

    def test_unix_publisher_client_hard_times_out_without_waiting_for_server(self):
        socket_path = self.root / "publisher" / "publisher.sock"
        def delayed(_request, _peer):
            time.sleep(0.5)
            return {"status": "error", "error": "late"}
        server = cache_audit_services.GovernedUnixServer(
            socket_path, delayed, schema_validator=self.validator,
            target_service="cache_audit_publisher",
            allowed_peer_principals={(os.getuid(), os.getgid()): "proof:service"},
            request_verification_keys_by_principal={"proof:service": {"proof:request:key": self.request_key.public_key()}},
            socket_uid=os.getuid(), socket_gid=os.getgid(),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = cache_audit.UnixSocketAuditPublisherClient(
                socket_path, verification_keys_by_id={},
                receipt_signing_registry_sha256="d" * 64, receipt_registry_records={},
                schema_validator=self.validator,
                request_signing_key=self.request_key,
                request_signer_key_id="proof:request:key", peer_principal_id="proof:service",
                expected_socket_uid=os.getuid(), expected_socket_gid=os.getgid(),
            )
            started = time.monotonic()
            with self.assertRaises((TimeoutError, OSError)):
                client({"schema_version": "cache_verification_evidence/v1"}, deadline_monotonic=started + 0.05)
            self.assertLess(time.monotonic() - started, 0.2)
        finally:
            server.close_and_unlink()
            thread.join(timeout=2)


class ValidatorExternalCancellationTests(unittest.TestCase):
    @staticmethod
    def _process_table() -> dict[int, int]:
        output = subprocess.check_output(["ps", "-eo", "pid=,ppid="], text=True)
        table: dict[int, int] = {}
        for line in output.splitlines():
            pid_text, parent_text = line.split()
            table[int(pid_text)] = int(parent_text)
        return table

    @classmethod
    def _descendants(cls, root_pid: int) -> set[int]:
        table = cls._process_table()
        found: set[int] = set()
        pending = [root_pid]
        while pending:
            parent = pending.pop()
            for pid, ppid in table.items():
                if ppid == parent and pid not in found:
                    found.add(pid); pending.append(pid)
        return found

    def test_sigterm_reaps_worker_and_escaped_descendant(self):
        command = [sys.executable, "executable/validators/validate_draft5_3_14_corpus.py", "--external-cancellation-probe"]
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        descendants: set[int] = set()
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                descendants = self._descendants(process.pid)
                if len(descendants) >= 2:
                    break
                time.sleep(0.05)
            self.assertGreaterEqual(len(descendants), 2)
            process.send_signal(signal.SIGTERM)
            self.assertEqual(process.wait(timeout=10), 128 + signal.SIGTERM)
            deadline = time.monotonic() + 3
            alive = set(descendants)
            while time.monotonic() < deadline:
                current = self._process_table()
                alive = {pid for pid in descendants if pid in current}
                if not alive:
                    break
                time.sleep(0.05)
            self.assertEqual(alive, set())
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=5)
            if process.stdout is not None:
                process.stdout.close()


if __name__ == "__main__":
    unittest.main()
