#!/usr/bin/env bash
set -euo pipefail

harness_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "${harness_root}/activation_harness.py" "$@"
