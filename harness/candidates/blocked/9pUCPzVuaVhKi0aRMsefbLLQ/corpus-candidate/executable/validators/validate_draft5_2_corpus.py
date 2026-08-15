#!/usr/bin/env python3
from __future__ import annotations
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
new_validator = ROOT / 'executable' / 'validators' / 'validate_draft5_2_1_corpus.py'
if new_validator.exists():
    runpy.run_path(str(new_validator), run_name='__main__')
else:
    raise SystemExit('Draft 5.2.1 validator missing')
