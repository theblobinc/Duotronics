#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class Draft5317RegenerationTests(unittest.TestCase):
    def test_schema_registry_regenerates_byte_for_byte(self) -> None:
        expected = (ROOT / "SCHEMA_REGISTRY_v1_6_draft_5_3_17.json").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            copy_root = pathlib.Path(directory) / "corpus"
            (copy_root / "executable/validators").mkdir(parents=True)
            (copy_root / "validation").mkdir(parents=True)
            shutil.copytree(ROOT / "schemas", copy_root / "schemas")
            shutil.copy2(ROOT / "validation/identity.py", copy_root / "validation/identity.py")
            shutil.copy2(ROOT / "executable/validators/build_schema_registry_v5317.py", copy_root / "executable/validators/build_schema_registry_v5317.py")
            completed = subprocess.run(
                [sys.executable, "executable/validators/build_schema_registry_v5317.py"],
                cwd=copy_root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual((copy_root / "SCHEMA_REGISTRY_v1_6_draft_5_3_17.json").read_bytes(), expected)

    def test_registry_covers_every_schema(self) -> None:
        registry = json.loads((ROOT / "SCHEMA_REGISTRY_v1_6_draft_5_3_17.json").read_text(encoding="utf-8"))
        registered = {item["path"] for item in registry["schemas"]}
        actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / "schemas").glob("*.schema.json")}
        self.assertEqual(registered, actual)
        self.assertEqual(registry["active_schema_count"], 7)


if __name__ == "__main__":
    unittest.main()
