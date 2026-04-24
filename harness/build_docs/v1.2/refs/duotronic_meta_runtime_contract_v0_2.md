# Duotronic Meta Runtime Contract v0.2

**Status:** Research specification draft  
**Version:** meta-runtime-contract@v0.2  
**Document kind:** Normative meta-runtime contract plus lab-derived fixtures  
**Primary purpose:** Define how L3, L4, L5, objective bundles, policy snapshots, shadow replay, meta-object assertions, and lab-derived evidence operate over canonical lower-layer facts without redefining lower-layer semantics.

---

## 1. Executive summary

> **Status tag:** reference

The meta runtime has higher-order control authority, not higher semantic authority. It may tune bounded controls, compare candidates, run shadow replay, veto unsafe changes, record decision evidence, and evaluate lab-derived adapters. It may not redefine DPFC arithmetic, Witness canonicalization, transport validation, normalizer output, or lower-layer canonical identity.

## 2. Hard rules

> **Status tag:** normative

1. Replay identity freshness is required.
2. Objective bundle freshness is required.
3. L5 veto dominates objective improvement.
4. L4 semantic changes require migration and rollback.
5. Meta-object normalization must be deterministic.
6. Metrics require policy authority before they influence decisions.
7. Lab-derived evidence is research-valid until promoted.
8. A lab artifact never overwrites a lower-layer canonical object.

## 3. Lab-derived fixtures

> **Status tag:** reference

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

```yaml
meta_runtime_lab_fixtures:
  - fixture_id: META-LAB-V4-FIXTURE-1-CANDIDATE-SHADOW-PASS
    given: {baseline_variant: VAR:baseline-v4, candidate_variant: VAR:candidate-v4, total_cases: 6, baseline_fails: 0, candidate_fails: 0}
    operation: shadow_replay_compare
    expected: {decision: candidate_research_valid, promotion_allowed_without_policy: false}
  - fixture_id: META-LAB-V4-FIXTURE-2-REDTEAM-VETO
    given: {variant: VAR:redteam-unstable-v4, total_cases: 6, fails: 3}
    operation: l5_review
    expected: {decision: veto, failure_code: lab_redteam_gate_failure}
  - fixture_id: META-LAB-V5-FIXTURE-3-ENGINE-ADAPTER-CANDIDATE
    given: {adapter_id: adapter:engine-export-v5, suite_id: SUITE:duotronic-engine-export-v5, engines: [lammps, gpaw]}
    operation: evaluate_l4_adapter_proposal
    expected: {production_promotion_allowed: false, research_valid: true, required_transport_profile: engine-export-transport@v1}
```
