#!/usr/bin/env python3
"""Portable identity helpers for the 5.3.17 contract.

This module implements only canonical bytes and authority digests. Production
signature, KEM, KDF, and AEAD operations must come from a validated provider.
"""

from __future__ import annotations

import base64
import hashlib
import json
import struct
import unicodedata
from typing import Any, Iterable


def _reject_float(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise ValueError(f"binary floating-point value is forbidden at {path}")
    if isinstance(value, str) and unicodedata.normalize("NFC", value) != value:
        raise ValueError(f"text is not NFC-normalized at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"object key is not text at {path}")
            if unicodedata.normalize("NFC", key) != key:
                raise ValueError(f"object key is not NFC-normalized at {path}")
            _reject_float(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_float(child, f"{path}[{index}]")


def canonical_bytes(value: Any) -> bytes:
    """Return canonical JSON bytes for the contract's restricted JSON domain."""
    _reject_float(value)
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def framed_digest(label: str, fields: Iterable[bytes], output_bytes: int = 64) -> bytes:
    if not label.isascii() or not label.endswith("/v1"):
        raise ValueError("domain label must be versioned ASCII")
    material = list(fields)
    sponge = hashlib.shake_256()
    encoded_label = label.encode("ascii")
    sponge.update(struct.pack(">Q", len(encoded_label)))
    sponge.update(encoded_label)
    sponge.update(struct.pack(">I", len(material)))
    for field in material:
        sponge.update(struct.pack(">Q", len(field)))
        sponge.update(field)
    return sponge.digest(output_bytes)


def duoid(label: str, *fields: bytes) -> str:
    encoded = base64.urlsafe_b64encode(framed_digest(label, fields)).rstrip(b"=").decode("ascii")
    return "duoid:shake256-512:" + encoded


def semantic_content_id(content_type: str, body: dict[str, Any]) -> str:
    return duoid(
        "DUOTRONIC/SEMANTIC-CONTENT/v1",
        content_type.encode("utf-8"),
        canonical_bytes(body),
    )


def edge_content_id(edge_without_id: dict[str, Any]) -> str:
    forbidden = {"edge_content_id", "created_at", "observer_principal_id", "corpus_id"}
    semantic = {key: value for key, value in edge_without_id.items() if key not in forbidden}
    return duoid("DUOTRONIC/META-EDGE/v1", canonical_bytes(semantic))


def corpus_file_id(relative_path: str, data: bytes) -> str:
    return duoid("DUOTRONIC/CORPUS-FILE/v1", relative_path.encode("utf-8"), data)
