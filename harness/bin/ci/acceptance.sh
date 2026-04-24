#!/usr/bin/env bash
# Acceptance gate: must exit 0 for the conformance suite to be considered green.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

echo "==> reference self-tests"
"$PYTHON" tools/run_self_test.py

echo "==> fixture YAML/JSON twin drift check"
"$PYTHON" tools/extract_fixtures.py --check

echo "==> normative pytest --strict-markers"
"$PYTHON" -m pytest -m normative --strict-markers -q

echo "==> meta-runtime conformance slice"
"$PYTHON" -m pytest conformance/test_meta_fixture_runner.py conformance/test_meta_golden_traces.py -m "normative and meta_runtime" --strict-markers -q

echo "==> full pytest (all markers)"
"$PYTHON" -m pytest --strict-markers -q

echo "OK: acceptance gate green"
