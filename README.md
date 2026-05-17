# Duotronics

Duotronics is a program repository for witness-bearing computation, recurrent cognition, formal evidence, conformance testing, and reference runtime work.

This repository is not only the newest witness-contract draft. It contains:

- a root program roadmap,
- historical and active specification corpora,
- a conformance harness for DPFC and Witness Contract behavior,
- a standalone meta-runtime package used by the harness,
- a Podman-first SRNN/WG-RNN runtime host,
- source/workbook material for the Duotronics theory track,
- release, governance, validation, security, and implementation-planning documents.

The newest witness-contract package is important, but it should be treated as one active package inside the larger Duotronics project.

## Repository status

Current high-level state:

- **Root project license:** MIT. See `LICENSE`.
- **Root README:** this file is intended to be placed at repository root.
- **Program roadmap:** `ROADMAP.md`.
- **Latest witness-contract package:** `build_docs/witness_contract/v1.6 - Draft 5.2.2/`.
- **Latest packaged SRNN runtime scaffold:** `build_docs/runtime/duotronic_srnn_open_runtime-v3/`.
- **Conformance harness:** `harness/bin/`.
- **Harness meta-runtime package:** `harness/runtime/`.
- **Long-horizon workbook/theory material:** root workbook HTML and older `build_docs/` research documents.

Many artifacts are draft, review-candidate, or scaffold-level. Do not treat every package as production-certified merely because it is present in the repository.

## Start here

For project orientation:

```text
ROADMAP.md
LICENSE
harness/bin/README.md
build_docs/runtime/duotronic_srnn_open_runtime-v3/README.md
build_docs/witness_contract/v1.6 - Draft 5.2.2/START_HERE.md
build_docs/witness_contract/v1.6 - Draft 5.2.2/README.md
build_docs/witness_contract/v1.6 - Draft 5.2.2/CORPUS_INDEX_v1_6_draft_5_2_2.md
```

For an implementation-oriented pass:

```text
harness/bin/README.md
harness/bin/pyproject.toml
harness/runtime/pyproject.toml
build_docs/runtime/duotronic_srnn_open_runtime-v3/README.md
build_docs/runtime/duotronic_srnn_open_runtime-v3/compose.yaml
build_docs/witness_contract/v1.6 - Draft 5.2.2/executable/validators/validate_draft5_2_2_corpus.py
```

For governance and release readiness:

```text
ROADMAP.md
build_docs/witness_contract/v1.6 - Draft 5.2.2/PACKAGE_METADATA_v1_6_draft_5_2_2.json
build_docs/witness_contract/v1.6 - Draft 5.2.2/refs/manifest/MANIFEST_v1_6_draft_5_2_2_complete.md
build_docs/runtime/duotronic_srnn_open_runtime-v3/docs/OPEN_SOURCE_NOTES.md
```

## Repository map

```text
.
├── LICENSE
├── ROADMAP.md
├── Duotronics - Chapter 1-17.html
├── build_docs/
│   ├── SRNN_Cognition_Architecture_Part_II.md
│   ├── old/
│   ├── runtime/
│   │   ├── duotronic_srnn_open_runtime-v2/
│   │   └── duotronic_srnn_open_runtime-v3/
│   └── witness_contract/
│       ├── v1.5 - Draft 1/
│       ├── v1.5 - Draft 2/
│       ├── v1.6 - Draft 1/
│       ├── v1.6 - Draft 2/
│       ├── v1.6 - Draft 3/
│       ├── v1.6 - Draft 4/
│       ├── v1.6 - Draft 5/
│       ├── v1.6 - Draft 5.1/
│       ├── v1.6 - Draft 5.2/
│       ├── v1.6 - Draft 5.2.1/
│       └── v1.6 - Draft 5.2.2/
└── harness/
    ├── conformance_harness-buildv1.md
    ├── bin/
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── conformance/
    │   ├── duotronic_ref/
    │   ├── harness_lib/
    │   ├── fixtures/
    │   ├── golden_traces/
    │   ├── meta_fixtures/
    │   ├── meta_golden_traces/
    │   ├── ci/
    │   └── tools/
    ├── runtime/
    └── build_docs/
```

The exact tree may evolve; use Git history and package manifests for authoritative file inventories.

## Major components

### 1. Program roadmap

`ROADMAP.md` tracks the Duotronics program as a whole: witness runtime, distributed-systems specification stack, conformance harness, WG-RNN research prototype, distributed cluster prototype, canonical implementation-target decision, production runtime, and long-horizon research.

Use the roadmap before assuming which package is canonical.

### 2. Conformance harness

Path:

```text
harness/bin/
```

The conformance harness is the executable test suite for DPFC and Witness Contract behavior. It includes a reference implementation, fixture loaders, golden traces, negative/fuzz tests, policy tests, migration/replay tests, and CI acceptance scripts.

Quick start:

```bash
cd harness/bin
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
pytest -m normative --strict-markers --schema-version v1.2
pytest --schema-version v1.2
bash ci/acceptance.sh
```

External implementations can be tested through:

```bash
DUOTRONIC_IMPL=my_package.duotronic_api pytest -m normative --schema-version v1.2
```

or:

```bash
pytest -m normative --impl=my_package.duotronic_api --schema-version v1.2
```

Meta-runtime tests use `DUOTRONIC_META_IMPL` or `--meta-impl`.

### 3. Harness meta-runtime

Path:

```text
harness/runtime/
```

This is a standalone SRNN-style meta-runtime reference package used by the harness.

The Python package metadata identifies it as:

```text
name: harness-meta-runtime
version: 0.2.0
purpose: standalone SRNN-style meta runtime reference package for meta-runtime-contract@v0.2
```

Typical development flow:

```bash
cd harness/runtime
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

### 4. SRNN runtime host

Path:

```text
build_docs/runtime/duotronic_srnn_open_runtime-v3/
```

This is a Podman-first runtime scaffold for Duotronic/SRNN corpora, WG-RNN cognition, model providers, formal truth observers, MCP tools, and gated self-development.

It includes:

- Corpus ABI loading,
- PostgreSQL witness/evidence persistence,
- Evidence Kernel and Non-Collapse Engine concepts,
- WG-RNN memory updates,
- Natural Language Activation witness support,
- FastAPI control plane,
- static browser UI,
- MCP stdio server,
- model gateway support for local echo, Ollama, and llama.cpp,
- module registry support for formal/model/media/UI components,
- Lean and TLA+ observer wrappers,
- compose profiles for core, models, vector, formal, media, UI, and MCP.

Quick start:

```bash
cd build_docs/runtime/duotronic_srnn_open_runtime-v3
cp .env.example .env
podman compose --env-file .env up --build postgres redis minio runtime
```

Useful endpoints after startup:

```text
UI:          http://127.0.0.1:8080
Health:      http://127.0.0.1:8080/health
OpenAPI UI:  http://127.0.0.1:8080/docs
```

Run tests:

```bash
python -m pytest -q
```

The package’s own notes describe this runtime as a scaffold, not a blanket production certification. Optional profiles require the relevant images, models, GPU drivers, and host resources.

### 5. Witness-contract corpus

Latest active package:

```text
build_docs/witness_contract/v1.6 - Draft 5.2.2/
```

Draft 5.2.2 is a completion-candidate witness-contract corpus with:

- formal evidence-language objects,
- non-collapse state and transition rules,
- SQL persistence,
- OpenAPI runtime surface,
- TLA+ state-machine models,
- Lean/Lake proof authority,
- `check_proof` syscall support,
- theorem-promotion gates,
- proof witness schemas,
- package inventory and hash-closure manifests.

Important entry points:

```text
START_HERE.md
README.md
CORPUS_INDEX_v1_6_draft_5_2_2.md
PACKAGE_METADATA_v1_6_draft_5_2_2.json
refs/manifest/MANIFEST_v1_6_draft_5_2_2_complete.md
```

Validation:

```bash
cd "build_docs/witness_contract/v1.6 - Draft 5.2.2"
python executable/validators/validate_draft5_2_2_corpus.py
```

Formal checks:

```bash
python executable/formal/run_lean_build.py --mode advisory --json
python executable/formal/run_tla_model_check.py --mode advisory
```

Strict release/freeze checks require real toolchains:

```bash
lake build
python executable/formal/run_tla_model_check.py --mode strict
```

Draft 5.2.2 is **not frozen** unless the strict Lean/Lake and strict TLA/TLC paths have passed in the intended environment.

### 6. Historical witness-contract drafts

The `build_docs/witness_contract/` tree contains older v1.5 and v1.6 draft packages, review notes, release notes, manifests, readiness reports, migration notes, and retained implementation guidance.

These are valuable for history and design rationale, but the latest draft package should not be confused with the entire repository.

When reading historical drafts, prefer package metadata and manifests over filename guesses.

### 7. SRNN cognition and research documents

Examples:

```text
build_docs/SRNN_Cognition_Architecture_Part_II.md
Duotronics - Chapter 1-17.html
build_docs/old/
```

These materials document the broader research and theory track, including SRNN cognition, compression/external-memory planes, workbook navigation, formal objects, state semantics, validation gates, theory variants, and open questions.

Treat these as design/theory references unless a current package or roadmap explicitly promotes them into the active implementation spine.

## Validation commands by component

### Harness

```bash
cd harness/bin
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
pytest -m normative --strict-markers --schema-version v1.2
pytest --schema-version v1.2
bash ci/acceptance.sh
```

### Harness meta-runtime

```bash
cd harness/runtime
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

### Runtime host

```bash
cd build_docs/runtime/duotronic_srnn_open_runtime-v3
python -m compileall app
PYTHONPATH=app python -m pytest -q tests
podman compose --env-file .env up --build postgres runtime
```

### Witness contract v1.6 Draft 5.2.2

```bash
cd "build_docs/witness_contract/v1.6 - Draft 5.2.2"
python executable/validators/validate_draft5_2_2_corpus.py
python executable/formal/run_lean_build.py --mode advisory --json
python executable/formal/run_tla_model_check.py --mode advisory
```

Strict formal checks:

```bash
lake build
python executable/formal/run_tla_model_check.py --mode strict
```

## Release and freeze discipline

Do not infer release readiness from the presence of generated artifacts.

Before treating a package as releasable:

1. Read its `START_HERE.md`, `README.md`, metadata, and manifest.
2. Run package validators.
3. Run harness acceptance tests where applicable.
4. Run strict formal toolchains where required.
5. Check open-source notes for secrets, demo credentials, optional services, and license readiness.
6. Confirm the root roadmap does not mark the relevant target as pending, deferred, or not frozen.

## Licensing

The repository root is MIT licensed under `LICENSE`.

Some corpus packages include draft license notices that say the repository-level license should control unless replaced by a formal corpus-specific license. Those package-level notices are placeholders and should not be treated as final legal review.

Before public release, review whether the project wants a split license policy, for example:

- specification prose under a documentation license,
- reference implementation code under MIT or another selected software license,
- fixtures and schemas under a permissive reuse license.

## Security and publication checklist

Before publishing runtime packages or public releases:

- replace demo passwords and placeholder credentials,
- confirm no real hosts, tokens, private SSH paths, or customer data are committed,
- run package tests,
- test Podman Compose on target platforms,
- decide which optional services are officially supported,
- document required GPU/model/toolchain dependencies,
- verify strict formal checks where release gates require them.

## Contributing

Keep contributions scoped to the relevant layer:

- harness changes should include fixture or test updates;
- runtime changes should include unit tests and compose/config notes;
- witness-contract changes should update schemas, fixtures, manifests, validation summaries, and release notes;
- roadmap changes that re-order phases or move items between active phases and long-horizon research should update the roadmap and the corresponding corpus review notes.

## Known caveats

- The repo contains multiple historical drafts and retained artifacts; not every file is current.
- The newest witness-contract package is not the whole project.
- Some packages are generated or bundled corpora with their own manifests.
- Strict Lean/Lake and TLA/TLC checks depend on local toolchain availability.
- Runtime optional profiles depend on images, models, GPUs, and host resources.
- License placeholders inside draft packages should be reviewed before public release.
