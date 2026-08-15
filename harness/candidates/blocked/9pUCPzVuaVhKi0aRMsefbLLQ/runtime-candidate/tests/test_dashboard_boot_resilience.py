from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_boot_uses_safe_binders():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "function safeBind" in js
    assert 'safeBind("tabs", bindDashboardTabs)' in js
    assert "DOMContentLoaded" in js


def test_dashboard_boot_binds_tabs_before_optional_panels():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    tabs_idx = js.index('safeBind("tabs", bindDashboardTabs)')
    inference_idx = js.index('safeBind("inference"')
    repo_idx = js.index('safeBind("repo operator"')
    assert tabs_idx < inference_idx
    assert tabs_idx < repo_idx


def test_status_and_model_select_are_guarded():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "if (!pill) return" in js
    assert "if (modelSelect)" in js
