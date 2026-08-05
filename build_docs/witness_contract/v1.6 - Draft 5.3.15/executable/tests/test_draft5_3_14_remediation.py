#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import os
import pathlib
import time
import sqlite3
import stat
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import closing
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
sys.path.insert(0, str(ROOT / "executable/tests"))

import proof_authority as authority  # noqa: E402
import proof_check_service as service  # noqa: E402
from test_proof_check_service import FakeAuthority, FakePolicyResolver, RequestBoundaryValidator  # noqa: E402


def proof_request() -> dict:
    return {
        "request_id": "request:historical", "idempotency_key": "idempotency:historical",
        "compiler_profile_id": "profile:governed", "claim_id": "claim:1",
        "canonical_claim": {"statement": "True"}, "theorem_statement": "True",
        "theorem_name": "t", "source_bundle_id": "bundle-1",
        "proof_artifact_relative_path": "Proof.lean", "policy_decision_id": "policy:1",
    }


class CacheEvidenceValidator(RequestBoundaryValidator):
    def validate(self, surface, value):
        if surface in {"proof_check_request", "cache_stale_row_evidence"}:
            self.real.validate(surface, value)


class HistoricalCacheBindingAndChronologyTests(unittest.TestCase):
    NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    OLD_TIME = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)

    @staticmethod
    def key_record(key_id: str, key: Ed25519PrivateKey, *, valid_from: str) -> dict:
        return {
            "key_id": key_id, "principal_id": "cache:principal",
            "public_key_base64url": authority.public_key_raw_b64url(key.public_key()),
            "authorization_scope": "idempotency_cache_envelope_signing",
            "status": "active", "valid_from": valid_from, "valid_until": None,
            "status_changed_at": valid_from, "rotation_predecessor_key_id": None,
        }

    @staticmethod
    def registry(governance: Ed25519PrivateKey, registry_id: str, created_at: str, record: dict) -> dict:
        return authority.sign_record({
            "schema_version": "cache_signing_registry/v2", "registry_id": registry_id,
            "governance_key_id": "governance:key", "created_at": created_at,
            "keys": [record],
        }, governance)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        bundle = self.root / "bundle-1"
        bundle.mkdir()
        (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
        self.governance = Ed25519PrivateKey.generate()
        self.old_key = Ed25519PrivateKey.generate()
        self.new_key = Ed25519PrivateKey.generate()
        self.old_record = self.key_record("cache:key:old", self.old_key, valid_from="2026-01-01T00:00:00Z")
        self.new_record = self.key_record("cache:key:current", self.new_key, valid_from="2026-07-01T00:00:00Z")
        self.old_registry = self.registry(self.governance, "cache:registry:old", "2026-02-01T00:00:00Z", self.old_record)
        self.current_registry = self.registry(self.governance, "cache:registry:current", "2026-08-01T00:00:00Z", self.new_record)
        self.old_digest = authority.sha256_bytes(authority.canonical_bytes(self.old_registry))
        self.current_digest = authority.sha256_bytes(authority.canonical_bytes(self.current_registry))
        self.lineage = authority.sign_record({
            "schema_version": "cache_registry_lineage/v1", "lineage_id": "cache:lineage:1",
            "governance_key_id": "governance:key", "current_registry_sha256": self.current_digest,
            "historical_registries": [{
                "registry_sha256": self.old_digest, "registry_file": "cache-registry-old.json",
                "successor_registry_sha256": self.current_digest,
                "stale_replay_policy": "authenticate_then_conflict", "revoked_key_ids": [],
            }],
            "created_at": "2026-08-01T00:00:00Z",
        }, self.governance)
        self.authority = FakeAuthority()
        self.validator = CacheEvidenceValidator()
        self.events: list[dict] = []
        old_application = service.ProofCheckApplication(
            self.authority, self.root, FakePolicyResolver(), schema_validator=self.validator,
            cache_signing_key=self.old_key, cache_verification_key=self.old_key.public_key(),
            cache_verification_keys_by_id={self.old_record["key_id"]: self.old_key.public_key()},
            cache_signer_principal_id=self.old_record["principal_id"],
            cache_signer_key_id=self.old_record["key_id"], cache_key_record=self.old_record,
            cache_registry_sha256=self.old_digest, cache_clock=lambda: self.OLD_TIME,
        )
        old_application.handle(proof_request(), authenticated_principal_id="principal:1")
        self.store = old_application.idempotency_store

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def snapshots(self) -> dict[str, service.GovernedCacheRegistrySnapshot]:
        lineage_digest = self.lineage["signed_payload_sha256"]
        lineage_created_at = self.lineage["created_at"]
        return {
            self.old_digest: service.build_governed_cache_registry_snapshot(
                self.old_registry, self.governance.public_key(),
                successor_registry_sha256=self.current_digest,
                stale_replay_policy="authenticate_then_conflict", revoked_key_ids=frozenset(),
                lineage_signed_payload_sha256=lineage_digest, lineage_created_at=lineage_created_at,
            ),
            self.current_digest: service.build_governed_cache_registry_snapshot(
                self.current_registry, self.governance.public_key(),
                successor_registry_sha256=None, stale_replay_policy="current_registry",
                lineage_signed_payload_sha256=lineage_digest, lineage_created_at=lineage_created_at,
                evaluated_at=self.NOW,
            ),
        }

    def current_application(self) -> service.ProofCheckApplication:
        return service.ProofCheckApplication(
            self.authority, self.root, FakePolicyResolver(), schema_validator=self.validator,
            idempotency_store=self.store,
            cache_signing_key=self.new_key, cache_verification_key=self.new_key.public_key(),
            cache_verification_keys_by_id={self.new_record["key_id"]: self.new_key.public_key()},
            cache_signer_principal_id=self.new_record["principal_id"],
            cache_signer_key_id=self.new_record["key_id"], cache_key_record=self.new_record,
            cache_registry_sha256=self.current_digest,
            cache_registry_snapshots_by_sha256=self.snapshots(),
            cache_clock=lambda: self.NOW, cache_verification_evidence_sink=self.events.append,
        )

    def stored_envelope(self) -> dict:
        with closing(sqlite3.connect(self.root / ".proof-check-idempotency.sqlite")) as connection:
            raw = connection.execute("SELECT result_canonical_json FROM proof_check_idempotency").fetchone()[0]
        return authority.canonical_json_loads(raw)

    def replace_stored_envelope(self, envelope: dict) -> None:
        with closing(sqlite3.connect(self.root / ".proof-check-idempotency.sqlite")) as connection:
            connection.execute(
                "UPDATE proof_check_idempotency SET result_canonical_json=?",
                (authority.canonical_bytes(envelope).decode("utf-8"),),
            )
            connection.commit()

    def rebind_database_slot(self, request: dict, *, principal_id: str = "principal:1") -> None:
        request_sha256 = authority.sha256_bytes(authority.canonical_bytes(request))
        with closing(sqlite3.connect(self.root / ".proof-check-idempotency.sqlite")) as connection:
            connection.execute(
                "UPDATE proof_check_idempotency SET principal_id=?, idempotency_key=?, request_sha256=?",
                (principal_id, request["idempotency_key"], request_sha256),
            )
            connection.commit()

    def assert_integrity_without_rotation_evidence(self, request: dict, principal_id: str = "principal:1") -> None:
        with self.assertRaises(authority.AuthorityFailure) as caught:
            self.current_application().handle(request, authenticated_principal_id=principal_id)
        self.assertEqual(caught.exception.code, "cache_integrity_invalid")
        self.assertEqual(self.events, [])

    def test_authentic_historical_envelope_transplanted_to_another_slot_is_integrity_failure(self):
        changed = {
            **proof_request(), "request_id": "request:other", "idempotency_key": "idempotency:other",
            "claim_id": "claim:other", "canonical_claim": {"statement": "False"},
        }
        self.rebind_database_slot(changed)
        self.assert_integrity_without_rotation_evidence(changed)

    def test_authentic_historical_envelope_transplanted_to_another_principal_is_integrity_failure(self):
        self.rebind_database_slot(proof_request(), principal_id="principal:other")
        self.assert_integrity_without_rotation_evidence(proof_request(), principal_id="principal:other")

    def test_authentic_historical_envelope_for_another_claim_is_integrity_failure(self):
        changed = {**proof_request(), "claim_id": "claim:other", "canonical_claim": {"statement": "False"}}
        self.rebind_database_slot(changed)
        self.assert_integrity_without_rotation_evidence(changed)

    def test_bound_historical_row_emits_self_contained_exact_envelope_evidence(self):
        envelope = self.stored_envelope()
        with self.assertRaises(authority.AuthorityFailure) as caught:
            self.current_application().handle(proof_request(), authenticated_principal_id="principal:1")
        self.assertEqual(caught.exception.code, "cache_key_rotation_requires_new_idempotency_key")
        self.assertEqual(len(self.events), 1)
        evidence = self.events[0]
        self.assertEqual(evidence["schema_version"], "cache_stale_row_evidence/v4")
        self.assertEqual(evidence["cache_envelope_signed_payload_sha256"], envelope["signed_payload_sha256"])
        self.assertEqual(evidence["cache_envelope_canonical_sha256"], authority.sha256_bytes(authority.canonical_bytes(envelope)))
        self.assertEqual(evidence["cache_envelope_signature"], envelope["signature"])

    def test_historical_registry_must_exist_before_cache_signing_time(self):
        envelope = self.stored_envelope()
        envelope["cache_signed_at"] = "2026-01-15T12:00:00+00:00"
        envelope["cache_key_validity_evidence"]["evaluated_at"] = envelope["cache_signed_at"]
        self.replace_stored_envelope(authority.sign_record(envelope, self.old_key))
        self.assert_integrity_without_rotation_evidence(proof_request())

    def test_lineage_must_postdate_every_referenced_registry(self):
        snapshots = self.snapshots()
        old = snapshots[self.old_digest]
        snapshots[self.old_digest] = service.GovernedCacheRegistrySnapshot(
            **{**old.__dict__, "lineage_created_at": "2026-01-31T00:00:00Z"},
        )
        with self.assertRaisesRegex(ValueError, "lineage predates"):
            service.validate_cache_registry_snapshot_lineage(
                snapshots, current_registry_sha256=self.current_digest, production_mode=True,
            )


class SignedCacheAuditSinkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.key = Ed25519PrivateKey.generate()
        self.governance = Ed25519PrivateKey.generate()
        self.anchor_key = Ed25519PrivateKey.generate()
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")
        self.audit_registry_sha256 = "d" * 64
        self.anchor_registry_sha256 = "e" * 64
        self.anchor_namespace = "cache:audit:anchor:test"
        self.anchor = service.InMemoryMonotonicAuditAnchor(
            self.anchor_key, key_id="cache:audit:anchor:key", schema_validator=self.validator,
        )
        self.key_evidence = {
            "schema_version": "cache_audit_key_validity_evidence/v1",
            "registry_sha256": self.audit_registry_sha256,
            "key_id": "cache:audit:key", "principal_id": "cache:audit:principal",
            "authorization_scope": "cache_audit_record_signing", "status": "active",
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": None,
            "status_changed_at": "2026-01-01T00:00:00Z",
            "rotation_predecessor_key_id": None,
            "decision": "active_time_valid_rotation_valid",
            "evaluated_at": "2026-08-01T12:00:00+00:00",
        }

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def evidence(marker: int = 1) -> dict:
        digest = f"{marker % 16:x}" * 64
        decision = {
            "schema_version": "cache_key_validity_evidence/v1",
            "registry_sha256": "a" * 64,
            "key_id": "cache:key:test", "principal_id": "cache:principal:test",
            "status": "active", "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None, "status_changed_at": "2026-01-01T00:00:00Z",
            "rotation_predecessor_key_id": None, "use": "signing",
            "decision": "active_time_valid_rotation_valid", "evaluated_at": "2026-08-01T12:00:00Z",
        }
        replay = {**decision, "use": "replay"}
        return {
            "schema_version": "cache_verification_evidence/v1",
            "cache_envelope_id": "cache:" + digest,
            "cache_registry_sha256": "a" * 64,
            "signing_decision": decision, "replay_decision": replay,
            "compiler_witness_signed_payload_sha256": "b" * 64,
        }

    def paths(self, suffix: str = "0001") -> tuple[pathlib.Path, pathlib.Path]:
        return (
            self.root / "segments" / f"cache-audit-{suffix}.jsonl",
            self.root / "checkpoints" / f"cache-audit-{suffix}.checkpoint.json",
        )

    def genesis(self, suffix: str = "0001") -> dict:
        return authority.sign_record({
            "schema_version": "cache_audit_genesis_authorization/v1",
            "authorization_id": f"cache:audit:genesis:{suffix}",
            "segment_id": f"cache:audit:segment:{suffix}",
            "anchor_namespace": self.anchor_namespace,
            "audit_signing_registry_sha256": self.audit_registry_sha256,
            "anchor_registry_sha256": self.anchor_registry_sha256,
            "decision": "authorize_audit_genesis",
            "created_at": "2026-08-01T12:00:00Z",
        }, self.governance)

    def sink(
        self, *, provision: bool = False, suffix: str = "0001",
        maximum_event_records: int = 100, maximum_log_bytes: int = 1048576,
        terminal_seal_reserved_bytes: int = 262144,
        transition_attestation: dict | None = None,
        predecessor_checkpoint: dict | None = None,
        predecessor_terminal_record: dict | None = None,
        recovery_mode: bool = False,
        **kwargs,
    ) -> service.SignedAppendOnlyAuditSink:
        log, checkpoint = self.paths(suffix)
        return service.SignedAppendOnlyAuditSink(
            log, checkpoint, self.key, {"cache:audit:key": self.key.public_key()},
            segment_id=f"cache:audit:segment:{suffix}",
            signer_principal_id="cache:audit:principal", signer_key_id="cache:audit:key",
            audit_signing_registry_sha256=self.audit_registry_sha256,
            audit_key_validity_evidence=self.key_evidence,
            schema_validator=self.validator, maximum_record_bytes=262144,
            maximum_log_bytes=maximum_log_bytes, maximum_event_records=maximum_event_records,
            terminal_seal_reserved_bytes=terminal_seal_reserved_bytes,
            anchor_client=self.anchor, anchor_namespace=self.anchor_namespace,
            anchor_registry_sha256=self.anchor_registry_sha256,
            clock=lambda: datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
            provision=provision, governance_key=self.governance.public_key(),
            genesis_authorization=self.genesis(suffix) if provision and transition_attestation is None else None,
            transition_attestation=transition_attestation,
            predecessor_checkpoint=predecessor_checkpoint,
            predecessor_terminal_record=predecessor_terminal_record,
            storage_root=self.root, recovery_mode=recovery_mode, **kwargs,
        )

    def test_unknown_or_structurally_invalid_event_is_rejected_before_append(self):
        sink = self.sink(provision=True)
        with self.assertRaises(RuntimeError):
            sink({"schema_version": "unknown_event/v1"})
        with self.assertRaises(authority.AuthorityFailure):
            sink({"schema_version": "cache_verification_evidence/v1"})
        self.assertEqual(self.sink()._sequence, 0)

    def test_startup_revalidates_embedded_event_schema(self):
        sink = self.sink(provision=True)
        sink(self.evidence())
        path = self.paths()[0]
        record = authority.canonical_json_loads(path.read_text(encoding="utf-8").strip())
        event = authority.canonical_json_loads(record["event_canonical_json"])
        event.pop("cache_registry_sha256")
        event_bytes = authority.canonical_bytes(event)
        unsigned = {k: v for k, v in record.items() if k not in {"signed_payload_sha256", "signature"}}
        unsigned["event_canonical_json"] = event_bytes.decode("utf-8")
        unsigned["event_sha256"] = authority.sha256_bytes(event_bytes)
        # Keep the outer record cryptographically valid so startup must reject the
        # embedded event through its allowlisted canonical schema, not a signature shortcut.
        path.write_bytes(authority.canonical_bytes(authority.sign_record(unsigned, self.key)) + b"\n")
        with self.assertRaises(authority.AuthorityFailure):
            self.sink()

    def test_signed_append_only_chain_is_durable_and_externally_anchored(self):
        sink = self.sink(provision=True)
        sink(self.evidence(1)); sink(self.evidence(2))
        restarted = self.sink()
        self.assertEqual(restarted._sequence, 2)
        self.assertEqual(self.anchor.read()["sequence"], 2)
        lines = self.paths()[0].read_text(encoding="utf-8").splitlines()
        second = authority.canonical_json_loads(lines[1])
        self.assertEqual(second["previous_audit_record_sha256"], authority.sha256_bytes(lines[0].encode("utf-8")))

    def test_coordinated_local_log_and_checkpoint_rollback_is_rejected_by_external_anchor(self):
        sink = self.sink(provision=True)
        sink(self.evidence(1))
        saved_log = self.paths()[0].read_bytes(); saved_checkpoint = self.paths()[1].read_bytes()
        sink(self.evidence(2))
        self.paths()[0].write_bytes(saved_log); self.paths()[1].write_bytes(saved_checkpoint)
        with self.assertRaises(authority.AuthorityFailure) as caught:
            self.sink()
        self.assertEqual(caught.exception.code, "cache_audit_integrity_invalid")

    def test_deleted_audit_log_is_not_silently_recreated(self):
        sink = self.sink(provision=True); sink(self.evidence())
        self.paths()[0].unlink()
        with self.assertRaises(authority.AuthorityFailure): self.sink()
        self.assertFalse(self.paths()[0].exists())

    def test_competing_genesis_requires_external_anchor_compare_and_swap(self):
        self.sink(provision=True)
        other_log, other_cp = self.paths("other")
        with self.assertRaises(Exception):
            service.SignedAppendOnlyAuditSink(
                other_log, other_cp, self.key, {"cache:audit:key": self.key.public_key()},
                segment_id="cache:audit:segment:other", signer_principal_id="cache:audit:principal",
                signer_key_id="cache:audit:key", audit_signing_registry_sha256=self.audit_registry_sha256,
                audit_key_validity_evidence=self.key_evidence, schema_validator=self.validator,
                maximum_record_bytes=262144, maximum_log_bytes=1048576, maximum_event_records=10,
                terminal_seal_reserved_bytes=262144, anchor_client=self.anchor,
                anchor_namespace=self.anchor_namespace, anchor_registry_sha256=self.anchor_registry_sha256,
                provision=True, governance_key=self.governance.public_key(), genesis_authorization=self.genesis("other"),
                storage_root=self.root,
            )

    def test_successor_requires_real_sealed_predecessor_and_governed_transition(self):
        first = self.sink(provision=True)
        first(self.evidence())
        sealed_checkpoint = first.seal_segment()
        terminal_record = authority.canonical_json_loads(self.paths()[0].read_text(encoding="utf-8").splitlines()[-1])
        anchor = self.anchor.read()
        transition = authority.sign_record({
            "schema_version": "cache_audit_segment_transition/v1",
            "transition_id": "cache:audit:transition:0001:0002",
            "predecessor_segment_id": "cache:audit:segment:0001",
            "predecessor_sealed_checkpoint_sha256": authority.sha256_bytes(authority.canonical_bytes(sealed_checkpoint)),
            "predecessor_terminal_record_sha256": authority.sha256_bytes(authority.canonical_bytes(terminal_record)),
            "predecessor_tail_record_sha256": anchor["tail_record_sha256"],
            "predecessor_anchor_state_sha256": authority.sha256_bytes(authority.canonical_bytes(anchor)),
            "successor_segment_id": "cache:audit:segment:0002",
            "successor_anchor_epoch": 1,
            "audit_signing_registry_sha256": self.audit_registry_sha256,
            "anchor_registry_sha256": self.anchor_registry_sha256,
            "decision": "authorize_successor_segment", "created_at": "2026-08-01T12:01:00Z",
        }, self.governance)
        successor = self.sink(
            provision=True, suffix="0002", transition_attestation=transition,
            predecessor_checkpoint=sealed_checkpoint, predecessor_terminal_record=terminal_record,
        )
        successor(self.evidence(2))
        self.assertEqual(self.anchor.read()["segment_id"], "cache:audit:segment:0002")
        self.assertEqual(self.anchor.read()["previous_sealed_segment_tail_sha256"], sealed_checkpoint["tail_record_sha256"])

    def test_arbitrary_predecessor_tail_is_not_an_api_surface(self):
        self.sink(provision=True).seal_segment()
        with self.assertRaises(TypeError):
            self.sink(provision=True, suffix="0002", previous_sealed_segment_tail_sha256="f" * 64)

    def test_normal_capacity_always_reserves_terminal_seal_record(self):
        sink = self.sink(provision=True, maximum_event_records=1)
        sink(self.evidence())
        with self.assertRaises(RuntimeError): sink(self.evidence(2))
        checkpoint = sink.seal_segment()
        self.assertEqual(checkpoint["sequence"], 2)
        self.assertEqual(checkpoint["segment_status"], "sealed")

    def test_oversized_log_is_rejected_by_fstat_before_any_log_read(self):
        self.sink(provision=True)
        self.paths()[0].write_bytes(b"x" * (5 * 1024 * 1024))
        reads = 0
        original = os.read
        def counting_read(fd, amount):
            nonlocal reads
            reads += 1
            return original(fd, amount)
        with mock.patch("cache_audit.os.read", side_effect=counting_read):
            with self.assertRaises(RuntimeError): self.sink(maximum_log_bytes=524288, terminal_seal_reserved_bytes=262144)
        self.assertEqual(reads, 0)

    def test_checkpoint_failure_removes_temporary_and_governed_recovery_reconciles(self):
        self.sink(provision=True)
        calls = 0
        def fail_checkpoint_fsync(descriptor):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("checkpoint fsync failure")
            os.fsync(descriptor)
        sink = self.sink(fsync=fail_checkpoint_fsync)
        with self.assertRaises(OSError): sink(self.evidence())
        self.assertEqual(list(self.paths()[1].parent.glob(".*.tmp")), [])
        recovery = self.sink(recovery_mode=True)
        checkpoint = authority.canonical_json_loads(self.paths()[1].read_text().strip())
        log_line = self.paths()[0].read_text().splitlines()[-1]
        authorization = authority.sign_record({
            "schema_version": "cache_audit_recovery_authorization/v1",
            "authorization_id": "cache:audit:recovery:1", "segment_id": "cache:audit:segment:0001",
            "action": "reconcile_signed_dangling_tail",
            "checkpoint_sequence_before": checkpoint["sequence"],
            "checkpoint_tail_before": checkpoint["tail_record_sha256"],
            "log_sequence_after": 1, "log_tail_after": authority.sha256_bytes(log_line.encode()),
            "decision": "authorize_governed_recovery", "created_at": "2026-08-01T12:02:00Z",
            "expires_at": "2026-08-02T12:02:00Z",
        }, self.governance)
        evidence_path = self.root / "recovery" / "recovery-1.json"
        result = recovery.recover_dangling_tail(authorization, self.governance.public_key(), evidence_path=evidence_path)
        self.assertTrue(authority.verify_record(result, self.key.public_key()))
        self.assertTrue(evidence_path.exists())
        self.assertEqual(self.sink()._sequence, 1)

    def test_event_idempotency_reconciles_ambiguous_completion_without_duplicates(self):
        sink = self.sink(provision=True)
        first = sink(self.evidence())
        second = sink(self.evidence())
        self.assertEqual(first["status"], "committed")
        self.assertEqual(second["status"], "already_committed")
        self.assertEqual(len(self.paths()[0].read_text().splitlines()), 1)

    def test_supervised_publication_is_hard_bounded_around_slow_fsync(self):
        self.sink(provision=True)
        def factory():
            def slow_fsync(descriptor):
                time.sleep(0.5)
                os.fsync(descriptor)
            return self.sink(fsync=slow_fsync)
        publisher = service.SupervisedAuditPublisher(factory)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            publisher(self.evidence(), deadline_monotonic=started + 0.05)
        self.assertLess(time.monotonic() - started, 0.2)

    def test_private_storage_directories_are_mode_0700(self):
        self.sink(provision=True)
        self.assertEqual(stat.S_IMODE(self.paths()[0].parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.paths()[1].parent.stat().st_mode), 0o700)

    def test_evidence_publication_failure_is_stable_fail_closed_error(self):
        application = service.ProofCheckApplication(
            FakeAuthority(), self.root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
            cache_verification_evidence_sink=lambda evidence: (_ for _ in ()).throw(OSError("full")),
        )
        request = proof_request(); application.handle(request, authenticated_principal_id="principal:1")
        with self.assertRaises(authority.AuthorityFailure) as caught:
            application.handle(request, authenticated_principal_id="principal:1")
        self.assertEqual(caught.exception.code, "cache_audit_publication_failed")
        application.idempotency_store.close()

if __name__ == "__main__":
    unittest.main()
