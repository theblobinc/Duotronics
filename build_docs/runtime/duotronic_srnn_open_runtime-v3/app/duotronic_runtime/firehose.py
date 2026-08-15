from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Any

FIREHOSE_TABLES: dict[str, dict[str, str]] = {
    "runtime_runs": {"lane": "control-decision", "kind": "runtime_run"},
    "wgrnn_memory_updates": {"lane": "memory-pressure", "kind": "wgrnn_memory_update"},
    "nla_activation_witnesses": {"lane": "witness-recurrent", "kind": "activation_witness"},
    "memory_cells": {"lane": "memory-recall", "kind": "memory_cell"},
    "audit_events": {"lane": "node-resource", "kind": "audit_event"},
    "corpus_documents": {"lane": "memory-recall", "kind": "corpus_document"},
    "corpus_versions": {"lane": "policy-replay", "kind": "corpus_version"},
    "evidence_claims": {"lane": "control-decision", "kind": "evidence_claim"},
    "evidence_witnesses": {"lane": "witness-recurrent", "kind": "evidence_witness"},
    "module_invocations": {"lane": "node-resource", "kind": "module_invocation"},
    "source_documents": {"lane": "memory-recall", "kind": "source_document"},
    "source_index_generations": {"lane": "node-resource", "kind": "source_generation"},
    "session_transcript_events": {"lane": "chat-user", "kind": "transcript_event"},
    "observer_claim_observations": {"lane": "witness-meta", "kind": "observer_claim"},
    "claim_consensus": {"lane": "control-decision", "kind": "claim_consensus"},
}


def build_firehose(kernel: Any, *, limit: int = 180, per_source: int = 40, text_limit: int = 900, include_raw: bool = True) -> dict[str, Any]:
    limit = max(1, min(int(limit), 500))
    per_source = max(1, min(int(per_source), 100))
    text_limit = max(120, min(int(text_limit), 5000))
    items: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    source_counts: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=min(12, len(FIREHOSE_TABLES))) as executor:
        futures = {
            executor.submit(kernel.store.fetch_recent, table, per_source, timeout=0.45): (table, meta)
            for table, meta in FIREHOSE_TABLES.items()
        }
        for future in as_completed(futures):
            table, meta = futures[future]
            try:
                rows = future.result()
            except Exception as exc:
                warnings.append({"source": table, "error": str(exc)})
                continue
            source_counts[table] = len(rows)
            for row in rows:
                items.append(_normalize_record(table, meta, row, text_limit=text_limit, include_raw=include_raw))
    runtime_health: dict[str, Any] | None = None
    try:
        runtime_health = kernel.health()
        source_counts["runtime_health"] = 1
        items.append(_normalize_record(
            "runtime_health",
            {"lane": "node-resource", "kind": "runtime_health"},
            {**runtime_health, "created_at": datetime.utcnow()},
            text_limit=text_limit,
            include_raw=include_raw,
        ))
    except Exception as exc:
        warnings.append({"source": "runtime_health", "error": str(exc)})

    wgrnn_snapshot: dict[str, Any] | None = None
    try:
        wgrnn_snapshot = kernel.wgrnn.snapshot(include_slots=False)
        source_counts["wgrnn_status"] = 1
        items.append(_normalize_record(
            "wgrnn_status",
            {"lane": "witness-recurrent", "kind": "wgrnn_status"},
            {**wgrnn_snapshot, "created_at": datetime.utcnow()},
            text_limit=text_limit,
            include_raw=include_raw,
        ))
    except Exception as exc:
        warnings.append({"source": "wgrnn_status", "error": str(exc)})

    items.sort(key=lambda item: item.get("timestamp_sort", 0), reverse=True)
    items = items[:limit]
    for item in items:
        item.pop("timestamp_sort", None)
    return {
        "schema_version": "wgrnn-runtime-firehose/v1",
        "generated_at": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "items": items,
        "source_counts": source_counts,
        "warnings": warnings,
        "sources": [*FIREHOSE_TABLES, "runtime_health", "wgrnn_status"],
        "runtime": {
            "health": _json_safe(runtime_health),
            "wgrnn": _json_safe(wgrnn_snapshot),
            "online": wgrnn_snapshot is not None,
            "source_count": len(FIREHOSE_TABLES) + 2,
            "active_source_count": len(source_counts),
            "contract": str((runtime_health or {}).get("corpus", {}).get("version") or "") or None,
            "corpus": _json_safe((runtime_health or {}).get("corpus")),
            "gates": [],
        },
    }


def _normalize_record(table: str, meta: dict[str, str], row: dict[str, Any], *, text_limit: int, include_raw: bool) -> dict[str, Any]:
    timestamp, timestamp_sort = _timestamp(row)
    text = _text_for(table, row)
    text = " ".join(str(text).split())[:text_limit]
    severity = _severity(row)
    item = {
        "id": _record_id(table, row),
        "timestamp": timestamp,
        "timestamp_sort": timestamp_sort,
        "source": table,
        "kind": meta["kind"],
        "lane": _lane_for(table, row, meta["lane"]),
        "severity": severity,
        "text": text or f"{table} activity",
        "loop_id": str(row.get("loop_id") or row.get("session_id") or row.get("repository_id") or "runtime"),
        "node_id": str(row.get("node_id") or row.get("observer_id") or row.get("module_id") or "runtime"),
        "trust_status": str(row.get("trust_status") or row.get("status") or row.get("claim_status") or severity),
        "authority_t": _float(row.get("authority_t"), 0.0),
    }
    if include_raw:
        item["raw"] = _json_safe(row)
    return item


def _record_id(table: str, row: dict[str, Any]) -> str:
    for key in ("run_id", "update_id", "witness_id", "cell_id", "event_id", "doc_id", "corpus_id", "claim_id", "invocation_id", "observation_id", "claim_key", "event_digest", "generation_id"):
        value = row.get(key)
        if value not in (None, ""):
            return f"{table}:{value}"
    seed = json.dumps(_json_safe(row), sort_keys=True, ensure_ascii=False)[:12000]
    return f"{table}:{shake256_hex(seed.encode('utf-8'))[:24]}"


def _timestamp(row: dict[str, Any]) -> tuple[str, float]:
    for key in ("created_at", "updated_at", "ingested_at", "started_at", "completed_at", "activated_at"):
        value = row.get(key)
        if isinstance(value, datetime):
            return value.isoformat(), value.timestamp()
        if isinstance(value, date):
            dt = datetime.combine(value, datetime.min.time())
            return dt.isoformat(), dt.timestamp()
        if value:
            try:
                text = str(value).replace("Z", "+00:00")
                dt = datetime.fromisoformat(text)
                return str(value), dt.timestamp()
            except Exception:
                pass
    for key in ("created_at_ms", "evaluated_at_ms"):
        try:
            ms = float(row.get(key))
            return datetime.utcfromtimestamp(ms / 1000.0).isoformat(timespec="milliseconds") + "Z", ms / 1000.0
        except Exception:
            pass
    return "", 0.0


def _text_for(table: str, row: dict[str, Any]) -> str:
    if table == "runtime_runs":
        return f"run {row.get('requested_action','')} model={_compact(row.get('model'))} prompt={row.get('prompt','')} response={row.get('response_text','')}"
    if table == "wgrnn_memory_updates":
        return f"WG-RNN {row.get('update_kind','update')} slot={row.get('slot_id','?')} trust={row.get('trust_status','')} authority={row.get('authority_t','')} confidence={row.get('confidence','')} payload={_compact(row.get('payload'))}"
    if table == "nla_activation_witnesses":
        return f"activation witness model={_compact(row.get('source_model'))} lifecycle={_compact(row.get('lifecycle'))} policy={_compact(row.get('policy'))} fidelity={_compact(row.get('fidelity'))}"
    if table == "memory_cells":
        return f"memory cell slot={row.get('slot_id','?')} trust={row.get('trust_status','')} authority={row.get('authority_t','')} payload={_compact(row.get('payload'))}"
    if table == "audit_events":
        return f"audit {row.get('event_type','event')} severity={row.get('severity','info')} payload={_compact(row.get('payload'))}"
    if table == "corpus_documents":
        return f"corpus document {row.get('title','')} path={row.get('path','')} excerpt={row.get('excerpt','')}"
    if table == "corpus_versions":
        return f"corpus {row.get('version','')} status={row.get('status','')} manifest={_compact(row.get('manifest'))} validation={_compact(row.get('validation'))}"
    if table == "evidence_claims":
        return f"claim {row.get('subject','')} {row.get('predicate','')} {_compact(row.get('object'))} status={row.get('claim_status','')} epistemic={row.get('epistemic_status','')} support={_compact(row.get('support'))}"
    if table == "evidence_witnesses":
        return f"witness {row.get('witness_type','')} observer={row.get('observer_id','')} status={row.get('status','')} payload={_compact(row.get('payload'))}"
    if table == "module_invocations":
        return f"module {row.get('module_id','')} kind={row.get('module_kind','')} status={row.get('status','')} payload={_compact(row.get('payload'))}"
    if table == "source_documents":
        return f"source {row.get('repository_id','')} {row.get('path','')} chunk={row.get('chunk_index','')} language={row.get('language','')} content={row.get('content','')} metadata={_compact(row.get('metadata'))}"
    if table == "source_index_generations":
        return f"source generation repo={row.get('repository_id','')} status={row.get('status','')} root={row.get('root_path','')} commit={row.get('commit_id','')} documents={row.get('document_count','')} bytes={row.get('byte_count','')} metadata={_compact(row.get('metadata'))}"
    if table == "session_transcript_events":
        return f"transcript {row.get('actor','')} {row.get('event_type','')} tags={_compact(row.get('tags'))} content={_compact(row.get('content'))}"
    if table == "observer_claim_observations":
        return f"observer {row.get('observer_kind','')}:{row.get('observer_id','')} {row.get('stance','')} confidence={row.get('confidence','')} {row.get('subject','')} {row.get('predicate','')} {_compact(row.get('object'))}"
    if table == "claim_consensus":
        return f"consensus {row.get('status','')} promote={row.get('promotion_recommended','')} support={row.get('support_ratio','')} contradict={row.get('contradiction_ratio','')} {row.get('subject','')} {row.get('predicate','')} {_compact(row.get('object'))}"
    return f"{table} {_compact(row)}"


def _lane_for(table: str, row: dict[str, Any], default: str) -> str:
    if table == "audit_events":
        event_type = str(row.get("event_type") or "").lower()
        if "media" in event_type or "source" in event_type or "ingest" in event_type:
            return "chat-user"
        if "witness" in event_type:
            return "witness-recurrent"
        if "memory" in event_type:
            return "memory-pressure"
    return default


def _severity(row: dict[str, Any]) -> str:
    text = str(row.get("severity") or row.get("status") or row.get("trust_status") or "info").lower()
    if any(word in text for word in ("critical", "fatal", "failed", "error", "rejected")):
        return "critical"
    if any(word in text for word in ("warning", "warn", "quarantine", "degraded", "candidate", "pending")):
        return "warning"
    if any(word in text for word in ("promoted", "active", "completed", "ok", "accepted")):
        return "notice"
    return "info"


def _compact(value: Any, limit: int = 1200) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:limit]
    try:
        return json.dumps(_json_safe(value), ensure_ascii=False, separators=(",", ":"))[:limit]
    except Exception:
        return str(value)[:limit]


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, bytes):
        return value.hex()
    return value


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default
