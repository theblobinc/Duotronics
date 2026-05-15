#!/usr/bin/env bash
set -euo pipefail

V3_DIR="${V3_DIR:-/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3}"
REPO_ROOT="${REPO_ROOT:-/var/www/xavi/Duotronics}"
HOST_CORPUS_DIR="${HOST_CORPUS_DIR:-$REPO_ROOT/build_docs/witness_contract/v1.6 - Draft 5.2.2}"

cd "$V3_DIR"

podman rm -f duotronic-runtime 2>/dev/null || true

podman run \
  --name=duotronic-runtime \
  -d \
  --requires=duotronic-postgres,duotronic-minio,duotronic-redis \
  --label io.podman.compose.project=duotronic-srnn-runtime-host-v3 \
  --label com.docker.compose.project=duotronic-srnn-runtime-host-v3 \
  --label com.docker.compose.project.working_dir="$V3_DIR" \
  --label com.docker.compose.project.config_files=compose.yaml \
  --label com.docker.compose.service=runtime \
  --env-file "$V3_DIR/.env" \
  -e CORPUS_DIR=/runtime/corpus \
  -e RUNTIME_DATA_DIR=/runtime/data \
  -e MODEL_REGISTRY_PATH=/runtime/config/models.json \
  -e MODULE_REGISTRY_PATH=/runtime/config/modules.json \
  -e POLICY_PACK_PATH=/runtime/config/policy_pack.json \
  -e XAVI_REPO_ROOT=/workspace/Duotronics \
  -e XAVI_WORKTREE_ROOT=/runtime/data/worktrees \
  -v "$HOST_CORPUS_DIR:/runtime/corpus:Z" \
  -v "$V3_DIR/data:/runtime/data:Z" \
  -v "$V3_DIR/config:/runtime/config:Z" \
  -v "$REPO_ROOT/build_docs/runtime/models/gguf:/models:Z" \
  -v "$V3_DIR/formal:/runtime/formal:Z" \
  -v "$REPO_ROOT:/workspace/Duotronics:Z" \
  --net duotronic-srnn-runtime-host_runtime-net \
  --network-alias runtime \
  --add-host host.containers.internal:host-gateway \
  -p 127.0.0.1:8080:8080 \
  --restart unless-stopped \
  --healthcheck-command 'python -m duotronic_runtime.cli health --url http://127.0.0.1:8080' \
  --healthcheck-interval 15s \
  --healthcheck-timeout 5s \
  --healthcheck-start-period 20s \
  --healthcheck-retries 5 \
  localhost/duotronic-srnn-runtime-host:v3 \
  python -m duotronic_runtime.main

sleep 3
curl -fsS http://127.0.0.1:8080/health
