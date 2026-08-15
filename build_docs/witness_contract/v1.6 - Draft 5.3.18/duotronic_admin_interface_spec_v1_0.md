# Duotronic Admin Interface Specification v1.0

**Status:** reference interface contract with normative authority boundaries  
**Version:** admin-interface@v1.0

## 1. Purpose

The admin interface lets authorized operators inspect corpus state, witnesses, contradictions, policy decisions, interpreter runs, promotion requests, replay packages, SRNN tasks, and MCP endpoint observations.

## 2. Required surfaces

1. CLI for automation and emergency use.
2. Dashboard for review queues and operational health.
3. API endpoints for integration.

## 3. CLI commands

```text
duotronic status
duotronic witness get <id>
duotronic math claim get <id>
duotronic policy decision get <id>
duotronic review queue
duotronic review decide <id> --decision approve|reject|audit-only
duotronic replay verify <package_id>
duotronic interpreter run <file> --language python|julia|lisp
duotronic srnn job get <job_id>
duotronic mcp query <endpoint_profile> <method>
duotronic migration report
```

## 4. Dashboard panels

```text
system health
policy decisions
human review queue
mathematical claim status transitions
conjecture/theorem promotion queue
interpreter and proof runs
SRNN oracle jobs
MCP endpoint observations
contradictions and disputes
replay verification
purge and retention events
```

## 5. Review packet

```yaml
HumanReviewPacket:
  review_id: string
  target_kind: string
  target_ref: string
  summary: string
  evidence_refs: []
  contradictions: []
  policy_context: object
  recommended_actions: []
  redactions_applied: []
```

## 6. Authority boundary

Admin UI actions are not side channels. Every approval, rejection, override, or promotion must create a `HumanReviewDecision`, `PolicyDecision`, and audit event.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
