from __future__ import annotations

import unicodedata
import zipfile
from pathlib import Path

from duotronic_runtime.artifact_extract import EXTRACTOR_VERSION, extract_artifact_text


def test_plain_text_and_source_are_extractable(tmp_path: Path):
    path = tmp_path / "sample.py"
    path.write_text("def answer():\n    return 42\n", encoding="utf-8")
    row = extract_artifact_text(path)
    assert row["schema_version"] == EXTRACTOR_VERSION
    assert row["status"] == "ok"
    assert row["extractor"] == "plain-text"
    assert "return 42" in row["text"]


def test_subtitles_are_preserved_as_searchable_text(tmp_path: Path):
    path = tmp_path / "captions.srt"
    path.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello from Xavi.\n", encoding="utf-8")
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert "Hello from Xavi" in row["text"]


def test_html_removes_script_content(tmp_path: Path):
    path = tmp_path / "page.html"
    path.write_text("<html><body><h1>Visible</h1><script>SECRET_NOISE</script><p>Body text</p></body></html>", encoding="utf-8")
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert "Visible" in row["text"] and "Body text" in row["text"]
    assert "SECRET_NOISE" not in row["text"]


def test_epub_spine_text_is_extracted(tmp_path: Path):
    path = tmp_path / "book.epub"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf", '<package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="c1" href="chapter1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>')
        z.writestr("OEBPS/chapter1.xhtml", "<html><body><h1>Chapter One</h1><p>The recurrent witness learns this text.</p></body></html>")
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert row["extractor"].startswith("stdlib-epub")
    assert "Chapter One" in row["text"]
    assert "recurrent witness learns this text" in row["text"]


def test_binary_file_is_unsupported(tmp_path: Path):
    path = tmp_path / "image.bin"
    path.write_bytes(b"\x00\x01\x02\x03")
    row = extract_artifact_text(path)
    assert row["status"] == "unsupported"



def test_mobi_palmdoc_uncompressed_extracts_markup(tmp_path: Path):
    import struct
    path = tmp_path / "book.mobi"
    text = b"<html><body><h1>Beyond Good and Evil</h1><p>The recurrent witness learns MOBI text.</p></body></html>"
    pdb = bytearray(78)
    pdb[:21] = b"Beyond_Good_and_Evil"
    pdb[60:68] = b"BOOKMOBI"
    pdb[76:78] = struct.pack(">H", 2)
    record0 = struct.pack(">HHIHHHH", 1, 0, len(text), 1, 4096, 0, 0)
    record0 += b"MOBI" + struct.pack(">IIIIIII", 32, 2, 65001, 1, 6, 0, 0)
    first = 78 + 16
    second = first + len(record0)
    table = struct.pack(">I", first) + b"\x00\x00\x00\x01" + struct.pack(">I", second) + b"\x00\x00\x00\x02"
    path.write_bytes(bytes(pdb) + table + record0 + text)
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert row["extractor"] == "stdlib-palmdoc-mobi+beautifulsoup-lxml"
    assert row["compression"] == 1
    assert "Beyond Good and Evil" in row["text"]
    assert "recurrent witness learns MOBI text" in row["text"]


def test_mobi_encrypted_is_explicitly_unsupported(tmp_path: Path):
    import struct
    path = tmp_path / "encrypted.mobi"
    text = b"<p>secret</p>"
    pdb = bytearray(78); pdb[60:68] = b"BOOKMOBI"; pdb[76:78] = struct.pack(">H", 2)
    record0 = struct.pack(">HHIHHHH", 1, 0, len(text), 1, 4096, 1, 0)
    record0 += b"MOBI" + struct.pack(">IIIIIII", 32, 2, 65001, 1, 6, 0, 0)
    first = 94; second = first + len(record0)
    table = struct.pack(">I", first) + b"\x00\x00\x00\x01" + struct.pack(">I", second) + b"\x00\x00\x00\x02"
    path.write_bytes(bytes(pdb) + table + record0 + text)
    row = extract_artifact_text(path)
    assert row["status"] == "unsupported"
    assert row["reason"] == "mobi_encrypted"



def test_mobi_uncompressed_trailing_entry_is_removed(tmp_path: Path):
    import struct
    path = tmp_path / "trailing.mobi"
    text = b"<html><body><p>Visible payload only.</p></body></html>"
    trailing = b"XY" + bytes([0x83])  # 3-byte entry; final byte is backward varint size.
    pdb = bytearray(78); pdb[60:68] = b"BOOKMOBI"; pdb[76:78] = struct.pack(">H", 2)
    record0 = bytearray(244)
    record0[0:16] = struct.pack(">HHIHHHH", 1, 0, len(text), 1, 4096, 0, 0)
    record0[16:20] = b"MOBI"
    record0[20:24] = struct.pack(">I", 228)
    record0[24:28] = struct.pack(">I", 2)
    record0[28:32] = struct.pack(">I", 65001)
    record0[104:108] = struct.pack(">I", 6)
    record0[242:244] = struct.pack(">H", 0x0002)
    first = 78 + 16; second = first + len(record0)
    table = struct.pack(">I", first) + b"\x00\x00\x00\x01" + struct.pack(">I", second) + b"\x00\x00\x00\x02"
    path.write_bytes(bytes(pdb) + table + bytes(record0) + text + trailing)
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert row["extra_data_flags"] == 2
    assert "Visible payload only" in row["text"]
    assert "XY" not in row["text"]



def test_opf_package_metadata_is_xml_extractable(tmp_path: Path):
    path = tmp_path / "metadata.opf"
    path.write_text('<?xml version="1.0"?><package><metadata><title>Witnessed Book</title><creator>Xavi</creator></metadata></package>', encoding="utf-8")
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert "Witnessed Book" in row["text"]
    assert "Xavi" in row["text"]


def test_sqlite_schema_and_rows_are_extracted_readonly(tmp_path: Path):
    import sqlite3
    path = tmp_path / "memory.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT, payload BLOB)")
    conn.execute("INSERT INTO notes(body, payload) VALUES (?, ?)", ("recurrent witness database row", b"abc"))
    conn.commit(); conn.close()
    before = path.stat().st_mtime_ns
    row = extract_artifact_text(path)
    after = path.stat().st_mtime_ns
    assert row["status"] == "ok"
    assert row["extractor"] == "stdlib-sqlite-readonly"
    assert "CREATE TABLE notes" in row["text"]
    assert "recurrent witness database row" in row["text"]
    assert "<blob:3 bytes>" in row["text"]
    assert before == after


def test_sqlite_extension_rejects_non_sqlite_binary(tmp_path: Path):
    path = tmp_path / "fake.db"
    path.write_bytes(b"not a sqlite database")
    row = extract_artifact_text(path)
    assert row["status"] == "unsupported"
    assert row["reason"] == "not_sqlite3"


def test_format_specific_limits_do_not_raise_generic_text_limit(tmp_path: Path):
    path = tmp_path / "large.txt"
    path.write_bytes(b"a" * 128)
    row = extract_artifact_text(path, max_bytes=64, max_pdf_bytes=1024, max_epub_bytes=1024)
    assert row["status"] == "deferred"
    assert row["reason"] == "artifact_exceeds_text_extraction_limit"


def test_successful_extraction_removes_nul_and_normalizes_nfc(tmp_path: Path):
    path = tmp_path / "canonical.txt"
    payload = ("prefix " * 100) + "Cafe\u0301\x00 tail"
    path.write_text(payload, encoding="utf-8")
    row = extract_artifact_text(path)
    assert row["status"] == "ok"
    assert "\x00" not in row["text"]
    assert unicodedata.is_normalized("NFC", row["text"])
    assert "Caf\u00e9 tail" in row["text"]
    assert row["chars"] == len(row["text"])
    assert row["nul_chars_removed"] == 1
    assert row["unicode_normalized"] == "NFC"
