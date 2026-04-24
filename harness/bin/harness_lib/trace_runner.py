"""Trace runner.

Reads a YAML golden trace and replays it through `run_operation`. Each
trace has the form:

    trace_id: t-001-policy-shield-recovery
    description: ...
    steps:
      - op: policy_decide
        given: { event: ok }
        expect: { equals: { mode: normal } }
      - op: ...

Steps execute in order; a failed expectation halts the trace with a
deterministic error message that includes the failing step index.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml

from .dispatch import get_run_operation
from .matchers import check_expectation_errors


GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden_traces"


@dataclass(frozen=True)
class TraceStep:
    op: str
    given: dict[str, Any]
    expect: dict[str, Any]


@dataclass
class Trace:
    trace_id: str
    description: str
    steps: list[TraceStep]
    source: Path | None = None


def load_trace(path: Path) -> Trace:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    steps = [
        TraceStep(op=s["op"], given=dict(s.get("given", {})), expect=dict(s.get("expect", {})))
        for s in data.get("steps", [])
    ]
    return Trace(
        trace_id=data.get("trace_id", path.stem),
        description=data.get("description", ""),
        steps=steps,
        source=path,
    )


def discover_traces(directory: Path | None = None) -> list[Trace]:
    directory = directory or GOLDEN_DIR
    return [load_trace(p) for p in sorted(directory.glob("*.yaml"))]


def _check_expectation(observed: Any, expect: dict[str, Any]) -> list[str]:
    """Return a list of error messages; empty means pass."""
    return check_expectation_errors(observed, expect)


def run_trace(
    trace: Trace,
    *,
    impl: str | None = None,
    runner: Callable[[str, Mapping[str, Any]], dict[str, Any]] | None = None,
) -> None:
    run_operation = runner or get_run_operation(impl)
    for index, step in enumerate(trace.steps):
        observed = run_operation(step.op, step.given)
        errors = _check_expectation(observed, step.expect)
        if errors:
            raise AssertionError(
                f"[{trace.trace_id} step #{index} op={step.op}] " + "; ".join(errors)
            )
