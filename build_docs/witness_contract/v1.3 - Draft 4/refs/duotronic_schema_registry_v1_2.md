# Duotronic Schema Registry v1.2

**Status:** Source-spec baseline candidate  
**Version:** schema-registry@v1.2  
**Document kind:** Normative registry plus reference schemas  
**Primary purpose:** Define stable identifiers, version rules, compatibility classes, schema-entry shapes, and fixture conventions used by DPFC, the Witness Contract, transport profiles, normalizers, retention diagnostics, policy shielding, and migration/replay documents.

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

The Schema Registry governs machine-readable identifiers for Duotronic source documents and runtime artifacts. It does not define DPFC arithmetic and does not grant runtime trust. Its job is to make names, versions, compatibility, and deprecation explicit.

This registry covers:

1. document identifiers;
2. schema identifiers;
3. family identifiers;
4. normalizer identifiers;
5. transport profile identifiers;
6. retention metric identifiers;
7. policy profile identifiers;
8. migration profile identifiers;
9. replay identity identifiers;
10. fixture-pack identifiers.

## 2. Registry authority and boundary

> **Status tag:** normative

A Duotronic implementation MUST NOT rely on unversioned semantic identifiers. Every object that affects canonical identity, trust, transport validation, retention scoring, or migration must carry a versioned identifier.

The Schema Registry does not decide whether a payload is trusted. The Witness Contract does that after validation and canonicalization. The registry only provides stable names and compatibility rules.

## 3. Identifier grammar

> **Status tag:** normative

A schema identifier SHOULD follow this shape:

```text
namespace/name@major.minor.patch
```

A shortened project-local identifier MAY omit patch when patch changes are non-semantic:

```text
dpfc-family@v5.10
witness-contract@v10.10
witness8-minsafe@v1
retention/core-magnitude@v1
policy-shield/minsafe@v1
```

Required fields:

1. `namespace`;
2. `name`;
3. `version`;
4. `status`;
5. `owner_document`;
6. `compatibility_class`;
7. `identity_affecting`;
8. `deprecation_policy`.

## 4. Version semantics

> **Status tag:** normative

Version changes are classified as:

| Change class | Meaning | Identity impact | Migration required |
|---|---|---:|---:|
| `patch` | editorial or non-semantic fix | no | no |
| `minor` | additive compatible change | usually no | maybe |
| `major` | semantic or incompatible change | yes | yes |
| `profile-fork` | new profile with related lineage | yes | yes |
| `deprecated` | retained for replay/history only | no new writes | migration preferred |

A change is semantic if it alters canonical identity, normalizer output, family value, transport validation result, retention meaning, policy action, or replay output.

## 5. Registry entry schema

> **Status tag:** normative

```yaml
schema_entry:
  schema_id: string
  human_name: string
  status: active | experimental | deprecated | future | rejected
  owner_document: string
  version: string
  compatibility_class: exact | additive | adapter_required | incompatible
  identity_affecting: true
  public_claim_class: C1 | C2 | C3 | C4 | C5 | C6
  depends_on: [string]
  supersedes: [string]
  deprecation_policy:
    read_allowed: true
    write_allowed: false
    migration_target: string | null
  validation:
    validator_id: string
    fixture_pack: string
    failure_action: reject | bypass | degrade | audit_only
```

## 6. Baseline registry table

> **Status tag:** reference

| Schema ID | Status | Owner document | Identity-affecting | Notes |
|---|---|---|---:|---|
| `source-architecture@v1.3` | active | Source Architecture Overview | no | corpus map and reading guide |
| `dpfc-core@v5.8` | active | DPFC | yes | positive core, family semantics, conversion |
| `witness-contract@v10.8` | active | Witness Contract | yes | trust, replay, policy, runtime layers |
| `schema-registry@v1.2` | active | Schema Registry | yes | this document |
| `family-registry@v1.2` | active | Family Registry | yes | family declarations |
| `normalizer-profiles@v1.2` | active | Normalizer Profiles | yes | canonicalization profiles |
| `transport-profiles@v1.2` | active | Transport Profiles | yes | Witness8, DBP, WSB2 |
| `retention-diagnostics@v1.2` | active | Retention Diagnostics | no by default | metric specs and baselines |
| `policy-shield@v1.2` | active | Policy Shield Guide | yes | modes and L5 decisions |
| `migration-guide@v1.2` | active | Migration Guide | yes | replay and migration |
| `research-edo@v1.2` | research | EDO Research Profile | no | bounded future/research |
| `research-acoustics@v1.2` | research | Acoustics Research Profile | no | bounded future/research |
| `research-qcd-analogy@v1.2` | analogy | QCD Analogy Research Profile | no | no physics claim |

## 7. Compatibility classes

> **Status tag:** normative

Compatibility classes:

1. `exact`: same canonical output and same trust behavior;
2. `additive`: new optional fields only; old objects remain valid;
3. `adapter_required`: conversion possible only through a declared adapter;
4. `incompatible`: migration plan required;
5. `replay_only`: accepted only for historical replay;
6. `rejected`: not accepted for read, write, promotion, or replay.

## 8. Canonical identity fields

> **Status tag:** normative

A canonical object that affects identity MUST include:

1. schema identifier;
2. schema version;
3. family identifier when applicable;
4. family schema version when applicable;
5. normalizer version when applicable;
6. serializer version when applicable;
7. canonical payload;
8. expected-loss metadata when applicable.

Raw witness metadata MAY be preserved, but it MUST NOT silently alter canonical identity.

## 9. Failure behavior

> **Status tag:** normative

Unknown schema behavior is never success. If a runtime encounters an unknown schema it must choose one declared behavior:

1. `reject`;
2. `audit_only`;
3. `family_bypass`;
4. `transport_bypass`;
5. `lookup_bypass`;
6. `full_bypass`.

Silent acceptance of unknown schema versions is non-conformant.

## 10. Fixture pack schema

> **Status tag:** reference

```json
{
  "fixture_pack": "schema-registry-v1-fixtures",
  "schema_version": "fixture-pack@v1",
  "fixtures": [
    {
      "fixture_id": "SCHEMA-FIXTURE-1-UNKNOWN-SCHEMA-REJECT",
      "given": {"schema_id": "unknown-profile@v99"},
      "operation": "resolve_schema",
      "expected": {
        "resolution": "unknown",
        "lookup_allowed": false,
        "failure_code": "schema_unknown"
      }
    }
  ]
}
```

## 11. Conformance checklist

> **Status tag:** normative

A conforming Schema Registry implementation must:

1. reject unversioned identity-affecting schemas;
2. distinguish exact, additive, adapter-required, incompatible, and replay-only compatibility;
3. pin registry versions in replay traces;
4. emit explicit failure codes;
5. prevent deprecated write paths unless a policy explicitly allows migration staging;
6. preserve one-based public labels in registry documentation;
7. distinguish external zero-bearing standards from native absence;
8. expose machine-readable registry entries.


---

# Appendix Lab - Historical Lab Schema Imports

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
