#!/usr/bin/env bash
set -euo pipefail
podman compose --env-file .env down
