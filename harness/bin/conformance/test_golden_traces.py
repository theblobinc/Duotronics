"""Golden-trace replay tests."""

from __future__ import annotations

import pytest

from harness_lib import trace_runner


TRACES = trace_runner.discover_traces()


@pytest.mark.normative
@pytest.mark.golden
@pytest.mark.parametrize("trace", TRACES, ids=[t.trace_id for t in TRACES])
def test_golden_trace(trace: trace_runner.Trace, impl_name: str | None) -> None:
    trace_runner.run_trace(trace, impl=impl_name)
