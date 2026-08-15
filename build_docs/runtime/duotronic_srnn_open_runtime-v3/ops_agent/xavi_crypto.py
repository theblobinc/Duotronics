from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_OUT = 64


def _raw(value: Any) -> bytes:
    if isinstance(value, bytes): return value
    if isinstance(value, bytearray): return bytes(value)
    if isinstance(value, str): return value.encode('utf-8')
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str).encode('utf-8')


def shake256_hex(value: Any) -> str:
    return hashlib.shake_256(_raw(value)).hexdigest(_OUT)


def shake256_ref(value: Any) -> str:
    return 'shake256-512:' + shake256_hex(value)


def shake256_file(path: str | Path, chunk_size: int = 4 * 1024 * 1024) -> str:
    h = hashlib.shake_256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return 'shake256-512:' + h.hexdigest(_OUT)


def kmac256_hex(key: bytes | str, payload: Any, *, custom: bytes | str = b'Xavi-Ops-KMAC256-v1', mac_len: int = 64) -> str:
    from Cryptodome.Hash import KMAC256
    k = key.encode('utf-8') if isinstance(key, str) else bytes(key)
    if len(k) < 32:
        k = hashlib.shake_256(k).digest(32)
    c = custom.encode('utf-8') if isinstance(custom, str) else bytes(custom)
    return KMAC256.new(key=k, data=_raw(payload), mac_len=mac_len, custom=c).hexdigest()
