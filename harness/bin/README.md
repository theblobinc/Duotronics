# Duotronic Conformance Harness

Self-contained verifier for **DPFC v5.6** and **Witness Contract v10.6** (plus the
seven extracted source registries).

The harness ships its own reference implementation (`duotronic_ref/`), so the
suite is green out of the box. External implementations plug in via the
`DUOTRONIC_IMPL` env var or `--impl` CLI flag (default `duotronic_ref.api`).
The standalone meta runtime is verified in parallel through `run_meta_operation`
via `DUOTRONIC_META_IMPL` or `--meta-impl` (default `runtime_ref.api`).

## Quick start

```sh
cd harness/bin
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
pytest -m normative --strict-markers     # merge gate
pytest                                    # full default suite
bash ci/acceptance.sh                     # full CI gate
```

## Layout

```
duotronic_ref/    reference implementation (DPFC App H + Witness App I/K + registries)
harness_lib/      loader, dispatch, hashes, fuzz strategies, policy driver, trace runner
fixtures/         versioned YAML+JSON twin fixture packs (verbatim from specs)
golden_traces/    end-to-end YAML traces (Witness Contract App U et al.)
meta_fixtures/    standalone meta-runtime fixture packs driven through run_meta_operation
meta_golden_traces/ replayable meta-runtime golden traces
conformance/      pytest suites mirroring DPFC App T tree
ci/               acceptance scripts and GitHub workflow
tools/            extract_fixtures.py, run_self_test.py
```

## Markers

| Marker      | Meaning                                                          |
|-------------|------------------------------------------------------------------|
| `normative` | required for the merge gate (DPFC App T, Witness App S, regs)    |
| `research`  | research-profile tests (acoustics, EDO, QCD analogy)             |
| `fuzz`      | hypothesis-based fuzz / negative tests (App S §S.2)              |
| `golden`    | end-to-end golden trace replay                                    |
| `migration` | migration-plan / dual-read tests                                 |
| `replay`    | replay-identity / version-pin tests                              |
| `policy`    | L5 policy-shield decision matrix                                  |
| `meta_runtime` | standalone meta-runtime conformance slice                     |
| `slow`      | long-running, excluded from default suite                         |

## Plugging in an external implementation

```sh
DUOTRONIC_IMPL=my_package.duotronic_api pytest -m normative
# or
pytest -m normative --impl=my_package.duotronic_api
```

The module must expose `run_operation(op_name: str, given: dict) -> dict`.

For the meta runtime seam:

```sh
DUOTRONIC_META_IMPL=my_package.meta_api pytest conformance/test_meta_fixture_runner.py -m "meta_runtime and normative"
# or
pytest conformance/test_meta_fixture_runner.py --meta-impl=my_package.meta_api -m "meta_runtime and normative"
```

The module must expose `run_meta_operation(op_name: str, given: dict) -> dict`.

## Re-derive fixtures from the spec markdown

```sh
python tools/extract_fixtures.py --check    # CI mode: fail on drift
python tools/extract_fixtures.py            # rewrite JSON twins from YAML
```

## Reference self-tests

```sh
python tools/run_self_test.py
```
