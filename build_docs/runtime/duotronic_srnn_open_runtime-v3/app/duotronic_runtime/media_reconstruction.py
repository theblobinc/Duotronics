from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx
import numpy as np

SCHEMA_VERSION = "media_reconstruction_witness/v1"
TEMPORAL_SCHEMA = "media_temporal_witness/v3"
GATE_SCHEMA = "wgrnn_temporal_witness_gate/v2"
ANALYSIS_VERSION = "duotronic-media-reconstruction/v2"
COMPARISON_SCHEMA = "media_cross_comparison_signature/v1"
MOTIF_SCHEMA = "media_motif_catalog/v1"
MOTIF_OCCURRENCE_SCHEMA = "media_motif_occurrence/v1"
FORMAL_CONTRACT = "Duotronic Witness Contract v1.6 Draft 5.3.18"
MAX_SOURCE_BYTES = 256 * 1024 * 1024


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Multiple runtime threads may persist progress/cancellation for the same job
    # concurrently. A fixed state.json.tmp lets one writer replace another writer's
    # temp file, causing FileNotFoundError or stale state. Use a unique temp inode in
    # the destination directory so os.replace remains atomic without writer collision.
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass


def _safe_name(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name or "media")).strip("-._") or "media"
    return base[:180]


def _parse_rate(value: Any, fallback: float = 30.0) -> float:
    text = str(value or "").strip()
    if "/" in text:
        a, b = text.split("/", 1)
        try:
            n, d = float(a), float(b)
            return n / d if d else fallback
        except Exception:
            return fallback
    try:
        n = float(text)
        return n if n > 0 else fallback
    except Exception:
        return fallback


def _note_name(freq: float) -> tuple[str | None, float | None]:
    if not math.isfinite(freq) or freq < 40.0 or freq > 5000.0:
        return None, None
    midi = 69.0 + 12.0 * math.log2(freq / 440.0)
    nearest = int(round(midi))
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[nearest % 12]}{nearest // 12 - 1}", 100.0 * (midi - nearest)


def _color_name(rgb: list[int] | tuple[int, int, int]) -> str:
    r, g, b = [max(0, min(255, int(x))) for x in rgb]
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 35:
        return "black"
    if mn > 220:
        return "white"
    if mx - mn < 22:
        return "gray"
    if r > g * 1.25 and r > b * 1.25:
        return "red" if g < 150 else "orange"
    if g > r * 1.2 and g > b * 1.2:
        return "green"
    if b > r * 1.2 and b > g * 1.2:
        return "blue"
    if r > 150 and g > 130 and b < 100:
        return "yellow"
    if r > 120 and b > 100 and g < 120:
        return "purple"
    return "mixed"


TERMINAL_JOB_STATUSES = frozenset({"completed", "failed", "cancelled", "interrupted"})


class MediaReconstructionCancelled(RuntimeError):
    pass


class MediaReconstructionManager:
    def __init__(self, data_dir: Path, service_registry: Any, *, max_workers: int = 1) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.service_registry = service_registry
        self.executor = ThreadPoolExecutor(max_workers=max(1, int(max_workers)), thread_name_prefix="media-reconstruction")
        self._lock = threading.Lock()
        self._futures: dict[str, Any] = {}
        self._recover_interrupted_jobs()

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=False)

    def _recover_interrupted_jobs(self) -> None:
        now_ms = int(time.time() * 1000)
        for root in self.data_dir.glob("mediarec-*"):
            state_path = root / "state.json"
            if not state_path.is_file():
                continue
            try:
                state = json.loads(state_path.read_text())
            except Exception:
                continue
            if str(state.get("status") or "") not in {"queued", "running", "cancelling"}:
                continue
            if (root / "result.json").is_file():
                state.update(status="completed", stage="completed", progress=1.0)
                state.setdefault("completed_at_ms", now_ms)
            else:
                state.update(
                    status="interrupted",
                    stage="interrupted",
                    interrupted_at_ms=now_ms,
                    detail="runtime_restart_interrupted_job",
                )
            state["updated_at_ms"] = now_ms
            _atomic_json(state_path, state)

    def start_job(self, source_bytes: bytes, *, filename: str, mime_type: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        data = bytes(source_bytes)
        if not data:
            raise ValueError("media_reconstruction_empty_source")
        if len(data) > MAX_SOURCE_BYTES:
            raise ValueError("media_reconstruction_source_too_large")
        job_id = "mediarec-" + uuid.uuid4().hex[:24]
        root = self.data_dir / job_id
        root.mkdir(parents=True, exist_ok=False)
        suffix = Path(filename or "media").suffix[:12]
        source = root / ("source" + suffix)
        source.write_bytes(data)
        state = {
            "schema_version": SCHEMA_VERSION,
            "job_id": job_id,
            "status": "queued",
            "stage": "queued",
            "progress": 0.0,
            "filename": _safe_name(filename),
            "mime_type": str(mime_type or "application/octet-stream"),
            "source_bytes": len(data),
            "created_at_ms": int(time.time() * 1000),
        }
        _atomic_json(root / "state.json", state)
        future = self.executor.submit(self._run_job, job_id, source, state["filename"], state["mime_type"], dict(options or {}))
        with self._lock:
            self._futures[job_id] = future
        return state

    def refine_from_job(
        self,
        parent_job_id: str,
        *,
        range_start_seconds: float,
        range_end_seconds: float,
        analysis_profile: str = "forensic_range",
        deterministic_rate_hz: float | None = None,
        semantic_interval_seconds: float | None = None,
        max_semantic_anchors: int | None = None,
    ) -> dict[str, Any]:
        parent_root = self._job_root(parent_job_id)
        parent_state = self.status(parent_job_id)
        source_candidates = sorted(
            p for p in parent_root.iterdir()
            if p.is_file() and p.name.startswith("source")
        )
        if not source_candidates:
            raise RuntimeError("media_reconstruction_retained_source_missing")
        start = float(range_start_seconds)
        end = float(range_end_seconds)
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start or end - start < 0.05:
            raise ValueError("media_reconstruction_invalid_range")
        profile = str(analysis_profile or "forensic_range").strip().lower()
        if profile not in {"full", "deep_range", "forensic_range"}:
            raise ValueError("media_reconstruction_invalid_profile")

        source_parent = source_candidates[0]
        job_id = "mediarec-" + uuid.uuid4().hex[:24]
        root = self.data_dir / job_id
        root.mkdir(parents=True, exist_ok=False)
        source = root / ("source" + source_parent.suffix[:12])
        reuse_mode = "hardlink"
        try:
            os.link(source_parent, source)
        except OSError:
            shutil.copy2(source_parent, source)
            reuse_mode = "copy"

        options = {
            "range_start_seconds": start,
            "range_end_seconds": end,
            "analysis_profile": profile,
            "deterministic_rate_hz": deterministic_rate_hz,
            "semantic_interval_seconds": semantic_interval_seconds,
            "max_semantic_anchors": max_semantic_anchors,
        }
        state = {
            "schema_version": SCHEMA_VERSION,
            "job_id": job_id,
            "status": "queued",
            "stage": "queued",
            "progress": 0.0,
            "filename": str(parent_state.get("filename") or source_parent.name),
            "mime_type": str(parent_state.get("mime_type") or "application/octet-stream"),
            "source_bytes": int(source.stat().st_size),
            "created_at_ms": int(time.time() * 1000),
            "parent_job_id": parent_job_id,
            "lineage": {
                "schema_version": "media_reconstruction_lineage/v1",
                "relation": "retained_source_refinement",
                "parent_job_id": parent_job_id,
                "source_reuse": reuse_mode,
                "requested_range": {
                    "start_seconds": round(start, 6),
                    "end_seconds": round(end, 6),
                    "analysis_profile": profile,
                },
            },
        }
        _atomic_json(root / "state.json", state)
        future = self.executor.submit(
            self._run_job,
            job_id,
            source,
            state["filename"],
            state["mime_type"],
            options,
        )
        with self._lock:
            self._futures[job_id] = future
        return state

    def status(self, job_id: str) -> dict[str, Any]:
        root = self._job_root(job_id)
        path = root / "state.json"
        if not path.is_file():
            raise KeyError(job_id)
        state = json.loads(path.read_text())
        if (root / "cancel.requested").exists() and state.get("status") not in TERMINAL_JOB_STATUSES:
            state["cancel_requested"] = True
        state["has_result"] = (root / "result.json").is_file()
        return state

    def list_jobs(self, *, limit: int = 50, status: str | None = None) -> dict[str, Any]:
        wanted = str(status or "").strip().lower()
        rows: list[dict[str, Any]] = []
        for root in self.data_dir.glob("mediarec-*"):
            path = root / "state.json"
            if not path.is_file():
                continue
            try:
                state = json.loads(path.read_text())
            except Exception:
                continue
            if wanted and str(state.get("status") or "").lower() != wanted:
                continue
            state["has_result"] = (root / "result.json").is_file()
            state["source_present"] = any(p.is_file() and p.name.startswith("source") for p in root.iterdir())
            rows.append(state)
        rows.sort(key=lambda row: (int(row.get("created_at_ms") or 0), str(row.get("job_id") or "")), reverse=True)
        bounded = max(1, min(int(limit or 50), 200))
        return {
            "schema_version": "media_reconstruction_job_history/v1",
            "jobs": rows[:bounded],
            "count": len(rows[:bounded]),
            "total_matching": len(rows),
        }

    def cancel(self, job_id: str) -> dict[str, Any]:
        root = self._job_root(job_id)
        state = self.status(job_id)
        if str(state.get("status") or "") in TERMINAL_JOB_STATUSES:
            return state
        (root / "cancel.requested").touch(exist_ok=True)
        with self._lock:
            future = self._futures.get(job_id)
        if future is not None and future.cancel():
            state.update(
                status="cancelled",
                stage="cancelled",
                progress=float(state.get("progress") or 0),
                cancel_requested=True,
                cancelled_at_ms=int(time.time() * 1000),
            )
            _atomic_json(root / "state.json", state)
            return state
        state.update(status="cancelling", stage="cancelling", cancel_requested=True)
        self._state(root, state)
        return state

    def delete(self, job_id: str) -> dict[str, Any]:
        root = self._job_root(job_id)
        state = self.status(job_id)
        if str(state.get("status") or "") not in TERMINAL_JOB_STATUSES:
            raise RuntimeError("media_reconstruction_job_active")
        with self._lock:
            self._futures.pop(job_id, None)
        shutil.rmtree(root)
        return {"schema_version": "media_reconstruction_job_delete/v1", "job_id": job_id, "deleted": True}

    def result(self, job_id: str) -> dict[str, Any]:
        root = self._job_root(job_id)
        path = root / "result.json"
        if not path.is_file():
            state = self.status(job_id)
            raise RuntimeError(f"media_reconstruction_result_not_ready:{state.get('status')}")
        return json.loads(path.read_text())

    def _comparison_signature_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        nodes = result.get("nodes") if isinstance(result, dict) else None
        if not isinstance(nodes, list) or not nodes or not isinstance(nodes[0], dict):
            raise ValueError("media_comparison_missing_reconstruction_node")
        witness = nodes[0].get("witness")
        if not isinstance(witness, dict):
            raise ValueError("media_comparison_missing_witness")
        existing = witness.get("comparison_signatures")
        reconstruction = witness.get("reconstruction")
        if not isinstance(reconstruction, dict):
            if isinstance(existing, dict) and existing.get("schema_version") == COMPARISON_SCHEMA:
                # Signature-only retained records remain valid. Without the original
                # reconstruction we cannot truthfully infer capability coverage, so
                # the comparator's legacy default semantics apply.
                return dict(existing)
            raise ValueError("media_comparison_missing_reconstruction")
        visual = reconstruction.get("visual") if isinstance(reconstruction.get("visual"), dict) else {}
        audio = reconstruction.get("audio") if isinstance(reconstruction.get("audio"), dict) else {}
        transcript = audio.get("transcript") if isinstance(audio.get("transcript"), dict) else {}
        if isinstance(existing, dict) and existing.get("schema_version") == COMPARISON_SCHEMA:
            bundle = dict(existing)
        else:
            bundle = self._comparison_signatures(
                visual.get("semantic_anchors") or [],
                transcript.get("segments") or [],
                audio,
                visual.get("entity_tracks") or [],
                visual.get("temporal_transitions") or [],
            )
        # Coverage is deliberately not part of the canonical signature hash. It tells
        # the comparator whether a retained historical reconstruction actually had a
        # given observation capability. "observed" with zero features is meaningful;
        # "unavailable" must not be treated as evidence that the feature was absent.
        has_transitions = "temporal_transitions" in visual
        has_tracks = "entity_tracks" in visual
        bundle["evidence_coverage"] = {
            "visual_context": "observed" if "semantic_anchors" in visual else "unavailable",
            "motion": "observed" if (has_tracks or has_transitions) else "unavailable",
            "state_change": "observed" if has_transitions else "unavailable",
            "scene_change": "observed" if has_transitions else "unavailable",
            "speech_text": "observed" if "transcript" in audio else "unavailable",
            "speech_prosody": "observed" if "transcript" in audio else "unavailable",
            "music": "observed" if any(key in audio for key in ("note_intervals", "chord_intervals", "ml_note_events", "tempo_bpm_hypothesis")) else "unavailable",
        }
        bundle["coverage_semantics"] = "observed_empty_is_evidence; unavailable_is_excluded_from_similarity_denominator"
        return bundle

    @staticmethod
    def _compare_signature_bundles(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        def jaccard(a_values: Any, b_values: Any) -> float | None:
            aa = {str(x) for x in (a_values or []) if str(x)}
            bb = {str(x) for x in (b_values or []) if str(x)}
            if not aa and not bb:
                return None
            return len(aa & bb) / max(1, len(aa | bb))

        def lcs_ratio(a_values: Any, b_values: Any) -> float | None:
            aa = [str(x) for x in (a_values or []) if str(x)][:128]
            bb = [str(x) for x in (b_values or []) if str(x)][:128]
            if not aa and not bb:
                return None
            if not aa or not bb:
                return 0.0
            # Two-row LCS keeps comparison bounded and deterministic.
            prev = [0] * (len(bb) + 1)
            for av in aa:
                cur = [0]
                for j, bv in enumerate(bb, 1):
                    cur.append(prev[j - 1] + 1 if av == bv else max(prev[j], cur[-1]))
                prev = cur
            return prev[-1] / max(len(aa), len(bb))

        family_weights = {
            "visual_context": 0.14,
            "motion": 0.20,
            "state_change": 0.16,
            "scene_change": 0.10,
            "speech_text": 0.14,
            "speech_prosody": 0.11,
            "music": 0.15,
        }
        lf = left.get("families") if isinstance(left.get("families"), dict) else {}
        rf = right.get("families") if isinstance(right.get("families"), dict) else {}
        lc = left.get("evidence_coverage") if isinstance(left.get("evidence_coverage"), dict) else {}
        rc = right.get("evidence_coverage") if isinstance(right.get("evidence_coverage"), dict) else {}

        def coverage_status(coverage: dict[str, Any], family: str) -> str:
            # Old in-memory/test bundles without explicit coverage predate this field;
            # preserve their prior semantics by treating them as observed.
            return str(coverage.get(family) or "observed")

        comparable_families = {
            family for family in family_weights
            if coverage_status(lc, family) == "observed" and coverage_status(rc, family) == "observed"
        }
        family_overlap: dict[str, Any] = {}
        weighted_sum = 0.0
        active_weight = 0.0
        for family, weight in family_weights.items():
            left_coverage = coverage_status(lc, family)
            right_coverage = coverage_status(rc, family)
            comparable = family in comparable_families
            score = jaccard(lf.get(family), rf.get(family)) if comparable else None
            family_overlap[family] = {
                "score": round(score, 6) if score is not None else None,
                "left_count": len(lf.get(family) or []),
                "right_count": len(rf.get(family) or []),
                "weight": weight,
                "comparable": comparable,
                "left_coverage": left_coverage,
                "right_coverage": right_coverage,
            }
            if score is not None:
                weighted_sum += weight * score
                active_weight += weight
        family_score = weighted_sum / active_weight if active_weight else None

        ls = left.get("sequence_sketches") if isinstance(left.get("sequence_sketches"), dict) else {}
        rs = right.get("sequence_sketches") if isinstance(right.get("sequence_sketches"), dict) else {}
        sequence_overlap: dict[str, Any] = {}
        seq_scores: list[float] = []
        sequence_families = {
            "transitions": {"motion", "state_change", "scene_change"},
            "chords": {"music"},
            "pitch_classes": {"music"},
        }
        for name in sorted(set(ls) | set(rs)):
            required = sequence_families.get(name, set())
            comparable = not required or required.issubset(comparable_families)
            score = lcs_ratio(ls.get(name), rs.get(name)) if comparable else None
            sequence_overlap[name] = {
                "score": round(score, 6) if score is not None else None,
                "left_length": len(ls.get(name) or []),
                "right_length": len(rs.get(name) or []),
                "metric": "normalized_lcs",
                "comparable": comparable,
                "required_families": sorted(required),
            }
            if score is not None:
                seq_scores.append(score)
        sequence_score = sum(seq_scores) / len(seq_scores) if seq_scores else None

        def comparable_tokens(bundle: dict[str, Any]) -> list[str]:
            out: list[str] = []
            for token in bundle.get("tokens") or []:
                value = str(token)
                family = value.split(":", 1)[0]
                if family in comparable_families:
                    out.append(value)
            return out

        left_comparable_tokens = comparable_tokens(left)
        right_comparable_tokens = comparable_tokens(right)
        token_score = jaccard(left_comparable_tokens, right_comparable_tokens)
        components: list[tuple[float, float]] = []
        if token_score is not None:
            components.append((0.40, token_score))
        if family_score is not None:
            components.append((0.40, family_score))
        if sequence_score is not None:
            components.append((0.20, sequence_score))
        denom = sum(weight for weight, _ in components)
        overall = sum(weight * score for weight, score in components) / denom if denom else 0.0
        exact = bool(left.get("signature")) and left.get("signature") == right.get("signature")
        if exact:
            overall = 1.0

        lt = {str(x) for x in (left.get("tokens") or [])}
        rt = {str(x) for x in (right.get("tokens") or [])}
        return {
            "schema_version": "media_cross_comparison/v1",
            "authority": "heuristic_similarity_evidence_only",
            "identity_semantics": "not_person_identity_evidence; compare witnessed media structure/content only",
            "exact_normalized_signature_match": exact,
            "overall_similarity": round(max(0.0, min(1.0, overall)), 6),
            "token_jaccard": round(token_score, 6) if token_score is not None else None,
            "family_weighted_similarity": round(family_score, 6) if family_score is not None else None,
            "sequence_similarity": round(sequence_score, 6) if sequence_score is not None else None,
            "family_overlap": family_overlap,
            "sequence_overlap": sequence_overlap,
            "comparison_coverage": {
                "comparable_families": sorted(comparable_families),
                "excluded_families": sorted(set(family_weights) - comparable_families),
                "left": {family: coverage_status(lc, family) for family in family_weights},
                "right": {family: coverage_status(rc, family) for family in family_weights},
                "semantics": "unavailable historical evidence is excluded; observed-empty remains comparable evidence",
            },
            "common_tokens": sorted(set(left_comparable_tokens) & set(right_comparable_tokens))[:160],
            "left_only_tokens": sorted(set(left_comparable_tokens) - set(right_comparable_tokens))[:160],
            "right_only_tokens": sorted(set(right_comparable_tokens) - set(left_comparable_tokens))[:160],
            "left_signature": left.get("signature"),
            "right_signature": right.get("signature"),
        }

    def _relationship_store(self) -> dict[str, Any]:
        path = self.data_dir / "relationships.json"
        if not path.is_file():
            return {"schema_version": "media_reconstruction_relationship_store/v1", "relationships": []}
        try:
            payload = json.loads(path.read_text())
        except Exception:
            return {"schema_version": "media_reconstruction_relationship_store/v1", "relationships": []}
        rows = payload.get("relationships") if isinstance(payload, dict) else None
        return {
            "schema_version": "media_reconstruction_relationship_store/v1",
            "relationships": [dict(row) for row in rows if isinstance(row, dict)] if isinstance(rows, list) else [],
        }

    def _record_relationship(
        self,
        *,
        relation_type: str,
        source_job_id: str,
        target_job_id: str,
        evidence: dict[str, Any],
        authority: str,
        relationship_key: str | None = None,
    ) -> dict[str, Any]:
        now_ms = int(time.time() * 1000)
        key = str(relationship_key or (relation_type + "|" + source_job_id + "|" + target_job_id))
        relation_id = "mediarel-" + uuid.uuid5(uuid.NAMESPACE_URL, key).hex[:24]
        with self._lock:
            store = self._relationship_store()
            rows = store["relationships"]
            existing = next((row for row in rows if str(row.get("relation_id") or "") == relation_id), None)
            if existing is None:
                existing = {
                    "schema_version": "media_reconstruction_relationship/v1",
                    "relation_id": relation_id,
                    "relation_type": str(relation_type),
                    "source_job_id": str(source_job_id),
                    "target_job_id": str(target_job_id),
                    "authority": str(authority or "witnessed_relationship_evidence"),
                    "observation_count": 0,
                    "created_at_ms": now_ms,
                }
                rows.append(existing)
            existing["source_job_id"] = str(source_job_id)
            existing["target_job_id"] = str(target_job_id)
            existing["authority"] = str(authority or existing.get("authority") or "witnessed_relationship_evidence")
            existing["evidence"] = json.loads(json.dumps(evidence or {}))
            existing["observation_count"] = int(existing.get("observation_count") or 0) + 1
            existing["updated_at_ms"] = now_ms
            rows.sort(key=lambda row: (int(row.get("updated_at_ms") or 0), str(row.get("relation_id") or "")), reverse=True)
            store["relationships"] = rows[:2000]
            _atomic_json(self.data_dir / "relationships.json", store)
            return json.loads(json.dumps(existing))

    def investigation_graph(self, *, limit: int = 100, relationship_limit: int = 500) -> dict[str, Any]:
        bounded = max(1, min(int(limit or 100), 200))
        rel_bound = max(1, min(int(relationship_limit or 500), 2000))
        history = self.list_jobs(limit=bounded)
        node_map: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        for state in history.get("jobs") or []:
            if not isinstance(state, dict):
                continue
            job_id = str(state.get("job_id") or "")
            if not job_id:
                continue
            lineage = state.get("lineage") if isinstance(state.get("lineage"), dict) else None
            analysis_profile = None
            analysis_range = None
            result_path = self.data_dir / job_id / "result.json"
            if result_path.is_file():
                try:
                    result = json.loads(result_path.read_text())
                    analysis_profile = result.get("analysis_profile")
                    reconstruction = self._reconstruction_from_result(result)
                    analysis_range = reconstruction.get("analysis_range") if isinstance(reconstruction.get("analysis_range"), dict) else None
                except Exception:
                    pass
            node_map[job_id] = {
                "job_id": job_id,
                "label": state.get("filename") or job_id,
                "filename": state.get("filename"),
                "status": state.get("status"),
                "stage": state.get("stage"),
                "created_at_ms": int(state.get("created_at_ms") or 0),
                "has_result": bool(state.get("has_result")),
                "source_present": bool(state.get("source_present")),
                "analysis_profile": analysis_profile or ((lineage or {}).get("requested_range") or {}).get("analysis_profile"),
                "analysis_range": analysis_range,
                "parent_job_id": state.get("parent_job_id"),
                "lineage": lineage,
                "node_role": "refinement_child" if lineage and lineage.get("relation") == "retained_source_refinement" else "reconstruction",
                "tombstone": False,
            }
            if lineage and lineage.get("relation") == "retained_source_refinement":
                parent = str(state.get("parent_job_id") or lineage.get("parent_job_id") or "")
                if parent:
                    edges.append({
                        "edge_id": "lineage-" + uuid.uuid5(uuid.NAMESPACE_URL, parent + "|" + job_id).hex[:24],
                        "relation_type": "retained_source_refinement",
                        "source_job_id": parent,
                        "target_job_id": job_id,
                        "authority": "direct_job_lineage_provenance",
                        "evidence": json.loads(json.dumps(lineage)),
                        "observation_count": 1,
                    })

        relationship_rows = self._relationship_store().get("relationships") or []
        relationship_rows = sorted(
            [row for row in relationship_rows if isinstance(row, dict)],
            key=lambda row: (int(row.get("updated_at_ms") or 0), str(row.get("relation_id") or "")),
            reverse=True,
        )[:rel_bound]
        for row in relationship_rows:
            edges.append({
                "edge_id": row.get("relation_id"),
                "relation_type": row.get("relation_type"),
                "source_job_id": row.get("source_job_id"),
                "target_job_id": row.get("target_job_id"),
                "authority": row.get("authority"),
                "evidence": row.get("evidence") or {},
                "observation_count": int(row.get("observation_count") or 1),
                "created_at_ms": row.get("created_at_ms"),
                "updated_at_ms": row.get("updated_at_ms"),
            })

        for edge in edges:
            for endpoint in ("source_job_id", "target_job_id"):
                job_id = str(edge.get(endpoint) or "")
                if not job_id or job_id in node_map:
                    continue
                node_map[job_id] = {
                    "job_id": job_id,
                    "label": job_id,
                    "filename": None,
                    "status": "missing_or_deleted",
                    "stage": "tombstone",
                    "created_at_ms": 0,
                    "has_result": False,
                    "source_present": False,
                    "analysis_profile": None,
                    "analysis_range": None,
                    "parent_job_id": None,
                    "lineage": None,
                    "node_role": "tombstone",
                    "tombstone": True,
                }

        nodes = list(node_map.values())
        nodes.sort(key=lambda row: (bool(row.get("tombstone")), -int(row.get("created_at_ms") or 0), str(row.get("job_id") or "")))
        edge_counts: dict[str, int] = {}
        for edge in edges:
            kind = str(edge.get("relation_type") or "unknown")
            edge_counts[kind] = edge_counts.get(kind, 0) + 1
        return {
            "schema_version": "media_witness_investigation_graph/v1",
            "authority": "job_lineage_plus_recorded_comparison_alignment_evidence",
            "identity_semantics": "not_person_identity_evidence; graph records media-analysis provenance and witnessed relationship evidence",
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "edge_counts": edge_counts,
            "relationship_store_count": len(relationship_rows),
        }

    def compare_jobs(self, left_job_id: str, right_job_id: str) -> dict[str, Any]:
        left_result = self.result(left_job_id)
        right_result = self.result(right_job_id)
        left = self._comparison_signature_from_result(left_result)
        right = self._comparison_signature_from_result(right_result)
        comparison = self._compare_signature_bundles(left, right)
        comparison.update({
            "left_job_id": left_job_id,
            "right_job_id": right_job_id,
            "left_label": ((left_result.get("nodes") or [{}])[0] or {}).get("label"),
            "right_label": ((right_result.get("nodes") or [{}])[0] or {}).get("label"),
        })
        pair = sorted((str(left_job_id), str(right_job_id)))
        self._record_relationship(
            relation_type="cross_media_comparison",
            source_job_id=left_job_id,
            target_job_id=right_job_id,
            relationship_key="cross_media_comparison|" + pair[0] + "|" + pair[1],
            authority=str(comparison.get("authority") or "heuristic_similarity_evidence_only"),
            evidence={
                "overall_similarity": comparison.get("overall_similarity"),
                "exact_normalized_signature_match": comparison.get("exact_normalized_signature_match"),
                "token_jaccard": comparison.get("token_jaccard"),
                "family_weighted_similarity": comparison.get("family_weighted_similarity"),
                "sequence_similarity": comparison.get("sequence_similarity"),
                "comparison_coverage": comparison.get("comparison_coverage"),
            },
        )
        return comparison

    @staticmethod
    def _reconstruction_from_result(result: dict[str, Any]) -> dict[str, Any]:
        nodes = result.get("nodes") if isinstance(result, dict) else None
        if not isinstance(nodes, list) or not nodes or not isinstance(nodes[0], dict):
            raise ValueError("media_comparison_missing_reconstruction_node")
        witness = nodes[0].get("witness")
        if not isinstance(witness, dict):
            raise ValueError("media_comparison_missing_witness")
        reconstruction = witness.get("reconstruction")
        if not isinstance(reconstruction, dict):
            raise ValueError("media_comparison_missing_reconstruction")
        return reconstruction

    @staticmethod
    def _record_overlaps_window(row: Any, start: float, end: float) -> bool:
        if not isinstance(row, dict):
            return False
        if row.get("time_seconds") is not None:
            value = float(row.get("time_seconds") or 0)
            return start <= value <= end
        a = row.get("start_seconds")
        b = row.get("end_seconds")
        if a is None and b is None:
            return False
        left = float(a if a is not None else b or 0)
        right = float(b if b is not None else a or 0)
        return right >= start and left <= end

    @staticmethod
    def _clip_interval_to_window(row: Any, start: float, end: float) -> dict[str, Any] | None:
        """Return one interval clipped to a window while preserving its source bounds."""
        if not isinstance(row, dict):
            return None
        a = row.get("start_seconds")
        b = row.get("end_seconds")
        if a is None and b is None:
            if row.get("time_seconds") is None:
                return None
            point = float(row.get("time_seconds") or 0)
            if not (start <= point <= end):
                return None
            out = dict(row)
            out["source_time_seconds"] = point
            out["window_overlap_fraction"] = 1.0
            return out
        left = float(a if a is not None else b or 0)
        right = float(b if b is not None else a or 0)
        if right < left:
            left, right = right, left
        if right == left:
            if not (start <= left <= end):
                return None
            clipped_left = clipped_right = left
            fraction = 1.0
        else:
            clipped_left = max(start, left)
            clipped_right = min(end, right)
            if clipped_right <= clipped_left:
                return None
            fraction = (clipped_right - clipped_left) / max(1e-9, right - left)
        out = dict(row)
        out["source_start_seconds"] = round(left, 6)
        out["source_end_seconds"] = round(right, 6)
        out["start_seconds"] = round(clipped_left, 6)
        out["end_seconds"] = round(clipped_right, 6)
        out["duration_seconds"] = round(max(0.0, clipped_right - clipped_left), 6)
        out["window_overlap_fraction"] = round(max(0.0, min(1.0, fraction)), 6)
        return out

    @staticmethod
    def _window_delivery(words: list[dict[str, Any]], audio_frames: list[dict[str, Any]], start: float, end: float) -> dict[str, Any]:
        """Recompute delivery/prosody from only the words and measured acoustics in a window."""
        in_window = [
            frame for frame in audio_frames
            if isinstance(frame, dict)
            and frame.get("time_seconds") is not None
            and start <= float(frame.get("time_seconds") or 0) <= end
        ]
        pitches = [float(frame["pitch_hz"]) for frame in in_window if frame.get("pitch_hz")]
        rms = [float(frame.get("rms") or 0) for frame in in_window]
        centroid = [float(frame.get("spectral_centroid_hz") or 0) for frame in in_window]
        flux = [float(frame.get("spectral_flux") or 0) for frame in in_window]
        probs = [float(word.get("probability") or 0) for word in words]
        ordered = sorted(words, key=lambda row: (float(row.get("start_seconds") or 0), int(row.get("word_index") or 0)))
        pause_total = 0.0
        previous_end = start
        for word in ordered:
            w_start = float(word.get("start_seconds") or start)
            pause_total += max(0.0, w_start - previous_end)
            previous_end = max(previous_end, float(word.get("end_seconds") or w_start))
        rate = len(ordered) / max(0.05, end - start)
        mean_rms = float(np.mean(rms)) if rms else None
        median_pitch = float(np.median(pitches)) if pitches else None
        pitch_range = float(max(pitches) - min(pitches)) if pitches else None
        pitch_std = float(np.std(pitches)) if pitches else None
        pace_band = "slow" if rate < 1.5 else ("moderate" if rate <= 3.2 else "fast")
        energy_band = None if mean_rms is None else ("low" if mean_rms < 0.03 else ("moderate" if mean_rms < 0.12 else "high"))
        pitch_dynamics = None
        if median_pitch and pitch_std is not None:
            ratio = pitch_std / max(1.0, median_pitch)
            pitch_dynamics = "steady" if ratio < 0.06 else ("moderately_variable" if ratio < 0.16 else "highly_variable")
        return {
            "mean_rms": round(mean_rms, 6) if mean_rms is not None else None,
            "median_pitch_hz": round(median_pitch, 2) if median_pitch is not None else None,
            "pitch_range_hz": round(pitch_range, 2) if pitch_range is not None else None,
            "pitch_stddev_hz": round(pitch_std, 2) if pitch_std is not None else None,
            "mean_spectral_centroid_hz": round(float(np.mean(centroid)), 2) if centroid else None,
            "mean_spectral_flux": round(float(np.mean(flux)), 6) if flux else None,
            "word_rate_per_second": round(rate, 3),
            "pause_total_seconds": round(pause_total, 4),
            "segment_asr_probability_mean": round(float(np.mean(probs)), 6) if probs else None,
            "segment_asr_probability_min": round(float(min(probs)), 6) if probs else None,
            "prosody": {
                "pace_band": pace_band,
                "energy_band": energy_band,
                "pitch_dynamics": pitch_dynamics,
                "authority": "heuristic_labels_from_window_local_measured_acoustics",
            },
            "affect": {
                "status": "not_inferred_from_acoustics_alone",
                "note": "Emotion/intent is not promoted from voice measurements without independent evidence.",
            },
            "accent": {
                "status": "not_geographically_inferred",
                "note": "Only acoustic/phonetic measurements are retained; ethnicity/nationality are not inferred from voice.",
            },
            "window_local": True,
        }

    def _window_transcript(
        self,
        transcript: dict[str, Any],
        audio_frames: list[dict[str, Any]],
        *,
        start: float,
        end: float,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
        """Slice ASR evidence by timed words first; never reuse a whole long segment when word timing exists."""
        source_segments = [row for row in (transcript.get("segments") or []) if isinstance(row, dict)]
        source_words = [row for row in (transcript.get("words") or []) if isinstance(row, dict)]
        if not source_words:
            for segment in source_segments:
                source_words.extend(row for row in (segment.get("words") or []) if isinstance(row, dict))
        timing_available = any(row.get("start_seconds") is not None or row.get("end_seconds") is not None for row in source_words)

        window_words: list[dict[str, Any]] = []
        for row in source_words:
            clipped = self._clip_interval_to_window(row, start, end)
            if clipped is not None:
                window_words.append(clipped)
        window_words.sort(key=lambda row: (float(row.get("start_seconds") or 0), int(row.get("segment_index") or 0), int(row.get("word_index") or 0)))

        by_segment: dict[int, list[dict[str, Any]]] = {}
        for word in window_words:
            try:
                idx = int(word.get("segment_index") or 0)
            except Exception:
                idx = 0
            by_segment.setdefault(idx, []).append(word)

        segments: list[dict[str, Any]] = []
        fallback_segments = 0
        for fallback_idx, source in enumerate(source_segments):
            try:
                idx = int(source.get("segment_index") if source.get("segment_index") is not None else fallback_idx)
            except Exception:
                idx = fallback_idx
            local_words = by_segment.get(idx, [])
            if local_words:
                seg_start = min(float(row.get("start_seconds") or start) for row in local_words)
                seg_end = max(float(row.get("end_seconds") or seg_start) for row in local_words)
                text = "".join(str(row.get("word") or "") for row in local_words).strip()
                segment = dict(source)
                segment["source_start_seconds"] = float(source.get("start_seconds") or seg_start)
                segment["source_end_seconds"] = float(source.get("end_seconds") or seg_end)
                segment["start_seconds"] = round(max(start, seg_start), 6)
                segment["end_seconds"] = round(min(end, seg_end), 6)
                segment["duration_seconds"] = round(max(0.0, segment["end_seconds"] - segment["start_seconds"]), 6)
                segment["text"] = text
                segment["words"] = local_words
                segment["delivery"] = self._window_delivery(local_words, audio_frames, segment["start_seconds"], segment["end_seconds"])
                segment["window_text_timing"] = "word_timestamps"
                segments.append(segment)
            elif not timing_available:
                clipped_segment = self._clip_interval_to_window(source, start, end)
                if clipped_segment is None:
                    continue
                clipped_segment["delivery"] = self._window_delivery([], audio_frames, clipped_segment["start_seconds"], clipped_segment["end_seconds"])
                clipped_segment["window_text_timing"] = "segment_interval_fallback"
                clipped_segment["source_text_scope"] = "entire_overlapping_segment_text"
                segments.append(clipped_segment)
                fallback_segments += 1

        # Handle timed words whose segment record is absent.
        known = {int(seg.get("segment_index") or 0) for seg in segments}
        for idx, words in sorted(by_segment.items()):
            if idx in known or not words:
                continue
            seg_start = min(float(row.get("start_seconds") or start) for row in words)
            seg_end = max(float(row.get("end_seconds") or seg_start) for row in words)
            segments.append({
                "segment_index": idx,
                "text": "".join(str(row.get("word") or "") for row in words).strip(),
                "start_seconds": round(seg_start, 6),
                "end_seconds": round(seg_end, 6),
                "duration_seconds": round(max(0.0, seg_end - seg_start), 6),
                "words": words,
                "delivery": self._window_delivery(words, audio_frames, seg_start, seg_end),
                "authority": "asr_and_window_local_acoustic_hypothesis",
                "window_text_timing": "word_timestamps",
            })

        segments.sort(key=lambda row: (float(row.get("start_seconds") or 0), int(row.get("segment_index") or 0)))
        text = " ".join(str(row.get("text") or "").strip() for row in segments if str(row.get("text") or "").strip()).strip()
        window_transcript = {
            **transcript,
            "text": text,
            "segments": segments,
            "words": window_words,
            "window": {"start_seconds": round(start, 6), "end_seconds": round(end, 6)},
            "window_text_timing": "word_timestamps" if timing_available else ("segment_interval_fallback" if fallback_segments else "no_timed_text"),
        }
        evidence = {
            "transcript_text": text[:480],
            "word_count": len(window_words),
            "segment_count": len(segments),
            "text_timing": window_transcript["window_text_timing"],
            "segment_fallback_count": fallback_segments,
        }
        return window_transcript, segments, evidence

    @staticmethod
    def _window_tempo_from_onsets(onsets: list[float]) -> float | None:
        # One measured inter-onset interval is enough for a bounded local hypothesis.
        # Evidence strength is exposed separately; this never becomes a global tempo claim.
        if len(onsets) < 2:
            return None
        intervals = [b - a for a, b in zip(onsets, onsets[1:]) if 0.15 <= (b - a) <= 2.0]
        if not intervals:
            return None
        bpm = 60.0 / max(1e-6, float(np.median(intervals)))
        while bpm < 50.0:
            bpm *= 2.0
        while bpm > 220.0:
            bpm /= 2.0
        return round(bpm, 3)

    def _window_signature_from_reconstruction(
        self,
        reconstruction: dict[str, Any],
        *,
        start_seconds: float,
        end_seconds: float,
    ) -> dict[str, Any]:
        """Build a comparison signature from witnessed evidence inside one original-clock window."""
        start = float(start_seconds)
        end = float(end_seconds)
        if end <= start:
            raise ValueError("media_alignment_invalid_window")
        visual = reconstruction.get("visual") if isinstance(reconstruction.get("visual"), dict) else {}
        audio = reconstruction.get("audio") if isinstance(reconstruction.get("audio"), dict) else {}
        transcript = audio.get("transcript") if isinstance(audio.get("transcript"), dict) else {}

        vision = [dict(row) for row in (visual.get("semantic_anchors") or []) if self._record_overlaps_window(row, start, end)]
        window_audio = dict(audio)
        window_audio["frames"] = [
            dict(row) for row in (audio.get("frames") or [])
            if isinstance(row, dict) and row.get("time_seconds") is not None and start <= float(row.get("time_seconds") or 0) <= end
        ]
        window_audio["note_intervals"] = [
            clipped for row in (audio.get("note_intervals") or [])
            if (clipped := self._clip_interval_to_window(row, start, end)) is not None
        ]
        window_audio["chord_intervals"] = [
            clipped for row in (audio.get("chord_intervals") or [])
            if (clipped := self._clip_interval_to_window(row, start, end)) is not None
        ]
        window_audio["ml_note_events"] = [
            clipped for row in (audio.get("ml_note_events") or [])
            if (clipped := self._clip_interval_to_window(row, start, end)) is not None
        ]
        window_audio["onsets"] = [float(value) for value in (audio.get("onsets") or []) if start <= float(value) <= end]
        window_audio["duration_seconds"] = max(0.0, end - start)
        # A source-global tempo hypothesis must not make every scanned target window
        # appear musically similar. Re-estimate only when this window has enough onsets.
        window_audio["source_tempo_bpm_hypothesis"] = audio.get("tempo_bpm_hypothesis")
        window_audio["tempo_bpm_hypothesis"] = self._window_tempo_from_onsets(window_audio["onsets"])
        window_transcript, segments, transcript_evidence = self._window_transcript(
            transcript, window_audio["frames"], start=start, end=end
        )
        window_audio["transcript"] = window_transcript

        # Only derive motion/state deltas when that capability existed in the retained
        # witness. This avoids retroactively inventing evidence for legacy analyses.
        has_tracks = "entity_tracks" in visual
        has_transitions = "temporal_transitions" in visual
        tracks = self._entity_tracks(vision) if has_tracks else []
        transitions = self._temporal_transitions(vision, tracks) if has_transitions else []
        bundle = self._comparison_signatures(vision, segments, window_audio, tracks, transitions)
        bundle["evidence_coverage"] = {
            "visual_context": "observed" if "semantic_anchors" in visual else "unavailable",
            "motion": "observed" if (has_tracks or has_transitions) else "unavailable",
            "state_change": "observed" if has_transitions else "unavailable",
            "scene_change": "observed" if has_transitions else "unavailable",
            "speech_text": "observed" if "transcript" in audio else "unavailable",
            "speech_prosody": "observed" if "transcript" in audio else "unavailable",
            "music": "observed" if any(key in audio for key in ("note_intervals", "chord_intervals", "ml_note_events", "tempo_bpm_hypothesis")) else "unavailable",
        }
        bundle["coverage_semantics"] = "observed_empty_is_evidence; unavailable_is_excluded_from_similarity_denominator"
        bundle["window"] = {"start_seconds": round(start, 6), "end_seconds": round(end, 6), "duration_seconds": round(end-start, 6)}
        bundle["window_evidence"] = {
            **transcript_evidence,
            "tempo_bpm_hypothesis": window_audio.get("tempo_bpm_hypothesis"),
            "tempo_scope": "window_onset_estimate" if window_audio.get("tempo_bpm_hypothesis") is not None else "unavailable_in_window",
            "tempo_onset_count": len(window_audio.get("onsets") or []),
            "tempo_evidence_strength": (
                "none" if window_audio.get("tempo_bpm_hypothesis") is None
                else ("low" if len(window_audio.get("onsets") or []) == 2 else ("moderate" if len(window_audio.get("onsets") or []) < 5 else "strong"))
            ),
            "notes": [
                {
                    "note": row.get("note"),
                    "start_seconds": row.get("start_seconds"),
                    "end_seconds": row.get("end_seconds"),
                    "overlap_fraction": row.get("window_overlap_fraction"),
                }
                for row in (window_audio.get("note_intervals") or [])[:16]
            ],
            "chords": [
                {
                    "chord": row.get("chord"),
                    "start_seconds": row.get("start_seconds"),
                    "end_seconds": row.get("end_seconds"),
                    "overlap_fraction": row.get("window_overlap_fraction"),
                }
                for row in (window_audio.get("chord_intervals") or [])[:16]
            ],
            "ml_notes": [
                {
                    "note": row.get("note"),
                    "midi": row.get("midi"),
                    "activation": row.get("activation"),
                    "start_seconds": row.get("start_seconds"),
                    "end_seconds": row.get("end_seconds"),
                    "overlap_fraction": row.get("window_overlap_fraction"),
                    "model": ((row.get("provenance") or {}).get("model") if isinstance(row.get("provenance"), dict) else None),
                }
                for row in (window_audio.get("ml_note_events") or [])[:32]
            ],
        }
        return bundle

    @staticmethod
    def _measured_alignment_similarity(
        query_reconstruction: dict[str, Any],
        target_reconstruction: dict[str, Any],
        *,
        query_start_seconds: float,
        query_end_seconds: float,
        target_start_seconds: float,
        target_end_seconds: float,
    ) -> dict[str, Any]:
        """Compare timestamped deterministic/acoustic measurements after normalized-time mapping."""
        q_start = float(query_start_seconds)
        q_end = float(query_end_seconds)
        t_start = float(target_start_seconds)
        t_end = float(target_end_seconds)
        q_duration = q_end - q_start
        t_duration = t_end - t_start
        if q_duration <= 0 or t_duration <= 0:
            return {"score": None, "reason": "invalid_window"}

        q_visual = query_reconstruction.get("visual") if isinstance(query_reconstruction.get("visual"), dict) else {}
        t_visual = target_reconstruction.get("visual") if isinstance(target_reconstruction.get("visual"), dict) else {}
        q_audio = query_reconstruction.get("audio") if isinstance(query_reconstruction.get("audio"), dict) else {}
        t_audio = target_reconstruction.get("audio") if isinstance(target_reconstruction.get("audio"), dict) else {}

        def field_score(
            query_rows: list[dict[str, Any]],
            target_rows: list[dict[str, Any]],
            field: str,
            scale: float,
        ) -> dict[str, Any] | None:
            q_points = sorted(
                (float(row["time_seconds"]), float(row[field]))
                for row in query_rows
                if isinstance(row, dict)
                and row.get("time_seconds") is not None
                and row.get(field) is not None
                and q_start <= float(row["time_seconds"]) <= q_end
            )
            t_points = sorted(
                (float(row["time_seconds"]), float(row[field]))
                for row in target_rows
                if isinstance(row, dict) and row.get("time_seconds") is not None and row.get(field) is not None
            )
            if len(q_points) < 2 or len(t_points) < 2:
                return None

            q_times = np.asarray([item[0] for item in q_points], dtype=np.float64)
            q_values = np.asarray([item[1] for item in q_points], dtype=np.float64)
            target_times = np.asarray([item[0] for item in t_points], dtype=np.float64)
            target_values = np.asarray([item[1] for item in t_points], dtype=np.float64)
            mapped_times = t_start + ((q_times - q_start) / q_duration) * t_duration
            valid = (mapped_times >= target_times[0]) & (mapped_times <= target_times[-1])
            if int(np.count_nonzero(valid)) < 2:
                return None
            q_values = q_values[valid]
            mapped_times = mapped_times[valid]
            mapped_values = np.interp(mapped_times, target_times, target_values)

            error = np.minimum(1.0, np.abs(q_values - mapped_values) / max(float(scale), 1e-9))
            mae_similarity = float(1.0 - float(np.mean(error)))
            shape_similarity = None
            correlation = None
            if len(q_values) >= 3 and float(np.std(q_values)) > 1e-9 and float(np.std(mapped_values)) > 1e-9:
                correlation = float(np.corrcoef(q_values, mapped_values)[0, 1])
                if math.isfinite(correlation):
                    correlation = max(-1.0, min(1.0, correlation))
                    shape_similarity = (correlation + 1.0) / 2.0
            score = mae_similarity if shape_similarity is None else (0.45 * mae_similarity + 0.55 * shape_similarity)
            return {
                "score": round(max(0.0, min(1.0, score)), 6),
                "mae_similarity": round(max(0.0, min(1.0, mae_similarity)), 6),
                "shape_similarity": round(shape_similarity, 6) if shape_similarity is not None else None,
                "correlation": round(correlation, 6) if correlation is not None else None,
                "sample_pairs": int(len(q_values)),
                "field": field,
            }

        def modality(
            query_rows: list[dict[str, Any]],
            target_rows: list[dict[str, Any]],
            specs: tuple[tuple[str, float], ...],
        ) -> dict[str, Any]:
            fields: dict[str, Any] = {}
            values: list[float] = []
            for field, scale in specs:
                observed = field_score(query_rows, target_rows, field, scale)
                fields[field] = observed
                if isinstance(observed, dict) and observed.get("score") is not None:
                    values.append(float(observed["score"]))
            return {
                "score": round(sum(values) / len(values), 6) if values else None,
                "fields": fields,
                "field_count": len(values),
            }

        video = modality(
            list(q_visual.get("deterministic_samples") or []),
            list(t_visual.get("deterministic_samples") or []),
            (("mean_luma", 40.0), ("change_score", 20.0)),
        )
        audio = modality(
            list(q_audio.get("frames") or []),
            list(t_audio.get("frames") or []),
            (("rms", 0.25), ("spectral_centroid_hz", 1800.0), ("spectral_flux", 0.35)),
        )
        components: list[tuple[float, float]] = []
        if video.get("score") is not None:
            components.append((0.55, float(video["score"])))
        if audio.get("score") is not None:
            components.append((0.45, float(audio["score"])))
        denom = sum(weight for weight, _ in components)
        score = (sum(weight * value for weight, value in components) / denom) if denom else None
        return {
            "schema_version": "media_measured_temporal_alignment/v1",
            "authority": "deterministic_and_measured_signal_similarity",
            "score": round(max(0.0, min(1.0, score)), 6) if score is not None else None,
            "video": video,
            "audio": audio,
            "modalities_used": [name for name, row in (("video", video), ("audio", audio)) if row.get("score") is not None],
            "time_mapping": {
                "query_start_seconds": round(q_start, 6),
                "query_end_seconds": round(q_end, 6),
                "target_start_seconds": round(t_start, 6),
                "target_end_seconds": round(t_end, 6),
                "mapping": "normalized_relative_time_linear_interpolation",
            },
            "scoring_semantics": "field=45% normalized absolute fit + 55% temporal-shape correlation; modality=mean fields; video/audio=55/45",
        }

    @staticmethod
    def _motif_duoid(payload: Any) -> str:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = base64.urlsafe_b64encode(hashlib.shake_256(encoded).digest(64)).decode("ascii").rstrip("=")
        return "duoid:shake256-512:" + digest

    @staticmethod
    def _motif_overlap_ratio(a: dict[str, Any], b: dict[str, Any]) -> float:
        left = max(float(a.get("start_seconds") or 0), float(b.get("start_seconds") or 0))
        right = min(float(a.get("end_seconds") or 0), float(b.get("end_seconds") or 0))
        inter = max(0.0, right - left)
        denom = max(
            1e-9,
            min(
                max(0.0, float(a.get("end_seconds") or 0) - float(a.get("start_seconds") or 0)),
                max(0.0, float(b.get("end_seconds") or 0) - float(b.get("start_seconds") or 0)),
            ),
        )
        return inter / denom

    def _motif_candidate_ranges(
        self,
        reconstruction: dict[str, Any],
        *,
        max_candidates: int = 480,
    ) -> list[dict[str, float]]:
        """Generate bounded, multi-scale candidate windows around witnessed events and uniform clock positions."""
        ar = reconstruction.get("analysis_range") if isinstance(reconstruction.get("analysis_range"), dict) else {}
        start = float(ar.get("start_seconds") or 0)
        end = float(ar.get("end_seconds") or start)
        if end <= start:
            clock = reconstruction.get("source_clock") if isinstance(reconstruction.get("source_clock"), dict) else {}
            end = float(clock.get("duration_seconds") or start)
        total = end - start
        if total < 0.05:
            return []

        visual = reconstruction.get("visual") if isinstance(reconstruction.get("visual"), dict) else {}
        audio = reconstruction.get("audio") if isinstance(reconstruction.get("audio"), dict) else {}
        transcript = audio.get("transcript") if isinstance(audio.get("transcript"), dict) else {}

        event_times: set[float] = {start, end}
        for row in visual.get("semantic_anchors") or []:
            if isinstance(row, dict) and row.get("time_seconds") is not None:
                event_times.add(float(row.get("time_seconds") or 0))
        for row in visual.get("temporal_transitions") or []:
            if not isinstance(row, dict):
                continue
            for key in ("time_seconds", "start_seconds", "end_seconds"):
                if row.get(key) is not None:
                    event_times.add(float(row.get(key) or 0))
            for key in ("from_time_range", "to_time_range", "time_range"):
                value = row.get(key)
                if isinstance(value, dict):
                    for time_key in ("start_seconds", "end_seconds"):
                        if value.get(time_key) is not None:
                            event_times.add(float(value.get(time_key) or 0))
        for row in (transcript.get("words") or []) + (transcript.get("segments") or []):
            if not isinstance(row, dict):
                continue
            for key in ("start_seconds", "end_seconds"):
                if row.get(key) is not None:
                    event_times.add(float(row.get(key) or 0))
        for value in audio.get("onsets") or []:
            try:
                event_times.add(float(value))
            except Exception:
                pass
        for key in ("note_intervals", "chord_intervals", "ml_note_events"):
            for row in audio.get(key) or []:
                if not isinstance(row, dict):
                    continue
                for time_key in ("start_seconds", "end_seconds"):
                    if row.get(time_key) is not None:
                        event_times.add(float(row.get(time_key) or 0))

        # Large deterministic streams can still contribute their strongest change boundaries.
        deterministic = [row for row in (visual.get("deterministic_samples") or []) if isinstance(row, dict)]
        strongest = sorted(
            deterministic,
            key=lambda row: float(row.get("change_score") or 0),
            reverse=True,
        )[:48]
        for row in strongest:
            if row.get("time_seconds") is not None:
                event_times.add(float(row.get("time_seconds") or 0))

        event_times = {value for value in event_times if start - 1e-6 <= value <= end + 1e-6 and math.isfinite(value)}
        ordered_events = sorted(event_times)
        if len(ordered_events) > 128:
            indices = np.linspace(0, len(ordered_events) - 1, 128).round().astype(int)
            ordered_events = [ordered_events[int(i)] for i in sorted(set(indices.tolist()))]

        durations: set[float] = set()
        for value in (0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0):
            if value <= total + 1e-6:
                durations.add(value)
        anchor_times = sorted(
            float(row.get("time_seconds") or 0)
            for row in (visual.get("semantic_anchors") or [])
            if isinstance(row, dict) and row.get("time_seconds") is not None
        )
        gaps = [b - a for a, b in zip(anchor_times, anchor_times[1:]) if b - a >= 0.05]
        if gaps:
            base = float(np.median(gaps))
            for factor in (1.0, 2.0, 4.0):
                value = round(base * factor, 3)
                if 0.25 <= value <= min(32.0, total):
                    durations.add(value)
        segment_durations = [
            float(row.get("end_seconds") or 0) - float(row.get("start_seconds") or 0)
            for row in transcript.get("segments") or []
            if isinstance(row, dict) and row.get("start_seconds") is not None and row.get("end_seconds") is not None
        ]
        segment_durations = [value for value in segment_durations if 0.25 <= value <= min(16.0, total)]
        if segment_durations:
            durations.add(round(float(np.median(segment_durations)), 3))
        if not durations:
            durations.add(round(total, 3))
        elif total < 1.0:
            durations.add(round(total, 3))

        ordered_durations = sorted(value for value in durations if value >= 0.05 and value <= total + 1e-6)
        per_scale_cap = max(16, int(max_candidates // max(1, len(ordered_durations))))
        ranges: list[dict[str, float]] = []
        for duration in ordered_durations:
            duration = min(duration, total)
            latest = end - duration
            starts: set[float] = {start, latest}
            stride = max(0.25, duration / 2.0)
            cursor = start
            while cursor <= latest + 1e-9 and len(starts) < per_scale_cap * 2:
                starts.add(cursor)
                cursor += stride
            for event_time in ordered_events:
                for candidate in (event_time, event_time - duration / 2.0, event_time - duration):
                    starts.add(max(start, min(latest, candidate)))
            ordered_starts = sorted(round(value, 4) for value in starts if start - 1e-6 <= value <= latest + 1e-6)
            if len(ordered_starts) > per_scale_cap:
                indices = np.linspace(0, len(ordered_starts) - 1, per_scale_cap).round().astype(int)
                ordered_starts = [ordered_starts[int(i)] for i in sorted(set(indices.tolist()))]
            for candidate_start in ordered_starts:
                candidate_end = min(end, candidate_start + duration)
                if candidate_end - candidate_start < 0.05:
                    continue
                ranges.append({
                    "start_seconds": round(candidate_start, 6),
                    "end_seconds": round(candidate_end, 6),
                    "duration_seconds": round(candidate_end - candidate_start, 6),
                })
        ranges.sort(key=lambda row: (float(row["duration_seconds"]), float(row["start_seconds"])))
        return ranges[: max(1, int(max_candidates))]

    def _motif_measured_sketch(
        self,
        reconstruction: dict[str, Any],
        start: float,
        end: float,
    ) -> dict[str, Any]:
        visual = reconstruction.get("visual") if isinstance(reconstruction.get("visual"), dict) else {}
        audio = reconstruction.get("audio") if isinstance(reconstruction.get("audio"), dict) else {}

        def rows_between(rows: list[Any]) -> list[dict[str, Any]]:
            return [row for row in rows if isinstance(row, dict) and row.get("time_seconds") is not None and start <= float(row.get("time_seconds") or 0) <= end]

        def interval_rows(rows: list[Any]) -> list[dict[str, Any]]:
            out=[]
            for row in rows:
                if not isinstance(row,dict): continue
                rs=float(row.get("start_seconds") if row.get("start_seconds") is not None else row.get("time_seconds") or 0)
                re_=float(row.get("end_seconds") if row.get("end_seconds") is not None else row.get("time_seconds") or rs)
                if re_ >= start and rs <= end: out.append(row)
            return out

        vrows = rows_between(list(visual.get("deterministic_samples") or []))
        erows = rows_between(list(visual.get("perceptual_embeddings") or []))
        arows = rows_between(list(audio.get("frames") or []))
        aerows = interval_rows(list(audio.get("perceptual_embeddings") or []))

        def stats(rows: list[dict[str, Any]], field: str) -> dict[str, float] | None:
            values = [float(row[field]) for row in rows if row.get(field) is not None and math.isfinite(float(row[field]))]
            if not values: return None
            return {"mean":round(float(np.mean(values)),6),"stddev":round(float(np.std(values)),6),"minimum":round(float(min(values)),6),"maximum":round(float(max(values)),6)}

        onsets=[float(v) for v in (audio.get("onsets") or []) if start <= float(v) <= end]
        out:dict[str,Any]={"duration_seconds":round(max(0.0,end-start),6),"visual_sample_count":len(vrows),"audio_frame_count":len(arows),"onset_count":len(onsets),"onset_rate_hz":round(len(onsets)/max(0.05,end-start),6)}
        for key in ("mean_luma","change_score","global_shift_magnitude_normalized"):
            value=stats(vrows,key)
            if value is not None: out["visual_"+key]=value
        for key in ("rms","spectral_centroid_hz","spectral_flux","pitch_hz"):
            value=stats(arows,key)
            if value is not None: out["audio_"+key]=value

        def centroid(rows:list[dict[str,Any]], *, identity_semantics:str) -> tuple[list[float]|None,str|None,int|None]:
            vectors=[]; model=None; dims=None
            for row in rows:
                raw=row.get("embedding")
                if not isinstance(raw,list) or not raw: continue
                vec=np.asarray(raw,dtype=np.float32)
                if vec.ndim!=1 or not np.all(np.isfinite(vec)): continue
                if dims is None: dims=int(vec.size)
                if int(vec.size)!=dims: continue
                norm=float(np.linalg.norm(vec))
                if norm<=1e-12: continue
                vectors.append(vec/norm); model=model or row.get("model")
            if not vectors: return None,None,None
            c=np.mean(np.stack(vectors,axis=0),axis=0); n=float(np.linalg.norm(c))
            if n<=1e-12: return None,None,None
            c=c/n
            return [round(float(v),8) for v in c.tolist()],model,int(c.size)

        vc,vm,vd=centroid(erows,identity_semantics="not_person_identity_evidence")
        if vc is not None:
            out.update({"visual_embedding_count":len(erows),"visual_embedding_model":vm,"visual_embedding_dimensions":vd,"visual_embedding_centroid":vc,"visual_embedding_authority":"perceptual_embedding_similarity_evidence_only","visual_embedding_identity_semantics":"not_person_identity_evidence"})
        ac,am,ad=centroid(aerows,identity_semantics="not_speaker_identity_evidence")
        if ac is not None:
            out.update({"audio_embedding_count":len(aerows),"audio_embedding_model":am,"audio_embedding_dimensions":ad,"audio_embedding_centroid":ac,"audio_embedding_authority":"perceptual_audio_embedding_similarity_evidence_only","audio_embedding_identity_semantics":"not_speaker_identity_evidence; audio content/timbre/structure similarity only"})
        return out

    def _motif_descriptor(
        self,
        reconstruction: dict[str, Any],
        start: float,
        end: float,
    ) -> dict[str, Any]:
        bundle = self._window_signature_from_reconstruction(
            reconstruction,
            start_seconds=start,
            end_seconds=end,
        )
        families = bundle.get("families") if isinstance(bundle.get("families"), dict) else {}
        active_families = sorted(key for key, values in families.items() if values)
        family_counts = {key: len(values or []) for key, values in families.items()}
        token_count = sum(family_counts.values())
        evidence = bundle.get("window_evidence") if isinstance(bundle.get("window_evidence"), dict) else {}
        visual = reconstruction.get("visual") if isinstance(reconstruction.get("visual"), dict) else {}
        transition_count = sum(
            1 for row in (visual.get("temporal_transitions") or [])
            if self._record_overlaps_window(row, start, end)
        )
        event_count = (
            int(evidence.get("word_count") or 0)
            + len(evidence.get("notes") or [])
            + len(evidence.get("chords") or [])
            + transition_count
        )
        family_diversity = min(1.0, len(active_families) / 4.0)
        semantic_richness = min(1.0, token_count / 24.0)
        event_density = min(1.0, event_count / max(2.0, (end - start) * 4.0))
        salience = 0.35 * family_diversity + 0.35 * semantic_richness + 0.30 * event_density
        return {
            "start_seconds": round(start, 6),
            "end_seconds": round(end, 6),
            "duration_seconds": round(max(0.0, end - start), 6),
            "signature_bundle": bundle,
            "signature": bundle.get("signature"),
            "active_families": active_families,
            "family_counts": family_counts,
            "window_evidence": evidence,
            "measured_sketch": self._motif_measured_sketch(reconstruction, start, end),
            "salience": round(max(0.0, min(1.0, salience)), 6),
            "transition_count": transition_count,
        }

    def _motif_pair_similarity(
        self,
        reconstruction: dict[str, Any],
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any]:
        semantic=self._compare_signature_bundles(left.get("signature_bundle") or {},right.get("signature_bundle") or {})
        semantic_score=float(semantic.get("overall_similarity") or 0.0)
        measured=self._measured_alignment_similarity(reconstruction,reconstruction,query_start_seconds=float(left.get("start_seconds") or 0),query_end_seconds=float(left.get("end_seconds") or 0),target_start_seconds=float(right.get("start_seconds") or 0),target_end_seconds=float(right.get("end_seconds") or 0))
        measured_score=measured.get("score")
        perceptual=self._motif_sketch_similarity(left.get("measured_sketch") if isinstance(left.get("measured_sketch"),dict) else {},right.get("measured_sketch") if isinstance(right.get("measured_sketch"),dict) else {})
        visual=perceptual.get("visual_embedding_cosine"); audio=perceptual.get("audio_embedding_cosine")
        available=[("visual_embedding",visual),("audio_embedding",audio)]; available=[x for x in available if x[1] is not None]
        if measured_score is not None and len(available)==2:
            overall=.20*semantic_score+.50*float(measured_score)+.15*float(visual)+.15*float(audio); weights={"semantic":.20,"measured":.50,"visual_embedding":.15,"audio_embedding":.15}
        elif measured_score is not None and len(available)==1:
            k,v=available[0]; overall=.25*semantic_score+.50*float(measured_score)+.25*float(v); weights={"semantic":.25,"measured":.50,"visual_embedding":.25 if k=="visual_embedding" else 0.0,"audio_embedding":.25 if k=="audio_embedding" else 0.0}
        elif measured_score is not None:
            overall=.35*semantic_score+.65*float(measured_score); weights={"semantic":.35,"measured":.65,"visual_embedding":0.0,"audio_embedding":0.0}
        elif len(available)==2:
            overall=.40*semantic_score+.30*float(visual)+.30*float(audio); weights={"semantic":.40,"measured":0.0,"visual_embedding":.30,"audio_embedding":.30}
        elif len(available)==1:
            k,v=available[0]; overall=.45*semantic_score+.55*float(v); weights={"semantic":.45,"measured":0.0,"visual_embedding":.55 if k=="visual_embedding" else 0.0,"audio_embedding":.55 if k=="audio_embedding" else 0.0}
        else:
            overall=semantic_score; weights={"semantic":1.0,"measured":0.0,"visual_embedding":0.0,"audio_embedding":0.0}
        return {"overall":round(max(0.0,min(1.0,overall)),6),"semantic":round(semantic_score,6),"measured":round(float(measured_score),6) if measured_score is not None else None,"visual_embedding":round(float(visual),6) if visual is not None else None,"audio_embedding":round(float(audio),6) if audio is not None else None,"weights":weights,"semantic_components":{"token_jaccard":semantic.get("token_jaccard"),"family_weighted_similarity":semantic.get("family_weighted_similarity"),"sequence_similarity":semantic.get("sequence_similarity"),"comparison_coverage":semantic.get("comparison_coverage")},"measured_components":measured,"perceptual_components":perceptual}

    @staticmethod
    def _motif_label(prototype: dict[str, Any], representative: dict[str, Any], index: int) -> str:
        families = prototype.get("families") if isinstance(prototype.get("families"), dict) else {}
        evidence = representative.get("window_evidence") if isinstance(representative.get("window_evidence"), dict) else {}
        parts: list[str] = []
        transcript = re.sub(r"\s+", " ", str(evidence.get("transcript_text") or "").strip())
        if transcript and families.get("speech_text"):
            parts.append('vocal "' + transcript[:72] + ('…' if len(transcript) > 72 else '') + '"')
        chords = [str(row.get("chord") or "") for row in (evidence.get("chords") or []) if isinstance(row, dict) and row.get("chord")]
        notes = [str(row.get("note") or "") for row in (evidence.get("notes") or []) if isinstance(row, dict) and row.get("note")]
        ml_notes = [str(row.get("note") or "") for row in (evidence.get("ml_notes") or []) if isinstance(row, dict) and row.get("note")]
        if chords and families.get("music"):
            parts.append("chords " + " → ".join(chords[:5]))
        elif ml_notes and families.get("music"):
            parts.append("ML notes " + " → ".join(ml_notes[:6]))
        elif notes and families.get("music"):
            parts.append("notes " + " → ".join(notes[:6]))
        preferred_prefixes = (
            "overall_action=", "setting=", "person:action:", "person:pose:",
            "camera_motion=", "camera_shot=", "person:net=", "object:net=",
        )
        flattened = [token for values in families.values() for token in (values or [])]
        for prefix in preferred_prefixes:
            hit = next((token for token in flattened if str(token).startswith(prefix)), None)
            if hit:
                value = str(hit).split("=", 1)[-1].split(":", 2)[-1].replace(">", " → ")
                if value and value not in parts:
                    parts.append(value[:80])
                    if len(parts) >= 3:
                        break
        if not parts:
            parts.append("measured audiovisual pattern")
        modalities: set[str] = set()
        for family, values in families.items():
            if not values:
                continue
            if family in ("speech_text", "speech_prosody"):
                modalities.add("vocal")
            elif family == "music":
                modalities.add("audio")
            else:
                modalities.add("visual")
        prefix = "Multimodal" if len(modalities) >= 2 else (
            "Music" if modalities == {"audio"} else
            "Vocal" if modalities == {"vocal"} else
            "Visual" if modalities == {"visual"} else
            "Motif"
        )
        return (prefix + " · " + " · ".join(parts))[:220]

    def _motif_family_similarity(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        lproto = left.get("prototype") if isinstance(left.get("prototype"), dict) else {}
        rproto = right.get("prototype") if isinstance(right.get("prototype"), dict) else {}
        return self._motif_prototype_similarity(lproto, rproto)

    def _motif_temporal_support_overlap(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        lrows = [row for row in (left.get("occurrences") or []) if isinstance(row, dict)]
        rrows = [row for row in (right.get("occurrences") or []) if isinstance(row, dict)]
        if not lrows or not rrows:
            return {"ratio": 0.0, "matched_occurrences": 0, "denominator": min(len(lrows), len(rrows))}
        smaller, larger = (lrows, rrows) if len(lrows) <= len(rrows) else (rrows, lrows)
        matched = 0
        best_overlaps: list[float] = []
        for row in smaller:
            best = max((self._motif_overlap_ratio(row, other) for other in larger), default=0.0)
            best_overlaps.append(best)
            if best >= 0.35:
                matched += 1
        ratio = matched / max(1, len(smaller))
        return {
            "ratio": round(ratio, 6),
            "matched_occurrences": matched,
            "denominator": len(smaller),
            "mean_best_overlap": round(float(np.mean(best_overlaps)), 6) if best_overlaps else 0.0,
        }

    def _consolidate_motif_families(self, motifs: list[dict[str, Any]], *, max_motifs: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Collapse phase-shifted motif variants while preserving raw variants as provenance."""
        ordered = sorted(
            motifs,
            key=lambda row: (
                -float(row.get("recurrence_score") or 0),
                -int(row.get("occurrence_count") or 0),
                float(row.get("duration_seconds") or 0),
                str(row.get("motif_id") or ""),
            ),
        )
        families: list[dict[str, Any]] = []
        suppressions: list[dict[str, Any]] = []
        for motif in ordered:
            duration = max(0.001, float(motif.get("duration_seconds") or 0))
            best_family = None
            best_rank = None
            best_evidence = None
            for family in families:
                canonical = family["canonical"]
                cduration = max(0.001, float(canonical.get("duration_seconds") or 0))
                duration_ratio = max(duration, cduration) / min(duration, cduration)
                if duration_ratio > 1.34:
                    continue
                temporal = self._motif_temporal_support_overlap(canonical, motif)
                if float(temporal.get("ratio") or 0) < 0.50:
                    continue
                similarity = self._motif_family_similarity(canonical, motif)
                semantic = float(similarity.get("semantic_similarity") or 0)
                overall = float(similarity.get("overall_similarity") or 0)
                if overall < 0.72 or semantic < 0.52:
                    continue
                rank = overall * 0.65 + float(temporal.get("ratio") or 0) * 0.35
                if best_rank is None or rank > best_rank:
                    best_family = family
                    best_rank = rank
                    best_evidence = {
                        "duration_ratio": round(duration_ratio, 6),
                        "prototype_similarity": similarity,
                        "temporal_support_overlap": temporal,
                        "family_match_score": round(rank, 6),
                    }
            if best_family is None:
                families.append({"canonical": motif, "members": [motif], "merge_evidence": []})
            else:
                best_family["members"].append(motif)
                best_family["merge_evidence"].append({
                    "suppressed_motif_id": motif.get("motif_id"),
                    **(best_evidence or {}),
                })
                suppressions.append({
                    "canonical_motif_id": best_family["canonical"].get("motif_id"),
                    "suppressed_motif_id": motif.get("motif_id"),
                    **(best_evidence or {}),
                })

        consolidated: list[dict[str, Any]] = []
        for family in families:
            canonical = dict(family["canonical"])
            members = family["members"]
            all_occurrences: list[dict[str, Any]] = []
            for member in members:
                member_score = float(member.get("recurrence_score") or 0)
                for occurrence in member.get("occurrences") or []:
                    if not isinstance(occurrence, dict):
                        continue
                    row = dict(occurrence)
                    row["_family_source_motif_id"] = member.get("motif_id")
                    row["_family_source_score"] = member_score
                    all_occurrences.append(row)
            all_occurrences.sort(key=lambda row: (
                -float(row.get("_family_source_score") or 0),
                -float(row.get("similarity_to_representative") or 0),
                -float(row.get("salience") or 0),
                float(row.get("start_seconds") or 0),
            ))
            selected: list[dict[str, Any]] = []
            suppressed_occurrences: list[dict[str, Any]] = []
            for row in all_occurrences:
                overlap = max((self._motif_overlap_ratio(row, prior) for prior in selected), default=0.0)
                cleaned = {key: value for key, value in row.items() if not key.startswith("_family_")}
                if overlap >= 0.35:
                    suppressed_occurrences.append({
                        "start_seconds": cleaned.get("start_seconds"),
                        "end_seconds": cleaned.get("end_seconds"),
                        "source_motif_id": row.get("_family_source_motif_id"),
                        "max_overlap_with_kept": round(overlap, 6),
                    })
                    continue
                cleaned["family_source_motif_id"] = row.get("_family_source_motif_id")
                selected.append(cleaned)
            selected.sort(key=lambda row: float(row.get("start_seconds") or 0))

            member_ids = [str(row.get("motif_id") or "") for row in members]
            canonical["occurrences"] = selected
            canonical["occurrence_count"] = len(selected)
            if selected:
                rep0 = canonical.get("representative_occurrence") if isinstance(canonical.get("representative_occurrence"), dict) else {}
                rep_start = float(rep0.get("start_seconds") or selected[0].get("start_seconds") or 0)
                representative = min(selected, key=lambda row: abs(float(row.get("start_seconds") or 0) - rep_start))
                canonical["representative_occurrence"] = {
                    "start_seconds": representative.get("start_seconds"),
                    "end_seconds": representative.get("end_seconds"),
                    "duration_seconds": representative.get("duration_seconds"),
                    "signature": rep0.get("signature"),
                }
                starts = [float(row.get("start_seconds") or 0) for row in selected]
                intervals = [b - a for a, b in zip(starts, starts[1:])]
                periodicity = dict(canonical.get("periodicity") or {})
                periodicity["interval_count"] = len(intervals)
                if intervals:
                    periodicity["mean_interval_seconds"] = round(float(np.mean(intervals)), 6)
                    periodicity["median_interval_seconds"] = round(float(np.median(intervals)), 6)
                    periodicity["stddev_interval_seconds"] = round(float(np.std(intervals)), 6)
                if len(intervals) >= 2:
                    mean_interval = max(1e-9, float(np.mean(intervals)))
                    cv = float(np.std(intervals)) / mean_interval
                    periodicity["coefficient_of_variation"] = round(cv, 6)
                    periodicity["classification"] = "periodic" if cv <= 0.15 else ("quasi_periodic" if cv <= 0.35 else "irregular")
                elif len(intervals) < 2:
                    periodicity["classification"] = "insufficient_occurrences"
                canonical["periodicity"] = periodicity
                canonical["span"] = {
                    "first_start_seconds": round(min(starts), 6),
                    "last_start_seconds": round(max(starts), 6),
                    "span_seconds": round(max(starts) - min(starts), 6),
                }

            raw_occurrence_count = sum(int(row.get("occurrence_count") or 0) for row in members)
            canonical["family_consolidation"] = {
                "schema_version": "media_motif_family_consolidation/v1",
                "canonical_motif_id": canonical.get("motif_id"),
                "member_motif_ids": member_ids,
                "raw_variant_count": len(members),
                "suppressed_variant_count": max(0, len(members) - 1),
                "raw_occurrence_count": raw_occurrence_count,
                "consolidated_occurrence_count": len(selected),
                "suppressed_occurrence_count": len(suppressed_occurrences),
                "phase_variant_policy": "same_scale_or_near_scale + prototype_similarity + temporal-support-overlap; occurrence NMS overlap>=0.35",
                "merge_evidence": family["merge_evidence"][:64],
                "suppressed_occurrences": suppressed_occurrences[:128],
            }
            canonical["status"] = (
                "strong_recurrence"
                if len(selected) >= 3 and float(canonical.get("recurrence_score") or 0) >= 0.72
                else "recurrent"
            )
            consolidated.append(canonical)

        consolidated.sort(key=lambda row: (
            -float(row.get("recurrence_score") or 0),
            -int(row.get("occurrence_count") or 0),
            float(row.get("duration_seconds") or 0),
        ))
        return consolidated[: max(1, int(max_motifs))], suppressions

    def _motif_catalog(
        self,
        reconstruction: dict[str, Any],
        *,
        max_candidates: int = 480,
        max_motifs: int = 128,
        min_similarity: float = 0.72,
    ) -> dict[str, Any]:
        """Extract recurrent and salient multi-scale motifs from one retained reconstruction."""
        ranges = self._motif_candidate_ranges(reconstruction, max_candidates=max_candidates)
        descriptors = [
            self._motif_descriptor(
                reconstruction,
                float(row["start_seconds"]),
                float(row["end_seconds"]),
            )
            for row in ranges
        ]
        duration_groups: dict[float, list[dict[str, Any]]] = {}
        for descriptor in descriptors:
            duration_groups.setdefault(round(float(descriptor["duration_seconds"]), 3), []).append(descriptor)

        clusters: list[dict[str, Any]] = []
        for duration, rows in sorted(duration_groups.items()):
            rows.sort(key=lambda row: (-float(row.get("salience") or 0), float(row.get("start_seconds") or 0)))
            local_clusters: list[dict[str, Any]] = []
            for descriptor in rows:
                best_cluster = None
                best_similarity = None
                for cluster in local_clusters:
                    if any(self._motif_overlap_ratio(descriptor, prior) >= 0.35 for prior in cluster["descriptors"]):
                        continue
                    similarity = self._motif_pair_similarity(reconstruction, cluster["representative"], descriptor)
                    measured = similarity.get("measured")
                    semantic = float(similarity.get("semantic") or 0)
                    overall = float(similarity.get("overall") or 0)
                    eligible = overall >= min_similarity and (
                        semantic >= 0.18 or (measured is not None and float(measured) >= 0.90)
                    )
                    if eligible and (best_similarity is None or overall > float(best_similarity.get("overall") or 0)):
                        best_cluster = cluster
                        best_similarity = similarity
                if best_cluster is None:
                    local_clusters.append({
                        "duration_seconds": duration,
                        "representative": descriptor,
                        "descriptors": [descriptor],
                    })
                else:
                    best_cluster["descriptors"].append(descriptor)
            clusters.extend(local_clusters)

        motifs: list[dict[str, Any]] = []
        motif_relations: list[dict[str, Any]] = []
        clustered_descriptor_ids: set[tuple[float, float]] = set()
        for cluster in clusters:
            rows = sorted(cluster["descriptors"], key=lambda row: float(row.get("start_seconds") or 0))
            if len(rows) < 2:
                continue

            # Pick a bounded medoid: the occurrence with the strongest average pairwise support.
            medoid_pool = rows[:20]
            medoid_scores: list[tuple[float, dict[str, Any]]] = []
            for candidate in medoid_pool:
                pair_scores: list[float] = []
                for other in medoid_pool:
                    if candidate is other:
                        continue
                    pair_scores.append(float(self._motif_pair_similarity(reconstruction, candidate, other).get("overall") or 0))
                medoid_scores.append((float(np.mean(pair_scores)) if pair_scores else 1.0, candidate))
            medoid_scores.sort(key=lambda item: (-item[0], float(item[1].get("start_seconds") or 0)))
            representative = medoid_scores[0][1]

            family_frequency: dict[str, dict[str, int]] = {}
            for row in rows:
                bundle = row.get("signature_bundle") if isinstance(row.get("signature_bundle"), dict) else {}
                for family, tokens in (bundle.get("families") or {}).items():
                    bucket = family_frequency.setdefault(family, {})
                    for token in set(tokens or []):
                        bucket[str(token)] = bucket.get(str(token), 0) + 1
            threshold = max(2, int(math.ceil(len(rows) * 0.60)))
            prototype_families: dict[str, list[str]] = {}
            for family in ("visual_context", "motion", "state_change", "scene_change", "speech_text", "speech_prosody", "music"):
                common = sorted(token for token, count in family_frequency.get(family, {}).items() if count >= threshold)
                if not common:
                    representative_bundle = representative.get("signature_bundle") or {}
                    representative_tokens = list((representative_bundle.get("families") or {}).get(family) or [])
                    if len(rows) == 2:
                        common = representative_tokens[:16]
                prototype_families[family] = common[:48]

            rep_bundle = representative.get("signature_bundle") if isinstance(representative.get("signature_bundle"), dict) else {}
            sequence_sketches = dict(rep_bundle.get("sequence_sketches") or {})
            prototype_canonical = {
                "schema_version": COMPARISON_SCHEMA,
                "families": prototype_families,
                "sequence_sketches": sequence_sketches,
                "measured_sketch": representative.get("measured_sketch"),
                "duration_seconds": round(float(cluster["duration_seconds"]), 3),
            }
            prototype_signature = self._motif_duoid(prototype_canonical)
            prototype_tokens = sorted({token for values in prototype_families.values() for token in values})
            prototype_bundle = {
                "schema_version": COMPARISON_SCHEMA,
                "signature": prototype_signature,
                "authority": "recurrent_window_prototype_for_similarity_only",
                "identity_semantics": "not_person_identity_evidence; ephemeral track ids excluded",
                "tokens": prototype_tokens,
                "token_count": len(prototype_tokens),
                "families": prototype_families,
                "sequence_sketches": sequence_sketches,
                "feature_counts": {family: len(tokens) for family, tokens in prototype_families.items()},
                "evidence_coverage": dict(rep_bundle.get("evidence_coverage") or {}),
                "measured_sketch": representative.get("measured_sketch"),
            }

            occurrences: list[dict[str, Any]] = []
            similarities: list[float] = []
            for row in rows:
                sim = self._motif_pair_similarity(reconstruction, representative, row)
                score = float(sim.get("overall") or 0)
                similarities.append(score)
                start = float(row.get("start_seconds") or 0)
                end = float(row.get("end_seconds") or start)
                occurrence = {
                    "schema_version": MOTIF_OCCURRENCE_SCHEMA,
                    "start_seconds": round(start, 6),
                    "end_seconds": round(end, 6),
                    "duration_seconds": round(max(0.0, end - start), 6),
                    "similarity_to_representative": round(score, 6),
                    "semantic_similarity": sim.get("semantic"),
                    "measured_similarity": sim.get("measured"),
                    "salience": row.get("salience"),
                    "active_families": row.get("active_families"),
                    "family_counts": row.get("family_counts"),
                    "window_evidence": row.get("window_evidence"),
                    "measured_sketch": row.get("measured_sketch"),
                    "source_time_semantics": "absolute_source_clock",
                    "authority": "witnessed_window_recurrence_candidate",
                }
                clock = reconstruction.get("source_clock") if isinstance(reconstruction.get("source_clock"), dict) else {}
                fps = float(clock.get("source_fps") or 0)
                if fps > 0:
                    occurrence["start_frame"] = int(round(start * fps))
                    occurrence["end_frame"] = int(round(end * fps))
                occurrences.append(occurrence)
                clustered_descriptor_ids.add((round(start, 6), round(end, 6)))

            occurrence_starts = [float(row["start_seconds"]) for row in occurrences]
            intervals = [b - a for a, b in zip(occurrence_starts, occurrence_starts[1:])]
            periodicity: dict[str, Any] = {
                "interval_count": len(intervals),
                "classification": "insufficient_occurrences" if len(intervals) < 2 else "irregular",
            }
            if intervals:
                periodicity.update({
                    "mean_interval_seconds": round(float(np.mean(intervals)), 6),
                    "median_interval_seconds": round(float(np.median(intervals)), 6),
                    "stddev_interval_seconds": round(float(np.std(intervals)), 6),
                })
            if len(intervals) >= 2:
                mean_interval = max(1e-9, float(np.mean(intervals)))
                cv = float(np.std(intervals)) / mean_interval
                periodicity["coefficient_of_variation"] = round(cv, 6)
                periodicity["classification"] = "periodic" if cv <= 0.15 else ("quasi_periodic" if cv <= 0.35 else "irregular")

            active_families = sorted(family for family, tokens in prototype_families.items() if tokens)
            modalities: set[str] = set()
            for family in active_families:
                if family in ("speech_text", "speech_prosody"):
                    modalities.add("vocal")
                elif family == "music":
                    modalities.add("audio")
                else:
                    modalities.add("visual")
            mean_similarity = float(np.mean(similarities)) if similarities else 0.0
            mean_salience = float(np.mean([float(row.get("salience") or 0) for row in rows]))
            recurrence_factor = min(1.0, 0.5 + 0.15 * max(0, len(rows) - 2))
            multimodal_factor = min(1.0, len(modalities) / 3.0)
            score = (
                0.45 * mean_similarity
                + 0.20 * mean_salience
                + 0.20 * recurrence_factor
                + 0.15 * multimodal_factor
            )
            motif_kind = (
                "cross_modal" if len(modalities) >= 2 else
                "musical_phrase" if modalities == {"audio"} else
                "vocal_phrase" if modalities == {"vocal"} else
                "visual_motion_pattern" if "motion" in active_families else
                "visual_scene_pattern"
            )
            motif_identity = {
                "prototype_signature": prototype_signature,
                "duration_seconds": round(float(cluster["duration_seconds"]), 3),
                "occurrence_starts": [round(value, 3) for value in occurrence_starts],
            }
            motif_id = "motif-" + hashlib.shake_256(
                json.dumps(motif_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest(12)
            motif = {
                "schema_version": MOTIF_SCHEMA,
                "motif_id": motif_id,
                "label": self._motif_label(prototype_bundle, representative, len(motifs) + 1),
                "motif_kind": motif_kind,
                "status": "strong_recurrence" if len(rows) >= 3 and score >= 0.72 else "recurrent",
                "authority": "heuristic_recurrence_over_witnessed_and_measured_media_evidence",
                "identity_semantics": "not_person_identity_evidence; content/structure recurrence only",
                "duration_seconds": round(float(cluster["duration_seconds"]), 6),
                "occurrence_count": len(occurrences),
                "occurrences": occurrences,
                "representative_occurrence": {
                    "start_seconds": representative.get("start_seconds"),
                    "end_seconds": representative.get("end_seconds"),
                    "duration_seconds": representative.get("duration_seconds"),
                    "signature": representative.get("signature"),
                },
                "prototype": prototype_bundle,
                "active_families": active_families,
                "modalities": sorted(modalities),
                "cross_modal": len(modalities) >= 2,
                "mean_similarity": round(mean_similarity, 6),
                "mean_salience": round(mean_salience, 6),
                "recurrence_score": round(max(0.0, min(1.0, score)), 6),
                "periodicity": periodicity,
                "span": {
                    "first_start_seconds": round(min(occurrence_starts), 6),
                    "last_start_seconds": round(max(occurrence_starts), 6),
                    "span_seconds": round(max(occurrence_starts) - min(occurrence_starts), 6),
                },
            }
            motifs.append(motif)

        raw_motif_count = len(motifs)
        motifs, motif_family_suppressions = self._consolidate_motif_families(motifs, max_motifs=max_motifs)

        # Build direct recurrence and hierarchy relationships.
        for motif in motifs:
            occurrences = motif.get("occurrences") or []
            for left, right in zip(occurrences, occurrences[1:]):
                motif_relations.append({
                    "schema_version": MOTIF_SCHEMA,
                    "relation_type": "motif_recurrence",
                    "motif_id": motif.get("motif_id"),
                    "from_time_range": {"start_seconds": left.get("start_seconds"), "end_seconds": left.get("end_seconds")},
                    "to_time_range": {"start_seconds": right.get("start_seconds"), "end_seconds": right.get("end_seconds")},
                    "temporal_distance_seconds": round(float(right.get("start_seconds") or 0) - float(left.get("start_seconds") or 0), 6),
                    "authority": "recurrent_window_relationship_evidence",
                })
        for larger in motifs:
            for smaller in motifs:
                if larger is smaller or float(larger.get("duration_seconds") or 0) < 1.5 * float(smaller.get("duration_seconds") or 0):
                    continue
                contained = 0
                for small_occ in smaller.get("occurrences") or []:
                    if any(
                        float(big_occ.get("start_seconds") or 0) <= float(small_occ.get("start_seconds") or 0) + 1e-6
                        and float(big_occ.get("end_seconds") or 0) >= float(small_occ.get("end_seconds") or 0) - 1e-6
                        for big_occ in larger.get("occurrences") or []
                    ):
                        contained += 1
                if contained >= min(2, int(smaller.get("occurrence_count") or 0)):
                    motif_relations.append({
                        "schema_version": MOTIF_SCHEMA,
                        "relation_type": "motif_contains",
                        "source_motif_id": larger.get("motif_id"),
                        "target_motif_id": smaller.get("motif_id"),
                        "contained_occurrence_count": contained,
                        "authority": "temporal_containment_relationship_evidence",
                    })

        # Retain salient singleton windows for cross-media discovery, but suppress phase-shifted
        # duplicates and windows already represented by a recurrent motif family.
        recurrent_occurrences = [
            (motif, occurrence)
            for motif in motifs
            for occurrence in (motif.get("occurrences") or [])
            if isinstance(occurrence, dict)
        ]
        salient_candidates: list[dict[str, Any]] = []
        singleton_suppressions: list[dict[str, Any]] = []
        for descriptor in sorted(descriptors, key=lambda row: (-float(row.get("salience") or 0), float(row.get("start_seconds") or 0))):
            if float(descriptor.get("salience") or 0) < 0.35:
                continue
            key = (
                round(float(descriptor.get("start_seconds") or 0), 6),
                round(float(descriptor.get("end_seconds") or 0), 6),
            )
            bundle = descriptor.get("signature_bundle") if isinstance(descriptor.get("signature_bundle"), dict) else {}
            candidate_proto = {
                "schema_version": COMPARISON_SCHEMA,
                "signature": bundle.get("signature"),
                "families": bundle.get("families"),
                "tokens": bundle.get("tokens"),
                "sequence_sketches": bundle.get("sequence_sketches"),
                "evidence_coverage": bundle.get("evidence_coverage"),
                "measured_sketch": descriptor.get("measured_sketch"),
            }

            represented_by = None
            for motif, occurrence in recurrent_occurrences:
                overlap = self._motif_overlap_ratio(descriptor, occurrence)
                if overlap < 0.50:
                    continue
                sim = self._motif_prototype_similarity(
                    candidate_proto,
                    motif.get("prototype") if isinstance(motif.get("prototype"), dict) else {},
                )
                if float(sim.get("overall_similarity") or 0) >= 0.68 and float(sim.get("semantic_similarity") or 0) >= 0.45:
                    represented_by = {
                        "reason": "represented_by_recurrent_motif",
                        "motif_id": motif.get("motif_id"),
                        "overlap": round(overlap, 6),
                        "similarity": sim.get("overall_similarity"),
                    }
                    break
            if represented_by is not None:
                singleton_suppressions.append({
                    "start_seconds": key[0], "end_seconds": key[1], **represented_by,
                })
                continue

            duplicate_of = None
            for prior in salient_candidates:
                overlap = self._motif_overlap_ratio(descriptor, prior)
                if overlap < 0.50:
                    continue
                sim = self._motif_prototype_similarity(candidate_proto, prior.get("prototype") or {})
                if float(sim.get("overall_similarity") or 0) >= 0.72 and float(sim.get("semantic_similarity") or 0) >= 0.50:
                    duplicate_of = {
                        "reason": "phase_shifted_singleton_duplicate",
                        "motif_candidate_id": prior.get("motif_candidate_id"),
                        "overlap": round(overlap, 6),
                        "similarity": sim.get("overall_similarity"),
                    }
                    break
            if duplicate_of is not None:
                singleton_suppressions.append({
                    "start_seconds": key[0], "end_seconds": key[1], **duplicate_of,
                })
                continue

            candidate_id = "motif-candidate-" + hashlib.shake_256(
                (str(bundle.get("signature") or "") + "|" + f"{key[0]:.6f}|{key[1]:.6f}").encode("utf-8")
            ).hexdigest(10)
            salient_candidates.append({
                "schema_version": MOTIF_SCHEMA,
                "motif_candidate_id": candidate_id,
                "status": "salient_singleton_candidate",
                "label": self._motif_label(bundle, descriptor, len(salient_candidates) + 1),
                "start_seconds": key[0],
                "end_seconds": key[1],
                "duration_seconds": descriptor.get("duration_seconds"),
                "salience": descriptor.get("salience"),
                "active_families": descriptor.get("active_families"),
                "window_evidence": descriptor.get("window_evidence"),
                "measured_sketch": descriptor.get("measured_sketch"),
                "signature": descriptor.get("signature"),
                "prototype": candidate_proto,
                "authority": "salient_window_candidate_not_yet_recurrent_within_source",
            })
            if len(salient_candidates) >= 32:
                break

        ar = reconstruction.get("analysis_range") if isinstance(reconstruction.get("analysis_range"), dict) else {}
        return {
            "schema_version": MOTIF_SCHEMA,
            "authority": "heuristic_multiscale_motif_extraction_over_witnessed_and_measured_evidence",
            "identity_semantics": "not_person_identity_evidence; motif recurrence is media content/structure evidence",
            "analysis_range": {
                "start_seconds": ar.get("start_seconds"),
                "end_seconds": ar.get("end_seconds"),
                "duration_seconds": ar.get("duration_seconds"),
            },
            "extraction_policy": {
                "candidate_strategy": "event_boundaries_plus_uniform_multiscale_windows",
                "duration_scales_seconds": sorted(duration_groups.keys()),
                "max_candidates": max_candidates,
                "candidate_count": len(descriptors),
                "min_recurrence_similarity": min_similarity,
                "same_motif_overlap_rejection_ratio": 0.35,
                "motif_family_consolidation": "prototype_similarity + >=50% temporal support overlap; occurrence NMS overlap>=0.35",
                "singleton_phase_nms": "overlap>=0.50 + prototype similarity",
                "prototype_token_support_ratio": 0.60,
                "measured_semantic_weights": {"measured": 0.65, "semantic": 0.35},
                "salient_singletons_retained": True,
                "timing": "absolute_source_clock; semantic transition instants remain bounded by sampled anchors",
            },
            "raw_motif_count": raw_motif_count,
            "motif_count": len(motifs),
            "motifs": motifs,
            "motif_family_suppression_count": len(motif_family_suppressions),
            "motif_family_suppressions": motif_family_suppressions[:256],
            "salient_candidate_count": len(salient_candidates),
            "salient_candidate_suppression_count": len(singleton_suppressions),
            "salient_candidate_suppressions": singleton_suppressions[:256],
            "salient_candidates": salient_candidates,
            "relationship_count": len(motif_relations),
            "relationships": motif_relations[:2048],
            "summary": {
                "recurrent_occurrence_count": sum(int(motif.get("occurrence_count") or 0) for motif in motifs),
                "strong_recurrence_count": sum(1 for motif in motifs if motif.get("status") == "strong_recurrence"),
                "cross_modal_motif_count": sum(1 for motif in motifs if motif.get("cross_modal")),
                "periodic_motif_count": sum(1 for motif in motifs if (motif.get("periodicity") or {}).get("classification") == "periodic"),
                "candidate_windows_evaluated": len(descriptors),
                "raw_recurrent_motif_count": raw_motif_count,
                "canonical_motif_count": len(motifs),
                "phase_variant_motifs_suppressed": len(motif_family_suppressions),
                "salient_windows_suppressed": len(singleton_suppressions),
            },
        }

    def motifs(self, job_id: str, *, recompute_if_missing: bool = True) -> dict[str, Any]:
        result = self.result(job_id)
        reconstruction = self._reconstruction_from_result(result)
        visual_enrichment = {"status": "skipped", "reason": "recompute_disabled"}
        audio_enrichment = {"status": "skipped", "reason": "recompute_disabled"}
        music_enrichment = {"status": "skipped", "reason": "recompute_disabled"}
        if recompute_if_missing:
            visual_enrichment = self._ensure_visual_embeddings_for_reconstruction(job_id, reconstruction)
            audio_enrichment = self._ensure_audio_embeddings_for_reconstruction(job_id, reconstruction)
            music_enrichment = self._ensure_music_transcription_for_reconstruction(job_id, reconstruction)
        catalog = reconstruction.get("motifs") if isinstance(reconstruction.get("motifs"), dict) else None
        dino_present = bool((reconstruction.get("visual") or {}).get("perceptual_embeddings"))
        clap_present = bool((reconstruction.get("audio") or {}).get("perceptual_embeddings"))
        ml_notes_present = "ml_note_events" in (reconstruction.get("audio") or {})
        needs_recompute = (
            catalog is None
            or (dino_present and not self._catalog_has_visual_embedding(catalog))
            or (clap_present and not self._catalog_has_audio_embedding(catalog))
            or (ml_notes_present and (reconstruction.get("audio") or {}).get("ml_note_events") and not self._catalog_has_ml_note_events(catalog))
        )
        if needs_recompute and recompute_if_missing:
            catalog = self._motif_catalog(reconstruction)
        if catalog is None:
            raise RuntimeError("media_motif_catalog_unavailable")
        return {
            "job_id": job_id,
            "label": ((result.get("nodes") or [{}])[0] or {}).get("label"),
            "derived_visual_embedding_enrichment": visual_enrichment,
            "derived_audio_embedding_enrichment": audio_enrichment,
            "derived_music_transcription_enrichment": music_enrichment,
            **catalog,
        }

    def align_motif(
        self,
        query_job_id: str,
        motif_id: str,
        target_job_id: str,
        *,
        step_seconds: float | None = None,
        limit: int = 8,
        min_similarity: float = 0.0,
        max_windows: int = 2000,
    ) -> dict[str, Any]:
        catalog = self.motifs(query_job_id)
        motif = next((row for row in catalog.get("motifs") or [] if str(row.get("motif_id") or "") == str(motif_id)), None)
        if motif is None:
            raise KeyError(motif_id)
        rep = motif.get("representative_occurrence") if isinstance(motif.get("representative_occurrence"), dict) else {}
        start = float(rep.get("start_seconds") or 0)
        end = float(rep.get("end_seconds") or start)
        if end - start < 0.05:
            raise ValueError("media_motif_representative_range_invalid")
        alignment = self.align_jobs(
            query_job_id,
            target_job_id,
            query_start_seconds=start,
            query_end_seconds=end,
            window_seconds=end - start,
            step_seconds=step_seconds,
            limit=limit,
            min_similarity=min_similarity,
            max_windows=max_windows,
        )
        alignment["motif_query"] = {
            "motif_id": motif.get("motif_id"),
            "label": motif.get("label"),
            "motif_kind": motif.get("motif_kind"),
            "occurrence_count": motif.get("occurrence_count"),
            "representative_occurrence": rep,
            "prototype_signature": (motif.get("prototype") or {}).get("signature"),
            "recurrence_score": motif.get("recurrence_score"),
            "authority": motif.get("authority"),
        }
        alignment["schema_version"] = "media_motif_alignment/v1"
        return alignment

    @staticmethod
    def _motif_sketch_similarity(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        scales={"visual_mean_luma":50.0,"visual_change_score":20.0,"visual_global_shift_magnitude_normalized":0.35,"audio_rms":0.20,"audio_spectral_centroid_hz":1800.0,"audio_spectral_flux":0.30,"audio_pitch_hz":300.0}
        component_scores:dict[str,float]={}
        for key,scale in scales.items():
            a,b=left.get(key),right.get(key)
            if not isinstance(a,dict) or not isinstance(b,dict): continue
            sub=[]
            for field,count in (("mean",7),("stddev",3)):
                if a.get(field) is None or b.get(field) is None: continue
                sub.extend([max(0.0,1.0-abs(float(a[field])-float(b[field]))/max(1e-9,scale))]*count)
            if sub: component_scores[key]=float(np.mean(sub))
        if left.get("onset_rate_hz") is not None and right.get("onset_rate_hz") is not None:
            component_scores["onset_rate_hz"]=max(0.0,1.0-abs(float(left.get("onset_rate_hz") or 0)-float(right.get("onset_rate_hz") or 0))/4.0)
        baseline=float(np.mean(list(component_scores.values()))) if component_scores else None

        def cosine(key:str)->float|None:
            a,b=left.get(key),right.get(key)
            if not isinstance(a,list) or not isinstance(b,list) or not a or len(a)!=len(b): return None
            av,bv=np.asarray(a,dtype=np.float32),np.asarray(b,dtype=np.float32)
            if not np.all(np.isfinite(av)) or not np.all(np.isfinite(bv)): return None
            den=float(np.linalg.norm(av)*np.linalg.norm(bv))
            if den<=1e-12: return None
            return max(0.0,min(1.0,float(np.dot(av,bv)/den)))
        visual_cos=cosine("visual_embedding_centroid")
        audio_cos=cosine("audio_embedding_centroid")
        if visual_cos is not None: component_scores["visual_embedding_cosine"]=visual_cos
        if audio_cos is not None: component_scores["audio_embedding_cosine"]=audio_cos
        perceptual=[v for v in (visual_cos,audio_cos) if v is not None]
        if baseline is not None and len(perceptual)==2:
            score=.40*baseline+.30*visual_cos+.30*audio_cos; weights={"coarse_measured":.40,"visual_embedding":.30,"audio_embedding":.30}
        elif baseline is not None and len(perceptual)==1:
            score=.55*baseline+.45*perceptual[0]; weights={"coarse_measured":.55,"visual_embedding":.45 if visual_cos is not None else 0.0,"audio_embedding":.45 if audio_cos is not None else 0.0}
        elif perceptual:
            score=float(np.mean(perceptual)); n=len(perceptual); weights={"coarse_measured":0.0,"visual_embedding":1.0/n if visual_cos is not None else 0.0,"audio_embedding":1.0/n if audio_cos is not None else 0.0}
        else:
            score=baseline; weights={"coarse_measured":1.0 if baseline is not None else 0.0,"visual_embedding":0.0,"audio_embedding":0.0}
        return {"score":round(score,6) if score is not None else None,"baseline_score":round(baseline,6) if baseline is not None else None,"visual_embedding_cosine":round(visual_cos,6) if visual_cos is not None else None,"audio_embedding_cosine":round(audio_cos,6) if audio_cos is not None else None,"weights":weights,"components":{k:round(v,6) for k,v in component_scores.items()},"authority":"coarse_measured_plus_optional_visual_and_audio_perceptual_embedding_similarity","identity_semantics":"not_person_identity_evidence; not_speaker_identity_evidence"}

    def _motif_prototype_similarity(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        semantic = self._compare_signature_bundles(left, right)
        semantic_score = float(semantic.get("overall_similarity") or 0)
        sketch = self._motif_sketch_similarity(
            left.get("measured_sketch") if isinstance(left.get("measured_sketch"), dict) else {},
            right.get("measured_sketch") if isinstance(right.get("measured_sketch"), dict) else {},
        )
        sketch_score = sketch.get("score")
        embedding_score = sketch.get("visual_embedding_cosine")
        if sketch_score is None:
            overall = semantic_score
            weights = {"semantic": 1.0, "measured_sketch": 0.0}
        elif embedding_score is not None:
            overall = 0.55 * semantic_score + 0.45 * float(sketch_score)
            weights = {"semantic": 0.55, "measured_sketch": 0.45}
        else:
            overall = 0.75 * semantic_score + 0.25 * float(sketch_score)
            weights = {"semantic": 0.75, "measured_sketch": 0.25}
        return {
            "overall_similarity": round(max(0.0, min(1.0, overall)), 6),
            "semantic_similarity": round(semantic_score, 6),
            "measured_sketch_similarity": round(float(sketch_score), 6) if sketch_score is not None else None,
            "weights": weights,
            "semantic": semantic,
            "measured_sketch": sketch,
            "authority": "motif_prototype_similarity_evidence_only",
            "identity_semantics": "not_person_identity_evidence; media motif structure/content only",
        }

    @staticmethod
    def _motif_row_from_catalog(catalog: dict[str, Any], motif_id: str) -> dict[str, Any] | None:
        for row in catalog.get("motifs") or []:
            if isinstance(row, dict) and str(row.get("motif_id") or "") == str(motif_id):
                return row
        for row in catalog.get("salient_candidates") or []:
            if isinstance(row, dict) and str(row.get("motif_candidate_id") or "") == str(motif_id):
                return row
        return None

    def find_similar_motifs(
        self,
        query_job_id: str,
        motif_id: str,
        *,
        limit: int = 20,
        min_similarity: float = 0.25,
        max_jobs: int = 200,
        include_salient_candidates: bool = True,
        include_query_job: bool = False,
    ) -> dict[str, Any]:
        query_catalog = self.motifs(query_job_id)
        query_motif = self._motif_row_from_catalog(query_catalog, motif_id)
        if query_motif is None:
            raise KeyError(motif_id)
        query_prototype = query_motif.get("prototype") if isinstance(query_motif.get("prototype"), dict) else {}
        if not query_prototype:
            raise RuntimeError("media_motif_prototype_unavailable")

        bounded_limit = max(1, min(int(limit or 20), 100))
        threshold = max(0.0, min(1.0, float(min_similarity or 0.0)))
        job_cap = max(1, min(int(max_jobs or 200), 2000))

        roots: list[tuple[int, Path, dict[str, Any]]] = []
        skipped: list[dict[str, str]] = []
        for root in self.data_dir.glob("mediarec-*"):
            if not include_query_job and root.name == query_job_id:
                continue
            state_path = root / "state.json"
            result_path = root / "result.json"
            if not state_path.is_file() or not result_path.is_file():
                continue
            try:
                state = json.loads(state_path.read_text())
            except Exception:
                skipped.append({"job_id": root.name, "reason": "invalid_state"})
                continue
            if str(state.get("status") or "") != "completed":
                continue
            roots.append((int(state.get("created_at_ms") or 0), root, state))
        roots.sort(key=lambda item: (item[0], item[1].name), reverse=True)

        matches: list[dict[str, Any]] = []
        scanned_jobs = 0
        scanned_motifs = 0
        recomputed_catalogs = 0
        for _, root, state in roots[:job_cap]:
            scanned_jobs += 1
            try:
                result = json.loads((root / "result.json").read_text())
                reconstruction = self._reconstruction_from_result(result)
                catalog = reconstruction.get("motifs") if isinstance(reconstruction.get("motifs"), dict) else None
                if catalog is None:
                    catalog = self._motif_catalog(reconstruction)
                    recomputed_catalogs += 1
            except Exception as exc:
                skipped.append({"job_id": root.name, "reason": type(exc).__name__})
                continue
            candidate_rows = list(catalog.get("motifs") or [])
            if include_salient_candidates:
                candidate_rows.extend(catalog.get("salient_candidates") or [])
            label = ((result.get("nodes") or [{}])[0] or {}).get("label") or state.get("filename") or root.name
            for candidate in candidate_rows:
                if not isinstance(candidate, dict):
                    continue
                prototype = candidate.get("prototype") if isinstance(candidate.get("prototype"), dict) else {}
                if not prototype:
                    continue
                scanned_motifs += 1
                similarity = self._motif_prototype_similarity(query_prototype, prototype)
                score = float(similarity.get("overall_similarity") or 0)
                if score < threshold:
                    continue
                candidate_id = candidate.get("motif_id") or candidate.get("motif_candidate_id")
                matches.append({
                    "job_id": root.name,
                    "label": label,
                    "motif_id": candidate_id,
                    "motif_label": candidate.get("label"),
                    "status": candidate.get("status"),
                    "motif_kind": candidate.get("motif_kind") or "salient_singleton_candidate",
                    "occurrence_count": int(candidate.get("occurrence_count") or (1 if candidate.get("motif_candidate_id") else 0)),
                    "representative_occurrence": candidate.get("representative_occurrence") or {
                        "start_seconds": candidate.get("start_seconds"),
                        "end_seconds": candidate.get("end_seconds"),
                        "duration_seconds": candidate.get("duration_seconds"),
                    },
                    "overall_similarity": similarity.get("overall_similarity"),
                    "semantic_similarity": similarity.get("semantic_similarity"),
                    "measured_sketch_similarity": similarity.get("measured_sketch_similarity"),
                    "similarity_components": similarity,
                    "prototype_signature": prototype.get("signature"),
                    "authority": similarity.get("authority"),
                    "identity_semantics": similarity.get("identity_semantics"),
                })
        matches.sort(key=lambda row: (
            -float(row.get("overall_similarity") or 0),
            -int(row.get("occurrence_count") or 0),
            str(row.get("job_id") or ""),
            str(row.get("motif_id") or ""),
        ))
        return {
            "schema_version": "media_motif_similarity_search/v1",
            "authority": "motif_prototype_similarity_evidence_only",
            "identity_semantics": "not_person_identity_evidence; search compares witnessed media motifs only",
            "query_job_id": query_job_id,
            "query_motif_id": motif_id,
            "query_motif_label": query_motif.get("label"),
            "query_prototype_signature": query_prototype.get("signature"),
            "limit": bounded_limit,
            "min_similarity": round(threshold, 6),
            "max_jobs": job_cap,
            "include_salient_candidates": bool(include_salient_candidates),
            "scanned_jobs": scanned_jobs,
            "scanned_motifs": scanned_motifs,
            "recomputed_legacy_catalogs": recomputed_catalogs,
            "skipped": skipped[:64],
            "count": min(len(matches), bounded_limit),
            "matches": matches[:bounded_limit],
        }

    def align_jobs(
        self,
        query_job_id: str,
        target_job_id: str,
        *,
        query_start_seconds: float | None = None,
        query_end_seconds: float | None = None,
        window_seconds: float | None = None,
        step_seconds: float | None = None,
        limit: int = 8,
        min_similarity: float = 0.0,
        max_windows: int = 2000,
    ) -> dict[str, Any]:
        """Locate time ranges in target whose witnessed structure best matches query."""
        query_result = self.result(query_job_id)
        target_result = self.result(target_job_id)
        query_reconstruction = self._reconstruction_from_result(query_result)
        target_reconstruction = self._reconstruction_from_result(target_result)
        query_perceptual_enrichment = self._ensure_visual_embeddings_for_reconstruction(query_job_id, query_reconstruction)
        target_perceptual_enrichment = self._ensure_visual_embeddings_for_reconstruction(target_job_id, target_reconstruction)
        query_audio_perceptual_enrichment = self._ensure_audio_embeddings_for_reconstruction(query_job_id, query_reconstruction)
        target_audio_perceptual_enrichment = self._ensure_audio_embeddings_for_reconstruction(target_job_id, target_reconstruction)
        query_music_transcription_enrichment = self._ensure_music_transcription_for_reconstruction(query_job_id, query_reconstruction)
        target_music_transcription_enrichment = self._ensure_music_transcription_for_reconstruction(target_job_id, target_reconstruction)

        qr = query_reconstruction.get("analysis_range") if isinstance(query_reconstruction.get("analysis_range"), dict) else {}
        tr = target_reconstruction.get("analysis_range") if isinstance(target_reconstruction.get("analysis_range"), dict) else {}
        retained_q_start = float(qr.get("start_seconds") or 0)
        retained_q_end = float(qr.get("end_seconds") or retained_q_start)
        if retained_q_end <= retained_q_start:
            q_clock = query_reconstruction.get("source_clock") if isinstance(query_reconstruction.get("source_clock"), dict) else {}
            retained_q_end = float(q_clock.get("duration_seconds") or retained_q_start)
        if retained_q_end <= retained_q_start:
            raise ValueError("media_alignment_query_has_no_timeline")

        explicit_query_range = query_start_seconds is not None or query_end_seconds is not None
        if explicit_query_range and (query_start_seconds is None or query_end_seconds is None):
            raise ValueError("media_alignment_query_range_requires_start_and_end")
        if explicit_query_range:
            q_start = float(query_start_seconds)
            q_end = float(query_end_seconds)
            if not math.isfinite(q_start) or not math.isfinite(q_end) or q_end - q_start < 0.05:
                raise ValueError("media_alignment_invalid_query_range")
            if q_start < retained_q_start - 1e-6 or q_end > retained_q_end + 1e-6:
                raise ValueError("media_alignment_query_range_outside_retained_analysis")
        else:
            q_start = retained_q_start
            q_end = retained_q_end
        query_duration = max(0.05, q_end - q_start)

        # Alignment is now symmetric: A and every scanned B candidate both use
        # window-local semantic/audio evidence. This prevents long ASR segments or
        # source-global music hypotheses from bleeding into motif localization.
        query_signature = self._window_signature_from_reconstruction(
            query_reconstruction,
            start_seconds=q_start,
            end_seconds=q_end,
        )
        query_perceptual_sketch = self._motif_measured_sketch(query_reconstruction, q_start, q_end)
        t_start = float(tr.get("start_seconds") or 0)
        t_end = float(tr.get("end_seconds") or t_start)
        if t_end <= t_start:
            clock = target_reconstruction.get("source_clock") if isinstance(target_reconstruction.get("source_clock"), dict) else {}
            t_end = float(clock.get("duration_seconds") or t_start)
        if t_end <= t_start:
            raise ValueError("media_alignment_target_has_no_timeline")

        window = max(0.05, float(window_seconds if window_seconds is not None else query_duration))
        window = min(window, max(0.05, t_end - t_start))
        step = max(0.01, float(step_seconds if step_seconds is not None else max(0.05, window / 4.0)))
        bounded_limit = max(1, min(int(limit or 8), 50))
        threshold = max(0.0, min(1.0, float(min_similarity or 0.0)))
        cap = max(1, min(int(max_windows or 2000), 10000))

        starts: list[float] = []
        cursor = t_start
        while cursor + window <= t_end + 1e-9 and len(starts) < cap:
            starts.append(cursor)
            cursor += step
        last_start = max(t_start, t_end - window)
        if len(starts) < cap and (not starts or abs(starts[-1] - last_start) > 1e-6):
            starts.append(last_start)

        candidates: list[dict[str, Any]] = []
        for index, start in enumerate(starts):
            end = min(t_end, start + window)
            target_signature = self._window_signature_from_reconstruction(target_reconstruction, start_seconds=start, end_seconds=end)
            comparison = self._compare_signature_bundles(query_signature, target_signature)
            semantic_score = float(comparison.get("overall_similarity") or 0)
            measured = self._measured_alignment_similarity(
                query_reconstruction,
                target_reconstruction,
                query_start_seconds=q_start,
                query_end_seconds=q_end,
                target_start_seconds=start,
                target_end_seconds=end,
            )
            target_perceptual_sketch = self._motif_measured_sketch(target_reconstruction, start, end)
            perceptual = self._motif_sketch_similarity(query_perceptual_sketch, target_perceptual_sketch)
            visual_embedding_score = perceptual.get("visual_embedding_cosine")
            audio_embedding_score = perceptual.get("audio_embedding_cosine")
            measured_score = measured.get("score")
            visual_weight = 0.0
            audio_weight = 0.0
            if measured_score is not None and visual_embedding_score is not None and audio_embedding_score is not None:
                measured_weight = 0.50
                semantic_weight = 0.20
                visual_weight = 0.15
                audio_weight = 0.15
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "visual_embedding": visual_weight, "audio_embedding": audio_weight}
                score = semantic_weight * semantic_score + measured_weight * float(measured_score) + visual_weight * float(visual_embedding_score) + audio_weight * float(audio_embedding_score)
            elif measured_score is not None and visual_embedding_score is not None:
                # Preserve the previously-qualified DINO-only alignment policy exactly.
                measured_weight = 0.60
                semantic_weight = 0.20
                visual_weight = 0.20
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "visual_embedding": visual_weight}
                score = semantic_weight * semantic_score + measured_weight * float(measured_score) + visual_weight * float(visual_embedding_score)
            elif measured_score is not None and audio_embedding_score is not None:
                measured_weight = 0.60
                semantic_weight = 0.20
                audio_weight = 0.20
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "audio_embedding": audio_weight}
                score = semantic_weight * semantic_score + measured_weight * float(measured_score) + audio_weight * float(audio_embedding_score)
            elif measured_score is not None:
                measured_weight = 0.75
                semantic_weight = 0.25
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "visual_embedding": 0.0}
                score = semantic_weight * semantic_score + measured_weight * float(measured_score)
            elif visual_embedding_score is not None and audio_embedding_score is not None:
                measured_weight = 0.0
                semantic_weight = 0.40
                visual_weight = 0.30
                audio_weight = 0.30
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "visual_embedding": visual_weight, "audio_embedding": audio_weight}
                score = semantic_weight * semantic_score + visual_weight * float(visual_embedding_score) + audio_weight * float(audio_embedding_score)
            elif visual_embedding_score is not None:
                measured_weight = 0.0
                semantic_weight = 0.35
                visual_weight = 0.65
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "visual_embedding": visual_weight}
                score = semantic_weight * semantic_score + visual_weight * float(visual_embedding_score)
            elif audio_embedding_score is not None:
                measured_weight = 0.0
                semantic_weight = 0.35
                audio_weight = 0.65
                score_weights = {"semantic": semantic_weight, "measured": measured_weight, "audio_embedding": audio_weight}
                score = semantic_weight * semantic_score + audio_weight * float(audio_embedding_score)
            else:
                score = semantic_score
                measured_weight = 0.0
                semantic_weight = 1.0
                score_weights = {"semantic": 1.0, "measured": 0.0, "visual_embedding": 0.0}
            if score < threshold:
                continue
            candidates.append({
                "window_index": index,
                "start_seconds": round(start, 6),
                "end_seconds": round(end, 6),
                "duration_seconds": round(end-start, 6),
                "overall_similarity": round(score, 6),
                "semantic_similarity": round(semantic_score, 6),
                "measured_similarity": round(float(measured_score), 6) if measured_score is not None else None,
                "visual_embedding_similarity": round(float(visual_embedding_score), 6) if visual_embedding_score is not None else None,
                "audio_embedding_similarity": round(float(audio_embedding_score), 6) if audio_embedding_score is not None else None,
                "score_weights": score_weights,
                "measured_alignment": measured,
                "perceptual_alignment": perceptual,
                "token_jaccard": comparison.get("token_jaccard"),
                "family_weighted_similarity": comparison.get("family_weighted_similarity"),
                "sequence_similarity": comparison.get("sequence_similarity"),
                "comparison_coverage": comparison.get("comparison_coverage"),
                "family_overlap": comparison.get("family_overlap"),
                "common_tokens": (comparison.get("common_tokens") or [])[:48],
                "target_window_evidence": target_signature.get("window_evidence"),
                "target_signature": target_signature.get("signature"),
            })
        candidates.sort(key=lambda row:(-float(row.get("overall_similarity") or 0), float(row.get("start_seconds") or 0)))

        def overlap_ratio(a: dict[str, Any], b: dict[str, Any]) -> float:
            left=max(float(a["start_seconds"]),float(b["start_seconds"]))
            right=min(float(a["end_seconds"]),float(b["end_seconds"]))
            inter=max(0.0,right-left)
            denom=max(1e-9,min(float(a["duration_seconds"]),float(b["duration_seconds"])))
            return inter/denom

        selected: list[dict[str, Any]] = []
        for row in candidates:
            if any(overlap_ratio(row, prior) >= 0.75 for prior in selected):
                continue
            selected.append(row)
            if len(selected) >= bounded_limit:
                break
        alignment = {
            "schema_version": "media_temporal_alignment/v1",
            "authority": "measured_temporal_alignment_plus_optional_visual_audio_perceptual_embeddings_plus_heuristic_semantic_evidence",
            "identity_semantics": "not_person_identity_evidence; not_speaker_identity_evidence; temporal alignment of witnessed media structure/content only",
            "scoring_policy": {
                "when_measured_and_both_perceptual_embeddings_available": {"measured_weight": 0.50, "semantic_weight": 0.20, "visual_embedding_weight": 0.15, "audio_embedding_weight": 0.15},
                "when_measured_and_visual_embedding_available": {"measured_weight": 0.60, "semantic_weight": 0.20, "visual_embedding_weight": 0.20},
                "when_measured_and_audio_embedding_available": {"measured_weight": 0.60, "semantic_weight": 0.20, "audio_embedding_weight": 0.20},
                "when_measured_available": {"measured_weight": 0.75, "semantic_weight": 0.25, "visual_embedding_weight": 0.0, "audio_embedding_weight": 0.0},
                "when_both_perceptual_embeddings_only": {"measured_weight": 0.0, "semantic_weight": 0.40, "visual_embedding_weight": 0.30, "audio_embedding_weight": 0.30},
                "when_one_perceptual_embedding_only": {"measured_weight": 0.0, "semantic_weight": 0.35, "available_perceptual_weight": 0.65},
                "fallback": "semantic_similarity_only_when_time_locked_and_perceptual_measurements_are_unavailable",
                "measured_schema": "media_measured_temporal_alignment/v1",
                "visual_perceptual_schema": "media_derived_visual_embeddings/v1",
                "audio_perceptual_schema": "media_derived_audio_embeddings/v1",
            },
            "perceptual_enrichment": {"query": query_perceptual_enrichment, "target": target_perceptual_enrichment},
            "audio_perceptual_enrichment": {"query": query_audio_perceptual_enrichment, "target": target_audio_perceptual_enrichment},
            "music_transcription_enrichment": {"query": query_music_transcription_enrichment, "target": target_music_transcription_enrichment},
            "query_job_id": query_job_id,
            "target_job_id": target_job_id,
            "query_label": ((query_result.get("nodes") or [{}])[0] or {}).get("label"),
            "target_label": ((target_result.get("nodes") or [{}])[0] or {}).get("label"),
            "query_range": {
                "start_seconds": q_start,
                "end_seconds": q_end,
                "duration_seconds": query_duration,
                "scope": "explicit_selection" if explicit_query_range else "retained_analysis_range",
                "retained_start_seconds": retained_q_start,
                "retained_end_seconds": retained_q_end,
            },
            "query_window_evidence": query_signature.get("window_evidence"),
            "target_range": {"start_seconds": t_start, "end_seconds": t_end, "duration_seconds": max(0.0,t_end-t_start)},
            "window_seconds": round(window, 6),
            "step_seconds": round(step, 6),
            "windows_scanned": len(starts),
            "candidate_count": len(candidates),
            "matches": selected,
        }
        best = selected[0] if selected else None
        best_start = float(best.get("start_seconds") or 0.0) if isinstance(best, dict) else -1.0
        best_end = float(best.get("end_seconds") or 0.0) if isinstance(best, dict) else -1.0
        self._record_relationship(
            relation_type="temporal_alignment",
            source_job_id=query_job_id,
            target_job_id=target_job_id,
            relationship_key=(
                "temporal_alignment|" + str(query_job_id) + "|" + str(target_job_id)
                + "|" + f"{q_start:.6f}|{q_end:.6f}"
                + "|" + f"{best_start:.6f}|{best_end:.6f}"
            ),
            authority=str(alignment.get("authority") or "measured_temporal_alignment_plus_heuristic_semantic_evidence"),
            evidence={
                "query_range": alignment.get("query_range"),
                "target_range": alignment.get("target_range"),
                "window_seconds": alignment.get("window_seconds"),
                "step_seconds": alignment.get("step_seconds"),
                "match_count": len(selected),
                "best_match": ({
                    "start_seconds": best.get("start_seconds"),
                    "end_seconds": best.get("end_seconds"),
                    "overall_similarity": best.get("overall_similarity"),
                    "measured_similarity": best.get("measured_similarity"),
                    "semantic_similarity": best.get("semantic_similarity"),
                    "visual_embedding_similarity": best.get("visual_embedding_similarity"),
                    "audio_embedding_similarity": best.get("audio_embedding_similarity"),
                } if isinstance(best, dict) else None),
                "scoring_policy": alignment.get("scoring_policy"),
            },
        )
        return alignment

    def find_similar_jobs(
        self,
        job_id: str,
        *,
        limit: int = 12,
        min_similarity: float = 0.0,
        max_candidates: int = 500,
    ) -> dict[str, Any]:
        """Rank retained completed reconstruction witnesses by normalized media similarity."""
        query_result = self.result(job_id)
        query_signature = self._comparison_signature_from_result(query_result)
        bounded_limit = max(1, min(int(limit or 12), 50))
        threshold = max(0.0, min(1.0, float(min_similarity or 0.0)))
        candidate_cap = max(bounded_limit, min(int(max_candidates or 500), 2000))

        candidates: list[dict[str, Any]] = []
        skipped: list[dict[str, str]] = []
        scanned = 0
        roots: list[tuple[int, Path, dict[str, Any]]] = []
        for root in self.data_dir.glob("mediarec-*"):
            if root.name == job_id:
                continue
            state_path = root / "state.json"
            result_path = root / "result.json"
            if not state_path.is_file() or not result_path.is_file():
                continue
            try:
                state = json.loads(state_path.read_text())
            except Exception:
                skipped.append({"job_id": root.name, "reason": "invalid_state"})
                continue
            if str(state.get("status") or "") != "completed":
                continue
            roots.append((int(state.get("created_at_ms") or 0), root, state))
        roots.sort(key=lambda row: (row[0], row[1].name), reverse=True)

        for _, root, state in roots[:candidate_cap]:
            scanned += 1
            try:
                candidate_result = json.loads((root / "result.json").read_text())
                candidate_signature = self._comparison_signature_from_result(candidate_result)
                comparison = self._compare_signature_bundles(query_signature, candidate_signature)
            except Exception as exc:
                skipped.append({"job_id": root.name, "reason": type(exc).__name__})
                continue
            score = float(comparison.get("overall_similarity") or 0.0)
            if score < threshold:
                continue
            nodes = candidate_result.get("nodes") if isinstance(candidate_result, dict) else None
            first_node = nodes[0] if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict) else {}
            candidates.append({
                "job_id": root.name,
                "filename": state.get("filename") or first_node.get("label") or "media",
                "label": first_node.get("label") or state.get("filename") or "media",
                "created_at_ms": int(state.get("created_at_ms") or 0),
                "analysis_profile": candidate_result.get("analysis_profile"),
                "overall_similarity": comparison.get("overall_similarity"),
                "exact_normalized_signature_match": comparison.get("exact_normalized_signature_match"),
                "token_jaccard": comparison.get("token_jaccard"),
                "family_weighted_similarity": comparison.get("family_weighted_similarity"),
                "sequence_similarity": comparison.get("sequence_similarity"),
                "family_overlap": comparison.get("family_overlap"),
                "common_tokens": (comparison.get("common_tokens") or [])[:64],
                "comparison_signature": candidate_signature.get("signature"),
                "authority": comparison.get("authority"),
                "identity_semantics": comparison.get("identity_semantics"),
            })

        candidates.sort(
            key=lambda row: (
                -float(row.get("overall_similarity") or 0.0),
                -int(bool(row.get("exact_normalized_signature_match"))),
                -int(row.get("created_at_ms") or 0),
                str(row.get("job_id") or ""),
            )
        )
        matches = candidates[:bounded_limit]
        query_nodes = query_result.get("nodes") if isinstance(query_result, dict) else None
        query_node = query_nodes[0] if isinstance(query_nodes, list) and query_nodes and isinstance(query_nodes[0], dict) else {}
        return {
            "schema_version": "media_similarity_search/v1",
            "authority": "heuristic_similarity_evidence_only",
            "identity_semantics": "not_person_identity_evidence; compare witnessed media structure/content only",
            "query_job_id": job_id,
            "query_label": query_node.get("label"),
            "query_signature": query_signature.get("signature"),
            "min_similarity": round(threshold, 6),
            "limit": bounded_limit,
            "max_candidates": candidate_cap,
            "scanned_candidates": scanned,
            "skipped_candidates": len(skipped),
            "skipped": skipped[:32],
            "count": len(matches),
            "matches": matches,
        }

    def _job_root(self, job_id: str) -> Path:
        if not re.fullmatch(r"mediarec-[a-f0-9]{24}", str(job_id or "")):
            raise KeyError(job_id)
        root = (self.data_dir / job_id).resolve()
        if self.data_dir.resolve() not in root.parents:
            raise KeyError(job_id)
        return root

    def _state(self, root: Path, state: dict[str, Any], **updates: Any) -> None:
        # State writes come from both the worker thread and request thread. Keep the
        # transition lattice monotonic so stale dictionaries can never resurrect a
        # terminal job or move a cancellation back to running.
        path = root / "state.json"
        with self._lock:
            current: dict[str, Any] = {}
            if path.is_file():
                try:
                    loaded = json.loads(path.read_text())
                    if isinstance(loaded, dict):
                        current = loaded
                except Exception:
                    current = {}
            current_status = str(current.get("status") or "")
            incoming_status = str(updates.get("status", state.get("status") or current_status) or "")
            if current_status in TERMINAL_JOB_STATUSES and incoming_status not in TERMINAL_JOB_STATUSES:
                state.clear()
                state.update(current)
                return
            if current_status == "cancelling" and incoming_status in {"queued", "running", "cancelling"}:
                updates["status"] = "cancelling"
                updates["stage"] = "cancelling"
                updates["cancel_requested"] = True
                if current.get("progress") is not None:
                    updates["progress"] = max(
                        float(current.get("progress") or 0),
                        float(updates.get("progress", state.get("progress") or 0) or 0),
                    )
            state.update(updates)
            if (root / "cancel.requested").exists() and state.get("status") not in TERMINAL_JOB_STATUSES:
                state["cancel_requested"] = True
            state["updated_at_ms"] = int(time.time() * 1000)
            _atomic_json(path, state)

    def _raise_if_cancelled(self, root: Path) -> None:
        if (root / "cancel.requested").exists():
            raise MediaReconstructionCancelled("media_reconstruction_cancelled")

    def _run_job(self, job_id: str, source: Path, filename: str, mime_type: str, options: dict[str, Any]) -> None:
        root = self.data_dir / job_id
        state = self.status(job_id)
        try:
            self._raise_if_cancelled(root)
            self._state(root, state, status="running", stage="probe", progress=0.02)
            def on_progress(stage: str, p: float) -> None:
                self._raise_if_cancelled(root)
                self._state(root, state, status="running", stage=stage, progress=float(p))
            result = self.analyze(source, filename=filename, mime_type=mime_type, options=options, progress=on_progress)
            self._raise_if_cancelled(root)
            lineage = state.get("lineage") if isinstance(state.get("lineage"), dict) else None
            if lineage:
                lineage_copy = json.loads(json.dumps(lineage))
                result["lineage"] = lineage_copy
                result["parent_job_id"] = state.get("parent_job_id") or lineage_copy.get("parent_job_id")
                for node in result.get("nodes") or []:
                    if not isinstance(node, dict):
                        continue
                    witness = node.get("witness") if isinstance(node.get("witness"), dict) else None
                    if witness is None:
                        continue
                    witness["lineage"] = json.loads(json.dumps(lineage_copy))
                    source_record = witness.get("source") if isinstance(witness.get("source"), dict) else None
                    if source_record is not None:
                        source_record["lineage"] = json.loads(json.dumps(lineage_copy))
            _atomic_json(root / "result.json", result)
            self._state(root, state, status="completed", stage="completed", progress=1.0, completed_at_ms=int(time.time() * 1000), summary=result.get("summary"))
        except MediaReconstructionCancelled:
            self._state(root, state, status="cancelled", stage="cancelled", progress=float(state.get("progress") or 0), cancel_requested=True, cancelled_at_ms=int(time.time() * 1000), detail="media_reconstruction_cancelled")
        except Exception as exc:
            self._state(root, state, status="failed", stage="failed", progress=float(state.get("progress") or 0), error=type(exc).__name__, detail=str(exc)[:1200], failed_at_ms=int(time.time() * 1000))
        finally:
            with self._lock:
                self._futures.pop(job_id, None)

    def _run(self, args: list[str], *, timeout: float = 120.0, input_bytes: bytes | None = None) -> bytes:
        cp = subprocess.run(args, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        if cp.returncode != 0:
            raise RuntimeError(f"media_tool_failed:{Path(args[0]).name}:{cp.stderr.decode('utf-8','replace')[-1200:]}")
        return cp.stdout

    def _probe(self, source: Path) -> dict[str, Any]:
        raw = self._run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(source)], timeout=30)
        return json.loads(raw.decode("utf-8"))

    def _service(self, service: str) -> dict[str, Any] | None:
        registry = self.service_registry
        if registry is None:
            return None
        report = registry.scheduler_candidates(service=service, require_live=True, live_timeout_seconds=3.0, observe_pressure=True, pressure_timeout_seconds=2.0, limit=1)
        rows = [r for r in report.get("candidates") or [] if isinstance(r, dict)]
        if not rows:
            return None
        candidate = rows[0]
        node_id = str(candidate.get("node_id") or "")
        record: dict[str, Any] = {}
        try:
            node = next((n for n in registry.nodes() if str(n.get("id") or "") == node_id), None)
            if isinstance(node, dict):
                services = node.get("services") if isinstance(node.get("services"), dict) else {}
                record = dict(services.get(service) or {}) if isinstance(services.get(service), dict) else {}
        except Exception:
            record = {}
        return {"candidate": candidate, "record": record}

    def _visual_metrics(self, source: Path, duration: float, rate_hz: float) -> list[dict[str, Any]]:
        # Deterministic visual witnesses may run up to the source frame clock (capped at
        # 60 Hz by analyze()). Semantic vision remains separately event/interval gated.
        rate = max(0.5, min(60.0, float(rate_hz or 4.0)))
        w, h = 160, 90
        args = ["ffmpeg", "-v", "error", "-i", str(source), "-an", "-vf", f"fps={rate:.6f},scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        frame_bytes = w * h * 3
        previous_gray: np.ndarray | None = None
        out: list[dict[str, Any]] = []
        try:
            index = 0
            while True:
                chunk = proc.stdout.read(frame_bytes) if proc.stdout else b""
                if len(chunk) != frame_bytes:
                    break
                arr = np.frombuffer(chunk, dtype=np.uint8).reshape(h, w, 3)
                mean_rgb = arr.mean(axis=(0, 1))
                gray = arr.astype(np.float32).mean(axis=2)
                luma = float(gray.mean())
                change = 0.0 if previous_gray is None else float(np.mean(np.abs(gray - previous_gray)))
                dx = dy = 0
                motion_error = 0.0
                if previous_gray is not None:
                    a = previous_gray[::4, ::4]
                    b = gray[::4, ::4]
                    best = (float("inf"), 0, 0)
                    for yy in range(-2, 3):
                        for xx in range(-2, 3):
                            y0a, y1a = max(0, yy), min(a.shape[0], a.shape[0] + yy)
                            x0a, x1a = max(0, xx), min(a.shape[1], a.shape[1] + xx)
                            y0b, y1b = max(0, -yy), min(b.shape[0], b.shape[0] - yy)
                            x0b, x1b = max(0, -xx), min(b.shape[1], b.shape[1] - xx)
                            if y1a <= y0a or x1a <= x0a:
                                continue
                            err = float(np.mean(np.abs(a[y0a:y1a, x0a:x1a] - b[y0b:y1b, x0b:x1b])))
                            if err < best[0]:
                                best = (err, xx * 4, yy * 4)
                    motion_error, dx, dy = best
                rgb = [int(round(float(x))) for x in mean_rgb]
                dx_norm = float(dx) / float(w)
                dy_norm = float(dy) / float(h)
                shift_mag = math.hypot(dx_norm, dy_norm)
                if shift_mag < 0.004:
                    shift_direction = "stationary_or_below_resolution"
                else:
                    horizontal = "right" if dx_norm > 0.003 else ("left" if dx_norm < -0.003 else "")
                    vertical = "down" if dy_norm > 0.003 else ("up" if dy_norm < -0.003 else "")
                    shift_direction = "-".join(x for x in (vertical, horizontal) if x) or "small_shift"
                out.append({
                    "sample_index": index,
                    "time_seconds": round(index / rate, 6),
                    "frame_interval_seconds": round(1.0 / rate, 9),
                    "mean_rgb": rgb,
                    "dominant_color": _color_name(rgb),
                    "mean_luma": round(luma, 3),
                    "change_score": round(change, 4),
                    "global_motion": {
                        "dx_pixels": int(dx), "dy_pixels": int(dy),
                        "dx_normalized": round(dx_norm, 6), "dy_normalized": round(dy_norm, 6),
                        "magnitude_normalized": round(shift_mag, 6),
                        "image_shift_direction": shift_direction,
                        "fit_error": round(float(motion_error), 4),
                        "authority": "deterministic_low_resolution_image_shift_measurement",
                        "note": "Image-plane shift only; not a direct real-world camera/person direction claim.",
                    },
                })
                previous_gray = gray
                index += 1
        finally:
            if proc.stdout:
                proc.stdout.close()
            stderr = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
            rc = proc.wait(timeout=20)
            if rc != 0:
                raise RuntimeError(f"visual_metric_ffmpeg_failed:{stderr[-1000:]}")
        return out

    def _select_anchors(self, metrics: list[dict[str, Any]], *, interval_seconds: float, max_anchors: int) -> list[dict[str, Any]]:
        if not metrics:
            return []
        interval = max(0.25, float(interval_seconds or 2.0))
        limit = max(4, min(240, int(max_anchors or 120)))
        scores = np.asarray([float(m.get("change_score") or 0) for m in metrics], dtype=np.float32)
        threshold = max(12.0, float(np.percentile(scores, 85))) if scores.size else 12.0
        selected: dict[int, dict[str, Any]] = {0: metrics[0], len(metrics) - 1: metrics[-1]}
        last_time = -1e9
        for m in metrics:
            t = float(m["time_seconds"])
            if t - last_time >= interval:
                selected[int(m["sample_index"])] = m
                last_time = t
            if float(m.get("change_score") or 0) >= threshold:
                selected[int(m["sample_index"])] = m
        rows = list(selected.values())
        if len(rows) > limit:
            mandatory = {0, int(metrics[-1]["sample_index"])}
            ranked = sorted(rows, key=lambda m: float(m.get("change_score") or 0), reverse=True)
            keep = {int(m["sample_index"]) for m in ranked[: max(0, limit // 2)]} | mandatory
            remaining = [m for m in rows if int(m["sample_index"]) not in keep]
            slots = max(0, limit - len(keep))
            if slots and remaining:
                step = max(1, math.ceil(len(remaining) / slots))
                keep.update(int(m["sample_index"]) for m in remaining[::step][:slots])
            rows = [m for m in rows if int(m["sample_index"]) in keep]
        rows.sort(key=lambda m: int(m["sample_index"]))
        return rows

    def _anchor_images(self, source: Path, anchors: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        img_dir = root / "anchors"
        img_dir.mkdir(parents=True, exist_ok=True)
        for i, anchor in enumerate(anchors):
            path = img_dir / f"anchor-{i:04d}.jpg"
            t = max(0.0, float(anchor.get("time_seconds") or 0))
            try:
                self._run(["ffmpeg", "-v", "error", "-ss", f"{t:.6f}", "-i", str(source), "-frames:v", "1", "-vf", "scale='min(640,iw)':-2", "-q:v", "3", "-y", str(path)], timeout=25)
                if path.is_file() and path.stat().st_size > 0:
                    out.append({**anchor, "image_path": str(path), "anchor_index": i})
            except Exception:
                continue
        return out

    @staticmethod
    def _audio_embedding_windows(start: float, end: float, *, max_windows: int = 512, window_seconds: float = 1.0, hop_seconds: float = 0.5) -> list[dict[str, float]]:
        start=max(0.0,float(start)); end=max(start,float(end)); span=end-start
        if span<0.05: return []
        window=min(max(0.05,float(window_seconds)),span)
        latest=end-window
        if latest<=start+1e-9: return [{"start_seconds":round(start,6),"end_seconds":round(end,6)}]
        hop=max(0.05,float(hop_seconds))
        estimated=int(math.floor((latest-start)/hop))+2
        if estimated>max_windows:
            hop=max(hop,(latest-start)/max(1,max_windows-1))
        starts=[]; cursor=start
        while cursor<=latest+1e-9 and len(starts)<max_windows:
            starts.append(cursor); cursor+=hop
        if starts and latest-starts[-1]>1e-4 and len(starts)<max_windows: starts.append(latest)
        elif starts: starts[-1]=latest
        return [{"start_seconds":round(v,6),"end_seconds":round(min(end,v+window),6)} for v in sorted(set(round(x,6) for x in starts))]

    def _audio_embeddings(self, source: Path, *, start_seconds: float, end_seconds: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        try: service=self._service("audio_embedding")
        except Exception as exc: return [],{"status":"unavailable","error":type(exc).__name__,"detail":str(exc)[:300]}
        if not service: return [],{"status":"unavailable"}
        candidate,record=service["candidate"],service["record"]
        endpoint=str(candidate.get("service_endpoint") or "").rstrip("/"); path=str(record.get("embed_path") or "/embed/windows")
        if not path.startswith("/"): path="/"+path
        windows=self._audio_embedding_windows(start_seconds,end_seconds,max_windows=max(1,min(512,int(record.get("max_windows") or 512))),window_seconds=float(record.get("window_seconds") or 1.0),hop_seconds=float(record.get("hop_seconds") or 0.5))
        if not windows: return [],{"status":"not_applicable","window_count":0}
        expected=int(record.get("dimensions") or 0); model=str(record.get("model") or "unknown")
        try:
            with source.open("rb") as fh, httpx.Client(timeout=httpx.Timeout(300.0,connect=5.0),trust_env=False) as client:
                response=client.post(endpoint+path,files={"file":(source.name,fh,"application/octet-stream")},data={"windows_json":json.dumps(windows,separators=(",",":"))})
                response.raise_for_status(); payload=response.json()
            items=payload.get("items") if isinstance(payload,dict) else None
            if not isinstance(items,list): raise RuntimeError("audio_embedding_items_missing")
            out=[]
            for item in items:
                if not isinstance(item,dict): continue
                raw=item.get("vector") if isinstance(item.get("vector"),list) else item.get("embedding")
                if not isinstance(raw,list) or not raw: continue
                vec=np.asarray(raw,dtype=np.float32)
                if vec.ndim!=1 or not np.all(np.isfinite(vec)): continue
                if expected and int(vec.size)!=expected: raise RuntimeError("audio_embedding_dimensions_mismatch")
                norm=float(np.linalg.norm(vec))
                if norm<=1e-12: continue
                vec=vec/norm; rs=float(item.get("start_seconds") or 0); re_=float(item.get("end_seconds") or rs)
                out.append({"time_seconds":round((rs+re_)/2.0,6),"start_seconds":round(rs,6),"end_seconds":round(re_,6),"embedding":[round(float(v),8) for v in vec.tolist()],"dimensions":int(vec.size),"model":str(payload.get("model") or model),"normalized":True,"provenance":{"source":"media_reconstruction","extractor":"audio_perceptual_embedding","worker_id":candidate.get("node_id"),"service":"audio_embedding","endpoint_scope":candidate.get("service_endpoint_scope"),"model":str(payload.get("model") or model),"authority":"perceptual_audio_embedding_similarity_evidence_only","identity_semantics":"not_speaker_identity_evidence; audio content/timbre/structure similarity only","evidence":"decoded_source_audio_window","internet_required":bool(record.get("internet_required",False))}})
            return out,{"status":"completed" if out else "failed","worker_id":candidate.get("node_id"),"model":model,"image":record.get("image"),"image_id":record.get("image_id"),"internet_required":bool(record.get("internet_required",False)),"window_count":len(windows),"embedding_count":len(out)}
        except Exception as exc:
            return [],{"status":"failed","worker_id":candidate.get("node_id"),"model":model,"error":type(exc).__name__,"detail":str(exc)[:500],"window_count":len(windows)}

    def _ensure_audio_embeddings_for_reconstruction(self, job_id: str, reconstruction: dict[str, Any]) -> dict[str, Any]:
        audio=reconstruction.get("audio") if isinstance(reconstruction.get("audio"),dict) else None
        if audio is None: return {"status":"unavailable","reason":"no_audio_reconstruction"}
        existing=audio.get("perceptual_embeddings")
        if isinstance(existing,list) and existing: return {"status":"embedded","embedding_count":len(existing),"model":existing[0].get("model") if isinstance(existing[0],dict) else None}
        root=self._job_root(job_id); cache=root/"derived_audio_embeddings.json"
        if cache.is_file():
            try:
                cached=json.loads(cache.read_text()); rows=cached.get("embeddings") if isinstance(cached,dict) else None
                if isinstance(rows,list) and rows:
                    audio["perceptual_embeddings"]=rows; audio["perceptual_embedding_policy"]="derived_from_retained_exact_source_audio; cache_sidecar_only"; audio["perceptual_embedding_identity_semantics"]="not_speaker_identity_evidence"
                    return {"status":"cached","embedding_count":len(rows),"model":cached.get("model"),"image_id":cached.get("image_id"),"cache_path":str(cache)}
            except Exception: pass
        sources=sorted([p for p in root.iterdir() if p.is_file() and p.name.startswith("source")],key=lambda p:p.name)
        if not sources: return {"status":"unavailable","reason":"retained_source_missing"}
        ar=reconstruction.get("analysis_range") if isinstance(reconstruction.get("analysis_range"),dict) else {}; clock=reconstruction.get("source_clock") if isinstance(reconstruction.get("source_clock"),dict) else {}
        start=float(ar.get("start_seconds") or 0); end=float(ar.get("end_seconds") or clock.get("duration_seconds") or 0)
        rows,worker=self._audio_embeddings(sources[0],start_seconds=start,end_seconds=end)
        if not rows: return {"status":worker.get("status") or "unavailable","source":"retained_source","worker":worker,"embedding_count":0}
        audio["perceptual_embeddings"]=rows; audio["perceptual_embedding_policy"]="derived_from_retained_exact_source_audio; cache_sidecar_only"; audio["perceptual_embedding_identity_semantics"]="not_speaker_identity_evidence"
        payload={"schema_version":"media_derived_audio_embeddings/v1","job_id":job_id,"source":"retained_exact_source_audio","authority":"perceptual_audio_embedding_similarity_evidence_only","identity_semantics":"not_speaker_identity_evidence; audio content/timbre/structure similarity only","model":worker.get("model"),"image":worker.get("image"),"image_id":worker.get("image_id"),"worker_id":worker.get("worker_id"),"internet_required":worker.get("internet_required"),"embedding_count":len(rows),"embeddings":rows}
        try: _atomic_json(cache,payload); cache_status="written"
        except Exception as exc: cache_status="write_failed:"+type(exc).__name__
        return {"status":"derived","source":"retained_source","embedding_count":len(rows),"model":worker.get("model"),"image_id":worker.get("image_id"),"cache_path":str(cache),"cache_status":cache_status}

    def _visual_embeddings(self, anchors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Embed exact witnessed semantic-anchor JPEGs using an optional private-LAN specialist."""
        if not anchors:
            return [], {"status": "not_applicable", "anchor_count": 0}
        try:
            service = self._service("visual_embedding")
        except Exception as exc:
            return [], {"status": "unavailable", "error": type(exc).__name__, "detail": str(exc)[:300]}
        if not service:
            return [], {"status": "unavailable", "anchor_count": len(anchors)}
        candidate, record = service["candidate"], service["record"]
        endpoint = str(candidate.get("service_endpoint") or "").rstrip("/")
        path = str(record.get("embed_path") or "/embed/batch")
        if not path.startswith("/"):
            path = "/" + path
        model = str(record.get("model") or "unknown")
        expected_dims = int(record.get("dimensions") or 0)
        batch_size = max(1, min(16, int(record.get("batch_size") or 12)))
        output: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []

        for bi, start in enumerate(range(0, len(anchors), batch_size)):
            batch = anchors[start:start + batch_size]
            try:
                images: list[str] = []
                for row in batch:
                    path_obj = Path(str(row.get("image_path") or ""))
                    raw = path_obj.read_bytes()
                    if not raw:
                        raise ValueError("empty_anchor_image")
                    images.append(base64.b64encode(raw).decode("ascii"))
                with httpx.Client(timeout=httpx.Timeout(180.0, connect=5.0), trust_env=False) as client:
                    response = client.post(endpoint + path, json={"images_b64": images, "normalize": True})
                    response.raise_for_status()
                    payload = response.json()
                items = payload.get("items") if isinstance(payload, dict) else None
                if not isinstance(items, list) or len(items) != len(batch):
                    raise RuntimeError("visual_embedding_batch_cardinality_mismatch")
                for anchor_row, item in zip(batch, items):
                    if not isinstance(item, dict):
                        raise RuntimeError("visual_embedding_item_invalid")
                    raw_vec = item.get("embedding")
                    if not isinstance(raw_vec, list) or not raw_vec:
                        raise RuntimeError("visual_embedding_vector_missing")
                    vector = np.asarray(raw_vec, dtype=np.float32)
                    if vector.ndim != 1 or not np.all(np.isfinite(vector)):
                        raise RuntimeError("visual_embedding_vector_invalid")
                    if expected_dims and int(vector.size) != expected_dims:
                        raise RuntimeError("visual_embedding_dimensions_mismatch")
                    norm = float(np.linalg.norm(vector))
                    if norm <= 1e-12:
                        raise RuntimeError("visual_embedding_zero_vector")
                    vector = vector / norm
                    output.append({
                        "anchor_index": int(anchor_row.get("anchor_index") or 0),
                        "sample_index": int(anchor_row.get("sample_index") or 0),
                        "time_seconds": round(float(anchor_row.get("time_seconds") or 0), 6),
                        "input_digest": item.get("input_digest"),
                        "embedding": [round(float(value), 8) for value in vector.tolist()],
                        "dimensions": int(vector.size),
                        "model": str(payload.get("model") or model) if isinstance(payload, dict) else model,
                        "normalized": True,
                        "provenance": {
                            "source": "media_reconstruction",
                            "extractor": "visual_perceptual_embedding",
                            "worker_id": candidate.get("node_id"),
                            "service": "visual_embedding",
                            "endpoint_scope": candidate.get("service_endpoint_scope"),
                            "model": str(payload.get("model") or model) if isinstance(payload, dict) else model,
                            "authority": "perceptual_embedding_similarity_evidence_only",
                            "identity_semantics": "not_person_identity_evidence; visual appearance/composition/content similarity only",
                            "evidence": "exact_sampled_frame",
                            "internet_required": bool(record.get("internet_required", False)),
                        },
                    })
            except Exception as exc:
                failures.append({
                    "batch_index": bi,
                    "start_anchor_index": start,
                    "batch_size": len(batch),
                    "error": type(exc).__name__,
                    "detail": str(exc)[:300],
                })

        status = "completed" if output and not failures else ("partial" if output else "failed")
        return output, {
            "status": status,
            "worker_id": candidate.get("node_id"),
            "model": model,
            "image": record.get("image"),
            "image_id": record.get("image_id"),
            "dimensions": expected_dims or (len(output[0]["embedding"]) if output else None),
            "normalized": True,
            "anchor_count": len(anchors),
            "embedded_count": len(output),
            "failed_batch_count": len(failures),
            "failures": failures[:16],
            "internet_required": bool(record.get("internet_required", False)),
            "authority": "perceptual_embedding_similarity_evidence_only",
            "identity_semantics": "not_person_identity_evidence",
        }

    @staticmethod
    def _catalog_has_audio_embedding(catalog: dict[str, Any] | None) -> bool:
        if not isinstance(catalog, dict):
            return False
        for row in list(catalog.get("motifs") or []) + list(catalog.get("salient_candidates") or []):
            if not isinstance(row, dict):
                continue
            proto = row.get("prototype") if isinstance(row.get("prototype"), dict) else {}
            sketch = proto.get("measured_sketch") if isinstance(proto.get("measured_sketch"), dict) else {}
            if isinstance(sketch.get("audio_embedding_centroid"), list) and sketch.get("audio_embedding_centroid"):
                return True
        return False

    @staticmethod
    def _catalog_has_ml_note_events(catalog: dict[str, Any] | None) -> bool:
        if not isinstance(catalog, dict):
            return False
        for row in list(catalog.get("motifs") or []):
            for occ in row.get("occurrences") or []:
                if isinstance(occ, dict) and (occ.get("window_evidence") or {}).get("ml_notes"):
                    return True
        for row in list(catalog.get("salient_candidates") or []):
            if isinstance(row, dict) and (row.get("window_evidence") or {}).get("ml_notes"):
                return True
        return False

    @staticmethod
    def _catalog_has_visual_embedding(catalog: dict[str, Any] | None) -> bool:
        if not isinstance(catalog, dict):
            return False
        for row in list(catalog.get("motifs") or []) + list(catalog.get("salient_candidates") or []):
            if not isinstance(row, dict):
                continue
            proto = row.get("prototype") if isinstance(row.get("prototype"), dict) else {}
            sketch = proto.get("measured_sketch") if isinstance(proto.get("measured_sketch"), dict) else {}
            if isinstance(sketch.get("visual_embedding_centroid"), list) and sketch.get("visual_embedding_centroid"):
                return True
        return False

    def _ensure_visual_embeddings_for_reconstruction(
        self,
        job_id: str,
        reconstruction: dict[str, Any],
    ) -> dict[str, Any]:
        """Attach cached/derived DINO evidence to an in-memory reconstruction without rewriting result.json."""
        visual = reconstruction.get("visual") if isinstance(reconstruction.get("visual"), dict) else {}
        existing = visual.get("perceptual_embeddings")
        if isinstance(existing, list) and existing:
            return {
                "status": "present",
                "source": "witness",
                "embedding_count": len(existing),
                "model": existing[0].get("model") if isinstance(existing[0], dict) else None,
            }

        root = self._job_root(job_id)
        cache_path = root / "derived_visual_embeddings.json"
        if cache_path.is_file():
            try:
                cached = json.loads(cache_path.read_text())
                rows = cached.get("embeddings") if isinstance(cached, dict) else None
                if isinstance(rows, list) and rows:
                    visual["perceptual_embeddings"] = rows
                    visual["perceptual_embedding_policy"] = "derived_from_retained_exact_anchor_jpegs; cache_sidecar_only"
                    visual["perceptual_embedding_identity_semantics"] = "not_person_identity_evidence"
                    return {
                        "status": "cached",
                        "source": "derived_sidecar",
                        "embedding_count": len(rows),
                        "model": cached.get("model"),
                        "image_id": cached.get("image_id"),
                        "cache_path": str(cache_path),
                    }
            except Exception:
                pass

        semantic = [row for row in (visual.get("semantic_anchors") or []) if isinstance(row, dict)]
        anchor_rows: list[dict[str, Any]] = []
        for row in semantic:
            try:
                anchor_index = int(row.get("anchor_index"))
            except Exception:
                continue
            image_path = root / "anchors" / f"anchor-{anchor_index:04d}.jpg"
            if not image_path.is_file():
                continue
            anchor_rows.append({
                "anchor_index": anchor_index,
                "sample_index": int(row.get("sample_index") or 0),
                "time_seconds": float(row.get("time_seconds") or 0),
                "image_path": str(image_path),
            })
        if not anchor_rows:
            return {"status": "unavailable", "source": "retained_anchors", "reason": "no_anchor_mapping"}

        embeddings, worker = self._visual_embeddings(anchor_rows)
        if not embeddings:
            return {
                "status": worker.get("status") or "unavailable",
                "source": "retained_anchors",
                "worker": worker,
                "embedding_count": 0,
            }
        visual["perceptual_embeddings"] = embeddings
        visual["perceptual_embedding_policy"] = "derived_from_retained_exact_anchor_jpegs; cache_sidecar_only"
        visual["perceptual_embedding_identity_semantics"] = "not_person_identity_evidence"
        payload = {
            "schema_version": "media_derived_visual_embeddings/v1",
            "job_id": job_id,
            "source": "retained_exact_anchor_jpegs",
            "authority": "perceptual_embedding_similarity_evidence_only",
            "identity_semantics": "not_person_identity_evidence",
            "model": worker.get("model"),
            "image": worker.get("image"),
            "image_id": worker.get("image_id"),
            "worker_id": worker.get("worker_id"),
            "internet_required": worker.get("internet_required"),
            "embedding_count": len(embeddings),
            "embeddings": embeddings,
        }
        try:
            tmp = cache_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            tmp.replace(cache_path)
            cache_status = "written"
        except Exception as exc:
            cache_status = "write_failed:" + type(exc).__name__
        return {
            "status": "derived",
            "source": "retained_anchors",
            "embedding_count": len(embeddings),
            "model": worker.get("model"),
            "image_id": worker.get("image_id"),
            "worker": worker,
            "cache_status": cache_status,
            "cache_path": str(cache_path),
        }

    def _vision_schema(self) -> dict[str, Any]:
        bbox = {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}
        string_array = {"type": "array", "items": {"type": "string"}, "maxItems": 12}
        person = {"type": "object", "properties": {
            "local_id": {"type": "string"}, "visible_skin_tone": {"type": "string"}, "hair": {"type": "string"},
            "clothing": string_array, "footwear": string_array, "accessories": string_array, "appearance_details": string_array,
            "pose": {"type": "string"}, "body_orientation": {"type": "string"}, "face_direction": {"type": "string"},
            "gaze_direction": {"type": "string"}, "facial_expression": {"type": "string"}, "action": {"type": "string"},
            "interaction": {"type": "string"}, "hand_state": {"type": "string"}, "held_objects": string_array,
            "occlusion": {"type": "string"}, "bbox": bbox, "confidence": {"type": "number"}},
            "required": ["local_id", "visible_skin_tone", "hair", "clothing", "pose", "action", "held_objects", "bbox", "confidence"]}
        obj = {"type": "object", "properties": {
            "name": {"type": "string"}, "attributes": string_array, "color": {"type": "string"}, "material": {"type": "string"},
            "state": {"type": "string"}, "position": {"type": "string"}, "relation": {"type": "string"}, "occlusion": {"type": "string"},
            "bbox": bbox, "confidence": {"type": "number"}}, "required": ["name", "attributes", "bbox", "confidence"]}
        text_region = {"type": "object", "properties": {"text": {"type": "string"}, "location": {"type": "string"}, "bbox": bbox, "confidence": {"type": "number"}}, "required": ["text", "bbox", "confidence"]}
        frame = {"type": "object", "properties": {
            "frame_id": {"type": "string"}, "people": {"type": "array", "items": person, "maxItems": 16}, "objects": {"type": "array", "items": obj, "maxItems": 48},
            "setting": {"type": "string"}, "foreground": {"type": "string"}, "background": {"type": "string"},
            "dominant_colors": string_array, "spatial_relations": string_array, "lighting": {"type": "string"},
            "camera_shot": {"type": "string"}, "camera_angle": {"type": "string"}, "camera_motion": {"type": "string"},
            "visible_text": string_array, "text_regions": {"type": "array", "items": text_region, "maxItems": 24}, "overall_action": {"type": "string"},
            "quality_issues": string_array, "confidence": {"type": "number"}},
            "required": ["frame_id", "people", "objects", "setting", "lighting", "camera_shot", "camera_motion", "visible_text", "overall_action", "confidence"]}
        return {"type": "object", "properties": {"frames": {"type": "array", "items": frame}}, "required": ["frames"]}

    def _vision_semantics(self, anchors: list[dict[str, Any]], progress: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        service = self._service("vision")
        if not service or not anchors:
            return [], {"status": "unavailable"}
        candidate, record = service["candidate"], service["record"]
        endpoint = str(candidate.get("service_endpoint") or "").rstrip("/")
        path = str(record.get("inference_path") or "/api/generate")
        if not path.startswith("/"):
            path = "/" + path
        model = str(record.get("model") or "gemma3:4b")
        output: list[dict[str, Any]] = []
        batches = [anchors[i:i + 3] for i in range(0, len(anchors), 3)]
        fallback_batches = 0
        fallback_frames = 0

        def prompt_for(frame_ids: list[str]) -> str:
            return (
                "Analyze each supplied frame independently for reconstruction-grade temporal witnessing. Return the frame_id exactly. "
                "Describe everything visibly supported: every person, neutral visible skin-tone color description (do NOT infer race/ethnicity/nationality), hair color/length/style, clothing colors/items, footwear, accessories, pose/body orientation, face and gaze direction, visible facial expression, hand state, held objects, interactions, occlusion and action; furniture and room/scene objects including couches/chairs/tables; object name/color/material/state/position/attributes/occlusion and spatial relations; foreground/background, dominant colors, setting, lighting, camera shot/angle/motion, visible text/OCR with regions, image quality issues and overall action. "
                "Bounding boxes are normalized [x,y,w,h] from 0 to 1. Do not identify people or infer race, ethnicity, nationality, religion, health, sexuality, intent, off-screen facts, dialogue or audio. Describe only visible evidence; keep uncertain fields literal and lower confidence. Frame IDs: " + ", ".join(frame_ids)
            )

        def infer(client: httpx.Client, batch: list[dict[str, Any]], *, num_predict: int) -> tuple[dict[str, dict[str, Any]], str | None]:
            images = [base64.b64encode(Path(a["image_path"]).read_bytes()).decode("ascii") for a in batch]
            frame_ids = [f"f{int(a['anchor_index']):04d}@{float(a['time_seconds']):.3f}s" for a in batch]
            payload = {"model": model, "prompt": prompt_for(frame_ids), "stream": False, "images": images, "format": self._vision_schema(), "options": {"temperature": 0, "num_predict": num_predict}}
            response = client.post(endpoint + path, json=payload)
            response.raise_for_status()
            raw = response.json()
            content = raw.get("response") if isinstance(raw, dict) else None
            try:
                decoded = json.loads(content) if isinstance(content, str) else raw
            except json.JSONDecodeError as exc:
                return {}, f"{type(exc).__name__}: {str(exc)[:240]}"
            frames = decoded.get("frames") if isinstance(decoded, dict) else None
            if not isinstance(frames, list):
                return {}, "structured_response_missing_frames"
            frames = [f for f in frames if isinstance(f, dict)]
            by_id = {str(f.get("frame_id") or ""): f for f in frames if str(f.get("frame_id") or "")}
            # Structured-model frame IDs are advisory. When cardinality is exact, preserve ordered
            # one-to-one evidence instead of discarding valid semantics because the model omitted or
            # normalized an ID differently. The runtime overwrites frame_id with the witnessed anchor ID.
            if len(frames) == len(frame_ids):
                for expected, frame in zip(frame_ids, frames):
                    by_id.setdefault(expected, frame)
            return by_id, None

        with httpx.Client(timeout=httpx.Timeout(180.0, connect=5.0), trust_env=False) as client:
            for bi, batch in enumerate(batches):
                frame_ids = [f"f{int(a['anchor_index']):04d}@{float(a['time_seconds']):.3f}s" for a in batch]
                by_id, parse_error = infer(client, batch, num_predict=2600)
                if parse_error or any(fid not in by_id for fid in frame_ids):
                    fallback_batches += 1
                    recovered: dict[str, dict[str, Any]] = {}
                    for anchor, frame_id in zip(batch, frame_ids):
                        one, one_error = infer(client, [anchor], num_predict=3200)
                        if frame_id in one:
                            recovered[frame_id] = one[frame_id]
                            fallback_frames += 1
                        elif one_error:
                            recovered[frame_id] = {"confidence": 0.0, "quality_issues": ["vision_structured_output_failed"], "vision_parse_error": one_error}
                    by_id = recovered
                for frame_id, anchor in zip(frame_ids, batch):
                    f = dict(by_id.get(frame_id) or {})
                    f.update({
                        "frame_id": frame_id,
                        "anchor_index": int(anchor["anchor_index"]),
                        "time_seconds": float(anchor["time_seconds"]),
                        "sample_index": int(anchor["sample_index"]),
                        "provenance": {"source": "media_reconstruction", "extractor": "vision_temporal_anchor", "model": model, "worker_id": candidate.get("node_id"), "authority": "observed_or_inferred_evidence_only", "evidence": "exact_sampled_frame", "structured_fallback": bool(parse_error or fallback_batches)},
                    })
                    output.append(f)
                progress("vision_semantics", 0.30 + 0.35 * ((bi + 1) / max(1, len(batches))))
        return output, {"status": "completed", "worker_id": candidate.get("node_id"), "model": model, "anchor_count": len(output), "batch_count": len(batches), "structured_fallback_batches": fallback_batches, "structured_fallback_frames": fallback_frames}

    def _normalize_transcription_audio(self, source: Path) -> Path:
        target = source.parent / "transcription-16k-mono.wav"
        self._run([
            "ffmpeg", "-v", "error", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", "-y", str(target),
        ], timeout=900)
        return target

    def _transcription(self, source: Path, mime_type: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        service = self._service("transcription")
        if not service:
            return None, {"status": "unavailable"}
        candidate, record = service["candidate"], service["record"]
        endpoint = str(candidate.get("service_endpoint") or "").rstrip("/")
        path = str(record.get("inference_path") or "/inference")
        if not path.startswith("/"):
            path = "/" + path
        normalized = self._normalize_transcription_audio(source)
        retryable = (
            httpx.RemoteProtocolError, httpx.ConnectError, httpx.ConnectTimeout,
            httpx.ReadError, httpx.ReadTimeout, httpx.WriteError, httpx.PoolTimeout,
        )
        attempts = 0
        last_error: Exception | None = None
        while attempts < 2:
            attempts += 1
            try:
                with normalized.open("rb") as fh, httpx.Client(timeout=httpx.Timeout(3600.0, connect=5.0), trust_env=False) as client:
                    response = client.post(
                        endpoint + path,
                        files={"file": (normalized.name, fh, "audio/wav")},
                        data={"response_format": "verbose_json"},
                    )
                    if response.status_code >= 500 and attempts < 2:
                        last_error = httpx.HTTPStatusError(
                            f"transcription worker returned {response.status_code}",
                            request=response.request, response=response,
                        )
                        continue
                    response.raise_for_status()
                    payload = response.json()
                return payload, {
                    "status": "completed",
                    "worker_id": candidate.get("node_id"),
                    "model": record.get("model"),
                    "image": record.get("image"),
                    "image_id": record.get("image_id"),
                    "response_format": "verbose_json",
                    "normalized_audio": True,
                    "normalized_format": "wav_pcm_s16le_16khz_mono",
                    "attempts": attempts,
                    "retried": attempts > 1,
                }
            except retryable as exc:
                last_error = exc
                if attempts >= 2:
                    raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("transcription_request_failed")

    def _music_transcription(self, source: Path, mime_type: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Return optional polyphonic ML note events without replacing deterministic spectral evidence."""
        try:
            service = self._service("music_transcription")
        except Exception as exc:
            return [], {"status": "unavailable", "error": type(exc).__name__, "detail": str(exc)[:300]}
        if not service:
            return [], {"status": "unavailable"}
        candidate, record = service["candidate"], service["record"]
        endpoint = str(candidate.get("service_endpoint") or "").rstrip("/")
        path = str(record.get("inference_path") or "/transcribe")
        if not path.startswith("/"):
            path = "/" + path
        model = str(record.get("model") or "spotify/basic-pitch")
        try:
            with source.open("rb") as fh, httpx.Client(timeout=httpx.Timeout(600.0, connect=5.0), trust_env=False) as client:
                response = client.post(
                    endpoint + path,
                    files={"file": (source.name, fh, mime_type or "application/octet-stream")},
                )
                response.raise_for_status()
                payload = response.json()
            if not isinstance(payload, dict) or payload.get("schema_version") != "xavi_polyphonic_note_events/v1":
                raise RuntimeError("music_transcription_schema_mismatch")
            events: list[dict[str, Any]] = []
            for row in payload.get("notes") or []:
                if not isinstance(row, dict):
                    continue
                start = float(row.get("start_seconds") or 0)
                end = float(row.get("end_seconds") or start)
                if not math.isfinite(start) or not math.isfinite(end) or end < start:
                    continue
                midi = int(row.get("midi")) if row.get("midi") is not None else None
                activation = float(row.get("activation") or 0)
                event = {
                    "start_seconds": round(start, 6),
                    "end_seconds": round(end, 6),
                    "duration_seconds": round(max(0.0, end-start), 6),
                    "midi": midi,
                    "note": str(row.get("note") or ""),
                    "frequency_hz": round(float(row.get("frequency_hz")), 6) if row.get("frequency_hz") is not None else None,
                    "activation": round(max(0.0, min(1.0, activation)), 6),
                    "pitch_bends": row.get("pitch_bends"),
                    "provenance": {
                        "source": "media_reconstruction",
                        "extractor": "polyphonic_music_transcription",
                        "worker_id": candidate.get("node_id"),
                        "service": "music_transcription",
                        "endpoint_scope": candidate.get("service_endpoint_scope"),
                        "model": str(payload.get("model") or model),
                        "runtime": payload.get("runtime"),
                        "authority": "ml_polyphonic_music_transcription_evidence",
                        "activation_semantics": str(payload.get("activation_semantics") or "model note-event activation, not calibrated probability"),
                        "evidence": "decoded_source_audio",
                        "internet_required": bool(record.get("internet_required", False)),
                    },
                }
                events.append(event)
            return events, {
                "status": "completed",
                "worker_id": candidate.get("node_id"),
                "model": str(payload.get("model") or model),
                "runtime": payload.get("runtime") or record.get("runtime"),
                "image": record.get("image"),
                "image_id": record.get("image_id"),
                "note_event_count": len(events),
                "internet_required": bool(record.get("internet_required", False)),
                "authority": "ml_polyphonic_music_transcription_evidence",
            }
        except Exception as exc:
            return [], {
                "status": "failed",
                "worker_id": candidate.get("node_id"),
                "model": model,
                "image": record.get("image"),
                "image_id": record.get("image_id"),
                "error": type(exc).__name__,
                "detail": str(exc)[:500],
            }

    def _ensure_music_transcription_for_reconstruction(self, job_id: str, reconstruction: dict[str, Any]) -> dict[str, Any]:
        """Attach/cache Basic Pitch note events for retained exact source bytes without rewriting result.json."""
        audio = reconstruction.get("audio") if isinstance(reconstruction.get("audio"), dict) else None
        if audio is None:
            return {"status": "unavailable", "reason": "no_audio_reconstruction"}
        existing = audio.get("ml_note_events")
        if isinstance(existing, list):
            return {
                "status": "present",
                "source": "witness",
                "note_event_count": len(existing),
                "model": ((existing[0].get("provenance") or {}).get("model") if existing and isinstance(existing[0], dict) else None),
            }
        root = self._job_root(job_id)
        cache = root / "derived_music_transcription.json"
        if cache.is_file():
            try:
                payload = json.loads(cache.read_text())
                rows = payload.get("note_events") if isinstance(payload, dict) else None
                if isinstance(rows, list):
                    audio["ml_note_events"] = rows
                    audio["ml_note_event_policy"] = "derived_from_retained_exact_source_audio; separate_model_evidence; cache_sidecar_only"
                    audio["ml_note_event_authority"] = "ml_polyphonic_music_transcription_evidence"
                    return {
                        "status": "cached",
                        "source": "derived_sidecar",
                        "note_event_count": len(rows),
                        "model": payload.get("model"),
                        "image_id": payload.get("image_id"),
                        "cache_path": str(cache),
                    }
            except Exception:
                pass
        sources = sorted([p for p in root.iterdir() if p.is_file() and p.name.startswith("source")], key=lambda p:p.name)
        if not sources:
            return {"status": "unavailable", "reason": "retained_source_missing"}
        rows, worker = self._music_transcription(sources[0], "application/octet-stream")
        # Empty is still a completed observation when the worker successfully found no confident notes.
        if worker.get("status") != "completed":
            return {"status": worker.get("status") or "unavailable", "source": "retained_source", "worker": worker, "note_event_count": 0}
        audio["ml_note_events"] = rows
        audio["ml_note_event_policy"] = "derived_from_retained_exact_source_audio; separate_model_evidence; cache_sidecar_only"
        audio["ml_note_event_authority"] = "ml_polyphonic_music_transcription_evidence"
        payload = {
            "schema_version": "media_derived_polyphonic_music_transcription/v1",
            "job_id": job_id,
            "source": "retained_exact_source_audio",
            "authority": "ml_polyphonic_music_transcription_evidence",
            "activation_semantics": "model note-event activation, not calibrated probability",
            "model": worker.get("model"),
            "runtime": worker.get("runtime"),
            "image": worker.get("image"),
            "image_id": worker.get("image_id"),
            "worker_id": worker.get("worker_id"),
            "internet_required": worker.get("internet_required"),
            "note_event_count": len(rows),
            "note_events": rows,
        }
        try:
            _atomic_json(cache, payload)
            cache_status = "written"
        except Exception as exc:
            cache_status = "write_failed:" + type(exc).__name__
        return {
            "status": "derived",
            "source": "retained_source",
            "note_event_count": len(rows),
            "model": worker.get("model"),
            "image_id": worker.get("image_id"),
            "cache_path": str(cache),
            "cache_status": cache_status,
        }

    def _pcm(self, source: Path, sample_rate: int = 16000) -> np.ndarray:
        raw = self._run(["ffmpeg", "-v", "error", "-i", str(source), "-vn", "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "pipe:1"], timeout=900)
        return np.frombuffer(raw, dtype="<f4").astype(np.float32, copy=False)

    def _audio_features(self, pcm: np.ndarray, sample_rate: int = 16000) -> dict[str, Any]:
        if pcm.size < 2048:
            return {"sample_rate_hz": sample_rate, "duration_seconds": pcm.size / sample_rate, "frames": [], "onsets": [], "note_intervals": [], "chord_intervals": [], "tempo_bpm_hypothesis": None}
        n, hop = 2048, 512
        count = 1 + max(0, (len(pcm) - n) // hop)
        shape = (count, n)
        strides = (pcm.strides[0] * hop, pcm.strides[0])
        frames = np.lib.stride_tricks.as_strided(pcm, shape=shape, strides=strides).copy()
        window = np.hanning(n).astype(np.float32)
        spec = np.abs(np.fft.rfft(frames * window, axis=1)).astype(np.float32)
        freqs = np.fft.rfftfreq(n, 1.0 / sample_rate).astype(np.float32)
        rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
        mag_sum = spec.sum(axis=1) + 1e-9
        centroid = (spec * freqs[None, :]).sum(axis=1) / mag_sum
        pitch_mask = (freqs >= 55.0) & (freqs <= 1760.0)
        pitch_spec = spec[:, pitch_mask]
        pitch_freqs = freqs[pitch_mask]
        peak_idx = np.argmax(pitch_spec, axis=1)
        pitch = pitch_freqs[peak_idx]
        peak_ratio = pitch_spec[np.arange(count), peak_idx] / (pitch_spec.sum(axis=1) + 1e-9)
        diff = np.diff(spec, axis=0, prepend=spec[:1])
        flux = np.maximum(diff, 0).sum(axis=1) / mag_sum
        threshold = float(np.percentile(flux, 88)) if flux.size else 0.0
        frame_times = (np.arange(count) * hop + n / 2) / sample_rate
        onset_idx = [i for i in range(1, count - 1) if float(flux[i]) >= threshold and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1]][:1024]
        onset_times = [round(float(frame_times[i]), 4) for i in onset_idx]
        tempo = None
        if len(onset_times) >= 4:
            diffs = np.diff(onset_times)
            usable = diffs[(diffs >= 0.22) & (diffs <= 1.5)]
            if usable.size:
                bpm = 60.0 / float(np.median(usable))
                while bpm < 60:
                    bpm *= 2
                while bpm > 190:
                    bpm /= 2
                tempo = round(bpm, 2)
        notes: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for i in range(count):
            if rms[i] < 0.006 or peak_ratio[i] < 0.035:
                name = None
            else:
                name, cents = _note_name(float(pitch[i]))
            t0 = float(i * hop / sample_rate)
            t1 = float((i * hop + n) / sample_rate)
            if name and current and current["note"] == name and t0 - current["end_seconds"] <= 0.08:
                current["end_seconds"] = round(t1, 4)
                current["confidence"] = round(max(current["confidence"], min(0.99, float(peak_ratio[i]) * 5)), 4)
            else:
                if current and current["end_seconds"] - current["start_seconds"] >= 0.06:
                    notes.append(current)
                current = None if not name else {"note": name, "start_seconds": round(t0, 4), "end_seconds": round(t1, 4), "frequency_hz": round(float(pitch[i]), 2), "cents_from_equal_temperament": round(float(cents or 0), 2), "confidence": round(min(0.99, float(peak_ratio[i]) * 5), 4), "authority": "measured_pitch_hypothesis"}
        if current and current["end_seconds"] - current["start_seconds"] >= 0.06:
            notes.append(current)
        note_names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
        midi = np.zeros_like(freqs, dtype=np.int32)
        valid = freqs > 20
        midi[valid] = np.rint(69 + 12 * np.log2(freqs[valid] / 440.0)).astype(np.int32)
        pc = np.mod(midi, 12)
        chords: list[dict[str, Any]] = []
        window_frames = max(1, int(round(0.5 * sample_rate / hop)))
        for start in range(0, count, window_frames):
            end = min(count, start + window_frames)
            chroma = np.zeros(12, dtype=np.float64)
            summed = spec[start:end].sum(axis=0)
            for k in range(12):
                chroma[k] = float(summed[(pc == k) & (freqs >= 55) & (freqs <= 3520)].sum())
            total = chroma.sum()
            if total <= 1e-6:
                continue
            chroma /= total
            best = (0.0, "")
            for root in range(12):
                for quality, offs in (("maj", (0, 4, 7)), ("min", (0, 3, 7))):
                    score = float(sum(chroma[(root + o) % 12] for o in offs))
                    if score > best[0]:
                        best = (score, f"{note_names[root]}:{quality}")
            if best[0] >= 0.42:
                t0 = start * hop / sample_rate
                t1 = min(len(pcm) / sample_rate, (end * hop + n) / sample_rate)
                if chords and chords[-1]["chord"] == best[1] and t0 - chords[-1]["end_seconds"] < 0.2:
                    chords[-1]["end_seconds"] = round(t1, 4)
                    chords[-1]["confidence"] = round(max(chords[-1]["confidence"], best[0]), 4)
                else:
                    chords.append({"chord": best[1], "start_seconds": round(t0, 4), "end_seconds": round(t1, 4), "confidence": round(best[0], 4), "authority": "spectral_chroma_hypothesis"})
        summary_frames = []
        stride = max(1, int(round(0.25 * sample_rate / hop)))
        for i in range(0, count, stride):
            summary_frames.append({"time_seconds": round(float(frame_times[i]), 4), "rms": round(float(rms[i]), 6), "spectral_centroid_hz": round(float(centroid[i]), 2), "spectral_flux": round(float(flux[i]), 6), "pitch_hz": round(float(pitch[i]), 2) if rms[i] >= 0.006 else None, "pitch_confidence": round(min(1.0, float(peak_ratio[i]) * 5), 4)})
        return {"sample_rate_hz": sample_rate, "duration_seconds": round(len(pcm) / sample_rate, 6), "frames": summary_frames, "onsets": onset_times, "note_intervals": notes[:4096], "chord_intervals": chords[:2048], "tempo_bpm_hypothesis": tempo}

    def _transcript_witnesses(self, transcript: dict[str, Any] | None, audio: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not isinstance(transcript, dict):
            return [], []
        words: list[dict[str, Any]] = []
        segments: list[dict[str, Any]] = []
        audio_frames = audio.get("frames") or []
        previous_word_end: float | None = None
        for si, seg in enumerate(transcript.get("segments") or []):
            if not isinstance(seg, dict):
                continue
            start, end = float(seg.get("start") or 0), float(seg.get("end") or 0)
            seg_words = []
            for wi, w in enumerate(seg.get("words") or []):
                if not isinstance(w, dict):
                    continue
                w_start = float(w.get("start") or start)
                w_end = float(w.get("end") or w_start)
                token = str(w.get("word") or "")
                pause_before = max(0.0, w_start - previous_word_end) if previous_word_end is not None else max(0.0, w_start - start)
                stripped = token.strip()
                nonverbal = bool(re.fullmatch(r"[\[(].*[\])]", stripped))
                rec = {"word": token, "start_seconds": w_start, "end_seconds": w_end,
                       "duration_seconds": round(max(0.0, w_end - w_start), 6),
                       "pause_before_seconds": round(pause_before, 6),
                       "probability": round(float(w.get("probability") or 0), 6),
                       "token_kind": "nonverbal_caption" if nonverbal else "lexical",
                       "segment_index": si, "word_index": wi, "authority": "asr_hypothesis"}
                words.append(rec); seg_words.append(rec); previous_word_end = w_end
            in_window = [f for f in audio_frames if start <= float(f.get("time_seconds") or 0) <= max(start, end)]
            pitches = [float(f["pitch_hz"]) for f in in_window if f.get("pitch_hz")]
            rms = [float(f.get("rms") or 0) for f in in_window]
            centroid = [float(f.get("spectral_centroid_hz") or 0) for f in in_window]
            flux = [float(f.get("spectral_flux") or 0) for f in in_window]
            probs = [float(w.get("probability") or 0) for w in seg_words]
            rate = len(seg_words) / max(0.05, end - start)
            mean_rms = float(np.mean(rms)) if rms else None
            median_pitch = float(np.median(pitches)) if pitches else None
            pitch_range = float(max(pitches) - min(pitches)) if pitches else None
            pitch_std = float(np.std(pitches)) if pitches else None
            pause_total = sum(float(w.get("pause_before_seconds") or 0) for w in seg_words)
            pace_band = "slow" if rate < 1.5 else ("moderate" if rate <= 3.2 else "fast")
            energy_band = None if mean_rms is None else ("low" if mean_rms < 0.03 else ("moderate" if mean_rms < 0.12 else "high"))
            pitch_dynamics = None
            if median_pitch and pitch_std is not None:
                ratio = pitch_std / max(1.0, median_pitch)
                pitch_dynamics = "steady" if ratio < 0.06 else ("moderately_variable" if ratio < 0.16 else "highly_variable")
            delivery = {
                "mean_rms": round(mean_rms, 6) if mean_rms is not None else None,
                "median_pitch_hz": round(median_pitch, 2) if median_pitch is not None else None,
                "pitch_range_hz": round(pitch_range, 2) if pitch_range is not None else None,
                "pitch_stddev_hz": round(pitch_std, 2) if pitch_std is not None else None,
                "mean_spectral_centroid_hz": round(float(np.mean(centroid)), 2) if centroid else None,
                "mean_spectral_flux": round(float(np.mean(flux)), 6) if flux else None,
                "word_rate_per_second": round(rate, 3), "pause_total_seconds": round(pause_total, 4),
                "segment_asr_probability_mean": round(float(np.mean(probs)), 6) if probs else None,
                "segment_asr_probability_min": round(float(min(probs)), 6) if probs else None,
                "prosody": {"pace_band": pace_band, "energy_band": energy_band, "pitch_dynamics": pitch_dynamics,
                            "authority": "heuristic_labels_from_measured_acoustics"},
                "affect": {"status": "not_inferred_from_acoustics_alone", "note": "Emotion/intent is not promoted from voice measurements without independent evidence."},
                "accent": {"status": "not_geographically_inferred", "note": "Only acoustic/phonetic measurements are retained; ethnicity/nationality are not inferred from voice."},
            }
            segments.append({"segment_index": si, "text": str(seg.get("text") or "").strip(), "start_seconds": start,
                             "end_seconds": end, "duration_seconds": round(max(0.0, end-start), 6), "words": seg_words,
                             "delivery": delivery, "authority": "asr_and_acoustic_hypothesis"})
        return words, segments

    def _state_intervals(self, anchors: list[dict[str, Any]], fps: float, duration: float) -> list[dict[str, Any]]:
        if not anchors:
            return []
        rows = sorted(anchors, key=lambda x: float(x.get("time_seconds") or 0))
        out = []
        for i, row in enumerate(rows):
            start = float(row.get("time_seconds") or 0)
            end = float(rows[i + 1].get("time_seconds") or duration) if i + 1 < len(rows) else duration
            out.append({
                "start_seconds": round(start, 6), "end_seconds": round(max(start, end), 6),
                "start_frame": int(round(start * fps)), "end_frame": max(int(round(start * fps)), int(round(max(start, end) * fps)) - 1),
                "anchor_frame_id": row.get("frame_id"), "state": {k: row.get(k) for k in ("people", "objects", "setting", "foreground", "background", "dominant_colors", "spatial_relations", "lighting", "camera_shot", "camera_angle", "camera_motion", "visible_text", "text_regions", "overall_action", "quality_issues", "confidence")},
                "gate": {"schema_version": GATE_SCHEMA, "state": "held_until_next_semantic_change", "anchor_authority": "observed_sampled_frame", "between_anchor_authority": "inferred_state_persistence", "confidence_decay": "bounded_by_next_anchor"},
            })
        return out

    def _entity_tracks(self, vision: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Associate nearby semantic-anchor observations without attempting identity recognition.

        Tracks are deliberately ephemeral reconstruction aids. They use only visible descriptors,
        object category, normalized bounding-box continuity and temporal proximity, and must never
        be interpreted as a biometric/person identity claim.
        """
        tracks: list[dict[str, Any]] = []
        next_id = {"person": 1, "object": 1}

        def norm_tokens(values: list[Any]) -> set[str]:
            text = " ".join(str(v or "") for v in values).lower()
            return {tok for tok in re.findall(r"[a-z0-9]+", text) if len(tok) > 1}

        def center(bbox: Any) -> tuple[float, float] | None:
            if not isinstance(bbox, list) or len(bbox) != 4:
                return None
            try:
                x,y,w,h=(float(v) for v in bbox)
                return x+w/2.0, y+h/2.0
            except Exception:
                return None

        def distance(a: Any, b: Any) -> float | None:
            ca,cb=center(a),center(b)
            if ca is None or cb is None: return None
            return math.hypot(ca[0]-cb[0], ca[1]-cb[1])

        def descriptor(kind: str, item: dict[str, Any]) -> set[str]:
            if kind == "person":
                return norm_tokens([
                    item.get("hair"), *(item.get("clothing") or []), *(item.get("footwear") or []),
                    *(item.get("accessories") or []), *(item.get("appearance_details") or []),
                ])
            return norm_tokens([
                item.get("name"), item.get("color"), item.get("material"), item.get("state"),
                *(item.get("attributes") or []),
            ])

        def match_score(track: dict[str, Any], kind: str, item: dict[str, Any], t: float) -> float:
            if track["kind"] != kind or t < track["end_seconds"] or t-track["end_seconds"] > 6.0:
                return -1.0
            if kind == "object":
                a=str(track.get("canonical_name") or "").strip().lower()
                b=str(item.get("name") or "").strip().lower()
                if a and b and a != b:
                    return -1.0
            old=set(track.get("descriptor_tokens") or [])
            new=descriptor(kind,item)
            union=old|new
            jacc=(len(old&new)/len(union)) if union else 0.0
            dist=distance(track.get("last_bbox"), item.get("bbox"))
            spatial=0.0 if dist is None else max(0.0, 1.0-min(1.0,dist/0.45))
            # Object category agreement is strong evidence; person continuation requires visual/spatial support.
            category=0.35 if kind=="object" and str(track.get("canonical_name") or "").strip().lower()==str(item.get("name") or "").strip().lower() and item.get("name") else 0.0
            return 0.55*jacc + 0.45*spatial + category

        for frame in sorted((f for f in vision if isinstance(f,dict)), key=lambda x: float(x.get("time_seconds") or 0)):
            t=float(frame.get("time_seconds") or 0)
            for kind,key in (("person","people"),("object","objects")):
                for item in frame.get(key) or []:
                    if not isinstance(item,dict): continue
                    candidates=[(match_score(track,kind,item,t),track) for track in tracks]
                    score,chosen=max(candidates,key=lambda x:x[0],default=(-1.0,None))
                    threshold=0.43 if kind=="person" else 0.50
                    if chosen is None or score < threshold:
                        track_id=f"{kind}-track-{next_id[kind]:04d}"
                        next_id[kind]+=1
                        tokens=descriptor(kind,item)
                        chosen={
                            "track_id":track_id,"kind":kind,"authority":"ephemeral_visual_association_hypothesis",
                            "identity_claim":False,"start_seconds":round(t,6),"end_seconds":round(t,6),
                            "canonical_name":str(item.get("name") or "") if kind=="object" else "person",
                            "descriptor_tokens":sorted(tokens),"last_bbox":item.get("bbox"),"observations":[],
                        }
                        tracks.append(chosen)
                    else:
                        chosen["end_seconds"]=round(t,6)
                        chosen["descriptor_tokens"]=sorted(set(chosen.get("descriptor_tokens") or [])|descriptor(kind,item))
                        chosen["last_bbox"]=item.get("bbox")
                    item["ephemeral_track_id"]=chosen["track_id"]
                    state_keys = (
                        ("action","pose","body_orientation","face_direction","gaze_direction","facial_expression","hand_state","held_objects","interaction","occlusion")
                        if kind == "person"
                        else ("name","state","position","relation","attributes","color","material","occlusion")
                    )
                    chosen["observations"].append({
                        "time_seconds":round(t,6),"frame_id":frame.get("frame_id"),"bbox":item.get("bbox"),
                        "confidence":round(float(item.get("confidence") or frame.get("confidence") or 0),6),
                        "local_id":item.get("local_id") if kind=="person" else None,
                        "state": {key:item.get(key) for key in state_keys},
                    })

        def bbox_center_and_area(bbox: Any) -> tuple[tuple[float,float] | None, float | None]:
            if not isinstance(bbox,list) or len(bbox)!=4:
                return None,None
            try:
                x,y,w,h=(float(v) for v in bbox)
                return (x+w/2.0,y+h/2.0), max(0.0,w*h)
            except Exception:
                return None,None

        def screen_direction(dx: float, dy: float, distance_value: float) -> str:
            if distance_value < 0.004:
                return "stationary_or_below_resolution"
            horizontal = "right" if dx > 0.003 else ("left" if dx < -0.003 else "")
            vertical = "down" if dy > 0.003 else ("up" if dy < -0.003 else "")
            return "-".join(v for v in (vertical,horizontal) if v) or "small_motion"

        def norm_state_value(value: Any) -> Any:
            if isinstance(value,list):
                return sorted(str(v).strip() for v in value if str(v).strip())
            if isinstance(value,dict):
                return json.dumps(value,sort_keys=True,ensure_ascii=False)
            if value is None:
                return None
            return str(value).strip()

        for track in tracks:
            observations=sorted(track["observations"],key=lambda row:float(row.get("time_seconds") or 0))
            track["observations"]=observations
            path_length=0.0
            direction_counts:dict[str,int]={}
            state_transitions:list[dict[str,Any]]=[]
            moving_steps=0
            previous=None
            for obs in observations:
                center_now,area_now=bbox_center_and_area(obs.get("bbox"))
                if center_now is not None:
                    obs["center_normalized"]={"x":round(center_now[0],6),"y":round(center_now[1],6)}
                if previous is not None:
                    center_prev,area_prev=bbox_center_and_area(previous.get("bbox"))
                    dt=max(0.0,float(obs.get("time_seconds") or 0)-float(previous.get("time_seconds") or 0))
                    if center_prev is not None and center_now is not None and dt>0:
                        dx=center_now[0]-center_prev[0]
                        dy=center_now[1]-center_prev[1]
                        distance_value=math.hypot(dx,dy)
                        direction=screen_direction(dx,dy,distance_value)
                        speed=distance_value/dt
                        area_ratio=(area_now/area_prev) if area_now is not None and area_prev and area_prev>1e-12 else None
                        motion={
                            "from_time_seconds":round(float(previous.get("time_seconds") or 0),6),
                            "to_time_seconds":round(float(obs.get("time_seconds") or 0),6),
                            "dt_seconds":round(dt,6),
                            "dx_normalized":round(dx,6),"dy_normalized":round(dy,6),
                            "distance_normalized":round(distance_value,6),
                            "speed_normalized_per_second":round(speed,6),
                            "screen_direction":direction,
                            "bbox_area_ratio":round(area_ratio,6) if area_ratio is not None else None,
                            "confidence":round(min(float(previous.get("confidence") or 0),float(obs.get("confidence") or 0)),6),
                            "authority":"screen_space_delta_from_semantic_bbox_hypotheses",
                            "coordinate_space":"normalized_frame_xy_y_down",
                        }
                        obs["motion_from_previous"]=motion
                        path_length+=distance_value
                        direction_counts[direction]=direction_counts.get(direction,0)+1
                        if direction!="stationary_or_below_resolution":
                            moving_steps+=1

                    previous_state=previous.get("state") if isinstance(previous.get("state"),dict) else {}
                    current_state=obs.get("state") if isinstance(obs.get("state"),dict) else {}
                    all_keys=sorted(set(previous_state)|set(current_state))
                    for field in all_keys:
                        before=norm_state_value(previous_state.get(field))
                        after=norm_state_value(current_state.get(field))
                        if before==after:
                            continue
                        transition={
                            "track_id":track["track_id"],"kind":track["kind"],"field":field,
                            "from_time_seconds":round(float(previous.get("time_seconds") or 0),6),
                            "to_time_seconds":round(float(obs.get("time_seconds") or 0),6),
                            "before":previous_state.get(field),"after":current_state.get(field),
                            "authority":"semantic_anchor_state_delta_hypothesis",
                            "time_semantics":"change occurred sometime after from anchor and was observed by to anchor",
                        }
                        if field=="held_objects":
                            a=set(norm_state_value(previous_state.get(field)) or [])
                            b=set(norm_state_value(current_state.get(field)) or [])
                            transition["added"]=sorted(b-a)
                            transition["removed"]=sorted(a-b)
                            transition["transition_kind"]="held_object_change"
                        else:
                            transition["transition_kind"]="entity_state_change"
                        state_transitions.append(transition)
                previous=obs

            first_center,_=bbox_center_and_area(observations[0].get("bbox")) if observations else (None,None)
            last_center,_=bbox_center_and_area(observations[-1].get("bbox")) if observations else (None,None)
            if first_center is not None and last_center is not None:
                net_dx=last_center[0]-first_center[0]
                net_dy=last_center[1]-first_center[1]
                net_distance=math.hypot(net_dx,net_dy)
                net_direction=screen_direction(net_dx,net_dy,net_distance)
            else:
                net_dx=net_dy=net_distance=0.0
                net_direction="unknown"
            dominant_direction=max(direction_counts,key=direction_counts.get) if direction_counts else "unknown"
            track["trajectory"]={
                "coordinate_space":"normalized_frame_xy_y_down",
                "path_length_normalized":round(path_length,6),
                "net_dx_normalized":round(net_dx,6),"net_dy_normalized":round(net_dy,6),
                "net_displacement_normalized":round(net_distance,6),
                "net_screen_direction":net_direction,
                "dominant_step_direction":dominant_direction,
                "moving_step_count":moving_steps,
                "measured_step_count":max(0,len(observations)-1),
                "authority":"screen_space_trajectory_from_semantic_bbox_hypotheses",
                "identity_claim":False,
            }
            track["state_transitions"]=state_transitions
            track["state_transition_count"]=len(state_transitions)
            track["observation_count"]=len(observations)
            track["duration_seconds"]=round(max(0.0,float(track["end_seconds"])-float(track["start_seconds"])),6)
            track.pop("last_bbox",None)
        return tracks

    def _temporal_transitions(self, vision: list[dict[str, Any]], tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build explicit bounded-time delta witnesses without pretending unsampled instants are known."""
        events:list[dict[str,Any]]=[]

        def add(kind:str, *, from_time:float, to_time:float, payload:dict[str,Any], authority:str) -> None:
            events.append({
                "schema_version":TEMPORAL_SCHEMA,
                "transition_type":kind,
                "from_time_seconds":round(float(from_time),6),
                "to_time_seconds":round(float(to_time),6),
                "observed_by_seconds":round(float(to_time),6),
                "transition_window_seconds":{"start_seconds":round(float(from_time),6),"end_seconds":round(float(to_time),6)},
                "time_semantics":"bounded interval; exact change instant is not asserted unless both bounds are identical",
                "authority":authority,
                **payload,
            })

        for track in tracks:
            observations=track.get("observations") or []
            if observations:
                first=float(observations[0].get("time_seconds") or 0)
                add("track_presence_started",from_time=first,to_time=first,payload={"track_id":track.get("track_id"),"entity_kind":track.get("kind")},authority="semantic_anchor_presence_hypothesis")
                last=float(observations[-1].get("time_seconds") or first)
                if last>first:
                    add("track_presence_last_observed",from_time=last,to_time=last,payload={"track_id":track.get("track_id"),"entity_kind":track.get("kind")},authority="semantic_anchor_presence_hypothesis")
            for obs in observations:
                motion=obs.get("motion_from_previous")
                if not isinstance(motion,dict):
                    continue
                if float(motion.get("distance_normalized") or 0)<0.001:
                    continue
                add(
                    "screen_space_motion",
                    from_time=float(motion.get("from_time_seconds") or 0),
                    to_time=float(motion.get("to_time_seconds") or 0),
                    payload={"track_id":track.get("track_id"),"entity_kind":track.get("kind"),"delta":motion},
                    authority="screen_space_delta_from_semantic_bbox_hypotheses",
                )
            for change in track.get("state_transitions") or []:
                if not isinstance(change,dict):
                    continue
                add(
                    str(change.get("transition_kind") or "entity_state_change"),
                    from_time=float(change.get("from_time_seconds") or 0),
                    to_time=float(change.get("to_time_seconds") or 0),
                    payload={"track_id":track.get("track_id"),"entity_kind":track.get("kind"),"field":change.get("field"),
                             "before":change.get("before"),"after":change.get("after"),
                             "added":change.get("added"),"removed":change.get("removed")},
                    authority="semantic_anchor_state_delta_hypothesis",
                )

        rows=sorted((row for row in vision if isinstance(row,dict)),key=lambda x:float(x.get("time_seconds") or 0))
        scene_fields=("setting","foreground","background","lighting","camera_shot","camera_angle","camera_motion","overall_action","visible_text")
        for previous,current in zip(rows,rows[1:]):
            t0=float(previous.get("time_seconds") or 0)
            t1=float(current.get("time_seconds") or t0)
            for field in scene_fields:
                before=previous.get(field)
                after=current.get(field)
                def canon(value:Any)->str:
                    if isinstance(value,(list,dict)):
                        return json.dumps(value,sort_keys=True,ensure_ascii=False)
                    return str(value or "").strip()
                if canon(before)==canon(after):
                    continue
                add(
                    "scene_state_change",
                    from_time=t0,to_time=t1,
                    payload={"field":field,"before":before,"after":after,
                             "from_frame_id":previous.get("frame_id"),"to_frame_id":current.get("frame_id")},
                    authority="semantic_anchor_scene_delta_hypothesis",
                )
        events.sort(key=lambda row:(float(row.get("to_time_seconds") or 0),str(row.get("transition_type") or ""),str(row.get("track_id") or "")))
        return events

    def _comparison_signatures(
        self,
        vision: list[dict[str, Any]],
        transcript_segments: list[dict[str, Any]],
        audio: dict[str, Any],
        tracks: list[dict[str, Any]],
        transitions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build source-independent tokens for comparing witnessed media timelines.

        Ephemeral track ids and model-specific identities are intentionally excluded
        from the canonical token stream. Tokens summarize *what happened* and retain
        modality/authority separately from the canonical SHAKE256-512 signature.
        """
        tokens: list[str] = []
        families: dict[str, list[str]] = {
            "visual_context": [],
            "motion": [],
            "state_change": [],
            "scene_change": [],
            "speech_text": [],
            "speech_prosody": [],
            "music": [],
        }

        def norm_text(value: Any, limit: int = 96) -> str:
            text = re.sub(r"\s+", " ", str(value or "").strip().lower())
            text = re.sub(r"[^a-z0-9+#.' _:=><-]+", "", text)
            return text[:limit].strip()

        def add(family: str, token: str) -> None:
            token = norm_text(token, 180)
            if not token:
                return
            full = f"{family}:{token}"
            if full not in tokens:
                tokens.append(full)
            if token not in families[family]:
                families[family].append(token)

        def band(value: float, cuts: tuple[float, ...], names: tuple[str, ...]) -> str:
            for cut, name in zip(cuts, names):
                if value < cut:
                    return name
            return names[-1]

        # Visual context is anchor-derived but stripped of track identity.
        for row in vision:
            if not isinstance(row, dict):
                continue
            for field in ("setting", "lighting", "camera_shot", "camera_angle", "camera_motion", "overall_action"):
                value = norm_text(row.get(field))
                if value:
                    add("visual_context", f"{field}={value}")
            person_count = len([x for x in (row.get("people") or []) if isinstance(x, dict)])
            object_count = len([x for x in (row.get("objects") or []) if isinstance(x, dict)])
            add("visual_context", f"people_count={band(float(person_count),(1,2,4),( 'none','one','few','many'))}")
            add("visual_context", f"object_count={band(float(object_count),(1,3,8),( 'none','few','several','many'))}")

        # Track-level trajectory shape. No track id enters the canonical token.
        for track in tracks:
            if not isinstance(track, dict):
                continue
            kind = norm_text(track.get("kind")) or "entity"
            traj = track.get("trajectory") if isinstance(track.get("trajectory"), dict) else {}
            direction = norm_text(traj.get("net_screen_direction")) or "unknown"
            path = float(traj.get("path_length_normalized") or 0)
            displacement = float(traj.get("net_displacement_normalized") or 0)
            moving = int(traj.get("moving_step_count") or 0)
            measured = int(traj.get("measured_step_count") or 0)
            motion_fraction = (moving / measured) if measured > 0 else 0.0
            add("motion", f"{kind}:net={direction}")
            add("motion", f"{kind}:path={band(path,(0.01,0.08,0.25,0.6),('still','small','medium','large','very_large'))}")
            add("motion", f"{kind}:displacement={band(displacement,(0.01,0.05,0.15,0.4),('still','small','medium','large','very_large'))}")
            add("motion", f"{kind}:activity={band(motion_fraction,(0.1,0.4,0.75),('mostly_still','intermittent','often_moving','continuous_motion'))}")

        # Ordered transition tokens preserve coarse event sequence while excluding IDs.
        transition_sequence: list[str] = []
        for event in transitions:
            if not isinstance(event, dict):
                continue
            etype = norm_text(event.get("transition_type"))
            kind = norm_text(event.get("entity_kind")) or "entity"
            field = norm_text(event.get("field"))
            if etype == "screen_space_motion":
                delta = event.get("delta") if isinstance(event.get("delta"), dict) else {}
                direction = norm_text(delta.get("screen_direction")) or "unknown"
                speed = float(delta.get("speed_normalized_per_second") or 0)
                tok = f"{kind}:motion:{direction}:speed={band(speed,(0.03,0.12,0.35,0.8),('tiny','slow','medium','fast','very_fast'))}"
                add("motion", tok)
                transition_sequence.append("motion:" + tok)
            elif etype == "held_object_change":
                added = len(event.get("added") or [])
                removed = len(event.get("removed") or [])
                tok = f"{kind}:held_object_change:add={band(float(added),(1,2),( 'none','one','multiple'))}:remove={band(float(removed),(1,2),('none','one','multiple'))}"
                add("state_change", tok)
                transition_sequence.append("state:" + tok)
            elif etype == "entity_state_change":
                before = norm_text(event.get("before"), 48)
                after = norm_text(event.get("after"), 48)
                tok = f"{kind}:{field or 'state'}:{before or 'none'}>{after or 'none'}"
                add("state_change", tok)
                transition_sequence.append("state:" + tok)
            elif etype == "scene_state_change":
                before = norm_text(event.get("before"), 48)
                after = norm_text(event.get("after"), 48)
                tok = f"{field or 'scene'}:{before or 'none'}>{after or 'none'}"
                add("scene_change", tok)
                transition_sequence.append("scene:" + tok)

        # Spoken/sung text and measured delivery. Literal words are useful for overlap,
        # but voice acoustics never infer ethnicity/nationality/emotion.
        for seg in transcript_segments:
            if not isinstance(seg, dict):
                continue
            text = norm_text(seg.get("text"), 160)
            if text:
                words = [w for w in re.findall(r"[a-z0-9']+", text) if len(w) > 1]
                for word in words[:48]:
                    add("speech_text", f"word={word}")
                if words:
                    add("speech_text", "phrase=" + " ".join(words[:12]))
            delivery = seg.get("delivery") if isinstance(seg.get("delivery"), dict) else {}
            prosody = delivery.get("prosody") if isinstance(delivery.get("prosody"), dict) else {}
            for field in ("energy_band", "pace_band", "pitch_dynamics"):
                value = norm_text(prosody.get(field))
                if value:
                    add("speech_prosody", f"{field}={value}")
            rate = float(delivery.get("word_rate_per_second") or 0)
            if rate > 0:
                add("speech_prosody", f"word_rate={band(rate,(1.2,2.2,3.3),('slow','moderate','fast','very_fast'))}")

        # Music uses relative/order-friendly note/chord tokens plus tempo bands.
        chord_sequence: list[str] = []
        for chord in (audio.get("chord_intervals") or [])[:96]:
            if isinstance(chord, dict):
                value = norm_text(chord.get("chord"), 24)
                if value:
                    add("music", f"chord={value}")
                    chord_sequence.append(value)
        note_sequence: list[str] = []
        for note in (audio.get("note_intervals") or [])[:128]:
            if isinstance(note, dict):
                value = norm_text(note.get("note"), 16)
                if value:
                    # Drop octave for a pitch-class token while retaining the exact note too.
                    pitch_class = re.sub(r"-?\d+$", "", value)
                    add("music", f"note={value}")
                    if pitch_class:
                        add("music", f"pitch_class={pitch_class}")
                    note_sequence.append(pitch_class or value)
        ml_note_sequence: list[str] = []
        for note in (audio.get("ml_note_events") or [])[:256]:
            if not isinstance(note, dict):
                continue
            value = norm_text(note.get("note"), 16)
            if not value:
                continue
            pitch_class = re.sub(r"-?\d+$", "", value)
            add("music", f"ml_note={value}")
            if pitch_class:
                add("music", f"ml_pitch_class={pitch_class}")
            ml_note_sequence.append(pitch_class or value)
        tempo = float(audio.get("tempo_bpm_hypothesis") or 0)
        if tempo > 0:
            add("music", f"tempo={band(tempo,(70,100,130,170),('slow','mid_slow','mid_fast','fast','very_fast'))}")

        # Stable sequence sketches add order information without exact timestamp dependence.
        sequence_sketches: dict[str, list[str]] = {}
        if transition_sequence:
            sequence_sketches["transitions"] = transition_sequence[:128]
        if chord_sequence:
            sequence_sketches["chords"] = chord_sequence[:64]
        if note_sequence:
            sequence_sketches["pitch_classes"] = note_sequence[:96]
        if ml_note_sequence:
            sequence_sketches["ml_pitch_classes"] = ml_note_sequence[:128]

        canonical = {
            "schema_version": COMPARISON_SCHEMA,
            "tokens": sorted(tokens),
            "sequence_sketches": sequence_sketches,
        }
        encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = base64.urlsafe_b64encode(hashlib.shake_256(encoded).digest(64)).decode("ascii").rstrip("=")
        return {
            "schema_version": COMPARISON_SCHEMA,
            "signature": "duoid:shake256-512:" + digest,
            "authority": "normalized_comparison_context_only",
            "identity_semantics": "no_person_identity_claim; ephemeral track ids excluded from canonical signature",
            "time_semantics": "coarse event order retained; exact timestamp alignment not required for token overlap",
            "token_count": len(tokens),
            "tokens": sorted(tokens),
            "families": {key: sorted(values) for key, values in families.items()},
            "sequence_sketches": sequence_sketches,
            "feature_counts": {key: len(values) for key, values in families.items()},
        }

    def _recurrence(self, vision: list[dict[str, Any]], transcript_segments: list[dict[str, Any]], audio: dict[str, Any]) -> dict[str, Any]:
        events: dict[str, list[dict[str, Any]]] = {}
        def add(sig: str, t0: float, t1: float, modality: str) -> None:
            if sig:
                events.setdefault(sig, []).append({"start_seconds": round(t0, 4), "end_seconds": round(t1, 4), "modality": modality})
        for f in vision:
            t = float(f.get("time_seconds") or 0)
            for p in f.get("people") or []:
                if isinstance(p, dict): add("person:" + str(p.get("ephemeral_track_id") or p.get("clothing") or p.get("hair") or "visible"), t, t, "visual")
            for o in f.get("objects") or []:
                if isinstance(o, dict): add("object:" + str(o.get("ephemeral_track_id") or o.get("name") or ""), t, t, "visual")
        for seg in transcript_segments:
            text = re.sub(r"\s+", " ", str(seg.get("text") or "").strip().lower())
            if text: add("vocal:" + text[:80], float(seg.get("start_seconds") or 0), float(seg.get("end_seconds") or 0), "text")
        for c in audio.get("chord_intervals") or []:
            add("chord:" + str(c.get("chord") or ""), float(c.get("start_seconds") or 0), float(c.get("end_seconds") or 0), "audio")
        links = []
        for sig, items in events.items():
            if len(items) < 2: continue
            items.sort(key=lambda x: x["start_seconds"])
            for a, b in zip(items, items[1:]):
                links.append({"schema_version": TEMPORAL_SCHEMA, "relation_type": "temporal_recurrence", "signature": sig, "modality": b["modality"], "from_time_range": {"start_seconds": a["start_seconds"], "end_seconds": a["end_seconds"]}, "to_time_range": {"start_seconds": b["start_seconds"], "end_seconds": b["end_seconds"]}, "temporal_distance": round(b["start_seconds"] - a["start_seconds"], 4), "evidence_basis": "normalized_reconstruction_signature", "authority": "exploratory_evidence_only"})
                if len(links) >= 512: break
            if len(links) >= 512: break
        return {"schema_version": TEMPORAL_SCHEMA, "recurrence_edges": len(links), "temporal_links": links}

    def _summary_meta_objects(self, vision: list[dict[str, Any]], transcript_segments: list[dict[str, Any]], audio: dict[str, Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        def add(category: str, name: str, confidence: float, modality: str, time_range: dict[str, Any] | None = None, provenance: dict[str, Any] | None = None) -> None:
            key = (category, name.lower())
            if not name or key in seen: return
            seen.add(key)
            rec = {"category": category, "object_name": name[:240], "confidence": max(0.0, min(1.0, confidence)), "modality": modality}
            if time_range: rec["time_range"] = time_range
            if provenance: rec["provenance"] = provenance
            out.append(rec)
        for f in vision:
            t = float(f.get("time_seconds") or 0)
            tr = {"start_seconds": t, "end_seconds": t, "kind": "semantic_anchor"}
            for p in f.get("people") or []:
                if isinstance(p, dict):
                    desc = "; ".join(x for x in ["person", str(p.get("visible_skin_tone") or ""), str(p.get("hair") or ""), ", ".join(p.get("clothing") or []), ", ".join(p.get("footwear") or []), str(p.get("facial_expression") or ""), str(p.get("pose") or ""), str(p.get("interaction") or ""), str(p.get("action") or "")] if x)
                    add("visual_person_state", desc, float(p.get("confidence") or f.get("confidence") or 0.7), "visual", tr, f.get("provenance"))
            for o in f.get("objects") or []:
                if isinstance(o, dict):
                    obj_desc = "; ".join(x for x in [str(o.get("name") or ""), str(o.get("color") or ""), str(o.get("material") or ""), str(o.get("state") or ""), str(o.get("position") or ""), str(o.get("relation") or ""), ", ".join(o.get("attributes") or [])] if x)
                    add("visual_object", obj_desc, float(o.get("confidence") or 0.7), "visual", tr, f.get("provenance"))
        for seg in transcript_segments:
            add("vocal_transcript_segment", str(seg.get("text") or ""), 0.85, "text", {"start_seconds": seg.get("start_seconds"), "end_seconds": seg.get("end_seconds"), "kind": "asr_segment"}, {"source": "vm1-whisper", "authority": "asr_hypothesis"})
        if audio.get("tempo_bpm_hypothesis"):
            add("tempo_hypothesis", f"tempo about {audio['tempo_bpm_hypothesis']} BPM", 0.7, "audio")
        for chord in (audio.get("chord_intervals") or [])[:32]:
            add("chord_hypothesis", str(chord.get("chord") or ""), float(chord.get("confidence") or 0.5), "audio", {"start_seconds": chord.get("start_seconds"), "end_seconds": chord.get("end_seconds"), "kind": "spectral_window"})
        return out[:256]

    def _clip_range(self, source: Path, *, start_seconds: float, end_seconds: float, has_video: bool) -> tuple[Path, str]:
        duration = max(0.05, float(end_seconds) - float(start_seconds))
        if has_video:
            target = source.parent / "range-analysis.mp4"
            args = [
                "ffmpeg", "-v", "error", "-ss", f"{start_seconds:.6f}", "-i", str(source), "-t", f"{duration:.6f}",
                "-map", "0:v:0?", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-y", str(target),
            ]
            self._run(args, timeout=max(120.0, min(1200.0, duration * 4.0 + 60.0)))
            return target, "video/mp4"
        target = source.parent / "range-analysis.wav"
        args = [
            "ffmpeg", "-v", "error", "-ss", f"{start_seconds:.6f}", "-i", str(source), "-t", f"{duration:.6f}",
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", str(target),
        ]
        self._run(args, timeout=max(90.0, min(900.0, duration * 3.0 + 45.0)))
        return target, "audio/wav"

    @staticmethod
    def _offset_time_record(record: dict[str, Any], offset: float) -> None:
        if not offset:
            return
        for key in ("time_seconds", "start_seconds", "end_seconds"):
            if record.get(key) is not None:
                record[key] = round(float(record[key]) + offset, 6)
        for key in ("from_time_range", "to_time_range", "time_range"):
            value = record.get(key)
            if isinstance(value, dict):
                for time_key in ("start_seconds", "end_seconds"):
                    if value.get(time_key) is not None:
                        value[time_key] = round(float(value[time_key]) + offset, 6)

    def _offset_analysis_timeline(
        self,
        *,
        offset: float,
        metrics: list[dict[str, Any]],
        vision: list[dict[str, Any]],
        audio: dict[str, Any],
        words: list[dict[str, Any]],
        transcript_segments: list[dict[str, Any]],
        visual_embeddings: list[dict[str, Any]] | None = None,
    ) -> None:
        if not offset:
            return
        for row in metrics:
            if isinstance(row, dict):
                self._offset_time_record(row, offset)
        for row in vision:
            if isinstance(row, dict):
                self._offset_time_record(row, offset)
        for row in visual_embeddings or []:
            if isinstance(row, dict):
                self._offset_time_record(row, offset)
        for row in audio.get("frames") or []:
            if isinstance(row, dict):
                self._offset_time_record(row, offset)
        for row in audio.get("perceptual_embeddings") or []:
            if isinstance(row, dict):
                self._offset_time_record(row, offset)
        audio["onsets"] = [round(float(value) + offset, 6) for value in (audio.get("onsets") or [])]
        for key in ("note_intervals", "chord_intervals", "ml_note_events"):
            for row in audio.get(key) or []:
                if isinstance(row, dict):
                    self._offset_time_record(row, offset)
        for row in words:
            if isinstance(row, dict):
                self._offset_time_record(row, offset)
        for segment in transcript_segments:
            if not isinstance(segment, dict):
                continue
            # Segment word records are the same dict objects already present in the flat words list.
            # Offset the segment envelope only so word timestamps are shifted exactly once.
            for key in ("start_seconds", "end_seconds"):
                if segment.get(key) is not None:
                    segment[key] = round(float(segment[key]) + offset, 6)

    def analyze(self, source: Path, *, filename: str, mime_type: str, options: dict[str, Any], progress: Any) -> dict[str, Any]:
        source_probe = self._probe(source)
        source_fmt = source_probe.get("format") or {}
        source_streams = source_probe.get("streams") or []
        source_duration = float(source_fmt.get("duration") or 0)
        source_video_stream = next((stream for stream in source_streams if stream.get("codec_type") == "video"), None)
        source_audio_stream = next((stream for stream in source_streams if stream.get("codec_type") == "audio"), None)
        source_fps = _parse_rate((source_video_stream or {}).get("avg_frame_rate") or (source_video_stream or {}).get("r_frame_rate"), 30.0)
        source_clock_hz = min(60.0, max(1.0, source_fps)) if source_video_stream else 0.0

        requested_start = options.get("range_start_seconds")
        requested_end = options.get("range_end_seconds")
        range_start = max(0.0, float(requested_start or 0.0)) if requested_start is not None else 0.0
        range_end = min(source_duration, float(requested_end)) if requested_end is not None and source_duration > 0 else source_duration
        range_requested = requested_start is not None or requested_end is not None
        if range_requested:
            if source_duration <= 0:
                raise ValueError("media_reconstruction_range_requires_known_duration")
            if range_end <= range_start or range_end - range_start < 0.05:
                raise ValueError("media_reconstruction_invalid_range")
            range_end = min(source_duration, range_end)
        else:
            range_start = 0.0
            range_end = source_duration

        analysis_profile = str(options.get("analysis_profile") or ("deep_range" if range_requested else "full")).strip().lower()
        if analysis_profile not in {"full", "deep_range", "forensic_range"}:
            analysis_profile = "deep_range" if range_requested else "full"
        if analysis_profile == "forensic_range":
            # Forensic mode makes the deterministic witness clock frame-addressable up
            # to source FPS / 60 Hz. Expensive semantic vision remains gated at 0.25 s
            # plus high-change anchors, then state deltas are held between witnesses.
            default_rate, default_interval, default_anchors = min(60.0, source_clock_hz or 60.0), 0.25, 240
        elif analysis_profile == "deep_range":
            default_rate, default_interval, default_anchors = 8.0, 0.5, 240
        else:
            default_rate, default_interval, default_anchors = 4.0, 2.0, 120
        deterministic_rate = max(0.5, min(60.0, source_clock_hz or 60.0, float(options.get("deterministic_rate_hz") or default_rate)))
        semantic_interval = max(0.25, min(10.0, float(options.get("semantic_interval_seconds") or default_interval)))
        max_anchors = max(8, min(240, int(options.get("max_semantic_anchors") or default_anchors)))

        analysis_source = source
        analysis_mime = mime_type
        time_offset = 0.0
        if range_requested:
            progress("range_extract", 0.03)
            analysis_source, analysis_mime = self._clip_range(
                source,
                start_seconds=range_start,
                end_seconds=range_end,
                has_video=bool(source_video_stream),
            )
            time_offset = range_start

        probe = self._probe(analysis_source)
        fmt = probe.get("format") or {}
        streams = probe.get("streams") or []
        analysis_duration = float(fmt.get("duration") or max(0.0, range_end - range_start) or source_duration)
        video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        root = source.parent
        metrics: list[dict[str, Any]] = []
        anchors: list[dict[str, Any]] = []
        vision: list[dict[str, Any]] = []
        vision_worker: dict[str, Any] = {"status": "not_applicable"}
        visual_embeddings: list[dict[str, Any]] = []
        visual_embedding_worker: dict[str, Any] = {"status": "not_applicable"}
        if video_stream:
            progress("visual_metrics", 0.08)
            metrics = self._visual_metrics(analysis_source, analysis_duration, deterministic_rate)
            anchors = self._select_anchors(metrics, interval_seconds=semantic_interval, max_anchors=max_anchors)
            progress("visual_anchor_extract", 0.18)
            anchors = self._anchor_images(analysis_source, anchors, root)
            progress("visual_embedding", 0.23)
            visual_embeddings, visual_embedding_worker = self._visual_embeddings(anchors)
            progress("vision_semantics", 0.28)
            vision, vision_worker = self._vision_semantics(anchors, progress)
        transcript = None
        transcript_worker = {"status": "not_applicable"}
        audio_embedding_worker: dict[str, Any] = {"status": "not_applicable"}
        music_transcription_worker: dict[str, Any] = {"status": "not_applicable"}
        if audio_stream:
            progress("transcription", 0.68)
            try:
                transcript, transcript_worker = self._transcription(analysis_source, analysis_mime)
            except Exception as exc:
                transcript_worker = {"status": "failed", "error": type(exc).__name__, "detail": str(exc)[:500]}
            progress("audio_features", 0.80)
            pcm = self._pcm(analysis_source)
            audio = self._audio_features(pcm)
            progress("music_transcription", 0.84)
            ml_note_events, music_transcription_worker = self._music_transcription(analysis_source, analysis_mime)
            audio["ml_note_events"] = ml_note_events
            audio["ml_note_event_policy"] = "separate_model_evidence; does_not_replace_deterministic_spectral_note_hypotheses"
            audio["ml_note_event_authority"] = "ml_polyphonic_music_transcription_evidence"
            progress("audio_embedding", 0.87)
            audio_embeddings, audio_embedding_worker = self._audio_embeddings(analysis_source, start_seconds=0.0, end_seconds=analysis_duration)
            audio["perceptual_embeddings"] = audio_embeddings
            audio["perceptual_embedding_policy"] = "decoded_audio_windows_clap_l2_normalized; optional_similarity_evidence_only"
            audio["perceptual_embedding_identity_semantics"] = "not_speaker_identity_evidence; audio content/timbre/structure similarity only"
        else:
            audio = {"sample_rate_hz": 16000, "duration_seconds": analysis_duration, "frames": [], "onsets": [], "note_intervals": [], "chord_intervals": [], "ml_note_events": [], "tempo_bpm_hypothesis": None}
        words, transcript_segments = self._transcript_witnesses(transcript, audio)
        self._offset_analysis_timeline(
            offset=time_offset,
            metrics=metrics,
            vision=vision,
            audio=audio,
            words=words,
            transcript_segments=transcript_segments,
            visual_embeddings=visual_embeddings,
        )
        absolute_end = range_end if range_requested else source_duration
        entity_tracks = self._entity_tracks(vision)
        temporal_transitions = self._temporal_transitions(vision, entity_tracks)
        intervals = self._state_intervals(vision, source_clock_hz or 1.0, absolute_end)
        if intervals and range_requested:
            intervals[0]["start_seconds"] = round(range_start, 6)
            intervals[0]["start_frame"] = int(round(range_start * (source_fps or 1.0)))
        recurrence = self._recurrence(vision, transcript_segments, audio)
        comparison_signatures = self._comparison_signatures(vision, transcript_segments, audio, entity_tracks, temporal_transitions)
        meta_objects = self._summary_meta_objects(vision, transcript_segments, audio)
        progress("witness_gate", 0.94)
        analysis_range = {
            "start_seconds": round(range_start, 6),
            "end_seconds": round(absolute_end, 6),
            "duration_seconds": round(max(0.0, absolute_end - range_start), 6),
            "profile": analysis_profile,
            "derived_clip": bool(range_requested),
            "source_time_offset_seconds": round(time_offset, 6),
        }
        reconstruction = {
            "schema_version": SCHEMA_VERSION,
            "formal_contract": FORMAL_CONTRACT,
            "analysis_version": ANALYSIS_VERSION,
            "authority": "observed_or_inferred_evidence_only",
            "source_clock": {"source_fps": source_fps if source_video_stream else None, "addressable_witness_hz": source_clock_hz, "duration_seconds": source_duration, "estimated_total_frames": int(round(source_duration * source_fps)) if source_video_stream else 0},
            "analysis_range": analysis_range,
            "temporal_gate": {
                "schema_version": GATE_SCHEMA,
                "policy": "event_activated_delta_compression_with_observed_anchors",
                "unchanged_state": "inherit_until_next_change_witness",
                "source_addressable_clock_hz": source_clock_hz,
                "semantic_anchor_interval_seconds": semantic_interval,
                "deterministic_measurement_rate_hz": deterministic_rate,
                "max_semantic_anchors": max_anchors,
                "transition_time_semantics": "semantic changes are bounded between observed anchors; exact unsampled change instants are not asserted",
                "forensic_strategy": "dense deterministic measurements plus sparse/event-selected semantic witnesses",
            },
            "visual": {
                "deterministic_samples": metrics,
                "semantic_anchors": vision,
                "state_intervals": intervals,
                "entity_tracks": entity_tracks,
                "entity_track_policy": "ephemeral_non_identity_visual_association",
                "temporal_transitions": temporal_transitions,
                "trajectory_policy": "normalized_screen_space_only_no_real_world_identity_or_direction_claim",
                "perceptual_embeddings": visual_embeddings,
                "perceptual_embedding_policy": "exact_semantic_anchor_frame_dinov2_cls_l2_normalized; optional_similarity_evidence_only",
                "perceptual_embedding_identity_semantics": "not_person_identity_evidence",
            },
            "audio": {**audio, "transcript": {"text": (transcript or {}).get("text") if isinstance(transcript, dict) else None, "language": (transcript or {}).get("language") if isinstance(transcript, dict) else None, "detected_language": (transcript or {}).get("detected_language") if isinstance(transcript, dict) else None, "words": words, "segments": transcript_segments, "content_role": "vocal_text_hypothesis; may be lyrics, speech, or both depending on the source"}},
            "recurrence": recurrence,
            "comparison_signatures": comparison_signatures,
            "workers": {"vision": vision_worker, "visual_embedding": visual_embedding_worker, "audio_embedding": audio_embedding_worker, "music_transcription": music_transcription_worker, "transcription": transcript_worker},
            "reconstruction_note": "State intervals are frame-addressable. Range child witnesses retain absolute source timestamps. Semantic attributes between sampled anchors are explicitly held as inferred persistence, never mislabeled as directly observed on every frame. Exact source bytes remain the source artifact; this witness is reconstruction evidence and comparison context.",
        }
        progress("motif_extraction", 0.965)
        motif_catalog = self._motif_catalog(reconstruction)
        reconstruction["motifs"] = motif_catalog
        source_record = {"source_type": "uploaded_media_reconstruction", "filename": filename, "mime_type": mime_type, "size_bytes": source.stat().st_size, "duration_seconds": source_duration, "analysis_range": analysis_range}
        witness = {"schema_version": "media_ml_meta_objects/v2-reconstruction", "source": source_record, "meta_objects": meta_objects, "recurrence": recurrence, "motifs": motif_catalog, "comparison_signatures": comparison_signatures, "reconstruction": reconstruction, "analysis": {"analysis_version": ANALYSIS_VERSION, "analysis_tier": "reconstruction", "analysis_profile": analysis_profile, "formal_contract": FORMAL_CONTRACT, "temporal_schema": TEMPORAL_SCHEMA, "worker_schema": "duotronic-analysis-worker-pool/v1", "vision_anchor_count": len(vision), "visual_embedding_count": len(visual_embeddings), "audio_embedding_count": len(audio.get("perceptual_embeddings") or []), "ml_note_event_count": len(audio.get("ml_note_events") or []), "entity_track_count": len(entity_tracks), "temporal_transition_count": len(temporal_transitions), "deterministic_visual_sample_count": len(metrics), "transcript_word_count": len(words), "transcript_segment_count": len(transcript_segments), "note_interval_count": len(audio.get("note_intervals") or []), "chord_interval_count": len(audio.get("chord_intervals") or []), "recurrence_edge_count": recurrence.get("recurrence_edges", 0), "motif_count": motif_catalog.get("motif_count", 0), "motif_candidate_count": motif_catalog.get("salient_candidate_count", 0), "motif_occurrence_count": (motif_catalog.get("summary") or {}).get("recurrent_occurrence_count", 0), "comparison_signature_token_count": comparison_signatures.get("token_count", 0)}, "note": "Reconstruction-grade witnessed media timeline; ML inference remains provenance-bound candidate evidence."}
        node_id = "media-reconstruction:" + uuid.uuid5(uuid.NAMESPACE_URL, f"{filename}|{source.stat().st_size}|{range_start:.6f}|{absolute_end:.6f}|{analysis_profile}").hex[:24]
        result = {"schema_version": "media_ml_meta_object_analysis/v2-reconstruction", "source_kind": "uploaded_file", "playlist": False, "nodes": [{"id": node_id, "label": filename, "epistemic": {"role": "evidence", "state": "observed+inferred", "model_id": ANALYSIS_VERSION, "viewpoint": "media-reconstruction", "layer": 0}, "witness": witness}], "relations": [], "models": {"vision": vision_worker.get("model"), "visual_embedding": visual_embedding_worker.get("model"), "audio_embedding": audio_embedding_worker.get("model"), "music_transcription": music_transcription_worker.get("model"), "transcription": transcript_worker.get("model"), "audio_features": "ffmpeg+numpy-stft/v1"}, "analysis_tier": "reconstruction", "analysis_profile": analysis_profile, "analysis_version": ANALYSIS_VERSION, "temporal_schema": TEMPORAL_SCHEMA, "warnings": [], "workers": [vision_worker, visual_embedding_worker, audio_embedding_worker, music_transcription_worker, transcript_worker], "summary": {"item_count": 1, "meta_object_count": len(meta_objects), "relation_count": recurrence.get("recurrence_edges", 0), "deterministic_visual_samples": len(metrics), "semantic_visual_anchors": len(vision), "visual_perceptual_embeddings": len(visual_embeddings), "audio_perceptual_embeddings": len(audio.get("perceptual_embeddings") or []), "ml_note_events": len(audio.get("ml_note_events") or []), "frame_state_intervals": len(intervals), "entity_tracks": len(entity_tracks), "temporal_transitions": len(temporal_transitions), "transcript_words": len(words), "transcript_segments": len(transcript_segments), "note_intervals": len(audio.get("note_intervals") or []), "chord_intervals": len(audio.get("chord_intervals") or []), "onsets": len(audio.get("onsets") or []), "temporal_recurrence_count": recurrence.get("recurrence_edges", 0), "motif_count": motif_catalog.get("motif_count", 0), "motif_candidate_count": motif_catalog.get("salient_candidate_count", 0), "motif_occurrences": (motif_catalog.get("summary") or {}).get("recurrent_occurrence_count", 0), "comparison_signature_tokens": comparison_signatures.get("token_count", 0), "comparison_signature": comparison_signatures.get("signature"), "analysis_range": analysis_range}}
        progress("finalize", 0.99)
        return result
