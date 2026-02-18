# Duotronics & Polygon Atomic Model Workbook

## Overview
This repository is a **specification workbook** for Duotronics and the Polygon Atomic Model, not a conventional application framework.

The workbook defines a geometry-first, test-driven research architecture where:
- polygon configurations act as the primary representation,
- labels are derived through explicit mapping rules (including offset policies),
- operators and solvers are modularized and versioned,
- variants are evaluated through reproducible validation gates.

At a high level, the project aims to provide an AI-executable path from:
**formal definitions → catalog generation → operator construction → solver runs → witness-based validation**.

## What Duotronics means in this repo
Duotronics is described as a polygon-native counting/labeling system with a strict semantic distinction between:
- **empty** (no entity),
- **unknown** (state not measured/defined),
- **zero** (known value equal to 0).

A recurring working convention is a center-dot/offset mapping rule (often “subtract one” when translating raw geometric sums to display labels), with explicit policy/version tracking so assumptions do not silently drift.

## Repository contents
- `ROADMAP.md` — Program roadmap for taking Duotronics from formal semantics to binary/quantum execution and eventual hardware co-design.
- `Duotronics - Chapter 1-17.html` — Core workbook foundations: scope, formal objects, state semantics, duotronics mapping, dynamics, observables, bridge tests, implementation mapping, validation gates, theory variants, and glossary.
- `Duotronics - Chapter 18.html` — End-to-end **catalog track instantiation**: family registry, canonicalization, offset survey, degeneracy policy, reproducible JSON/CSV artifacts.
- `Duotronics - Chapter 19.html` — **Catalog expansion protocol**: versioning discipline, drift/threat model, semantic vs display identity, migration-safe catalog growth.
- `Duotronics - Chapter 20-21.html` — **Operator and execution workbook**: reusable operator templates, solver recipes (`hex2d`, `coulomb3d`), benchmark suites, witness system, scorecards, canonicalization policy, and epoch/version migration workflow.
- `Duotronics - ai prep instructions.html` — AI-oriented preparation notes and draft synthesis of the project model, implementation direction, and formalization priorities.
- Matching `.odt` files provide editable source documents for the chapter exports.

## Workbook structure (quick map)
### Chapters 1–17 (foundation)
Focus areas include:
- project scope and non-goals,
- formal schema for lattice/polygon/state objects,
- unknown-aware semantics and invariants,
- duotronics mapping/equivalence conventions,
- dynamics and measurement model,
- variant management and validation gates.

### Chapter 18 (catalog pipeline)
Defines a repeatable catalog workflow producing artifacts such as:
- `catalog_entries.jsonl`,
- `z_index.json`,
- `degeneracy_report.json`,
- `offset_survey.json`,
- `catalog_run_record.json`.

### Chapter 19 (safe expansion)
Adds protocol-level controls so catalog changes are **published artifacts**, not in-place edits:
- catalog IDs and schema versioning,
- explicit policy drift categories,
- semantic label identity vs human display labels,
- migration and compatibility discipline.

### Chapters 20–21 (operators, witnesses, and governance)
Defines how to operationalize and validate theory variants:
- graph/lattice operator construction contracts,
- modular solver recipes for hex-lattice and soft-Coulomb tracks,
- benchmark and witness specifications,
- scorecards/ranking,
- canonicalization and catalog epoch governance.

## How to use this repository
1. Read `Duotronics - Chapter 1-17.html` for core semantics and object contracts.
2. Use `Duotronics - Chapter 18.html` to generate and audit catalog artifacts.
3. Apply `Duotronics - Chapter 19.html` before introducing catalog or policy changes.
4. Implement/compare operator variants using `Duotronics - Chapter 20-21.html`.
5. Use witness/scorecard/epoch sections to keep results reproducible and comparable over time.

## Current status
This repository currently serves as a **documentation/specification backbone** for ongoing implementation work. The chapters repeatedly emphasize reproducibility, explicit policy versioning, and gate-based falsification before broad theoretical claims.

## License
MIT License. See `LICENSE`.
