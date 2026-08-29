from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import duotronic_runtime.autonomy_stack as autonomy_module
from duotronic_runtime.autonomy_stack import AutonomyStack


class _StoreStub:
    def __init__(self) -> None:
        self.documents: list[dict] = []
        self.generations: list[dict] = []

    def begin_source_generation(self, **kwargs):
        self.generations.append(dict(kwargs))
        return kwargs

    def upsert_source_documents(self, docs):
        rows = [dict(row) for row in docs]
        self.documents.extend(rows)
        return {"upserted": len(rows)}

    def finalize_source_generation(self, **kwargs):
        return kwargs


class _EvidenceStub:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def witness(self, witness_type, payload, **kwargs):
        row = {
            "witness_id": f"witness-{len(self.rows) + 1}",
            "witness_type": witness_type,
            **kwargs,
        }
        self.rows.append({"payload": payload, **row})
        return row


class _RegistryStub:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def scheduler_candidates(self, **kwargs):
        self.calls.append(dict(kwargs))
        return {
            "candidates": [
                {
                    "node_id": "vm1",
                    "service_endpoint": "http://10.77.0.3:8790",
                    "transport": "dedicated-private-ethernet",
                    "internet_required": False,
                    "score": 94.55,
                    "base_score": 98.76,
                    "pressure": 0.12,
                    "pressure_observation_digest": "node-pressure:test",
                }
            ],
            "pressure_observation": {"observation_digest": "node-pressure:test"},
        }

    def nodes(self):
        return [
            {
                "id": "vm1",
                "services": {
                    "transcription": {
                        "inference_path": "/inference",
                        "response_format": "json",
                        "protocol": "whisper.cpp-http",
                        "model": "ggml-small.bin",
                        "model_sha256": "model-sha",
                        "image": "localhost/xavi-whisper-cpu:server-v1",
                        "image_id": "image-id",
                    }
                },
            }
        ]


class _KernelStub:
    def __init__(self, tmp_path: Path) -> None:
        self.settings = SimpleNamespace(runtime_data_dir=str(tmp_path))
        self.store = _StoreStub()
        self.evidence = _EvidenceStub()
        self.service_registry = _RegistryStub()


def _stack(tmp_path: Path) -> tuple[AutonomyStack, _KernelStub]:
    kernel = _KernelStub(tmp_path)
    stack = AutonomyStack(kernel, root=tmp_path / "autonomy")
    stack.record_event = lambda **kwargs: {  # type: ignore[method-assign]
        "event_type": kwargs.get("event_type"),
        "content": kwargs.get("content"),
        "tags": kwargs.get("tags"),
    }
    return stack, kernel


class _FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return {"text": "ask not what your country can do for you"}


class _FakeClient:
    def __init__(self, *, calls: list[dict], **kwargs) -> None:
        self.calls = calls
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return _FakeResponse()


def test_transcription_uses_live_pressure_aware_scheduler_candidate(tmp_path, monkeypatch):
    stack, kernel = _stack(tmp_path)
    audio = tmp_path / "speech.flac"
    audio.write_bytes(b"fake-flac")
    client_calls: list[dict] = []

    monkeypatch.setattr(
        autonomy_module.httpx,
        "Client",
        lambda **kwargs: _FakeClient(calls=client_calls, **kwargs),
    )

    result = stack._transcribe_media(audio, mime_type="audio/flac", timeout_seconds=60)

    assert result["status"] == "ok"
    assert result["node_id"] == "vm1"
    assert result["endpoint"] == "http://10.77.0.3:8790"
    assert result["internet_required"] is False
    assert result["model"] == "ggml-small.bin"
    assert result["image_id"] == "image-id"
    assert result["text"] == "ask not what your country can do for you"
    assert kernel.service_registry.calls == [
        {
            "service": "transcription",
            "require_live": True,
            "live_timeout_seconds": 3.0,
            "observe_pressure": True,
            "pressure_timeout_seconds": 2.0,
            "limit": 1,
        }
    ]
    assert client_calls[0]["url"] == "http://10.77.0.3:8790/inference"
    assert client_calls[0]["data"] == {"response_format": "json"}
    assert client_calls[0]["files"]["file"][0] == "speech.flac"


def test_audio_ingest_auto_transcribes_and_indexes_transcript(tmp_path):
    stack, kernel = _stack(tmp_path)
    audio = tmp_path / "speech.mp3"
    audio.write_bytes(b"fake-mp3")
    stack._transcribe_media = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "schema_version": "xavi-media-transcription/v1",
        "status": "ok",
        "text": "transcribed spoken words",
        "text_digest": "shake256-512:transcript",
        "node_id": "vm1",
        "endpoint": "http://10.77.0.3:8790",
        "model": "ggml-small.bin",
        "pressure": 0.1,
    }

    result = stack.ingest_artifact(path=str(audio), source_kind="training-media")

    assert result["transcription"]["status"] == "ok"
    assert "text" not in result["transcription"]
    assert result["artifact"]["transcription"]["node_id"] == "vm1"
    assert result["artifact"]["derived_text_digest"]
    assert result["source_index"]["upsert"]["upserted"] == 1
    assert kernel.store.documents[0]["content"] == "transcribed spoken words"
    assert kernel.store.documents[0]["metadata"]["derivation"] == "transcript"
    assert kernel.store.documents[0]["metadata"]["transcription"]["status"] == "ok"
    assert result["event"]["tags"][-1] == "transcription:ok"


def test_transcription_failure_is_fail_soft_and_witnessed(tmp_path):
    stack, _kernel = _stack(tmp_path)
    audio = tmp_path / "broken.wav"
    audio.write_bytes(b"not-really-wav")
    stack._transcribe_media = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "schema_version": "xavi-media-transcription/v1",
        "status": "failed",
        "reason": "transcription_request_failed",
        "error": "ConnectError",
        "node_id": "vm1",
    }

    result = stack.ingest_artifact(path=str(audio), source_kind="training-media")

    assert result["artifact"]["witness"]["witness_type"] == "SourceMediaArtifactWitness"
    assert result["transcription"]["status"] == "failed"
    assert result["artifact"]["derived_text_digest"] is None
    assert result["source_index"] is None
    assert "transcription:failed" in result["event"]["tags"]


def test_explicit_derived_text_bypasses_auto_transcription(tmp_path):
    stack, kernel = _stack(tmp_path)
    audio = tmp_path / "supplied.mp3"
    audio.write_bytes(b"fake-mp3")

    def _unexpected(*args, **kwargs):
        raise AssertionError("transcription should be bypassed when derived_text is supplied")

    stack._transcribe_media = _unexpected  # type: ignore[method-assign]
    result = stack.ingest_artifact(
        path=str(audio),
        source_kind="training-media",
        derived_text="operator supplied transcript",
    )

    assert result["transcription"] is None
    assert kernel.store.documents[0]["content"] == "operator supplied transcript"


def test_large_media_is_explicitly_deferred_without_worker_call(tmp_path):
    stack, _kernel = _stack(tmp_path)
    video = tmp_path / "movie.mp4"
    video.write_bytes(b"12345678")

    def _unexpected(*args, **kwargs):
        raise AssertionError("oversized synchronous media must be deferred")

    stack._transcribe_media = _unexpected  # type: ignore[method-assign]
    result = stack.ingest_artifact(
        path=str(video),
        source_kind="training-media",
        metadata={"transcription_max_bytes": 4},
    )

    assert result["transcription"]["status"] == "deferred"
    assert result["transcription"]["reason"] == "artifact_exceeds_synchronous_transcription_limit"
    assert result["source_index"] is None


def test_typescript_ts_stays_text_and_never_transcribes(tmp_path, monkeypatch):
    stack, kernel = _stack(tmp_path)
    source = tmp_path / "example.ts"
    source.write_text("const answer: number = 42;", encoding="utf-8")
    monkeypatch.setattr(autonomy_module.mimetypes, "guess_type", lambda _name: ("text/typescript", None))

    def _unexpected(*args, **kwargs):
        raise AssertionError("TypeScript must not be sent to the transcription worker")

    stack._transcribe_media = _unexpected  # type: ignore[method-assign]
    result = stack.ingest_artifact(path=str(source), source_kind="source-code")

    assert result["transcription"] is None
    assert kernel.store.documents[0]["content"] == "const answer: number = 42;"


def test_mpeg_transport_stream_ts_uses_media_mime_and_transcribes(tmp_path, monkeypatch):
    stack, kernel = _stack(tmp_path)
    source = tmp_path / "capture.ts"
    source.write_bytes(b"fake-mpeg-ts")
    monkeypatch.setattr(autonomy_module.mimetypes, "guess_type", lambda _name: ("video/mp2t", None))
    stack._transcribe_media = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "schema_version": "xavi-media-transcription/v1",
        "status": "ok",
        "text": "transport stream spoken words",
        "text_digest": "shake256-512:mpeg-ts",
        "node_id": "vm1",
        "endpoint": "http://10.77.0.3:8790",
    }

    result = stack.ingest_artifact(path=str(source), source_kind="training-media")

    assert result["transcription"]["status"] == "ok"
    assert kernel.store.documents[0]["content"] == "transport stream spoken words"
    assert kernel.store.documents[0]["metadata"]["derivation"] == "transcript"


class _VisionRegistryStub:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def scheduler_candidates(self, **kwargs):
        self.calls.append(dict(kwargs))
        return {
            "candidates": [{
                "node_id": "tbi-production-3",
                "service_endpoint": "http://10.77.0.2:11434",
                "transport": "dedicated-private-ethernet",
                "internet_required": False,
                "score": 146.12,
                "base_score": 150.84,
                "pressure": 0.135,
                "pressure_observation_digest": "node-pressure:vision-test",
            }],
            "pressure_observation": {"observation_digest": "node-pressure:vision-test"},
        }

    def nodes(self):
        return [{
            "id": "tbi-production-3",
            "services": {"vision": {
                "inference_path": "/api/generate",
                "protocol": "ollama-api",
                "model": "minicpm-v:latest",
                "num_predict": 192,
                "temperature": 0.0,
            }},
        }]


class _FakeVisionResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return {"response": "A red painted cover with the visible number 148."}


class _FakeVisionClient:
    def __init__(self, *, calls: list[dict], **kwargs) -> None:
        self.calls = calls
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return _FakeVisionResponse()


def test_vision_uses_live_pressure_aware_scheduler_candidate(tmp_path, monkeypatch):
    stack, kernel = _stack(tmp_path)
    kernel.service_registry = _VisionRegistryStub()
    image = tmp_path / "cover.jpg"
    image.write_bytes(b"fake-jpeg")
    client_calls: list[dict] = []
    monkeypatch.setattr(autonomy_module.httpx, "Client", lambda **kwargs: _FakeVisionClient(calls=client_calls, **kwargs))

    result = stack._understand_image(image, mime_type="image/jpeg", timeout_seconds=30)

    assert result["status"] == "ok"
    assert result["node_id"] == "tbi-production-3"
    assert result["endpoint"] == "http://10.77.0.2:11434"
    assert result["internet_required"] is False
    assert result["model"] == "minicpm-v:latest"
    assert result["pressure"] == 0.135
    assert result["text"].startswith("A red painted cover")
    assert kernel.service_registry.calls == [{
        "service": "vision", "require_live": True, "live_timeout_seconds": 3.0,
        "observe_pressure": True, "pressure_timeout_seconds": 2.0, "limit": 1,
    }]
    payload = client_calls[0]["json"]
    assert client_calls[0]["url"] == "http://10.77.0.2:11434/api/generate"
    assert payload["model"] == "minicpm-v:latest"
    assert payload["images"] and isinstance(payload["images"][0], str)
    assert payload["stream"] is False


def test_image_ingest_auto_describes_and_indexes_candidate_text(tmp_path):
    stack, kernel = _stack(tmp_path)
    image = tmp_path / "art.jpg"
    image.write_bytes(b"fake-image")
    stack._understand_image = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "schema_version": "xavi-image-understanding/v1", "status": "ok",
        "text": "Abstract red artwork with the visible number 148.",
        "text_digest": "shake256-512:vision", "node_id": "tbi-production-3",
        "endpoint": "http://10.77.0.2:11434", "model": "minicpm-v:latest", "pressure": 0.1,
    }

    result = stack.ingest_artifact(path=str(image), source_kind="training-image")

    assert result["vision"]["status"] == "ok"
    assert "text" not in result["vision"]
    assert result["artifact"]["vision"]["model"] == "minicpm-v:latest"
    assert result["artifact"]["derived_text_digest"]
    assert result["source_index"]["upsert"]["upserted"] == 1
    assert kernel.store.documents[0]["content"].startswith("Abstract red artwork")
    assert kernel.store.documents[0]["metadata"]["derivation"] == "image-description"
    assert kernel.store.documents[0]["metadata"]["vision"]["status"] == "ok"
    assert "vision:ok" in result["event"]["tags"]


def test_image_vision_failure_is_fail_soft_and_witnessed(tmp_path):
    stack, _kernel = _stack(tmp_path)
    image = tmp_path / "broken.png"
    image.write_bytes(b"not-really-png")
    stack._understand_image = lambda *args, **kwargs: {  # type: ignore[method-assign]
        "schema_version": "xavi-image-understanding/v1", "status": "failed",
        "reason": "vision_request_failed", "error": "ConnectError", "node_id": "tbi-production-3",
    }
    result = stack.ingest_artifact(path=str(image), source_kind="training-image")
    assert result["artifact"]["witness"]["witness_type"] == "SourceMediaArtifactWitness"
    assert result["vision"]["status"] == "failed"
    assert result["artifact"]["derived_text_digest"] is None
    assert result["source_index"] is None
    assert "vision:failed" in result["event"]["tags"]


def test_explicit_derived_text_bypasses_auto_vision(tmp_path):
    stack, kernel = _stack(tmp_path)
    image = tmp_path / "captioned.jpg"
    image.write_bytes(b"fake-image")
    def _unexpected(*args, **kwargs):
        raise AssertionError("vision should be bypassed when derived_text is supplied")
    stack._understand_image = _unexpected  # type: ignore[method-assign]
    result = stack.ingest_artifact(path=str(image), source_kind="training-image", derived_text="operator supplied caption")
    assert result["vision"] is None
    assert kernel.store.documents[0]["content"] == "operator supplied caption"


def test_vision_http_failure_keeps_bounded_diagnostics(tmp_path, monkeypatch):
    stack, kernel = _stack(tmp_path)
    kernel.service_registry = _VisionRegistryStub()
    image = tmp_path / "error.jpg"
    image.write_bytes(b"fake-jpeg")
    class ErrorClient:
        def __init__(self, **kwargs): self.kwargs = kwargs
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
        def post(self, url, **kwargs):
            request = autonomy_module.httpx.Request("POST", url)
            return autonomy_module.httpx.Response(500, request=request, json={"error": "connection refused"})
    monkeypatch.setattr(autonomy_module.httpx, "Client", ErrorClient)
    result = stack._understand_image(image, mime_type="image/jpeg", timeout_seconds=30)
    assert result["status"] == "failed"
    assert result["error"] == "HTTPStatusError"
    assert result["http_status"] == 500
    assert result["http_error"] == "connection refused"
    assert result["queue_wait_seconds"] >= 0



class _FakeFailedTranscriptionResponse:
    status_code = 413

    def raise_for_status(self) -> None:
        raise autonomy_module.httpx.HTTPStatusError(
            "payload too large",
            request=autonomy_module.httpx.Request("POST", "http://10.77.0.3:8790/inference"),
            response=autonomy_module.httpx.Response(413, json={"error": "worker payload rejected"}),
        )

    def json(self):
        return {"error": "worker payload rejected"}


class _FakeFailedTranscriptionClient(_FakeClient):
    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return _FakeFailedTranscriptionResponse()


def test_transcription_http_failure_retains_bounded_response_provenance(tmp_path, monkeypatch):
    stack, _kernel = _stack(tmp_path)
    audio = tmp_path / "rejected.mp4"
    audio.write_bytes(b"fake-video")
    calls = []
    monkeypatch.setattr(autonomy_module.httpx, "Client", lambda **kwargs: _FakeFailedTranscriptionClient(calls=calls, **kwargs))
    result = stack._transcribe_media(audio, mime_type="video/mp4", timeout_seconds=60)
    assert result["status"] == "failed"
    assert result["reason"] == "transcription_request_failed"
    assert result["error"] == "HTTPStatusError"
    assert result["http_status"] == 413
    assert result["http_error"] == "worker payload rejected"


def test_invalid_mp4_preflight_skips_transcription_worker(tmp_path):
    stack, _kernel = _stack(tmp_path)
    video = tmp_path / "broken.mp4"

    def box(kind: bytes, payload: bytes = b"") -> bytes:
        return (8 + len(payload)).to_bytes(4, "big") + kind + payload

    video.write_bytes(box(b"ftyp", b"isom0000") + box(b"mdat", b"payload"))

    def _unexpected(*args, **kwargs):
        raise AssertionError("structurally invalid MP4 must not reach the transcription worker")

    stack._transcribe_media = _unexpected  # type: ignore[method-assign]
    result = stack.ingest_artifact(path=str(video), source_kind="training-media")

    assert result["transcription"]["status"] == "invalid"
    assert result["transcription"]["reason"] == "isobmff_missing_moov"
    assert result["artifact"]["media_preflight"]["status"] == "invalid"
    assert result["source_index"] is None
