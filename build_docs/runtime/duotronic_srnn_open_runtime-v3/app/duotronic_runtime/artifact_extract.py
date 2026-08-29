from __future__ import annotations

import html
import mimetypes
import re
import sqlite3
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

EXTRACTOR_VERSION = "xavi-artifact-text-extraction/v2"
DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_PDF_BYTES = 384 * 1024 * 1024
DEFAULT_MAX_EPUB_BYTES = 192 * 1024 * 1024
DEFAULT_MAX_SQLITE_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_CHARS = 8_000_000
DEFAULT_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_ARCHIVE_MEMBERS = 10_000
DEFAULT_MAX_PDF_PAGES = 4_000

_TEXT_EXTENSIONS = {
    ".txt", ".text", ".md", ".markdown", ".rst", ".adoc", ".csv", ".tsv",
    ".json", ".jsonl", ".ndjson", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".conf", ".log", ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".jsx", ".php", ".go", ".rs", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp",
    ".java", ".kt", ".kts", ".scala", ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".sql", ".css", ".scss", ".sass", ".less", ".tex", ".bib", ".properties",
    ".env", ".gitignore", ".dockerignore", ".srt", ".vtt", ".ass", ".ssa", ".sub",
    ".lrc", ".cue", ".m3u", ".m3u8",
}
_HTML_EXTENSIONS = {".html", ".htm", ".xhtml", ".xml", ".svg", ".opf"}
_EPUB_EXTENSIONS = {".epub"}
_PDF_EXTENSIONS = {".pdf"}
_MOBI_EXTENSIONS = {".mobi"}
_SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}
LOCAL_TEXT_EXTRACTOR_EXTENSIONS = frozenset(_TEXT_EXTENSIONS | _HTML_EXTENSIONS | _EPUB_EXTENSIONS | _PDF_EXTENSIONS | _MOBI_EXTENSIONS | _SQLITE_EXTENSIONS)


def _result(*, status: str, extractor: str | None = None, reason: str | None = None, **extra: Any) -> dict[str, Any]:
    if status == "ok" and isinstance(extra.get("text"), str):
        original = extra["text"]
        nul_chars_removed = original.count("\x00")
        without_nul = original.replace("\x00", "") if nul_chars_removed else original
        normalized = unicodedata.normalize("NFC", without_nul)
        extra["text"] = normalized
        if "chars" in extra:
            extra["chars"] = len(normalized)
        if nul_chars_removed:
            extra["nul_chars_removed"] = nul_chars_removed
        if normalized != without_nul:
            extra["unicode_normalized"] = "NFC"
    row: dict[str, Any] = {"schema_version": EXTRACTOR_VERSION, "status": status}
    if extractor:
        row["extractor"] = extractor
    if reason:
        row["reason"] = reason
    row.update(extra)
    return row


def _clip(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def _clean_markup_text(raw: bytes) -> str:
    soup = BeautifulSoup(raw, "lxml")
    for node in soup(["script", "style", "noscript", "template"]):
        node.decompose()
    text = html.unescape(soup.get_text("\n"))
    lines = [re.sub(r"[\t\f\v ]+", " ", line).strip() for line in text.splitlines()]
    out: list[str] = []
    blank = False
    for line in lines:
        if line:
            out.append(line)
            blank = False
        elif not blank and out:
            out.append("")
            blank = True
    return "\n".join(out).strip()


def _plain_text(path: Path, *, max_bytes: int, max_chars: int) -> dict[str, Any]:
    size = path.stat().st_size
    if size > max_bytes:
        return _result(status="deferred", extractor="plain-text", reason="artifact_exceeds_text_extraction_limit", bytes=size, max_bytes=max_bytes)
    raw = path.read_bytes()
    if raw and raw.count(b"\x00") / max(1, len(raw)) > 0.01:
        return _result(status="unsupported", extractor="plain-text", reason="binary_content_detected")
    text = raw.decode("utf-8", errors="replace")
    text, truncated = _clip(text, max_chars)
    if not text.strip():
        return _result(status="empty", extractor="plain-text", chars=0, truncated=truncated)
    return _result(status="ok", extractor="plain-text", text=text, chars=len(text), truncated=truncated)


def _markup_text(path: Path, *, max_bytes: int, max_chars: int) -> dict[str, Any]:
    size = path.stat().st_size
    is_xml = path.suffix.lower() in {".xml", ".svg", ".opf"}
    extractor = "beautifulsoup-xml" if is_xml else "beautifulsoup-lxml"
    if size > max_bytes:
        return _result(status="deferred", extractor=extractor, reason="artifact_exceeds_markup_extraction_limit", bytes=size, max_bytes=max_bytes)
    raw = path.read_bytes()
    if is_xml:
        soup = BeautifulSoup(raw, "xml")
        for node in soup(["script", "style", "noscript", "template"]):
            node.decompose()
        text = html.unescape(soup.get_text("\n"))
        lines = [re.sub(r"[\t\f\v ]+", " ", line).strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line).strip()
    else:
        text = _clean_markup_text(raw)
    text, truncated = _clip(text, max_chars)
    if not text:
        return _result(status="empty", extractor=extractor, chars=0, truncated=truncated)
    return _result(status="ok", extractor=extractor, text=text, chars=len(text), truncated=truncated)


def _epub_order(zf: zipfile.ZipFile) -> list[str]:
    names = {name for name in zf.namelist() if not name.endswith("/")}
    ordered: list[str] = []
    opf_name: str | None = None
    try:
        root = ET.fromstring(zf.read("META-INF/container.xml"))
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] == "rootfile":
                opf_name = node.attrib.get("full-path")
                if opf_name:
                    break
    except Exception:
        opf_name = None
    if opf_name and opf_name in names:
        try:
            root = ET.fromstring(zf.read(opf_name))
            manifest: dict[str, str] = {}
            spine: list[str] = []
            for node in root.iter():
                local = node.tag.rsplit("}", 1)[-1]
                if local == "item" and node.attrib.get("id") and node.attrib.get("href"):
                    manifest[node.attrib["id"]] = node.attrib["href"]
                elif local == "itemref" and node.attrib.get("idref"):
                    spine.append(node.attrib["idref"])
            base = PurePosixPath(opf_name).parent
            for item_id in spine:
                href = manifest.get(item_id)
                if not href:
                    continue
                member = str(base / PurePosixPath(href))
                if member in names and member.lower().endswith((".xhtml", ".html", ".htm", ".xml")):
                    ordered.append(member)
        except Exception:
            ordered = []
    for name in sorted(names):
        if name.lower().endswith((".xhtml", ".html", ".htm")) and name not in ordered:
            ordered.append(name)
    return ordered


def _epub_text(path: Path, *, max_bytes: int, max_chars: int) -> dict[str, Any]:
    size = path.stat().st_size
    if size > max_bytes:
        return _result(status="deferred", extractor="stdlib-epub+beautifulsoup-lxml", reason="artifact_exceeds_epub_extraction_limit", bytes=size, max_bytes=max_bytes)
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            if len(infos) > DEFAULT_MAX_ARCHIVE_MEMBERS:
                return _result(status="deferred", extractor="stdlib-epub+beautifulsoup-lxml", reason="epub_member_limit", members=len(infos))
            expanded = sum(max(0, int(info.file_size)) for info in infos)
            if expanded > DEFAULT_MAX_ARCHIVE_BYTES:
                return _result(status="deferred", extractor="stdlib-epub+beautifulsoup-lxml", reason="epub_expanded_size_limit", expanded_bytes=expanded)
            parts: list[str] = []
            used: list[str] = []
            accumulated_chars = 0
            for name in _epub_order(zf):
                info = zf.getinfo(name)
                if info.file_size > 16 * 1024 * 1024:
                    continue
                part = _clean_markup_text(zf.read(name))
                if not part:
                    continue
                parts.append(part)
                used.append(name)
                accumulated_chars += len(part)
                if accumulated_chars >= max_chars:
                    break
            text = "\n\n".join(parts)
    except (zipfile.BadZipFile, KeyError, OSError, ET.ParseError) as exc:
        return _result(status="failed", extractor="stdlib-epub+beautifulsoup-lxml", reason="epub_parse_failed", error=exc.__class__.__name__)
    text, truncated = _clip(text, max_chars)
    if not text:
        return _result(status="empty", extractor="stdlib-epub+beautifulsoup-lxml", members_used=0, chars=0, truncated=truncated)
    return _result(status="ok", extractor="stdlib-epub+beautifulsoup-lxml", text=text, members_used=len(used), chars=len(text), truncated=truncated)


def _mobi_trailing_entry_size(data: bytes) -> int:
    value = 0
    for i in range(1, min(4, len(data)) + 1):
        byte = data[-i]
        value |= (byte & 0x7F) << (7 * (i - 1))
        if byte & 0x80:
            return value
    raise ValueError("mobi_trailing_size_unterminated")


def _mobi_trim_record_trailers(data: bytes, flags: int) -> bytes:
    # MOBI trailing entries are physically stored in bit order, so when
    # consuming from the record end the highest set normal-entry bit is first.
    for bit in range(15, 0, -1):
        if flags & (1 << bit):
            size = _mobi_trailing_entry_size(data)
            if size <= 0 or size > len(data):
                raise ValueError("mobi_trailing_size_invalid")
            data = data[:-size]
    # Bit 0 is the multibyte-character overlap entry immediately after text.
    if flags & 1:
        if not data:
            raise ValueError("mobi_multibyte_overlap_missing")
        size = (data[-1] & 0x03) + 1
        if size > len(data):
            raise ValueError("mobi_multibyte_overlap_invalid")
        data = data[:-size]
    return data


def _palmdoc_decompress(data: bytes, *, max_output: int) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        c = data[i]
        i += 1
        if c == 0:
            out.append(0)
        elif 1 <= c <= 8:
            if i + c > len(data):
                raise ValueError("palmdoc_literal_truncated")
            out.extend(data[i:i + c])
            i += c
        elif c <= 0x7F:
            out.append(c)
        elif c <= 0xBF:
            if i >= len(data):
                raise ValueError("palmdoc_truncated_backreference")
            pair = ((c & 0x3F) << 8) | data[i]
            i += 1
            distance = pair >> 3
            length = (pair & 0x07) + 3
            if distance <= 0 or distance > len(out):
                raise ValueError("palmdoc_invalid_backreference")
            for _ in range(length):
                out.append(out[-distance])
                if len(out) > max_output:
                    raise ValueError("palmdoc_decompressed_limit")
        else:
            out.extend((0x20, c ^ 0x80))
        if len(out) > max_output:
            raise ValueError("palmdoc_decompressed_limit")
    return bytes(out)


def _mobi_text(path: Path, *, max_bytes: int, max_chars: int) -> dict[str, Any]:
    size = path.stat().st_size
    if size > max_bytes:
        return _result(status="deferred", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="artifact_exceeds_mobi_extraction_limit", bytes=size, max_bytes=max_bytes)
    try:
        raw = path.read_bytes()
        if len(raw) < 78 or raw[60:68] != b"BOOKMOBI":
            return _result(status="unsupported", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="not_bookmobi")
        record_count = int.from_bytes(raw[76:78], "big")
        if record_count < 2 or record_count > DEFAULT_MAX_ARCHIVE_MEMBERS:
            return _result(status="failed", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="mobi_record_count_invalid", records=record_count)
        table_end = 78 + record_count * 8
        if table_end > len(raw):
            raise ValueError("mobi_record_table_truncated")
        offsets = [int.from_bytes(raw[78 + i * 8:82 + i * 8], "big") for i in range(record_count)]
        if any(offset < table_end or offset >= len(raw) for offset in offsets) or offsets != sorted(offsets) or len(set(offsets)) != len(offsets):
            raise ValueError("mobi_record_offsets_invalid")
        records = [raw[offsets[i]:(offsets[i + 1] if i + 1 < record_count else len(raw))] for i in range(record_count)]
        header = records[0]
        if len(header) < 48 or header[16:20] != b"MOBI":
            return _result(status="unsupported", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="mobi_header_missing")
        compression = int.from_bytes(header[0:2], "big")
        text_length = int.from_bytes(header[4:8], "big")
        text_records = int.from_bytes(header[8:10], "big")
        encryption = int.from_bytes(header[12:14], "big")
        encoding = int.from_bytes(header[28:32], "big")
        header_length = int.from_bytes(header[20:24], "big")
        format_version = int.from_bytes(header[104:108], "big") if len(header) >= 108 else None
        extra_data_flags = int.from_bytes(header[242:244], "big") if header_length >= 228 and len(header) >= 244 else 0
        if encryption != 0:
            return _result(status="unsupported", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="mobi_encrypted", encryption=encryption)
        if text_records <= 0 or text_records >= record_count:
            raise ValueError("mobi_text_record_count_invalid")
        if compression not in {1, 2}:
            return _result(status="unsupported", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="mobi_compression_unsupported", compression=compression)
        output_limit = min(DEFAULT_MAX_ARCHIVE_BYTES, max(max_chars * 6, 1_000_000))
        parts: list[bytes] = []
        total = 0
        for rec in records[1:1 + text_records]:
            payload_record = _mobi_trim_record_trailers(rec, extra_data_flags) if extra_data_flags else rec
            part = payload_record if compression == 1 else _palmdoc_decompress(payload_record, max_output=max(1, output_limit - total))
            parts.append(part)
            total += len(part)
            if total > output_limit:
                raise ValueError("mobi_decompressed_limit")
        payload = b"".join(parts)
        if text_length > 0:
            payload = payload[:text_length]
        codec = "utf-8" if encoding == 65001 else "cp1252" if encoding == 1252 else "utf-8"
        decoded = payload.decode(codec, errors="replace")
        text = _clean_markup_text(decoded.encode("utf-8", errors="replace"))
        text, truncated = _clip(text, max_chars)
        if not text:
            return _result(status="empty", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", compression=compression, encoding=encoding, format_version=format_version, extra_data_flags=extra_data_flags, records_used=text_records, chars=0, truncated=truncated)
        return _result(status="ok", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", text=text, compression=compression, encoding=encoding, format_version=format_version, extra_data_flags=extra_data_flags, records_used=text_records, chars=len(text), truncated=truncated)
    except Exception as exc:
        return _result(status="failed", extractor="stdlib-palmdoc-mobi+beautifulsoup-lxml", reason="mobi_parse_failed", error=exc.__class__.__name__)


def _pdf_text(path: Path, *, max_bytes: int, max_chars: int) -> dict[str, Any]:
    size = path.stat().st_size
    if size > max_bytes:
        return _result(status="deferred", extractor="pypdf", reason="artifact_exceeds_pdf_extraction_limit", bytes=size, max_bytes=max_bytes)
    try:
        from pypdf import PdfReader  # container dependency; deliberately optional for source-only tooling
    except Exception:
        return _result(status="unavailable", extractor="pypdf", reason="pypdf_not_installed")
    try:
        reader = PdfReader(str(path), strict=False)
        parts: list[str] = []
        pages_used = 0
        accumulated_chars = 0
        for index, page in enumerate(reader.pages):
            if index >= DEFAULT_MAX_PDF_PAGES:
                break
            try:
                part = page.extract_text() or ""
            except Exception:
                part = ""
            if part.strip():
                cleaned = part.strip()
                parts.append(cleaned)
                accumulated_chars += len(cleaned)
            pages_used += 1
            if accumulated_chars >= max_chars:
                break
        text = "\n\n".join(parts)
        page_count = len(reader.pages)
    except Exception as exc:
        return _result(status="failed", extractor="pypdf", reason="pdf_parse_failed", error=exc.__class__.__name__)
    text, truncated = _clip(text, max_chars)
    if not text:
        return _result(status="empty", extractor="pypdf", pages=page_count, pages_used=pages_used, chars=0, truncated=truncated)
    return _result(status="ok", extractor="pypdf", text=text, pages=page_count, pages_used=pages_used, chars=len(text), truncated=truncated)


def _sqlite_render_value(value: Any, *, max_chars: int = 4096) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bytes):
        return f"<blob:{len(value)} bytes>"
    text = str(value).replace("\x00", "\\0")
    if len(text) > max_chars:
        return text[:max_chars] + "…"
    return text


def _sqlite_text(path: Path, *, max_bytes: int, max_chars: int) -> dict[str, Any]:
    size = path.stat().st_size
    if size > max_bytes:
        return _result(status="deferred", extractor="stdlib-sqlite-readonly", reason="artifact_exceeds_sqlite_extraction_limit", bytes=size, max_bytes=max_bytes)
    try:
        with path.open("rb") as fh:
            if fh.read(16) != b"SQLite format 3\x00":
                return _result(status="unsupported", extractor="stdlib-sqlite-readonly", reason="not_sqlite3")
    except OSError as exc:
        return _result(status="failed", extractor="stdlib-sqlite-readonly", reason="sqlite_header_read_failed", error=exc.__class__.__name__)

    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    parts: list[str] = []
    tables_used = 0
    rows_used = 0
    truncated = False
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=2.0)
        try:
            conn.execute("PRAGMA query_only=ON")
            schema_rows = conn.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE type IN ('table','view') ORDER BY type, name LIMIT 256"
            ).fetchall()
            for obj_type, name, tbl_name, sql in schema_rows:
                schema_text = str(sql or f"{obj_type} {name}")
                parts.append(f"[{obj_type}] {name}\n{schema_text}")
                if obj_type != "table" or str(name).startswith("sqlite_"):
                    continue
                quoted = '"' + str(name).replace('"', '""') + '"'
                try:
                    cursor = conn.execute(f"SELECT * FROM {quoted} LIMIT 200")
                    columns = [str(item[0]) for item in (cursor.description or [])]
                    if columns:
                        parts.append(f"[columns] {name}: " + " | ".join(columns))
                    table_rows = 0
                    for row in cursor:
                        rendered = " | ".join(_sqlite_render_value(value) for value in row)
                        parts.append(rendered)
                        table_rows += 1
                        rows_used += 1
                        if sum(len(item) + 1 for item in parts) >= max_chars:
                            truncated = True
                            break
                    tables_used += 1
                except sqlite3.DatabaseError as exc:
                    parts.append(f"[table-read-error] {name}: {exc.__class__.__name__}")
                if truncated:
                    break
        finally:
            conn.close()
    except sqlite3.DatabaseError as exc:
        return _result(status="failed", extractor="stdlib-sqlite-readonly", reason="sqlite_parse_failed", error=exc.__class__.__name__)

    text = "\n\n".join(parts)
    text, clipped = _clip(text, max_chars)
    truncated = truncated or clipped
    if not text.strip():
        return _result(status="empty", extractor="stdlib-sqlite-readonly", tables_used=tables_used, rows_used=rows_used, chars=0, truncated=truncated)
    return _result(status="ok", extractor="stdlib-sqlite-readonly", text=text, tables_used=tables_used, rows_used=rows_used, chars=len(text), truncated=truncated)


def extract_artifact_text(
    path: str | Path,
    *,
    mime_type: str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_pdf_bytes: int = DEFAULT_MAX_PDF_BYTES,
    max_epub_bytes: int = DEFAULT_MAX_EPUB_BYTES,
    max_sqlite_bytes: int = DEFAULT_MAX_SQLITE_BYTES,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    mime = (mime_type or mimetypes.guess_type(source.name)[0] or "application/octet-stream").lower()
    max_bytes = max(1, int(max_bytes))
    max_pdf_bytes = max(1, int(max_pdf_bytes))
    max_epub_bytes = max(1, int(max_epub_bytes))
    max_sqlite_bytes = max(1, int(max_sqlite_bytes))
    max_chars = max(1_000, int(max_chars))
    try:
        if suffix in _PDF_EXTENSIONS or mime == "application/pdf":
            return _pdf_text(source, max_bytes=max_pdf_bytes, max_chars=max_chars)
        if suffix in _MOBI_EXTENSIONS or mime in {"application/x-mobipocket-ebook", "application/vnd.amazon.ebook"}:
            return _mobi_text(source, max_bytes=max_bytes, max_chars=max_chars)
        if suffix in _EPUB_EXTENSIONS or mime == "application/epub+zip":
            return _epub_text(source, max_bytes=max_epub_bytes, max_chars=max_chars)
        if suffix in _SQLITE_EXTENSIONS or mime in {"application/vnd.sqlite3", "application/x-sqlite3"}:
            return _sqlite_text(source, max_bytes=max_sqlite_bytes, max_chars=max_chars)
        if suffix in _HTML_EXTENSIONS or mime in {"text/html", "application/xhtml+xml", "application/xml", "text/xml", "image/svg+xml", "application/oebps-package+xml"}:
            return _markup_text(source, max_bytes=max_bytes, max_chars=max_chars)
        if suffix in _TEXT_EXTENSIONS or mime.startswith("text/") or mime in {"application/json", "application/x-ndjson", "application/javascript", "application/sql"}:
            return _plain_text(source, max_bytes=max_bytes, max_chars=max_chars)
        return _result(status="unsupported", reason="no_local_text_extractor", mime_type=mime, suffix=suffix)
    except Exception as exc:
        return _result(status="failed", reason="artifact_text_extraction_failed", error=exc.__class__.__name__, mime_type=mime, suffix=suffix)
