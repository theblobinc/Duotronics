#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import pathlib
import sqlite3
import sys
import tempfile
import threading
import types
import unittest
from contextlib import closing

from executable.runtime.pq_provider import MLDSA87PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))

from proof_authority import (  # noqa: E402
    AuthorityFailure, CanonicalSchemaValidator, EffectiveResourceLimits,
    canonical_bytes, shake256_512_bytes, sign_record,
)
from proof_check_service import DurableIdempotencyStore, ProofCheckApplication  # noqa: E402
from proof_check_wsgi import AUTHENTICATED_PRINCIPAL_ENVIRON_KEY, ProofCheckWSGI  # noqa: E402


class RequestBoundaryValidator:
    def __init__(self):
        self.real = CanonicalSchemaValidator(ROOT / "schemas")

    def validate(self, surface, value):
        if surface == "proof_check_request":
            self.real.validate(surface, value)


class FakeAuthority:
    def __init__(self):
        self.arguments = None
        self.calls = 0
        self.signing_key = MLDSA87PrivateKey.generate()
        self.key_id = "witness-key:test"
        self.verifier_principal_id = "verifier:test"

    def verify(self, **arguments):
        self.calls += 1
        self.arguments = arguments
        return sign_record({
            "schema_version": "lean_compiler_witness/v7",
            "lean_compiler_witness_id": "lean:test",
            "semantic_witness_content_id": "lean-semantic:" + "1" * 128,
            "execution_evidence_content_id": "lean-execution:" + "2" * 128,
            "service_request_id": arguments["service_request_id"],
            "authenticated_principal_id": arguments["authenticated_principal_id"],
            "source_bundle_id": arguments["source_bundle_id"],
            "claim_id": arguments["claim_id"],
            "claim_content_shake256_512": shake256_512_bytes(canonical_bytes(arguments["canonical_claim"])),
            "theorem_statement_shake256_512": shake256_512_bytes(arguments["theorem_statement"].encode("utf-8")),
            "compiler_profile_id": arguments["compiler_profile_id"],
            "policy_decision_id": arguments["policy_decision_id"],
            "policy_decision_shake256_512": arguments["policy_decision_shake256_512"],
            "proof_artifact_relative_path": arguments["proof_artifact"].relative_to(arguments["source_root"]).as_posix(),
            "result": "passed", "key_id": self.key_id,
            "verifier_principal_id": self.verifier_principal_id,
        }, self.signing_key)


class FakePolicyResolver:
    def __init__(self):
        self.arguments = None
        self.calls = 0

    def resolve(self, policy_decision_id, **arguments):
        self.calls += 1
        self.arguments = {"policy_decision_id": policy_decision_id, **arguments}
        return types.SimpleNamespace(
            policy_decision_id=policy_decision_id, canonical_record_shake256_512="a" * 128,
            effective_limits=lambda: EffectiveResourceLimits(600, 1000000, 134217728, 536870912, 4194304, 1048576, 1048576, 1048576, 2097152),
        )


class ProofCheckServiceTests(unittest.TestCase):
    PRINCIPAL = "principal:1"

    def request(self):
        return {
            "request_id": "request:1", "idempotency_key": "idempotency:1",
            "compiler_profile_id": "profile:governed", "claim_id": "claim:1",
            "canonical_claim": {"statement": "True"}, "theorem_statement": "True",
            "theorem_name": "t", "source_bundle_id": "bundle-1",
            "proof_artifact_relative_path": "Proof.lean", "policy_decision_id": "policy:1",
        }

    def application(self, directory, *, authority=None, policy=None, store=None):
        root = pathlib.Path(directory)
        bundle = root / "bundle-1"
        bundle.mkdir(exist_ok=True)
        (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
        authority = authority or FakeAuthority()
        policy = policy or FakePolicyResolver()
        application = ProofCheckApplication(
            authority, root, policy, idempotency_store=store,
            schema_validator=RequestBoundaryValidator(),
        )
        return application, authority, policy

    def test_exact_request_uses_authenticated_principal_and_preserves_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            application, authority, policy = self.application(directory)
            result = application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
        self.assertEqual(authority.arguments["compiler_profile_id"], "profile:governed")
        self.assertEqual(authority.arguments["authenticated_principal_id"], self.PRINCIPAL)
        self.assertEqual(policy.arguments["subject_id"], self.PRINCIPAL)
        self.assertEqual(result["authenticated_principal_id"], self.PRINCIPAL)

    def test_caller_controlled_subject_id_is_forbidden(self):
        with tempfile.TemporaryDirectory() as directory:
            application, _, _ = self.application(directory)
            request = self.request(); request["subject_id"] = "principal:other"
            with self.assertRaisesRegex(ValueError, "schema validation"):
                application.handle(request, authenticated_principal_id=self.PRINCIPAL)

    def test_request_cannot_supply_path_hash_environment_or_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            application, _, _ = self.application(directory)
            for forbidden, value in (
                ("lake_executable", "/tmp/fake-lake"), ("expected_lake_shake256_512", "0" * 128),
                ("environment", {"LEAN_PATH": "/attacker"}), ("created_at", "2020-01-01T00:00:00Z"),
            ):
                request = self.request(); request[forbidden] = value
                with self.assertRaisesRegex(ValueError, "schema validation"):
                    application.handle(request, authenticated_principal_id=self.PRINCIPAL)

    def test_bundle_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            application, _, _ = self.application(directory)
            request = self.request(); request["proof_artifact_relative_path"] = "../outside.lean"
            with self.assertRaisesRegex(ValueError, "proof_artifact_relative_path"):
                application.handle(request, authenticated_principal_id=self.PRINCIPAL)

    def test_cache_hit_revalidates_policy_witness_signature_and_all_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            application, authority, policy = self.application(directory)
            expected = application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
            replay = application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
            self.assertEqual(expected, replay)
            self.assertEqual(authority.calls, 1)
            self.assertEqual(policy.calls, 2)

    def test_schema_valid_cache_row_with_invalid_witness_signature_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            application, _, _ = self.application(directory)
            application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
            database = pathlib.Path(directory) / ".proof-check-idempotency.sqlite"
            with closing(sqlite3.connect(database)) as connection:
                envelope = json.loads(connection.execute("SELECT result_canonical_json FROM proof_check_idempotency").fetchone()[0])
                envelope["result"]["compiler_witness"]["service_request_id"] = "request:tampered"
                envelope = sign_record(envelope, application.cache_signing_key)
                connection.execute("UPDATE proof_check_idempotency SET result_canonical_json=?", (canonical_bytes(envelope).decode("utf-8"),))
                connection.commit()
            with self.assertRaisesRegex(AuthorityFailure, "compiler-witness signature"):
                application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)

    def test_cache_hit_rejects_resigned_witness_binding_and_signer_mismatches(self):
        cases = (
            ("service_request_id", "request:other"),
            ("authenticated_principal_id", "principal:other"),
            ("source_bundle_id", "bundle-other"),
            ("claim_id", "claim:other"),
            ("claim_content_shake256_512", "0" * 128),
            ("theorem_statement_shake256_512", "0" * 128),
            ("compiler_profile_id", "profile:other"),
            ("policy_decision_id", "policy:other"),
            ("policy_decision_shake256_512", "0" * 128),
            ("proof_artifact_relative_path", "Other.lean"),
            ("key_id", "witness-key:unauthorized"),
            ("verifier_principal_id", "verifier:unauthorized"),
        )
        for field, value in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                application, authority, _ = self.application(directory)
                application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
                database = pathlib.Path(directory) / ".proof-check-idempotency.sqlite"
                with closing(sqlite3.connect(database)) as connection:
                    envelope = json.loads(connection.execute("SELECT result_canonical_json FROM proof_check_idempotency").fetchone()[0])
                    witness = envelope["result"]["compiler_witness"]
                    witness[field] = value
                    envelope["result"]["compiler_witness"] = sign_record(witness, authority.signing_key)
                    envelope = sign_record(envelope, application.cache_signing_key)
                    connection.execute("UPDATE proof_check_idempotency SET result_canonical_json=?", (canonical_bytes(envelope).decode("utf-8"),))
                    connection.commit()
                with self.assertRaises(AuthorityFailure):
                    application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)

    def test_cache_hit_rejects_outer_status_that_differs_from_signed_witness(self):
        with tempfile.TemporaryDirectory() as directory:
            application, _, _ = self.application(directory)
            application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
            database = pathlib.Path(directory) / ".proof-check-idempotency.sqlite"
            with closing(sqlite3.connect(database)) as connection:
                envelope = json.loads(connection.execute("SELECT result_canonical_json FROM proof_check_idempotency").fetchone()[0])
                envelope["result"]["status"] = "failed"
                envelope = sign_record(envelope, application.cache_signing_key)
                connection.execute("UPDATE proof_check_idempotency SET result_canonical_json=?", (canonical_bytes(envelope).decode("utf-8"),))
                connection.commit()
            with self.assertRaisesRegex(AuthorityFailure, "outer result status"):
                application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)

    def test_concurrent_identical_idempotency_key_shares_one_execution(self):
        class SlowAuthority(FakeAuthority):
            def __init__(self):
                super().__init__(); self.entered = threading.Event(); self.release = threading.Event()
            def verify(self, **arguments):
                self.entered.set(); self.release.wait(5)
                return super().verify(**arguments)

        with tempfile.TemporaryDirectory() as directory:
            authority = SlowAuthority()
            application, _, _ = self.application(directory, authority=authority)
            results = []
            first = threading.Thread(target=lambda: results.append(application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)))
            second = threading.Thread(target=lambda: results.append(application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)))
            first.start(); self.assertTrue(authority.entered.wait(2)); second.start(); authority.release.set()
            first.join(5); second.join(5)
        self.assertEqual(authority.calls, 1); self.assertEqual(len(results), 2); self.assertEqual(results[0], results[1])


class DurableIdempotencyStoreTests(unittest.TestCase):
    def test_global_and_per_principal_inflight_limits_and_expiry_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "idem.sqlite"
            store = DurableIdempotencyStore(path, maximum_inflight_rows=2, maximum_inflight_rows_per_principal=1)
            self.assertEqual(store.acquire("alice", "a", "1" * 128)[0], "execute")
            with self.assertRaisesRegex(RuntimeError, "in-flight"):
                store.acquire("alice", "b", "2" * 128)
            self.assertEqual(store.acquire("bob", "b", "2" * 128)[0], "execute")
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("UPDATE proof_check_idempotency SET lease_expires_at=0 WHERE principal_id='alice'")
                connection.commit()
            self.assertEqual(store.acquire("carol", "c", "3" * 128)[0], "execute")

    def test_repeated_operations_do_not_leak_file_descriptors(self):
        descriptor_root = pathlib.Path("/proc/self/fd")
        if not descriptor_root.is_dir():
            self.skipTest("Linux descriptor accounting is unavailable")
        with tempfile.TemporaryDirectory() as directory:
            store = DurableIdempotencyStore(pathlib.Path(directory) / "idem.sqlite", maximum_inflight_rows=100)
            before = len(list(descriptor_root.iterdir()))
            for index in range(50):
                key = f"key:{index}"; digest = f"{index:064x}"
                action, owner = store.acquire("principal", key, digest)
                self.assertEqual(action, "execute")
                store.complete("principal", key, str(owner), digest, {"envelope": index})
                self.assertEqual(store.acquire("principal", key, digest)[0], "completed")
            after = len(list(descriptor_root.iterdir()))
        self.assertLessEqual(after, before + 2)

    def test_total_row_completed_row_and_database_byte_admission_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "rows.sqlite"
            store = DurableIdempotencyStore(
                path, maximum_completed_rows=1, maximum_inflight_rows=10,
                maximum_inflight_rows_per_principal=10, maximum_total_rows=2,
            )
            for index in range(2):
                digest = f"{index:064x}"; key = f"key:{index}"
                action, owner = store.acquire("principal", key, digest)
                self.assertEqual(action, "execute")
                store.complete("principal", key, str(owner), digest, {"value": index})
            action, _ = store.acquire("principal", "key:2", f"{2:064x}")
            self.assertEqual(action, "execute")
            with closing(sqlite3.connect(path)) as connection:
                completed = connection.execute("SELECT count(*) FROM proof_check_idempotency WHERE state='completed'").fetchone()[0]
                total = connection.execute("SELECT count(*) FROM proof_check_idempotency").fetchone()[0]
            self.assertLessEqual(completed, 1); self.assertLessEqual(total, 2)
        with tempfile.TemporaryDirectory() as directory:
            store = DurableIdempotencyStore(
                pathlib.Path(directory) / "bytes.sqlite", maximum_database_bytes=1,
            )
            with self.assertRaisesRegex(RuntimeError, "byte admission"):
                store.acquire("principal", "key", "1" * 128)

    def test_database_path_rejects_unsafe_parent_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            unsafe = root / "unsafe"; unsafe.mkdir(mode=0o755)
            with self.assertRaisesRegex(RuntimeError, "parent ownership or mode"):
                DurableIdempotencyStore(unsafe / "cache.sqlite")
            safe = root / "safe"; safe.mkdir(mode=0o700)
            target = safe / "target.sqlite"; target.write_bytes(b"")
            link = safe / "link.sqlite"; link.symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, "unsafe SQLite file identity"):
                DurableIdempotencyStore(link)


class ProofCheckWSGITests(unittest.TestCase):
    class Application:
        def __init__(self): self.principal = None
        def handle(self, request, *, authenticated_principal_id):
            self.principal = authenticated_principal_id
            return {"ok": True}

    @staticmethod
    def invoke(adapter, request, principal=None):
        body = canonical_bytes(request); status = []
        environ = {
            "REQUEST_METHOD": "POST", "PATH_INFO": "/v2/proof-checks",
            "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(body)),
            "HTTP_IDEMPOTENCY_KEY": request["idempotency_key"], "wsgi.input": io.BytesIO(body),
        }
        if principal is not None: environ[AUTHENTICATED_PRINCIPAL_ENVIRON_KEY] = principal
        response = b"".join(adapter(environ, lambda value, headers: status.append(value)))
        return status[0], json.loads(response)

    def test_verified_middleware_principal_is_required(self):
        application = self.Application(); adapter = ProofCheckWSGI(application)
        status, result = self.invoke(adapter, {"idempotency_key": "key"})
        self.assertEqual(status, "403 Forbidden"); self.assertEqual(result["error"], "governance_authorization_invalid")
        status, _ = self.invoke(adapter, {"idempotency_key": "key"}, "principal:1")
        self.assertEqual(status, "200 OK"); self.assertEqual(application.principal, "principal:1")


if __name__ == "__main__":
    unittest.main()
