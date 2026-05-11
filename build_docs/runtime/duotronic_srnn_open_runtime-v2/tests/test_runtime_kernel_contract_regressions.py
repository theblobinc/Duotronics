from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_kernel_does_not_reference_missing_model_result():
    content = (ROOT / "app" / "duotronic_runtime" / "runtime_kernel.py").read_text()
    assert "model_result" not in content
    assert 'source_model=completion.get("model", {})' in content
    assert "nla_activation_witness_v1" in content
