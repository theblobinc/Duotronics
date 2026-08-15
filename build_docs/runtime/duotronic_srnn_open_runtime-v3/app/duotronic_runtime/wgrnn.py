from __future__ import annotations

import json
import math
import threading
from functools import wraps
from pathlib import Path
from typing import Any

from .crypto_primitives import shake256_hex, shake256_ref
from .meta_graph import feature_content_ids

from .models import WGRNNMemoryUpdate, now_ms, stable_id


PROMOTABLE_ACTIONS = {"memory_write", "promote_witness"}
RISKY_ACTIONS = {"memory_write", "promote_witness", "external_action"}


def _synchronized(method):
    @wraps(method)
    def wrapped(self, *args: Any, **kwargs: Any):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapped


def _clamp01(v: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except Exception:
        return default


def _digest_payload(payload: Any) -> str:
    return shake256_ref(payload)


def _digest_vector(values: list[float]) -> str:
    payload = [round(float(v), 8) for v in values]
    return _digest_payload(payload)


def _namespace(user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> str:
    return "/".join([
        str(user_id or "system").strip() or "system",
        str(agent_id or "default-agent").strip() or "default-agent",
        str(thread_id or "default-thread").strip() or "default-thread",
    ])


def _safe_namespace_path(namespace: str) -> str:
    safe = namespace.replace("/", "__").replace("..", "_")
    return safe[:180]


def text_feature_vector(text: str, dim: int = 32) -> list[float]:
    """Deterministic small feature vector used for sandbox-mode recurrence.

    This is not a model embedding. It is a predictable runtime shim that lets the
    witness/memory/policy flow run anywhere without GPUs or model downloads.
    """
    dim = max(4, int(dim))
    buckets = [0.0] * dim
    if not text:
        return buckets
    raw = text.encode("utf-8", errors="ignore")
    for i, ch in enumerate(raw):
        buckets[(ch + i) % dim] += ((ch % 31) + 1) / 32.0
        buckets[(i * 17 + ch * 3) % dim] += ((ch % 17) + 1) / 64.0
    norm = math.sqrt(sum(v * v for v in buckets)) or 1.0
    return [round(v / norm, 6) for v in buckets]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(float(a[i]) * float(b[i]) for i in range(n))
    na = math.sqrt(sum(float(a[i]) ** 2 for i in range(n)))
    nb = math.sqrt(sum(float(b[i]) ** 2 for i in range(n)))
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return dot / (na * nb)


class WGRNNRuntime:
    """SRNN-facing WG-RNN runtime with governed, persistent memory writes.

    This is still the deterministic open-runtime shim, but it is no longer
    ephemeral: every namespace has durable recurrent state, slot state, and a
    witness ledger. It supports observe/memory modes, promote/reject/quarantine,
    replay verification, and lightweight retrieval over memory slots.
    """

    def __init__(
        self,
        *,
        loop_id: str,
        node_id: str,
        state_dim: int = 32,
        slot_dim: int = 32,
        num_slots: int = 64,
        data_dir: str | Path | None = None,
        store: Any | None = None,
    ) -> None:
        self.loop_id = loop_id
        self.node_id = node_id
        self.state_dim = max(int(state_dim), 4)
        self.slot_dim = max(int(slot_dim), 4)
        self.num_slots = max(int(num_slots), 4)
        self.data_dir = Path(data_dir or "/runtime/data/wgrnn")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = store
        self._lock = threading.RLock()
        self.namespace = _namespace()
        self.h = [0.0] * self.state_dim
        self.c = [0.0] * self.state_dim
        self.memory_bank = [[0.0] * self.slot_dim for _ in range(self.num_slots)]
        self.slot_meta = [self._empty_slot_meta(i) for i in range(self.num_slots)]
        self.ledger: list[dict[str, Any]] = []
        self.step_count = 0
        self.load_namespace(self.namespace)

    def _empty_slot_meta(self, slot_id: int) -> dict[str, Any]:
        return {
            "slot_id": slot_id,
            "trust_status": "empty",
            "authority_t": 0.0,
            "confidence": 0.0,
            "contradiction": 0.0,
            "update_id": None,
            "state_digest": None,
            "prompt_digest": None,
            "response_digest": None,
            "created_at_ms": None,
            "promoted_at_ms": None,
            "rejected_at_ms": None,
            "namespace": None,
            "tags": [],
        }

    def namespace_id(self, user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> str:
        return _namespace(user_id, agent_id, thread_id)

    def _state_path(self, namespace: str | None = None) -> Path:
        return self.data_dir / f"{_safe_namespace_path(namespace or self.namespace)}.state.json"

    def _ledger_path(self, namespace: str | None = None) -> Path:
        return self.data_dir / f"{_safe_namespace_path(namespace or self.namespace)}.ledger.jsonl"

    def _fit_vector(self, values: Any, dim: int) -> list[float]:
        """Pad/truncate persisted vectors so config dimension changes are safe."""
        try:
            raw = list(values or [])
        except Exception:
            raw = []
        fitted: list[float] = []
        for value in raw[:dim]:
            fitted.append(float(value))
        return (fitted + [0.0] * dim)[:dim]

    def load_namespace(self, namespace: str) -> None:
        self.namespace = namespace
        path = self._state_path(namespace)
        if not path.exists():
            self.h = [0.0] * self.state_dim
            self.c = [0.0] * self.state_dim
            self.memory_bank = [[0.0] * self.slot_dim for _ in range(self.num_slots)]
            self.slot_meta = [self._empty_slot_meta(i) for i in range(self.num_slots)]
            self.ledger = self._read_ledger(namespace)
            self.step_count = 0
            return
        data = json.loads(path.read_text())
        self.h = self._fit_vector(data.get("h"), self.state_dim)
        self.c = self._fit_vector(data.get("c"), self.state_dim)
        self.memory_bank = list(data.get("memory_bank", []))[: self.num_slots]
        while len(self.memory_bank) < self.num_slots:
            self.memory_bank.append([0.0] * self.slot_dim)
        self.memory_bank = [self._fit_vector(slot, self.slot_dim) for slot in self.memory_bank]
        self.slot_meta = list(data.get("slot_meta", []))[: self.num_slots]
        while len(self.slot_meta) < self.num_slots:
            self.slot_meta.append(self._empty_slot_meta(len(self.slot_meta)))
        self.step_count = int(data.get("step_count", 0))
        self.ledger = self._read_ledger(namespace)

    def _read_ledger(self, namespace: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        path = self._ledger_path(namespace)
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows[-limit:] if limit else rows

    def _write_state(self) -> None:
        path = self._state_path()
        payload = {
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "namespace": self.namespace,
            "state_dim": self.state_dim,
            "slot_dim": self.slot_dim,
            "num_slots": self.num_slots,
            "step_count": self.step_count,
            "h": self.h,
            "c": self.c,
            "memory_bank": self.memory_bank,
            "slot_meta": self.slot_meta,
            "updated_at_ms": now_ms(),
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2))
        tmp.replace(path)

    def _append_ledger(self, entry: dict[str, Any]) -> dict[str, Any]:
        entry = dict(entry)
        previous = self.ledger[-1].get("entry_digest") if self.ledger else None
        entry["previous_entry_digest"] = previous
        entry["entry_digest"] = _digest_payload({k: v for k, v in entry.items() if k != "entry_digest"})
        with self._ledger_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
        self.ledger.append(entry)
        return entry

    @_synchronized
    def snapshot(self, *, include_slots: bool = False, user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        if namespace != self.namespace:
            self.load_namespace(namespace)
        memory_digest_values = [x for slot in self.memory_bank for x in slot[:4]]
        out = {
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "namespace": self.namespace,
            "state_dim": self.state_dim,
            "slot_dim": self.slot_dim,
            "num_slots": self.num_slots,
            "step_count": self.step_count,
            "h": self.h,
            "c": self.c,
            "memory_bank_digest": _digest_vector(memory_digest_values),
            "ledger_entries": len(self.ledger),
            "promoted_slots": [m["slot_id"] for m in self.slot_meta if m.get("trust_status") == "promoted"],
            "candidate_slots": [m["slot_id"] for m in self.slot_meta if m.get("trust_status") == "candidate"],
            "quarantine_slots": [m["slot_id"] for m in self.slot_meta if m.get("trust_status") == "quarantine"],
        }
        if include_slots:
            out["slots"] = self.inspect_slots()
        return out

    @_synchronized
    def inspect_slots(self, *, status: str | None = None, limit: int = 128) -> list[dict[str, Any]]:
        rows = []
        for meta, slot in zip(self.slot_meta, self.memory_bank):
            if status and meta.get("trust_status") != status:
                continue
            row = dict(meta)
            row["slot_digest"] = _digest_vector(slot)
            row["nonzero"] = any(abs(float(v)) > 1e-9 for v in slot)
            rows.append(row)
        return rows[: max(1, min(int(limit), self.num_slots))]

    @_synchronized
    def retrieve(self, query: str, *, top_k: int = 8, include_empty: bool = False, user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        if namespace != self.namespace:
            self.load_namespace(namespace)
        q = text_feature_vector(query, self.slot_dim)

        # Vector similarity remains a useful retrieval signal, but it is no longer
        # treated as the ontology. 5.3.18 semantic/meta-object overlap supplies a
        # separate bounded ranking signal tied to witnessed candidate observations.
        graph_query_ids = feature_content_ids(query, limit=32)
        graph_search: dict[str, Any] = {"matches": [], "authority": "unavailable"}
        if self.store is not None:
            try:
                graph_search = self.store.search_meta_graph(
                    namespace=namespace,
                    query_content_ids=graph_query_ids,
                    limit=max(self.num_slots * 8, 256),
                )
            except Exception as exc:
                graph_search = {
                    "matches": [],
                    "authority": "candidate_ranking_signal_only",
                    "error": exc.__class__.__name__,
                }
        graph_by_update = {
            str(row.get("source_update_id")): row
            for row in (graph_search.get("matches") or [])
            if row.get("source_update_id")
        }

        results = []
        for slot, meta in zip(self.memory_bank, self.slot_meta):
            if not include_empty and meta.get("trust_status") in {"empty", None}:
                continue
            vector_score = cosine_similarity(q, slot)
            graph_match = graph_by_update.get(str(meta.get("update_id") or "")) or {}
            graph_score = float(graph_match.get("graph_score") or 0.0)
            # Graph evidence can boost/reorder candidates but cannot modify trust
            # status or create authority. Its contribution is deliberately bounded.
            score = float(vector_score) + 0.35 * graph_score
            results.append({
                "slot_id": meta.get("slot_id"),
                "score": round(score, 6),
                "vector_score": round(vector_score, 6),
                "graph_score": round(graph_score, 6),
                "graph_overlap_count": int(graph_match.get("overlap_count") or 0),
                "graph_recurrence_support": int(graph_match.get("recurrence_support") or 0),
                "graph_shared_source_recurrence_support": int(graph_match.get("shared_source_recurrence_support") or 0),
                "graph_shared_source_recurrence_score": round(float(graph_match.get("shared_source_recurrence_score") or 0.0), 6),
                "graph_shared_adapter_recurrence_support": int(graph_match.get("shared_adapter_recurrence_support") or 0),
                "graph_shared_adapter_recurrence_score": round(float(graph_match.get("shared_adapter_recurrence_score") or 0.0), 6),
                "graph_local_score": round(float(graph_match.get("local_graph_score") or 0.0), 6),
                "graph_observation_id": graph_match.get("observation_id"),
                "trust_status": meta.get("trust_status"),
                "authority_t": meta.get("authority_t"),
                "confidence": meta.get("confidence"),
                "update_id": meta.get("update_id"),
                "state_digest": meta.get("state_digest"),
                "slot_digest": _digest_vector(slot),
            })
        results.sort(key=lambda r: (r["score"], r.get("authority_t") or 0.0), reverse=True)
        return {
            "namespace": self.namespace,
            "query_digest": _digest_payload(query),
            "top_k": top_k,
            "graph_query_content_ids": graph_query_ids,
            "graph_authority": graph_search.get("authority") or "candidate_ranking_signal_only",
            "graph_error": graph_search.get("error"),
            "results": results[: max(1, int(top_k))],
        }

    def _slot_for(self, requested_action: str, prompt: str, namespace: str) -> int:
        key = f"{namespace}\n{requested_action}\n{prompt[:256]}"
        digest = shake256_hex(key)
        base = int(digest[:12], 16) % self.num_slots
        prompt_digest = _digest_payload(prompt)

        # Recurrent updates for the same feature category should reuse a candidate
        # slot, but a promoted slot is immutable and must never be overwritten.
        for offset in range(self.num_slots):
            slot_id = (base + offset) % self.num_slots
            meta = self.slot_meta[slot_id]
            if meta.get("prompt_digest") == prompt_digest and meta.get("trust_status") != "promoted":
                return slot_id

        # Prefer empty/rejected capacity, then quarantine, then the weakest
        # non-promoted candidate. This keeps promoted operational knowledge stable.
        for preferred in ({"empty", "rejected", None}, {"quarantine"}):
            for offset in range(self.num_slots):
                slot_id = (base + offset) % self.num_slots
                if self.slot_meta[slot_id].get("trust_status") in preferred:
                    return slot_id

        candidates = [
            meta for meta in self.slot_meta
            if meta.get("trust_status") != "promoted"
        ]
        if not candidates:
            raise RuntimeError("WG-RNN memory is full of promoted slots; review or expand capacity")
        weakest = min(candidates, key=lambda meta: (float(meta.get("authority_t") or 0.0), int(meta.get("created_at_ms") or 0)))
        return int(weakest["slot_id"])

    @_synchronized
    def step(
        self,
        *,
        prompt: str,
        response_text: str,
        requested_action: str = "observe",
        evidence_quality: float = 0.72,
        user_id: str | None = None,
        agent_id: str | None = None,
        thread_id: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        if namespace != self.namespace:
            self.load_namespace(namespace)
        # Runtime dimensions are configurable. Older persisted namespaces may be
        # shorter than the active config; normalize again before indexing.
        self.h = self._fit_vector(self.h, self.state_dim)
        self.c = self._fit_vector(self.c, self.state_dim)
        self.step_count += 1
        tags = list(tags or [])
        text = f"{namespace}\n{requested_action}\n{prompt}\n{response_text}"
        x = text_feature_vector(text, self.state_dim)
        confidence = _clamp01(evidence_quality, 0.5)
        contradiction = _clamp01(1.0 - confidence, 0.0)
        action_risk = 0.35 if requested_action in RISKY_ACTIONS else 0.1
        authority = _clamp01(0.62 * confidence + 0.22 * (1.0 - contradiction) - action_risk * 0.18, 0.0)

        old_h = list(self.h)
        old_c = list(self.c)
        self.h = [round(max(-1.0, min(1.0, self.h[i] * 0.90 + x[i] * 0.10)), 6) for i in range(self.state_dim)]
        self.c = [round(max(-1.0, min(1.0, self.c[i] * 0.94 + self.h[i] * 0.06)), 6) for i in range(self.state_dim)]

        slot_id = self._slot_for(requested_action, prompt, namespace)
        slot = self.memory_bank[slot_id]
        update_kind = "candidate_write" if authority >= 0.50 and requested_action != "promote_witness" else "quarantine_write"
        trust_status = "candidate" if update_kind == "candidate_write" else "quarantine"
        if requested_action == "observe":
            # Observations can become candidates but should not be auto-promoted.
            update_kind = "candidate_write" if authority >= 0.55 else "quarantine_write"
            trust_status = "candidate" if update_kind == "candidate_write" else "quarantine"
        for i in range(min(self.slot_dim, len(self.h))):
            slot[i] = round(max(-1.0, min(1.0, slot[i] * 0.88 + self.h[i] * authority * 0.12)), 6)
        self.memory_bank[slot_id] = slot

        state_digest = _digest_vector(self.h + self.c + slot[: min(8, len(slot))])
        update_payload = {
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "namespace": namespace,
            "slot_id": slot_id,
            "step_count": self.step_count,
            "requested_action": requested_action,
            "authority": authority,
            "confidence": confidence,
            "contradiction": contradiction,
            "prompt_digest": _digest_payload(prompt),
            "response_digest": _digest_payload(response_text),
            "state_digest": state_digest,
        }
        update = WGRNNMemoryUpdate(
            update_id=stable_id("wgrnn_update", update_payload),
            loop_id=self.loop_id,
            node_id=self.node_id,
            slot_id=slot_id,
            update_kind=update_kind,
            trust_status=trust_status,
            authority_t=round(authority, 6),
            confidence=round(confidence, 6),
            contradiction=round(contradiction, 6),
            affected_slot_ids=[slot_id],
            replay_identity_ref=_digest_payload(update_payload),
            state_digest=state_digest,
            created_at_ms=now_ms(),
        )
        self.slot_meta[slot_id] = {
            "slot_id": slot_id,
            "trust_status": trust_status,
            "authority_t": round(authority, 6),
            "confidence": round(confidence, 6),
            "contradiction": round(contradiction, 6),
            "update_id": update.update_id,
            "state_digest": state_digest,
            "prompt_digest": _digest_payload(prompt),
            "response_digest": _digest_payload(response_text),
            "created_at_ms": update.created_at_ms,
            "promoted_at_ms": None,
            "rejected_at_ms": None,
            "namespace": namespace,
            "tags": tags,
        }
        ledger_entry = self._append_ledger({
            "event": "wgrnn.step",
            "namespace": namespace,
            "loop_id": self.loop_id,
            "node_id": self.node_id,
            "update": update.to_dict(),
            "requested_action": requested_action,
            "prompt_digest": _digest_payload(prompt),
            "response_digest": _digest_payload(response_text),
            "old_state_digest": _digest_vector(old_h + old_c),
            "new_state_digest": _digest_vector(self.h + self.c),
            "slot_digest": _digest_vector(slot),
            "created_at_ms": now_ms(),
            "tags": tags,
        })
        self._write_state()
        return {
            "runtime_status": "persistent_authoritative_shim",
            "namespace": namespace,
            "activation_vector": list(self.h),
            "memory_update": update.to_dict(),
            "ledger_entry": ledger_entry,
            "retrieval_preview": self.retrieve(
                prompt, top_k=3, user_id=user_id, agent_id=agent_id, thread_id=thread_id
            ),
            "snapshot": self.snapshot(
                user_id=user_id, agent_id=agent_id, thread_id=thread_id
            ),
        }

    @_synchronized
    def promote(self, *, slot_id: int, reason: str = "manual_promote", user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        if namespace != self.namespace:
            self.load_namespace(namespace)
        slot_id = int(slot_id)
        if slot_id < 0 or slot_id >= self.num_slots:
            raise ValueError("slot_id out of range")
        meta = dict(self.slot_meta[slot_id])
        if meta.get("trust_status") not in {"candidate", "quarantine"}:
            return {"promoted": False, "reason": "slot_not_promotable", "slot": meta}
        meta["trust_status"] = "promoted"
        meta["promoted_at_ms"] = now_ms()
        self.slot_meta[slot_id] = meta
        entry = self._append_ledger({"event": "wgrnn.promote", "namespace": namespace, "slot_id": slot_id, "reason": reason, "slot": meta, "created_at_ms": now_ms()})
        self._write_state()
        return {"promoted": True, "slot": meta, "ledger_entry": entry}

    @_synchronized
    def reject(self, *, slot_id: int, reason: str = "manual_reject", user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        if namespace != self.namespace:
            self.load_namespace(namespace)
        slot_id = int(slot_id)
        if slot_id < 0 or slot_id >= self.num_slots:
            raise ValueError("slot_id out of range")
        meta = dict(self.slot_meta[slot_id])
        meta["trust_status"] = "rejected"
        meta["rejected_at_ms"] = now_ms()
        self.slot_meta[slot_id] = meta
        entry = self._append_ledger({"event": "wgrnn.reject", "namespace": namespace, "slot_id": slot_id, "reason": reason, "slot": meta, "created_at_ms": now_ms()})
        self._write_state()
        return {"rejected": True, "slot": meta, "ledger_entry": entry}

    @_synchronized
    def quarantine(self, *, slot_id: int, reason: str = "manual_quarantine", user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        if namespace != self.namespace:
            self.load_namespace(namespace)
        slot_id = int(slot_id)
        if slot_id < 0 or slot_id >= self.num_slots:
            raise ValueError("slot_id out of range")
        meta = dict(self.slot_meta[slot_id])
        meta["trust_status"] = "quarantine"
        self.slot_meta[slot_id] = meta
        entry = self._append_ledger({"event": "wgrnn.quarantine", "namespace": namespace, "slot_id": slot_id, "reason": reason, "slot": meta, "created_at_ms": now_ms()})
        self._write_state()
        return {"quarantined": True, "slot": meta, "ledger_entry": entry}

    @_synchronized
    def ledger_tail(self, *, limit: int = 50, user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        rows = self._read_ledger(namespace, limit=max(1, min(int(limit), 500)))
        return {"namespace": namespace, "count": len(rows), "entries": rows}

    @_synchronized
    def verify_replay(self, *, user_id: str | None = None, agent_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        namespace = self.namespace_id(user_id, agent_id, thread_id)
        rows = self._read_ledger(namespace)
        previous = None
        failures = []
        for i, row in enumerate(rows):
            expected_prev = row.get("previous_entry_digest")
            if expected_prev != previous:
                failures.append({"index": i, "reason": "previous_digest_mismatch", "expected": previous, "actual": expected_prev})
            digest = row.get("entry_digest")
            recalculated = _digest_payload({k: v for k, v in row.items() if k != "entry_digest"})
            if digest != recalculated:
                failures.append({"index": i, "reason": "entry_digest_mismatch", "expected": recalculated, "actual": digest})
            previous = digest
        return {"namespace": namespace, "verified": not failures, "entries": len(rows), "failures": failures[:20]}
