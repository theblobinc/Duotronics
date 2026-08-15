python -m compileall app
$env:PYTHONPATH="app"
python -m pytest -q tests
