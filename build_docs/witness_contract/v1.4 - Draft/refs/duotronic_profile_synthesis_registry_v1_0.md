# Duotronic Profile Synthesis Registry v1.0

**Status:** Source-spec baseline candidate  
**Version:** profile-synthesis-registry@v1.0  
**Document kind:** Normative profile staging and promotion registry plus reference schemas  
**Primary purpose:** Define how candidate profiles, learned profiles, profile promotion requests, sandbox profiles, rejected profiles, and profile migrations are recorded and governed.

---

## 1. Scope

The Profile Synthesis Registry tracks profiles before and during promotion.

It complements the Family Registry. The Family Registry records approved or declared families. The Profile Synthesis Registry records how new profiles are proposed, staged, tested, rejected, demoted, or promoted.

---

## 2. Status ladder

```text
observed_pattern
candidate_witness
candidate_profile
research_profile
sandbox_runtime_profile
reference_profile
normative_profile
deprecated_profile
rejected_profile
```

Only `reference_profile` and `normative_profile` may be treated as stable registry dependencies. `sandbox_runtime_profile` may be used only in policy-approved sandbox paths.

---

## 3. Candidate profile record

```yaml
CandidateProfileRecord:
  candidate_profile_id: string
  proposed_profile_id: string
  profile_kind: symbolic_numeric | natural_language_semantic | glyphic_visual | graph | matrix | tensor | geometry | search_source | social_source | transport_adapter | custom
  created_at: string
  created_by_node_id: string
  source_evidence_ids: []
  model_witness_ids: []
  candidate_witness_ids: []
  proposed_owner_document: string
  object_space_summary: string
  absence_policy: string
  zero_policy: string
  invalid_state_policy: string
  normalizer_candidate_id: string
  bridge_candidate_id: string | null
  fixture_pack_id: string
  replay_trace_set_id: string
  adjudication_record_ids: []
  current_status: string
  current_policy_mode: audit_only | sandbox | restricted | normal | blocked
```

---

## 4. Promotion request

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
  requested_by: human | system | node | model_assisted
  approval_required: true
```

---

## 5. Rejection record

```yaml
ProfileRejectionRecord:
  rejection_id: string
  candidate_profile_id: string
  rejected_at: string
  rejected_by_policy_gate: string
  reasons: []
  reusable_evidence_ids: []
  blocked_reuse:
    profile_id: string
    until_condition: string
```

Rejected profiles may still contribute negative fixtures.

---

## 6. Demotion record

```yaml
ProfileDemotionRecord:
  demotion_id: string
  profile_id: string
  prior_status: string
  new_status: string
  trigger:
    kind: replay_failure | contradiction | policy_change | migration_failure | normalizer_instability | bridge_failure | manual_review
    ref: string
  affected_runtime_paths: []
  rollback_plan_id: string
```

Demotion must propagate to lookup memory, recurrent state, and any dependent profiles.

---

## 7. Dependency graph

The registry should maintain dependencies:

1. profile depends on schema;
2. profile depends on normalizer;
3. profile depends on bridge;
4. profile depends on fixture pack;
5. profile depends on policy gate;
6. profile depends on migration plan;
7. profile depends on source evidence class;
8. profile depends on model family or model witness class.

A dependency change may force migration or demotion.

---

## 8. Machine-readable index

The registry should be exportable as:

```text
profile_synthesis_registry.yaml
profile_dependency_graph.json
profile_status_index.json
profile_fixture_manifest.json
```

---

## 9. Non-claims

This registry does not judge truth. It records profile lifecycle, evidence, decisions, dependencies, and authority status.
