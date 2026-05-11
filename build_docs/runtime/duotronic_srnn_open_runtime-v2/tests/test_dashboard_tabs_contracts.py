from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_has_tabs():
    html = (ROOT / "app" / "duotronic_runtime" / "static" / "index.html").read_text()
    assert "runtime-tabs" in html
    assert 'data-tab-target="overview"' in html
    assert 'data-tab-target="operator"' in html
    assert 'data-tab-panel="operator"' in html


def test_dashboard_js_binds_tabs():
    js = (ROOT / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "bindDashboardTabs" in js
    assert "showTab" in js
    assert "xavi_runtime_active_tab" in js


def test_dashboard_css_hides_inactive_tab_panels():
    css = (ROOT / "app" / "duotronic_runtime" / "static" / "styles.css").read_text()
    assert "[data-tab-panel]" in css
    assert "active-tab-panel" in css
    assert ".runtime-tabs" in css
