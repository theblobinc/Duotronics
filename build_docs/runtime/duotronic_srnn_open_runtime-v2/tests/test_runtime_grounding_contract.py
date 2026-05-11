from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_kernel_records_response_grounding():
    content = (ROOT / "app" / "duotronic_runtime" / "runtime_kernel.py").read_text()
    assert "ground_response" in content
    assert "raw_response_text" in content
    assert "response_grounding" in content
