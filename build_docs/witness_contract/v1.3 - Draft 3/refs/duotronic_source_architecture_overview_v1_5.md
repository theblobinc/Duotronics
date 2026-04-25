# Duotronic Source Architecture Overview v1.5

**Status:** Internal source architecture draft  
**Version:** 1.5-source-overview  
**Document kind:** Reference architecture and reading guide  
**Primary purpose:** Explain the full Duotronic source-spec stack, where DPFC ends, where the Witness Contract begins, and why the corpus separates absence, zero, origin, raw witnesses, canonical identity, transport encoding, and analogies.

> Drafting note. This document follows the one-based Duotronic style for public labels and checklists. External domains may still contain ordinary zero where their standards require it.

---



## v1.3 runtime-profile note

> **Status tag:** reference
> **Related tags:** research

The v1.3 source-corpus draft adds one new optional research profile: **DW-SSM, the Duotronic Witness Selective State-Space Model**. This overview mentions it because the overview is the corpus map. The rest of the corpus should not be treated as selective-state-space documentation unless a document explicitly owns that topic.

The governing boundary is:

```text
raw evidence -> validation -> canonicalization -> policy gate -> selective state update
```

Raw, untrusted witness evidence MUST NOT directly select state-transition matrices, memory-write strength, lookup injection authority, or promotion decisions when a normal-form path exists.

## Revision 1.1 polish note

> **Status tag:** reference

The v1.5 overview keeps the v1.3 architecture map, fixes companion-document status entries, and adds a concise reference to the new DW-SSM research profile.

## Document status tag key

> **Status tag:** reference

Every major section carries exactly one primary status tag. If a section needs a secondary classification, use `Related tags:` on a separate line. Machine parsers should read only the primary `Status tag` value.

| Tag | Meaning |
|---|---|
| `normative` | Binding rule in a specification document. |
| `reference` | Architecture explanation, examples, schemas, or guidance. |
| `research` | Experimental profile or metric. |
| `future` | Planned work not active yet. |
| `analogy` | Outside-field comparison or motivation. |

## 1. What Duotronics is

> **Status tag:** reference

Duotronics is a presence-first witness calculus and runtime contract for representing, transporting, canonicalizing, comparing, replaying, and safely promoting identity-bearing facts without collapsing absence, zero, invalidity, origin, display geometry, transport encoding, or canonical value.

The corpus has two major halves:

1. **DPFC — Duotronic Polygon Family Calculus.** This is the mathematical and representational layer. It defines realized positive magnitudes, family-native numerals, canonical family identity, witness history, export boundaries, and inter-family conversion.
2. **Duotronic Witness Contract.** This is the runtime trust and safety layer. It defines how witness facts are extracted, validated, canonicalized, stored, retrieved, replayed, transported, gated, promoted, degraded, and rejected.

## 2. The problem it solves

> **Status tag:** reference

Many systems overload a single representation, often zero, empty string, null, all-zero row, or default object, to mean several different things. That works until the system must reason about trust, replay, transport, invalidity, derived evidence, and conversion loss.

Duotronics solves this by separating:

1. structural absence;
2. token-free transport absence;
3. ordinary numeric zero;
4. invalid payload;
5. unknown present value;
6. least realized magnitude;
7. origin role;
8. display geometry;
9. canonical identity;
10. exported conventional arithmetic.

## 3. The four major separations

> **Status tag:** normative
> **Related tags:** reference

### 3.1 Absence versus zero

An absent object is not a numeric value. A present numeric zero is not absence. A token-free inactive row is a transport state, not a family numeral.

### 3.2 Raw witness versus canonical identity

A raw witness can carry valuable evidence, but it is not trusted identity. Canonical identity requires schema, normalizer, serializer, family registry, and replay-pinned versions.

### 3.3 Transport encoding versus semantic object

DBP frames, Witness8 rows, and WSB2 rows are transport or implementation profiles. They are not mathematical truth by themselves.

### 3.4 Analogy versus proof

QCD, acoustics, EDO, temperament, and spectral witnesses are useful research/reference profiles. They do not prove DPFC arithmetic or runtime trust rules.

## 4. Source-spec stack

> **Status tag:** reference

```text
Source Architecture
├── DPFC Core Specification
│   ├── core magnitudes
│   ├── scalar line
│   ├── family numerals
│   ├── conversion
│   └── export policies
├── Family and Geometry Registries
│   ├── family declarations
│   ├── normalizer profiles
│   ├── geometry groups/orbits
│   └── witness schemas
├── Witness Contract
│   ├── L1 extraction
│   ├── L2 recurrence
│   ├── L2M lookup
│   ├── L3 controller
│   ├── L4 architecture proposals
│   └── L5 shield
├── Transport Profiles
│   ├── Witness8
│   ├── DBP
│   └── WSB2
├── Diagnostics
│   ├── retention metrics
│   ├── baselines
│   ├── telemetry
│   └── replay identity
└── Research Profiles
    ├── QCD analogy
    ├── acoustic/spectral witnesses
    ├── EDO temperament profiles
    ├── selective witness state-space profile
    └── future physical profiles
```

## 5. Data movement through the system

> **Status tag:** reference

A typical trusted path is:

```text
raw event
-> transport validation
-> semantic decode
-> L1 witness signature
-> registry lookup
-> canonicalization
-> normal-form key
-> policy gate
-> L2M lookup
-> L2 recurrence
-> telemetry/replay
-> possible L3/L4/L5 action
```

A failure at any stage produces an explicit state: rejected, audit-only, degraded, family-bypass, transport-bypass, lookup-bypass, or full-bypass.

## 6. What must never be confused

> **Status tag:** normative
> **Related tags:** reference

1. \(\mu_1\) is not absence.
2. exported zero is not native absence.
3. token-free absence is not numeric zero.
4. raw witness evidence is not canonical identity.
5. transport integrity is not semantic validity.
6. semantic validity is not policy authority.
7. geometry is not arithmetic proof.
8. analogy is not external-domain claim.
9. retention score is not proof without baseline.
10. migration candidate is not promoted schema.

## 7. Minimal conforming implementation

> **Status tag:** reference

A minimal implementation supports:

1. at least one DPFC family;
2. bijective family evaluation;
3. family successor;
4. core magnitude preservation under conversion;
5. canonical storage;
6. Witness8 absence/numeric-zero distinction;
7. DBP or simulated transport-before-semantics;
8. normal-form-before-trust;
9. at least one bypass mode;
10. fixture-driven self-tests.

## 8. Full research implementation

> **Status tag:** future
> **Related tags:** research

A full research implementation adds:

1. multiple families;
2. geometry/orbit reducers;
3. EDO and spectral witness profiles;
4. retention diagnostics;
5. migration and replay harness;
6. policy shield telemetry;
7. schema registry;
8. source-corpus map;
9. threat model;
10. public/internal language guide.

## 9. Source corpus map

> **Status tag:** reference

The corpus map distinguishes documents that already exist from documents that are identified but still need standalone drafts.

| Document | Corpus status | Role |
|---|---|---|
| Source Architecture Overview | existing | reading guide and architecture map |
| DPFC | existing | mathematical and representational core |
| Witness Contract | existing | runtime trust and safety |
| Schema Registry | existing - baseline candidate | versioned identifiers and compatibility matrix |
| Family Registry | existing - baseline candidate | family declarations and geometry registry |
| Normalizer Profiles | existing - baseline candidate | canonicalization declarations and failure codes |
| Transport Profiles | existing - baseline candidate | Witness8, DBP, and WSB2 boundaries |
| Retention Diagnostics | existing - baseline candidate | metrics, baselines, pass rules, and telemetry |
| Migration Guide | existing - baseline candidate | replay, rollback, and promotion discipline |
| Policy Shield Guide | existing - baseline candidate | L5 modes, decision tables, and operator policy |
| Research Profiles | existing - research | EDO, acoustics, QCD analogy, selective witness state-space, GCD-jump recurrences, and future physical profiles |
| Public/Internal Language Guide | future | naming, public claims, and analogy-boundary language |

Status meanings:

1. `existing` means the document is present in the current source corpus.
2. `existing - baseline candidate` means the document exists and is ready for experimental implementation/conformance review, but is not a production-final standard.
3. `existing - research` means the document exists as an opt-in research profile.
4. `draft-needed` means the corpus has identified the role, but the document should be extracted before production use.
5. `future` means the topic is valuable but not active implementation authority.

## 10. Recommended reading order

> **Status tag:** reference

1. Source Architecture Overview;
2. Absence-Zero-Origin Problem;
3. DPFC Core Magnitude Calculus;
4. DPFC Numeral Families;
5. DPFC Inter-Family Conversion;
6. Witness Contract Hard Rules;
7. Witness Lifecycle;
8. Transport Profiles;
9. Conformance Harness;
10. Migration and Replay Guide.

## 11. Final architecture statement

> **Status tag:** reference

Duotronics is not one formula and not one runtime class. It is a source-spec stack. DPFC keeps family identity and arithmetic disciplined. The Witness Contract keeps runtime trust disciplined. Transport profiles keep wire formats subordinate to validation. Retention diagnostics keep research claims measurable. Policy shielding keeps failure controlled.

The guiding architecture rule is:

> Represent precisely, validate before trust, canonicalize before lookup, declare every boundary, and demote anything that cannot pass its tests.

---

# Appendix Lab - Lab Evidence Integration

> **Status tag:** reference

This appendix imports the Duotronic lab lineage through the standalone `duotronic_lab_evidence_registry_v1_1.md`. The lab evidence is used as executable engineering lineage. It is not imported as proof of physics or as lower-layer semantic authority.

```yaml
lab_lineage:
  - lab_id: polygon-catalog-v0
    status: historical_reference
    contribution: finite polygon catalog and label summaries
  - lab_id: polygon-lab-v1
    status: historical_reference
    contribution: glyph rendering and canonical polygon configurations
  - lab_id: polygon-lab-v2
    status: historical_reference
    contribution: projection, selection, and operator-evidence CSVs
  - lab_id: polygon-lab-v3
    status: historical_reference
    contribution: baseline/candidate comparison artifacts and run evidence
  - lab_id: polygon-lab-v4
    status: research_valid
    contribution: benchmark suite, gate reports, red-team variants, toy graph operator, and subprocess JSON adapter
  - lab_id: engine-lab-v5
    status: research_valid
    contribution: LAMMPS/GPAW export adapter, benchmark suite, evidence bundle, parser outputs, and external-engine gate reports
```

```yaml
polygon_lab_v4_summary:
  suite_id: SUITE:poly4-anchors-v4
  suite_version: 4.0.0
  purpose: Live-wrapper benchmark suite with red-team variants.
  benchmark_ids:
    - bench:spectral-anchor-v4
    - bench:propagation-anchor-v4
  case_ids: [case:edge1, case:edge2, case:edge3]
  variants:
    - theta_id: VAR:baseline-v4
      total_cases: 6
      passes: 6
      fails: 0
    - theta_id: VAR:candidate-v4
      total_cases: 6
      passes: 6
      fails: 0
    - theta_id: VAR:redteam-disconnect-v4
      total_cases: 6
      passes: 3
      fails: 3
    - theta_id: VAR:redteam-unstable-v4
      total_cases: 6
      passes: 3
      fails: 3
  imported_as: [retention_baseline, policy_redteam_fixture, meta_shadow_replay_example, family_geometry_diagnostic]
```

```yaml
engine_lab_v5_summary:
  suite_id: SUITE:duotronic-engine-export-v5
  suite_version: 5.0.0
  purpose: External-engine benchmark suite derived from LAMMPS/GPAW exports.
  adapter_id: adapter:engine-export-v5
  adapter_track: wrapped-external
  engines:
    - engine_id: lammps
      engine_family: md
      evidence_files: [lammps_melt.log, lammps_melt_mpi.log]
    - engine_id: gpaw
      engine_family: dft
      evidence_files: [gpaw_h2.json, gpaw_h2.txt, gpaw_h2.log, gpaw_he.json, gpaw_he.txt, gpaw_he.log, gpaw_info.txt]
  benchmark_ids:
    - bench:lammps-melt-serial-vs-mpi
    - bench:lammps-thermo-consistency
    - bench:lammps-mpi-proc-shape
    - bench:lammps-final-energy-alignment
    - bench:gpaw-h2-energy
    - bench:gpaw-he-energy
    - bench:gpaw-h2-rank-consistency
    - bench:gpaw-he-rank-consistency
    - bench:redteam-gpaw-iteration-threshold
    - bench:redteam-lammps-speedup-threshold
  latest_dev4_summary:
    - theta_id: VAR_md_lammps-v5
      total_cases: 5
      passes: 4
      fails: 1
      pass_rate: 0.8
    - theta_id: VAR_dft_gpaw-v5
      total_cases: 5
      passes: 4
      fails: 1
      pass_rate: 0.8
  imported_as: [external_engine_transport_profile, adapter_inventory_schema, evidence_bundle_schema, policy_gate_fixture, migration_worked_example, meta_runtime_shadow_replay_case]
```

## Local rule

> **Status tag:** normative

This document may consume lab-derived schemas, evidence bundles, adapter reports, and gate reports only through versioned registry entries and declared migration/replay compatibility. A lab artifact MUST NOT become authoritative merely because the code ran or the output file exists.


---

## 15. Selective witness state-space architecture

> **Status tag:** research
> **Related tags:** reference

The v1.3 selective-state-space draft adds a runtime/research profile named **DW-SSM: Duotronic Witness Selective State-Space Model**. DW-SSM belongs to the Witness/Runtime side of the corpus, not the DPFC arithmetic core.

The added data path is:

```text
raw event
-> transport validation
-> semantic decode
-> L1 witness signature
-> registry lookup
-> canonicalization
-> normal-form key
-> policy gate
-> selective state-space update
-> L2/L2M recurrence and telemetry
```

The central rule is that canonical witness context, normalization diagnostics, retention diagnostics, and policy mode may select the recurrent transition, but raw untrusted evidence may not.

A compact form is:

\[
s_t=A(k_t^{nf},d_t^{norm},p_t,r_t)s_{t-1}+B(k_t^{nf},d_t^{norm},p_t,r_t)u_t.
\]

This profile creates a bridge from the source specifications to practical RNN/RWKV/Mamba-style implementations while preserving the existing Duotronic separations: DPFC defines values; Witness defines trust; Transport defines boundaries; Policy controls authority; Retention measures survival of declared invariants.


---

## 16. GCD-jump recurrence profile in the corpus

> **Status tag:** research
> **Related tags:** reference

The v1.3 Draft 3 corpus adds **GCD-Jump Recurrences as Sparse Duotronic Witness Gates v1.0** as a bounded research profile.

The profile belongs beside DW-SSM in the Witness/Runtime research area. Its role is not to redefine DPFC and not to advertise faster prime generation. Its role is to provide a compact recurrence pattern for:

1. cheap event detection;
2. sparse update scheduling;
3. L2/L2M witness-gate examples;
4. DW-SSM auxiliary event embeddings;
5. conformance fixtures for trivial versus nontrivial recurrence events.

The corpus-level rule is:

```text
GCD jump -> candidate event -> validation/canonicalization/policy -> optional runtime use
```

The profile is intentionally referenced only in the owning documents: Source Architecture, Witness Contract, DPFC boundary language, and the standalone GCD-jump profile.
