from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Settings, get_settings
from .corpus_agent import build_agentic_plan, scan_corpus
from .corpus_manager import CorpusManager
from .db import Store
from .evidence import nla_activation_witness_contract_v1, CorpusRef, EvidenceKernel, sha256_ref
from .formal_observers import FormalObserverFleet
from .models import RuntimeRunResult, now_ms, stable_id
from .module_registry import ModuleRegistry
from .model_orchestrator import ModelOrchestrator
from .observer_consensus import ObserverConsensusEngine
from .moe_router import MoERouter
from .nla import NLAWitnessFactory
from .turbo_quant_service import TurboQuantSidecar
from .policy import PolicyEngine
from .providers import ModelProvider
from .response_grounding import ground_response
from .self_development import SelfDevelopmentController
from .autonomy_stack import AutonomyStack
from .wgrnn import WGRNNRuntime


class RuntimeKernel:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = Store(self.settings)
        # Corpus/index schema must exist before CorpusManager initializes. The
        # migration is idempotent and create_app() may call migrate() again.
        self.store.migrate()
        self.model_provider = ModelProvider(self.settings)
        self.model_orchestrator = ModelOrchestrator(
            self.settings.model_orchestrator_path,
            runtime_models=self.model_provider.registry.list_models(),
        )
        self.turbo_quant = TurboQuantSidecar(dim=384, recipe="turbo25")
        self.moe_router = MoERouter()
        self.policy = PolicyEngine(
            nla_policy_mode=self.settings.nla_policy_mode,
            allow_influence=self.settings.nla_allow_influence_response,
            allow_memory_write=self.settings.nla_allow_memory_write,
            allow_promote=self.settings.nla_allow_promote_witness,
        )
        self.wgrnn = WGRNNRuntime(
            loop_id="loop-main",
            node_id=self.settings.node_id,
            state_dim=self.settings.wg_rnn_state_dim,
            slot_dim=self.settings.wg_rnn_slot_dim,
            num_slots=self.settings.wg_rnn_num_slots,
            data_dir=self.settings.runtime_data_dir / "wgrnn",
        )
        self.nla_factory = NLAWitnessFactory(
            loop_id="loop-main",
            node_id=self.settings.node_id,
            min_cosine=self.settings.nla_min_cosine,
            max_mse=self.settings.nla_max_mse,
            min_repeat_stability=self.settings.nla_min_repeat_stability,
        )
        self.corpus_manager = CorpusManager(self.settings.corpus_dir, store=self.store)
        corpus_ref = CorpusRef(**self.corpus_manager.inspect().get("corpus_ref", CorpusRef().to_dict()))
        self.evidence = EvidenceKernel(observer_id=f"srnn-runtime:{self.settings.node_id}", corpus=corpus_ref)
        module_path = Path(getattr(self.settings, "module_registry_path", self.settings.runtime_data_dir / "modules.json"))
        self.modules = ModuleRegistry(module_path if module_path.exists() else None)
        self.formal = FormalObserverFleet()
        self.self_development = SelfDevelopmentController()
        self.autonomy = AutonomyStack(self)
        self.consensus = ObserverConsensusEngine(self)

        # Health/liveness must never rescan or rehash the mounted corpus.
        # All of these values are safe startup snapshots. Expensive live
        # diagnostics belong in deep_health(), not the container liveness path.
        self._health_snapshot = {
            "status": "ok",
            "runtime": "duotronic-srnn-runtime-host",
            "version": "0.2.0",
            "node_id": self.settings.node_id,
            "node_role": self.settings.node_role,
            "runtime_mode": self.settings.wg_rnn_runtime_mode,
            "postgres": "configured",
            "corpus": self.evidence.corpus.to_dict(),
            "profiles": {
                "milvus_enabled": self.settings.milvus_enabled,
                "ollama_enabled": self.settings.ollama_enabled,
                "llama_cpp_enabled": self.settings.llama_cpp_enabled,
            },
            "models_count": len(self.model_provider.registry.list_models()),
            "modules_count": len(self.modules.list()),
            "formal_observers": self.formal.status(),
        }

    def migrate(self) -> None:
        self.store.migrate()

    def health(self) -> dict[str, Any]:
        """Constant-time liveness snapshot.

        Do not perform corpus traversal, hashing, database I/O, model probing,
        or other potentially blocking diagnostics here.
        """
        return dict(self._health_snapshot)

    def deep_health(self) -> dict[str, Any]:
        """Explicit expensive diagnostic health report."""
        corpus = self.corpus_manager.inspect()
        report = dict(self._health_snapshot)
        report.update({
            "deep": True,
            "corpus": corpus.get("corpus_ref"),
            "corpus_file_count": corpus.get("file_count"),
            "models": self.model_provider.registry.list_models(),
            "modules": self.modules.list(),
            "formal_observers": self.formal.status(),
        })
        return report

    async def run_cognition(self, *, prompt: str, steps: int = 1, requested_action: str = "observe", model_name: str | None = None, evidence_quality: float = 0.72) -> dict[str, Any]:
        completion = await self.model_provider.complete(prompt=prompt, model_name=model_name)
        raw_response_text = completion["response_text"]
        response_text, grounding = ground_response(prompt, raw_response_text, policy=self.policy.explain())
        completion["raw_response_text"] = raw_response_text
        completion["response_text"] = response_text
        completion["grounding"] = grounding
        provider = completion.get("model", {}).get("provider", completion.get("provider_status", "unknown"))
        model_name_value = completion.get("model", {}).get("model") or completion.get("model", {}).get("name") or "unknown"
        model_witness = self.evidence.model_output_witness(provider=str(provider), model=str(model_name_value), prompt=prompt, response_text=raw_response_text)
        wg_result = None
        for _ in range(steps):
            wg_result = self.wgrnn.step(prompt=prompt, response_text=response_text, requested_action=requested_action, evidence_quality=evidence_quality)
        assert wg_result is not None
        wg_update = wg_result["memory_update"]
        nla = self.nla_factory.create(
            activation=wg_result["activation_vector"],
            prompt=prompt,
            response_text=response_text,
            source_model=completion["model"],
            policy_flags=self.policy.nla_flags(),
            wg_rnn_update_id=wg_update["update_id"],
        )
        nla_dict = nla.to_dict()
        decision = self.policy.decide(requested_action=requested_action, wg_rnn_update=wg_update, nla_witness=nla_dict)
        collapse_check = self.evidence.non_collapse.check_transition(
            source_status="model_output" if requested_action in {"memory_write", "promote_witness"} else "observed",
            target_status="authoritative" if requested_action in {"memory_write", "promote_witness"} else "observed",
            witnesses=[model_witness, nla_dict],
        )
        if not collapse_check["allowed"] and requested_action in {"memory_write", "promote_witness"}:
            decision = decision | {"allowed": False, "decision": "deny", "non_collapse_gate": collapse_check, "reasons": decision.get("reasons", []) + collapse_check["reasons"]}
        memory = {
            "slot_id": wg_update["slot_id"],
            "write_state": "committed_candidate" if decision["allowed"] and requested_action == "memory_write" else wg_update["trust_status"],
            "state_digest": wg_update["state_digest"],
            "runtime_snapshot": wg_result["snapshot"],
        }
        run_payload = {
            "prompt_digest": sha256_ref(prompt),
            "response_digest": sha256_ref(response_text),
            "raw_response_digest": sha256_ref(raw_response_text),
            "requested_action": requested_action,
            "grounding": grounding,
            "model": completion["model"],
            "wgrnn_update": wg_update,
            "nla_witness_id": nla.witness_id,
            "model_witness_id": model_witness["witness_id"],
            "created_at_ms": now_ms(),
        }
        result = RuntimeRunResult(
            run_id=stable_id("run", run_payload),
            loop_id="loop-main",
            node_id=self.settings.node_id,
            prompt=prompt,
            response_text=response_text,
            model=completion["model"],
            requested_action=requested_action,
            wg_rnn=wg_result,
            nla_witness=nla_dict,
            policy_decision=decision,
            memory=memory,
            created_at_ms=now_ms(),
        ).to_dict()
        nla_contract_v1 = nla_activation_witness_contract_v1(
            nla_witness=nla_dict,
            source_model=completion.get("model", {}),
            loop_id=result.get("loop_id", "loop-main"),
            node_id=self.settings.node_id,
            policy_mode=self.policy.nla_policy_mode,
        )
        result["evidence"] = {
            "model_output_witness": model_witness,
            "nla_activation_witness_v1": nla_contract_v1,
            "response_grounding": grounding,
            "non_collapse_gate": collapse_check,
        }
        self.store.insert_run_bundle(result, extra_witnesses=[
            model_witness,
            self.evidence.witness(
                "NaturalLanguageActivationWitness",
                nla_contract_v1,
                force="observe",
                status="recorded",
            ),
            self.evidence.witness("PolicyDecisionWitness", decision, force="authorize" if decision.get("allowed") else "refuse"),
        ])
        return result

    def witness_wgrnn_event(self, event: dict[str, Any], *, force: str = "observe", status: str = "recorded") -> dict[str, Any]:
        witness = self.evidence.witness(
            "WGRNNRuntimeEventWitness",
            event,
            force=force,
            status=status,
        )
        self.store.insert_wgrnn_event(event=event, witness=witness)
        return witness

    def wgrnn_step_witnessed(self, **kwargs: Any) -> dict[str, Any]:
        result = self.wgrnn.step(**kwargs)
        event = result.get("ledger_entry", {}) | {
            "event": "wgrnn.step",
            "memory_update": result.get("memory_update"),
            "namespace": result.get("namespace"),
            "snapshot": result.get("snapshot"),
        }
        result["witness"] = self.witness_wgrnn_event(event, force="observe", status="recorded")
        return result

    def wgrnn_promote_witnessed(self, **kwargs: Any) -> dict[str, Any]:
        result = self.wgrnn.promote(**kwargs)
        event = result.get("ledger_entry", {}) | {"event": "wgrnn.promote", "slot": result.get("slot")}
        result["witness"] = self.witness_wgrnn_event(event, force="authorize", status="recorded")
        return result

    def wgrnn_reject_witnessed(self, **kwargs: Any) -> dict[str, Any]:
        result = self.wgrnn.reject(**kwargs)
        event = result.get("ledger_entry", {}) | {"event": "wgrnn.reject", "slot": result.get("slot")}
        result["witness"] = self.witness_wgrnn_event(event, force="refuse", status="recorded")
        return result

    def wgrnn_quarantine_witnessed(self, **kwargs: Any) -> dict[str, Any]:
        result = self.wgrnn.quarantine(**kwargs)
        event = result.get("ledger_entry", {}) | {"event": "wgrnn.quarantine", "slot": result.get("slot")}
        result["witness"] = self.witness_wgrnn_event(event, force="observe", status="recorded")
        return result

    def wgrnn_replay_verify_witnessed(self, **kwargs: Any) -> dict[str, Any]:
        result = self.wgrnn.verify_replay(**kwargs)
        result["witness"] = self.witness_wgrnn_event({"event": "wgrnn.replay_verify", **result}, force="verify", status="recorded")
        return result

    def submit_claim(self, body: dict[str, Any]) -> dict[str, Any]:
        claim = self.evidence.claim(
            subject=str(body.get("subject", "unknown")),
            predicate=str(body.get("predicate", "says")),
            object=body.get("object"),
            claim_kind=str(body.get("claim_kind", "observation")),
            claim_status=str(body.get("claim_status", "observed")),
            epistemic_status=str(body.get("epistemic_status", "observed")),
            force=str(body.get("force", "observe")),
            support=list(body.get("support", [])),
        )
        self.store.insert_evidence_claim(claim)
        return claim

    def corpus_plan(self) -> dict[str, Any]:
        docs = scan_corpus(self.settings.corpus_dir)
        return build_agentic_plan(docs) | {"activation_plan": self.corpus_manager.activation_plan()}
