# Duotronic Human Review and Escalation Protocol v1.0

**Status:** Source-spec baseline candidate  
**Version:** human-review-escalation-protocol@v1.0  
**Document kind:** Normative human-in-the-loop review, escalation, decision recording, and feedback protocol  
**Primary purpose:** Define how Duotronic systems invoke human review, record human decisions, route action conflicts and policy escalations, and feed human decisions back into policy, witnesses, profiles, replay, and future decision contexts.

---

## 1. Scope

This protocol applies when a Duotronic system requires human judgment, approval, rejection, correction, or escalation.

Typical triggers:

1. action conflict cannot be safely resolved;
2. policy change proposal requires approval;
3. external side effect is requested;
4. profile promotion requires review;
5. purge request requires privacy/legal review;
6. source ambiguity is high;
7. model diversity is insufficient;
8. self-model actor scope is ambiguous;
9. high-speed loop resource violation requires operational review;
10. replay fails or is blocked by purged data;
11. planner proposes irreversible or high-risk action;
12. human review is explicitly required by policy.

---

## 2. Central rule

> **Status tag:** normative

Human review is a governed evidence event, not an informal side channel.

If the system routes to human review, it must create a review request, record the reviewer context and decision, attach the decision to affected objects, and preserve replay/policy impact.

---

## 3. Human review request

```yaml
HumanReviewRequest:
  human_review_request_id: string
  requested_at: string
  requested_by:
    kind: policy | planner | system | human | node | model | custom
    ref: string
  review_reason: action_conflict | policy_change | purge_request | profile_promotion | external_action | actor_scope_ambiguity | source_ambiguity | replay_failure | resource_violation | safety | privacy | custom
  target_refs: []
  target_kinds: []
  decision_context_id: string | null
  action_conflict_id: string | null
  policy_change_proposal_id: string | null
  purge_request_id: string | null
  required_reviewer_role: owner | admin | privacy_reviewer | safety_reviewer | domain_expert | legal | operator | custom
  required_response: approve | reject | choose_option | classify | annotate | request_more_info | custom
  deadline: string | null
  default_if_expired: no_action | reject | audit_only | escalate | custom
  privacy_class: public | internal | restricted | sensitive | mixed
  status: open | assigned | answered | expired | cancelled | escalated
```

---

## 4. Human review packet

The system should show the reviewer only the information needed for the decision.

```yaml
HumanReviewPacket:
  human_review_packet_id: string
  human_review_request_id: string
  included_refs: []
  redacted_refs: []
  summary: string
  options: []
  risks: []
  privacy_notes: []
  policy_notes: []
  recommended_default: string | null
```

Sensitive or purged content must not be included unless policy permits.

---

## 5. Human review decision

```yaml
HumanReviewDecision:
  human_review_decision_id: string
  human_review_request_id: string
  reviewer_ref: string
  reviewer_role: owner | admin | privacy_reviewer | safety_reviewer | domain_expert | legal | operator | custom
  decision_time: string
  decision: approve | reject | choose_option | no_action | audit_only | sandbox | restricted | normal | request_more_info | escalate | custom
  chosen_option_ref: string | null
  rationale: string
  conditions: []
  policy_decision_id: string | null
  creates_policy_change: true | false
  creates_training_or_fixture_signal: true | false
  appeal_or_review_ref: string | null
```

A human decision is itself evidence. It does not automatically override L5 policy unless policy grants that reviewer role such authority.

---

## 6. Feedback into policy and learning

Human decisions may feed back into the system as:

1. policy decisions;
2. profile promotion approvals;
3. profile rejection reasons;
4. action conflict resolutions;
5. purge authorizations;
6. source reliability annotations;
7. fixture labels;
8. model-failure examples;
9. planner outcome examples;
10. red-team cases.

Feedback must be recorded.

```yaml
HumanReviewFeedbackRecord:
  human_review_feedback_id: string
  human_review_decision_id: string
  feedback_targets: []
  feedback_kind: policy_update | fixture_label | profile_annotation | model_failure | action_outcome | source_annotation | purge_authorization | custom
  allowed_use: audit_only | sandbox | restricted | normal
  retention_policy: string
```

---

## 7. Expiration and default behavior

If a human review request expires:

1. external actions default to reject or no-action;
2. policy increases default to reject;
3. profile promotions default to no promotion;
4. purge requests follow privacy/legal policy;
5. action conflicts default to most restrictive policy;
6. ambiguous self-models default to audit-only.

No high-authority path should become allowed because a human failed to respond.

---

## 8. Multi-party review

Some decisions may require multiple reviewers.

```yaml
MultiPartyReviewRule:
  multi_party_review_rule_id: string
  target_kind: policy_change | purge_request | external_action | profile_promotion | custom
  required_roles: []
  quorum_rule: all_required | majority | one_privacy_one_owner | custom
  conflict_rule: any_reject_blocks | majority_wins | l5_decides | custom
```

---

## 9. Audit and replay

Human review records must be replay-visible.

Replay must record:

1. review request ID;
2. review packet version;
3. reviewer role;
4. decision;
5. policy decision;
6. conditions;
7. expiration/default behavior if applicable.

Replay may not expose sensitive content unless policy allows.

---

## 10. Non-claims

This protocol does not define who the human reviewer must be in every deployment. It defines the records and gates required when human review is used.

---

## 11. Global human response timeout policy

> **Status tag:** normative

A human review request may declare its own deadline and expiration behavior. If it does not, the system must apply a global human response timeout policy.

### 11.1 Global policy schema

```yaml
HumanReviewTimeoutPolicy:
  human_review_timeout_policy_id: string
  default_deadline_seconds: integer
  default_if_expired: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
  per_reason_overrides:
    action_conflict:
      deadline_seconds: integer | null
      default_if_expired: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
    policy_change:
      deadline_seconds: integer | null
      default_if_expired: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
    purge_request:
      deadline_seconds: integer | null
      default_if_expired: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
    external_action:
      deadline_seconds: integer | null
      default_if_expired: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
    profile_promotion:
      deadline_seconds: integer | null
      default_if_expired: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
  escalation_policy_ref: string | null
  policy_decision_id: string
```

### 11.2 Timeout resolution

When a `HumanReviewRequest` lacks an explicit `deadline`, the system must compute one from `HumanReviewTimeoutPolicy`.

When a `HumanReviewRequest` lacks an explicit `default_if_expired`, the system must use the global default or the per-reason override.

### 11.3 Expiration event

```yaml
HumanReviewExpirationEvent:
  human_review_expiration_event_id: string
  human_review_request_id: string
  timeout_policy_id: string
  expired_at: string
  applied_default: no_action | reject | audit_only | escalate | most_restrictive_policy | custom
  resulting_policy_decision_id: string | null
  notes: string
```

### 11.4 Safe default

If no timeout policy can be found, high-authority paths must fail closed:

```text
external action -> reject
policy authority increase -> reject
profile promotion -> no promotion
action conflict -> most restrictive policy or no_action
ambiguous actor scope -> audit_only
purge request -> privacy/legal review or most privacy-preserving hold
```
