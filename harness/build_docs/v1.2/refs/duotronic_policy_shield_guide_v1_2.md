# Duotronic Policy Shield Guide v1.2

**Status:** Source-spec baseline candidate  
**Version:** policy-shield@v1.2  
**Document kind:** Normative L5 policy guide plus reference decision tables  
**Primary purpose:** Define how L5 shields runtime operation by enforcing feasibility, bypass modes, rollback authority, migration gates, and promotion boundaries.

> Drafting note. This document follows the one-based Duotronic style for public headings, claim labels, and checklist labels. External domains, wire formats, host languages, and physical sciences may still contain ordinary zero where their own standards require it. The Duotronic rule is not that zero is forbidden; the rule is that absence, origin, invalidity, numeric zero, raw witness evidence, canonical identity, and transport encoding must not be silently collapsed.

---

## Document status tag key

> **Status tag:** reference

Every major section carries one primary status tag. If a section needs secondary classification, use `Related tags:` on a separate line.

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for the active source document. | Conforming implementations must follow it. |
| `reference` | Examples, schemas, fixtures, algorithms, explanations, and implementation aids. | Useful for implementation; not a new semantic rule unless cited by a normative section. |
| `research` | Experimental metric, profile, analogy, or benchmark candidate. | Must remain opt-in until promoted by evidence. |
| `future` | Useful planned work not active yet. | Must not be treated as live authority. |
| `analogy` | Outside-domain comparison or inspiration. | Must not be treated as proof or runtime authority. |


## 1. Scope

> **Status tag:** normative

The Policy Shield is the L5 layer. It decides which paths are allowed, degraded, bypassed, rolled back, or blocked. It is not an arithmetic layer and not a normalizer. It is a runtime safety authority.

## 2. L5 hard rules

> **Status tag:** normative

L5 MUST enforce:

1. normal-form-before-trust;
2. transport-before-semantics;
3. no silent family reinterpretation;
4. no schema promotion without migration;
5. bypass as valid behavior;
6. failed canonicalization as a first-class state;
7. replay mismatch blocks promotion;
8. retention metrics require baselines before authority.

## 3. Runtime modes

> **Status tag:** normative

| Mode | Meaning | Lookup | Recurrence | Promotion |
|---|---|---|---|---|
| `normal` | all checks passing | allowed | allowed | allowed by policy |
| `degraded` | warning state | limited | allowed conservative | blocked or limited |
| `family_bypass` | family-sensitive path disabled | generic only | allowed | blocked |
| `transport_bypass` | failed transport path disabled | blocked for frame | no semantic update | blocked |
| `lookup_bypass` | lookup unavailable/unsafe | disabled | allowed without lookup | blocked if dependent |
| `full_bypass` | unsafe semantic path | blocked | blocked or minimal | blocked |

## 4. Decision matrix

> **Status tag:** reference

| Condition | Default mode | Required action |
|---|---|---|
| transport integrity failed | transport_bypass | reject semantic decode |
| absence-zero collision | full_bypass | reject decoder/profile |
| family registry missing | family_bypass | generic handling only |
| normalizer timeout | degraded | bypass affected path |
| replay identity mismatch | full_bypass | block promotion and rollback |
| retention metric lacks baseline | degraded | keep metric observe-only |
| migration plan missing | degraded | block L4 promotion |
| lookup p99 over ceiling | lookup_bypass | disable lookup enrichment |

## 5. Policy profile schema

> **Status tag:** normative

```yaml
policy_profile:
  policy_id: string
  policy_version: string
  status: active | experimental | deprecated
  allowed_modes: [normal, degraded, family_bypass, transport_bypass, lookup_bypass, full_bypass]
  default_mode: normal
  thresholds:
    canonicalization_failure_rate: number
    lookup_timeout_rate: number
    replay_mismatch_rate: number
    transport_reject_rate: number
  actions:
    on_transport_integrity_failed: transport_bypass
    on_absence_zero_collision: full_bypass
    on_replay_mismatch: full_bypass
  rollback:
    rollback_allowed: true
    approval_required: true
```

## 6. Promotion gates

> **Status tag:** normative

L5 must block promotion unless:

1. migration plan exists;
2. replay traces pass;
3. canonical identity is stable;
4. must-preserve invariants hold;
5. failure behavior is defined;
6. rollback plan exists;
7. policy approval is recorded.

## 7. Bypass philosophy

> **Status tag:** reference

Bypass is not failure to implement. Bypass is the mechanism that prevents uncertain, malformed, ambiguous, or untrusted evidence from entering stronger layers. A well-designed Duotronic runtime should degrade cleanly rather than improvise authority.

## 8. Operator record

> **Status tag:** reference

```yaml
policy_event:
  event_id: string
  time: string
  previous_mode: normal
  new_mode: family_bypass
  trigger_failure_code: normalizer_error
  affected_family: refl3
  lookup_allowed: generic_only
  promotion_allowed: false
  rollback_candidate: null
  operator_ack_required: true
```

## 9. Conformance checklist

> **Status tag:** normative

A policy shield implementation must:

1. implement all required modes;
2. treat failed canonicalization as a state;
3. block failed transport semantics;
4. block migration without replay;
5. keep diagnostic metrics non-authoritative unless promoted;
6. emit policy events;
7. support rollback.


---

# Appendix Lab - Red-Team Gate Evidence

> **Status tag:** reference

```yaml
code_derived_objects:
  polygon_lab_v4:
    dataclasses: [PolygonFamilySpec, PolygonConfig, CanonicalRecord, VariantFamily, ThetaSpec, RunSpec, BenchmarkSpec, BenchmarkSuiteSpec, GateReport, BenchmarkResult]
    functions: [canonical_json, sha256_id, canonicalize, orbit_of, enumerate_canonical_catalog, build_operator_adjacency, engine_compute, evaluate_gates, build_comparison_artifact]
    adapters: [InProcessToyAdapter, SubprocessJSONAdapter]
  engine_lab_v5:
    dataclasses: [BenchmarkSpec, GateReport, BenchmarkSuiteSpec, ThetaSpec, VariantFamily, RunSpec, EngineExportAdapter]
    parsers: [parse_lammps_log, parse_gpaw_info, parse_gpaw_json, parse_gpaw_log, parse_gpaw_txt]
    functions: [file_digest, evaluate_gates_v5, benchmark_specs_v5, build_variant_family, build_thetas, source_artifacts_for_benchmark, build_run_spec, validate_artifact_schema, run_suite, compare_baseline]
```

```yaml
lab_schema_imports:
  - schema_id: duotronic/variant-family@v4
    source_lab: polygon-lab-v4
    status: historical_reference
    identity_affecting: true
    migration_before_use: true
  - schema_id: duotronic/theta@v4
    source_lab: polygon-lab-v4
    status: historical_reference
    identity_affecting: true
    migration_before_use: true
  - schema_id: duotronic/run-spec@v4
    source_lab: polygon-lab-v4
    status: historical_reference
    identity_affecting: true
    migration_before_use: true
  - schema_id: duotronic/benchmark-suite@v4
    source_lab: polygon-lab-v4
    status: research_valid
    identity_affecting: true
    migration_before_use: true
  - schema_id: duotronic/gate-report-bundle@v4
    source_lab: polygon-lab-v4
    status: research_valid
    identity_affecting: true
    migration_before_use: true
  - schema_id: duotronic/adapter-inventory@v5
    source_lab: engine-lab-v5
    status: research_valid
    identity_affecting: true
    promotion_status: adapter_profile_candidate
  - schema_id: duotronic/evidence-bundle@v5
    source_lab: engine-lab-v5
    status: research_valid
    identity_affecting: true
    promotion_status: replay_evidence_candidate
  - schema_id: duotronic/benchmark-suite@v5
    source_lab: engine-lab-v5
    status: research_valid
    identity_affecting: true
    promotion_status: retention_diagnostics_candidate
  - schema_id: duotronic/gate-report-bundle@v5
    source_lab: engine-lab-v5
    status: research_valid
    identity_affecting: true
    promotion_status: policy_fixture_candidate
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

## Local boundary

> **Status tag:** normative

Lab-derived evidence may inform this document only through versioned registry entries, migration/replay compatibility, policy gates, and conformance fixtures. It does not become proof of physics or lower-layer semantic authority.
