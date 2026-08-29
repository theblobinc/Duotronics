from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace

from duotronic_runtime.train_ingest import TrainFolderIngestLoop


class FakeAutonomy:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def ingest_artifact(self, **kwargs):
        self.calls.append(kwargs)
        path = Path(kwargs["path"])
        return {"artifact": {"artifact_id": "artifact-" + path.name, "source_digest": "shake256-512:" + path.name}, "source_index": {"upsert": {"ok": True}}, "extraction": {"status": "ok"} if path.suffix in {".txt", ".md"} else None, "transcription": {"status": "ok"} if path.suffix == ".flac" else None}


def _loop(tmp_path: Path, monkeypatch, *, settle: float = 0):
    root = tmp_path / "train"
    state = tmp_path / "runtime" / "train_ingest_state.json"
    root.mkdir()
    monkeypatch.setenv("XAVI_TRAIN_ROOT", str(root))
    monkeypatch.setenv("XAVI_TRAIN_INGEST_STATE_PATH", str(state))
    monkeypatch.setenv("XAVI_TRAIN_SETTLE_SECONDS", str(settle))
    monkeypatch.setenv("XAVI_TRAIN_MAX_FILES_PER_SCAN", "4")
    autonomy = FakeAutonomy()
    return TrainFolderIngestLoop(SimpleNamespace(autonomy=autonomy)), autonomy, root


def test_stable_file_ingests_once_and_persists_state(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    (root / "speech.flac").write_bytes(b"fixture")
    first = loop.scan_once(); second = loop.scan_once()
    assert first["ingested"] == 1
    assert second["ingested"] == 0 and second["skipped_unchanged"] == 1
    assert len(autonomy.calls) == 1
    call = autonomy.calls[0]
    assert call["source_kind"].startswith("training-folder-")
    assert len(call["metadata"]["train_path_key"]) == 24
    assert call["training_eligible"] is True and call["auto_transcribe"] is True and call["auto_extract"] is True and call["auto_vision"] is True
    assert call["metadata"]["train_relative_path"] == "speech.flac"
    state = json.loads(loop.state_path.read_text())
    assert state["files"]["speech.flac"]["transcription_status"] == "ok"
    assert state["files"]["speech.flac"]["source_indexed"] is True
    assert state["files"]["speech.flac"]["processor_version"] == loop._processor_version_for(root / "speech.flac")


def test_changed_file_reingests(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    path = root / "notes.txt"; path.write_text("one")
    assert loop.scan_once()["ingested"] == 1
    path.write_text("two two"); os.utime(path, ns=(time.time_ns(), time.time_ns()))
    assert loop.scan_once()["ingested"] == 1
    assert len(autonomy.calls) == 2


def test_fresh_file_waits_for_settle_window(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch, settle=60)
    (root / "copying.mp4").write_bytes(b"still-copying")
    report = loop.scan_once()
    assert report["scanned"] == 0 and report["ingested"] == 0
    assert autonomy.calls == []


def test_failed_file_is_retried(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    (root / "retry.wav").write_bytes(b"audio")
    attempts = {"count": 0}
    def flaky(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return {"artifact": {"artifact_id": "ok", "source_digest": "shake256-512:ok"}, "source_index": {"upsert": {"ok": True}}, "extraction": None, "transcription": {"status": "ok"}}
    autonomy.ingest_artifact = flaky
    first = loop.scan_once()
    assert first["failed"] == 1 and first["retry_pending"] == 1
    state = json.loads(loop.state_path.read_text())
    row = state["files"]["retry.wav"]
    assert row["retry_pending"] is True
    assert row["retry_reason"] == "ingest_exception"
    assert row["retry_error"] == "RuntimeError"
    assert row["retry_attempts"] == 1
    second = loop.scan_once()
    assert second["ingested"] == 0 and second["retry_cooling"] == 1
    assert attempts["count"] == 1
    state["files"]["retry.wav"]["next_retry_at_ms"] = 0
    loop.state_path.write_text(json.dumps(state))
    third = loop.scan_once()
    assert third["ingested"] == 1
    assert attempts["count"] == 2


def test_state_survives_new_loop_instance(tmp_path, monkeypatch):
    loop, _, root = _loop(tmp_path, monkeypatch)
    (root / "persist.md").write_text("hello")
    assert loop.scan_once()["ingested"] == 1
    replacement_autonomy = FakeAutonomy()
    replacement = TrainFolderIngestLoop(SimpleNamespace(autonomy=replacement_autonomy))
    report = replacement.scan_once()
    assert report["skipped_unchanged"] == 1
    assert replacement_autonomy.calls == []


def test_legacy_state_without_processor_version_is_reprocessed(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    path = root / "legacy.txt"
    path.write_text("learn me")
    sig = loop._signature(path)
    loop.state_path.parent.mkdir(parents=True, exist_ok=True)
    loop.state_path.write_text(json.dumps({"schema_version": "old", "files": {"legacy.txt": sig}}))
    report = loop.scan_once()
    assert report["ingested"] == 1
    assert len(autonomy.calls) == 1


def test_retryable_vision_failure_remains_eligible(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    (root / "retry.jpg").write_bytes(b"image")
    attempts = {"count": 0}
    def flaky(**kwargs):
        attempts["count"] += 1
        base = {"artifact": {"artifact_id": "img", "source_digest": "shake256-512:img"}, "extraction": None, "transcription": None}
        if attempts["count"] == 1:
            return {**base, "source_index": None, "vision": {"status": "failed", "reason": "vision_request_failed"}}
        return {**base, "source_index": {"upsert": {"ok": True}}, "vision": {"status": "ok"}}
    autonomy.ingest_artifact = flaky
    first = loop.scan_once()
    assert first["retry_pending"] == 1 and first["remaining"] >= 1
    state = json.loads(loop.state_path.read_text())
    assert state["files"]["retry.jpg"]["processor_version"] is None
    assert state["files"]["retry.jpg"]["retry_pending"] is True
    assert state["files"]["retry.jpg"]["retry_attempts"] == 1
    assert state["files"]["retry.jpg"]["retry_processor_version"] == loop._processor_version_for(root / "retry.jpg")
    assert state["files"]["retry.jpg"]["next_retry_at_ms"] > state["files"]["retry.jpg"]["ingested_at_ms"]
    second = loop.scan_once()
    assert second["ingested"] == 0 and second["retry_cooling"] == 1
    assert attempts["count"] == 1
    state["files"]["retry.jpg"]["next_retry_at_ms"] = 0
    loop.state_path.write_text(json.dumps(state))
    third = loop.scan_once()
    assert third["ingested"] == 1
    assert attempts["count"] == 2
    state = json.loads(loop.state_path.read_text())
    assert state["files"]["retry.jpg"]["processor_version"] == loop._processor_version_for(root / "retry.jpg")
    assert state["files"]["retry.jpg"]["vision_status"] == "ok"
    assert state["files"]["retry.jpg"]["retry_pending"] is False


def test_size_deferred_vision_is_terminal_until_processor_changes(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    (root / "large.jpg").write_bytes(b"image")
    def deferred(**kwargs):
        return {
            "artifact": {"artifact_id": "large", "source_digest": "shake256-512:large"},
            "source_index": None, "extraction": None, "transcription": None,
            "vision": {"status": "deferred", "reason": "artifact_exceeds_synchronous_vision_limit"},
        }
    autonomy.ingest_artifact = deferred
    first = loop.scan_once(); second = loop.scan_once()
    assert first["retry_pending"] == 0
    assert second["skipped_unchanged"] == 1


def test_modality_specific_fingerprint_preserves_existing_document_index(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    doc = root / "already.txt"
    doc.write_text("already indexed", encoding="utf-8")
    sig = loop._signature(doc)
    loop.state_path.parent.mkdir(parents=True, exist_ok=True)
    loop.state_path.write_text(json.dumps({
        "schema_version": loop.schema_version,
        "files": {"already.txt": {**sig, "processor_version": f"{loop.schema_version}:xavi-artifact-text-extraction/v2", "source_indexed": True, "extraction_status": "ok"}},
    }), encoding="utf-8")
    report = loop.scan_once()
    assert report["skipped_unchanged"] == 1
    assert report["eligible"] == 0
    assert autonomy.calls == []


def test_new_vision_work_is_prioritized_before_legacy_documents(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    loop.max_files_per_scan = 1
    (root / "old.txt").write_text("legacy document", encoding="utf-8")
    (root / "cover.jpg").write_bytes(b"image")

    first = loop.scan_once()
    assert first["eligible_by_modality"]["vision"] == 1
    assert first["eligible_by_modality"]["extraction"] == 1
    assert autonomy.calls[0]["path"].endswith("old.txt")
    assert autonomy.calls[0]["metadata"]["modality"] == "extraction"

    second = loop.scan_once()
    assert second["selected_by_modality"]["vision"] == 1
    assert autonomy.calls[-1]["path"].endswith("cover.jpg")
    assert autonomy.calls[-1]["metadata"]["modality"] == "vision"


def test_mpeg_transport_stream_modality_uses_mime_not_typescript_suffix(tmp_path, monkeypatch):
    loop, _autonomy, root = _loop(tmp_path, monkeypatch)
    source = root / "capture.ts"
    source.write_bytes(b"mpeg")
    monkeypatch.setattr("duotronic_runtime.train_ingest.mimetypes.guess_type", lambda _name: ("video/mp2t", None))
    assert loop._modality(source) == "transcription"


def test_cooling_retry_does_not_starve_fresh_image(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    loop.max_files_per_scan = 1
    (root / "a-fails.jpg").write_bytes(b"bad")
    (root / "b-fresh.jpg").write_bytes(b"good")
    calls = []
    def ingest(**kwargs):
        calls.append(Path(kwargs["path"]).name)
        base = {"artifact": {"artifact_id": calls[-1], "source_digest": "shake256-512:x"}, "extraction": None, "transcription": None}
        if calls[-1] == "a-fails.jpg":
            return {**base, "source_index": None, "vision": {"status": "failed", "reason": "vision_request_failed", "error": "HTTPStatusError", "http_status": 500, "http_error": "connection refused"}}
        return {**base, "source_index": {"upsert": {"ok": True}}, "vision": {"status": "ok"}}
    autonomy.ingest_artifact = ingest
    first = loop.scan_once()
    assert first["results"][0]["path"] == "a-fails.jpg"
    second = loop.scan_once()
    assert second["retry_cooling"] == 1
    assert second["results"][0]["path"] == "b-fresh.jpg"
    assert calls == ["a-fails.jpg", "b-fresh.jpg"]
    state = json.loads(loop.state_path.read_text())
    row = state["files"]["a-fails.jpg"]
    assert row["retry_http_status"] == 500
    assert row["retry_http_error"] == "connection refused"


class _RegistryModelStub:
    def __init__(self, vision_model: str = "", transcription_model: str = "") -> None:
        self.vision_model = vision_model
        self.transcription_model = transcription_model

    def nodes(self, *, scheduler_ready_only: bool = False, role=None):
        services = {}
        if self.vision_model:
            services["vision"] = {"model": self.vision_model, "protocol": "ollama-api", "inference_path": "/api/generate", "request_format": "ollama-generate-images-base64", "response_format": "json", "worker_kind": "gpu"}
        if self.transcription_model:
            services["transcription"] = {"model": self.transcription_model, "model_sha256": "fixture", "protocol": "whisper.cpp-http", "inference_path": "/inference", "request_format": "multipart/form-data", "response_format": "json", "worker_kind": "cpu"}
        return [{"id": "worker", "scheduler_eligible": True, "services": services}]


def test_vision_processor_fingerprint_tracks_commissioned_model(tmp_path, monkeypatch):
    root = tmp_path / "train"; root.mkdir()
    state = tmp_path / "state.json"
    monkeypatch.setenv("XAVI_TRAIN_ROOT", str(root))
    monkeypatch.setenv("XAVI_TRAIN_INGEST_STATE_PATH", str(state))
    monkeypatch.setenv("XAVI_TRAIN_SETTLE_SECONDS", "0")
    a = TrainFolderIngestLoop(SimpleNamespace(autonomy=FakeAutonomy(), service_registry=_RegistryModelStub("minicpm-v:latest", "ggml-small.bin")))
    b = TrainFolderIngestLoop(SimpleNamespace(autonomy=FakeAutonomy(), service_registry=_RegistryModelStub("gemma3:4b", "ggml-small.bin")))
    assert a.processor_versions["vision"] != b.processor_versions["vision"]
    assert a.processor_versions["transcription"] == b.processor_versions["transcription"]
    assert a.processor_service_profiles["vision"]["models"] == ["minicpm-v:latest"]
    assert b.processor_service_profiles["vision"]["models"] == ["gemma3:4b"]


def test_old_processor_retry_cooldown_is_invalidated(tmp_path, monkeypatch):
    root = tmp_path / "train"; root.mkdir()
    state_path = tmp_path / "state.json"
    monkeypatch.setenv("XAVI_TRAIN_ROOT", str(root))
    monkeypatch.setenv("XAVI_TRAIN_INGEST_STATE_PATH", str(state_path))
    monkeypatch.setenv("XAVI_TRAIN_SETTLE_SECONDS", "0")
    autonomy = FakeAutonomy()
    loop = TrainFolderIngestLoop(SimpleNamespace(autonomy=autonomy, service_registry=_RegistryModelStub("gemma3:4b")))
    image = root / "retry.jpg"; image.write_bytes(b"image")
    sig = loop._signature(image)
    future_ms = int(time.time() * 1000) + 3_600_000
    state_path.write_text(json.dumps({"schema_version": loop.schema_version, "files": {"retry.jpg": {**sig, "processor_version": None, "retry_pending": True, "retry_processor_version": "old-minicpm-processor", "retry_attempts": 7, "next_retry_at_ms": future_ms}}}))
    report = loop.scan_once()
    assert report["retry_cooling"] == 0
    assert report["ingested"] == 1
    assert len(autonomy.calls) == 1
    state = json.loads(state_path.read_text())
    assert state["files"]["retry.jpg"]["processor_version"] == loop.processor_versions["vision"]
    assert state["files"]["retry.jpg"]["retry_pending"] is False
    assert state["files"]["retry.jpg"]["retry_attempts"] == 0


def test_weighted_modality_schedule_advances_mixed_backlog(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    loop.max_files_per_scan = 4
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        (root / name).write_bytes(b"image")
    for name in ("a.txt", "b.txt", "c.txt"):
        (root / name).write_text("document", encoding="utf-8")
    for name in ("a.flac", "b.flac", "c.flac"):
        (root / name).write_bytes(b"audio")
    (root / "a.bin").write_bytes(b"opaque")

    report = loop.scan_once()
    assert report["selected_by_modality"] == {"vision": 1, "extraction": 2, "transcription": 1, "witness": 0}
    modalities = [call["metadata"]["modality"] for call in autonomy.calls]
    assert modalities.count("extraction") == 2
    assert modalities.count("transcription") == 1
    assert modalities.count("vision") == 1


def test_modality_schedule_cursor_persists_and_reaches_witness(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    loop.max_files_per_scan = 1
    (root / "a.jpg").write_bytes(b"image")
    (root / "b.txt").write_text("document", encoding="utf-8")
    (root / "c.flac").write_bytes(b"audio")
    (root / "d.bin").write_bytes(b"opaque")

    first = loop.scan_once()
    assert first["selected_by_modality"]["extraction"] == 1

    replacement_autonomy = FakeAutonomy()
    replacement = TrainFolderIngestLoop(SimpleNamespace(autonomy=replacement_autonomy))
    replacement.max_files_per_scan = 1
    second = replacement.scan_once()
    third = replacement.scan_once()
    fourth = replacement.scan_once()

    assert second["selected_by_modality"]["transcription"] == 1
    assert third["selected_by_modality"]["vision"] == 1
    assert fourth["selected_by_modality"]["witness"] == 1
    assert [call["metadata"]["modality"] for call in replacement_autonomy.calls] == ["transcription", "vision", "witness"]
    state = replacement._load_state()
    assert state["modality_schedule_cursor"] == fourth["modality_schedule_cursor_end"]


def test_custom_modality_schedule_cannot_omit_a_modality(tmp_path, monkeypatch):
    monkeypatch.setenv("XAVI_TRAIN_MODALITY_SCHEDULE", "vision,vision")
    loop, _autonomy, _root = _loop(tmp_path, monkeypatch)
    assert loop.modality_schedule[:2] == ("vision", "vision")
    assert set(loop.modality_schedule) == {"vision", "extraction", "transcription", "witness"}



def test_transcription_http_failure_is_persisted_in_retry_state(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    (root / "course.mp4").write_bytes(b"video")
    def failed(**kwargs):
        return {
            "artifact": {"artifact_id": "vid", "source_digest": "shake256-512:vid"},
            "source_index": None, "extraction": None, "vision": None,
            "transcription": {"status": "failed", "reason": "transcription_request_failed", "error": "HTTPStatusError", "http_status": 413, "http_error": "worker payload rejected"},
        }
    autonomy.ingest_artifact = failed
    report = loop.scan_once()
    assert report["retry_pending"] == 1
    state = json.loads(loop.state_path.read_text())
    row = state["files"]["course.mp4"]
    assert row["retry_http_status"] == 413
    assert row["retry_http_error"] == "worker payload rejected"


def test_reclassified_items_precede_older_same_modality_items(tmp_path, monkeypatch):
    loop = _loop(tmp_path, monkeypatch)[0]
    loop.modality_schedule = ("extraction",)
    old = tmp_path / "old.pdf"
    old.write_bytes(b"old")
    reclassified = tmp_path / "newly-supported.mobi"
    reclassified.write_bytes(b"mobi")
    changed = [
        (1, old, "old.pdf", {"size": 3, "mtime_ns": 1}, "extraction", "v"),
        (0, reclassified, "newly-supported.mobi", {"size": 4, "mtime_ns": 2}, "extraction", "v"),
    ]
    selected, _start, _end = loop._select_batch(changed, {"modality_schedule_cursor": 0})
    assert selected[0][2] == "newly-supported.mobi"


def test_transcription_processor_version_binds_media_preflight(tmp_path, monkeypatch):
    loop = _loop(tmp_path, monkeypatch)[0]
    assert "transcription-v3" in loop.processor_versions["transcription"]
    assert "preflight-v1" in loop.processor_versions["transcription"]



def test_default_schedule_prefers_extraction_without_starving_modalities(tmp_path, monkeypatch):
    monkeypatch.delenv("XAVI_TRAIN_MODALITY_SCHEDULE", raising=False)
    loop = _loop(tmp_path, monkeypatch)[0]
    assert loop.modality_schedule == ("extraction", "transcription", "extraction", "vision", "witness")
    assert set(loop.modality_schedule) == {"extraction", "transcription", "vision", "witness"}



def test_retryable_extraction_failure_uses_bounded_backoff(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    path = root / "retry.txt"
    path.write_text("retry extraction", encoding="utf-8")
    attempts = {"count": 0}

    def flaky(**kwargs):
        attempts["count"] += 1
        base = {
            "artifact": {"artifact_id": "doc", "source_digest": "shake256-512:doc"},
            "transcription": None,
            "vision": None,
        }
        if attempts["count"] == 1:
            return {
                **base,
                "source_index": None,
                "extraction": {"status": "failed", "reason": "pdf_parse_failed", "error": "RuntimeError"},
            }
        return {
            **base,
            "source_index": {"upsert": {"ok": True}},
            "extraction": {"status": "ok"},
        }

    autonomy.ingest_artifact = flaky
    first = loop.scan_once()
    assert first["retry_pending"] == 1
    state = json.loads(loop.state_path.read_text())
    row = state["files"]["retry.txt"]
    assert row["processor_version"] is None
    assert row["retry_pending"] is True
    assert row["retry_attempts"] == 1
    assert row["retry_reason"] == "pdf_parse_failed"
    assert row["retry_error"] == "RuntimeError"
    assert row["retry_processor_version"] == loop._processor_version_for(path)

    second = loop.scan_once()
    assert second["retry_cooling"] == 1
    assert attempts["count"] == 1

    state["files"]["retry.txt"]["next_retry_at_ms"] = 0
    loop.state_path.write_text(json.dumps(state))
    third = loop.scan_once()
    assert third["ingested"] == 1
    assert attempts["count"] == 2
    state = json.loads(loop.state_path.read_text())
    row = state["files"]["retry.txt"]
    assert row["extraction_status"] == "ok"
    assert row["source_indexed"] is True
    assert row["retry_pending"] is False
    assert row["processor_version"] == loop._processor_version_for(path)


def test_extraction_limit_defer_is_terminal_until_processor_changes(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    path = root / "large.pdf"
    path.write_bytes(b"%PDF-1.7\nfixture")

    def deferred(**kwargs):
        return {
            "artifact": {"artifact_id": "large-doc", "source_digest": "shake256-512:large-doc"},
            "source_index": None,
            "extraction": {
                "status": "deferred",
                "reason": "artifact_exceeds_pdf_extraction_limit",
                "bytes": 400 * 1024 * 1024,
                "max_bytes": 384 * 1024 * 1024,
            },
            "transcription": None,
            "vision": None,
        }

    autonomy.ingest_artifact = deferred
    first = loop.scan_once()
    assert first["retry_pending"] == 0
    state = json.loads(loop.state_path.read_text())
    row = state["files"]["large.pdf"]
    assert row["extraction_status"] == "deferred"
    assert row["retry_pending"] is False
    assert row["processor_version"] == loop._processor_version_for(path)

    second = loop.scan_once()
    assert second["skipped_unchanged"] == 1



def test_transcription_service_fingerprint_changes_with_worker_image(tmp_path, monkeypatch):
    root = tmp_path / "train"
    root.mkdir()
    monkeypatch.setenv("XAVI_TRAIN_ROOT", str(root))
    monkeypatch.setenv("XAVI_TRAIN_INGEST_STATE_PATH", str(tmp_path / "state.json"))
    monkeypatch.setenv("XAVI_TRAIN_SETTLE_SECONDS", "0")

    class Registry:
        def __init__(self, image: str, image_id: str):
            self.image = image
            self.image_id = image_id

        def nodes(self, *, scheduler_ready_only: bool = False, role=None):
            return [{
                "id": "vm1",
                "services": {
                    "transcription": {
                        "model": "ggml-small.bin",
                        "model_sha256": "model-sha",
                        "protocol": "whisper.cpp-http",
                        "inference_path": "/inference",
                        "request_format": "multipart/form-data",
                        "response_format": "json",
                        "worker_kind": "cpu",
                        "image": self.image,
                        "image_id": self.image_id,
                    }
                },
            }]

    first = TrainFolderIngestLoop(SimpleNamespace(autonomy=FakeAutonomy(), service_registry=Registry("localhost/xavi-whisper-cpu:server-v1", "image-v1")))
    second = TrainFolderIngestLoop(SimpleNamespace(autonomy=FakeAutonomy(), service_registry=Registry("localhost/xavi-whisper-cpu:server-v2", "image-v2")))

    p1 = first.processor_service_profiles["transcription"]
    p2 = second.processor_service_profiles["transcription"]
    assert p1["records"][0]["image"] == "localhost/xavi-whisper-cpu:server-v1"
    assert p1["records"][0]["image_id"] == "image-v1"
    assert p2["records"][0]["image"] == "localhost/xavi-whisper-cpu:server-v2"
    assert p2["records"][0]["image_id"] == "image-v2"
    assert p1["digest"] != p2["digest"]
    assert first.processor_versions["transcription"] != second.processor_versions["transcription"]


def test_selected_modalities_execute_in_parallel(tmp_path, monkeypatch):
    loop, autonomy, root = _loop(tmp_path, monkeypatch)
    loop.max_files_per_scan = 2
    loop.parallel_workers = 2
    (root / "document.txt").write_text("hello", encoding="utf-8")
    (root / "speech.flac").write_bytes(b"audio")
    barrier = threading.Barrier(2)

    def parallel_ingest(**kwargs):
        path = Path(kwargs["path"])
        barrier.wait(timeout=2.0)
        base = {"artifact": {"artifact_id": "artifact-" + path.name, "source_digest": "shake256-512:" + path.name}}
        if path.suffix == ".txt":
            return {**base, "source_index": {"upsert": {"ok": True}}, "extraction": {"status": "ok"}, "transcription": None, "vision": None}
        return {**base, "source_index": {"upsert": {"ok": True}}, "extraction": None, "transcription": {"status": "ok"}, "vision": None}

    autonomy.ingest_artifact = parallel_ingest
    report = loop.scan_once()
    assert report["ingested"] == 2
    assert report["failed"] == 0
    assert report["parallel_workers"] == 2
    assert report["selected_by_modality"]["extraction"] == 1
    assert report["selected_by_modality"]["transcription"] == 1


def test_status_reports_parallel_workers(tmp_path, monkeypatch):
    loop, _autonomy, _root = _loop(tmp_path, monkeypatch)
    loop.parallel_workers = 3
    assert loop.status()["parallel_workers"] == 3
