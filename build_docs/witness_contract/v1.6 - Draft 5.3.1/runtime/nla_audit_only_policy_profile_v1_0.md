# NLA Audit-Only Policy Profile v1.0

Status: active Draft 5 policy profile.

## Default mode

Draft 5 sets the NLA system to audit-only mode.

```yaml
nla_policy_mode: audit_only
may_store_witness: true
may_display_to_operator: true
may_route_human_review: true
may_support_diagnostics: true
may_support_replay: true
may_write_user_memory: false
may_write_system_memory: false
may_change_policy_authority: false
may_shape_assistant_response: false
may_trigger_mutation: false
may_execute_tools: false
```

## Rationale

NLA explanations may be useful and informative, but they are generated
interpretability artifacts. They must not be allowed to become an unreviewed
source of memory, authority, or behavioral control.

## Allowed uses

1. Operator diagnostics.
2. Offline audit reports.
3. Test fixture scoring.
4. Replay comparison.
5. Human-review triage.
6. Base Object creation with audit-only flags.
7. Meta/Hyper Object proposal after gates.

## Forbidden uses in Draft 5

1. Direct user memory write.
2. Direct policy score change.
3. Direct refusal/allow decision.
4. Automated mutation approval.
5. Tool execution.
6. Silent prompt injection into user-facing model context.
7. Claiming hidden intent as fact.

## Required UI/consumer warning

Any consumer that displays NLA text must include equivalent semantics to:

```text
This is an NLA explanation of an activation vector. It is evidence scored by
reconstruction and replay gates, not privileged truth about model intent.
```

## Escalation path

Changing NLA from audit-only to advisory or authoritative mode requires a future
contract revision with:

1. Runtime validation evidence.
2. Security review.
3. Human review process.
4. Abuse-case tests.
5. Rollback mechanism.
6. Explicit governance approval.
