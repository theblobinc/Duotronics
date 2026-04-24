# EDO, Temperament, and Circle Families as a Bounded Duotronic Research Profile v1.0

**Status:** Research profile paper  
**Version:** research-edo@v1.0  
**Document kind:** Research/reference paper, not normative core  
**Primary purpose:** Explore how equal divisions of the octave, 31-EDO, circle-of-diesis geometry, temperament, ratio approximation, and enharmonic separation can inform DPFC family design without becoming proof or required ontology.

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

This paper treats EDO systems as a bounded research profile. It does not claim that 31-EDO is the universal Duotronic family. It does not change the DPFC core. It supplies a rich worked example of a finite, modular, geometric, approximate, notation-rich family.

## 2. Why EDO helps DPFC

> **Status tag:** reference

EDO systems divide an octave into a finite number of equal logarithmic steps. This helps DPFC because it demonstrates:

1. finite family identity;
2. modular external arithmetic;
3. multiple geometries over one family;
4. ratio-to-step approximation;
5. declared error budgets;
6. enharmonic separation and collapse;
7. expected-loss conversion.

## 3. External-zero boundary

> **Status tag:** normative

Pitch-class systems naturally use an external zero. DPFC may use that only through a bridge:

```text
external_step(k) = k in 0..N-1
native_label(k) = e_(k+1)
```

External pitch class `0` maps to native label `e1`; it is not structural absence.

## 4. 31-EDO profile

> **Status tag:** reference

```yaml
EDOFamilyProfile:
  family_id: edo31
  status: research_valid
  step_count: 31
  period: octave
  external_domain: "0..30 modulo 31"
  native_label_domain: "e1..e31"
  step_ratio: "2^(1/31)"
  step_cents: 38.7096774194
  canonical_geometries:
    - circle_of_diesis
    - circle_of_fifths_31
```

## 5. Circle of diesis

> **Status tag:** research

The circle of diesis is the successor geometry:

```text
0 -> 1 -> 2 -> ... -> 30 -> 0
```

DPFC-native rendering uses:

```text
e1 -> e2 -> e3 -> ... -> e31 -> e1
```

This geometry is useful for adjacency, micro-step witness relations, local movement, and enharmonic distance.

## 6. Circle of fifths in 31-EDO

> **Status tag:** research

A fifth in 31-EDO is often represented by `18\31`. Since `gcd(18,31)=1`, repeated `+18 mod 31` visits every pitch class. This gives a second generator geometry over the same family.

## 7. Ratio approximation bridge

> **Status tag:** reference

To approximate a just ratio `r` in `N`-EDO:

```math
k = round(N log_2(r))
```

The EDO approximation is `2^(k/N)`, and the cents error is:

```math
error = 1200k/N - 1200log_2(r)
```

## 8. Temperament as declared approximation

> **Status tag:** research

Temperament teaches DPFC that conversion may be exact for some invariants, approximate for others, and lossy for others. A conversion is not merely correct or incorrect; it must declare preserved, approximate, expected-loss, and invalid cases.

## 9. Enharmonic separation

> **Status tag:** research

A distinction collapsed in one family may be preserved in another. In one 31-EDO spelling scheme, C-sharp and D-flat may be separated by one diesis. DPFC should treat this as a canonicalization warning: family identity determines whether two surface forms are equal.

## 10. Example fixtures

> **Status tag:** reference

```yaml
fixture_pack: research-edo-v1-fixtures
fixtures:
  - fixture_id: EDO-FIXTURE-1-MAJOR-THIRD
    given:
      ratio: "5/4"
      edo_steps: 31
    operation: approximate_ratio
    expected:
      nearest_step: '10\31'
      preservation_class: approximate_preserve

  - fixture_id: EDO-FIXTURE-2-TRANSPOSITION
    given:
      chord_external_steps: [0, 11, 18]
      transposition: 5
      modulus: 31
    operation: transpose_mod_n
    expected:
      transposed_chord_external_steps: [5, 16, 23]
      preserved: [internal_step_distances, family_id, modulus]
```

## 11. Non-claims

> **Status tag:** normative

This profile does not claim:

1. 31-EDO is the correct Duotronic core;
2. musical consonance is truth;
3. external zero should become native absence;
4. temperament proves DPFC;
5. EDO notation is required runtime ontology.

## 12. Useful outcome

> **Status tag:** reference

The EDO profile is useful because it gives DPFC a concrete family that is finite, geometric, modular, approximate, and notationally rich. It should remain research/reference unless promoted through conformance tests.
