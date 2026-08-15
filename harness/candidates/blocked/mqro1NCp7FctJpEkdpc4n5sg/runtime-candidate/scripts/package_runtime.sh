#!/usr/bin/env sh
set -eu
OUT=${1:-../duotronic_srnn_runtime_host-v2.zip}
ROOT=$(basename "$(pwd)")
cd ..
zip -qr "$OUT" "$ROOT" -x "$ROOT/.venv/*" "$ROOT/__pycache__/*" "$ROOT/.pytest_cache/*" "$ROOT/data/*"
echo "$OUT"
