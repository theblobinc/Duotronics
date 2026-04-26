# Duotronic Polygon Family Calculus (DPFC v5.13)

**Status:** Research specification draft  
**Version:** 5.13-standalone-revision  
**Supersedes:** DPFC v5.12  
**Prior supersedes:** DPFC v5.11  
**Document kind:** Normative mathematical and representational core plus bounded implementation and research interfaces  
**Primary purpose:** Define the Duotronic family-native mathematical core, canonical representation discipline, bridge boundaries, export policy, and the rules by which learned representation profiles may connect to the core without redefining it.

---

## Document status tag key

Every major section carries one primary status tag.

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for the active specification. | Conforming implementations must follow it. |
| `reference` | Architecture explanation, examples, algorithms, schemas, or implementation aids. | Useful for implementation, but not itself a semantic rule unless cited by a normative section. |
| `research` | Experimental profile, metric, learned candidate, diagnostic, or benchmark. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as current behavior. |
| `analogy` | Outside-domain comparison or inspiration. | Must not be treated as proof or runtime authority. |

---

## 1. Executive summary

> **Status tag:** reference

DPFC v5.13 defines the mathematical and representational layer of Duotronics.

The core is presence-first. A realized native Duotronic value names something present. Structural absence is not encoded as a native digit. Ordinary zero remains available at declared export and import boundaries. Display geometry, transport encoding, raw witness history, learned model output, and canonical identity are separate layers.

v5.12 adds explicit language for the v1.4 auto-profile learning architecture. Learned profiles may propose new representation families, adapters, normalizers, bridges, glyph inventories, language witnesses, or conversion rules. These proposals do not mutate DPFC. They attach to DPFC only through declared bridge profiles and policy-gated registry staging.

The governing rule is:

```text
representation pattern
-> family or adapter declaration
-> validation
-> deterministic normalizer
-> canonical identity
-> explicit bridge
-> export/import policy
-> witness contract policy gate
```

No learned pattern, neural embedding, search result, social signal, visual cluster, glyph segmentation, or model consensus is DPFC authority by itself.

---

## 2. Design stance

> **Status tag:** normative

The DPFC design stance is:

1. Realized native magnitudes are present objects.
2. Native family words are finite and nonempty unless a specific adapter declares a non-native absence state.
3. No native digit is reserved for absence.
4. Ordinary zero is supported only at declared external boundaries.
5. Origin roles, least realized magnitudes, structural absence, inactive transport rows, invalid payloads, unknown values, and exported zero are distinct states.
6. Canonical identity is the versioned normal form used for equality, hashing, signing, storage, replay, conversion, and promotion.
7. Witness history may be richer than canonical identity.
8. Display geometry may help canonicalization, rendering, debugging, or witness extraction, but display alone does not prove arithmetic.
9. A learned representation profile is research or staging material until it has registry, fixture, replay, migration, and policy support.
10. DPFC is not a theory of all mathematics. It is a disciplined bridge layer for representation families that can declare their semantics precisely enough to be validated and normalized.

---

## 3. Core concepts

> **Status tag:** normative

### 3.1 Realized magnitude

A realized magnitude is a positive present quantity in the DPFC core. It may be written abstractly as `mu_n`, where `n` is a positive index.

The phrase `mu_n` is a specification marker, not a claim that every implementation must expose a literal `mu` object. Implementations may represent core magnitudes with typed positive integers, canonical byte strings, registry-backed IDs, or other deterministic encodings.

### 3.2 Native family word

A native family word is a finite nonempty sequence of symbols from a declared family alphabet.

A conforming family declaration must define:

1. family identifier;
2. family schema version;
3. ordered symbol inventory or object-space definition;
4. valid object rules;
5. deterministic evaluation or bridge rule;
6. deterministic inverse rule where applicable;
7. canonical serializer;
8. canonical normalizer;
9. absence policy;
10. exported-zero policy;
11. invalid-state policy;
12. fixture pack;
13. promotion requirements.

### 3.3 Family value

A family value is the interpreted value of a valid native family word under the declared family semantics.

Family value is not the same as surface spelling. Different surface spellings may normalize to the same canonical family value if the family permits aliases. If aliases are not declared, two surface spellings are different candidate objects until a normalizer proves equivalence.

### 3.4 Canonical family identity

Canonical family identity is the stable identity used for equality, hashing, signing, storage, conversion, and replay.

A canonical identity must pin:

1. family ID;
2. family schema version;
3. normalizer ID and version;
4. serializer ID and version;
5. bridge profile ID where conversion is involved;
6. canonical object bytes or canonical object graph;
7. replay identity version;
8. expected-loss declaration when the object came through a lossy bridge.

### 3.5 Witness history

Witness history may include construction path, raw evidence, model outputs, source references, glyph images, visual geometry, OCR spans, intermediate parses, confidence scores, contradiction records, and search provenance.

Witness history is not canonical identity. It may inform diagnostics, replay, and policy, but it must not silently change equality.

---

## 4. Family declarations

> **Status tag:** normative

A family declaration has this conceptual shape:

```yaml
FamilyDeclaration:
  family_id: string
  family_schema_version: string
  status: sketch | candidate | research_valid | sandbox_runtime | reference | normative | deprecated | rejected
  kind: symbolic | polygon | glyphic | language | graph | matrix | tensor | transport_adapter | external_numeric | learned_adapter | research
  owner_document: string
  object_space:
    surface_modality: text | image | audio | video | mixed | structured
    valid_object_rule: string
    invalid_object_rule: string
  alphabet_or_inventory:
    ordered_symbols: []
    unordered_symbols: []
    learned_clusters: []
    external_registry: string | null
  absence_policy:
    structural_absence: string
    empty_input_policy: reject | absence_if_declared | audit_only
    inactive_transport_policy: not_applicable | token_free_absence | explicit_inactive_row
  zero_policy:
    native_zero: forbidden | allowed_by_adapter | external_only
    export_zero_rule: string | null
  bridge:
    bridge_profile_id: string
    source_to_core: string | null
    source_to_canonical_object: string | null
    inverse_bridge: string | null
  canonicalization:
    normalizer_id: string
    serializer_id: string
    identity_fields: []
    display_only_fields: []
    expected_loss_fields: []
  conformance:
    fixture_pack_id: string
    property_tests: []
    replay_tests: []
    failure_tests: []
  promotion:
    required_evidence: []
    required_policy_gate: string
    migration_required_for_semantic_change: true
```

A family declaration may be hand-authored or auto-proposed. Auto-proposed declarations must start at `candidate` or lower. They cannot start as `reference` or `normative`.

---

## 5. Core bridge rules

> **Status tag:** normative

### 5.1 Simple family bridge

For a simple finite symbolic family, the preferred bridge is:

```text
family word -> family value -> core magnitude
```

For conversion between two such families:

```text
source family -> core magnitude -> target family
```

This prevents ad hoc direct conversion paths from creating silent incompatibilities.

### 5.2 Rich representation bridge

For richer objects, the bridge may be:

```text
source representation -> canonical semantic object
```

or:

```text
source representation -> canonical witness object
```

or:

```text
source representation -> canonical geometry object -> optional core image
```

A glyphic-script profile, English claim/evidence profile, social-source profile, graph profile, matrix profile, or video-derived profile may not have a direct total map into `mu_n`. That is acceptable. DPFC requires the profile to say which canonical object is being produced and which parts, if any, bridge into the positive core.

### 5.3 Lossy bridge

A lossy bridge is allowed only if it declares expected loss.

Examples of expected loss may include:

1. display glyph style;
2. handwriting stroke variation;
3. source ordering that does not affect canonical meaning;
4. unsupported historical spelling variant;
5. uncertain translation reading;
6. nonsemantic markup;
7. platform-specific social metadata;
8. model-internal hidden activations;
9. confidence traces not used for identity.

Unexpected loss must produce degradation, bypass, audit-only status, or rejection.

---

## 6. Export and import boundaries

> **Status tag:** normative

DPFC supports external arithmetic and ordinary numeric zero through explicit import/export policies.

A profile must declare one of:

```text
positive_index_policy
nonnegative_export_policy
signed_scalar_policy
external_float_policy
symbolic_policy
custom_policy
```

For nonnegative export, the conventional shape is:

```text
export(mu_n) = n - 1
```

This does not make `mu_1` absence. It means external systems may use an ordinary zero token at a declared boundary.

A profile that imports external zero must declare whether external `0` maps to:

1. least realized magnitude;
2. explicit numeric zero object in an external adapter;
3. origin role;
4. absence;
5. invalid input.

Only the first three are normally safe. Mapping external zero to absence is dangerous and requires explicit profile-specific justification and policy gating.

---

## 7. Learned representation profiles

> **Status tag:** normative

A learned profile may propose a family or adapter from data.

The proposal is valid only as a candidate until it defines:

1. object space;
2. absence policy;
3. zero policy;
4. invalid-state policy;
5. canonical identity;
6. normalizer;
7. serializer;
8. bridge rule;
9. inverse bridge where applicable;
10. preservation claims;
11. expected-loss claims;
12. fixture pack;
13. replay behavior;
14. contradiction policy;
15. promotion boundary.

A learned profile must not silently override an existing profile. If it claims equivalence to an existing profile, it must provide an equivalence bridge and replay suite.

---

## 8. Example: Roman numeral adapter

> **Status tag:** reference

Roman numerals are a useful first auto-profile target because the object space is small enough to test but rich enough to expose ambiguity.

A Roman numeral adapter may declare:

```yaml
family_id: roman-numeral
kind: symbolic_numeric_adapter
symbols: [I, V, X, L, C, D, M]
native_zero: forbidden
absence_policy: empty_string_reject_or_absence_if_outer_container_declares_absence
normalizer:
  output_mode: canonical_subtractive
bridge:
  source_to_external_integer: roman_parse_value
  external_integer_to_core: declared_import_policy
failure_modes:
  - malformed_reject
  - ambiguous_reject
  - range_reject
```

The profile must distinguish canonical Roman spelling from loose historical variants. Loose variants may be accepted only if the profile declares alias reduction rules and expected loss.

---

## 9. Example: English claim/evidence profile

> **Status tag:** reference

English is not a numeric family. It is a semantic witness environment.

An English profile should produce canonical objects such as:

1. claim witness;
2. entity witness;
3. source witness;
4. quote witness;
5. stance witness;
6. contradiction witness;
7. evidence span witness;
8. temporal assertion witness;
9. uncertainty witness.

The canonical identity of a claim is not the same as the truth of the claim. A normalized claim can be stored, compared, contradicted, supported, or searched without being promoted as true.

---

## 10. Example: glyphic script profile

> **Status tag:** reference

A glyphic script profile should start by preserving visual and source uncertainty.

Possible canonical layers:

```text
image region
-> visual segmentation witness
-> glyph cluster witness
-> candidate sign identity
-> candidate reading
-> candidate semantic role
```

The visual identity can be more stable than the reading. Therefore a conforming glyphic profile should allow a canonical visual witness even when semantic reading is unresolved.

---

## 11. Conformance requirements

> **Status tag:** normative

A conforming DPFC-linked profile must pass tests for:

1. valid examples;
2. invalid examples;
3. malformed input;
4. absence/zero separation;
5. canonical serialization stability;
6. normalizer determinism;
7. replay identity stability;
8. bridge preservation;
9. expected-loss reporting;
10. unexpected-loss detection;
11. migration compatibility;
12. policy failure modes;
13. registry pinning;
14. no silent family reinterpretation.

Profiles that fail these tests may remain as research candidates but must not be promoted into runtime authority.

---

## 12. Non-claims

> **Status tag:** normative

DPFC v5.13 does not claim that:

1. all mathematical systems can be reduced to positive integers;
2. all languages can be fully learned from data;
3. model agreement proves semantic truth;
4. glyphic script segmentation proves translation;
5. social-media consensus proves a claim;
6. search result rank proves evidence quality;
7. display geometry proves arithmetic;
8. neural embeddings are canonical identity;
9. a learned bridge is trustworthy before replay;
10. analogies are external-domain proofs.


---

## 13. Draft 2 registry and glossary alignment

> **Status tag:** normative

DPFC v5.13 adopts `refs/duotronic_glossary_v1_0.md` for shared terms.

When a learned representation profile becomes a DPFC-linked family, its promoted runtime-referenceable entry must appear in the Family Registry with a cross-reference to the Profile Synthesis Registry.

DPFC-linked runtime use requires:

1. profile status `reference_profile` or `normative_profile`;
2. Family Registry entry;
3. normalizer reference;
4. bridge reference where applicable;
5. absence/zero policy;
6. fixture pack;
7. replay trace set;
8. policy decision.

A DPFC-linked profile may remain in `research_profile` or `sandbox_runtime_profile` for experimentation, but it must not be treated as a normal DPFC family until Family Registry handoff is complete.
