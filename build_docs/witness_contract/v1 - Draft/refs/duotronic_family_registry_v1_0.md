# Duotronic Family Registry v1.0

**Status:** Source-spec baseline candidate  
**Version:** family-registry@v1.0  
**Document kind:** Normative family registry plus reference declarations  
**Primary purpose:** Define how DPFC families are declared, validated, normalized, serialized, converted, deprecated, and promoted.

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

The Family Registry governs family declarations used by DPFC and the Witness Contract. A family declaration defines how a native family word maps to the DPFC positive core, how it is serialized, how it is normalized, and how it may carry geometry or witness metadata.

A family registry entry is required before a family-sensitive witness object may become authoritative.

## 2. Family declaration schema

> **Status tag:** normative

```yaml
family_entry:
  family_id: string
  family_schema_version: string
  status: sketch | experimental | research_valid | normative_reference | deprecated | rejected
  kind: symbolic | polygon | reflection | edo | adapter | research
  alphabet:
    ordered_digits: [string]
    public_labels_are_one_based: true
  bijective_modulus: integer
  evaluation_rule: bijective_positional
  successor_rule: bijective_carry_successor
  core_bridge: Phi_F
  inverse_bridge: Phi_F_inverse
  canonical_storage:
    serializer_id: string
    serializer_version: string
  normalizer:
    normalizer_id: string
    normalizer_version: string
  geometry:
    geometry_id: string | null
    geometry_version: string | null
    status: reference | research | null
  witness_schema: string | null
  conversion_profiles: [string]
  conformance_fixture_pack: string
  promotion_requirements: [string]
```

## 3. Normative family requirements

> **Status tag:** normative

A valid finite DPFC family MUST satisfy:

1. finite ordered digit alphabet;
2. nonempty native words;
3. no native absence digit;
4. deterministic bijective positional evaluation;
5. deterministic inverse encoding;
6. deterministic successor;
7. canonical serializer;
8. registry-pinned schema version;
9. explicit failure behavior;
10. conformance fixtures.

## 4. Family status ladder

> **Status tag:** normative

| Status | Meaning | Runtime authority |
|---|---|---|
| `sketch` | idea only | none |
| `experimental` | schema exists, tests incomplete | no authoritative lookup |
| `research_valid` | passes local tests but not normative | opt-in only |
| `normative_reference` | approved baseline family | allowed by policy |
| `deprecated` | retained for replay/migration | read/replay only |
| `rejected` | failed conformance or safety | none |

## 5. Baseline families

> **Status tag:** reference

```yaml
families:
  - family_id: hex6
    family_schema_version: dpfc-family@v5.6
    status: normative_reference
    kind: polygon
    alphabet: [h1, h2, h3, h4, h5, h6]
    bijective_modulus: 6
    geometry_id: regular-hexagon@v1
    normalizer_id: simple-bijective-word-normalizer@v1

  - family_id: refl3
    family_schema_version: dpfc-family@v5.6
    status: research_valid
    kind: reflection
    alphabet: [r1, r2, r3]
    bijective_modulus: 3
    geometry_id: reflection-triangle@v1
    normalizer_id: reflection-path-normalizer@v1

  - family_id: edo31
    family_schema_version: dpfc-family@v5.6
    status: research_valid
    kind: edo
    alphabet: [e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14, e15, e16, e17, e18, e19, e20, e21, e22, e23, e24, e25, e26, e27, e28, e29, e30, e31]
    bijective_modulus: 31
    geometry_id: circle-of-diesis@v1
    external_zero_bridge: external_step_k_maps_to_e_k_plus_1
```

## 6. Successor law requirement

> **Status tag:** normative

Every finite family must implement the bijective carry successor. For any possibly empty prefix `X` and any non-maximal final digit `δ_i` with `1 <= i < b_F`:

```text
fsucc_F(X δ_i) = X δ_{i+1}
```

For maximal final digits:

```text
fsucc_F(X δ_b) = fsucc_F(X) δ_1
```

When `X` is empty:

```text
fsucc_F(δ_b) = δ_1 δ_1
```

## 7. Conversion profiles

> **Status tag:** normative

A family conversion profile MUST declare:

1. source family;
2. target family;
3. preserved invariants;
4. expected losses;
5. approximate invariants when applicable;
6. invalid cases;
7. error budgets when applicable;
8. fixture pack.

## 8. Geometry registry link

> **Status tag:** reference

Geometry may aid canonicalization, orbit reduction, display, debugging, compression, and witness construction. Geometry does not prove arithmetic unless paired with a valid bridge and successor theorem.

## 9. Promotion checklist

> **Status tag:** normative

A family may not be promoted to `normative_reference` unless:

1. evaluation and inverse encoding round-trip;
2. successor bridge tests pass;
3. conversion preserves core magnitude;
4. canonical serialization is deterministic;
5. normalizer failures are explicit;
6. absence and numeric zero remain separate;
7. geometry claims are tested or bounded;
8. migration plan exists for future changes.
