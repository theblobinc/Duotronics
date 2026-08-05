#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from contextlib import closing
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "executable/runtime"))
sys.path.insert(0, str(ROOT / "executable/trusted_verifier"))
sys.path.insert(0, str(ROOT / "executable/tests"))

from proof_authority import CanonicalSchemaValidator, OciSandboxRunner, canonical_bytes, sha256_bytes  # noqa: E402
from proof_check_service import DurableIdempotencyStore, ProofCheckApplication  # noqa: E402
from test_proof_check_service import FakeAuthority, FakePolicyResolver, RequestBoundaryValidator  # noqa: E402


def load_module(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class CompileHandoffIntegrationTests(unittest.TestCase):
    def _fake_lean(self, root: pathlib.Path, *, warning: bool = False) -> pathlib.Path:
        executable = root / "lean"
        warning_line = "print('warning: governed test warning', file=sys.stderr)" if warning else ""
        executable.write_text(
            "#!/usr/bin/env python3\nimport pathlib,sys\n"
            + warning_line + "\n"
            + "target=pathlib.Path(sys.argv[sys.argv.index('-o')+1]); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(('olean:'+sys.argv[-1]).encode())\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        return executable

    def test_true_producer_output_is_accepted_by_trusted_consumer(self):
        compile_lean = load_module("draft539_compile_lean", "executable/trusted_verifier/compile_lean.py")
        verify_lean = load_module("draft539_verify_lean", "executable/trusted_verifier/verify_lean.py")
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source = root / "source"; source.mkdir(); (source / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            generated = root / "generated"; (generated / "WitnessAuthorityGenerated").mkdir(parents=True)
            binding = generated / "WitnessAuthorityGenerated/Check_deadbeef.lean"
            binding.write_text("import Proof\n#check t\n", encoding="utf-8")
            handoff = root / "handoff"; handoff.mkdir(mode=0o700)
            work = root / "work/project"
            lean = self._fake_lean(root)
            with patch.multiple(compile_lean, SOURCE=source, GENERATED=generated, HANDOFF=handoff, WORK=work, LEAN=lean), patch.object(
                sys, "argv", ["compile-lean", "--generated", "/input/generated", "--artifact-limit", "1000000", "--handoff-limit", "2000000"]
            ):
                self.assertEqual(compile_lean.main(), 0)
            manifest = json.loads((handoff / "compile-manifest.json").read_text(encoding="utf-8"))
            binding_records = [item for item in manifest["compiled_modules"] if item["role"] == "generated_binding"]
            self.assertEqual(len(binding_records), 1)
            invocation = {"handoff_total_bytes_limit": 2000000, "compiler_artifact_file_size_limit": 1000000}
            with patch.multiple(verify_lean, HANDOFF=handoff, HANDOFF_OLEAN=handoff / "olean"):
                accepted, _ = verify_lean.validate_handoff(CanonicalSchemaValidator(ROOT / "schemas"), invocation)
            self.assertEqual(accepted, manifest)

    def test_warning_diagnostic_fails_even_when_lean_exits_zero(self):
        compile_lean = load_module("draft539_compile_warning", "executable/trusted_verifier/compile_lean.py")
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            source = root / "source"; source.mkdir(); (source / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
            generated = root / "generated"; generated.mkdir(); (generated / "Binding.lean").write_text("import Proof\n", encoding="utf-8")
            handoff = root / "handoff"; handoff.mkdir(); work = root / "work/project"
            with patch.multiple(compile_lean, SOURCE=source, GENERATED=generated, HANDOFF=handoff, WORK=work, LEAN=self._fake_lean(root, warning=True)), patch.object(
                sys, "argv", ["compile-lean", "--generated", "/input/generated", "--artifact-limit", "1000000", "--handoff-limit", "2000000"]
            ):
                self.assertEqual(compile_lean.main(), 1)
            self.assertFalse((handoff / "compile-manifest.json").exists())


class LifecycleAndDatabaseTests(unittest.TestCase):
    PRINCIPAL = "principal:1"

    @staticmethod
    def request() -> dict:
        return {
            "request_id": "request:lease", "idempotency_key": "idempotency:lease",
            "compiler_profile_id": "profile:governed", "claim_id": "claim:1",
            "canonical_claim": {"statement": "True"}, "theorem_statement": "True", "theorem_name": "t",
            "source_bundle_id": "bundle-1", "proof_artifact_relative_path": "Proof.lean", "policy_decision_id": "policy:1",
        }

    def _application(self, root: pathlib.Path, authority: FakeAuthority, store: DurableIdempotencyStore) -> ProofCheckApplication:
        bundle = root / "bundle-1"; bundle.mkdir(); (bundle / "Proof.lean").write_text("theorem t : True := by trivial\n", encoding="utf-8")
        return ProofCheckApplication(authority, root, FakePolicyResolver(), idempotency_store=store, schema_validator=RequestBoundaryValidator())

    def test_active_execution_renews_owner_fenced_lease(self):
        class SlowAuthority(FakeAuthority):
            def verify(self, **arguments):
                time.sleep(0.28)
                return super().verify(**arguments)
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); store = DurableIdempotencyStore(root / "cache.sqlite", lease_seconds=0.09)
            authority = SlowAuthority(); application = self._application(root, authority, store)
            results: list[dict] = []
            first = threading.Thread(target=lambda: results.append(application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)))
            first.start(); time.sleep(0.16)
            replay = application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL)
            first.join(timeout=2)
            self.assertEqual(len(results), 1); self.assertEqual(replay, results[0]); self.assertEqual(authority.calls, 1)

    def test_one_monotonic_deadline_is_passed_to_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); authority = FakeAuthority()
            application = self._application(root, authority, DurableIdempotencyStore(root / "cache.sqlite"))
            before = time.monotonic(); application.handle(self.request(), authenticated_principal_id=self.PRINCIPAL); after = time.monotonic()
            deadline = authority.arguments["request_deadline_monotonic"]
            self.assertGreater(deadline, before); self.assertLessEqual(deadline - after, authority.arguments["timeout_seconds"])

    def test_production_rejects_cache_and_witness_key_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); authority = FakeAuthority()
            with self.assertRaisesRegex(ValueError, "must be distinct"):
                ProofCheckApplication(
                    authority, root, FakePolicyResolver(), schema_validator=RequestBoundaryValidator(),
                    cache_signing_key=authority.signing_key, cache_signer_principal_id="cache:one",
                    cache_signer_key_id="cache:key", production_mode=True,
                )

    def test_completion_bound_rejects_growth_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"
            store = DurableIdempotencyStore(path, maximum_database_bytes=200000, maximum_cache_envelope_bytes=30000)
            action, owner = store.acquire("principal", "key", "a" * 64); self.assertEqual(action, "execute")
            with self.assertRaisesRegex(RuntimeError, "envelope byte limit"):
                store.complete("principal", "key", str(owner), "a" * 64, {"payload": "x" * 100000})
            size = sum(candidate.stat().st_size for candidate in path.parent.glob("cache.sqlite*") if candidate.is_file())
            self.assertLessEqual(size, 200000)

    def test_cached_json_must_be_duplicate_free_and_canonical(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "cache.sqlite"; store = DurableIdempotencyStore(path)
            _, owner = store.acquire("principal", "key", "a" * 64); store.complete("principal", "key", str(owner), "a" * 64, {"a": 1})
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("UPDATE proof_check_idempotency SET result_canonical_json=?", ('{"a":1,"a":1}',)); connection.commit()
            with self.assertRaisesRegex(RuntimeError, "canonical duplicate-free"):
                store.acquire("principal", "key", "a" * 64)

    def test_schema_version_and_unexpected_objects_fail_closed(self):
        for mutation in ("PRAGMA user_version=99", "CREATE TRIGGER injected AFTER INSERT ON proof_check_idempotency BEGIN SELECT 1; END"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = pathlib.Path(directory) / "cache.sqlite"; store = DurableIdempotencyStore(path)
                with closing(sqlite3.connect(path)) as connection:
                    connection.execute(mutation); connection.commit()
                with self.assertRaisesRegex(RuntimeError, "schema"):
                    store.acquire("principal", "key", "a" * 64)

    def test_complete_database_ancestry_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); root.chmod(0o770)
            parent = root / "private"; parent.mkdir(mode=0o700)
            with self.assertRaisesRegex(RuntimeError, "ancestry"):
                DurableIdempotencyStore(parent / "cache.sqlite")


class GovernedBuildContractTests(unittest.TestCase):
    def test_keep_id_handoff_is_host_sealed_for_trusted_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            handoff = pathlib.Path(directory) / "handoff"; nested = handoff / "olean/Generated"
            nested.mkdir(parents=True, mode=0o700); artifact = nested / "Binding.olean"; artifact.write_bytes(b"sealed")
            runner = OciSandboxRunner.__new__(OciSandboxRunner)
            runner.authority_uid = os.getuid(); runner.authority_gid = os.getgid()
            evidence = runner._seal_handoff(handoff)
            self.assertEqual(evidence["root_mode"], "0550")
            self.assertEqual(oct(artifact.stat().st_mode & 0o777), "0o440")
            self.assertEqual(oct(nested.stat().st_mode & 0o777), "0o550")
            self.assertEqual(artifact.read_bytes(), b"sealed")

    def test_inspector_uses_only_sealed_handoff_search_root(self):
        source = (ROOT / "formal/draft5_3_6/lean/WitnessAuthority/InspectorMain.lean").read_text(encoding="utf-8")
        self.assertIn('handoffRoot != "/handoff"', source)
        self.assertIn('handoffReal / "olean"', source)
        self.assertIn("initSearchPath sysroot [handoffOLean]", source)
        self.assertIn('getEnv "LEAN_PATH"', source)

    def test_build_and_lake_select_same_source_generation(self):
        containerfile = (ROOT / "executable/trusted_verifier/Containerfile.inspector-build").read_text(encoding="utf-8")
        build_script = (ROOT / "executable/formal/build_trusted_inspector.py").read_text(encoding="utf-8")
        lakefile = (ROOT / "lakefile.lean").read_text(encoding="utf-8")
        self.assertIn("formal/draft5_3_6/lean", containerfile)
        self.assertIn('Path("formal/draft5_3_6/lean")', build_script)
        self.assertIn("WitnessAuthority", lakefile)
        self.assertNotIn("formal/draft5_3_5/lean", containerfile)

    def test_runtime_container_pins_python_cryptography_and_lean_tools(self):
        source = (ROOT / "executable/trusted_verifier/Containerfile").read_text(encoding="utf-8")
        for literal in ("PYTHON_VERSION=3.12.13", "CRYPTOGRAPHY_VERSION=46.0.0", "lean --version", "lake --version", "inspect-lean --version"):
            self.assertIn(literal, source)


if __name__ == "__main__":
    unittest.main()
