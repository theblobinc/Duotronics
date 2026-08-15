from pathlib import Path


def test_dashboard_static_assets_exist():
    root = Path(__file__).resolve().parents[1] / "app" / "duotronic_runtime" / "static"
    assert (root / "index.html").exists()
    assert (root / "styles.css").exists()
    assert (root / "app.js").exists()


def test_dashboard_references_runtime_endpoints():
    app_js = (Path(__file__).resolve().parents[1] / "app" / "duotronic_runtime" / "static" / "app.js").read_text()
    assert "/v1/run" in app_js
    assert "/v1/memory" in app_js
    assert "/v1/evidence/witnesses" in app_js
