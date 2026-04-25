# QCD Spin-Correlation Measurement as a Bounded Duotronic Analogy Profile v1.2

**Status:** Analogy/research profile paper  
**Version:** research-qcd-analogy@v1.2  
**Document kind:** Bounded analogy paper, not physics claim and not normative core  
**Primary purpose:** Extract method-level lessons from the STAR spin-correlation measurement for Duotronic witness retention, decoherence-style diagnostics, and hidden-to-observable transition reasoning without claiming that Duotronics models QCD.

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


## 1. Boundary statement

> **Status tag:** analogy

This paper is an analogy profile. It does not claim that DPFC models quantum chromodynamics, virtual particles, confinement, quark condensates, entanglement, or hadronization. It imports only method-level patterns:

1. hidden correlated source;
2. transition through a complex medium;
3. observable final-state proxy;
4. correlation measurement;
5. baseline comparison;
6. loss of correlation with separation.

## 2. Source-paper method pattern

> **Status tag:** reference

The STAR measurement studies whether spin-correlated strange quark-antiquark pairs can leave a measurable correlation in final-state Lambda hyperon pairs. The paper reports a relative polarization signal and observes that the correlation vanishes for widely separated hyperon pairs. For Duotronics, the useful pattern is not the physics result; it is the measurement design.

## 3. Duotronic analogy map

> **Status tag:** analogy

| QCD measurement concept | Duotronic analogy | Boundary |
|---|---|---|
| virtual correlated pair | hidden source correlation | analogy only |
| hadronization | transformation through runtime/transport/canonicalization | analogy only |
| Lambda pair | observable witness pair | analogy only |
| spin correlation | retained invariant | analogy only |
| angular separation | transformation distance / context separation | analogy only |
| decoherence | retention loss or diagnostic collapse | analogy only |

## 4. Retention diagnostic pattern

> **Status tag:** research

The useful Duotronic abstraction is:

```text
hidden structure
-> transformation
-> observable proxy
-> correlation measurement
-> baseline comparison
-> distance/separation dependence
```

This can inspire retained-correlation diagnostics for family conversion, replay, transport, or witness lookup.

## 5. Baseline requirement

> **Status tag:** normative

Any Duotronic metric inspired by the QCD analogy must include baselines. The source-paper method compares against control channels and simulations; a Duotronic analog must compare against shuffled, malformed, long-separation, random-family, or schema-mismatch baselines.

## 6. Example Duotronic metric

> **Status tag:** reference

```yaml
RetentionMetricSpec:
  metric_id: hidden-to-observable-correlation-retention@v1
  invariant_kind: paired_witness_correlation
  extractor_id: pairwise-witness-extractor@v1
  similarity_id: separation_conditioned_correlation@v1
  transformation: transport_or_canonicalization
  baseline_suite:
    - shuffled_pairs
    - long_separation_pairs
    - unrelated_family_pairs
    - malformed_pairs
  preservation_class: should_preserve
  failure_action: observe_only
```

## 7. What not to import

> **Status tag:** normative

Duotronic documents MUST NOT say:

1. Duotronics proves virtual particles;
2. DPFC is QCD;
3. witness retention is quantum coherence;
4. retention loss is physical decoherence;
5. polygon families are particle multiplets;
6. analogy profiles are implementation authority.

## 8. Useful outcome

> **Status tag:** reference

The QCD profile is useful because it shows a disciplined way to reason from hidden correlation to final-state observable, with controls and separation-dependent loss. That helps Duotronics design better retention diagnostics, but it remains bounded as analogy/research.

## 9. Claim-class assignment

> **Status tag:** normative

All QCD-inspired statements in this profile are C5 analogy or C4 metric-design hypotheses unless a separate external-domain evidence document is created. They are not C2 proofs or C3 runtime requirements.


---

# Appendix Lab - Hidden-to-Observable Benchmark Analogy Integration

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
