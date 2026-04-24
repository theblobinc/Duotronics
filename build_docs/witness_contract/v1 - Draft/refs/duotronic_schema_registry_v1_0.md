# Duotronic Schema Registry v1.0

**Status:** Source-spec baseline candidate  
**Version:** schema-registry@v1.0  
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
dpfc-family@v5.6
witness-contract@v10.6
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
| `source-architecture@v1.1` | active | Source Architecture Overview | no | corpus map and reading guide |
| `dpfc-core@v5.6` | active | DPFC | yes | positive core, family semantics, conversion |
| `witness-contract@v10.6` | active | Witness Contract | yes | trust, replay, policy, runtime layers |
| `schema-registry@v1.0` | active | Schema Registry | yes | this document |
| `family-registry@v1.0` | active | Family Registry | yes | family declarations |
| `normalizer-profiles@v1.0` | active | Normalizer Profiles | yes | canonicalization profiles |
| `transport-profiles@v1.0` | active | Transport Profiles | yes | Witness8, DBP, WSB2 |
| `retention-diagnostics@v1.0` | active | Retention Diagnostics | no by default | metric specs and baselines |
| `policy-shield@v1.0` | active | Policy Shield Guide | yes | modes and L5 decisions |
| `migration-guide@v1.0` | active | Migration Guide | yes | replay and migration |
| `research-edo@v1.0` | research | EDO Research Profile | no | bounded future/research |
| `research-acoustics@v1.0` | research | Acoustics Research Profile | no | bounded future/research |
| `research-qcd-analogy@v1.0` | analogy | QCD Analogy Research Profile | no | no physics claim |

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
