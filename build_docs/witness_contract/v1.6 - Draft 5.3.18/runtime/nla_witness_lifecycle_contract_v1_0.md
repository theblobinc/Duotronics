# NLA Witness Lifecycle Contract v1.0

Status: active Draft 5 lifecycle contract.

## Lifecycle states

```text
requested
captured
verbalized
scored
accepted
accepted_single_use_only
diagnostic_only
unscored_diagnostic
quarantined
human_review_pending
human_review_accepted
human_review_rejected
promotable
promoted_to_meta
promoted_to_hyper
expired
failed
```

## State transitions

```text
requested -> captured
captured -> verbalized
verbalized -> scored
scored -> accepted | quarantined | diagnostic_only | failed
accepted -> human_review_pending | accepted_single_use_only | promotable | expired
promotable -> promoted_to_meta
promoted_to_meta -> promoted_to_hyper
any nonterminal -> failed
any accepted state -> expired
```

## Minimum state fields

```yaml
NlaLifecycle:
  current_state: string
  previous_state: string | null
  transition_reason: string
  transitioned_at: timestamp
  actor: system | operator | test | migration
  review_ref: string | null
  expiry_at: timestamp | null
```

## Expiry

NLA witnesses must expire by default unless retained as fixture, audit artifact,
or release artifact. Expiry removes raw vector references but may retain digest,
metrics, and explanation if policy allows.

## Human review

Human review is mandatory when:

1. The explanation concerns hidden intent, deception, evaluation awareness, or
   policy-relevant reward reasoning.
2. The witness is proposed for Meta or Hyper Object promotion.
3. The witness might be shown in a user-facing report.
4. The witness conflicts with direct runtime logs.
5. The witness would influence an incident response.

## Audit trail

Every state transition must be append-only and reference the previous state.
Deletion or mutation of past lifecycle records is not allowed except through a
redaction event that preserves digest and reason.

## Display rules

Operator UI must display lifecycle state and fidelity status next to every NLA
explanation. A low-fidelity explanation must be visibly marked as such.
