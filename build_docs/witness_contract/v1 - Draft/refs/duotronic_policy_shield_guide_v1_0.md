# Duotronic Policy Shield Guide v1.0

**Status:** Source-spec baseline candidate  
**Version:** policy-shield@v1.0  
**Document kind:** Normative L5 policy guide plus reference decision tables  
**Primary purpose:** Define how L5 shields runtime operation by enforcing feasibility, bypass modes, rollback authority, migration gates, and promotion boundaries.

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

> **Status tag:** normative

The Policy Shield is the L5 layer. It decides which paths are allowed, degraded, bypassed, rolled back, or blocked. It is not an arithmetic layer and not a normalizer. It is a runtime safety authority.

## 2. L5 hard rules

> **Status tag:** normative

L5 MUST enforce:

1. normal-form-before-trust;
2. transport-before-semantics;
3. no silent family reinterpretation;
4. no schema promotion without migration;
5. bypass as valid behavior;
6. failed canonicalization as a first-class state;
7. replay mismatch blocks promotion;
8. retention metrics require baselines before authority.

## 3. Runtime modes

> **Status tag:** normative

| Mode | Meaning | Lookup | Recurrence | Promotion |
|---|---|---|---|---|
| `normal` | all checks passing | allowed | allowed | allowed by policy |
| `degraded` | warning state | limited | allowed conservative | blocked or limited |
| `family_bypass` | family-sensitive path disabled | generic only | allowed | blocked |
| `transport_bypass` | failed transport path disabled | blocked for frame | no semantic update | blocked |
| `lookup_bypass` | lookup unavailable/unsafe | disabled | allowed without lookup | blocked if dependent |
| `full_bypass` | unsafe semantic path | blocked | blocked or minimal | blocked |

## 4. Decision matrix

> **Status tag:** reference

| Condition | Default mode | Required action |
|---|---|---|
| transport integrity failed | transport_bypass | reject semantic decode |
| absence-zero collision | full_bypass | reject decoder/profile |
| family registry missing | family_bypass | generic handling only |
| normalizer timeout | degraded | bypass affected path |
| replay identity mismatch | full_bypass | block promotion and rollback |
| retention metric lacks baseline | degraded | keep metric observe-only |
| migration plan missing | degraded | block L4 promotion |
| lookup p99 over ceiling | lookup_bypass | disable lookup enrichment |

## 5. Policy profile schema

> **Status tag:** normative

```yaml
policy_profile:
  policy_id: string
  policy_version: string
  status: active | experimental | deprecated
  allowed_modes: [normal, degraded, family_bypass, transport_bypass, lookup_bypass, full_bypass]
  default_mode: normal
  thresholds:
    canonicalization_failure_rate: number
    lookup_timeout_rate: number
    replay_mismatch_rate: number
    transport_reject_rate: number
  actions:
    on_transport_integrity_failed: transport_bypass
    on_absence_zero_collision: full_bypass
    on_replay_mismatch: full_bypass
  rollback:
    rollback_allowed: true
    approval_required: true
```

## 6. Promotion gates

> **Status tag:** normative

L5 must block promotion unless:

1. migration plan exists;
2. replay traces pass;
3. canonical identity is stable;
4. must-preserve invariants hold;
5. failure behavior is defined;
6. rollback plan exists;
7. policy approval is recorded.

## 7. Bypass philosophy

> **Status tag:** reference

Bypass is not failure to implement. Bypass is the mechanism that prevents uncertain, malformed, ambiguous, or untrusted evidence from entering stronger layers. A well-designed Duotronic runtime should degrade cleanly rather than improvise authority.

## 8. Operator record

> **Status tag:** reference

```yaml
policy_event:
  event_id: string
  time: string
  previous_mode: normal
  new_mode: family_bypass
  trigger_failure_code: normalizer_error
  affected_family: refl3
  lookup_allowed: generic_only
  promotion_allowed: false
  rollback_candidate: null
  operator_ack_required: true
```

## 9. Conformance checklist

> **Status tag:** normative

A policy shield implementation must:

1. implement all required modes;
2. treat failed canonicalization as a state;
3. block failed transport semantics;
4. block migration without replay;
5. keep diagnostic metrics non-authoritative unless promoted;
6. emit policy events;
7. support rollback.
