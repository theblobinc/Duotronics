from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inference_chat_shows_witness_contract_in_inspector():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "nla_activation_witness_v1" in js
    assert "No inference run yet" in js


def test_inference_chat_css_has_polish_rules():
    css = (ROOT / "app" / "duotronic_runtime" / "static" / "styles.css").read_text()
    assert "Inference tab polish" in css
    assert ".inference-chat-main" in css
    assert ".latest-output .avatar" in css
