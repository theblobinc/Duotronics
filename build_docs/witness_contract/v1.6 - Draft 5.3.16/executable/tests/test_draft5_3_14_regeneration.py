#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class Draft5314RegenerationTests(unittest.TestCase):
    def test_schema_registry_regenerates_from_absence_byte_for_byte(self):
        expected = (ROOT / "refs/schema_registry_v1_6_draft_5_3_14.json").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            copy_root = pathlib.Path(directory) / "corpus"
            (copy_root / "executable/validators").mkdir(parents=True)
            (copy_root / "executable/tests").mkdir(parents=True)
            (copy_root / "refs").mkdir(parents=True)
            shutil.copytree(ROOT / "schemas", copy_root / "schemas")
            shutil.copytree(ROOT / "executable/tests/fixtures", copy_root / "executable/tests/fixtures")
            shutil.copy2(
                ROOT / "executable/validators/build_schema_registry_v5314.py",
                copy_root / "executable/validators/build_schema_registry_v5314.py",
            )
            output = copy_root / "refs/schema_registry_v1_6_draft_5_3_14.json"
            self.assertFalse(output.exists())
            completed = subprocess.run(
                [sys.executable, "executable/validators/build_schema_registry_v5314.py"],
                cwd=copy_root, text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertEqual(output.read_bytes(), expected)

    def test_historical_generator_remains_available_while_root_readme_tracks_current_revision(self):
        self.assertTrue((ROOT / "executable/validators/build_schema_registry_v5314.py").is_file())
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("build_schema_registry_v5316.py", readme)
        self.assertNotIn("build_schema_registry_v5312.py", readme)


if __name__ == "__main__":
    unittest.main()
