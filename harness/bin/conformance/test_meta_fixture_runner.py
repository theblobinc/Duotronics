"""Parametric meta-runtime fixture runner."""

from __future__ import annotations

from typing import Any

import pytest

from harness_lib import loader
from harness_lib.matchers import check_expectation_errors


def _check(observed: Any, expect: dict[str, Any]) -> None:
    errors = check_expectation_errors(observed, expect)
    assert not errors, "; ".join(errors)


def test_meta_fixture_case(meta_case: loader.Case, run_meta_operation: Any) -> None:
    expect = meta_case.expect
    raises = expect.get("raises")
    if raises:
        with pytest.raises(eval(raises)):  # noqa: S307
            run_meta_operation(meta_case.op, meta_case.given)
        return

    observed = run_meta_operation(meta_case.op, meta_case.given)
    _check(observed, expect)