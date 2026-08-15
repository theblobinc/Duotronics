from __future__ import annotations

"""Witness-gated autonomous learning and self-development substrate for Xavi.

This module intentionally composes existing Duotronics primitives instead of
creating an independent agent framework:

* SessionLedger: append-only, hash-chained interaction/event history.
* WG-RNN: candidate/promoted/quarantined recurrent memory and replay ledger.
* EvidenceKernel: witness generation and non-collapse semantics.
* PostgreSQL source index: searchable provenance-bound source material.
* Duotronic bijective positive-baseline math: deterministic positive ordinals,
  slot identities and score projections.

The architecture also incorporates permissively licensed implementation ideas
from pinned local source references under /var/www/xavi/vendor/
xavi-integration-references. See VENDOR_PROVENANCE below. In particular:

* SceneProof: evidence bundles, reference comparison and source bundles.
* cognicore-my-openenv: memory events, context preservation and trajectory analysis.
* truthmark: workflow state, write leases and truth/workflow separation.
* Forge: lifecycle events, task observability, terminal/task artifacts.
* Argentos: session/memory/tool surfaces and sandboxed capability composition.
* LoongFlow: Planner-Executor-Summary separation and evolutionary memory/islands.

The Witness Contract remains the authority boundary. Autonomous operational
promotion is distinct from theorem/release/authority promotion; the latter is
never inferred merely from model output, passing tests or this module.
"""

import json
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .duotronic_bijective import (
    REFERENCE_SHAKE256_512 as BIJECTIVE_REFERENCE_SHAKE256_512,
    bounded_score_codeword,
    positive_index_payload,
    positive_ordinal_payload,
)
from .crypto_primitives import shake256_file, shake256_ref
from .meta_graph import build_information_graph
from .session_ledger import SessionLedger

AUTONOMY_SCHEMA = "xavi-wgrnn-autonomy/v1"
CONTRACT_REF = "Witness Contract v1.6 Draft 5.3.18"
CONTRACT_PATH = "build_docs/witness_contract/v1.6 - Draft 5.3.18"

VENDOR_PROVENANCE: dict[str, dict[str, str]] = {
    "SceneProof": {
        "origin": "https://github.com/ReyJ94/SceneProof",
        "commit": "cc52dee5a2365a62f24f77559df855b37361aa68",
        "legacy_license_hash_indicator": "572d3a5d46a790e5caa2a52107b0fb9829a87fe5a58f61b152e186a098150566",
    },
    "cognicore-my-openenv": {
        "origin": "https://github.com/cognicore-dev/cognicore-my-openenv",
        "commit": "31b2c32fc0befd2e647573bad9c86dc941569c59",
        "legacy_license_hash_indicator": "1fda5c1f38609c91d4ef26aeb1e5e0767c9ae0f17f7740cb764b53ec219d679e",
    },
    "truthmark": {
        "origin": "https://github.com/merlinhu1/truthmark",
        "commit": "5050eb0fb7829c974d4cfc8daecb888f44ef8747",
        "legacy_license_hash_indicator": "3b511f5a6aec6c68ab6f1b217a1e33f2d311d13137efc01c3485fa1ec87983ec",
    },
    "forge": {
        "origin": "https://github.com/ForgeAILab/forge",
        "commit": "a3cf8deb06c92d4df9b672122f791fc0913dd8d3",
        "legacy_license_hash_indicator": "7954f1ecfbd861b92c7b91d9d542c1cda02d5d86c0e5edcf6e9c3978d872acd2",
    },
    "argentos-core": {
        "origin": "https://github.com/ArgentAIOS/argentos-core",
        "commit": "acbf92944b9748c74691808953f580f1cd1fee9a",
        "legacy_license_hash_indicator": "8d9e8a72e6c0f2833775f58d5849bacbf23b4a4071a9a7ece3e7773cb0f6863f",
    },
    "LoongFlow": {
        "origin": "https://github.com/baidu-baige/LoongFlow",
        "commit": "945c78bc1554f8281aac40320b3599bd68d528d7",
        "legacy_license_hash_indicator": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    },
}

_SECRET_KEY = re.compile(
    r"password|passwd|secret|token|api[_-]?key|authorization|cookie|credential|private[_-]?key|dsn|database[_-]?url",
    re.I,
)
_TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".rs", ".ts", ".tsx", ".js", ".jsx",
    ".sql", ".lean", ".tla", ".toml", ".csv", ".xml", ".html", ".css", ".ini", ".cfg", ".log",
}
ACTION_EVENT_TYPES = {
    "mcp_call_start", "cli_command", "tool_call", "code_patch", "code_candidate", "workflow_action", "deployment_action",
    "delegated_tool_action",
}
OBSERVATION_EVENT_TYPES = {
    "mcp_call_result", "mcp_call_error", "tool_result", "cli_result", "evaluation_result", "environment_observation",
    "delegated_tool_result", "delegated_tool_error",
}
CONTEXT_EVENT_TYPES = {
    "chat_message", "context_assembly", "model_prompt", "source_retrieval", "memory_retrieval", "system_context",
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _digest(value: Any) -> str:
    return shake256_ref(value)


def _file_shake256(path: Path) -> str:
    return shake256_file(path)


def _jsonl_append(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(_canonical(value) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def _jsonl_read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def sanitize_training_value(value: Any, *, depth: int = 0) -> Any:
    """Remove direct credential plaintext from derived training material.

    The runtime may resolve/use secrets through SecretCapabilityMemory, but
    gradient/evaluation corpora store capability references and digests rather
    than credential values. This preserves revocation and rotation.
    """

    if depth > 10:
        return {"redacted": "max_depth", "digest": _digest(value)}
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _SECRET_KEY.search(str(key)):
                out[str(key)] = {"secret_ref_only": True, "value_digest": _digest(item)}
            else:
                out[str(key)] = sanitize_training_value(item, depth=depth + 1)
        return out
    if isinstance(value, list):
        return [sanitize_training_value(item, depth=depth + 1) for item in value]
    if isinstance(value, tuple):
        return [sanitize_training_value(item, depth=depth + 1) for item in value]
    if isinstance(value, str) and len(value) > 200_000:
        return {"text": value[:200_000], "truncated": len(value) - 200_000, "digest": _digest(value)}
    return value


@dataclass(frozen=True)
class EvaluationCheck:
    name: str
    passed: bool
    score: float = 1.0
    required: bool = True
    evidence_ref: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        score = max(0.0, min(1.0, float(self.score)))
        return {
            "name": self.name,
            "passed": bool(self.passed),
            "score": score,
            "score_duotronic": bounded_score_codeword(score),
            "required": bool(self.required),
            "evidence_ref": self.evidence_ref,
            "details": self.details or {},
        }


class SecretCapabilityMemory:
    """Stores rotatable secret *references*, never a training copy of plaintext."""

    def __init__(self, root: Path) -> None:
        self.path = root / "secret_capabilities.json"

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": "secret-capability-index/v1", "items": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"schema_version": "secret-capability-index/v1", "items": {}, "corrupt": True}
        data.setdefault("schema_version", "secret-capability-index/v1")
        data.setdefault("items", {})
        return data

    def register(self, *, name: str, resolver: str, locator: str, capabilities: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if resolver not in {"env", "file", "external-store", "mcp"}:
            raise ValueError("unsupported secret resolver")
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("secret capability name is required")
        index = self._read()
        item = {
            "name": clean_name,
            "resolver": resolver,
            "locator": locator if resolver in {"env", "file"} else None,
            "locator_digest": _digest(locator),
            "capabilities": sorted(set(capabilities or [])),
            "metadata": metadata or {},
            "updated_at_ms": _now_ms(),
        }
        item["ref"] = "secret://" + clean_name
        index["items"][clean_name] = item
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return item

    def list(self) -> dict[str, Any]:
        data = self._read()
        return {
            "schema_version": data.get("schema_version"),
            "items": [{k: v for k, v in item.items() if k != "locator"} for item in data.get("items", {}).values()],
        }

    def resolve_internal(self, ref: str) -> str:
        """Resolve a secret internally. Never expose this method as an MCP tool."""

        name = str(ref).removeprefix("secret://")
        item = self._read().get("items", {}).get(name)
        if not item:
            raise KeyError(f"unknown secret capability: {ref}")
        resolver = item.get("resolver")
        locator = item.get("locator")
        if resolver == "env":
            value = os.environ.get(str(locator), "")
            if not value:
                raise RuntimeError(f"secret environment variable unavailable for {ref}")
            return value
        if resolver == "file":
            path = Path(str(locator))
            return path.read_text(encoding="utf-8").strip()
        raise RuntimeError(f"secret resolver {resolver!r} requires its external adapter")


class AutonomyStack:
    """Unified witnessed autonomy stack implementing the eight requested layers."""

    def __init__(self, kernel: Any, root: str | Path | None = None) -> None:
        self.kernel = kernel
        self.root = Path(root) if root is not None else Path(kernel.settings.runtime_data_dir) / "autonomy"
        self.root.mkdir(parents=True, exist_ok=True)
        self.ledger = SessionLedger(root=Path(kernel.settings.runtime_data_dir) / "session_ledger", store=kernel.store)
        self.secrets = SecretCapabilityMemory(self.root)
        self.trajectories_path = self.root / "trajectories.jsonl"
        self.artifacts_path = self.root / "artifacts.jsonl"
        self.evaluations_path = self.root / "evaluations.jsonl"
        self.candidates_path = self.root / "candidates.jsonl"
        self.resources_path = self.root / "resource_snapshots.jsonl"
        self.promotion_path = self.root / "promotion_decisions.jsonl"
        self.experiments_path = self.root / "self_experiments.jsonl"
        self.experiment_results_path = self.root / "self_experiment_results.jsonl"
        self.training_dir = self.root / "training"

    def provenance(self) -> dict[str, Any]:
        return {
            "schema_version": "xavi-autonomy-provenance/v1",
            "witness_contract": {"ref": CONTRACT_REF, "path": CONTRACT_PATH},
            "duotronic_bijective_reference_shake256_512": BIJECTIVE_REFERENCE_SHAKE256_512,
            "vendor_sources": VENDOR_PROVENANCE,
        }

    def status(self) -> dict[str, Any]:
        index = self.ledger.index()
        return {
            "schema_version": AUTONOMY_SCHEMA,
            "status": "active",
            "mode": "witness-gated-autonomous",
            "session_count": len(index.get("sessions", {})),
            "trajectory_count": len(_jsonl_read(self.trajectories_path)),
            "artifact_count": len(_jsonl_read(self.artifacts_path)),
            "evaluation_count": len(_jsonl_read(self.evaluations_path)),
            "candidate_count": len(_jsonl_read(self.candidates_path)),
            "resource_snapshot_count": len(_jsonl_read(self.resources_path)),
            "self_experiment_count": len(_jsonl_read(self.experiments_path)),
            "self_experiment_result_count": len(_jsonl_read(self.experiment_results_path)),
            "self_experimentation": "continuous-observer-driven",
            "operational_auto_promotion": True,
            "authority_auto_promotion": False,
            "secret_model": "rotatable-capability-reference",
            "provenance": self.provenance(),
        }

    def record_event(
        self,
        *,
        session_id: str,
        event_type: str,
        actor: str,
        content: dict[str, Any],
        tags: list[str] | None = None,
        witness_id: str | None = None,
        training_eligible: bool = True,
        redaction: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = dict(content)
        payload.setdefault("autonomy_schema", AUTONOMY_SCHEMA)
        payload.setdefault("contract_ref", CONTRACT_REF)
        event_tags = sorted(set((tags or []) + ["xavi-autonomy", "witnessed-event"]))
        event = self.ledger.append(
            session_id=session_id,
            event_type=event_type,
            actor=actor,
            content=payload,
            tags=event_tags,
            witness_id=witness_id,
            training_eligible=training_eligible,
            redaction=redaction or {},
        )

        # Build one redaction-aware information view that both recurrent learning
        # and the 5.3.18 candidate meta graph can observe. Redacted payload bodies
        # never cross this boundary; only their witnessed event identity does.
        redaction_info = redaction or {}
        if redaction_info:
            observed_for_graph = {
                "session_id": session_id,
                "event_type": event_type,
                "actor": actor,
                "event_digest": event.get("event_digest"),
                "witness_id": witness_id,
                "tags": event_tags,
                "redaction_present": True,
            }
        else:
            observed_for_graph = {
                "session_id": session_id,
                "event_type": event_type,
                "actor": actor,
                "content": payload,
                "event_digest": event.get("event_digest"),
                "witness_id": witness_id,
                "tags": event_tags,
                "redaction_present": False,
            }

        graph_user_id = f"conversation-source:{str(payload.get('conversation_source') or 'runtime')[:80]}"
        graph_agent_id = str(payload.get("agent_id") or actor or "self")[:256]
        graph_thread_id = (
            f"conversation:{str(payload.get('conversation_id'))[:256]}"
            if payload.get("conversation_id")
            else f"session:{session_id}"
        )
        graph_namespace = self.kernel.wgrnn.namespace_id(graph_user_id, graph_agent_id, graph_thread_id)

        # Training-eligible session/MCP/tool events become immediate candidate
        # autobiographical recurrence as well as durable transcript rows.  WG-RNN
        # chat turns already write the self tier explicitly in finalize_turn, so
        # skip them here to avoid double-updating the same event.
        recurrent_learning = None
        if training_eligible and event_type != "wgrnn_chat_turn":
            try:
                observed = observed_for_graph
                observed_text = _canonical(observed)
                if len(observed_text) > 16000:
                    observed_text = observed_text[:16000] + "...[bounded]"
                recurrent_learning = self.kernel.wgrnn.step(
                    prompt="Observed training-eligible runtime/session event: " + observed_text,
                    response_text="",
                    requested_action="observe",
                    evidence_quality=0.72,
                    user_id=graph_user_id,
                    agent_id=graph_agent_id,
                    thread_id=graph_thread_id,
                    tags=[
                        "autobiographical-memory",
                        "session-event",
                        "candidate-training",
                        f"event:{event_type}",
                        f"actor:{actor}",
                    ],
                ).get("memory_update")
            except Exception as exc:
                recurrent_learning = {"status": "error", "error": exc.__class__.__name__}
        if recurrent_learning is not None:
            event = {**event, "recurrent_learning": recurrent_learning}

        meta_graph_event = None
        if event_type != "wgrnn_chat_turn":
            try:
                graph_text = _canonical(observed_for_graph)
                if len(graph_text) > 16000:
                    graph_text = graph_text[:16000] + "...[bounded]"
                graph = build_information_graph(
                    information_kind=f"runtime_event/{event_type}",
                    text_fields={"event": graph_text},
                    facets={
                        "event_type": event_type,
                        "actor": actor,
                        "training_eligible": bool(training_eligible),
                        "redaction_present": bool(redaction_info),
                        "tags": event_tags,
                        "payload": (
                            payload
                            if not redaction_info
                            else {
                                "event_digest": event.get("event_digest"),
                                "redaction_present": True,
                            }
                        ),
                    },
                    metadata={
                        "session_id": session_id,
                        "event_digest": event.get("event_digest"),
                        "witness_id": witness_id,
                        "contract_ref": CONTRACT_REF,
                    },
                )
                source_update_id = None
                graph_trust = "candidate"
                if isinstance(recurrent_learning, dict):
                    source_update_id = str(recurrent_learning.get("update_id") or "") or None
                    candidate_trust = str(recurrent_learning.get("trust_status") or "candidate")
                    if candidate_trust in {"candidate", "quarantine", "promoted", "rejected"}:
                        graph_trust = candidate_trust
                meta_graph_event = self.kernel.store.insert_meta_graph_observation(
                    graph=graph,
                    namespace=graph_namespace,
                    source_update_id=source_update_id,
                    trust_status=graph_trust,
                    observed_at_ms=_now_ms(),
                    metadata={
                        "event_type": event_type,
                        "actor": actor,
                        "training_eligible": bool(training_eligible),
                        "redaction_present": bool(redaction_info),
                        "authority": "candidate_observation_only",
                    },
                )
            except Exception as exc:
                meta_graph_event = {
                    "schema_version": "meta_graph_persist_result/v1",
                    "status": "error",
                    "error": exc.__class__.__name__,
                    "authority": "candidate_observation_only",
                }
        if meta_graph_event is not None:
            event = {**event, "meta_graph": meta_graph_event}
        return event

    def _experiment_proposal(self, experiment_id: str) -> dict[str, Any] | None:
        experiment_id = str(experiment_id or "").strip()
        if not experiment_id:
            return None
        for row in reversed(_jsonl_read(self.experiments_path)):
            if str(row.get("experiment_id") or "") == experiment_id:
                return row
        return None

    def _experiment_latest_results(self) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in _jsonl_read(self.experiment_results_path):
            experiment_id = str(row.get("experiment_id") or "")
            if experiment_id:
                latest[experiment_id] = row
        return latest

    def propose_experiment(
        self,
        *,
        subject: str,
        predicate: str,
        object_value: Any,
        question: str | None = None,
        hypothesis: str | None = None,
        experiment_kind: str = "observer_consensus",
        falsification: str | None = None,
        observer_plan: list[str] | None = None,
        minimum_independent_groups: int = 3,
        min_support_ratio: float = 0.75,
        max_contradiction_ratio: float = 0.20,
        priority: int = 50,
        origin: str = "wg-rnn:self",
        metadata: dict[str, Any] | None = None,
        session_id: str = "wg-rnn:self-experimentation",
    ) -> dict[str, Any]:
        subject = str(subject or "").strip()
        predicate = str(predicate or "").strip()
        if not subject or not predicate:
            raise ValueError("experiment subject and predicate are required")
        consensus = getattr(self.kernel, "consensus", None)
        if consensus is None:
            raise RuntimeError("observer consensus engine unavailable")
        claim_key = consensus.claim_key(subject, predicate, object_value)
        latest_results = self._experiment_latest_results()
        for row in reversed(_jsonl_read(self.experiments_path)):
            if row.get("claim_key") != claim_key:
                continue
            last = latest_results.get(str(row.get("experiment_id") or "")) or {}
            if str(last.get("status") or "") not in {"completed_supported", "completed_disputed", "completed_inconclusive", "cancelled"}:
                return {"experiment": row, "reused_open_experiment": True}

        plan = list(observer_plan or ["independent_model", "internet_search", "document_corpus"])
        payload = {
            "schema_version": "wg-rnn-self-experiment/v1",
            "experiment_kind": str(experiment_kind or "observer_consensus"),
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "claim_key": claim_key,
            "question": str(question or f"What independent evidence supports or contradicts {subject} {predicate} {object_value!r}?").strip(),
            "hypothesis": str(hypothesis or f"{subject} {predicate} {object_value!r}").strip(),
            "falsification": str(
                falsification
                or f"Treat the hypothesis as disputed if contradiction ratio exceeds {max_contradiction_ratio:.2f}; do not promote without independent quorum."
            ).strip(),
            "observer_plan": plan,
            "minimum_independent_groups": max(1, min(int(minimum_independent_groups), 32)),
            "min_support_ratio": max(0.0, min(float(min_support_ratio), 1.0)),
            "max_contradiction_ratio": max(0.0, min(float(max_contradiction_ratio), 1.0)),
            "priority": max(0, min(int(priority), 100)),
            "origin": str(origin or "wg-rnn:self"),
            "metadata": sanitize_training_value(metadata or {}),
            "promotion_policy": "recommendation_only_existing_witness_gate_required",
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        payload["experiment_id"] = "experiment_" + _digest(payload).split(":", 1)[1][:24]
        witness = self.kernel.evidence.witness(
            "SelfExperimentPlanWitness",
            payload,
            force="propose",
            status="candidate",
        )
        row = {**payload, "status": "proposed", "witness": witness}
        _jsonl_append(self.experiments_path, row)
        self.record_event(
            session_id=session_id,
            event_type="self_experiment_proposed",
            actor="wg-rnn:self",
            content={
                "experiment_id": payload["experiment_id"],
                "claim_key": claim_key,
                "question": payload["question"],
                "hypothesis": payload["hypothesis"],
                "observer_plan": plan,
                "witness_id": witness.get("witness_id"),
            },
            tags=["self-experiment", "hypothesis", "candidate-training", str(experiment_kind)],
            witness_id=witness.get("witness_id"),
            training_eligible=True,
        )
        return {"experiment": row, "reused_open_experiment": False}

    def list_experiments(self, *, limit: int = 50, status: str | None = None) -> dict[str, Any]:
        proposals = _jsonl_read(self.experiments_path)
        latest_results = self._experiment_latest_results()
        items: list[dict[str, Any]] = []
        for proposal in reversed(proposals):
            experiment_id = str(proposal.get("experiment_id") or "")
            result = latest_results.get(experiment_id)
            current_status = str((result or {}).get("status") or proposal.get("status") or "proposed")
            if status and current_status != status:
                continue
            items.append({**proposal, "current_status": current_status, "latest_result": result})
            if len(items) >= max(1, min(int(limit), 200)):
                break
        return {
            "schema_version": "wg-rnn-self-experiment-index/v1",
            "count": len(items),
            "items": items,
        }

    def next_experiment(self, *, session_id: str = "wg-rnn:self-experimentation") -> dict[str, Any]:
        proposals = _jsonl_read(self.experiments_path)
        latest_results = self._experiment_latest_results()
        open_rows: list[dict[str, Any]] = []
        terminal = {"completed_supported", "completed_disputed", "completed_inconclusive", "cancelled"}
        for row in proposals:
            experiment_id = str(row.get("experiment_id") or "")
            result = latest_results.get(experiment_id) or {}
            if str(result.get("status") or "") not in terminal:
                open_rows.append(row)
        if open_rows:
            open_rows.sort(key=lambda row: (int(row.get("priority") or 0), -int(row.get("created_at_ms") or 0)), reverse=True)
            return {"status": "open_experiment", "experiment": open_rows[0], "selected_by": "existing_open_experiment"}

        consensus = getattr(self.kernel, "consensus", None)
        if consensus is None:
            return {"status": "unavailable", "reason": "observer_consensus_engine_unavailable"}
        candidates = consensus.recent(limit=100)
        rank = {"disputed": 100, "candidate_consensus": 85, "insufficient_observers": 75, "unresolved": 65}
        candidates = [
            row for row in candidates
            if not bool(row.get("promotion_recommended")) and str(row.get("status") or "") in rank
        ]
        if candidates:
            candidates.sort(
                key=lambda row: (
                    rank.get(str(row.get("status") or ""), 0),
                    float(row.get("contradiction_ratio") or 0.0),
                    -int(row.get("independent_groups") or 0),
                ),
                reverse=True,
            )
            row = candidates[0]
            proposed = self.propose_experiment(
                subject=str(row.get("subject") or ""),
                predicate=str(row.get("predicate") or ""),
                object_value=row.get("object"),
                question=(
                    "Independently test this unresolved claim. Seek evidence that could falsify it as actively as evidence that could support it: "
                    + f"{row.get('subject')} {row.get('predicate')} {row.get('object')!r}."
                ),
                hypothesis=f"{row.get('subject')} {row.get('predicate')} {row.get('object')!r}",
                experiment_kind="observer_consensus",
                falsification=(
                    "A materially independent contradiction, reproducible counterexample, failed benchmark, or source conflict counts against the hypothesis. "
                    "Repeated outputs from the same model/source family do not create quorum."
                ),
                observer_plan=["independent_model", "internet_search", "document_corpus", "formal_or_sensor_if_applicable"],
                minimum_independent_groups=3,
                min_support_ratio=0.75,
                max_contradiction_ratio=0.20,
                priority=rank.get(str(row.get("status") or ""), 50),
                origin="wg-rnn:consensus-gap",
                metadata={
                    "prior_status": row.get("status"),
                    "prior_support_ratio": row.get("support_ratio"),
                    "prior_contradiction_ratio": row.get("contradiction_ratio"),
                    "prior_independent_groups": row.get("independent_groups"),
                },
                session_id=session_id,
            )
            return {"status": "new_experiment", **proposed, "selected_by": "consensus_gap"}

        # Bootstrap consensus research from ordinary evidence claims when no
        # consensus record exists yet. Conversation, MCP, document, and sensor
        # claims are all peers here; none receives privileged truth status.
        try:
            evidence_rows = self.kernel.store.fetch_recent("evidence_claims", 80)
        except Exception:
            evidence_rows = []
        for row in evidence_rows:
            if str(row.get("claim_kind") or "") == "observer_consensus":
                continue
            subject = str(row.get("subject") or "").strip()
            predicate = str(row.get("predicate") or "").strip()
            if not subject or not predicate:
                continue
            proposed = self.propose_experiment(
                subject=subject,
                predicate=predicate,
                object_value=row.get("object"),
                question=f"Collect independent observations for an unevaluated evidence claim: {subject} {predicate} {row.get('object')!r}.",
                experiment_kind="observer_consensus",
                observer_plan=["independent_model", "internet_search", "document_corpus"],
                priority=55,
                origin="wg-rnn:evidence-claim-bootstrap",
                metadata={"source_claim_id": row.get("claim_id"), "epistemic_status": row.get("epistemic_status")},
                session_id=session_id,
            )
            return {"status": "new_experiment", **proposed, "selected_by": "unevaluated_evidence_claim"}
        return {"status": "idle", "reason": "no_unresolved_claim_available"}

    def experiment_observe(
        self,
        *,
        experiment_id: str,
        observer_id: str,
        observer_kind: str,
        independence_group: str,
        stance: str,
        confidence: float,
        observation: str | None = None,
        source_ref: str | None = None,
        evidence_refs: list[str] | None = None,
        measurement: dict[str, Any] | None = None,
        session_id: str = "wg-rnn:self-experimentation",
    ) -> dict[str, Any]:
        experiment = self._experiment_proposal(experiment_id)
        if experiment is None:
            raise KeyError(f"unknown experiment: {experiment_id}")
        result = self.kernel.consensus.observe(
            subject=str(experiment.get("subject") or ""),
            predicate=str(experiment.get("predicate") or ""),
            object_value=experiment.get("object"),
            observer_id=str(observer_id),
            observer_kind=str(observer_kind or "unknown"),
            independence_group=str(independence_group or observer_id),
            stance=str(stance or "uncertain"),
            confidence=float(confidence),
            source_ref=source_ref,
            evidence_refs=list(evidence_refs or []),
            payload={
                "experiment_id": experiment_id,
                "observation": str(observation or "")[:12000],
                "measurement": sanitize_training_value(measurement or {}),
            },
        )
        row = {
            "schema_version": "wg-rnn-self-experiment-observation/v1",
            "result_type": "observation",
            "experiment_id": experiment_id,
            "claim_key": experiment.get("claim_key"),
            "observer_id": str(observer_id),
            "observer_kind": str(observer_kind or "unknown"),
            "independence_group": str(independence_group or observer_id),
            "stance": str(stance or "uncertain"),
            "confidence": max(0.0, min(float(confidence), 1.0)),
            "observation": str(observation or "")[:12000],
            "source_ref": source_ref,
            "evidence_refs": list(evidence_refs or []),
            "measurement": sanitize_training_value(measurement or {}),
            "consensus": result.get("consensus"),
            "created_at_ms": _now_ms(),
        }
        _jsonl_append(self.experiment_results_path, row)
        self.record_event(
            session_id=session_id,
            event_type="self_experiment_observation",
            actor=str(observer_id),
            content={
                "experiment_id": experiment_id,
                "claim_key": experiment.get("claim_key"),
                "observer_kind": observer_kind,
                "independence_group": independence_group,
                "stance": stance,
                "confidence": confidence,
                "source_ref": source_ref,
                "consensus_status": (result.get("consensus") or {}).get("status"),
            },
            tags=["self-experiment", "observation", str(observer_kind), "candidate-training"],
            training_eligible=True,
        )
        return {"experiment": experiment, "observation": row, "consensus": result.get("consensus")}

    def complete_experiment(
        self,
        *,
        experiment_id: str,
        session_id: str = "wg-rnn:self-experimentation",
    ) -> dict[str, Any]:
        experiment = self._experiment_proposal(experiment_id)
        if experiment is None:
            raise KeyError(f"unknown experiment: {experiment_id}")
        consensus = self.kernel.consensus.evaluate(
            claim_key=str(experiment.get("claim_key") or ""),
            min_independent_groups=int(experiment.get("minimum_independent_groups") or 3),
            min_support_ratio=float(experiment.get("min_support_ratio") or 0.75),
            min_support_weight=max(1.0, float(experiment.get("minimum_independent_groups") or 3) * 0.60),
            max_contradiction_ratio=float(experiment.get("max_contradiction_ratio") or 0.20),
        )
        groups = int(consensus.get("independent_groups") or 0)
        min_groups = int(experiment.get("minimum_independent_groups") or 3)
        if bool(consensus.get("promotion_recommended")):
            status = "completed_supported"
            outcome = "supporting_consensus_reached"
        elif str(consensus.get("status") or "") == "disputed":
            status = "completed_disputed"
            outcome = "material_independent_disagreement"
        elif groups >= min_groups:
            status = "completed_inconclusive"
            outcome = "quorum_reached_without_support_threshold"
        else:
            status = "needs_more_observers"
            outcome = "insufficient_independent_evidence"
        payload = {
            "schema_version": "wg-rnn-self-experiment-result/v1",
            "result_type": "evaluation",
            "experiment_id": experiment_id,
            "claim_key": experiment.get("claim_key"),
            "status": status,
            "outcome": outcome,
            "consensus": consensus,
            "minimum_independent_groups": min_groups,
            "missing_independent_groups": max(0, min_groups - groups),
            "promotion_performed": False,
            "promotion_policy": experiment.get("promotion_policy"),
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        witness = self.kernel.evidence.witness(
            "SelfExperimentResultWitness",
            payload,
            force="verify",
            status=status,
        )
        row = {**payload, "witness": witness}
        _jsonl_append(self.experiment_results_path, row)
        self.record_event(
            session_id=session_id,
            event_type="self_experiment_result",
            actor="wg-rnn:self",
            content={
                "experiment_id": experiment_id,
                "status": status,
                "outcome": outcome,
                "claim_key": experiment.get("claim_key"),
                "consensus_status": consensus.get("status"),
                "promotion_recommended": consensus.get("promotion_recommended"),
                "promotion_performed": False,
                "witness_id": witness.get("witness_id"),
            },
            tags=["self-experiment", "result", status, "candidate-training"],
            witness_id=witness.get("witness_id"),
            training_eligible=True,
        )
        return {"experiment": experiment, "result": row}

    def build_trajectory(
        self,
        *,
        session_id: str,
        start_sequence: int | None = None,
        end_sequence: int | None = None,
        outcome: dict[str, Any] | None = None,
        evaluator: str = "xavi-autonomy",
        learn: bool = True,
    ) -> dict[str, Any]:
        events = self.ledger._read_events(session_id)  # same append-only ledger, intentionally local
        selected = [
            event for event in events
            if (start_sequence is None or int(event.get("sequence", 0)) >= int(start_sequence))
            and (end_sequence is None or int(event.get("sequence", 0)) <= int(end_sequence))
        ]
        if not selected:
            raise ValueError("trajectory contains no events")

        actions = [e.get("event_digest") for e in selected if e.get("event_type") in ACTION_EVENT_TYPES]
        observations = [e.get("event_digest") for e in selected if e.get("event_type") in OBSERVATION_EVENT_TYPES]
        contexts = [e.get("event_digest") for e in selected if e.get("event_type") in CONTEXT_EVENT_TYPES]
        result = outcome or {}
        success = result.get("success")
        if success is None:
            success = not any(e.get("event_type") in {"mcp_call_error", "tool_error", "evaluation_failed"} for e in selected)
        score = max(0.0, min(1.0, float(result.get("score", 1.0 if success else 0.0))))

        body = {
            "schema_version": "experience-trajectory/v1",
            "session_id": session_id,
            "start_sequence": int(selected[0]["sequence"]),
            "end_sequence": int(selected[-1]["sequence"]),
            "start_ordinal": positive_ordinal_payload(int(selected[0]["sequence"])),
            "end_ordinal": positive_ordinal_payload(int(selected[-1]["sequence"])),
            "state": {"entry_event": selected[0].get("event_digest"), "context_refs": contexts},
            "actions": actions,
            "observations": observations,
            "outcome": {**result, "success": bool(success), "score": score, "score_duotronic": bounded_score_codeword(score)},
            "event_chain": [e.get("event_digest") for e in selected],
            "evaluator": evaluator,
            "contract_ref": CONTRACT_REF,
            "created_at_ms": _now_ms(),
        }
        body["trajectory_id"] = "trajectory_" + _digest(body).split(":", 1)[1][:24]
        witness = self.kernel.evidence.witness("ExperienceTrajectoryWitness", body, force="observe", status="recorded")
        row = {**body, "witness": witness}
        _jsonl_append(self.trajectories_path, row)
        self.record_event(
            session_id=session_id,
            event_type="experience_trajectory",
            actor="autonomy-stack",
            content={"trajectory_id": body["trajectory_id"], "trajectory_digest": _digest(body), "score": score, "witness_id": witness.get("witness_id")},
            tags=["trajectory", "candidate-training", "outcome-success" if success else "outcome-failure"],
            witness_id=witness.get("witness_id"),
        )

        learning = None
        if learn:
            summary = {
                "trajectory_id": body["trajectory_id"],
                "event_count": len(selected),
                "action_count": len(actions),
                "observation_count": len(observations),
                "success": bool(success),
                "score": score,
            }
            learning = self.kernel.wgrnn_step_witnessed(
                prompt="Learn evaluated experience trajectory: " + _canonical(summary),
                response_text="Outcome evidence: " + _canonical(body["outcome"]),
                requested_action="observe",
                evidence_quality=max(0.05, score),
                thread_id=session_id,
                agent_id="autonomy-stack",
                tags=["experience", "trajectory", "evaluated", body["trajectory_id"]],
            )
        return {"trajectory": row, "learning": learning}

    def record_external_research(
        self,
        *,
        query: str,
        objective: str,
        channel_results: list[dict[str, Any]],
        initiated_by: str = "wgrnn-autonomy",
        reason: str = "autonomous-research",
        session_id: str = "autonomous-research",
        training_eligible: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query_text=str(query or "").strip()
        if not query_text:
            raise ValueError("research query is required")
        normalized=[]
        for item in channel_results:
            if not isinstance(item,dict):
                continue
            witness=item.get("witness") if isinstance(item.get("witness"),dict) else {}
            normalized.append({
                "channel":str(item.get("channel") or "web"),
                "result_count":int(item.get("result_count") or len(item.get("results") or [])),
                "results_digest":item.get("results_digest"),
                "search_witness_id":witness.get("witness_id"),
                "source":item.get("source"),
                "errors":[str(x)[:240] for x in (item.get("errors") or [])[:8]],
            })
        body={
            "schema_version":"autonomous-external-research/v1",
            "query":query_text,
            "objective":str(objective or query_text)[:4000],
            "initiated_by":str(initiated_by or "wgrnn-autonomy")[:160],
            "reason":str(reason or "autonomous-research")[:240],
            "channels":normalized,
            "channel_count":len(normalized),
            "total_result_count":sum(x["result_count"] for x in normalized),
            "metadata":dict(metadata or {}),
            "created_at_ms":_now_ms(),
            "contract_ref":CONTRACT_REF,
            "non_collapse":{
                "search_results_are_observations_not_truth":True,
                "training_observation_is_not_authority":True,
                "similarity_or_recurrence_is_not_automatic_promotion":True,
            },
        }
        body["research_id"]="research_"+_digest(body).split(":",1)[1][:24]
        witness=self.kernel.evidence.witness("AutonomousResearchWitness",body,force="observe",status="recorded")
        try:
            self.kernel.store.insert_witness(witness)
        except Exception:
            pass
        event=self.record_event(
            session_id=session_id,
            event_type="autonomous_external_research",
            actor=str(initiated_by or "wgrnn-autonomy"),
            content={"research":body,"witness_id":witness.get("witness_id")},
            tags=["research","external-evidence","candidate-training",*(f"channel:{x['channel']}" for x in normalized)],
            witness_id=witness.get("witness_id"),
            training_eligible=bool(training_eligible),
        )
        return {"research":body,"witness":witness,"event":event,"channel_results":channel_results}

    def observe_source_training_chunk(
        self,
        *,
        artifact_id: str,
        source_path: str,
        source_digest: str,
        chunk_index: int,
        content: str,
        adapter: str | None = None,
        mime_type: str | None = None,
        derivation: str = "derived-content",
        metadata: dict[str, Any] | None = None,
        session_id: str = "datalake-training",
    ) -> dict[str, Any]:
        chunk = str(content or "")[:12000]
        if not chunk.strip():
            raise ValueError("training chunk content is empty")
        idx = max(0, int(chunk_index))
        chunk_digest = _digest(chunk)
        witness_body = {
            "schema_version": "source-training-chunk/v1",
            "artifact_id": str(artifact_id),
            "source_path": str(source_path),
            "source_digest": str(source_digest),
            "chunk_index": idx,
            "content_digest": chunk_digest,
            "chars": len(chunk),
            "adapter": str(adapter or "unknown"),
            "mime_type": str(mime_type or "application/octet-stream"),
            "derivation": str(derivation or "derived-content"),
            "metadata": dict(metadata or {}),
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        witness = self.kernel.evidence.witness(
            "SourceTrainingChunkWitness", witness_body, force="observe", status="recorded"
        )
        event = self.record_event(
            session_id=session_id,
            event_type="source_training_chunk",
            actor="datalake-training-worker",
            content={
                "artifact_id": str(artifact_id),
                "source_path": str(source_path),
                "source_digest": str(source_digest),
                "chunk_index": idx,
                "content": chunk,
                "content_digest": chunk_digest,
                "adapter": str(adapter or "unknown"),
                "mime_type": str(mime_type or "application/octet-stream"),
                "derivation": str(derivation or "derived-content"),
                "metadata": dict(metadata or {}),
                "witness_id": witness.get("witness_id"),
            },
            tags=[
                "datalake", "source-training-chunk", "candidate-training",
                f"adapter:{str(adapter or 'unknown')}", f"derivation:{str(derivation or 'derived-content')}",
            ],
            witness_id=witness.get("witness_id"),
            training_eligible=True,
        )
        return {
            "chunk": witness_body,
            "witness": witness,
            "event": event,
            "recurrent_learning": event.get("recurrent_learning"),
        }

    def ingest_artifact(
        self,
        *,
        path: str,
        source_kind: str,
        derived_text: str | None = None,
        derived_records: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        training_eligible: bool = True,
        session_id: str = "media-ingest",
    ) -> dict[str, Any]:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(str(source))
        size = source.stat().st_size
        source_digest = _file_shake256(source)
        mime_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        text = derived_text
        if text is None and source.suffix.lower() in _TEXT_EXTENSIONS and size <= 4 * 1024 * 1024:
            text = source.read_text(encoding="utf-8", errors="replace")

        artifact = {
            "schema_version": "source-media-artifact/v1",
            "artifact_id": "artifact_" + source_digest.split(":", 1)[1][:24],
            "path": str(source),
            "name": source.name,
            "source_kind": str(source_kind),
            "mime_type": mime_type,
            "bytes": size,
            "source_digest": source_digest,
            "metadata": metadata or {},
            "training_eligible": bool(training_eligible),
            "derived_text_digest": _digest(text) if text is not None else None,
            "derived_record_count": len(derived_records or []),
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        witness = self.kernel.evidence.witness("SourceMediaArtifactWitness", artifact, force="observe", status="recorded")
        row = {**artifact, "witness": witness}
        _jsonl_append(self.artifacts_path, row)

        source_index = None
        if text is not None or derived_records:
            generation_id = "media_" + source_digest.split(":", 1)[1][:24]
            repository_id = "media:" + re.sub(r"[^A-Za-z0-9_.-]+", "-", str(source_kind).strip().lower())[:80]
            self.kernel.store.begin_source_generation(
                generation_id=generation_id,
                repository_id=repository_id,
                root_path=str(source.parent),
                commit_id=source_digest,
                metadata={"artifact_id": artifact["artifact_id"], "mime_type": mime_type, "source_kind": source_kind},
            )
            documents: list[dict[str, Any]] = []
            chunks: list[tuple[str, dict[str, Any]]] = []
            if text is not None:
                chunk_size = 12_000
                for offset in range(0, len(text), chunk_size):
                    chunks.append((text[offset: offset + chunk_size], {"derivation": "text-or-transcript", "offset": offset}))
            for record in derived_records or []:
                content = str(record.get("content") or record.get("text") or "")
                if content:
                    chunks.append((content, {"derivation": record.get("kind", "derived-record"), **(record.get("metadata") or {})}))
            for index, (content, chunk_meta) in enumerate(chunks):
                documents.append({
                    "generation_id": generation_id,
                    "repository_id": repository_id,
                    "path": source.name,
                    "chunk_index": index,
                    "language": (metadata or {}).get("language"),
                    "content_digest": _digest(content),
                    "source_digest": source_digest,
                    "content": content,
                    "metadata": {"artifact_id": artifact["artifact_id"], "mime_type": mime_type, **chunk_meta},
                    "training_eligible": bool(training_eligible),
                })
            if documents:
                upsert = self.kernel.store.upsert_source_documents(documents)
                final = self.kernel.store.finalize_source_generation(generation_id=generation_id, status="completed", keep_generations=4)
                source_index = {"upsert": upsert, "finalize": final}

        event = self.record_event(
            session_id=session_id,
            event_type="source_media_ingest",
            actor="autonomy-stack",
            content={"artifact": artifact, "source_index": source_index, "witness_id": witness.get("witness_id")},
            tags=["source", "media", str(source_kind), "candidate-training"],
            witness_id=witness.get("witness_id"),
            training_eligible=training_eligible,
        )
        return {"artifact": row, "source_index": source_index, "event": event}

    def record_datalake_observation(
        self,
        *,
        artifact_id: str,
        source_path: str,
        source_digest: str,
        observation_kind: str,
        statement: str,
        confidence: float = 0.7,
        observer_id: str = "wgrnn-datalake",
        observer_kind: str = "derived_observer",
        independence_group: str | None = None,
        epistemic_class: str = "machine_derived",
        metadata: dict[str, Any] | None = None,
        claim: dict[str, Any] | None = None,
        session_id: str = "datalake-ingest",
    ) -> dict[str, Any]:
        confidence = max(0.0, min(1.0, float(confidence)))
        body = {
            "schema_version": "wgrnn-datalake-observation/v1",
            "artifact_id": str(artifact_id),
            "source_path": str(source_path),
            "source_digest": str(source_digest),
            "observation_kind": str(observation_kind),
            "statement": str(statement),
            "confidence": confidence,
            "observer_id": str(observer_id),
            "observer_kind": str(observer_kind),
            "independence_group": str(independence_group or observer_id),
            "epistemic_class": str(epistemic_class),
            "metadata": dict(metadata or {}),
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        witness = self.kernel.evidence.witness("DataLakeObservationWitness", body, force="observe", status="recorded")
        event = self.record_event(
            session_id=session_id,
            event_type="datalake_observation",
            actor="wgrnn-datalake",
            content={"observation": body, "witness_id": witness.get("witness_id")},
            tags=["datalake", "observation", str(observation_kind), str(epistemic_class), "candidate-training"],
            witness_id=witness.get("witness_id"),
            training_eligible=True,
        )
        consensus = None
        if isinstance(claim, dict) and claim.get("subject") and claim.get("predicate"):
            consensus = self.kernel.consensus.observe(
                subject=str(claim["subject"]),
                predicate=str(claim["predicate"]),
                object_value=claim.get("object"),
                observer_id=str(observer_id),
                observer_kind=str(observer_kind),
                independence_group=str(independence_group or observer_id),
                stance=str(claim.get("stance") or "support"),
                confidence=confidence,
                source_ref=str(source_digest),
                evidence_refs=[str(witness.get("witness_id") or "")],
                payload={"artifact_id": artifact_id, "observation_kind": observation_kind, **dict(metadata or {})},
            )
        return {"observation": body, "witness": witness, "event": event, "consensus": consensus}

    def record_datalake_pattern(
        self,
        *,
        pattern_kind: str,
        statement: str,
        members: list[dict[str, Any]],
        confidence: float = 0.7,
        observer_id: str = "wgrnn-pattern-engine",
        metadata: dict[str, Any] | None = None,
        session_id: str = "datalake-patterns",
    ) -> dict[str, Any]:
        confidence = max(0.0, min(1.0, float(confidence)))
        body = {
            "schema_version": "wgrnn-datalake-pattern/v1",
            "pattern_id": "pattern_" + _digest({"kind": pattern_kind, "statement": statement, "members": members}).split(":", 1)[1][:28],
            "pattern_kind": str(pattern_kind),
            "statement": str(statement),
            "members": list(members),
            "confidence": confidence,
            "observer_id": str(observer_id),
            "metadata": dict(metadata or {}),
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        witness = self.kernel.evidence.witness("DataLakePatternWitness", body, force="observe", status="recorded")
        event = self.record_event(
            session_id=session_id,
            event_type="datalake_pattern",
            actor="wgrnn-pattern-engine",
            content={"pattern": body, "witness_id": witness.get("witness_id")},
            tags=["datalake", "pattern", str(pattern_kind), "candidate-training"],
            witness_id=witness.get("witness_id"),
            training_eligible=True,
        )
        return {"pattern": body, "witness": witness, "event": event}

    def record_evaluation(
        self,
        *,
        candidate_id: str,
        checks: Iterable[EvaluationCheck | dict[str, Any]],
        evaluator: str,
        environment: dict[str, Any] | None = None,
        session_id: str = "autonomous-evaluation",
    ) -> dict[str, Any]:
        normalized: list[dict[str, Any]] = []
        for item in checks:
            check = item if isinstance(item, EvaluationCheck) else EvaluationCheck(
                name=str(item.get("name", "check")),
                passed=bool(item.get("passed", False)),
                score=float(item.get("score", 1.0 if item.get("passed") else 0.0)),
                required=bool(item.get("required", True)),
                evidence_ref=item.get("evidence_ref"),
                details=item.get("details") if isinstance(item.get("details"), dict) else {},
            )
            normalized.append(check.to_dict())
        if not normalized:
            raise ValueError("at least one evaluation check is required")
        required = [c for c in normalized if c["required"]]
        passed = all(c["passed"] for c in required)
        score = sum(float(c["score"]) for c in normalized) / len(normalized)
        payload = {
            "schema_version": "autonomous-evaluation/v1",
            "candidate_id": candidate_id,
            "evaluator": evaluator,
            "environment": environment or {},
            "checks": normalized,
            "passed": passed,
            "score": score,
            "score_duotronic": bounded_score_codeword(score),
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
            "non_collapse": {"passing_tests_are_not_proof": True, "evaluation_is_not_authority": True},
        }
        payload["evaluation_id"] = "eval_" + _digest(payload).split(":", 1)[1][:24]
        witness = self.kernel.evidence.witness("AutonomousEvaluationWitness", payload, force="verify", status="recorded")
        row = {**payload, "witness": witness}
        _jsonl_append(self.evaluations_path, row)
        self.record_event(
            session_id=session_id,
            event_type="evaluation_result",
            actor=evaluator,
            content={"evaluation_id": payload["evaluation_id"], "candidate_id": candidate_id, "passed": passed, "score": score, "witness_id": witness.get("witness_id")},
            tags=["evaluation", "candidate", "pass" if passed else "fail"],
            witness_id=witness.get("witness_id"),
        )
        return row

    def register_candidate(
        self,
        *,
        objective: str,
        repo_ref: str,
        parent_ref: str,
        diff_digest: str,
        changed_paths: list[str],
        rollback_ref: str | None,
        session_id: str = "self-development",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "schema_version": "self-development-candidate/v1",
            "objective": objective,
            "repo_ref": repo_ref,
            "parent_ref": parent_ref,
            "diff_digest": diff_digest,
            "changed_paths": sorted(set(changed_paths)),
            "rollback_ref": rollback_ref,
            "metadata": metadata or {},
            "created_at_ms": _now_ms(),
            "contract_ref": CONTRACT_REF,
        }
        payload["candidate_id"] = "candidate_" + _digest(payload).split(":", 1)[1][:24]
        witness = self.kernel.evidence.witness("SelfDevelopmentCandidateWitness", payload, force="propose", status="candidate")
        row = {**payload, "witness": witness, "status": "candidate"}
        _jsonl_append(self.candidates_path, row)
        self.record_event(
            session_id=session_id,
            event_type="code_candidate",
            actor="self-development-controller",
            content={"candidate_id": payload["candidate_id"], "diff_digest": diff_digest, "changed_paths": payload["changed_paths"], "witness_id": witness.get("witness_id")},
            tags=["self-development", "code", "candidate"],
            witness_id=witness.get("witness_id"),
        )
        return row

    def promotion_gate(
        self,
        *,
        candidate: dict[str, Any],
        evaluation: dict[str, Any],
        rollback_ready: bool,
        witness_chain_verified: bool,
        independent_validation: bool = False,
        authority_witness: str | None = None,
        session_id: str = "self-development",
    ) -> dict[str, Any]:
        changed_paths = [str(p) for p in candidate.get("changed_paths", [])]
        protected_tokens = ("witness_contract/", "evidence.py", "policy.py", "formal_observers", "validation", "verifier")
        protected_change = any(any(token in path for token in protected_tokens) for path in changed_paths)
        evaluation_passed = bool(evaluation.get("passed"))
        operational_allowed = bool(
            evaluation_passed
            and rollback_ready
            and witness_chain_verified
            and (not protected_change or independent_validation)
        )
        decision = {
            "schema_version": "recursive-improvement-gate/v1",
            "candidate_id": candidate.get("candidate_id"),
            "evaluation_id": evaluation.get("evaluation_id"),
            "operational_promotion_allowed": operational_allowed,
            "authority_promotion_allowed": False,
            "authority_witness_supplied": bool(authority_witness),
            "rollback_ready": bool(rollback_ready),
            "witness_chain_verified": bool(witness_chain_verified),
            "protected_surface_change": protected_change,
            "independent_validation": bool(independent_validation),
            "reasons": [],
            "contract_ref": CONTRACT_REF,
            "created_at_ms": _now_ms(),
        }
        if not evaluation_passed:
            decision["reasons"].append("evaluation_failed")
        if not rollback_ready:
            decision["reasons"].append("rollback_not_ready")
        if not witness_chain_verified:
            decision["reasons"].append("witness_chain_not_verified")
        if protected_change and not independent_validation:
            decision["reasons"].append("protected_surface_requires_independent_validation")
        decision["reasons"].append("theorem_release_authority_remains_separate")
        witness = self.kernel.evidence.witness(
            "RecursiveImprovementGateWitness",
            decision,
            force="authorize" if operational_allowed else "refuse",
            status="recorded",
        )
        row = {**decision, "witness": witness}
        _jsonl_append(self.promotion_path, row)
        self.record_event(
            session_id=session_id,
            event_type="recursive_improvement_gate",
            actor="autonomy-stack",
            content={"decision": decision, "witness_id": witness.get("witness_id")},
            tags=["recursive-improvement", "operational-promotion", "allowed" if operational_allowed else "refused"],
            witness_id=witness.get("witness_id"),
        )
        return row

    def record_resource_snapshot(
        self,
        *,
        node_id: str,
        resources: dict[str, Any],
        services: dict[str, Any] | None = None,
        transport: dict[str, Any] | None = None,
        session_id: str = "resource-pool",
    ) -> dict[str, Any]:
        row = {
            "schema_version": "distributed-resource-snapshot/v1",
            "node_id": node_id,
            "resources": resources,
            "services": services or {},
            "transport": transport or {},
            "observed_at_ms": _now_ms(),
        }
        row["snapshot_digest"] = _digest(row)
        _jsonl_append(self.resources_path, row)
        self.record_event(
            session_id=session_id,
            event_type="resource_snapshot",
            actor="resource-scheduler",
            content=row,
            tags=["distributed", "resource", node_id],
        )
        return row

    def latest_resource_snapshots(self) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for row in _jsonl_read(self.resources_path):
            latest[str(row.get("node_id"))] = row
        return latest

    def schedule_task(self, *, requirements: dict[str, Any]) -> dict[str, Any]:
        snapshots = self.latest_resource_snapshots()
        candidates: list[dict[str, Any]] = []
        need_gpu = bool(requirements.get("gpu", False))
        min_gpu_mb = int(requirements.get("min_gpu_memory_mb", 0) or 0)
        min_cpu = int(requirements.get("min_cpu_threads", 1) or 1)
        min_ram_mb = int(requirements.get("min_ram_mb", 0) or 0)
        preferred_labels = set(str(x) for x in requirements.get("labels", []) if str(x))
        for node_id, snapshot in snapshots.items():
            r = snapshot.get("resources") if isinstance(snapshot.get("resources"), dict) else {}
            if r.get("reachable") is False or r.get("available") is False:
                continue
            cpu = int(r.get("available_cpu_threads", r.get("cpu_threads", 0)) or 0)
            ram = int(r.get("available_ram_mb", r.get("ram_mb", 0)) or 0)
            gpu_mb = int(r.get("available_gpu_memory_mb", r.get("gpu_memory_mb", 0)) or 0)
            gpu_present = bool(r.get("gpu", False) or gpu_mb > 0)
            if cpu < min_cpu or ram < min_ram_mb or (need_gpu and (not gpu_present or gpu_mb < min_gpu_mb)):
                continue
            labels = set(str(x) for x in r.get("labels", []) if str(x))
            label_bonus = len(labels & preferred_labels) * 0.05
            score = min(1.0, 0.35 * min(cpu / max(min_cpu, 1), 4) / 4 + 0.25 * min(ram / max(min_ram_mb or 1, 1), 4) / 4 + 0.30 * (1.0 if gpu_present else 0.0) + label_bonus + 0.10)
            candidates.append({
                "node_id": node_id,
                "score": score,
                "score_duotronic": bounded_score_codeword(score),
                "resources": r,
                "snapshot_digest": snapshot.get("snapshot_digest"),
            })
        candidates.sort(key=lambda row: (-float(row["score"]), row["node_id"]))
        for index, row in enumerate(candidates):
            row["rank"] = positive_index_payload(index)
        return {
            "schema_version": "distributed-resource-schedule/v1",
            "requirements": requirements,
            "selected": candidates[0] if candidates else None,
            "candidates": candidates,
            "created_at_ms": _now_ms(),
        }

    def build_training_corpus(
        self,
        *,
        session_ids: list[str] | None = None,
        include_failures: bool = True,
        session_id: str = "training-pipeline",
    ) -> dict[str, Any]:
        available = sorted((self.ledger.index().get("sessions") or {}).keys())
        selected_sessions = session_ids or available
        records: list[dict[str, Any]] = []
        for sid in selected_sessions:
            for event in self.ledger._read_events(sid):
                if event.get("training_eligible") is False:
                    continue
                if not include_failures and event.get("event_type") in {"mcp_call_error", "tool_error", "evaluation_failed"}:
                    continue
                records.append({
                    "schema_version": "wgrnn-training-example/v1",
                    "session_id": sid,
                    "sequence": event.get("sequence"),
                    "sequence_bijective": event.get("sequence_bijective") or positive_ordinal_payload(int(event.get("sequence", 1))),
                    "event_type": event.get("event_type"),
                    "actor": event.get("actor"),
                    "content": sanitize_training_value(event.get("content") or {}),
                    "event_digest": event.get("event_digest"),
                    "previous_event_digest": event.get("previous_event_digest"),
                    "witness_id": event.get("witness_id"),
                    "tags": event.get("tags", []),
                    "contract_ref": CONTRACT_REF,
                })
        created = _now_ms()
        corpus_id = "training_" + _digest({"created": created, "records": [r["event_digest"] for r in records]}).split(":", 1)[1][:24]
        path = self.training_dir / f"{corpus_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(_canonical(record) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        manifest = {
            "schema_version": "wgrnn-training-corpus-manifest/v1",
            "corpus_id": corpus_id,
            "path": str(path),
            "record_count": len(records),
            "session_ids": selected_sessions,
            "include_failures": bool(include_failures),
            "shake256_512": _file_shake256(path),
            "source_index_status": self.kernel.store.source_index_status(),
            "provenance": self.provenance(),
            "created_at_ms": created,
        }
        witness = self.kernel.evidence.witness("TrainingCorpusManifestWitness", manifest, force="observe", status="recorded")
        self.record_event(
            session_id=session_id,
            event_type="training_corpus_built",
            actor="training-pipeline",
            content={"manifest": manifest, "witness_id": witness.get("witness_id")},
            tags=["training", "reproducible", "evaluated-experience"],
            witness_id=witness.get("witness_id"),
            training_eligible=False,
        )
        return {"manifest": manifest, "witness": witness}

    def continuation_context(self, *, session_id: str, limit: int = 80) -> dict[str, Any]:
        tail = self.ledger.tail(session_id=session_id, limit=max(1, min(int(limit), 200)))
        trajectories = [row for row in _jsonl_read(self.trajectories_path) if row.get("session_id") == session_id][-12:]
        return {
            "schema_version": "cross-session-continuation-context/v1",
            "session_id": session_id,
            "ledger_summary": self.ledger.summary(session_id=session_id),
            "events": tail.get("events", []),
            "trajectories": trajectories,
            "secret_capabilities": self.secrets.list(),
            "contract_ref": CONTRACT_REF,
            "provenance": self.provenance(),
        }
