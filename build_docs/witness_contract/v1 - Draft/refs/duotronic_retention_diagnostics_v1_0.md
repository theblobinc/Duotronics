# Duotronic Retention Diagnostics v1.0

**Status:** Source-spec baseline candidate  
**Version:** retention-diagnostics@v1.0  
**Document kind:** Research/reference metrics specification with normative discipline rules  
**Primary purpose:** Define how to measure whether declared invariants survive canonicalization, conversion, transport, replay, migration, and policy-controlled transformations without overclaiming proof.

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

> **Status tag:** reference

Retention diagnostics measure whether something declared as important survives a transformation. Retention metrics are diagnostics by default. They become policy authority only if a Policy Shield profile explicitly promotes them.

## 2. Metric discipline rule

> **Status tag:** normative

A retention metric MUST NOT be treated as meaningful unless it declares:

1. invariant kind;
2. extractor;
3. similarity function;
4. transformation;
5. baseline suite;
6. preservation class;
7. pass rule;
8. failure action.

## 3. RetentionMetricSpec schema

> **Status tag:** normative

```yaml
RetentionMetricSpec:
  metric_id: string
  metric_version: string
  status: research | reference | normative
  invariant_kind: string
  extractor_id: string
  similarity_id: string
  transformation: string
  baseline_suite: [string]
  preservation_class: must_preserve | should_preserve | metadata_only | expected_loss
  pass_rule: string
  failure_action: observe_only | degrade_confidence | block_promotion | bypass
  metric_elasticity_allowed: false
```

## 4. Preservation classes

> **Status tag:** normative

| Class | Meaning | Failure behavior |
|---|---|---|
| `must_preserve` | invariant required for correctness | block or bypass |
| `should_preserve` | useful but not identity-defining | degrade confidence |
| `metadata_only` | retained for audit/provenance | warn if dropped unexpectedly |
| `expected_loss` | loss is declared by profile | no alert unless undeclared |

## 5. Metric elasticity prohibition

> **Status tag:** normative

A metric must not change extractor, similarity function, baseline, or pass rule after observing results. If those change, the metric receives a new version and prior measurements are not comparable without a declared migration.

## 6. Baseline types

> **Status tag:** reference

Useful baselines include:

1. shuffled baseline;
2. malformed baseline;
3. random-family baseline;
4. long-separation baseline;
5. schema-mismatch baseline;
6. collapsed-family baseline;
7. masked-signal baseline;
8. transport-noise baseline;
9. replay-version baseline;
10. migration-shadow baseline.

## 7. Baseline metric catalog

> **Status tag:** reference

```yaml
metrics:
  - metric_id: core-magnitude-retention@v1
    invariant_kind: core_magnitude
    preservation_class: must_preserve
    transformation: family_conversion
    failure_action: block_promotion

  - metric_id: source-family-identity-retention@v1
    invariant_kind: family_identity
    preservation_class: expected_loss
    transformation: family_conversion_without_metadata
    failure_action: observe_only

  - metric_id: witness8-absence-zero-separation@v1
    invariant_kind: absence_zero_distinction
    preservation_class: must_preserve
    transformation: witness8_decode
    failure_action: full_bypass

  - metric_id: edo31-step-pattern-retention@v1
    invariant_kind: modular_interval_pattern
    preservation_class: should_preserve
    transformation: transposition
    failure_action: observe_only

  - metric_id: roughness-weighted-partial-alignment@v1
    invariant_kind: spectral_partial_alignment
    preservation_class: should_preserve
    transformation: spectral_canonicalization
    failure_action: degrade_confidence
```

## 8. Example retained-correlation report

> **Status tag:** reference

```yaml
retention_report:
  report_id: retention-report-example-1
  transformation: hex6_to_refl3
  metrics:
    core-magnitude-retention@v1:
      score: 1.0
      pass: true
    source-family-identity-retention@v1:
      score: expected_loss
      pass: true
  conclusion: conversion_valid_under_declared_expected_loss
```

## 9. What retention is not

> **Status tag:** normative

A retention score is not:

1. proof of arithmetic;
2. proof of physics;
3. proof of quantum coherence;
4. proof of consciousness;
5. proof of semantic truth;
6. authority to change schema;
7. a substitute for replay identity.

## 10. Conformance checklist

> **Status tag:** normative

A retention implementation must:

1. declare extractor and similarity;
2. run at least one baseline;
3. record metric version;
4. avoid metric elasticity;
5. respect preservation classes;
6. emit failure actions;
7. distinguish diagnostic output from policy authority.
