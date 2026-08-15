# Duotronic Human Review State Machine v1.0

**Status:** Draft 2 normative workflow profile  
**Purpose:** Define concrete human-review workflow mechanics for proof promotion, policy overrides, profile promotion, purge authorization, and high-risk MCP actions.

---

## 1. Ticket lifecycle

```text
opened
-> assigned
-> in_review
-> needs_more_evidence
-> in_review
-> accepted | rejected | escalated | expired | withdrawn
```

Allowed terminal states:

```text
accepted
rejected
expired
withdrawn
superseded
```

---

## 2. ReviewTicket schema

```yaml
HumanReviewTicket:
  ticket_id: string
  ticket_kind: theorem_promotion | profile_promotion | policy_override | purge_authorization | high_risk_action | incident_review | other
  opened_at: string
  opened_by: string
  assigned_to: []
  status: opened | assigned | in_review | needs_more_evidence | accepted | rejected | escalated | expired | withdrawn | superseded
  subject_ref: string
  evidence_refs: []
  policy_refs: []
  risk_level: low | medium | high | critical
  deadline: string | null
  quorum_rule_id: string
```

---

## 3. Reviewer packet

A reviewer must see:

1. proposed status transition;
2. old and new canonical object states;
3. diff of semantic fields;
4. linked evidence and proof witnesses;
5. interpreter runs, if relevant;
6. policy rules that apply;
7. replay status;
8. known contradictions;
9. stale or purge-impacted evidence warnings;
10. structured decision form.

---

## 4. Decision form

```yaml
HumanReviewDecision:
  decision_id: string
  ticket_id: string
  reviewer_id: string
  decision: accept | reject | needs_more_evidence | escalate | abstain
  rationale: string
  evidence_considered: []
  policy_basis: []
  conditions: []
  created_at: string
```

---

## 5. Quorum model

Allowed quorum policies:

```text
single_reviewer
two_person_review
majority
unanimous
designated_arbiter
policy_board
```

High-risk theorem promotions and high-risk external actions should require at least `two_person_review` unless waived by policy.

---

## 6. Contradictory review resolution

If reviews conflict:

```text
conflict_detected
-> escalated
-> arbiter_assigned
-> arbiter_decision
-> accepted | rejected | needs_more_evidence
```

An arbiter decision must cite which review arguments were accepted or rejected.

---

## 7. Audit requirement

Human review decisions are witness-bearing. No review may be an undocumented side channel.

Every review decision must attach to:

1. policy decision;
2. subject object;
3. evidence refs;
4. reviewer identity;
5. timestamp;
6. replay package if action changes authority.
