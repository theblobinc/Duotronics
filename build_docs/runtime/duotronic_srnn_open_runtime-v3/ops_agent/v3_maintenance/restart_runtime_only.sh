#!/usr/bin/env bash
set -euo pipefail

V3_DIR="${V3_DIR:-/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3}"
REPO_ROOT="${REPO_ROOT:-/var/www/xavi/Duotronics}"
HOST_CORPUS_DIR="${HOST_CORPUS_DIR:-$REPO_ROOT/build_docs/witness_contract/v1.6 - Draft 5.3.18}"
HOST_CORPUS_HISTORY_DIR="${HOST_CORPUS_HISTORY_DIR:-$REPO_ROOT/build_docs/witness_contract}"
HOST_RUNTIME_DATA_DIR="${HOST_RUNTIME_DATA_DIR:-/datastore2/xavi/data/duotronic-runtime/runtime-data}"
HOST_DATALAKE_DIR="${HOST_DATALAKE_DIR:-/datastore2/xavi/data}"
HOST_TRAIN_DIR="${HOST_TRAIN_DIR:-/datastore2/xavi/train}"
RUNTIME_IMAGE="${RUNTIME_IMAGE:-localhost/duotronic-srnn-runtime-host:v3}"
PROJECT_ARACHNID_SECRET_FILE="${PROJECT_ARACHNID_SECRET_FILE:-/var/www/xavi/Duotronics/secrets/project-arachnid.json}"
ARACHNID_MOUNT_ARGS=()
if [ -f "$PROJECT_ARACHNID_SECRET_FILE" ]; then
  ARACHNID_MOUNT_ARGS=(
    -e PROJECT_ARACHNID_CREDENTIAL_FILE=/run/secrets/project-arachnid.json
    -v "$PROJECT_ARACHNID_SECRET_FILE:/run/secrets/project-arachnid.json:ro,Z"
  )
fi
XAVI_SANDBOX_AGENT_SECRET_FILE="${XAVI_SANDBOX_AGENT_SECRET_FILE:-/var/www/xavi/Duotronics/secrets/xavi-sandbox-1-agent.key}"
SANDBOX_AGENT_MOUNT_ARGS=()
if [ -f "$XAVI_SANDBOX_AGENT_SECRET_FILE" ]; then
  SANDBOX_AGENT_MOUNT_ARGS=(
    -e XAVI_SANDBOX_AGENT_URL=http://192.168.123.10:8765
    -e XAVI_SANDBOX_AGENT_KEY_FILE=/run/secrets/xavi-sandbox-1-agent.key
    -v "$XAVI_SANDBOX_AGENT_SECRET_FILE:/run/secrets/xavi-sandbox-1-agent.key:ro,Z"
  )
fi
BROWSER_WORKER_SECRET_FILE="${XAVI_BROWSER_WORKER_SECRET_FILE:-/datastore2/xavi/tools/browser-runtime/worker.key}"
BROWSER_WORKER_MOUNT_ARGS=()
if [ -f "$BROWSER_WORKER_SECRET_FILE" ]; then
  BROWSER_WORKER_MOUNT_ARGS=(
    -e XAVI_BROWSER_WORKER_URL=http://10.77.0.1:8767/run
    -e XAVI_BROWSER_WORKER_KEY_FILE=/run/secrets/xavi-browser-worker.key
    -v "$BROWSER_WORKER_SECRET_FILE:/run/secrets/xavi-browser-worker.key:ro,Z"
  )
fi
LOCK_FILE="${XAVI_RECOVERY_LOCK_FILE:-${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/xavi-podman-recovery.lock}"
if [ "${XAVI_RECOVERY_LOCK_HELD:-0}" != "1" ]; then
  mkdir -p "$(dirname "$LOCK_FILE")"
  exec flock -w 300 -o "$LOCK_FILE" env XAVI_RECOVERY_LOCK_HELD=1 "$0" "$@"
fi

cd "$V3_DIR"

podman rm -f duotronic-runtime 2>/dev/null || true

podman run \
  --name=duotronic-runtime \
  -d \
  --requires=duotronic-postgres,duotronic-redis \
  --label io.podman.compose.project=duotronic-srnn-runtime-host-v3 \
  --label com.docker.compose.project=duotronic-srnn-runtime-host-v3 \
  --label com.docker.compose.project.working_dir="$V3_DIR" \
  --label com.docker.compose.project.config_files=compose.yaml \
  --label com.docker.compose.service=runtime \
  --env-file "$V3_DIR/.env" \
  "${ARACHNID_MOUNT_ARGS[@]}" \
  "${SANDBOX_AGENT_MOUNT_ARGS[@]}" \
  "${BROWSER_WORKER_MOUNT_ARGS[@]}" \
  -e CORPUS_DIR=/runtime/corpus \
  -e CORPUS_HISTORY_DIR=/runtime/corpus-history \
  -e RUNTIME_DATA_DIR=/runtime/data \
  -e XAVI_DATALAKE_ROOT=/data-lake \
  -e XAVI_TRAIN_ROOT=/train \
  -e XAVI_TRAIN_INGEST_ENABLED=${XAVI_TRAIN_INGEST_ENABLED:-1} \
  -e XAVI_TRAIN_SCAN_SECONDS=${XAVI_TRAIN_SCAN_SECONDS:-120} \
  -e XAVI_TRAIN_BACKLOG_SCAN_SECONDS=${XAVI_TRAIN_BACKLOG_SCAN_SECONDS:-3} \
  -e XAVI_TRAIN_SETTLE_SECONDS=${XAVI_TRAIN_SETTLE_SECONDS:-30} \
  -e XAVI_TRAIN_MAX_FILES_PER_SCAN=${XAVI_TRAIN_MAX_FILES_PER_SCAN:-4} \
  -e XAVI_TRAIN_PARALLEL_WORKERS=${XAVI_TRAIN_PARALLEL_WORKERS:-3} \
  -e XAVI_TRAIN_MODALITY_SCHEDULE=${XAVI_TRAIN_MODALITY_SCHEDULE:-extraction,transcription,extraction,vision,witness} \
  -e MODEL_REGISTRY_PATH=/runtime/config/models.json \
  -e MODULE_REGISTRY_PATH=/runtime/config/modules.json \
  -e POLICY_PACK_PATH=/runtime/config/policy_pack.json \
  -e XAVI_REPO_ROOT=/workspace/Duotronics \
  -e XAVI_WORKTREE_ROOT=/runtime/data/worktrees \
  -v "$HOST_CORPUS_DIR:/runtime/corpus:Z" \
  -v "$HOST_CORPUS_HISTORY_DIR:/runtime/corpus-history:ro,Z" \
  -v "$V3_DIR/corpus/skills:/runtime/corpus/skills:ro,Z" \
  -v "$HOST_RUNTIME_DATA_DIR:/runtime/data:Z" \
  -v "$HOST_DATALAKE_DIR:/data-lake:ro,Z" \
  -v "$HOST_TRAIN_DIR:/train:ro,Z" \
  -v "$V3_DIR/config:/runtime/config:Z" \
  -v "$REPO_ROOT/build_docs/runtime/models/gguf:/models:Z" \
  -v "$V3_DIR/formal:/runtime/formal:Z" \
  -v "$V3_DIR/app/duotronic_runtime:/app/duotronic_runtime:ro,Z" \
  -v "$REPO_ROOT:/workspace/Duotronics:Z" \
  --net duotronic-srnn-runtime-host_runtime-net \
  --network-alias runtime \
  --add-host host.containers.internal:host-gateway \
  -p 127.0.0.1:8080:8080 \
  --restart unless-stopped \
  --healthcheck-command 'curl -fsS --max-time 3 http://127.0.0.1:8080/health' \
  --healthcheck-interval 15s \
  --healthcheck-timeout 5s \
  --healthcheck-start-period 20s \
  --healthcheck-retries 5 \
  "$RUNTIME_IMAGE" \
  python -m duotronic_runtime.main

# Private east-west research bus: SearXNG/Morphic research services remain unexposed to LAN/public interfaces.
if podman network exists xavi-research-bus 2>/dev/null; then
  podman network connect --alias wgrnn-runtime xavi-research-bus duotronic-runtime 2>/dev/null || true
fi

health_file=$(mktemp)
trap 'rm -f "$health_file"' EXIT
for attempt in $(seq 1 90); do
  if curl -fsS --max-time 10 http://127.0.0.1:8080/health -o "$health_file"; then
    cat "$health_file"
    exit 0
  fi
  sleep 2
done
podman logs --tail 200 duotronic-runtime || true
exit 1
