#!/usr/bin/env python3
"""Run unittest discovery and emit counts from the TestResult object."""

from __future__ import annotations

import json
import sys
import unittest
from collections import Counter


def _test_ids(suite: unittest.TestSuite) -> list[str]:
    identifiers: list[str] = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            identifiers.extend(_test_ids(test))
        else:
            identifiers.append(test.id())
    return identifiers


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover("executable/tests", pattern="test*.py")
    identifiers = _test_ids(suite)
    discovered = suite.countTestCases()
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    duplicates = sorted(name for name, count in Counter(identifiers).items() if count > 1)
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    expected_failures = len(result.expectedFailures)
    unexpected_successes = len(result.unexpectedSuccesses)
    passed = result.testsRun - failures - errors - skipped - expected_failures - unexpected_successes
    record = {
        "tests_discovered": discovered,
        "tests_run": result.testsRun,
        "tests_passed": passed,
        "tests_failed": failures,
        "tests_errored": errors,
        "tests_skipped": skipped,
        "expected_failures": expected_failures,
        "unexpected_successes": unexpected_successes,
        "duplicate_test_ids": duplicates,
        "python_version": ".".join(map(str, sys.version_info[:3])),
    }
    print("WC_UNITTEST_RESULT=" + json.dumps(record, sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() and not duplicates and discovered == result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(main())
