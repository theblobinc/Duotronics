# Acoustics, Fourier Analysis, and Spectral Witnesses as a Bounded Duotronic Research Profile v1.2

**Status:** Research profile paper  
**Version:** research-acoustics@v1.2  
**Document kind:** Research/reference paper, not normative core  
**Primary purpose:** Explore how waveform analysis, spectra, partials, missing fundamentals, roughness, masking, and timbre-scale theory can inform witness extraction and retention diagnostics without overclaiming truth.

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


## 1. Research boundary

> **Status tag:** research

This profile treats acoustics as a source of witness-design analogies and optional signal profiles. It does not claim that Fourier spectra are canonical Duotronic witnesses by default. Spectral evidence requires provenance, validation, canonicalization, confidence, and policy gating.

## 2. Central import

> **Status tag:** reference

The useful chain is:

```text
waveform -> spectrum -> partials -> inferred structure -> witness signature -> canonicalization candidate
```

This maps well to the Witness Contract because raw signal evidence is not trusted merely because it is observed.

## 3. Spectral witness signature

> **Status tag:** reference

```yaml
SpectralWitnessSignature:
  schema_version: spectral-witness@v1
  observed_waveform_hash: string
  sample_rate_hz: number
  analysis_window:
    window_size_samples: integer
    hop_size_samples: integer
    window_function: string
  spectrum_profile:
    partials:
      - frequency_hz: number
        amplitude: number
        phase: number | null
        confidence: number
    inharmonicity_score: number | null
    roughness_score: number | null
    masking_score: number | null
  inferred_pitch:
    pitch_hz: number | null
    inference_type: observed_fundamental | missing_fundamental | ambiguous | none
  trust:
    canonicalization_status: raw | canonicalized | rejected
    provenance: string
```

## 4. Fourier provenance rule

> **Status tag:** normative

A Fourier-derived witness must record sample rate, window function, window size, hop size, normalization policy, leakage handling, source hash, and confidence policy. Without provenance, it may remain audit data but must not enter authoritative memory.

## 5. Missing fundamental as derived witness

> **Status tag:** research

A listener or algorithm may infer a fundamental that is not directly present. In witness terms, this is a derived witness, not an observed witness.

```yaml
MissingFundamentalDerivedWitness:
  observed_components_hz: [200, 300, 400, 500]
  inferred_fundamental_hz: 100
  inference_type: missing_fundamental
  trust_status: conditional
  rule: inferred_witness_must_not_be_stored_as_observed_witness
```

## 6. Roughness and partial alignment

> **Status tag:** research

Roughness metrics can inspire retention diagnostics. They show how local interactions among components can produce a stability score. This is useful only if baselines and failure actions are declared.

## 7. Retention metric candidate

> **Status tag:** reference

```yaml
RetentionMetricSpec:
  metric_id: roughness-weighted-partial-alignment@v1
  invariant_kind: partial_alignment
  extractor_id: spectral-partial-extractor@v1
  similarity_id: roughness_weighted_alignment@v1
  transformation: spectral_canonicalization
  baseline_suite:
    - shuffled_partials
    - detuned_partials
    - masked_signal
    - window_leakage_control
  preservation_class: should_preserve
  failure_action: degrade_confidence
```

## 8. Masking boundary

> **Status tag:** research

A spectral component may be physically present but masked by a stronger nearby component. A masked witness must not receive the same confidence as an unmasked witness.

## 9. Signal-to-witness pipeline

> **Status tag:** reference

```text
raw waveform
-> provenance check
-> windowed spectral analysis
-> partial extraction
-> masking/roughness diagnostics
-> inferred structure
-> witness signature
-> canonicalization candidate
-> policy gate
```

## 10. Non-claims

> **Status tag:** normative

This profile does not claim:

1. spectral consonance is semantic truth;
2. Fourier components are canonical witnesses by default;
3. missing fundamentals are observed facts;
4. roughness scores prove correctness;
5. music theory proves Duotronics.

## 11. Useful outcome

> **Status tag:** reference

The acoustics profile gives Duotronics a high-value example of raw evidence becoming structured evidence only through explicit extraction, provenance, inference, and trust boundaries.


---

# Appendix Lab - Spectral and Engine Evidence Integration

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
