# Duotronics

Duotronics is a **witness-runtime and distributed-systems program**. It defines, in layered specifications, how a system can represent, transport, validate, replay, learn from, and govern identity-bearing facts across a federated cluster without collapsing absence, zero, unknown, invalidity, origin, transport encoding, or canonical identity.

This repository is the **specification and corpus authority** for the program. It is not a runtime. The canonical runtime implementation target is currently undecided; see `build_docs/witness_contract/v1.5 - Draft 2/duotronic_canonical_implementation_target_v0_1.md`.

## What the program covers

1. **Witness calculus and runtime trust** — evidence bundles, candidate witnesses, canonical witness facts, lookup memory, recurrent witness state, replay identity, and policy gating. Owned by `duotronic_witness_contract_v10_16.md`.
2. **Representational core** — DPFC: realized magnitudes, family-native numerals, conversion, bridge boundaries, export/import policy. Owned by `duotronic_polygon_family_calculus_v5_15.md`.
3. **Distributed self-governing recurrent network** — node federation over DBP v2 S2 full-duplex transport, canonical resource witnesses, policy-gated task delegation, task-outcome witnesses, and Docker-native node lifecycle. Owned by `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md` and its referenced specs.
4. **Auto-profile learning** — segmentation, relation, normalizer, bridge, and profile candidates that are validated and policy-gated rather than silently adopted.
5. **Witness-gated recurrent cell (WG-RNN)** — governed persistent memory with write/decay/quarantine/promote gates, policy clamps, replay identity, and slot lifecycle.
6. **Governance** — policy shield, evidence purge and privacy deletion, human review and escalation, model diversity adjudication, migration, and retention diagnostics.
7. **Polygon atomic-model research workbook** — a bounded research input (the chapter HTML/ODT exports), informing the polygon family research profile but not defining runtime authority.

## Active corpus

The active source corpus is `build_docs/witness_contract/v1.5 - Draft 2/`.

Top-level entry points:

- `build_docs/witness_contract/v1.5 - Draft 2/duotronic_program_charter_v1_0.md` — program charter and scope.
- `build_docs/witness_contract/v1.5 - Draft 2/README_v1_5_draft_2.md` — release overview.
- `build_docs/witness_contract/v1.5 - Draft 2/v1_5_draft_2_reading_guide.md` — corpus map and reading order by role.
- `build_docs/witness_contract/v1.5 - Draft 2/duotronic_canonical_implementation_target_v0_1.md` — implementation-target decision status (TBD).
- `build_docs/witness_contract/v1.5 - Draft 2/refs/duotronic_source_architecture_overview_v1_7.md` — architecture map.
- `build_docs/witness_contract/v1.5 - Draft 2/refs/duotronic_glossary_v1_0.md` — terminology authority.

Earlier draft folders under `build_docs/witness_contract/` are kept for historical replay. Reviewers and implementers should treat v1.5 Draft 2 as the active corpus unless a later draft supersedes it.

## Repository contents

### Active specification corpus

- `build_docs/witness_contract/v1.5 - Draft 2/` — current active corpus (program charter, witness contract v10.16, DPFC v5.15, distributed cluster addendum, WG-RNN contract, reading guide, canonical-target status, and all referenced specs).
- `build_docs/witness_contract/<earlier drafts>/` — historical drafts kept for replay and migration review.

### Conformance and harness assets

- `harness/` — conformance harness scaffolding.
- `build_docs/witness_contract/v1.5 - Draft 2/refs/duotronic_v1_5_cluster_conformance_fixtures_v1_0.md` — cluster conformance fixtures.

### Research workbook (polygon atomic model)

- `Duotronics - Chapter 1-17.html` and matching `.odt` — foundation: scope, formal objects, state semantics, duotronics mapping, dynamics, observables, bridge tests, validation gates.
- `Duotronics - Chapter 18.html` — catalog pipeline.
- `Duotronics - Chapter 19.html` — catalog expansion protocol.
- `Duotronics - Chapter 20-21.html` — operator and execution workbook.
- `Duotronics - Chapter 22.html`, `Duotronics - Chapter 23.html` — extended workbook material.
- `Duotronics - ai prep instructions.html`, `Duotronic Math - Rough Draft.html` — prior synthesis notes.

These chapter materials are research input only. Where they conflict with the v1.5 Draft 2 corpus, the corpus controls (see `duotronic_program_charter_v1_0.md` section 4).

### Other top-level files

- `Duotronics_Concept_Source_Paper.md` — early concept paper, retained as background.
- `ROADMAP.md` — program roadmap and execution phases.
- `LICENSE` — MIT.

## How to use this repository

1. Read `build_docs/witness_contract/v1.5 - Draft 2/duotronic_program_charter_v1_0.md` and `v1_5_draft_2_reading_guide.md` first.
2. Pick a role (architecture review, implementation, governance, research-profile authoring) and follow the reading order in section 4 of the reading guide.
3. Use `build_docs/witness_contract/v1.5 - Draft 2/refs/duotronic_glossary_v1_0.md` as the terminology authority.
4. For implementation work, also read `duotronic_canonical_implementation_target_v0_1.md` first; treat all prototypes as research prototypes until that decision is recorded.
5. For polygon-track research, read the chapter exports as background, then map your work to a bounded research profile via `refs/duotronic_auto_profile_learning_contract_v1_3.md` and `refs/duotronic_profile_synthesis_registry_v1_2.md`.

## Status

The v1.5 Draft 2 corpus is documentation-complete for its declared research and normative scope. The canonical implementation target has not yet been chosen. Build work that follows this corpus is therefore expected to:

- run as a research prototype until a target is recorded;
- preserve the language- and storage-agnostic posture required by the Witness Contract;
- emit replayable records (`MemoryUpdateRecord`, `MetaDiagnostics`, `TaskOutcomeWitness`, etc.) so that any later target choice does not invalidate prior runs.

## License

MIT License. See `LICENSE`.
