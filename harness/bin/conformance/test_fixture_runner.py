"""Parametric fixture runner.

Runs every Case loaded by `harness_lib.loader.discover_packs()` against
the SUT's `run_operation`. Each case's `expect` block is enforced via
the same matchers as the trace runner (equals/contains/matches/raises +
must_emit_audit/must_not_emit_audit).
"""

from __future__ import annotations

from typing import Any

import pytest

from duotronic_ref import audit
from harness_lib import loader
from harness_lib.matchers import check_expectation_errors


def _all_fixture_cases() -> list:
    items = []
    for pack in loader.discover_packs():
        for case in pack.cases:
            marks = [getattr(pytest.mark, m) for m in case.all_markers]
            items.append(pytest.param(case, marks=marks, id=f"{pack.pack_id}/{case.case_id}"))
    return items


ALL_FIXTURE_CASES = _all_fixture_cases()


def _check(observed: Any, expect: dict[str, Any]) -> None:
    errors = check_expectation_errors(observed, expect)
    assert not errors, "; ".join(errors)


@pytest.mark.parametrize("case", ALL_FIXTURE_CASES)
def test_fixture_case(case: loader.Case, run_operation: Any) -> None:
    expect = case.expect
    raises = expect.get("raises")
    if raises:
        with pytest.raises(eval(raises)):  # noqa: S307
            run_operation(case.op, case.given)
        return

    observed = run_operation(case.op, case.given)

    _check(observed, expect)

    must_emit = expect.get("must_emit_audit") or []
    for kind in must_emit:
        events = audit.LEDGER.events(kind)
        assert events, f"expected audit event {kind!r} not emitted"

    must_not_emit = expect.get("must_not_emit_audit") or []
    for kind in must_not_emit:
        events = audit.LEDGER.events(kind)
        assert not events, f"forbidden audit event {kind!r} emitted: {events}"
