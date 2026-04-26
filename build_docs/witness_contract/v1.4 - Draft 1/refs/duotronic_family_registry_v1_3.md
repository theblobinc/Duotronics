# Duotronic Family Registry v1.3

**Status:** Source-spec baseline candidate  
**Version:** family-registry@v1.3  
**Document kind:** Normative family and profile declaration registry plus reference declarations  
**Primary purpose:** Define how DPFC families, learned representation profiles, adapters, and canonical object families are declared, validated, normalized, serialized, converted, deprecated, promoted, and rejected.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

The Family Registry governs declared families and profile-backed object spaces used by DPFC and the Witness Contract.

A family or profile entry is required before a family-sensitive or profile-sensitive witness object may become authoritative.

---

## 2. Family entry schema

```yaml
FamilyRegistryEntry:
  family_id: string
  family_schema_version: string
  status: sketch | candidate | experimental | research_valid | sandbox_runtime | reference | normative | deprecated | rejected
  kind: symbolic | polygon | glyphic | language | graph | matrix | tensor | adapter | external_numeric | learned
  owner_document: string

  object_space:
    modality: text | image | audio | video | mixed | structured
    valid_object_rule: string
    invalid_object_rule: string
    ambiguity_policy: reject | preserve | audit_only | custom

  alphabet_or_inventory:
    ordered_symbols: []
    learned_clusters: []
    external_inventory_ref: string | null

  absence_policy:
    structural_absence: string
    empty_input: reject | absence_if_declared | audit_only
    inactive_transport: not_applicable | token_free_absence | explicit_inactive

  zero_policy:
    native_zero: forbidden | allowed | external_only
    ordinary_zero_boundary: string | null

  bridge:
    bridge_profile_id: string | null
    core_bridge: string | null
    inverse_bridge: string | null

  canonical_storage:
    serializer_id: string
    normalizer_id: string
    identity_fields: []

  conformance:
    fixture_pack_id: string
    replay_trace_set: string
    promotion_requirements: []
```

---

## 3. Status requirements

| Status | Meaning | Runtime authority |
|---|---|---|
| sketch | human or system idea | none |
| candidate | proposed from evidence | none |
| experimental | manually or automatically tested in research | none or audit-only |
| research_valid | fixtures pass for research | sandbox only |
| sandbox_runtime | approved isolated runtime experiments | sandbox |
| reference | supported implementation path | restricted or normal by policy |
| normative | trusted under current contract | normal |
| deprecated | no new use except migration/replay | limited |
| rejected | failed or unsafe | blocked |

---

## 4. Learned family rule

Auto-learned families must start as `candidate`.

They require:

1. evidence bundles;
2. model witness lineage;
3. candidate witness lineage;
4. generated fixtures;
5. replay trace set;
6. normalizer candidate;
7. bridge candidate;
8. absence/zero policy;
9. policy gate.

They may not be promoted directly to `reference` or `normative`.

---

## 5. Baseline reference families

v1.4 should include or develop reference entries for:

1. DPFC positive core;
2. symbolic finite families;
3. pronic-centered polygon family;
4. external nonnegative integer adapter;
5. Roman numeral adapter;
6. English claim/evidence semantic profile;
7. glyphic visual-semantic research profile.

---

## 6. Non-claims

A Family Registry entry declares object-space behavior. It does not prove external truth, translation accuracy, source reliability, or model correctness.
