from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inference_shell_does_not_force_display_when_inactive():
    css = (ROOT / "app" / "duotronic_runtime" / "static" / "styles.css").read_text()

    shell_block_start = css.index(".inference-chat-shell {")
    shell_block_end = css.index("}", shell_block_start)
    shell_block = css[shell_block_start:shell_block_end]

    assert "display:" not in shell_block
    assert ".inference-chat-shell.active-tab-panel" in css
    assert "display: grid" in css[css.index(".inference-chat-shell.active-tab-panel"):]
