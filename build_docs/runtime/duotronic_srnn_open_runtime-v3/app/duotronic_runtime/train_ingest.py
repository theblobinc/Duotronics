from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .artifact_extract import EXTRACTOR_VERSION, LOCAL_TEXT_EXTRACTOR_EXTENSIONS

_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"})
_TRANSCRIPTION_EXTENSIONS = frozenset({".mp3", ".wav", ".flac", ".ogg", ".oga", ".opus", ".m4a", ".aac", ".wma", ".aiff", ".aif", ".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".mpeg", ".mpg", ".3gp", ".3g2"})


class TrainFolderIngestLoop:
    """Bounded, deduplicated ingestion loop for the operator training folder."""

    schema_version = "xavi-train-folder-ingest/v2"

    def __init__(self, kernel: Any) -> None:
        self.kernel = kernel
        self.enabled = str(os.getenv("XAVI_TRAIN_INGEST_ENABLED", "1")).strip().lower() not in {"0", "false", "no", "off"}
        self.root = Path(os.getenv("XAVI_TRAIN_ROOT", "/train")).expanduser()
        runtime_data = Path(os.getenv("RUNTIME_DATA_DIR", "/runtime/data")).expanduser()
        self.state_path = Path(os.getenv("XAVI_TRAIN_INGEST_STATE_PATH", str(runtime_data / "train_ingest_state.json"))).expanduser()
        self.scan_seconds = max(10.0, float(os.getenv("XAVI_TRAIN_SCAN_SECONDS", "120")))
        self.backlog_scan_seconds = max(0.5, float(os.getenv("XAVI_TRAIN_BACKLOG_SCAN_SECONDS", "3")))
        self.settle_seconds = max(0.0, float(os.getenv("XAVI_TRAIN_SETTLE_SECONDS", "30")))
        self.processor_version = f"{self.schema_version}:modality-map/v2"
        self.processor_service_profiles = {
            "vision": self._service_processor_profile("vision"),
            "transcription": self._service_processor_profile("transcription"),
        }
        self.processor_versions = {
            "extraction": f"{self.schema_version}:{EXTRACTOR_VERSION}",
            "vision": f"{self.schema_version}:vision-v2:{self.processor_service_profiles['vision']['digest']}:retry-v2",
            "transcription": f"{self.schema_version}:transcription-v3:{self.processor_service_profiles['transcription']['digest']}:preflight-v1:retry-v2",
            "witness": f"{self.schema_version}:witness-v1",
        }
        self.max_files_per_scan = max(1, min(int(os.getenv("XAVI_TRAIN_MAX_FILES_PER_SCAN", "4")), 128))
        self.parallel_workers = max(1, min(int(os.getenv("XAVI_TRAIN_PARALLEL_WORKERS", "3")), 8))
        self.max_state_entries = max(100, min(int(os.getenv("XAVI_TRAIN_MAX_STATE_ENTRIES", "50000")), 500000))
        self.retry_base_seconds = max(5.0, min(float(os.getenv("XAVI_TRAIN_RETRY_BASE_SECONDS", "60")), 3600.0))
        self.retry_max_seconds = max(self.retry_base_seconds, min(float(os.getenv("XAVI_TRAIN_RETRY_MAX_SECONDS", "3600")), 86400.0))
        allowed_modalities = ("vision", "extraction", "transcription", "witness")
        requested_schedule = [item.strip().lower() for item in os.getenv("XAVI_TRAIN_MODALITY_SCHEDULE", "extraction,transcription,extraction,vision,witness").split(",") if item.strip().lower() in allowed_modalities]
        if not requested_schedule:
            requested_schedule = ["extraction", "transcription", "extraction", "vision", "witness"]
        for modality in allowed_modalities:
            if modality not in requested_schedule:
                requested_schedule.append(modality)
        self.modality_schedule = tuple(requested_schedule)
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._last_report: dict[str, Any] | None = None
        self._scan_lock = threading.Lock()

    def _service_processor_profile(self, service_name: str) -> dict[str, Any]:
        registry = getattr(self.kernel, "service_registry", None)
        records: list[dict[str, Any]] = []
        if registry is not None and hasattr(registry, "nodes"):
            try:
                nodes = registry.nodes(scheduler_ready_only=True)
            except Exception:
                nodes = []
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                services = node.get("services") if isinstance(node.get("services"), dict) else {}
                service = services.get(service_name) if isinstance(services.get(service_name), dict) else None
                if not service:
                    continue
                records.append({
                    "node_id": str(node.get("id") or ""),
                    "model": str(service.get("model") or ""),
                    "model_sha256": str(service.get("model_sha256") or ""),
                    "protocol": str(service.get("protocol") or ""),
                    "inference_path": str(service.get("inference_path") or service.get("embed_path") or ""),
                    "request_format": str(service.get("request_format") or ""),
                    "response_format": str(service.get("response_format") or ""),
                    "worker_kind": str(service.get("worker_kind") or ""),
                    "image": str(service.get("image") or ""),
                    "image_id": str(service.get("image_id") or ""),
                })
        records.sort(key=lambda row: (row["node_id"], row["model"], row["protocol"], row["inference_path"]))
        canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        digest = hashlib.shake_256(canonical).hexdigest(12)
        return {
            "service": service_name,
            "digest": digest,
            "models": sorted({row["model"] for row in records if row["model"]}),
            "nodes": [row["node_id"] for row in records],
            "records": records,
        }

    @staticmethod
    def _signature(path: Path) -> dict[str, int]:
        stat = path.stat()
        return {"size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)}

    @staticmethod
    def _modality(path: Path) -> str:
        suffix = path.suffix.lower()
        mime = str(mimetypes.guess_type(path.name)[0] or "").lower()
        if mime.startswith("image/") or suffix in _IMAGE_EXTENSIONS:
            return "vision"
        if mime.startswith(("audio/", "video/")) or suffix in _TRANSCRIPTION_EXTENSIONS:
            return "transcription"
        if suffix in LOCAL_TEXT_EXTRACTOR_EXTENSIONS or mime.startswith("text/") or mime in {"application/json", "application/x-ndjson", "application/javascript", "application/sql", "application/pdf", "application/epub+zip", "application/xhtml+xml", "application/xml"}:
            return "extraction"
        return "witness"

    def _processor_version_for(self, path: Path) -> str:
        return self.processor_versions[self._modality(path)]

    @staticmethod
    def _priority_for_modality(modality: str) -> int:
        return {"vision": 0, "transcription": 1, "extraction": 2, "witness": 3}.get(modality, 4)

    def _select_batch(self, changed: list[tuple[int, Path, str, dict[str, int], str, str]], state: dict[str, Any]) -> tuple[list[tuple[int, Path, str, dict[str, int], str, str]], int, int]:
        if not changed:
            cursor = int(state.get("modality_schedule_cursor") or 0) % len(self.modality_schedule)
            return [], cursor, cursor
        queues: dict[str, list[tuple[int, Path, str, dict[str, int], str, str]]] = {modality: [] for modality in {"vision", "extraction", "transcription", "witness"}}
        for row in changed:
            queues.setdefault(row[4], []).append(row)
        for queue in queues.values():
            queue.sort(key=lambda row: row[0])
        schedule = self.modality_schedule
        cursor = int(state.get("modality_schedule_cursor") or 0) % len(schedule)
        start_cursor = cursor
        selected: list[tuple[int, Path, str, dict[str, int], str, str]] = []
        misses = 0
        while len(selected) < self.max_files_per_scan and any(queues.values()):
            modality = schedule[cursor]
            cursor = (cursor + 1) % len(schedule)
            queue = queues.get(modality) or []
            if queue:
                selected.append(queue.pop(0))
                misses = 0
            else:
                misses += 1
                if misses >= len(schedule) and not any(queues.get(item) for item in schedule):
                    break
        state["modality_schedule_cursor"] = cursor
        return selected, start_cursor, cursor

    def _load_state(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("files"), dict):
                return payload
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return {"schema_version": self.schema_version, "files": {}}

    def _save_state(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        files = state.get("files") if isinstance(state.get("files"), dict) else {}
        if len(files) > self.max_state_entries:
            ordered = sorted(files.items(), key=lambda item: int((item[1] or {}).get("ingested_at_ms", 0)), reverse=True)[: self.max_state_entries]
            state["files"] = dict(ordered)
        state["schema_version"] = self.schema_version
        state["updated_at_ms"] = int(time.time() * 1000)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.state_path)

    def _candidate_files(self) -> list[Path]:
        if not self.root.is_dir():
            return []
        now = time.time()
        rows: list[tuple[int, str, Path]] = []
        for path in self.root.rglob("*"):
            try:
                if not path.is_file() or path.is_symlink():
                    continue
                stat = path.stat()
                if now - stat.st_mtime < self.settle_seconds:
                    continue
                rows.append((int(stat.st_mtime_ns), str(path), path))
            except OSError:
                continue
        rows.sort(key=lambda row: (row[0], row[1]))
        return [row[2] for row in rows]

    def scan_once(self) -> dict[str, Any]:
        with self._scan_lock:
            return self._scan_once_unlocked()

    def _scan_once_unlocked(self) -> dict[str, Any]:
        started = time.perf_counter()
        report: dict[str, Any] = {
            "schema_version": self.schema_version,
            "enabled": self.enabled,
            "root": str(self.root),
            "state_path": str(self.state_path),
            "settle_seconds": self.settle_seconds,
            "max_files_per_scan": self.max_files_per_scan,
            "scanned": 0,
            "eligible": 0,
            "ingested": 0,
            "skipped_unchanged": 0,
            "failed": 0,
            "retry_pending": 0,
            "retry_cooling": 0,
            "reclassified_eligible": 0,
            "next_retry_at_ms": None,
            "results": [],
        }
        if not self.enabled:
            report["status"] = "disabled"
            self._last_report = report
            return report
        if not self.root.is_dir():
            report.update({"status": "unavailable", "reason": "train_root_missing"})
            self._last_report = report
            return report

        state = self._load_state()
        known = state.setdefault("files", {})
        candidates = self._candidate_files()
        report["scanned"] = len(candidates)
        changed: list[tuple[int, Path, str, dict[str, int], str, str]] = []
        eligible_by_modality: dict[str, int] = {"vision": 0, "transcription": 0, "extraction": 0, "witness": 0}
        for path in candidates:
            try:
                rel = path.relative_to(self.root).as_posix()
                signature = self._signature(path)
            except (OSError, ValueError):
                continue
            previous = known.get(rel) if isinstance(known.get(rel), dict) else {}
            modality = self._modality(path)
            target_processor_version = self.processor_versions[modality]
            same_signature = previous.get("size") == signature["size"] and previous.get("mtime_ns") == signature["mtime_ns"]
            if same_signature and previous.get("processor_version") == target_processor_version:
                report["skipped_unchanged"] += 1
                continue
            now_ms = int(time.time() * 1000)
            same_retry_processor = str(previous.get("retry_processor_version") or "") == target_processor_version
            next_retry_at_ms = int(previous.get("next_retry_at_ms") or 0) if same_signature and previous.get("retry_pending") and same_retry_processor else 0
            if next_retry_at_ms > now_ms:
                report["retry_cooling"] += 1
                current_next = report.get("next_retry_at_ms")
                report["next_retry_at_ms"] = next_retry_at_ms if current_next is None else min(int(current_next), next_retry_at_ms)
                continue
            eligible_by_modality[modality] = int(eligible_by_modality.get(modality, 0)) + 1
            previous_modality = str(previous.get("modality") or "")
            reclassified = bool(previous_modality and previous_modality != modality)
            if reclassified:
                report["reclassified_eligible"] += 1
            selection_priority = 0 if reclassified else 1
            changed.append((selection_priority, path, rel, signature, modality, target_processor_version))

        selected, schedule_cursor_start, schedule_cursor_end = self._select_batch(changed, state)
        report["eligible"] = len(changed)
        report["eligible_by_modality"] = eligible_by_modality
        report["modality_schedule"] = list(self.modality_schedule)
        report["modality_schedule_cursor_start"] = schedule_cursor_start
        report["modality_schedule_cursor_end"] = schedule_cursor_end
        report["selected_by_modality"] = {modality: sum(1 for row in selected if row[4] == modality) for modality in ("vision", "extraction", "transcription", "witness")}
        report["parallel_workers"] = self.parallel_workers
        if selected:
            self._save_state(state)

        ingest_results: dict[str, Any] = {}
        ingest_errors: dict[str, Exception] = {}

        def _ingest_row(row: tuple[int, Path, str, dict[str, int], str, str]) -> Any:
            _priority, path, rel, _signature, modality, target_processor_version = row
            path_key = hashlib.shake_256(rel.encode("utf-8")).hexdigest(12)
            return self.kernel.autonomy.ingest_artifact(
                path=str(path),
                source_kind=f"training-folder-{path_key}",
                metadata={"scanner": self.schema_version, "scanner_processor_profile": self.processor_version, "processor_version": target_processor_version, "modality": modality, "train_relative_path": rel, "train_root": str(self.root), "train_path_key": path_key},
                training_eligible=True,
                auto_transcribe=True,
                auto_extract=True,
                auto_vision=True,
                session_id="train-folder-ingest",
            )

        def _ingest_group(rows: list[tuple[int, Path, str, dict[str, int], str, str]]) -> list[tuple[str, Any | None, Exception | None]]:
            outcomes: list[tuple[str, Any | None, Exception | None]] = []
            for row in rows:
                rel = row[2]
                try:
                    outcomes.append((rel, _ingest_row(row), None))
                except Exception as exc:
                    outcomes.append((rel, None, exc))
            return outcomes

        groups: dict[str, list[tuple[int, Path, str, dict[str, int], str, str]]] = {}
        for row in selected:
            groups.setdefault(row[4], []).append(row)
        if len(groups) > 1 and self.parallel_workers > 1:
            with ThreadPoolExecutor(max_workers=min(self.parallel_workers, len(groups)), thread_name_prefix="xavi-train-ingest") as pool:
                futures = [pool.submit(_ingest_group, rows) for rows in groups.values()]
                for future in as_completed(futures):
                    for rel_key, result, error in future.result():
                        if error is None:
                            ingest_results[rel_key] = result
                        else:
                            ingest_errors[rel_key] = error
        else:
            for rows in groups.values():
                for rel_key, result, error in _ingest_group(rows):
                    if error is None:
                        ingest_results[rel_key] = result
                    else:
                        ingest_errors[rel_key] = error

        for _priority, path, rel, signature, modality, target_processor_version in selected:
            try:
                path_key = hashlib.shake_256(rel.encode("utf-8")).hexdigest(12)
                if rel in ingest_errors:
                    raise ingest_errors[rel]
                result = ingest_results.get(rel)
                artifact = result.get("artifact") if isinstance(result, dict) else {}
                extraction = result.get("extraction") if isinstance(result, dict) else None
                transcription = result.get("transcription") if isinstance(result, dict) else None
                vision = result.get("vision") if isinstance(result, dict) else None
                source_index = result.get("source_index") if isinstance(result, dict) else None
                def _retryable_derived(row: Any) -> bool:
                    if not isinstance(row, dict):
                        return False
                    status = str(row.get("status") or "").lower()
                    reason = str(row.get("reason") or "").lower()
                    if status in {"failed", "unavailable"}:
                        return True
                    if status == "deferred" and "exceeds_synchronous" not in reason and "limit" not in reason:
                        return True
                    return False
                retryable = not bool(source_index) and (_retryable_derived(extraction) or _retryable_derived(transcription) or _retryable_derived(vision))
                previous = known.get(rel) if isinstance(known.get(rel), dict) else {}
                same_signature = previous.get("size") == signature["size"] and previous.get("mtime_ns") == signature["mtime_ns"]
                same_retry_processor = same_signature and str(previous.get("retry_processor_version") or "") == target_processor_version
                previous_attempts = int(previous.get("retry_attempts") or 0) if same_retry_processor else 0
                retry_attempts = previous_attempts + 1 if retryable else 0
                retry_delay_seconds = min(self.retry_max_seconds, self.retry_base_seconds * (2 ** min(max(retry_attempts - 1, 0), 16))) if retryable else 0.0
                now_ms = int(time.time() * 1000)
                next_retry_at_ms = now_ms + int(retry_delay_seconds * 1000) if retryable else None
                failure_row = extraction if _retryable_derived(extraction) else vision if _retryable_derived(vision) else transcription if _retryable_derived(transcription) else None
                known[rel] = {
                    **signature,
                    "processor_version": None if retryable else target_processor_version,
                    "modality": modality,
                    "artifact_id": artifact.get("artifact_id") if isinstance(artifact, dict) else None,
                    "source_digest": artifact.get("source_digest") if isinstance(artifact, dict) else None,
                    "extraction_status": extraction.get("status") if isinstance(extraction, dict) else None,
                    "transcription_status": transcription.get("status") if isinstance(transcription, dict) else None,
                    "vision_status": vision.get("status") if isinstance(vision, dict) else None,
                    "source_indexed": bool(source_index),
                    "retry_pending": retryable,
                    "retry_processor_version": target_processor_version if retryable else None,
                    "retry_attempts": retry_attempts,
                    "retry_delay_seconds": retry_delay_seconds if retryable else None,
                    "next_retry_at_ms": next_retry_at_ms,
                    "retry_reason": failure_row.get("reason") if isinstance(failure_row, dict) else None,
                    "retry_error": failure_row.get("error") if isinstance(failure_row, dict) else None,
                    "retry_http_status": failure_row.get("http_status") if isinstance(failure_row, dict) else None,
                    "retry_http_error": failure_row.get("http_error") if isinstance(failure_row, dict) else None,
                    "ingested_at_ms": now_ms,
                }
                report["ingested"] += 1
                if retryable:
                    report["retry_pending"] += 1
                report["results"].append({"path": rel, "status": "retry_pending" if retryable else "ingested", "modality": modality, "reclassified": _priority == 0, "processor_version": None if retryable else target_processor_version, "artifact_id": known[rel].get("artifact_id"), "extraction_status": known[rel].get("extraction_status"), "transcription_status": known[rel].get("transcription_status"), "vision_status": known[rel].get("vision_status"), "source_indexed": known[rel].get("source_indexed"), "retry_attempts": known[rel].get("retry_attempts"), "retry_delay_seconds": known[rel].get("retry_delay_seconds"), "next_retry_at_ms": known[rel].get("next_retry_at_ms")})
                self._save_state(state)
            except Exception as exc:
                previous = known.get(rel) if isinstance(known.get(rel), dict) else {}
                same_signature = previous.get("size") == signature["size"] and previous.get("mtime_ns") == signature["mtime_ns"]
                same_retry_processor = same_signature and str(previous.get("retry_processor_version") or "") == target_processor_version
                previous_attempts = int(previous.get("retry_attempts") or 0) if same_retry_processor else 0
                retry_attempts = previous_attempts + 1
                retry_delay_seconds = min(self.retry_max_seconds, self.retry_base_seconds * (2 ** min(max(retry_attempts - 1, 0), 16)))
                now_ms = int(time.time() * 1000)
                next_retry_at_ms = now_ms + int(retry_delay_seconds * 1000)
                known[rel] = {
                    **signature,
                    "processor_version": None,
                    "modality": modality,
                    "artifact_id": previous.get("artifact_id"),
                    "source_digest": previous.get("source_digest"),
                    "extraction_status": "failed" if modality == "extraction" else previous.get("extraction_status"),
                    "transcription_status": "failed" if modality == "transcription" else previous.get("transcription_status"),
                    "vision_status": "failed" if modality == "vision" else previous.get("vision_status"),
                    "source_indexed": False,
                    "retry_pending": True,
                    "retry_processor_version": target_processor_version,
                    "retry_attempts": retry_attempts,
                    "retry_delay_seconds": retry_delay_seconds,
                    "next_retry_at_ms": next_retry_at_ms,
                    "retry_reason": "ingest_exception",
                    "retry_error": exc.__class__.__name__,
                    "retry_detail": str(exc)[:1000],
                    "retry_http_status": None,
                    "retry_http_error": None,
                    "ingested_at_ms": now_ms,
                }
                report["failed"] += 1
                report["retry_pending"] += 1
                report["results"].append({"path": rel, "status": "retry_pending", "modality": modality, "error": exc.__class__.__name__, "retry_attempts": retry_attempts, "retry_delay_seconds": retry_delay_seconds, "next_retry_at_ms": next_retry_at_ms})
                self._save_state(state)

        report["remaining"] = max(0, len(changed) - len(selected)) + int(report.get("retry_pending") or 0) + int(report.get("retry_cooling") or 0)
        report["status"] = "ok" if report["failed"] == 0 else "degraded"
        report["wall_seconds"] = round(time.perf_counter() - started, 3)
        self._last_report = report
        return report

    def status(self) -> dict[str, Any]:
        state = self._load_state()
        return {
            "schema_version": self.schema_version,
            "enabled": self.enabled,
            "running": bool(self._task and not self._task.done()),
            "root": str(self.root),
            "root_available": self.root.is_dir(),
            "state_path": str(self.state_path),
            "known_file_count": len(state.get("files") or {}),
            "scan_seconds": self.scan_seconds,
            "backlog_scan_seconds": self.backlog_scan_seconds,
            "processor_version": self.processor_version,
            "processor_versions": dict(self.processor_versions),
            "processor_service_profiles": dict(self.processor_service_profiles),
            "settle_seconds": self.settle_seconds,
            "max_files_per_scan": self.max_files_per_scan,
            "parallel_workers": self.parallel_workers,
            "retry_base_seconds": self.retry_base_seconds,
            "retry_max_seconds": self.retry_max_seconds,
            "modality_schedule": list(self.modality_schedule),
            "modality_schedule_cursor": int(state.get("modality_schedule_cursor") or 0) % len(self.modality_schedule),
            "last_report": self._last_report,
        }

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            report = await asyncio.to_thread(self.scan_once)
            delay = self.backlog_scan_seconds if int(report.get("remaining") or 0) > 0 else self.scan_seconds
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
            except asyncio.TimeoutError:
                continue

    async def start(self) -> None:
        if not self.enabled or (self._task and not self._task.done()):
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="xavi-train-folder-ingest")

    async def stop(self) -> None:
        self._stop_event.set()
        task = self._task
        if task is None:
            return
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        finally:
            self._task = None
