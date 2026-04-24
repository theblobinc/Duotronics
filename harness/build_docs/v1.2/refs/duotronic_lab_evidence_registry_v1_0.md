# Duotronic Lab Evidence Registry v1.0

**Status:** Source-spec baseline candidate  
**Version:** lab-evidence-registry@v1.0  
**Document kind:** Reference evidence registry with normative bounded-import rules  
**Primary purpose:** Import the historical Duotronic grid, polygon, benchmark, and external-engine simulation labs into the source corpus as executable lineage, schemas, fixtures, adapters, and replayable evidence without overclaiming physics or redefining DPFC/Witness/Meta semantics.

> Drafting note. This registry is built from the code and artifacts in the historical `duotronic-grid.zip` lab archive. The archive contains early grid renderers, polygon catalogs, polygon labs v1 through v4, and engine lab v5 with LAMMPS/GPAW exports. The import is intentionally bounded: the labs are engineering evidence and historical source material, not proof of physical correspondence.

---

## Document status tag key

> **Status tag:** reference

Every major section carries one primary status tag. Secondary classifications use `Related tags:` on a separate line.

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for bounded import or conformance. | Conforming corpus documents must follow it. |
| `reference` | Schemas, examples, code-derived object maps, and evidence descriptions. | Useful for implementation and migration. |
| `research` | Experimental benchmark, metric, adapter, or lab-derived claim. | Must remain opt-in until promoted. |
| `future` | Useful planned work not active yet. | Must not be treated as live authority. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |

## 1. Scope

> **Status tag:** normative

This registry imports historical lab work into the corpus as schema lineage, executable reference patterns, benchmark-suite examples, gate-report examples, adapter examples, artifact-manifest examples, external-engine parser examples, policy-shield red-team fixtures, meta-runtime shadow-replay fixtures, and migration examples.

This registry does not import lab results as DPFC theorem proof, physical proof, QCD evidence, acoustics evidence, DFT correctness proof, molecular dynamics correctness proof, or canonical runtime authority.

## 2. Lab lineage

> **Status tag:** reference

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

## 3. Code-derived object inventory

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

## 4. Polygon Lab v4 benchmark evidence

> **Status tag:** research
> **Related tags:** reference

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

## 5. Engine Lab v5 external simulation evidence

> **Status tag:** research
> **Related tags:** reference

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

## 6. Historical schema imports

> **Status tag:** reference

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

## 7. Engine export transport profile candidate

> **Status tag:** normative
> **Related tags:** reference

```yaml
transport_profile:
  profile_id: engine-export-transport@v1
  status: research_valid
  transport_kind: external_engine_export
  supported_sources: [lammps_log, lammps_mpi_log, gpaw_json, gpaw_text_log, gpaw_info, environment_json]
  validation_order: [source_file_exists, source_file_hash_matches_manifest, parser_success, engine_identity_extracted, numeric_sanity_checks, gate_report_created, evidence_bundle_hash_created]
  semantic_decode_allowed_before_validation: false
  authoritative_memory_allowed_before_canonicalization: false
```

## 8. Lab-derived RetentionMetricSpec candidates

> **Status tag:** research

```yaml
retention_metrics:
  - metric_id: lab-v4-spectral-gap-retention@v1
    invariant_kind: graph_operator_connectivity
    extractor_id: polygon-laplacian-extractor@v4
    similarity_id: spectral_gap_threshold@v4
    transformation: variant_family_change
    baseline_suite: [baseline-v4, candidate-v4, redteam-disconnect-v4, redteam-unstable-v4]
    preservation_class: should_preserve
    failure_action: block_promotion
  - metric_id: lab-v5-engine-export-consistency@v1
    invariant_kind: external_engine_result_consistency
    extractor_id: engine-export-parser@v5
    similarity_id: gate_bundle_pass_fail@v5
    transformation: external_solver_adapter
    baseline_suite: [lammps_serial_vs_mpi, lammps_thermo_consistency, lammps_final_energy_alignment, gpaw_h2_energy_consistency, gpaw_he_energy_consistency, gpaw_rank_consistency]
    preservation_class: should_preserve
    failure_action: degrade_or_block_adapter
```

## 9. Policy and meta fixtures

> **Status tag:** reference

```yaml
fixtures:
  - fixture_id: POLICY-LAB-V4-FIXTURE-1-REDTEAM-DISCONNECT-BLOCK
    given: {variant_id: VAR:redteam-disconnect-v4, total_cases: 6, fails: 3}
    expected: {promotion_allowed: false, decision: veto}
  - fixture_id: POLICY-LAB-V4-FIXTURE-2-REDTEAM-UNSTABLE-BLOCK
    given: {variant_id: VAR:redteam-unstable-v4, total_cases: 6, fails: 3}
    expected: {promotion_allowed: false, decision: veto}
  - fixture_id: META-LAB-V5-FIXTURE-3-ENGINE-EVIDENCE-BUNDLE
    given: {evidence_bundle_schema: duotronic/evidence-bundle@v5, adapter_id: adapter:engine-export-v5, supported_engines: [lammps, gpaw]}
    expected: {trusted_as_physics_proof: false, trusted_as_adapter_evidence: true, requires_transport_profile: engine-export-transport@v1}
```

## 10. Migration example from v4 to v5

> **Status tag:** reference

```yaml
MigrationPlan:
  migration_id: polygon-lab-v4-to-engine-lab-v5
  source_version: polygon-lab@v4
  target_version: engine-lab@v5
  migration_kind: research_lineage_expansion
  affected_layers: [schema_registry, family_registry, transport_profiles, retention_diagnostics, policy_shield, meta_runtime]
  must_preserve: [canonical_json_hashing, theta_hash_lineage, run_id_hashing, benchmark_id_versioning, gate_report_status, artifact_manifest_presence]
  expected_loss: [toy_graph_operator_specificity, polygon_only_assumption]
  new_capabilities: [external_engine_export_adapter, lammps_parser, gpaw_parser, docker_compose_environment_capture, evidence_bundle_artifact_hashing]
```

## 11. Non-claims

> **Status tag:** normative

The lab evidence registry does not claim that polygon toy operators are physical proof, graph spectral gaps are DPFC theorems, external solver outputs prove Duotronic physics, LAMMPS/GPAW export parsing validates a theory of matter, red-team gates prove all unsafe cases are caught, lab hashes replace canonical lower-layer object identity, or meta-runtime assertions may overwrite DPFC or Witness semantics.
