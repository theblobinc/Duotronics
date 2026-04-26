# Duotronic Family Registry v1.4

**Status:** Source-spec baseline candidate  
**Version:** family-registry@v1.4  
**Supersedes:** family-registry@v1.3  
**Document kind:** Normative family and promoted-profile declaration registry plus reference declarations  
**Primary purpose:** Define how DPFC families, representation profiles, learned profiles, adapters, and canonical object families become runtime-referenceable after profile synthesis, validation, replay, and policy approval.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

The Family Registry records families and profile-backed object spaces that may be referenced by runtime systems.

It is not the staging registry for unproven learned profiles. That role belongs to the Profile Synthesis Registry.

A profile or family appears in the Family Registry only when it has reached `reference_profile`, `normative_profile`, `deprecated_profile`, or a policy-approved compatibility alias. Candidate, observed, and research-only records belong in the Profile Synthesis Registry unless the Family Registry explicitly carries them as non-authoritative references.

---

## 2. Relationship to Profile Synthesis Registry

> **Status tag:** normative

The two registries have distinct jobs:

| Registry | Owns | Runtime authority |
|---|---|---|
| Profile Synthesis Registry | observed patterns, candidate witnesses, candidate profiles, research profiles, sandbox profiles, promotion requests, rejection/demotion records | none, audit-only, or sandbox depending on policy |
| Family Registry | promoted family/profile declarations that can be referenced by runtime objects | reference or normative depending on status and policy |

When a learned profile is promoted to `reference_profile` or `normative_profile`, the system must create or update a corresponding Family Registry entry.

The Family Registry entry must include a cross-reference back to:

1. candidate profile record;
2. promotion request;
3. evidence lineage;
4. fixture pack;
5. replay trace set;
6. policy decision;
7. migration plan where applicable.

A Family Registry entry without promotion lineage may exist only as a `manual_reference_record` for documentation and must not influence runtime authority.

---

## 3. Canonical status ladder

> **Status tag:** normative

Family Registry entries use the canonical v1.4 Draft 2 status names:

```text
reference_profile
normative_profile
deprecated_profile
rejected_profile
```

For compatibility, the registry may accept aliases from older documents, but exported machine-readable records must use canonical names.

Alias mapping:

| Older/local alias | Canonical status |
|---|---|
| `reference` | `reference_profile` |
| `normative` | `normative_profile` |
| `normative_reference` | `normative_profile` |
| `deprecated` | `deprecated_profile` |
| `rejected` | `rejected_profile` |

Candidate and research statuses should remain in the Profile Synthesis Registry:

| Pre-promotion status | Owning registry |
|---|---|
| `observed_pattern` | Profile Synthesis Registry |
| `candidate_witness` | Profile Synthesis Registry |
| `candidate_profile` | Profile Synthesis Registry |
| `research_profile` | Profile Synthesis Registry |
| `sandbox_runtime_profile` | Profile Synthesis Registry, with optional non-authoritative Family Registry pointer |

---

## 4. No-bypass rule for manual profiles

> **Status tag:** normative

Human-authored or manually imported profiles do not bypass promotion.

Any profile that can influence runtime authority must have:

1. traceable evidence or rationale lineage;
2. fixture pack;
3. replay trace set;
4. normalizer declaration;
5. bridge declaration where applicable;
6. policy decision;
7. rollback or demotion path.

Hand-authored profiles for testing may exist as `manual_sketch` or `manual_experimental` records in the Profile Synthesis Registry. They may not be entered as `reference_profile` or `normative_profile` in the Family Registry without a promotion record.

---

## 5. Family registry entry schema

```yaml
FamilyRegistryEntry:
  family_registry_entry_id: string
  family_id: string
  family_schema_version: string
  status: reference_profile | normative_profile | deprecated_profile | rejected_profile
  entry_origin: learned_promotion | manual_promotion | migrated_existing | deprecated_legacy | rejected_record
  owner_document: string

  synthesis_cross_reference:
    candidate_profile_id: string | null
    promotion_request_id: string | null
    profile_synthesis_registry_version: string | null
    policy_decision_id: string | null

  object_space:
    kind: symbolic | polygon | glyphic | language | graph | matrix | tensor | adapter | external_numeric | learned | custom
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
    partial_bridge_allowed: true | false

  canonical_storage:
    serializer_id: string
    normalizer_id: string
    identity_fields: []

  conformance:
    fixture_pack_id: string
    replay_trace_set: string
    property_tests: []
    failure_tests: []
    promotion_requirements: []

  governance:
    migration_plan_id: string | null
    rollback_plan_id: string | null
    demotion_policy_id: string
```

---

## 6. Runtime-reference rule

> **Status tag:** normative

Runtime systems may reference only Family Registry entries whose status is:

1. `reference_profile`, if policy permits restricted or normal use;
2. `normative_profile`, if policy permits normal use;
3. `deprecated_profile`, only for replay, migration, or compatibility paths;
4. `rejected_profile`, only as negative fixture or blocked history.

A runtime system must not use a `candidate_profile`, `research_profile`, or `sandbox_runtime_profile` as a normal Family Registry dependency.

---

## 7. Learned profile copy rule

> **Status tag:** normative

When a Profile Synthesis Registry record is promoted to the Family Registry, the copied Family Registry entry must not omit uncertainty, expected loss, bridge partiality, source restrictions, or policy limitations.

Promotion must preserve constraints. It must not launder a weak learned profile into a clean family declaration.

---

## 8. Non-claims

A Family Registry entry declares runtime-referenceable object-space behavior. It does not prove external truth, translation accuracy, source reliability, model correctness, or physical correspondence.
