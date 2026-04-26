# Duotronic Normalizer Profiles v1.3

**Status:** Source-spec baseline candidate  
**Version:** normalizer-profiles@v1.3  
**Document kind:** Normative normalizer contract plus reference profile schemas  
**Primary purpose:** Define deterministic normal-form construction for family objects, witness keys, geometry paths, learned profiles, source evidence records, model witnesses, bridge results, replay identity, and search/social claim objects.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

A normalizer constructs canonical identity.

Normalizers apply to:

1. DPFC family objects;
2. symbolic numerals;
3. polygon or geometry objects;
4. glyphic visual clusters;
5. English or natural-language claim witnesses;
6. source evidence records;
7. model witness records;
8. candidate profile records;
9. bridge results;
10. replay records.

A normalizer does not decide truth. It decides stable identity under declared rules.

---

## 2. Hard rule

A normalizer must be deterministic for a given input object, schema version, normalizer version, registry snapshot, and policy mode.

If determinism cannot be guaranteed, the result must be audit-only, degraded, or rejected.

---

## 3. Normalizer profile schema

```yaml
NormalizerProfile:
  normalizer_id: string
  normalizer_version: string
  status: candidate | research_valid | sandbox_runtime | reference | normative | deprecated | rejected
  owner_document: string
  input_schema_id: string
  output_schema_id: string
  deterministic: true
  registry_dependencies: []
  identity_fields: []
  display_only_fields: []
  provenance_fields: []
  uncertainty_fields: []
  expected_loss_fields: []
  invalid_states: []
  ambiguity_policy: reject | preserve_uncertainty | canonical_choice | audit_only
  absence_policy: string
  zero_policy: string
  serialization:
    serializer_id: string
    byte_stable: true
  conformance:
    fixture_pack_id: string
    replay_trace_set: string
    property_tests: []
```

---

## 4. Learned normalizers

A learned normalizer is a proposed normalizer generated from observed evidence or model outputs.

A learned normalizer must:

1. declare its training or evidence lineage;
2. pin model witnesses that proposed it;
3. produce stable output on fixtures;
4. preserve ambiguity if it cannot resolve it;
5. reject malformed inputs rather than inventing meaning;
6. avoid collapsing absence, zero, invalidity, unknown, and empty transport;
7. declare all expected loss;
8. run replay before promotion.

Learned normalizers start as `candidate` or `research_valid`.

---

## 5. Canonicalization examples

### 5.1 Roman numeral

Surface:

```text
xliv
```

Possible normalized identity:

```yaml
profile_id: roman-numeral@0.1
canonical_surface: XLIV
external_value: 44
zero_policy: no_native_zero
```

### 5.2 English claim witness

Surface:

```text
"The engine supports Roman numerals."
```

Possible normalized identity:

```yaml
claim_hash: sha256(normalized_claim_text + entity_profile + source_span)
modality: asserted
truth_status: not_decided
```

### 5.3 Glyphic visual witness

Surface:

```text
image region coordinates + source image hash
```

Possible normalized identity:

```yaml
visual_region_hash: string
segmentation_profile_id: string
glyph_cluster_id: string
reading_status: unresolved
```

---

## 6. Failure states

```text
normalizer_missing
normalizer_version_mismatch
normalizer_timeout
non_deterministic_output
identity_field_missing
display_field_used_as_identity
provenance_required_but_missing
ambiguity_not_preserved
absence_zero_collision
invalid_state_collision
serialization_unstable
```

---

## 7. Non-claims

A normalizer creates stable representation. It does not prove semantics, truth, translation, source reliability, or model correctness.
