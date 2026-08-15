#!/usr/bin/env bash
set -euo pipefail
H=/usr/local/sbin/xavi-ops-root
sudo -n "$H" systemctl disable NetworkManager.service || true
sudo -n "$H" systemctl stop NetworkManager.service || true
sudo -n "$H" systemctl disable NetworkManager-wait-online.service || true
sudo -n "$H" systemctl stop NetworkManager-wait-online.service || true
sudo -n "$H" systemctl enable systemd-networkd.service
sudo -n "$H" netplan-apply
sleep 3
printf '== services ==\n'
systemctl is-enabled NetworkManager 2>/dev/null || true
systemctl is-active NetworkManager 2>/dev/null || true
systemctl is-enabled NetworkManager-wait-online 2>/dev/null || true
systemctl is-active NetworkManager-wait-online 2>/dev/null || true
systemctl is-enabled systemd-networkd 2>/dev/null || true
systemctl is-active systemd-networkd 2>/dev/null || true
printf '\n== public ==\n'
networkctl --no-pager status enp5s0 | sed -n '1,80p'
printf '\n== private ==\n'
networkctl --no-pager status enp4s0f0 | sed -n '1,80p'
printf '\n== addresses/routes ==\n'
ip -br addr show dev enp5s0
ip -br addr show dev enp4s0f0
ip route
printf '\n== link tests ==\n'
ping -c 3 -W 2 209.53.57.57
ping -c 3 -W 2 10.77.0.1
