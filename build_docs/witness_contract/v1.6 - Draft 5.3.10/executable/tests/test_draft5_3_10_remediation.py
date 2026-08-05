#!/usr/bin/env python3
from __future__ import annotations

import gc
import importlib.util
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import time
import unittest
from contextlib import closing
from datetime import datetime, timezone
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
sys.path.insert(0, str(ROOT / "executable/trusted_verifier"))
sys.path.insert(0, str(ROOT / "executable/tests"))

from proof_authority import AuthorityFailure, CanonicalSchemaValidator, EffectiveResourceLimits  # noqa: E402
from proof_check_service import (  # noqa: E402
    DurableIdempotencyStore, ProofCheckApplication,
    validate_cache_signing_registry_lineage,
)
from test_proof_check_service import FakeAuthority, FakePolicyResolver, RequestBoundaryValidator  # noqa: E402


def load_module(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class ExactSQLiteSchemaTests(unittest.TestCase):
    def _create_v1(self, path: pathlib.Path, *, table_sql: str | None = None, indexes: dict[str, str] | None = None) -> None:
        with closing(sqlite3.connect(path)) as connection:
            connection.execute(table_sql or DurableIdempotencyStore.TABLE_SQL)
            for sql in (indexes or DurableIdempotencyStore.INDEX_SQL).values():
                connection.execute(sql)
            connection.execute("PRAGMA user_version=1")
            connection.commit()

    def test_exact_v1_migrates_to_digest_bound_v2_without_losing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"
            self._create_v1(path)
            with closing(sqlite3.connect(path)) as connection:
                connection.execute(
                    "INSERT INTO proof_check_idempotency VALUES (?,?,?,?,?,?,?,?,?)",
                    ("principal", "key", "a" * 64, "inflight", "owner", time.time() + 60, None, time.time(), None),
                )
                connection.commit()
            store = DurableIdempotencyStore(path)
            with closing(sqlite3.connect(path)) as connection:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0], 1)
                self.assertEqual(
                    connection.execute("SELECT canonical_schema_sha256 FROM idempotency_schema_metadata").fetchone()[0],
                    store.canonical_schema_sha256(),
                )
            store.close()

    def test_weakened_equivalent_name_schemas_are_rejected(self):
        weak_tables = {
            "missing_pk_constraints_and_checks": """CREATE TABLE proof_check_idempotency (
                principal_id TEXT, idempotency_key TEXT, request_sha256 TEXT, state TEXT,
                lease_owner TEXT, lease_expires_at REAL, result_canonical_json TEXT,
                created_at REAL, completed_at REAL)""",
            "wrong_affinities": """CREATE TABLE proof_check_idempotency (
                principal_id BLOB NOT NULL, idempotency_key TEXT NOT NULL, request_sha256 TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('inflight','completed')), lease_owner TEXT,
                lease_expires_at TEXT, result_canonical_json TEXT, created_at INTEGER NOT NULL,
                completed_at REAL, PRIMARY KEY (principal_id,idempotency_key))""",
            "altered_default": DurableIdempotencyStore.TABLE_SQL.replace(
                "completed_at REAL,", "completed_at REAL DEFAULT 0,",
            ),
            "reordered_pk": DurableIdempotencyStore.TABLE_SQL.replace(
                "PRIMARY KEY (principal_id, idempotency_key)",
                "PRIMARY KEY (idempotency_key, principal_id)",
            ),
        }
        wrong_indexes = {
            "proof_check_idempotency_completed":
                "CREATE INDEX proof_check_idempotency_completed ON proof_check_idempotency(principal_id)",
            "proof_check_idempotency_state_lease":
                "CREATE UNIQUE INDEX proof_check_idempotency_state_lease ON proof_check_idempotency(idempotency_key DESC)",
        }
        cases = [(name, table, DurableIdempotencyStore.INDEX_SQL) for name, table in weak_tables.items()]
        cases.append(("wrong_index_columns_order_and_uniqueness", DurableIdempotencyStore.TABLE_SQL, wrong_indexes))
        for name, table, indexes in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = pathlib.Path(directory) / "cache.sqlite"
                self._create_v1(path, table_sql=table, indexes=indexes)
                with self.assertRaisesRegex(RuntimeError, "schema"):
                    DurableIdempotencyStore(path)

    def test_primary_key_uniqueness_and_state_check_are_behavioral(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"; store = DurableIdempotencyStore(path)
            with closing(sqlite3.connect(path)) as connection:
                row = ("principal", "key", "a" * 64, "inflight", "owner", time.time() + 60, None, time.time(), None)
                connection.execute("INSERT INTO proof_check_idempotency VALUES (?,?,?,?,?,?,?,?,?)", row)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("INSERT INTO proof_check_idempotency VALUES (?,?,?,?,?,?,?,?,?)", row)
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "INSERT INTO proof_check_idempotency VALUES (?,?,?,?,?,?,?,?,?)",
                        ("principal", "other", "b" * 64, "invented", None, None, None, time.time(), None),
                    )
            store.close()

    def test_schema_digest_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"; store = DurableIdempotencyStore(path)
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("UPDATE idempotency_schema_metadata SET canonical_schema_sha256=?", ("0" * 64,))
                connection.commit()
            with self.assertRaisesRegex(RuntimeError, "digest"):
                store.acquire("principal", "key", "a" * 64)
            store.close()

    def test_connect_closes_handle_when_post_open_verification_fails(self):
        descriptors = pathlib.Path("/proc/self/fd")
        if not descriptors.is_dir():
            self.skipTest("Linux descriptor accounting is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            store = DurableIdempotencyStore(pathlib.Path(directory) / "cache.sqlite")
            before = len(list(descriptors.iterdir()))
            with patch.object(store, "_verify_sqlite_schema", side_effect=RuntimeError("forced verification failure")):
                for _ in range(50):
                    with self.assertRaisesRegex(RuntimeError, "forced"):
                        store._connect()
            gc.collect()
            after = len(list(descriptors.iterdir()))
            self.assertLessEqual(after, before + 1)
            store.close()

    def test_unsupported_version_failure_is_warning_and_descriptor_clean(self):
        descriptors = pathlib.Path("/proc/self/fd")
        if not descriptors.is_dir():
            self.skipTest("Linux descriptor accounting is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"; store = DurableIdempotencyStore(path)
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("PRAGMA user_version=99")
            before = len(list(descriptors.iterdir()))
            for _ in range(20):
                with self.assertRaisesRegex(RuntimeError, "version"):
                    store.acquire("principal", "key", "a" * 64)
            gc.collect()
            self.assertLessEqual(len(list(descriptors.iterdir())), before + 1)
            store.close()


class CacheKeyLifecycleTests(unittest.TestCase):
    @staticmethod
    def record(key_id: str = "cache:key", **changes) -> dict:
        value = {
            "key_id": key_id, "principal_id": "cache:principal",
            "public_key_base64url": "A" * 43,
            "authorization_scope": "idempotency_cache_envelope_signing",
            "status": "active", "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "status_changed_at": "2026-01-01T00:00:00Z",
            "rotation_predecessor_key_id": None,
        }
        value.update(changes)
        return value

    @classmethod
    def registry(cls, keys: list[dict] | None = None) -> dict:
        return {"keys": keys or [cls.record()]}

    def test_rotation_predecessors_are_complete_ordered_and_acyclic(self):
        missing = self.registry([self.record(rotation_predecessor_key_id="missing")])
        with self.assertRaisesRegex(RuntimeError, "missing"):
            validate_cache_signing_registry_lineage(missing)
        first = self.record("cache:first", valid_from="2025-01-01T00:00:00Z", status="retired")
        second = self.record("cache:second", rotation_predecessor_key_id="cache:first")
        validate_cache_signing_registry_lineage(self.registry([first, second]))
        first["rotation_predecessor_key_id"] = "cache:second"
        with self.assertRaisesRegex(RuntimeError, "cycle|older"):
            validate_cache_signing_registry_lineage(self.registry([first, second]))

    def test_malformed_valid_until_is_schema_invalid(self):
        validator = CanonicalSchemaValidator(ROOT / "schemas")
        registry = {
            "schema_version": "cache_signing_registry/v2", "registry_id": "registry:1",
            "governance_key_id": "governance:1", "created_at": "2026-01-01T00:00:00Z",
            "keys": [self.record(valid_until="not-a-date")],
            "signed_payload_sha256": "a" * 64, "signature": "A" * 86,
        }
        with self.assertRaises(AuthorityFailure):
            validator.validate("cache_signing_registry", registry)

    def test_future_expired_retired_and_revoked_keys_fail_closed(self):
        authority = FakeAuthority(); cache_key = Ed25519PrivateKey.generate()
        base = {
            "key_id": "cache:key", "principal_id": "cache:principal",
            "public_key_base64url": __import__("proof_authority").public_key_raw_b64url(cache_key.public_key()),
            "authorization_scope": "idempotency_cache_envelope_signing",
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2027-01-01T00:00:00Z",
            "status_changed_at": "2026-01-01T00:00:00Z", "rotation_predecessor_key_id": None,
        }
        clock = lambda: datetime(2026, 8, 1, tzinfo=timezone.utc)
        cases = {
            "future": {**base, "status": "active", "valid_from": "2099-01-01T00:00:00Z", "status_changed_at": "2099-01-01T00:00:00Z"},
            "expired": {**base, "status": "active", "valid_until": "2026-02-01T00:00:00Z"},
            "retired": {**base, "status": "retired"},
            "revoked": {**base, "status": "revoked"},
        }
        for name, record in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(AuthorityFailure):
                    ProofCheckApplication(
                        authority, pathlib.Path(directory), FakePolicyResolver(),
                        schema_validator=RequestBoundaryValidator(), cache_signing_key=cache_key,
                        cache_signer_principal_id="cache:principal", cache_signer_key_id="cache:key",
                        cache_key_record=record, cache_registry_sha256="b" * 64,
                        cache_clock=clock,
                    )

    def test_cache_replay_rechecks_current_key_and_records_registry_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); bundle = root / "bundle-1"; bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n")
            evidence: list[dict] = []
            application = ProofCheckApplication(
                FakeAuthority(), root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
                cache_verification_evidence_sink=evidence.append,
            )
            request = DeadlineAndCompileEvidenceTests.request()
            first = application.handle(request, authenticated_principal_id="principal:1")
            replay = application.handle(request, authenticated_principal_id="principal:1")
            self.assertEqual(first, replay); self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["cache_registry_sha256"], application.cache_registry_sha256)
            self.assertEqual(evidence[0]["replay_decision"]["decision"], "active_time_valid_rotation_valid")
            application.cache_key_record["status"] = "revoked"
            with self.assertRaisesRegex(AuthorityFailure, "retired or revoked"):
                application.handle(request, authenticated_principal_id="principal:1")


class DeadlineAndCompileEvidenceTests(unittest.TestCase):
    @staticmethod
    def request() -> dict:
        return {
            "request_id": "request:deadline", "idempotency_key": "idempotency:deadline",
            "compiler_profile_id": "profile:governed", "claim_id": "claim:1",
            "canonical_claim": {"statement": "True"}, "theorem_statement": "True",
            "theorem_name": "t", "source_bundle_id": "bundle-1",
            "proof_artifact_relative_path": "Proof.lean", "policy_decision_id": "policy:1",
        }

    def _application(self, root: pathlib.Path, authority: FakeAuthority, *, timeout: int = 1):
        bundle = root / "bundle-1"; bundle.mkdir(); (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n")
        class Policy(FakePolicyResolver):
            def resolve(self, policy_decision_id, **arguments):
                result = super().resolve(policy_decision_id, **arguments)
                result.effective_limits = lambda: EffectiveResourceLimits(timeout, 1000000, 134217728, 536870912, 4194304, 1048576, 1048576, 1048576, 2097152)
                return result
        return ProofCheckApplication(authority, root, Policy(), schema_validator=RequestBoundaryValidator())

    def test_deadline_expiry_during_cache_signing_cannot_publish_success(self):
        import proof_check_service
        real_sign = proof_check_service.sign_record
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); application = self._application(root, FakeAuthority())
            def delayed_sign(*arguments, **keywords):
                time.sleep(1.05)
                return real_sign(*arguments, **keywords)
            with patch.object(proof_check_service, "sign_record", side_effect=delayed_sign):
                with self.assertRaisesRegex(TimeoutError, "cache-envelope signing"):
                    application.handle(self.request(), authenticated_principal_id="principal:1")
            with closing(sqlite3.connect(root / ".proof-check-idempotency.sqlite")) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0], 0)

    def test_deadline_expiry_during_authority_execution_cannot_publish_success(self):
        class SlowAuthority(FakeAuthority):
            def verify(self, **arguments):
                time.sleep(1.05)
                return super().verify(**arguments)
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); application = self._application(root, SlowAuthority())
            with self.assertRaisesRegex(TimeoutError, "authority execution"):
                application.handle(self.request(), authenticated_principal_id="principal:1")
            with closing(sqlite3.connect(root / ".proof-check-idempotency.sqlite")) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0], 0)

    def test_owner_fenced_final_renewal_prevents_publication_after_lease_loss(self):
        class LostLeaseStore(DurableIdempotencyStore):
            def renew(self, *arguments, **keywords):
                return False
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); bundle = root / "bundle-1"; bundle.mkdir()
            (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n")
            store = LostLeaseStore(root / "cache.sqlite", lease_seconds=60)
            application = ProofCheckApplication(
                FakeAuthority(), root, FakePolicyResolver(), idempotency_store=store,
                schema_validator=RequestBoundaryValidator(),
            )
            with self.assertRaisesRegex(RuntimeError, "lease was lost"):
                application.handle(self.request(), authenticated_principal_id="principal:1")
            with closing(sqlite3.connect(root / "cache.sqlite")) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0], 0)
            store.close()

    def test_sqlite_busy_wait_consumes_only_remaining_request_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"; store = DurableIdempotencyStore(path)
            with closing(sqlite3.connect(path, isolation_level=None)) as blocker:
                blocker.execute("BEGIN IMMEDIATE")
                started = time.monotonic()
                with self.assertRaises((sqlite3.OperationalError, TimeoutError)):
                    store.acquire("principal", "key", "a" * 64, deadline_monotonic=started + 0.12)
                self.assertLess(time.monotonic() - started, 0.6)
                blocker.execute("ROLLBACK")
            store.close()

    def test_trusted_consumer_recomputes_ordered_complete_compile_commands(self):
        compile_lean = load_module("draft5310_compile", "executable/trusted_verifier/compile_lean.py")
        verify_lean = load_module("draft5310_verify", "executable/trusted_verifier/verify_lean.py")
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); source = root / "source"; source.mkdir()
            (source / "Proof.lean").write_text("theorem t : True := by trivial\n")
            generated = root / "generated"; generated.mkdir(); (generated / "Binding.lean").write_text("import Proof\n")
            handoff = root / "handoff"; handoff.mkdir(); work = root / "work/project"
            lean = root / "lean"; lean.write_text(
                "#!/usr/bin/env python3\nimport pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index('-o')+1]);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'olean')\n"
            ); lean.chmod(0o755)
            with patch.multiple(compile_lean, SOURCE=source, GENERATED=generated, HANDOFF=handoff, WORK=work, LEAN=lean), patch.object(
                sys, "argv", ["compile-lean", "--generated", str(generated), "--artifact-limit", "1000000", "--handoff-limit", "2000000"],
            ):
                self.assertEqual(compile_lean.main(), 0)
            manifest_path = handoff / "compile-manifest.json"
            original = json.loads(manifest_path.read_text())
            invocation = {"handoff_total_bytes_limit": 2000000, "compiler_artifact_file_size_limit": 1000000}
            profile = {"lean_executable_sha256": compile_lean.digest(lean)}
            mutations = []
            altered = json.loads(json.dumps(original)); altered["compilation_commands"][0]["argv_sha256"] = "0" * 64; mutations.append(altered)
            reordered = json.loads(json.dumps(original)); reordered["compilation_commands"].reverse(); mutations.append(reordered)
            missing = json.loads(json.dumps(original)); missing["compilation_commands"].pop(); mutations.append(missing)
            extra = json.loads(json.dumps(original)); extra["compilation_commands"].append(dict(extra["compilation_commands"][0])); mutations.append(extra)
            validator = CanonicalSchemaValidator(ROOT / "schemas")
            for mutation in mutations:
                manifest_path.write_text(json.dumps(mutation, sort_keys=True, separators=(",", ":")))
                with patch.multiple(verify_lean, HANDOFF=handoff, HANDOFF_OLEAN=handoff / "olean", WORK=work, LEAN=lean):
                    with self.assertRaises((ValueError, AuthorityFailure)):
                        verify_lean.validate_handoff(validator, invocation, profile)


if __name__ == "__main__":
    unittest.main()
