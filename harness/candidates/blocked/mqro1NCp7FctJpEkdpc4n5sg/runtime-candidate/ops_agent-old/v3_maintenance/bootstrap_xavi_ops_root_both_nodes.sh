#!/usr/bin/env bash
set -euo pipefail

BASE=/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/ops_agent/v3_maintenance
LOCAL_HELPER="$BASE/xavi_ops_root.py"
LOCAL_INSTALLER="$BASE/install_xavi_ops_root.sh"
REMOTE_DIR='$HOME/.local/share/xavi-ops-root-bootstrap'

printf '== bootstrap tbi-production-4 ==\n'
sudo /usr/bin/bash "$LOCAL_INSTALLER" "$LOCAL_HELPER"

printf '\n== bootstrap tbi-production-3 ==\n'
ssh -t resource 'sudo /usr/bin/bash "$HOME/.local/share/xavi-ops-root-bootstrap/install_xavi_ops_root.sh" "$HOME/.local/share/xavi-ops-root-bootstrap/xavi_ops_root.py"'

printf '\n== passwordless helper probes ==\n'
printf 'production-4: '
sudo -n /usr/local/sbin/xavi-ops-root probe
printf 'production-3: '
ssh -o BatchMode=yes -o ConnectTimeout=10 resource 'sudo -n /usr/local/sbin/xavi-ops-root probe'

printf '\nXavi privileged boundary is installed on both nodes.\n'
