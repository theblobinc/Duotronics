#!/usr/bin/env bash
set -euo pipefail
cd /var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3
podman compose --env-file .env up -d --force-recreate runtime
