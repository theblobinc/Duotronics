from __future__ import annotations

import hashlib
import json
from typing import Any

SHAKE256_512_BYTES = 64


def stable_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def shake256_hex(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = stable_json(value).encode("utf-8")
    return hashlib.shake_256(raw).hexdigest(SHAKE256_512_BYTES)


def shake256_ref(value: Any) -> str:
    return "shake256-512:" + shake256_hex(value)
