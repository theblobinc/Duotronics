# NLA WG-RNN Acceptance Matrix v1.0

Status: active Draft 5 validation matrix.

## Acceptance levels

| Level | Name | Meaning |
|---|---|---|
| A0 | Contract present | Schema and docs exist |
| A1 | Fixture capable | Offline fixtures validate |
| A2 | Runtime diagnostic | Runtime can create audit-only witnesses |
| A3 | Replay verified | Witnesses replay with stable metrics |
| A4 | Human-review integrated | Review workflow records decisions |
| A5 | Release verified | Release bundle contains complete evidence |

Draft 5 zip reaches A0 by definition. Later implementation work must prove A1+
with runtime evidence.

## Required acceptance cases

| Case | Requirement | Pass condition |
|---|---|---|
| schema_valid | NLA witness validates against schema | JSON schema validation passes |
| capture_valid | Activation capture records provenance | required fields present |
| sidecar_valid | AV/AR sidecar digests recorded | digest present and checked |
| av_parse_valid | Explanation parser works | tags parsed or diagnostic status recorded |
| ar_score_valid | AR score computed | MSE/cosine present or AR unavailable recorded |
| fidelity_accept | High-fidelity witness accepted | lifecycle `accepted` |
| fidelity_quarantine | Low-fidelity witness quarantined | lifecycle `quarantined` |
| unsupported_backend | Backend without hidden states fails closed | no accepted witness |
| no_memory_write | NLA cannot write memory | policy flag false and tests pass |
| no_policy_escalation | NLA cannot alter authority | policy flag false and tests pass |
| human_review | Sensitive explanation routes to review | review pending/accepted/rejected recorded |
| replay | Fixture replays to similar score | replay_valid true |

## Sensitive explanation categories

Human review is required if explanation text or classifier labels indicate:

1. hidden intent
2. deception
3. evaluation awareness
4. reward hacking
5. tool misreporting
6. policy bypass
7. private user inference
8. memory write temptation
9. self-modification or mutation intent
10. contradiction with direct logs

## Release gate

A release may claim NLA support only when it provides:

```yaml
nla_release_evidence:
  schema_tests_passed: true
  fixture_tests_passed: true
  runtime_smoke_passed: true
  unsupported_backend_tested: true
  low_fidelity_quarantine_tested: true
  policy_non_escalation_tested: true
  human_review_tested: true
  replay_bundle_present: true
```
