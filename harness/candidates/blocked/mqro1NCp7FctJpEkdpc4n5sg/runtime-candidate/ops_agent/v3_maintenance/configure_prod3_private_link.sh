#!/usr/bin/env bash
set -euo pipefail
H=/usr/local/sbin/xavi-ops-root
sudo -n "$H" ip-link-up enp4s0f0
if ! ip -4 addr show dev enp4s0f0 | grep -q '10\.77\.0\.2/30'; then
  sudo -n "$H" ip-addr-add 10.77.0.2/30 enp4s0f0
fi
ip -br link show dev enp4s0f0
ip -br addr show dev enp4s0f0
ip route get 10.77.0.1
ip route show default
