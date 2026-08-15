#!/usr/bin/env python3
from __future__ import annotations

import copy
import os
import pathlib
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone

from executable.runtime.pq_provider import MLDSA87PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "executable/runtime"))

import cache_audit
import cache_audit_services
import proof_authority as authority


NOW = datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc)


def key_record(key_id, principal, key, scope, *, status="active", valid_from="2026-01-01T00:00:00Z", valid_until=None, changed="2026-01-01T00:00:00Z", predecessor=None):
    return {
        "key_id": key_id, "principal_id": principal,
        "public_key_base64url": authority.public_key_raw_b64url(key.public_key()),
        "authorization_scope": scope, "status": status,
        "valid_from": valid_from, "valid_until": valid_until,
        "status_changed_at": changed, "rotation_predecessor_key_id": predecessor,
    }


def governed_registry(governance, schema_version, registry_id, records):
    return authority.sign_record({
        "schema_version": schema_version, "registry_id": registry_id,
        "governance_key_id": "governance:key:1", "created_at": "2026-08-02T09:00:00Z",
        "keys": records,
    }, governance)


class RegistryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.governance = MLDSA87PrivateKey.generate()

    def test_rotation_cycle_is_rejected(self):
        first = MLDSA87PrivateKey.generate(); second = MLDSA87PrivateKey.generate()
        registry = governed_registry(self.governance, "cache_audit_signing_registry/v1", "cache:audit:registry:cycle", [
            key_record("key:a", "principal:audit", first, "cache_audit_record_signing", predecessor="key:b"),
            key_record("key:b", "principal:audit", second, "cache_audit_record_signing", status="retired", valid_from="2025-01-01T00:00:00Z", valid_until="2026-01-01T00:00:00Z", changed="2025-12-31T23:59:59Z", predecessor="key:a"),
        ])
        with self.assertRaisesRegex(RuntimeError, "rotation cycle"):
            cache_audit.validate_governed_signing_registry(
                registry, self.governance.public_key(), schema_validator=self.validator,
                surface="cache_audit_signing_registry", required_scope="cache_audit_record_signing",
                evaluated_at=NOW,
            )

    def test_expired_or_revoked_artifact_key_is_rejected_at_artifact_timestamp(self):
        key = MLDSA87PrivateKey.generate()
        record = key_record(
            "key:old", "principal:audit", key, "cache_audit_record_signing",
            status="retired", valid_until="2026-02-01T00:00:00Z", changed="2026-02-01T00:00:00Z",
        )
        with self.assertRaisesRegex(RuntimeError, "expired, revoked, or unauthorized"):
            cache_audit.verify_artifact_key_lifecycle(
                registry_shake256_512="a" * 128, registry_records={"key:old": record},
                key_id="key:old", principal_id="principal:audit",
                required_scope="cache_audit_record_signing",
                artifact_timestamp="2099-01-01T00:00:00Z", embedded_evidence=None,
                schema_validator=self.validator, allow_retired_historical=True,
            )
        revoked = {**record, "status": "revoked"}
        with self.assertRaisesRegex(RuntimeError, "revoked"):
            cache_audit.verify_artifact_key_lifecycle(
                registry_shake256_512="a" * 128, registry_records={"key:old": revoked},
                key_id="key:old", principal_id="principal:audit",
                required_scope="cache_audit_record_signing",
                artifact_timestamp="2026-01-15T00:00:00Z", embedded_evidence=None,
                schema_validator=self.validator, allow_retired_historical=True,
            )


class AnchorTransitionTests(unittest.TestCase):
    def setUp(self):
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.key = MLDSA87PrivateKey.generate()
        self.records = {"anchor:key": key_record("anchor:key", "anchor:principal", self.key, "cache_audit_monotonic_anchor_signing")}
        self.anchor = cache_audit.InMemoryMonotonicAuditAnchor(
            self.key, key_id="anchor:key", signer_principal_id="anchor:principal",
            anchor_registry_shake256_512="b" * 128, anchor_registry_records=self.records,
            schema_validator=self.validator, clock=lambda: NOW,
        )

    def genesis(self):
        return {
            "schema_version": "cache_audit_anchor_state/v2", "anchor_namespace": "anchor:ns",
            "anchor_epoch": 0, "segment_id": "segment:1", "sequence": 0,
            "tail_record_shake256_512": None, "segment_status": "open",
            "previous_sealed_segment_tail_shake256_512": None,
            "transition_authorization_shake256_512": "c" * 128,
            "audit_signing_registry_shake256_512": "d" * 128,
            "anchor_registry_shake256_512": "b" * 128,
            "previous_anchor_state_shake256_512": None, "updated_at": NOW.isoformat(),
        }

    def test_same_sequence_rewrite_and_registry_change_are_rejected(self):
        state = self.anchor.compare_and_swap(None, self.genesis())
        rewritten = self.genesis()
        rewritten["tail_record_shake256_512"] = "e" * 128
        rewritten["previous_anchor_state_shake256_512"] = cache_audit.InMemoryMonotonicAuditAnchor.state_shake256_512(state)
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            self.anchor.compare_and_swap(cache_audit.InMemoryMonotonicAuditAnchor.state_shake256_512(state), rewritten)
        advanced = copy.deepcopy(rewritten)
        advanced["sequence"] = 1
        advanced["audit_signing_registry_shake256_512"] = "f" * 128
        with self.assertRaisesRegex(RuntimeError, "immutable"):
            self.anchor.compare_and_swap(cache_audit.InMemoryMonotonicAuditAnchor.state_shake256_512(state), advanced)

    def test_file_backed_anchor_is_explicitly_non_authoritative(self):
        self.assertFalse(cache_audit_services.FileBackedMonotonicAnchorStore.authoritative)


class ServiceAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.request_key = MLDSA87PrivateKey.generate()

    def tearDown(self):
        self.temp.cleanup()

    def test_unapproved_peer_is_rejected_before_dispatch(self):
        socket_path = self.root / "service" / "publisher.sock"
        calls = []
        server = cache_audit_services.GovernedUnixServer(
            socket_path, lambda payload, peer: calls.append((payload, peer)) or {"status": "ok"},
            schema_validator=self.validator, target_service="cache_audit_publisher",
            allowed_peer_principals={(12345, 12345): "proof:service"},
            request_verification_keys_by_principal={"proof:service": {"proof:req": self.request_key.public_key()}},
            socket_uid=os.getuid(), socket_gid=os.getgid(),
        )
        try:
            payload = {"operation": "publish", "event": {}, "event_shake256_512": "a" * 128, "event_idempotency_key": "event:" + "a" * 128}
            request = cache_audit.build_authenticated_service_request(
                operation="publish", payload=payload, peer_principal_id="proof:service",
                request_signer_key_id="proof:req", request_signing_key=self.request_key,
                target_service="cache_audit_publisher", socket_path=socket_path,
                deadline_monotonic=time.monotonic() + 5,
            )
            with self.assertRaises(PermissionError):
                server.authenticate(request, {"pid": os.getpid(), "uid": os.getuid(), "gid": os.getgid(), "start_time_ticks": None})
            self.assertEqual(calls, [])
        finally:
            server.server_close(); socket_path.unlink(missing_ok=True)

    def test_world_writable_socket_configuration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "world writable"):
            cache_audit_services.GovernedUnixServer(
                self.root / "bad" / "bad.sock", lambda payload, peer: {},
                schema_validator=self.validator, target_service="cache_audit_publisher",
                allowed_peer_principals={(os.getuid(), os.getgid()): "proof:service"},
                request_verification_keys_by_principal={"proof:service": {"proof:req": self.request_key.public_key()}},
                socket_uid=os.getuid(), socket_gid=os.getgid(), socket_mode=0o666,
            )


class SinkAndPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.governance = MLDSA87PrivateKey.generate()
        self.audit_key = MLDSA87PrivateKey.generate()
        self.anchor_key = MLDSA87PrivateKey.generate()
        self.receipt_key = MLDSA87PrivateKey.generate()
        self.audit_records = {"audit:key": key_record("audit:key", "audit:principal", self.audit_key, "cache_audit_record_signing")}
        self.anchor_records = {"anchor:key": key_record("anchor:key", "anchor:principal", self.anchor_key, "cache_audit_monotonic_anchor_signing")}
        self.receipt_records = {"receipt:key": key_record("receipt:key", "receipt:principal", self.receipt_key, "cache_audit_receipt_signing")}
        self.audit_registry_sha = "1" * 128
        self.anchor_registry_sha = "2" * 128
        self.receipt_registry_sha = "3" * 128
        self.anchor = cache_audit.InMemoryMonotonicAuditAnchor(
            self.anchor_key, key_id="anchor:key", signer_principal_id="anchor:principal",
            anchor_registry_shake256_512=self.anchor_registry_sha, anchor_registry_records=self.anchor_records,
            schema_validator=self.validator, clock=lambda: NOW,
        )
        self.current_sink = None

    def tearDown(self):
        self.temp.cleanup()

    def event(self, marker=1):
        digest = f"{marker:x}" * 128
        decision = {
            "schema_version": "cache_key_validity_evidence/v1", "registry_shake256_512": "a" * 128,
            "key_id": "cache:key", "principal_id": "cache:principal", "status": "active",
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
            "status_changed_at": "2026-01-01T00:00:00Z", "rotation_predecessor_key_id": None,
            "use": "signing", "decision": "active_time_valid_rotation_valid", "evaluated_at": NOW.isoformat(),
        }
        return {
            "schema_version": "cache_verification_evidence/v1", "cache_envelope_id": "cache:" + digest,
            "cache_registry_shake256_512": "a" * 128, "signing_decision": decision,
            "replay_decision": {**decision, "use": "replay"},
            "compiler_witness_signed_payload_shake256_512": "b" * 128,
        }

    def genesis(self, suffix):
        return authority.sign_record({
            "schema_version": "cache_audit_genesis_authorization/v1",
            "authorization_id": f"genesis:{suffix}", "segment_id": f"segment:{suffix}",
            "anchor_namespace": "anchor:namespace", "audit_signing_registry_shake256_512": self.audit_registry_sha,
            "anchor_registry_shake256_512": self.anchor_registry_sha, "decision": "authorize_audit_genesis",
            "created_at": NOW.isoformat(),
        }, self.governance)

    def make_sink(self, suffix, *, provision=False, transition=None, predecessor_checkpoint=None, predecessor_terminal=None, clock=lambda: NOW):
        return cache_audit.SignedAppendOnlyAuditSink(
            self.root / "segments" / f"{suffix}.jsonl", self.root / "checkpoints" / f"{suffix}.json",
            self.audit_key, {"audit:key": self.audit_key.public_key()}, segment_id=f"segment:{suffix}",
            signer_principal_id="audit:principal", signer_key_id="audit:key",
            audit_signing_registry_shake256_512=self.audit_registry_sha, audit_registry_records=self.audit_records,
            schema_validator=self.validator, maximum_record_bytes=262144, maximum_log_bytes=1048576,
            maximum_event_records=20, terminal_seal_reserved_bytes=262144,
            anchor_client=self.anchor, anchor_namespace="anchor:namespace",
            anchor_registry_shake256_512=self.anchor_registry_sha, clock=clock,
            provision=provision, governance_key=self.governance.public_key(),
            genesis_authorization=self.genesis(suffix) if provision and transition is None else None,
            transition_attestation=transition, predecessor_checkpoint=predecessor_checkpoint,
            predecessor_terminal_record=predecessor_terminal, storage_root=self.root,
        )

    def test_successor_rejects_unrelated_terminal_record(self):
        first = self.make_sink("1", provision=True)
        first(self.event())
        checkpoint = first.seal_segment()
        real_terminal = authority.canonical_json_loads((self.root / "segments/1.jsonl").read_text().splitlines()[-1])
        unrelated = copy.deepcopy(real_terminal)
        unrelated_event = authority.canonical_json_loads(unrelated["event_canonical_json"])
        unrelated["segment_id"] = "segment:other"
        unrelated_event["segment_id"] = "segment:other"
        unrelated["event_canonical_json"] = authority.canonical_bytes(unrelated_event).decode()
        unrelated["event_shake256_512"] = authority.shake256_512_bytes(authority.canonical_bytes(unrelated_event))
        unrelated = authority.sign_record({k:v for k,v in unrelated.items() if k not in {"signed_payload_shake256_512","signature"}}, self.audit_key)
        anchor = self.anchor.read()
        transition = authority.sign_record({
            "schema_version": "cache_audit_segment_transition/v1", "transition_id": "transition:1:2",
            "predecessor_segment_id": "segment:1",
            "predecessor_sealed_checkpoint_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(checkpoint)),
            "predecessor_terminal_record_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(unrelated)),
            "predecessor_tail_record_shake256_512": anchor["tail_record_shake256_512"],
            "predecessor_anchor_state_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(anchor)),
            "successor_segment_id": "segment:2", "successor_anchor_epoch": 1,
            "audit_signing_registry_shake256_512": self.audit_registry_sha,
            "anchor_registry_shake256_512": self.anchor_registry_sha,
            "decision": "authorize_successor_segment", "created_at": NOW.isoformat(),
        }, self.governance)
        with self.assertRaisesRegex(RuntimeError, "anchored tail|actual anchored"):
            self.make_sink("2", provision=True, transition=transition, predecessor_checkpoint=checkpoint, predecessor_terminal=unrelated)

    def test_global_event_idempotency_survives_segment_rotation(self):
        first = self.make_sink("1", provision=True)
        self.current_sink = first
        index = cache_audit_services.DurableEventIdIndex(self.root / "publisher" / "events.sqlite")
        server = cache_audit_services.AuditPublisherServer(
            self.root / "publisher-socket" / "publisher.sock", lambda: self.current_sink,
            receipt_signing_key=self.receipt_key, receipt_key_id="receipt:key",
            receipt_signer_principal_id="receipt:principal",
            receipt_signing_registry_shake256_512=self.receipt_registry_sha,
            receipt_registry_records=self.receipt_records, schema_validator=self.validator,
            event_index=index, proof_service_uid=os.getuid(), proof_service_gid=os.getgid(),
            proof_service_principal_id="proof:service", request_verification_keys={"proof:req": MLDSA87PrivateKey.generate().public_key()},
            socket_uid=os.getuid(), socket_gid=os.getgid(), clock=lambda: NOW,
        )
        try:
            payload = {"operation":"publish", "event":self.event(), "event_shake256_512":authority.shake256_512_bytes(authority.canonical_bytes(self.event())), "event_idempotency_key":"event:"+authority.shake256_512_bytes(authority.canonical_bytes(self.event()))}
            first_response = server.dispatch(payload, {"uid":os.getuid(),"gid":os.getgid(),"pid":os.getpid(),"start_time_ticks":None})
            checkpoint = first.seal_segment()
            terminal = authority.canonical_json_loads((self.root / "segments/1.jsonl").read_text().splitlines()[-1])
            anchor = self.anchor.read()
            transition = authority.sign_record({
                "schema_version": "cache_audit_segment_transition/v1", "transition_id": "transition:1:2",
                "predecessor_segment_id": "segment:1", "predecessor_sealed_checkpoint_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(checkpoint)),
                "predecessor_terminal_record_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(terminal)),
                "predecessor_tail_record_shake256_512": anchor["tail_record_shake256_512"], "predecessor_anchor_state_shake256_512": authority.shake256_512_bytes(authority.canonical_bytes(anchor)),
                "successor_segment_id": "segment:2", "successor_anchor_epoch": 1,
                "audit_signing_registry_shake256_512": self.audit_registry_sha, "anchor_registry_shake256_512": self.anchor_registry_sha,
                "decision": "authorize_successor_segment", "created_at": NOW.isoformat(),
            }, self.governance)
            self.current_sink = self.make_sink("2", provision=True, transition=transition, predecessor_checkpoint=checkpoint, predecessor_terminal=terminal)
            second_response = server.dispatch(payload, {"uid":os.getuid(),"gid":os.getgid(),"pid":os.getpid(),"start_time_ticks":None})
            self.assertEqual(first_response["receipt"]["decision"], "durably_committed")
            self.assertEqual(second_response["receipt"]["decision"], "already_committed")
            self.assertEqual((self.root / "segments/2.jsonl").read_text(), "")
        finally:
            server.server.server_close(); server.server.socket_path.unlink(missing_ok=True)

    def test_expired_and_replayed_recovery_authorizations_fail(self):
        sink = self.make_sink("1", provision=True)
        expired = authority.sign_record({
            "schema_version":"cache_audit_recovery_authorization/v2", "authorization_id":"recovery:expired",
            "segment_id":"segment:1", "action":"remove_orphan_checkpoint_temporaries",
            "checkpoint_sequence_before":0, "checkpoint_tail_before":None,
            "log_sequence_after":0, "log_tail_after":None, "target_file_identities":[],
            "operator_principal_id":"operator:1", "reason":"expired test",
            "decision":"authorize_governed_recovery", "created_at":"2020-01-01T00:00:00Z", "expires_at":"2020-01-01T00:05:00Z",
        }, self.governance)
        with self.assertRaisesRegex(RuntimeError, "not currently valid"):
            sink.cleanup_checkpoint_temporaries(expired, self.governance.public_key(), evidence_path=self.root/"recovery/expired.json")
        valid = authority.sign_record({
            **{k:v for k,v in expired.items() if k not in {"signed_payload_shake256_512","signature"}},
            "authorization_id":"recovery:valid", "created_at":"2026-08-02T09:59:00Z", "expires_at":"2026-08-02T10:04:00Z",
        }, self.governance)
        sink.cleanup_checkpoint_temporaries(valid, self.governance.public_key(), evidence_path=self.root/"recovery/valid.json")
        with self.assertRaisesRegex(RuntimeError, "already been consumed"):
            sink.cleanup_checkpoint_temporaries(valid, self.governance.public_key(), evidence_path=self.root/"recovery/replay.json")


if __name__ == "__main__":
    unittest.main()
