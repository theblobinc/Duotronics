#!/usr/bin/env bash
set -euo pipefail
if [ ! -f .env ]; then cp .env.example .env; fi
podman compose --env-file .env up --build postgres runtime
