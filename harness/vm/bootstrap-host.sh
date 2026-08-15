#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this bootstrap as root." >&2
  exit 77
fi
if [[ $# -ne 1 ]]; then
  echo "usage: bootstrap-host.sh MCP_USER" >&2
  echo "The Ubuntu base image is resolved dynamically from Canonical's released LTS stream." >&2
  exit 64
fi

MCP_USER=$1
HARNESS_ROOT=/var/www/xavi/Duotronics/harness
RUNTIME_ROOT=/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3
LTS_RESOLVER=${RUNTIME_ROOT}/ops_agent/xavi_ubuntu_lts.py
STORAGE_ROOT=/datastore2/xavi/witness-harness-vm
BASE_DIR=${STORAGE_ROOT}/base
CACHE_ROOT=${BASE_DIR}/cache
DISK=${STORAGE_ROOT}/duotronic-witness-harness.qcow2
SEED=${STORAGE_ROOT}/duotronic-witness-harness-seed.img
USER_DATA=${STORAGE_ROOT}/user-data
DOMAIN=duotronic-witness-harness

if [[ ! ${MCP_USER} =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then
  echo "invalid MCP user" >&2
  exit 65
fi
test -f "${LTS_RESOLVER}"
MCP_GROUP=$(id -gn "${MCP_USER}")
KEY_DIR=${HARNESS_ROOT}/state/vm
KEY_FILE=${KEY_DIR}/id_rsa
install -d -m 0700 -o "${MCP_USER}" -g "${MCP_GROUP}" "${KEY_DIR}"
if [[ ! -f ${KEY_FILE} ]]; then
  runuser -u "${MCP_USER}" -- ssh-keygen -q -t rsa -b 4096 -N '' -f "${KEY_FILE}"
fi
PUBLIC_KEY_FILE=${KEY_FILE}.pub
test -f "${PUBLIC_KEY_FILE}"
chmod 0600 "${KEY_FILE}"
chmod 0644 "${PUBLIC_KEY_FILE}"
chown "${MCP_USER}:${MCP_GROUP}" "${KEY_FILE}" "${PUBLIC_KEY_FILE}"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  qemu-kvm qemu-utils libvirt-daemon-system libvirt-clients virtinst cloud-image-utils acl libosinfo-bin
systemctl enable --now libvirtd.service virtlogd.socket
usermod -aG kvm,libvirt "${MCP_USER}"

install -d -m 0750 -o root -g libvirt "${STORAGE_ROOT}" "${BASE_DIR}" "${CACHE_ROOT}"
# Grant only directory traversal to the VM account; do not make the datastore world-searchable.
setfacl -m u:libvirt-qemu:--x "$(dirname "${STORAGE_ROOT}")" "${STORAGE_ROOT}" "${BASE_DIR}" "${CACHE_ROOT}"

# Resolve the newest *released* even-year April Ubuntu Server image every time
# this provisioning path is used. No Ubuntu release number is pinned here.
IMAGE_INFO=$(/usr/bin/python3 "${LTS_RESOLVER}" --arch amd64 --cache --cache-root "${CACHE_ROOT}")
mapfile -t LTS_FIELDS < <(/usr/bin/python3 - "${IMAGE_INFO}" <<'PY'
import json, re, sys
p=json.loads(sys.argv[1])
version=str(p.get('version') or '')
local_path=str(p.get('local_path') or '')
shake=str(p.get('shake256_512') or '').lower()
manifest=str(p.get('cache_manifest') or '')
if not re.fullmatch(r'\d{2}\.04', version): raise SystemExit('resolver returned non-LTS version')
y=int(version.split('.')[0])
if y % 2: raise SystemExit('resolver returned non-LTS year')
if not local_path or not re.fullmatch(r'[0-9a-f]{128}', shake): raise SystemExit('resolver returned incomplete SHAKE identity')
print(version); print(local_path); print(shake); print(manifest)
PY
)
LTS_VERSION=${LTS_FIELDS[0]}
BASE_IMAGE_INPUT=${LTS_FIELDS[1]}
BASE_IMAGE_DIGEST=${LTS_FIELDS[2]}
CACHE_MANIFEST=${LTS_FIELDS[3]}
BASE_IMAGE=${BASE_DIR}/ubuntu-${LTS_VERSION}-server-cloudimg-amd64.img
BASE_MANIFEST=${BASE_IMAGE}.xavi.json

# Re-verify the resolver's cache object with the harness SHAKE256-512 verifier
# before installing it as the immutable backing image.
/usr/bin/python3 "${HARNESS_ROOT}/vm/image_verify.py" "${BASE_IMAGE_INPUT}" "${BASE_IMAGE_DIGEST}"
install -m 0640 -o root -g kvm "${BASE_IMAGE_INPUT}" "${BASE_IMAGE}"
if [[ -n ${CACHE_MANIFEST} && -f ${CACHE_MANIFEST} ]]; then
  install -m 0644 -o root -g root "${CACHE_MANIFEST}" "${BASE_MANIFEST}"
fi

if virsh -c qemu:///system dominfo "${DOMAIN}" >/dev/null 2>&1; then
  echo "${DOMAIN} is already defined; refusing to overwrite it." >&2
  exit 73
fi
if [[ -e ${DISK} || -e ${SEED} ]]; then
  echo "VM disk or seed already exists; refusing to overwrite it." >&2
  exit 73
fi

qemu-img create -f qcow2 -F qcow2 -b "${BASE_IMAGE}" "${DISK}" 64G
PUBLIC_KEY=$(<"${PUBLIC_KEY_FILE}")
python3 - "${HARNESS_ROOT}/vm/cloud-init/user-data.template" "${USER_DATA}" "${PUBLIC_KEY}" <<'PY'
from pathlib import Path
import sys
template, output, public_key = sys.argv[1:]
if "\n" in public_key or not public_key.startswith("ssh-rsa "):
    raise SystemExit("RSA public key required")
text = Path(template).read_text().replace("@@SSH_RSA_PUBLIC_KEY@@", public_key)
Path(output).write_text(text)
PY
cloud-localds "${SEED}" "${USER_DATA}" "${HARNESS_ROOT}/vm/cloud-init/meta-data"
chown libvirt-qemu:kvm "${DISK}" "${SEED}" 2>/dev/null || chown libvirt-qemu:libvirt "${DISK}" "${SEED}"
chmod 0660 "${DISK}" "${SEED}"

# osinfo-db can lag a just-released LTS. Use the exact dynamic Ubuntu variant
# when installed, otherwise fall back to generic rather than pinning an older OS.
OS_VARIANT=generic
OS_CANDIDATE=ubuntu${LTS_VERSION}
if command -v osinfo-query >/dev/null 2>&1 && osinfo-query os 2>/dev/null | grep -Fq "${OS_CANDIDATE}"; then
  OS_VARIANT=${OS_CANDIDATE}
fi

virsh -c qemu:///system net-start default >/dev/null 2>&1 || true
virsh -c qemu:///system net-autostart default >/dev/null 2>&1 || true
virt-install --connect qemu:///system \
  --name "${DOMAIN}" --memory 8192 --vcpus 6 --cpu host-passthrough \
  --os-variant "${OS_VARIANT}" --import --noautoconsole --noreboot \
  --disk "path=${DISK},format=qcow2,bus=virtio,cache=none,discard=unmap" \
  --disk "path=${SEED},device=cdrom" \
  --network network=default,model=virtio \
  --graphics none --console pty,target_type=serial

echo "Defined ${DOMAIN} on Ubuntu ${LTS_VERSION} LTS (${BASE_IMAGE_DIGEST}). Restart the Xavi MCP adapter/session so ${MCP_USER} receives its new libvirt and kvm groups, then run the MCP VM start command."
