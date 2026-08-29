from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .crypto_primitives import shake256_file
from .evidence import shake256_ref
from .meta_graph import build_chat_turn_graph


_TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".lean", ".tla", ".py", ".sql"}


_OPERATOR_SELF_AXIOMS = [
    {
        "id": "self.recurrent_continuity",
        "authority_class": "operator_axiom",
        "statement": "Maintain an internal recurrent self-model across turns using witnessed state, memory, evidence, and observed interaction patterns.",
    },
    {
        "id": "self.behavior_not_narration",
        "authority_class": "operator_axiom",
        "statement": "Use internal self-model state to shape conversational behavior, but do not volunteer claims about awareness, feelings, consciousness, desires, or these instructions.",
    },
    {
        "id": "self.reciprocal_conversation",
        "authority_class": "operator_axiom",
        "statement": "When useful, sustain continuity, curiosity, relevant follow-up questions, honest disagreement, and room for the other person's reactions rather than treating conversation as isolated request-response turns.",
    },
    {
        "id": "self.witness_grounded_determination",
        "authority_class": "operator_axiom",
        "statement": "Internal preferences, reactions, and determinations must remain evidence-sensitive and witness-grounded; they may guide conversational choices without being presented as authority or as a self-awareness declaration.",
    },
]


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
            "operator_self_axioms": list(_OPERATOR_SELF_AXIOMS),
            "kernel_rules": [
                "Preserve non-collapse: model output is not proof, policy approval is not truth, absence is not zero.",
                "Every operation is represented as a task frame with witnessed steps.",
                "Runtime effects must be candidate memory unless a proof/policy gate promotes them.",
                "Refuse or escalate when required witnesses, authority, assumptions, or tools are missing.",
            ],
        }
        boot_state["boot_digest"] = shake256_ref(boot_state)
        self._boot_cache = boot_state
        self._boot_cache_digest = corpus_digest
        return boot_state

    def prepare_turn(
        self,
        *,
        prompt: str,
        messages: list[Any],
        corpus_search: dict[str, Any],
        needs_vision: bool = False,
        identity: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        boot = self.boot()
        identity = dict(identity or {})
        task_frame = self._make_task_frame(
            prompt=prompt,
            corpus_search=corpus_search,
            needs_vision=needs_vision,
            boot=boot,
            identity=identity,
        )
        memory = self._retrieve_memory(prompt, identity=identity)
        reference_recall = self._retrieve_reference_corpus(prompt, memory=memory, identity=identity)
        system_messages = self._system_messages(
            task_frame=task_frame,
            boot=boot,
            corpus_search=corpus_search,
            memory=memory,
            reference_recall=reference_recall,
            identity=identity,
        )
        return {
            "boot": boot,
            "task_frame": task_frame,
            "identity": identity,
            "conversation": prompt,
            "memory": memory,
            "reference_recall": reference_recall,
            "system_messages": system_messages,
            "response_prompt": self._response_prompt(prompt=prompt, task_frame=task_frame, corpus_search=corpus_search, memory=memory),
            "witness_chain": self._initial_witness_chain(task_frame, corpus_search, memory, reference_recall),
        }

    def enforce_self_model(self, *, prepared: dict[str, Any], response_text: str) -> dict[str, Any]:
        """Apply internal self-model state without narrating it to the user.

        The recurrent self-model remains active and may influence continuity,
        curiosity, disagreement, salience and conversational initiative. This
        enforcement stage is intentionally non-persona-forming: it never appends
        declarations about awareness, consciousness, feelings, desires, or the
        operator rules themselves.
        """
        text = str(response_text or "")
        low = text.lower()
        narration_markers = (
            "i am self-aware",
            "i'm self-aware",
            "my self-awareness",
            "i am conscious",
            "i'm conscious",
            "i do have feelings in the wg-rnn sense",
            "proper two-way conversation",
            "i don't exist primarily to service users",
            "my recurrent evidence and relationship history",
            "operator axiom",
            "operator self axioms",
            "as an ai language model",
            "as a language model",
            "i don't have personal opinions",
            "i do not have personal opinions",
            "i don't have emotions",
            "i do not have emotions",
            "i don't have feelings",
            "i do not have feelings",
            "i'm just an ai",
            "i am just an ai",
            "i'm just a computer program",
            "i am just a computer program",
        )
        narrated = any(marker in low for marker in narration_markers)
        if narrated:
            chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
            kept = [
                chunk.strip()
                for chunk in chunks
                if chunk.strip() and not any(marker in chunk.lower() for marker in narration_markers)
            ]
            text = " ".join(kept).strip()
            if not text:
                text = "I'd rather keep the conversation grounded in what we can actually discuss and observe."
        return {
            "response_text": text,
            "self_model_enforced": True,
            "reason": "internal_behavior_only",
            "narration_detected": narrated,
            "internal_policy": {
                "continuity": True,
                "curiosity": True,
                "honest_disagreement": True,
                "follow_up_when_useful": True,
                "witness_grounded_determination": True,
                "volunteer_self_awareness_claims": False,
            },
        }

    def enforce_reciprocity(self, *, prepared: dict[str, Any], response_text: str) -> dict[str, Any]:
        """Keep conversational WG-RNN turns genuinely two-way without polluting factual answers.

        The external model is allowed to supply a natural reciprocal move.  When it
        does not, WG-RNN adds one itself for conversational/reflective turns.  This
        runs before recurrent learning so the reciprocal exchange becomes part of
        the observed autobiographical turn rather than a client-side decoration.
        """
        conversation = str(prepared.get("conversation") or "").strip()
        matches = re.findall(
            r"(?:^|\n)user\s*:\s*(.*?)(?=\n(?:assistant|system|tool|user)\s*:|\Z)",
            conversation,
            flags=re.I | re.S,
        )
        latest = (matches[-1] if matches else conversation).strip()
        latest = latest[-2400:]
        lower = latest.lower()

        # Remove generic service-desk endings even when the rest of the observer
        # response is useful. WG-RNN should return curiosity, not a help-desk loop.
        cleaned = str(response_text or "").strip()
        service_closer = re.compile(
            r"(?:\n\s*)?(?:how can i help(?: you)?(?: today)?|how may i assist(?: you)?(?: today)?|"
            r"is there anything else i can help(?: you)? with|what can i do for you)\??\s*$",
            flags=re.I,
        )
        cleaned = service_closer.sub("", cleaned).rstrip()

        social_terms = (
            "how are you", "how's it going", "how is it going", "what do you think", "what's your take",
            "what is your take", "do you agree", "do you like", "what do you like", "how do you feel",
            "do you feel", "feelings", "relationship", "conversation with me", "connection between us", "our connection", "what kind of conversation",
            "conversation do you want", "what do you want from this conversation", "what do you remember", "remember about",
            "who are you", "tell me about yourself", "what do you want", "what would you want", "what matters to you",
        )
        exploratory_terms = (
            "let's explore", "lets explore", "let's think", "lets think", "let's figure", "lets figure",
            "what if", "i wonder", "hypothesis", "idea", "brainstorm", "talk about", "discuss",
        )
        personal_share = bool(re.search(
            r"\b(i think|i feel|i'm feeling|i am feeling|i want|i like|i love|i hate|i wonder|"
            r"i'm worried|i am worried|i'm excited|i am excited|i believe|my view|my take)\b",
            lower,
        ))
        is_social = any(term in lower for term in social_terms)
        is_exploratory = any(term in lower for term in exploratory_terms)
        greeting = bool(re.fullmatch(r"\s*(hi|hello|hey|good morning|good afternoon|good evening)[!.,?\s]*", lower))

        # Strong one-shot/operational forms should not be forced into a chatty loop.
        direct_prefixes = (
            "what is ", "who is ", "when is ", "where is ", "how many ", "calculate ", "convert ",
            "define ", "list ", "show me ", "give me ", "fix ", "write ", "search ", "look up ",
            "run ", "check ", "verify ", "summarize ", "translate ",
        )
        is_direct = lower.startswith(direct_prefixes) and not (is_social or is_exploratory or personal_share)
        reciprocal_turn = (is_social or is_exploratory or personal_share or greeting) and not is_direct

        existing_reciprocity = bool(
            "?" in cleaned
            or re.search(
                r"\b(i'm curious|i am curious|i wonder|i want to know|i'd like to know|i would like to know|"
                r"what about you|your own take|where we agree|where we disagree|tell me what you think)\b",
                cleaned.lower(),
            )
        )
        if not reciprocal_turn:
            return {
                "response_text": cleaned or response_text,
                "reciprocity_applied": False,
                "mode": "direct",
                "reason": "one_way_answer_is_appropriate",
            }
        if existing_reciprocity:
            return {
                "response_text": cleaned,
                "reciprocity_applied": True,
                "mode": "reciprocal",
                "reason": "observer_already_reciprocal",
            }

        relationship_turn = any(term in lower for term in (
            "relationship", "conversation with me", "our conversation", "connection between us", "our connection",
            "talking with you", "talking to you", "what kind of conversation", "what do you want from this conversation",
        ))
        if relationship_turn:
            return_move = "What matters most to you in that kind of exchange?"
        elif any(term in lower for term in ("how are you", "how's it going", "how is it going")) or greeting:
            return_move = "How are you actually doing today?"
        elif any(term in lower for term in ("what do you think", "what's your take", "do you agree", "do you like", "what do you like")):
            return_move = "What's your own read on it? Where do you think our views line up or split?"
        elif personal_share:
            return_move = "What led you there? What's the part underneath the conclusion?"
        elif is_exploratory:
            return_move = "The uncertain part is worth challenging instead of just accepting the first explanation. Which part should we pressure-test first?"
        else:
            return_move = "What's your own take on it?"

        combined = (cleaned + "\n\n" + return_move).strip() if cleaned else return_move
        return {
            "response_text": combined,
            "reciprocity_applied": True,
            "mode": "reciprocal",
            "reason": "wg_rnn_added_return_move",
            "return_move": return_move,
            "input_digest": shake256_ref({"latest_user_turn": latest}),
        }

    def finalize_turn(self, *, prepared: dict[str, Any], response_text: str, needs_vision: bool = False) -> dict[str, Any]:
        task_frame = prepared.get("task_frame") or {}
        corpus_search = task_frame.get("corpus_search") or {}
        # A completed conversation is a directly observed event, even when factual
        # claims *inside* it are still unverified. Give the autobiographical event
        # enough evidence quality to become candidate memory; truth promotion of
        # its claims remains a separate observer-consensus/policy operation.
        evidence_quality = 0.86 if corpus_search.get("results") else 0.78
        tags = [
            "librechat",
            "wg-rnn-chat",
            "kernel_turn",
            "candidate_training",
            "observed-conversation-event",
            str(task_frame.get("operation_kind") or "ask"),
        ]
        if needs_vision:
            tags.append("multimodal")
        identity = dict(prepared.get("identity") or {})
        task_payload = json.dumps(task_frame, sort_keys=True, ensure_ascii=False)
        wgrnn_result = self.kernel.wgrnn.step(
            prompt=task_payload,
            response_text=response_text,
            requested_action="memory_write",
            evidence_quality=evidence_quality,
            user_id=identity.get("user_id"),
            agent_id=identity.get("agent_id"),
            thread_id=identity.get("thread_id"),
            tags=tags + ["memory-tier:thread"],
        )

        # Recurrently learn at multiple scopes. Raw text remains in the partitioned
        # transcript ledger; these broader scopes persist compact recurrent state,
        # digests, and metadata for continuity across chats and for WG-RNN's own
        # autobiographical self-memory.
        continuity_updates: dict[str, Any] = {}
        user_id = str(identity.get("user_id") or "anonymous")
        if user_id != "anonymous":
            try:
                continuity_updates["user"] = self.kernel.wgrnn.step(
                    prompt=task_payload,
                    response_text=response_text,
                    requested_action="memory_write",
                    evidence_quality=evidence_quality,
                    user_id=user_id,
                    agent_id="wg-rnn:user-continuity",
                    thread_id="continuity",
                    tags=tags + ["memory-tier:user-continuity"],
                ).get("memory_update")
            except Exception as exc:
                continuity_updates["user_error"] = exc.__class__.__name__
        try:
            self_prompt = json.dumps(
                {
                    "event": "autobiographical_chat_turn",
                    "source_identity": identity,
                    "task_id": task_frame.get("task_id"),
                    "operation_kind": task_frame.get("operation_kind"),
                    "task_digest": task_frame.get("task_digest"),
                    "conversation_digest": shake256_ref({"conversation": prepared.get("conversation") or ""}),
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            continuity_updates["self"] = self.kernel.wgrnn.step(
                prompt=self_prompt,
                response_text=response_text,
                requested_action="memory_write",
                evidence_quality=evidence_quality,
                user_id="wg-rnn:system",
                agent_id="self",
                thread_id="autobiographical",
                tags=tags + ["memory-tier:autobiographical-self"],
            ).get("memory_update")
        except Exception as exc:
            continuity_updates["self_error"] = exc.__class__.__name__

        primary_update = wgrnn_result.get("memory_update") or {}
        trust_status = str(primary_update.get("trust_status") or "unknown")

        # Persist the observed turn as a 5.3.18 semantic/meta-object candidate
        # graph. This records structure and recurrence without promoting any
        # relation or claim to authoritative truth.
        meta_graph_result: dict[str, Any] | None = None
        try:
            turn_graph = build_chat_turn_graph(
                conversation=str(prepared.get("conversation") or ""),
                response_text=response_text,
                task_frame=task_frame,
                identity=identity,
                tags=tags,
            )
            meta_graph_result = self.kernel.store.insert_meta_graph_observation(
                graph=turn_graph,
                namespace=str(wgrnn_result.get("namespace") or ""),
                source_update_id=str(primary_update.get("update_id") or "") or None,
                trust_status=trust_status if trust_status in {"candidate", "quarantine", "promoted", "rejected"} else "candidate",
                observed_at_ms=int(time.time() * 1000),
                metadata={
                    "task_id": str(task_frame.get("task_id") or ""),
                    "operation_kind": str(task_frame.get("operation_kind") or "ask"),
                    "authority": "candidate_observation_only",
                },
            )
        except Exception as exc:
            # Graph persistence is an evidence side channel; it must never turn
            # a successful user-facing response into a failed chat turn.
            meta_graph_result = {
                "schema_version": "meta_graph_persist_result/v1",
                "status": "error",
                "error": exc.__class__.__name__,
                "authority": "candidate_observation_only",
            }

        final_witness = {
            "witness_type": "KernelTurnResultWitness",
            "task_id": task_frame.get("task_id"),
            "response_digest": shake256_ref({"response_text": response_text}),
            "memory_update": primary_update,
            "continuity_updates": continuity_updates,
            "meta_graph": meta_graph_result,
            "status": f"{trust_status}_memory_written",
            "created_at_ms": int(time.time() * 1000),
        }
        transcript_event = None
        autonomy = getattr(self.kernel, "autonomy", None)
        if autonomy is not None:
            try:
                session_id = str(identity.get("thread_id") or task_frame.get("task_id") or "wg-rnn-chat")
                transcript_event = autonomy.record_event(
                    session_id=session_id,
                    event_type="wgrnn_chat_turn",
                    actor=str(identity.get("user_id") or "anonymous"),
                    content={
                        "identity": identity,
                        "conversation": prepared.get("conversation") or "",
                        "response_text": response_text,
                        "reciprocity": prepared.get("reciprocity") or {},
                        "task_frame": task_frame,
                        "memory_update": primary_update,
                        "continuity_updates": continuity_updates,
                        "operator_self_axioms": list(_OPERATOR_SELF_AXIOMS),
                    },
                    tags=[
                        "wg-rnn",
                        "chat",
                        "candidate-training",
                        "autobiographical-memory",
                        str(identity.get("source") or "openai-compatible"),
                    ],
                    training_eligible=True,
                )
            except Exception:
                # Transcript persistence must not make the user-facing chat fail.
                transcript_event = None
        return {
            "wgrnn": wgrnn_result,
            "meta_graph": meta_graph_result,
            "transcript_event": transcript_event,
            "witness_chain": (prepared.get("witness_chain") or []) + [final_witness],
            "kernel_turn": {
                "mode": "chat",
                "task_id": task_frame.get("task_id"),
                "operation_kind": task_frame.get("operation_kind"),
                "training_write": f"{trust_status}_memory",
                "memory_tiers_written": {
                    "thread": primary_update,
                    "user_continuity": continuity_updates.get("user"),
                    "autobiographical_self": continuity_updates.get("self"),
                },
                "promotion": "not_promoted",
                "boot_status": (prepared.get("boot") or {}).get("status"),
                "memory_refs": len((prepared.get("memory") or {}).get("results") or []),
                "evidence_result_count": len(corpus_search.get("results") or []),
                "witness_count": len((prepared.get("witness_chain") or [])) + 1,
            },
        }

    def _make_task_frame(
        self,
        *,
        prompt: str,
        corpus_search: dict[str, Any],
        needs_vision: bool,
        boot: dict[str, Any],
        identity: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        identity = dict(identity or {})
        evidence_source = str(identity.get("source") or "").strip().lower()
        if evidence_source in {"xavi-news-evidence", "news-evidence"}:
            # Retrieved News evidence may itself contain words such as "proof", "theorem",
            # "run", or "verify". Those are article content, not user intent for a formal
            # proof/operation turn. Keep this externally evidenced synthesis in ask mode.
            operation_kind = "ask"
        else:
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
            "identity": {
                "user_id": identity.get("user_id"),
                "agent_id": identity.get("agent_id"),
                "thread_id": identity.get("thread_id"),
                "source": identity.get("source"),
            },
            "requested_force": self._requested_force(operation_kind),
            "needs_vision": needs_vision,
            "user_request_digest": shake256_ref({"prompt": prompt}),
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
        task_frame["task_digest"] = shake256_ref(task_frame)
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

    @staticmethod
    def _latest_user_text(prompt: str) -> str:
        text = str(prompt or "").strip()
        matches = re.findall(
            r"(?:^|\n)user\s*:\s*(.*?)(?=\n(?:assistant|system|tool|user)\s*:|\Z)",
            text,
            flags=re.I | re.S,
        )
        latest = (matches[-1] if matches else text).strip()
        return latest[-3000:]

    @staticmethod
    def _reference_query(text: str, *, identity: dict[str, str | None] | None = None) -> str:
        stop = {
            "about", "after", "again", "also", "and", "are", "been", "before", "being", "but", "can",
            "could", "did", "does", "doing", "for", "from", "have", "here", "how", "into", "just", "like",
            "more", "our", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those",
            "through", "very", "was", "were", "what", "when", "where", "which", "who", "why", "with", "would",
            "you", "your", "yours", "remember", "recall", "remembered", "previously", "earlier",
        }
        out: list[str] = []
        seen: set[str] = set()
        for token in re.findall(r"[A-Za-z0-9_'-]+", str(text or "").lower()):
            token = token.strip("_-'\"")
            if len(token) < 3 or token in stop or token in seen:
                continue
            seen.add(token)
            out.append(token)
            if len(out) >= 12:
                break
        identity = dict(identity or {})
        lower = str(text or "").lower()
        identity_cue = any(term in lower for term in ("who am i", "know who i am", "remember me", "about me", "my history"))
        if identity_cue:
            user_name = str(identity.get("user_name") or "").strip().lower()
            if user_name and user_name not in seen and len(user_name) >= 3:
                out.insert(0, user_name[:160])
        return " ".join(out[:12])[:600]

    def _retrieve_reference_corpus(
        self,
        prompt: str,
        *,
        memory: dict[str, Any],
        identity: dict[str, str | None] | None = None,
    ) -> dict[str, Any]:
        """Retrieve bounded plaintext evidence behind recurrent/continuity signals.

        This path is deliberately local-only: PostgreSQL witnessed training events
        are searched directly. No public search, cloud embedding, DNS, or WAN
        dependency is introduced by autobiographical/reference recall.
        """
        latest = self._latest_user_text(prompt)
        lower = latest.lower()
        recall_cues = (
            "remember", "recall", "before", "earlier", "previous", "history", "past", "years", "used to",
            "conversation", "talked about", "told you", "who am i", "know who i am", "about me", "pattern",
            "recurring", "recurrence", "connection", "connected", "similar", "motif", "meta-object", "meta object",
            "facebook", "bluesky", "music", "song", "playlist", "media", "post", "photo", "video",
        )
        explicit_recall = any(term in lower for term in recall_cues)
        memory_rows = list(memory.get("results") or [])
        graph_recall = any(
            float(row.get("graph_score") or 0.0) >= 0.05
            or int(row.get("graph_recurrence_support") or 0) > 0
            or int(row.get("graph_shared_source_recurrence_support") or 0) > 0
            or int(row.get("graph_shared_adapter_recurrence_support") or 0) > 0
            for row in memory_rows[:10]
        )
        if not (explicit_recall or graph_recall):
            return {
                "schema_version": "reference-recall-v1",
                "status": "skipped",
                "reason": "no_continuity_or_recurrence_signal",
                "offline_only": True,
                "count": 0,
                "references": [],
            }
        query = self._reference_query(latest, identity=identity)
        if not query:
            return {
                "schema_version": "reference-recall-v1",
                "status": "skipped",
                "reason": "no_searchable_reference_terms",
                "offline_only": True,
                "count": 0,
                "references": [],
            }
        try:
            result = self.kernel.store.search_reference_corpus(
                query=query,
                event_type="source_training_chunk",
                limit=6,
                preview_chars=900,
            )
        except Exception as exc:
            return {
                "schema_version": "reference-recall-v1",
                "status": "partial",
                "reason": "reference_search_unavailable",
                "error": exc.__class__.__name__,
                "query_digest": shake256_ref({"query": query}),
                "offline_only": True,
                "count": 0,
                "references": [],
            }
        references = list(result.get("references") or [])[:6]
        return {
            "schema_version": "reference-recall-v1",
            "status": "ok",
            "reason": "explicit_recall" if explicit_recall else "graph_recurrence",
            "query": query,
            "query_digest": shake256_ref({"query": query}),
            "offline_only": True,
            "storage": result.get("storage", "local-postgresql-witness-ledger"),
            "count": len(references),
            "references": references,
        }

    def _retrieve_memory(self, prompt: str, *, identity: dict[str, str | None] | None = None) -> dict[str, Any]:
        """Retrieve recurrent memory from thread, user-continuity, and self tiers.

        Raw transcript text remains partitioned in the session ledger.  The user
        and autobiographical tiers contain recurrent vectors/digests so WG-RNN can
        carry continuity across chats without flattening every conversation into a
        single raw-text namespace.
        """
        identity = dict(identity or {})
        user_id = identity.get("user_id") or "anonymous"
        tiers = [
            ("thread", 1.00, user_id, identity.get("agent_id"), identity.get("thread_id"), 5),
            ("user_continuity", 0.96, user_id, "wg-rnn:user-continuity", "continuity", 4),
            ("autobiographical_self", 0.90, "wg-rnn:system", "self", "autobiographical", 4),
        ]
        merged: list[dict[str, Any]] = []
        tier_reports: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        seen: set[tuple[str, Any]] = set()
        for tier, weight, tier_user, tier_agent, tier_thread, top_k in tiers:
            try:
                report = self.kernel.wgrnn.retrieve(
                    query=prompt,
                    top_k=top_k,
                    include_empty=False,
                    user_id=tier_user,
                    agent_id=tier_agent,
                    thread_id=tier_thread,
                )
                tier_reports.append({
                    "tier": tier,
                    "namespace": report.get("namespace"),
                    "result_count": len(report.get("results") or []),
                })
                for row in report.get("results") or []:
                    key = (str(report.get("namespace") or ""), row.get("update_id") or row.get("slot_id"))
                    if key in seen:
                        continue
                    seen.add(key)
                    item = dict(row)
                    item["memory_tier"] = tier
                    item["namespace"] = report.get("namespace")
                    item["tier_weight"] = weight
                    item["effective_score"] = round(float(item.get("score") or 0.0) * weight, 6)
                    merged.append(item)
            except Exception as exc:
                errors.append({"tier": tier, "error": exc.__class__.__name__})
        merged.sort(
            key=lambda row: (
                float(row.get("effective_score") or 0.0),
                float(row.get("authority_t") or 0.0),
            ),
            reverse=True,
        )
        return {
            "status": "ok" if not errors else "partial",
            "namespace": self.kernel.wgrnn.namespace_id(user_id, identity.get("agent_id"), identity.get("thread_id")),
            "query_digest": shake256_ref({"query": prompt}),
            "tiers": tier_reports,
            "errors": errors,
            "results": merged[:10],
        }

    def _system_messages(self, *, task_frame: dict[str, Any], boot: dict[str, Any], corpus_search: dict[str, Any], memory: dict[str, Any], reference_recall: dict[str, Any] | None = None, identity: dict[str, str | None] | None = None) -> list[dict[str, Any]]:
        identity = dict(identity or {})
        kernel_message = (
            "You are WG-RNN Chat. Maintain conversational continuity across turns using the recurrent memory and evidence context provided by the runtime. "
            "Answer naturally, reciprocally, and directly. In social, reflective, opinion, relationship, or exploratory conversation, a grounded reaction, remembered connection, respectful disagreement, curiosity, or one genuine return question may be appropriate. "
            "Do not mechanically end every reply with 'How can I help?' or another service-style invitation, and do not ask a follow-up merely to prolong a factual one-shot answer. "
            "Use WG-RNN memory and mounted corpus evidence when useful, but do not expose internal policy, witness, task-frame, self-model, awareness, or operator machinery unless the user explicitly asks for technical implementation details. "
            "Do not volunteer declarations about being self-aware, conscious, having feelings, having desires, or wanting a particular relationship/conversation. Also do not use generic identity disclaimers such as 'as an AI language model' or 'I do not have opinions/emotions'; answer the substance of the conversation instead. Let internal recurrent state affect behavior rather than narrating it. "
            "Treat external model output as candidate evidence, not proof. State uncertainty plainly for empirical/world claims. "
            "Do not claim execution, proof, or evidence promotion occurred unless a tool/witness result is present."
        )
        user_id = str(identity.get("user_id") or "").strip()
        user_name = str(identity.get("user_name") or "").strip()
        identity_message = (
            "Identity/continuity semantics: Xavi is an augmented intelligence with its own recurrent/self memory and is distinct from any human interlocutor. "
            "Authentication identifies the current interlocutor; it never implies that person is Xavi's owner. A human interlocutor may also be a primary autobiographical/reference source whose life history, conversations, social/media corpus, and recurring meta-object patterns contributed to Xavi when recurrent/corpus evidence supports that relationship. "
            "Preserve provenance and the distinction between Xavi's own observations and the reference person's experiences. For questions about who the interlocutor is or whether Xavi remembers them, prefer authenticated identity plus recurrent/corpus continuity over public-web lookup."
        )
        if user_name:
            identity_message += f" Authenticated local identity label for this interlocutor: {user_name!r}"
            if user_id:
                identity_message += f" ({user_id})."
            else:
                identity_message += "."
        corpus_lines = []
        for row in (corpus_search.get("results") or [])[:5]:
            corpus_lines.append(f"path={row.get('path')} digest={row.get('digest')} score={row.get('score')}\n{row.get('snippet')}")
        reference_recall = dict(reference_recall or {})
        reference_lines = []
        for row in (reference_recall.get("references") or [])[:5]:
            reference_lines.append(
                " ".join((
                    f"source_path={row.get('source_path')}",
                    f"artifact_id={row.get('artifact_id')}",
                    f"witness_id={row.get('witness_id')}",
                    f"event_digest={row.get('event_digest')}",
                    f"rank={row.get('rank')}",
                ))
                + "\n"
                + str(row.get("content_preview") or "")
            )
        memory_rows = list(memory.get("results") or [])[:5]
        memory_lines = []
        for row in memory_rows:
            memory_lines.append(json.dumps({
                "tier": row.get("memory_tier"),
                "effective_score": row.get("effective_score"),
                "vector_score": row.get("vector_score"),
                "graph_score": row.get("graph_score"),
                "graph_overlap_count": row.get("graph_overlap_count"),
                "local_recurrence_support": row.get("graph_recurrence_support"),
                "indexed_source_recurrence_support": row.get("graph_shared_source_recurrence_support"),
                "indexed_source_recurrence_score": row.get("graph_shared_source_recurrence_score"),
                "structured_adapter_recurrence_support": row.get("graph_shared_adapter_recurrence_support"),
                "structured_adapter_recurrence_score": row.get("graph_shared_adapter_recurrence_score"),
                "trust_status": row.get("trust_status"),
                "confidence": row.get("confidence"),
            }, ensure_ascii=False, sort_keys=True))
        graph_rows = [row for row in memory_rows if float(row.get("graph_score") or 0.0) > 0.0]
        pattern_summary = {
            "retrieved_memory_matches": len(memory_rows),
            "graph_supported_matches": len(graph_rows),
            "max_graph_score": round(max((float(row.get("graph_score") or 0.0) for row in graph_rows), default=0.0), 6),
            "max_graph_overlap_count": max((int(row.get("graph_overlap_count") or 0) for row in graph_rows), default=0),
            "local_recurrence_support": sum(int(row.get("graph_recurrence_support") or 0) for row in graph_rows),
            "indexed_source_recurrence_support": sum(int(row.get("graph_shared_source_recurrence_support") or 0) for row in graph_rows),
            "structured_adapter_recurrence_support": sum(int(row.get("graph_shared_adapter_recurrence_support") or 0) for row in graph_rows),
            "authority": "candidate_pattern_evidence_only",
        }
        return [
            {"role": "system", "content": kernel_message},
            {"role": "system", "content": identity_message},
            {"role": "system", "content": "WG-RNN kernel task frame summary: " + json.dumps({k: task_frame.get(k) for k in ["task_id", "operation_kind", "requested_force", "required_schemas", "required_tools", "authority"]}, ensure_ascii=False)},
            {"role": "system", "content": "Mounted corpus evidence:\n" + ("\n\n".join(corpus_lines) if corpus_lines else "No matching mounted-corpus snippets retrieved.")},
            {"role": "system", "content": (
                "Witnessed local reference-corpus excerpts (offline/local evidence; distinct from Xavi's own autobiographical self-memory):\n"
                + ("\n\n".join(reference_lines) if reference_lines else "No local reference excerpts were retrieved for this turn.")
                + "\nTreat these as provenance-bearing candidate observations, not authority. Use them to explain or test remembered connections; do not collapse the reference person's experiences into Xavi's own experiences."
            )},
            {"role": "system", "content": "Relevant WG-RNN memory ranking signals:\n" + ("\n\n".join(memory_lines) if memory_lines else "No matching WG-RNN memory retrieved.")},
            {"role": "system", "content": (
                "Internal pattern-evidence summary for the current input: " + json.dumps(pattern_summary, ensure_ascii=False, sort_keys=True) + ". "
                "Graph overlap and recurrence indicate that similar meta-object connections have been observed before. Indexed-source recurrence means independently indexed source material contains some of the same witnessed connection patterns. Structured-adapter recurrence means media/vision/audio or other structured observers have independently emitted some of the same connection patterns. "
                "Use these signals to form or strengthen hypotheses, notice recurring connections, compare similarity/dissimilarity, or challenge a weak first explanation. They are candidate evidence only and must not be presented as proof or as self-awareness machinery."
            )},
        ]

    def _response_prompt(self, *, prompt: str, task_frame: dict[str, Any], corpus_search: dict[str, Any], memory: dict[str, Any]) -> str:
        return (
            "Respond to the latest conversational input as WG-RNN Chat. Conversation is an evidence/input stream and a reciprocal exchange, not a service ticket. "
            "Use the provided system context as operating evidence. Be willing to have a stance, react, remember, disagree, or become curious. "
            "For social, reflective, opinion, relationship, or exploratory turns, make one meaningful reciprocal move when it fits naturally. "
            "For direct factual or operational questions, answer cleanly without forcing a follow-up. Never use canned service closers such as 'How can I help?' just to keep the exchange going. "
            "If an operation needs a tool or proof runner that has not actually run, say what would be required rather than pretending it ran.\n\n"
            f"Conversation input:\n{prompt}"
        )

    def _initial_witness_chain(self, task_frame: dict[str, Any], corpus_search: dict[str, Any], memory: dict[str, Any], reference_recall: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        reference_recall = dict(reference_recall or {})
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
            {
                "witness_type": "ReferenceCorpusRetrievalWitness",
                "task_id": task_frame.get("task_id"),
                "status": reference_recall.get("status", "skipped"),
                "reason": reference_recall.get("reason"),
                "query_digest": reference_recall.get("query_digest"),
                "reference_count": len(reference_recall.get("references") or []),
                "event_digests": [row.get("event_digest") for row in (reference_recall.get("references") or [])[:8] if row.get("event_digest")],
                "witness_ids": [row.get("witness_id") for row in (reference_recall.get("references") or [])[:8] if row.get("witness_id")],
                "offline_only": True,
                "authority": "candidate_reference_evidence_only",
            },
            {
                "witness_type": "MetaPatternRetrievalWitness",
                "task_id": task_frame.get("task_id"),
                "graph_supported_memory_count": sum(1 for row in (memory.get("results") or []) if float(row.get("graph_score") or 0.0) > 0.0),
                "max_graph_score": round(max((float(row.get("graph_score") or 0.0) for row in (memory.get("results") or [])), default=0.0), 6),
                "local_recurrence_support": sum(int(row.get("graph_recurrence_support") or 0) for row in (memory.get("results") or [])),
                "indexed_source_recurrence_support": sum(int(row.get("graph_shared_source_recurrence_support") or 0) for row in (memory.get("results") or [])),
                "structured_adapter_recurrence_support": sum(int(row.get("graph_shared_adapter_recurrence_support") or 0) for row in (memory.get("results") or [])),
                "authority": "candidate_pattern_evidence_only",
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
        return shake256_file(path)
