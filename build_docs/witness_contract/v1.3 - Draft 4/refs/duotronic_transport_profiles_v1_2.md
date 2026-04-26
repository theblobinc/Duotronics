# Duotronic Transport Profiles v1.2

**Status:** Source-spec baseline candidate  
**Version:** transport-profiles@v1.2  
**Document kind:** Normative transport boundary profiles plus reference fixtures  
**Primary purpose:** Define Witness8, DBP, and WSB2 transport boundaries without confusing transport encoding with canonical semantics.

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

Transport profiles define how information crosses wire, row, frame, sparse, or implementation boundaries. Transport profiles do not define DPFC arithmetic and do not grant trust by themselves.

## 2. Transport-before-semantics rule

> **Status tag:** normative

Transport validation MUST precede semantic interpretation. A failed frame, row, integrity check, profile check, shape check, or sequence check MUST NOT enter authoritative witness memory.

## 3. Witness8 profile

> **Status tag:** normative

A Witness8 row has exactly eight ordered fields:

1. `value_norm`;
2. `n_sides_norm`;
3. `center_on`;
4. `activation_density`;
5. `kind_flag`;
6. `band_position`;
7. `parity`;
8. `degeneracy`.

Mapping inputs must be decoded by this explicit order, not by map iteration order.

## 4. Token-free absence

> **Status tag:** normative

An all-inactive Witness8 row under the active profile represents token-free absence:

```text
[0, 0, 0, 0, 0, 0, 0, 0]
```

It does not infer numeric zero. A present numeric-zero value must use a present row under a profile that supports numeric zero.

## 5. DBP minimum profile

> **Status tag:** normative

A DBP-like frame contains:

1. frame shape;
2. profile identifier;
3. payload length;
4. structural fields;
5. semantic payload region;
6. integrity field such as CRC or authentication tag;
7. optional encryption metadata;
8. optional sequence number;
9. optional replay protection field.

DBP structural fields are transport structure, not witness numerals.

## 6. WSB2 sparse-row profile

> **Status tag:** normative

WSB2 represents sparse witness rows or lanes. An inactive lane is absence at the sparse-row layer. It is not numeric zero. A sparse-row profile must declare its inactive-lane representation, active-lane validation, and payload decoder.

## 7. Transport state machine

> **Status tag:** reference

```text
received
-> shape_checked
-> profile_resolved
-> integrity_checked
-> replay_checked
-> payload_extracted
-> semantic_decoder_allowed
-> canonicalization_candidate
```

Any failed transition produces a rejected or bypass state.

## 8. Transport profile schema

> **Status tag:** reference

```yaml
transport_profile:
  profile_id: string
  profile_version: string
  transport_kind: dbp | witness8 | wsb2 | adapter
  shape_validator: string
  integrity_validator: string | null
  sequence_policy: string | null
  replay_policy: string | null
  semantic_decoder: string
  failure_behavior: reject | audit_only | transport_bypass
  authoritative_memory_allowed_before_validation: false
```

## 9. Baseline fixtures

> **Status tag:** reference

```yaml
fixture_pack: transport-profiles-v1-fixtures
fixtures:
  - fixture_id: TRANSPORT-FIXTURE-1-FAILED-DBP-INTEGRITY
    given:
      frame:
        shape_valid: true
        profile_id: dbp-minsafe@v1
        integrity_check: failed
        payload_kind: witness8
    operation: ingress_frame
    expected:
      semantic_decode_allowed: false
      trusted_memory_write: false
      failure_code: transport_integrity_failed

  - fixture_id: TRANSPORT-FIXTURE-2-WITNESS8-ABSENCE
    given:
      witness8_row: [0, 0, 0, 0, 0, 0, 0, 0]
    operation: decode_witness8
    expected:
      presence_status: structurally_absent
      numeric_zero_inferred: false
      trusted_for_lookup: false

  - fixture_id: TRANSPORT-FIXTURE-3-PRESENT-ZERO
    given:
      witness8_row:
        value_norm: 0.0
        n_sides_norm: 0.6
        center_on: 1.0
        activation_density: 0.125
        kind_flag: 1.0
        band_position: 0.5
        parity: 1.0
        degeneracy: 1.0
      profile_declares_numeric_zero: true
    operation: decode_witness8
    expected:
      presence_status: present_zero_value
      token_free_absent: false
```

## 10. Security and replay

> **Status tag:** normative

A transport profile must define whether it uses no integrity, checksum-only integrity, authenticated integrity, encryption, replay windows, sequence numbers, or signed payloads. A profile lacking integrity may be allowed for local experiments, but it must not be used for authoritative cross-boundary trust without an explicit policy exception.

## 11. Conformance checklist

> **Status tag:** normative

A transport implementation must:

1. validate transport before semantics;
2. reject failed integrity;
3. distinguish inactive lane from numeric zero;
4. decode ordered rows by explicit order;
5. emit explicit failure codes;
6. record profile version in replay traces;
7. prevent failed frames from entering trusted memory.


---

# Appendix Lab - Engine Export Transport Profile

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
