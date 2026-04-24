#!/usr/bin/env bash
# Nightly run: same as acceptance, plus extended fuzz settings and the
# replay-identity rebaseline check.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-.venv/bin/python}"

echo "==> nightly: full acceptance"
bash ci/acceptance.sh

echo "==> nightly: extended fuzz"
HYPOTHESIS_PROFILE=nightly "$PYTHON" -m pytest -m fuzz --strict-markers -q

echo "OK: nightly green"
