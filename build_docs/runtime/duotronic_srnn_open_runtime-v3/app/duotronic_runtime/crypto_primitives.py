from __future__ import annotations

import base64
import hashlib
import json
import struct
import unicodedata
from pathlib import Path
from typing import Any, Iterable

SHAKE256_512_BYTES = 64
SHAKE256_512_HEX_LEN = SHAKE256_512_BYTES * 2
SHAKE256_512_PREFIX = "shake256-512:"
DUOID_PREFIX = "duoid:shake256-512:"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    return canonical_json(value).encode("utf-8")


def shake256_hex(value: Any, *, out_bytes: int = SHAKE256_512_BYTES) -> str:
    return hashlib.shake_256(_bytes(value)).hexdigest(out_bytes)


def shake256_ref(value: Any, *, out_bytes: int = SHAKE256_512_BYTES) -> str:
    return f"shake256-{out_bytes * 8}:" + shake256_hex(value, out_bytes=out_bytes)


def shake256_duoid(value: Any) -> str:
    raw = hashlib.shake_256(_bytes(value)).digest(SHAKE256_512_BYTES)
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return DUOID_PREFIX + encoded


def _contract_reject_float(value: Any, path: str = "$") -> None:
    """Validate the restricted canonical JSON domain used by Witness Contract 5.3.18."""
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
            _contract_reject_float(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _contract_reject_float(child, f"{path}[{index}]")


def contract_canonical_bytes(value: Any) -> bytes:
    _contract_reject_float(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def framed_shake256_digest(label: str, fields: Iterable[bytes], *, output_bytes: int = SHAKE256_512_BYTES) -> bytes:
    """5.3.18 domain-framed SHAKE256 identity primitive."""
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


def framed_shake256_duoid(label: str, *fields: bytes) -> str:
    raw = framed_shake256_digest(label, fields)
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return DUOID_PREFIX + encoded


def semantic_content_id(content_type: str, body: dict[str, Any]) -> str:
    return framed_shake256_duoid(
        "DUOTRONIC/SEMANTIC-CONTENT/v1",
        content_type.encode("utf-8"),
        contract_canonical_bytes(body),
    )


def meta_edge_content_id(edge_without_id: dict[str, Any]) -> str:
    forbidden = {"edge_content_id", "created_at", "observer_principal_id", "corpus_id"}
    semantic = {key: value for key, value in edge_without_id.items() if key not in forbidden}
    return framed_shake256_duoid("DUOTRONIC/META-EDGE/v1", contract_canonical_bytes(semantic))


def shake256_file(path: str | Path, *, out_bytes: int = SHAKE256_512_BYTES, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.shake_256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return f"shake256-{out_bytes * 8}:" + h.hexdigest(out_bytes)


def stable_shake_id(prefix: str, payload: Any, *, length: int = 20) -> str:
    return f"{prefix}_{shake256_hex(payload)[: max(1, int(length))]}"


def kmac256_hex(key: bytes | str, payload: Any, *, custom: bytes | str = b"Xavi-Duotronics-KMAC256-v1", mac_len: int = 64) -> str:
    try:
        from Cryptodome.Hash import KMAC256
    except Exception as exc:  # fail closed; keyed auth must not silently downgrade
        raise RuntimeError("KMAC256 provider unavailable") from exc
    key_bytes = key.encode("utf-8") if isinstance(key, str) else bytes(key)
    custom_bytes = custom.encode("utf-8") if isinstance(custom, str) else bytes(custom)
    if len(key_bytes) < 32:
        # KMAC256 requires a 256-bit key. Deterministically derive one from an
        # operator secret without introducing another hash family.
        key_bytes = hashlib.shake_256(key_bytes).digest(32)
    return KMAC256.new(key=key_bytes, data=_bytes(payload), mac_len=mac_len, custom=custom_bytes).hexdigest()
