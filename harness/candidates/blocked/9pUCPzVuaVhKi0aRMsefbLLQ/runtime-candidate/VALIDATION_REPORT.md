# Validation Report

Generated during packaging in the ChatGPT container.

## Checks run

```text
python -m py_compile app/duotronic_runtime/*.py
OK
```

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
........                                                                 [100%]
8 passed in 0.35s
```

The two test files were also run independently with the default plugin set:

```text
python -m pytest tests/test_runtime_kernel_contracts.py -q -s
.....
5 passed in 2.20s

python -m pytest tests/test_wgrnn_nla_policy.py -q -s
...
3 passed in 0.77s
```

## Secret scan

Searched packaged tree for sensitive values observed in the supplied agent prompt and found no matches.

## Known limits

- Optional services are declared through Podman profiles but require host images/resources.
- TLA+ image builds from `tla2tools.jar`; pin or pre-stage for locked-down/offline environments.
- Lean/TLA checks report `tool_unavailable` unless those binaries or formal profile containers are available.
- Self-development is intentionally candidate-only; merge/deploy require external approval witnesses.
