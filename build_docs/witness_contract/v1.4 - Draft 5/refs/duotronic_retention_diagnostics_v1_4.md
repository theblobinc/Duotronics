# Duotronic Retention Diagnostics v1.4

**Status:** Source-spec baseline candidate  
**Version:** retention-diagnostics@v1.4  
**Supersedes:** retention-diagnostics@v1.3  
**Document kind:** Normative diagnostics contract plus reference metrics  
**Primary purpose:** Define how to measure whether declared invariants survive canonicalization, representation bridges, model inference, profile synthesis, search/social ingestion, replay, migration, and policy-controlled transformations without overclaiming proof.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

Retention diagnostics measure preservation.

They apply to:

1. DPFC family conversions;
2. bridge results;
3. normalizer output;
4. learned profile candidates;
5. model witness extraction;
6. source evidence ingestion;
7. search/social claim extraction;
8. distributed node adjudication;
9. replay behavior;
10. migration behavior.

---

## 2. Metric discipline rule

A retention metric requires:

1. metric ID;
2. extractor;
3. input profile;
4. output profile;
5. invariant being measured;
6. baseline suite;
7. pass rule;
8. failure action;
9. policy authority if it affects runtime.

A metric without baseline is observe-only.

---

## 3. Retention metric schema

```yaml
RetentionMetricSpec:
  metric_id: string
  metric_version: string
  status: candidate | research_valid | reference | normative | deprecated | rejected
  measures: value | identity | structure | source | claim | contradiction | uncertainty | replay | bridge | normalizer | profile
  input_profile_id: string
  output_profile_id: string
  extractor_id: string
  similarity_function: string
  baseline_suite_id: string
  pass_rule: string
  failure_action: observe | audit_only | degrade | bypass | reject | rollback
  policy_gate_required: string | null
```

---

## 4. v1.4 metric classes

| Metric class | Question |
|---|---|
| bridge preservation | Did source-to-target preserve required invariants? |
| expected-loss compliance | Was all loss declared? |
| normalizer stability | Did canonical output stay stable across replay? |
| model agreement | Do model witnesses agree on the target field? |
| contradiction density | How often do sources contradict the candidate? |
| source diversity | Are supporting sources independent enough? |
| profile utility | Does the profile parse new examples better than baseline? |
| replay stability | Can the profile synthesis be reproduced? |
| uncertainty preservation | Did the system preserve ambiguity instead of collapsing it? |
| gate safety | Did witness-gated ML behavior stay within policy? |

---

## 5. Failure actions

A metric may trigger:

1. continue observing;
2. audit-only;
3. degrade runtime mode;
4. bypass profile;
5. block promotion;
6. require more fixtures;
7. require human review;
8. demote profile;
9. rollback migration.

---

## 6. Non-claims

A retention metric is not proof. It is an engineering diagnostic unless promoted by policy.


---

## 7. Candidate metric baseline exception

> **Status tag:** normative

Draft 2 allows new metrics to exist before baselines are complete, but restricts their authority.

A metric may declare:

```yaml
baseline_suite_id: null
```

only when its status is:

```text
candidate
research
research_profile
```

A metric with no baseline is observe-only. It must not influence:

1. runtime authority;
2. profile promotion;
3. model gating;
4. source reliability authority;
5. bridge approval;
6. normalizer approval;
7. migration approval.

Before promotion to `reference` or `normative`, the metric must declare:

1. baseline suite ID;
2. baseline construction method;
3. pass rule;
4. failure action;
5. policy authority.

### 7.1 Updated baseline rule

| Metric status | Baseline required? | Authority |
|---|---|---|
| `candidate` | no | observe only |
| `research` / `research_profile` | no, but strongly recommended | audit-only |
| `sandbox_runtime_profile` | yes unless L5 grants sandbox exception | sandbox only |
| `reference_profile` | yes | restricted/normal by policy |
| `normative_profile` | yes | normal by policy |
