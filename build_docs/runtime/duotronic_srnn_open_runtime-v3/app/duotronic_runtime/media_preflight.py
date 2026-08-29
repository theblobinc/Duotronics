from __future__ import annotations

"""Bounded, dependency-free structural checks for media containers.

The preflight is deliberately conservative: it only declares formats invalid when
container structure is provably broken. Other formats are left as not_applicable
and continue to the commissioned transcription service.
"""

from pathlib import Path
from typing import Any

MEDIA_PREFLIGHT_VERSION = "xavi-media-preflight/v1"
_ISOBMFF_EXTENSIONS = {".mp4", ".m4v", ".mov", ".m4a", ".3gp", ".3g2"}
_MAX_TOP_LEVEL_BOXES = 10000


def _result(status: str, *, reason: str | None = None, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"schema_version": MEDIA_PREFLIGHT_VERSION, "status": status}
    if reason:
        row["reason"] = reason
    row.update(extra)
    return row


def _isobmff(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size < 8:
        return _result("invalid", reason="isobmff_too_small", bytes=size)
    offset = 0
    count = 0
    types: list[str] = []
    has_moov = False
    has_mdat = False
    has_ftyp = False
    with path.open("rb") as fh:
        while offset < size:
            remaining = size - offset
            if remaining < 8:
                return _result("invalid", reason="isobmff_trailing_bytes", bytes=size, offset=offset, trailing_bytes=remaining, boxes=types[:64])
            fh.seek(offset)
            header = fh.read(8)
            if len(header) != 8:
                return _result("invalid", reason="isobmff_header_truncated", bytes=size, offset=offset, boxes=types[:64])
            size32 = int.from_bytes(header[:4], "big")
            raw_type = header[4:8]
            try:
                box_type = raw_type.decode("ascii")
            except UnicodeDecodeError:
                box_type = raw_type.hex()
            header_size = 8
            if size32 == 1:
                ext = fh.read(8)
                if len(ext) != 8:
                    return _result("invalid", reason="isobmff_extended_size_truncated", bytes=size, offset=offset, box_type=box_type, boxes=types[:64])
                box_size = int.from_bytes(ext, "big")
                header_size = 16
            elif size32 == 0:
                box_size = remaining
            else:
                box_size = size32
            if box_size < header_size:
                return _result("invalid", reason="isobmff_box_size_invalid", bytes=size, offset=offset, box_type=box_type, box_size=box_size, boxes=types[:64])
            if box_size > remaining:
                return _result("invalid", reason="isobmff_box_truncated", bytes=size, offset=offset, box_type=box_type, box_size=box_size, remaining=remaining, boxes=types[:64])
            count += 1
            if count > _MAX_TOP_LEVEL_BOXES:
                return _result("invalid", reason="isobmff_box_count_limit", bytes=size, box_count=count, boxes=types[:64])
            if len(types) < 64:
                types.append(box_type)
            has_moov = has_moov or box_type == "moov"
            has_mdat = has_mdat or box_type == "mdat"
            has_ftyp = has_ftyp or box_type == "ftyp"
            offset += box_size
    if not has_moov:
        return _result("invalid", reason="isobmff_missing_moov", bytes=size, box_count=count, has_ftyp=has_ftyp, has_mdat=has_mdat, boxes=types)
    if not has_mdat:
        return _result("invalid", reason="isobmff_missing_mdat", bytes=size, box_count=count, has_ftyp=has_ftyp, has_moov=has_moov, boxes=types)
    return _result("ok", container="iso-bmff", bytes=size, box_count=count, has_ftyp=has_ftyp, has_moov=True, has_mdat=True, boxes=types)


def preflight_media(path: str | Path, *, mime_type: str | None = None) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in _ISOBMFF_EXTENSIONS:
        return _result("not_applicable", suffix=suffix, mime_type=str(mime_type or ""))
    try:
        return _isobmff(source)
    except OSError as exc:
        return _result("failed", reason="media_preflight_io_failed", error=exc.__class__.__name__, suffix=suffix)
