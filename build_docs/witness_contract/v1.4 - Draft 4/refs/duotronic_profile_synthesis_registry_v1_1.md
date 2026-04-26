# Duotronic Profile Synthesis Registry v1.1

**Status:** Source-spec baseline candidate  
**Version:** profile-synthesis-registry@v1.1  
**Supersedes:** profile-synthesis-registry@v1.0  
**Document kind:** Normative profile staging and promotion registry plus reference schemas  
**Primary purpose:** Define how observed patterns, candidate witnesses, candidate profiles, learned profiles, profile promotion requests, sandbox profiles, rejected profiles, demoted profiles, and Family Registry handoff records are recorded and governed.

---

## 1. Scope

The Profile Synthesis Registry tracks profiles before and during promotion.

It complements the Family Registry. The Profile Synthesis Registry owns the profile birth and promotion path. The Family Registry owns promoted runtime-referenceable entries.

---

## 2. Canonical status ladder

> **Status tag:** normative

The canonical v1.4 Draft 2 profile status ladder is:

```text
observed_pattern
-> candidate_witness
-> candidate_profile
-> research_profile
-> sandbox_runtime_profile
-> reference_profile
-> normative_profile
-> deprecated_profile
-> rejected_profile
```

All machine-readable records should use these names.

---

## 3. Status meanings

| Status | Meaning | Allowed use | Owning registry |
|---|---|---|---|
| `observed_pattern` | recurring unstructured pattern | clustering and evidence only | Profile Synthesis |
| `candidate_witness` | structured hypothesis | testing and comparison | Profile Synthesis |
| `candidate_profile` | proposed object space, normalizer, bridge, fixtures | offline testing | Profile Synthesis |
| `research_profile` | documented, testable, non-authoritative profile | research and audit-only | Profile Synthesis |
| `sandbox_runtime_profile` | policy-approved isolated runtime experiment | sandbox only | Profile Synthesis, optional Family pointer |
| `reference_profile` | supported implementation profile | restricted or normal by policy | Family Registry with synthesis cross-reference |
| `normative_profile` | trusted profile under current contract | normal by policy | Family Registry with synthesis cross-reference |
| `deprecated_profile` | no new normal use | replay/migration only | Family Registry and/or Synthesis history |
| `rejected_profile` | failed or unsafe profile | negative fixtures / blocked reuse | Synthesis history, optional Family rejected record |

---

## 4. Manual and automatic profile rule

> **Status tag:** normative

The promotion ladder applies to both auto-generated and hand-authored profiles.

A human may author a profile candidate directly, but if the profile can influence runtime authority it must still pass through:

1. candidate profile record;
2. fixture pack;
3. normalizer declaration;
4. bridge declaration where applicable;
5. replay trace set;
6. retention diagnostics where applicable;
7. policy review;
8. promotion request;
9. Family Registry handoff for reference or normative status.

Manual authorship may supply rationale; it is not a trust bypass.

---

## 5. Candidate profile record

```yaml
CandidateProfileRecord:
  candidate_profile_id: string
  proposed_profile_id: string
  profile_kind: symbolic_numeric | natural_language_semantic | glyphic_visual | graph | matrix | tensor | geometry | search_source | social_source | transport_adapter | custom
  status: observed_pattern | candidate_witness | candidate_profile | research_profile | sandbox_runtime_profile | rejected_profile
  origin: learned | manual | imported | migrated | hybrid
  created_at: string
  created_by_node_id: string | null
  created_by_human_id: string | null
  source_evidence_ids: []
  model_witness_ids: []
  candidate_witness_ids: []
  proposed_owner_document: string

  proposed_object_space:
    object_space_schema_id: string | null
    inline_definition: object | null
    valid_examples: []
    invalid_examples: []
    ambiguity_examples: []
    minimum_fixture_count:
      valid: integer
      invalid: integer
      ambiguity: integer

  profile_behavior:
    absence_policy: string
    zero_policy: string
    invalid_state_policy: string
    ambiguity_policy: reject | preserve_uncertainty | audit_only | custom
    identity_fields: []
    display_only_fields: []
    expected_loss: []
    prohibited_loss: []

  implementation_candidates:
    normalizer_candidate_id: string
    bridge_candidate_id: string | null
    serializer_candidate_id: string | null

  conformance:
    fixture_pack_id: string
    replay_trace_set_id: string
    property_tests: []
    failure_tests: []
    fixture_minimum_met: true | false

  adjudication:
    adjudication_record_ids: []
    contradiction_record_ids: []
    unresolved_ambiguities: []

  policy:
    current_policy_mode: audit_only | sandbox | restricted | normal | blocked
    learning_mode_used: blocked | audit_only | sandbox | active
    required_policy_gate: string
```

---

## 6. Minimum fixture rule

> **Status tag:** normative

Every `candidate_profile` must include at least:

1. one valid example;
2. one invalid example;
3. one ambiguity or near-miss example, unless the profile explicitly declares that no ambiguity class is known yet and remains `audit_only`.

A candidate profile without this minimum may remain an `observed_pattern` or `candidate_witness`, but it must not become a `research_profile`.

---

## 7. Promotion request

```yaml
ProfilePromotionRequest:
  promotion_request_id: string
  candidate_profile_id: string
  requested_target_status: research_profile | sandbox_runtime_profile | reference_profile | normative_profile
  rationale: string
  evidence_summary: string
  fixture_pack_id: string
  replay_trace_set_id: string
  retention_metric_ids: []
  migration_plan_id: string | null
  rollback_plan_id: string
  risk_assessment_id: string
  policy_gate_id: string
  family_registry_handoff_required: true | false
  requested_by: human | system | node | model_assisted
  approval_required: true
```

---

## 8. Family Registry handoff

> **Status tag:** normative

Promotion to `reference_profile` or `normative_profile` requires a Family Registry handoff.

```yaml
FamilyRegistryHandoff:
  handoff_id: string
  promotion_request_id: string
  candidate_profile_id: string
  target_family_registry_entry_id: string
  copied_constraints:
    absence_policy: true
    zero_policy: true
    invalid_state_policy: true
    expected_loss: true
    prohibited_loss: true
    bridge_partiality: true
    source_restrictions: true
    runtime_policy_limits: true
  policy_decision_id: string
```

If handoff fails, promotion fails.

---

## 9. Rejection and demotion

Rejected profiles may still contribute:

1. negative fixtures;
2. red-team cases;
3. contradiction examples;
4. migration sentinel cases.

Demoted profiles must update dependent Family Registry entries, lookup-memory records, recurrent-state permissions, and ML gating policy.

---

## 10. Non-claims

This registry records profile lifecycle. It does not decide truth and does not replace the Family Registry for promoted runtime dependencies.
