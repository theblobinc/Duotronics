from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inference_css_is_viewport_bounded():
    css = (ROOT / "app" / "duotronic_runtime" / "static" / "styles.css").read_text()
    assert "Compact inference viewport v2 - UI only" in css
    assert "height: calc(100vh - 12.25rem)" in css
    assert ".inference-chat-sidebar" in css
    assert ".inference-chat-inspector" in css
