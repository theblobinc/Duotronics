# Duotronic Normalizer Profiles v1.2

**Status:** Source-spec baseline candidate  
**Version:** normalizer-profiles@v1.2  
**Document kind:** Normative normalizer contract plus reference profiles  
**Primary purpose:** Define deterministic normal-form construction for family objects, witness keys, geometry paths, transport adapters, and replay identity.

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

A normalizer converts accepted raw input into canonical form or rejects it. Normalizers are identity-affecting components and MUST be versioned, deterministic, and replay-pinned.

## 2. Hard rule

> **Status tag:** normative

No raw witness bundle, raw family word, raw geometry path, or raw transport payload may become authoritative merely because parsing did not crash. Normal-form construction must succeed under a declared normalizer profile.

## 3. Normalizer profile schema

> **Status tag:** normative

```yaml
normalizer_profile:
  normalizer_id: string
  normalizer_version: string
  status: active | experimental | deprecated | rejected
  input_schema: string
  output_schema: string
  accepted_language: string
  rejected_language: string
  deterministic_ordering: string
  ambiguity_policy: reject | select_canonical | preserve_metadata
  low_confidence_policy: reject | generic_bypass | conditional
  canonical_selection_rule: string
  identity_affecting: true
  failure_codes: [string]
  fixture_pack: string
```

## 4. Normalizer classes

> **Status tag:** reference

| Class | Use | Example |
|---|---|---|
| identity | input already canonical | hex6 canonical digit word |
| finite-state | regular token languages | digit parser |
| symbolic reducer | bounded symbolic expressions | canonical tuple ordering |
| path reducer | group/path words | reflection family paths |
| orbit reducer | geometry representatives | sector/chamber canonical form |
| adapter normalizer | lossy boundary conversion | Witness8 row decode |
| transport normalizer | validated payload projection | DBP payload after integrity check |

## 5. Determinism requirements

> **Status tag:** normative

A normalizer MUST:

1. be deterministic under pinned inputs and versions;
2. reject unsupported family identifiers;
3. reject unknown schema versions unless an adapter is declared;
4. emit a failure code on failure;
5. preserve expected-loss metadata;
6. avoid using display glyphs as identity unless explicitly declared;
7. avoid field-order dependence for mapping objects;
8. include version in replay identity.

## 6. Non-conformant behavior

> **Status tag:** normative

A normalizer MUST NOT:

1. silently switch family identity;
2. silently switch schema version;
3. silently collapse token-free absence to numeric zero;
4. convert invalid input into valid output without failure metadata;
5. let raw geometry override family arithmetic;
6. use unordered mappings as ordered witness rows;
7. mutate canonical identity without migration.

## 7. Baseline profiles

> **Status tag:** reference

```yaml
profiles:
  - normalizer_id: simple-bijective-word-normalizer
    normalizer_version: simple-bijective-word-normalizer@v1
    input_schema: family-word-raw@v1
    output_schema: dpfc-family-object@v5.8
    ambiguity_policy: reject
    canonical_selection_rule: ordinal_digit_sequence

  - normalizer_id: reflection-path-normalizer
    normalizer_version: reflection-path-normalizer@v1
    input_schema: reflection-path-raw@v1
    output_schema: dpfc-family-object@v5.8
    ambiguity_policy: select_canonical
    canonical_selection_rule: lexicographically_smallest_reduced_path

  - normalizer_id: witness8-row-normalizer
    normalizer_version: witness8-row-normalizer@v1
    input_schema: witness8-row@v1
    output_schema: witness8-decoded-state@v1
    ambiguity_policy: reject
    canonical_selection_rule: explicit_field_order
```

## 8. Failure code table

> **Status tag:** reference

| Failure code | Meaning | Default action |
|---|---|---|
| `unknown_family` | family not in registry | family_bypass |
| `schema_mismatch` | input schema not accepted | reject |
| `invalid_digit` | digit outside family alphabet | reject |
| `empty_family_word` | no native magnitude | reject |
| `ambiguous_orbit` | geometry representative ambiguous | family_bypass |
| `field_order_invalid` | ordered witness fields unavailable | reject |
| `absence_zero_collision` | absence decoded as numeric zero | full_bypass |
| `normalizer_timeout` | normalizer exceeded budget | degraded |

## 9. Reference fixture

> **Status tag:** reference

```yaml
fixture_pack: normalizer-profiles-v1-fixtures
fixtures:
  - fixture_id: NORMALIZER-FIXTURE-1-HEX6-CANONICAL
    given:
      family_id: hex6
      word: [h1, h4]
    operation: normalize_family_word
    expected:
      canonical_storage: "family:hex6 schema_version:dpfc-family@v5.8 digits:1 4"
      core_magnitude: mu_10
      lookup_allowed: true

  - fixture_id: NORMALIZER-FIXTURE-2-WITNESS8-MAPPING-ORDER
    given:
      witness8_row:
        degeneracy: 1.0
        parity: 1.0
        band_position: 0.5
        kind_flag: 1.0
        activation_density: 0.125
        center_on: 1.0
        n_sides_norm: 0.6
        value_norm: 0.0
    operation: normalize_witness8_row
    expected:
      field_order_used: [value_norm, n_sides_norm, center_on, activation_density, kind_flag, band_position, parity, degeneracy]
      presence_status: present_zero_value
```

## 10. Conformance checklist

> **Status tag:** normative

A normalizer implementation passes this source spec only if it:

1. runs deterministically under pinned versions;
2. emits explicit failure codes;
3. distinguishes absence, invalidity, unknown, and numeric zero;
4. blocks authoritative lookup on failure;
5. records expected losses;
6. supports replay comparison;
7. passes normative fixtures.


---

# Appendix Lab - Canonical JSON and Hashing Lab Imports

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
