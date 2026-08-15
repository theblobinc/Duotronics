from pathlib import Path

from duotronic_runtime.corpus_manager import CorpusManager
from duotronic_runtime.evidence import EvidenceKernel, NonCollapseEngine
from duotronic_runtime.module_registry import ModuleRegistry
from duotronic_runtime.self_development import SelfDevelopmentController


def test_non_collapse_blocks_model_output_to_truth_without_proof():
    gate = NonCollapseEngine().check_transition(source_status="model_output", target_status="truth", witnesses=[])
    assert gate["allowed"] is False
    assert "forbidden epistemic collapse" in gate["reasons"][0]


def test_evidence_kernel_emits_stable_witness_shape():
    kernel = EvidenceKernel(observer_id="test-observer")
    witness = kernel.model_output_witness(provider="echo", model="sandbox", prompt="hello", response_text="world")
    assert witness["witness_type"] == "ModelOutputWitness"
    assert witness["force"] == "propose"
    assert witness["payload"]["non_collapse"]["model_output_is_truth"] is False
    assert witness["witness_id"].startswith("witness_")


def test_corpus_manager_derives_ref_without_manifest(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# Demo\nA corpus doc.")
    manager = CorpusManager(tmp_path)
    inspected = manager.inspect()
    assert inspected["status"] == "ok"
    assert inspected["file_count"] == 1
    assert inspected["corpus_ref"]["digest"].startswith("duoid:shake256-512:")
    validation = manager.validate()
    assert validation["valid"] is True
    assert validation["witness"]["witness_type"] == "CorpusValidationWitness"


def test_module_registry_default_contracts():
    report = ModuleRegistry(path=None).capability_report()
    module_ids = {m["id"] for m in report["modules"]}
    assert "runtime.kernel" in module_ids
    assert "ollama.local" in module_ids
    assert report["witness"]["witness_type"] == "ModuleCapabilityReportWitness"


def test_self_development_is_candidate_only():
    result = SelfDevelopmentController().plan("Add a module adapter")
    assert "merge" in result["plan"]["requires_external_approval"]
    assert result["plan"]["non_collapse"]["self_patch_is_not_release"] is True
    assert result["witness"]["force"] == "propose"
