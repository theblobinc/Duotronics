#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/ops_agent/v3_maintenance/xavi_ops_root.py}"
DST=/usr/local/sbin/xavi-ops-root
SUDOERS=/etc/sudoers.d/xavi-ops-root
OWNER_USER="${XAVI_OPS_USER:-tbi}"

if [ "$(id -u)" -ne 0 ]; then
  echo "install_xavi_ops_root.sh must be run as root" >&2
  exit 1
fi

if [ ! -f "$SRC" ]; then
  echo "missing helper source: $SRC" >&2
  exit 1
fi

python3 -m py_compile "$SRC"

BACKUP_DIR="/var/backups/xavi-ops-root/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"
[ -f "$DST" ] && cp -a "$DST" "$BACKUP_DIR/xavi-ops-root.before" || true
[ -f "$SUDOERS" ] && cp -a "$SUDOERS" "$BACKUP_DIR/xavi-ops-root.sudoers.before" || true

install -o root -g root -m 0755 "$SRC" "$DST"
cat > "$SUDOERS.tmp" <<EOF
# Managed by Xavi privileged helper installer.
# The executable is root-owned and validates every subcommand/argument itself.
Defaults!$DST !requiretty
$OWNER_USER ALL=(root) NOPASSWD: $DST *
EOF
chown root:root "$SUDOERS.tmp"
chmod 0440 "$SUDOERS.tmp"
visudo -cf "$SUDOERS.tmp"
mv -f "$SUDOERS.tmp" "$SUDOERS"
visudo -cf "$SUDOERS"

mkdir -p /var/lib/xavi-ops-root
chown root:root /var/lib/xavi-ops-root
chmod 0755 /var/lib/xavi-ops-root
python3 - "$DST" > /var/lib/xavi-ops-root/helper.shake256_512 <<'PYHASH'
import hashlib, pathlib, sys
p=pathlib.Path(sys.argv[1]); h=hashlib.shake_256()
with p.open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
print('shake256-512:'+h.hexdigest(64), p)
PYHASH
chmod 0644 /var/lib/xavi-ops-root/helper.shake256_512
# Remove superseded digest sidecars after the SHAKE256-512 sidecar is durable.
# Keep this algorithm-agnostic so future legacy sidecars are not preserved by name.
find /var/lib/xavi-ops-root -maxdepth 1 -type f -name 'helper.*' ! -name 'helper.shake256_512' -delete
find /var/lib/xavi-ops-root -maxdepth 3 -type f -name 'head.*' ! -name 'head.shake256_512' -delete

printf 'installed=%s\n' "$DST"
printf 'sudoers=%s\n' "$SUDOERS"
printf 'backup=%s\n' "$BACKUP_DIR"
printf 'probe=' 
sudo -u "$OWNER_USER" sudo -n "$DST" probe
