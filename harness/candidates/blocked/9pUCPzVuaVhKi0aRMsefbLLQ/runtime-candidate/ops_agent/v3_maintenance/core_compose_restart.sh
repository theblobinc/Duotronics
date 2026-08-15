#!/usr/bin/env bash
set -euo pipefail

ROOT=${V3_DIR:-/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3}
COMPOSE=${DUOTRONIC_CORE_COMPOSE:-$ROOT/compose.core.yaml}
LOCK_FILE=${XAVI_RECOVERY_LOCK_FILE:-${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/xavi-podman-recovery.lock}

if [ "${XAVI_RECOVERY_LOCK_HELD:-0}" != "1" ]; then
  mkdir -p "$(dirname "$LOCK_FILE")"
  exec flock -w 300 -o "$LOCK_FILE" env XAVI_RECOVERY_LOCK_HELD=1 "$0" "$@"
fi

cd "$ROOT"

mode=${1:-restart}
case "$mode" in
  up)
    podman compose -f "$COMPOSE" up -d
    ;;
  restart|rebuild)
    # podman-compose 1.0.6 does not reliably recreate an existing container after --build.
    # The core compose file keeps all persistent data outside container writable layers,
    # so an orderly compose down/up is the canonical code/config rollout path.
    podman compose -f "$COMPOSE" down
    podman ps -a --sync \
      --filter name=duotronic-runtime \
      --filter name=duotronic-postgres \
      --filter name=duotronic-redis \
      --filter name=duotronic-minio \
      --format 'table {{.Names}}\t{{.Status}}' || true
    podman compose -f "$COMPOSE" up -d --build
    ;;
  down)
    podman compose -f "$COMPOSE" down
    exit 0
    ;;
  *)
    echo "usage: $0 {up|restart|rebuild|down}" >&2
    exit 2
    ;;
esac

for i in $(seq 1 90); do
  pg=$(podman inspect duotronic-postgres --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' 2>/dev/null || true)
  rd=$(podman inspect duotronic-redis --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' 2>/dev/null || true)
  mi=$(podman inspect duotronic-minio --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' 2>/dev/null || true)
  rt=$(podman inspect duotronic-runtime --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' 2>/dev/null || true)
  printf '[%02d] postgres=%s redis=%s minio=%s runtime=%s\n' "$i" "$pg" "$rd" "$mi" "$rt"
  if [[ "$pg" == healthy && "$rd" == healthy && "$mi" == healthy && "$rt" == healthy ]]; then
    break
  fi
  sleep 1
done

curl -fsS --max-time 8 http://127.0.0.1:8080/health
printf '\n'

# Warm the expensive cryptographic corpus inspection while we are still inside
# the coordinated maintenance window. Interactive WG-RNN/LibreChat calls then
# hit the cached snapshot instead of paying a full corpus hash walk.
printf 'warming corpus inspection cache... '
start_ns=$(date +%s%N)
curl -fsS --max-time 90 http://127.0.0.1:8080/v1/corpus/inspect >/dev/null
end_ns=$(date +%s%N)
printf '%d ms\n' $(( (end_ns - start_ns) / 1000000 ))

# Warm dynamic model discovery as well; its cache is short-lived but this proves
# the configured provider mesh is reachable after a rebuild.
printf 'warming model registry... '
start_ns=$(date +%s%N)
curl -fsS --max-time 20 http://127.0.0.1:8080/v1/models >/dev/null
end_ns=$(date +%s%N)
printf '%d ms\n' $(( (end_ns - start_ns) / 1000000 ))
