#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sqlite3
import sys
import tempfile
import unittest
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
        self.validator = authority.CanonicalSchemaValidator(ROOT / "schemas")

    def tearDown(self):
        self.temporary.cleanup()

    def sink(self) -> service.SignedAppendOnlyAuditSink:
        return service.SignedAppendOnlyAuditSink(
            self.root / "cache-audit.jsonl", self.key, self.key.public_key(),
            signer_principal_id="cache:audit:principal", signer_key_id="cache:audit:key",
            schema_validator=self.validator, maximum_record_bytes=262144,
            maximum_log_bytes=1048576, maximum_records=100,
            clock=lambda: datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
        )

    def test_signed_append_only_chain_is_durable_and_startup_verified(self):
        sink = self.sink()
        sink({"schema_version": "cache_stale_row_evidence/v3", "value": 1})
        sink({"schema_version": "cache_verification_evidence/v1", "value": 2})
        restarted = self.sink()
        self.assertEqual(restarted._sequence, 2)
        lines = (self.root / "cache-audit.jsonl").read_text(encoding="utf-8").splitlines()
        first = authority.canonical_json_loads(lines[0])
        second = authority.canonical_json_loads(lines[1])
        self.assertTrue(authority.verify_record(first, self.key.public_key()))
        self.assertTrue(authority.verify_record(second, self.key.public_key()))
        self.assertEqual(second["previous_audit_record_sha256"], authority.sha256_bytes(lines[0].encode("utf-8")))

    def test_preinitialized_sinks_serialize_against_the_latest_tail(self):
        first = self.sink()
        second = self.sink()
        first({"schema_version": "cache_stale_row_evidence/v3", "value": 1})
        second({"schema_version": "cache_stale_row_evidence/v3", "value": 2})
        restarted = self.sink()
        self.assertEqual(restarted._sequence, 2)
        lines = (self.root / "cache-audit.jsonl").read_text(encoding="utf-8").splitlines()
        first_record = authority.canonical_json_loads(lines[0])
        second_record = authority.canonical_json_loads(lines[1])
        self.assertEqual(second_record["sequence"], 2)
        self.assertEqual(
            second_record["previous_audit_record_sha256"],
            authority.sha256_bytes(lines[0].encode("utf-8")),
        )
        self.assertTrue(authority.verify_record(first_record, self.key.public_key()))
        self.assertTrue(authority.verify_record(second_record, self.key.public_key()))

    def test_tampered_audit_chain_fails_startup(self):
        sink = self.sink()
        sink({"schema_version": "cache_stale_row_evidence/v3", "value": 1})
        path = self.root / "cache-audit.jsonl"
        record = authority.canonical_json_loads(path.read_text(encoding="utf-8").strip())
        record["event_sha256"] = "0" * 64
        path.write_text(authority.canonical_bytes(record).decode("utf-8") + "\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.sink()

    def test_evidence_publication_failure_is_stable_fail_closed_error(self):
        application = service.ProofCheckApplication(
            FakeAuthority(), self.root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
            cache_verification_evidence_sink=lambda evidence: (_ for _ in ()).throw(OSError("full")),
        )
        request = proof_request()
        application.handle(request, authenticated_principal_id="principal:1")
        with self.assertRaises(authority.AuthorityFailure) as caught:
            application.handle(request, authenticated_principal_id="principal:1")
        self.assertEqual(caught.exception.code, "cache_audit_publication_failed")
        application.idempotency_store.close()


if __name__ == "__main__":
    unittest.main()
