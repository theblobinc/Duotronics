"""Golden-trace replay tests for the standalone meta runtime."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness_lib import trace_runner


META_GOLDEN_DIR = Path(__file__).resolve().parent.parent / "meta_golden_traces"
TRACES = trace_runner.discover_traces(META_GOLDEN_DIR)


@pytest.mark.normative
@pytest.mark.golden
@pytest.mark.meta_runtime
@pytest.mark.parametrize("trace", TRACES, ids=[t.trace_id for t in TRACES])
def test_meta_golden_trace(trace: trace_runner.Trace, run_meta_operation) -> None:
    trace_runner.run_trace(trace, runner=run_meta_operation)