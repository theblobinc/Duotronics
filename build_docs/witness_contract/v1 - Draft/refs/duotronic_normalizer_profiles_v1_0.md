# Duotronic Normalizer Profiles v1.0

**Status:** Source-spec baseline candidate  
**Version:** normalizer-profiles@v1.0  
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
    output_schema: dpfc-family-object@v5.6
    ambiguity_policy: reject
    canonical_selection_rule: ordinal_digit_sequence

  - normalizer_id: reflection-path-normalizer
    normalizer_version: reflection-path-normalizer@v1
    input_schema: reflection-path-raw@v1
    output_schema: dpfc-family-object@v5.6
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
      canonical_storage: "family:hex6 schema_version:dpfc-family@v5.6 digits:1 4"
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
