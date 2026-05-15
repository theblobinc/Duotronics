#!/usr/bin/env bash
set -euo pipefail
podman build -t duotronic-srnn-open-runtime-test -f Containerfile .
podman run --rm duotronic-srnn-open-runtime-test python -m pytest -q /app/tests || true
python -m compileall app
PYTHONPATH=app python -m pytest -q tests
