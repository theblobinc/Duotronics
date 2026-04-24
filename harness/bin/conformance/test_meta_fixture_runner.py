"""Parametric meta-runtime fixture runner."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from harness_lib import loader
from harness_lib.matchers import check_expectation_errors


META_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "meta_fixtures"


def _all_meta_fixture_cases() -> list:
    items = []
    for pack in loader.discover_packs(META_FIXTURES_DIR):
        for case in pack.cases:
            marks = [pytest.mark.meta_runtime, *(getattr(pytest.mark, m) for m in case.all_markers)]
            items.append(pytest.param(case, marks=marks, id=f"{pack.pack_id}/{case.case_id}"))
    return items


ALL_META_FIXTURE_CASES = _all_meta_fixture_cases()


def _check(observed: Any, expect: dict[str, Any]) -> None:
    errors = check_expectation_errors(observed, expect)
    assert not errors, "; ".join(errors)


@pytest.mark.parametrize("case", ALL_META_FIXTURE_CASES)
def test_meta_fixture_case(case: loader.Case, run_meta_operation: Any) -> None:
    expect = case.expect
    raises = expect.get("raises")
    if raises:
        with pytest.raises(eval(raises)):  # noqa: S307
            run_meta_operation(case.op, case.given)
        return

    observed = run_meta_operation(case.op, case.given)
    _check(observed, expect)