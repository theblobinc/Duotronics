from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .evidence import sha256_ref


_TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".lean", ".tla", ".py", ".sql"}


class WGRNNKernelChat:
    """OS-like WG-RNN chat orchestration layer.

    This is intentionally a governed control plane, not an unrestricted executor.
    It treats the mounted corpus as a read-only operating specification, turns a
    chat request into a task frame, retrieves memory/evidence, asks a selected
    worker model to synthesize a response, and writes the result to WG-RNN as
    candidate memory with witness-style metadata.
    """

    def __init__(self, runtime_kernel: Any, *, observer_id: str = "wg-rnn-kernel-chat") -> None:
        self.kernel = runtime_kernel
        self.observer_id = observer_id
        self._boot_cache: dict[str, Any] | None = None
        self._boot_cache_digest: str | None = None

    def boot(self) -> dict[str, Any]:
        inspection = self.kernel.corpus_manager.inspect()
        corpus_ref = inspection.get("corpus_ref") or {}
        corpus_digest = str(corpus_ref.get("digest") or "")
        if self._boot_cache is not None and self._boot_cache_digest == corpus_digest:
            return self._boot_cache

        corpus_dir = Path(str(inspection.get("corpus_dir") or self.kernel.settings.corpus_dir))
        entrypoints = [
            "START_HERE.md",
            "README.md",
            "EVIDENCE_LANGUAGE_OPERATING_SYSTEM_PRIMER_v1_0.md",
            "CORPUS_INDEX_v1_6_draft_5_2_2.md",
            "kernel/logical_observer_kernel_contract_v1_0.md",
            "kernel/corpus_boot_and_canonical_resolver_v1_0.md",
            "executable/kernel/logical_observer_kernel_syscalls.yaml",
        ]
        loaded: list[dict[str, Any]] = []
        for rel in entrypoints:
            path = corpus_dir / rel
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            loaded.append(
                {
                    "path": rel,
                    "bytes": path.stat().st_size,
                    "digest": self._file_digest(path),
                    "excerpt": " ".join(text.split())[:2200],
                }
            )

        capability_index = self._build_corpus_capability_index(corpus_dir, inspection.get("documents") or [])
        boot_state = {
            "status": "safe_mode" if not inspection.get("manifest_path") else "booted",
            "reason": "no explicit manifest found; derived corpus ref is used" if not inspection.get("manifest_path") else "manifest present",
            "observer_id": self.observer_id,
            "corpus_ref": corpus_ref,
            "manifest_path": inspection.get("manifest_path"),
            "entrypoints": loaded,
            "capability_index": capability_index,
            "kernel_rules": [
                "Preserve non-collapse: model output is not proof, policy approval is not truth, absence is not zero.",
                "Every operation is represented as a task frame with witnessed steps.",
                "Runtime effects must be candidate memory unless a proof/policy gate promotes them.",
                "Refuse or escalate when required witnesses, authority, assumptions, or tools are missing.",
            ],
        }
        boot_state["boot_digest"] = sha256_ref(boot_state)
        self._boot_cache = boot_state
        self._boot_cache_digest = corpus_digest
        return boot_state

    def prepare_turn(self, *, prompt: str, messages: list[Any], corpus_search: dict[str, Any], needs_vision: bool = False) -> dict[str, Any]:
        boot = self.boot()
        task_frame = self._make_task_frame(prompt=prompt, corpus_search=corpus_search, needs_vision=needs_vision, boot=boot)
        memory = self._retrieve_memory(prompt)
        system_messages = self._system_messages(task_frame=task_frame, boot=boot, corpus_search=corpus_search, memory=memory)
        return {
            "boot": boot,
            "task_frame": task_frame,
            "memory": memory,
            "system_messages": system_messages,
            "response_prompt": self._response_prompt(prompt=prompt, task_frame=task_frame, corpus_search=corpus_search, memory=memory),
            "witness_chain": self._initial_witness_chain(task_frame, corpus_search, memory),
        }

    def finalize_turn(self, *, prepared: dict[str, Any], response_text: str, needs_vision: bool = False) -> dict[str, Any]:
        task_frame = prepared.get("task_frame") or {}
        corpus_search = task_frame.get("corpus_search") or {}
        evidence_quality = 0.86 if corpus_search.get("results") else 0.64
        tags = [
            "librechat",
            "wg-rnn-chat",
            "kernel_turn",
            "candidate_training",
            str(task_frame.get("operation_kind") or "ask"),
        ]
        if needs_vision:
            tags.append("multimodal")
        wgrnn_result = self.kernel.wgrnn.step(
            prompt=json.dumps(task_frame, sort_keys=True, ensure_ascii=False),
            response_text=response_text,
            requested_action="memory_write",
            evidence_quality=evidence_quality,
            tags=tags,
        )
        final_witness = {
            "witness_type": "KernelTurnResultWitness",
            "task_id": task_frame.get("task_id"),
            "response_digest": sha256_ref({"response_text": response_text}),
            "memory_update": wgrnn_result.get("memory_update"),
            "status": "candidate_memory_written",
            "created_at_ms": int(time.time() * 1000),
        }
        return {
            "wgrnn": wgrnn_result,
            "witness_chain": (prepared.get("witness_chain") or []) + [final_witness],
            "kernel_turn": {
                "mode": "chat",
                "task_id": task_frame.get("task_id"),
                "operation_kind": task_frame.get("operation_kind"),
                "training_write": "candidate_memory",
                "promotion": "not_promoted",
                "boot_status": (prepared.get("boot") or {}).get("status"),
                "memory_refs": len((prepared.get("memory") or {}).get("results") or []),
                "evidence_result_count": len(corpus_search.get("results") or []),
                "witness_count": len((prepared.get("witness_chain") or [])) + 1,
            },
        }

    def _make_task_frame(self, *, prompt: str, corpus_search: dict[str, Any], needs_vision: bool, boot: dict[str, Any]) -> dict[str, Any]:
        operation_kind = self._classify_operation(prompt)
        required_tools = self._required_tools(operation_kind, prompt, boot)
        evidence_refs = [
            {"path": row.get("path"), "digest": row.get("digest"), "score": row.get("score")}
            for row in (corpus_search.get("results") or [])[:8]
        ]
        task_frame = {
            "task_id": "wgrnn_task_" + uuid.uuid4().hex[:16],
            "mode": "wg-rnn:chat",
            "operation_kind": operation_kind,
            "requested_force": self._requested_force(operation_kind),
            "needs_vision": needs_vision,
            "user_request_digest": sha256_ref({"prompt": prompt}),
            "corpus_ref": boot.get("corpus_ref"),
            "corpus_search": {"status": corpus_search.get("status"), "results": evidence_refs},
            "required_schemas": self._required_schemas(operation_kind),
            "required_tools": required_tools,
            "authority": {
                "memory_write": "candidate_only",
                "promotion": "manual_or_proof_gate_required",
                "external_effects": "disabled_by_default",
            },
            "non_collapse": [
                "model_output_is_candidate_evidence_not_truth",
                "corpus_rule_is_operating_spec_not_execution_result",
                "chat_memory_is_candidate_until_promoted",
            ],
        }
        task_frame["task_digest"] = sha256_ref(task_frame)
        return task_frame

    def _classify_operation(self, prompt: str) -> str:
        text = (prompt or "").lower()
        if any(word in text for word in ["prove", "theorem", "lean", "proof"]):
            return "verify_proof"
        if any(word in text for word in ["tla", "model check", "state machine", "invariant"]):
            return "verify_state"
        if any(word in text for word in ["run", "execute", "operate", "do this", "build", "fix", "patch"]):
            return "operate"
        if any(word in text for word in ["remember", "train", "learn", "write to memory"]):
            return "train"
        if any(word in text for word in ["is this true", "verify", "validate", "check"]):
            return "verify_claim"
        return "ask"

    def _requested_force(self, operation_kind: str) -> str:
        return {
            "ask": "respond",
            "train": "memory_write_candidate",
            "operate": "plan_before_effect",
            "verify_claim": "verify_or_escalate",
            "verify_proof": "formal_check_required",
            "verify_state": "formal_check_required",
        }.get(operation_kind, "respond")

    def _required_schemas(self, operation_kind: str) -> list[str]:
        base = ["EvidenceClaim", "PragmaticContext", "TaskFrame", "TaskStepWitness", "TaskResultWitness"]
        if operation_kind.startswith("verify"):
            base += ["VerificationGrammar", "VerificationResult", "InferenceWitness"]
        if operation_kind == "operate":
            base += ["KernelTransaction", "PolicyDecisionEvidenceExtension", "KernelErrorWitness"]
        if operation_kind == "train":
            base += ["LogicalMemoryCell", "NonCollapseTransition"]
        return base

    def _required_tools(self, operation_kind: str, prompt: str, boot: dict[str, Any]) -> list[str]:
        tools = ["corpus.search", "memory.retrieve", "model.ask", "witness.emit", "memory.write_candidate"]
        if operation_kind == "verify_proof":
            tools.append("formal.lean_check")
        if operation_kind == "verify_state":
            tools.append("formal.tla_check")
        if operation_kind == "operate":
            tools += ["kernel.plan", "policy.check", "transaction.begin", "transaction.commit"]
        available = {item.get("id") for item in (boot.get("capability_index") or [])}
        return [{"id": tool, "available": tool in available or tool.split(".", 1)[0] in {"corpus", "memory", "model", "witness", "policy", "transaction", "kernel"}} for tool in tools]

    def _retrieve_memory(self, prompt: str) -> dict[str, Any]:
        try:
            return self.kernel.wgrnn.retrieve(query=prompt, top_k=6, include_empty=False)
        except Exception as exc:
            return {"status": "error", "error": exc.__class__.__name__, "results": []}

    def _system_messages(self, *, task_frame: dict[str, Any], boot: dict[str, Any], corpus_search: dict[str, Any], memory: dict[str, Any]) -> list[dict[str, Any]]:
        kernel_message = (
            "You are WG-RNN Chat, a conversational shell for a governed evidence-language runtime. "
            "Answer naturally and directly. Use WG-RNN memory and mounted corpus evidence when useful, "
            "but do not expose internal policy, witness, or task-frame machinery unless asked. "
            "Treat model output as candidate evidence, not proof. State uncertainty plainly. "
            "Do not claim execution, proof, or promotion occurred unless a tool/witness result is present."
        )
        corpus_lines = []
        for row in (corpus_search.get("results") or [])[:5]:
            corpus_lines.append(f"path={row.get('path')} digest={row.get('digest')} score={row.get('score')}\n{row.get('snippet')}")
        memory_lines = []
        for row in (memory.get("results") or [])[:5]:
            memory_lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True)[:900])
        return [
            {"role": "system", "content": kernel_message},
            {"role": "system", "content": "WG-RNN kernel task frame summary: " + json.dumps({k: task_frame.get(k) for k in ["task_id", "operation_kind", "requested_force", "required_schemas", "required_tools", "authority"]}, ensure_ascii=False)},
            {"role": "system", "content": "Mounted corpus evidence:\n" + ("\n\n".join(corpus_lines) if corpus_lines else "No matching mounted-corpus snippets retrieved.")},
            {"role": "system", "content": "Relevant WG-RNN memory:\n" + ("\n\n".join(memory_lines) if memory_lines else "No matching WG-RNN memory retrieved.")},
        ]

    def _response_prompt(self, *, prompt: str, task_frame: dict[str, Any], corpus_search: dict[str, Any], memory: dict[str, Any]) -> str:
        return (
            "Respond to the user's latest request as WG-RNN Chat. Use the provided system context as operating evidence. "
            "Keep the user-facing response conversational. If an operation needs a tool or proof runner that has not actually run, "
            "say what would be required rather than pretending it ran.\n\n"
            f"User request:\n{prompt}"
        )

    def _initial_witness_chain(self, task_frame: dict[str, Any], corpus_search: dict[str, Any], memory: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "witness_type": "KernelTaskFrameWitness",
                "task_id": task_frame.get("task_id"),
                "task_digest": task_frame.get("task_digest"),
                "operation_kind": task_frame.get("operation_kind"),
                "created_at_ms": int(time.time() * 1000),
            },
            {
                "witness_type": "CorpusRuleResolutionWitness",
                "task_id": task_frame.get("task_id"),
                "corpus_ref": task_frame.get("corpus_ref"),
                "evidence_count": len(corpus_search.get("results") or []),
                "status": "resolved" if corpus_search.get("results") else "no_relevant_snippets",
            },
            {
                "witness_type": "MemoryRetrievalWitness",
                "task_id": task_frame.get("task_id"),
                "memory_count": len(memory.get("results") or []),
                "status": memory.get("status", "ok"),
            },
        ]

    def _build_corpus_capability_index(self, corpus_dir: Path, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        capabilities: list[dict[str, Any]] = [
            {"id": "corpus.search", "kind": "syscall", "safe": True},
            {"id": "corpus.read", "kind": "syscall", "safe": True},
            {"id": "memory.retrieve", "kind": "syscall", "safe": True},
            {"id": "memory.write_candidate", "kind": "syscall", "safe": True},
            {"id": "model.ask", "kind": "syscall", "safe": True},
            {"id": "witness.emit", "kind": "syscall", "safe": True},
        ]
        for item in documents:
            rel = str(item.get("path") or "")
            suffix = Path(rel).suffix.lower()
            if suffix not in _TEXT_EXTENSIONS:
                continue
            kind = None
            cid = None
            safe = True
            if rel.startswith("schemas/") and rel.endswith(".json"):
                kind, cid = "schema", "schema." + Path(rel).stem
            elif rel.startswith("executable/kernel/") and rel.endswith((".yaml", ".yml")):
                kind, cid = "syscall_table", "kernel.syscalls"
            elif rel.startswith("executable/validators/") and rel.endswith(".py"):
                kind, cid = "validator", "validator." + Path(rel).stem
            elif rel.startswith("executable/formal/") and "lean" in rel.lower():
                kind, cid = "formal_runner", "formal.lean_check"
            elif rel.startswith("executable/formal/") and "tla" in rel.lower():
                kind, cid = "formal_runner", "formal.tla_check"
            elif rel.startswith("kernel/"):
                kind, cid = "kernel_contract", "kernel." + Path(rel).stem
            elif rel.startswith("Duotronic/") or rel.endswith(".lean"):
                kind, cid = "lean_source", "proof_source." + Path(rel).stem
            elif rel.endswith(".tla"):
                kind, cid = "tla_source", "state_source." + Path(rel).stem
            if kind and cid:
                capabilities.append({"id": cid, "kind": kind, "path": rel, "digest": item.get("digest"), "safe": safe})
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for cap in capabilities:
            key = str(cap.get("id")) + str(cap.get("path"))
            if key in seen:
                continue
            seen.add(key)
            out.append(cap)
        return out[:200]

    def _file_digest(self, path: Path) -> str:
        import hashlib
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return "sha256:" + h.hexdigest()
