"""WG-RNN prototype research-slice smoke tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


pytestmark = [pytest.mark.research, pytest.mark.replay, pytest.mark.policy]


def test_wgrnn_sample_loop_runs() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from prototypes.wgrnn.duotronic_wgrnn.runner import run_sample_loop
    except ImportError as exc:
        pytest.skip(f"WG-RNN prototype not installed: {exc}")

    records = run_sample_loop(return_records=True)
    assert len(records) == 4
    assert any(record.update_kind == "candidate_write" for record in records)
    assert any(record.update_kind == "quarantine_write" for record in records)
    assert any(record.update_kind == "no_op" for record in records)
    assert records[2].authority_t == 0.0
