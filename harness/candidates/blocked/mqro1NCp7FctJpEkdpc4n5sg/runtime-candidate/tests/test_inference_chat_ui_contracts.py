from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inference_chat_js_exists():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "bindInferenceChatUi" in js
    assert "appendChatMessage" in js
    assert "xavi-chat-log" in js
    assert "inference-chat-shell" in js


def test_inference_chat_css_exists():
    css = (ROOT / "app" / "duotronic_runtime" / "static" / "styles.css").read_text()
    assert ".inference-chat-shell" in css
    assert ".inference-chat-main" in css
    assert ".chat-message.user" in css
    assert ".inference-composer" in css


def test_inference_runtime_controls_remain_available():
    html = (ROOT / "app" / "duotronic_runtime" / "static" / "index.html").read_text()
    for token in ["api-key", "model", "action", "steps", "quality", "run-btn", "prompt", "model-output", "policy-output"]:
        assert token in html
