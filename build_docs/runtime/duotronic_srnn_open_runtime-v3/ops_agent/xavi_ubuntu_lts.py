#!/usr/bin/env python3
"""Resolve and cache the latest released Ubuntu Server LTS cloud image.

The resolver uses Canonical's official simplestreams released-cloud metadata.
It intentionally follows the LTS cadence (even-year YY.04) rather than a
hard-coded Ubuntu version so future Xavi Ubuntu VMs naturally advance to the
next released LTS.

Canonical currently publishes a SHA-256 field in simplestreams. Xavi preserves
that value only as untrusted interoperability metadata; it is not used as a
Xavi identity or qualification primitive. Cached images are identified and
re-qualified with the project's SHAKE256-512 profile.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.request
from pathlib import Path

STREAM_URL = "https://cloud-images.ubuntu.com/releases/streams/v1/com.ubuntu.cloud:released:download.json"
IMAGE_BASE = "https://cloud-images.ubuntu.com/"
USER_AGENT = "Xavi-Ubuntu-LTS-Resolver/2.0"


def _version_tuple(value: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{2})\.(\d{2})", value or "")
    if not m:
        raise ValueError(value)
    return int(m.group(1)), int(m.group(2))


def fetch_stream() -> dict:
    req = urllib.request.Request(STREAM_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def resolve_latest_lts(arch: str = "amd64") -> dict:
    data = fetch_stream()
    candidates: list[tuple[tuple[int, int], str, dict]] = []
    for product_id, product in (data.get("products") or {}).items():
        if str(product.get("os") or "") != "ubuntu":
            continue
        if str(product.get("arch") or "") != arch:
            continue
        if ":server:" not in product_id:
            continue
        version = str(product.get("version") or "")
        try:
            year, month = _version_tuple(version)
        except ValueError:
            continue
        # Ubuntu LTS releases are even-year April releases. Using released
        # simplestreams metadata ensures development/interim releases do not
        # become eligible just because a version number exists elsewhere.
        if month != 4 or year % 2:
            continue
        versions = product.get("versions") or {}
        if not versions:
            continue
        build = sorted(versions)[-1]
        items = (versions.get(build) or {}).get("items") or {}
        disk_key = "disk1.img" if "disk1.img" in items else None
        if not disk_key:
            disk_key = next((k for k, v in items.items() if str(v.get("ftype") or "") == "disk1.img"), None)
        if not disk_key:
            continue
        item = items[disk_key]
        path = str(item.get("path") or "")
        upstream_sha256 = str(item.get("sha256") or "").lower()
        if not path:
            continue
        if upstream_sha256 and not re.fullmatch(r"[0-9a-f]{64}", upstream_sha256):
            upstream_sha256 = ""
        candidates.append(((year, month), product_id, {
            "schema": "xavi-ubuntu-lts-image/v2",
            "stream_url": STREAM_URL,
            "stream_updated": data.get("updated"),
            "product_id": product_id,
            "arch": arch,
            "version": version,
            "codename": product.get("release"),
            "release_codename": product.get("release_codename"),
            "support_eol": product.get("support_eol"),
            "build": build,
            "ftype": item.get("ftype"),
            "path": path,
            "url": IMAGE_BASE + path.lstrip("/"),
            "size": int(item.get("size") or 0),
            "upstream_sha256_untrusted": upstream_sha256 or None,
            "upstream_checksum_trust": "untrusted_interoperability",
            "xavi_identity_profile": "SHAKE256-512",
        }))
    if not candidates:
        raise RuntimeError(f"no released Ubuntu Server LTS image found for {arch}")
    candidates.sort(key=lambda row: row[0], reverse=True)
    return candidates[0][2]


def shake256_512_file(path: Path) -> str:
    digest = hashlib.shake_256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest(64)


def _cache_manifest_path(target: Path) -> Path:
    return target.with_name(target.name + ".xavi.json")


def cache_image(info: dict, cache_root: Path) -> dict:
    target_dir = cache_root / str(info["version"]) / str(info["build"])
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(str(info["path"])).name
    target = target_dir / filename
    manifest = _cache_manifest_path(target)

    if target.is_file() and manifest.is_file():
        try:
            cached = json.loads(manifest.read_text(encoding="utf-8"))
            expected_shake = str(cached.get("shake256_512") or "").lower()
            expected_size = int(cached.get("size") or 0)
            if re.fullmatch(r"[0-9a-f]{128}", expected_shake):
                if expected_size and target.stat().st_size != expected_size:
                    raise ValueError("cached image size mismatch")
                actual_shake = shake256_512_file(target)
                if actual_shake == expected_shake:
                    return {
                        **info,
                        "local_path": str(target),
                        "cache_hit": True,
                        "shake256_512": actual_shake,
                        "cache_manifest": str(manifest),
                    }
        except Exception:
            pass

    if target.exists():
        target.unlink()
    if manifest.exists():
        manifest.unlink()

    fd, tmp_name = tempfile.mkstemp(prefix=filename + ".", suffix=".part", dir=str(target_dir))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        req = urllib.request.Request(str(info["url"]), headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as response, tmp.open("wb") as out:
            shutil.copyfileobj(response, out, length=8 * 1024 * 1024)
        expected_size = int(info.get("size") or 0)
        actual_size = tmp.stat().st_size
        if expected_size and actual_size != expected_size:
            raise RuntimeError(f"Ubuntu image size mismatch: expected {expected_size}, got {actual_size}")
        shake = shake256_512_file(tmp)
        os.replace(tmp, target)
        cache_record = {
            "schema": "xavi-ubuntu-lts-cache/v2",
            "version": info.get("version"),
            "build": info.get("build"),
            "arch": info.get("arch"),
            "source_url": info.get("url"),
            "size": target.stat().st_size,
            "shake256_512": shake,
            "xavi_identity_profile": "SHAKE256-512",
            "upstream_sha256_untrusted": info.get("upstream_sha256_untrusted"),
            "upstream_checksum_trust": "untrusted_interoperability",
        }
        manifest.write_text(json.dumps(cache_record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    finally:
        if tmp.exists():
            tmp.unlink()
    return {
        **info,
        "local_path": str(target),
        "cache_hit": False,
        "shake256_512": shake,
        "cache_manifest": str(manifest),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default="amd64")
    ap.add_argument("--cache-root", default="/datastore2/xavi/vms/images/ubuntu")
    ap.add_argument("--cache", action="store_true", help="download and identify the selected image with SHAKE256-512")
    args = ap.parse_args()
    info = resolve_latest_lts(args.arch)
    if args.cache:
        info = cache_image(info, Path(args.cache_root))
    print(json.dumps(info, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
