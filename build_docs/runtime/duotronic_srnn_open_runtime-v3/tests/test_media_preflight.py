from pathlib import Path

from duotronic_runtime.media_preflight import MEDIA_PREFLIGHT_VERSION, preflight_media


def _box(kind: bytes, payload: bytes = b"") -> bytes:
    return (8 + len(payload)).to_bytes(4, "big") + kind + payload


def test_valid_isobmff_requires_moov_and_mdat(tmp_path: Path):
    path = tmp_path / "valid.mp4"
    path.write_bytes(_box(b"ftyp", b"isom0000") + _box(b"moov") + _box(b"mdat", b"abc"))
    row = preflight_media(path, mime_type="video/mp4")
    assert row["schema_version"] == MEDIA_PREFLIGHT_VERSION
    assert row["status"] == "ok"
    assert row["has_moov"] is True
    assert row["has_mdat"] is True


def test_isobmff_missing_moov_is_invalid(tmp_path: Path):
    path = tmp_path / "broken.mp4"
    path.write_bytes(_box(b"ftyp", b"isom0000") + _box(b"mdat", b"abc"))
    row = preflight_media(path, mime_type="video/mp4")
    assert row["status"] == "invalid"
    assert row["reason"] == "isobmff_missing_moov"


def test_isobmff_truncated_box_is_invalid(tmp_path: Path):
    path = tmp_path / "truncated.m4a"
    path.write_bytes((100).to_bytes(4, "big") + b"mdat" + b"tiny")
    row = preflight_media(path)
    assert row["status"] == "invalid"
    assert row["reason"] == "isobmff_box_truncated"


def test_non_isobmff_is_not_applicable(tmp_path: Path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"not validated here")
    row = preflight_media(path, mime_type="audio/mpeg")
    assert row["status"] == "not_applicable"
