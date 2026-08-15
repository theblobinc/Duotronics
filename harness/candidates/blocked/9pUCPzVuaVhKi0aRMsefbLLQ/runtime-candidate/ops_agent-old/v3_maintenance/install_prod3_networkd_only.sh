#!/usr/bin/env bash
set -euo pipefail
H=/usr/local/sbin/xavi-ops-root
SRC=/var/www/xavi/xavi-stack-manager/data/privileged_staging/99-xavi-networkd.yaml
sudo -n "$H" netplan-install "$SRC" 99-xavi-networkd.yaml
sudo -n "$H" netplan-generate
echo '== installed files =='
ls -l /etc/netplan
echo '== generated networkd filenames =='
ls -1 /run/systemd/network | sort
echo '== services before cutover =='
systemctl is-enabled NetworkManager 2>/dev/null || true
systemctl is-active NetworkManager 2>/dev/null || true
systemctl is-enabled systemd-networkd 2>/dev/null || true
systemctl is-active systemd-networkd 2>/dev/null || true
