# Duotronic Specification Governance v1.0

**Status:** normative corpus governance contract  
**Version:** specification-governance@v1.0

## 1. Version classes

```text
major: changes authority boundaries or incompatible canonical identity
minor: adds documents, object kinds, profiles, or optional features
patch: clarifies wording without changing conformance behavior
errata: fixes mistake with explicit record
```

## 2. Draft ladder

```text
working_note
-> draft_1
-> draft_2
-> release_candidate
-> reference_spec
-> normative_spec
-> deprecated
-> retired
```

## 3. Change control

A change affecting any of these requires a corpus review record:

1. mathematical canon object identity;
2. witness trust path;
3. policy engine behavior;
4. proof/conjecture status ladder;
5. storage authority;
6. language/runtime roles;
7. security model;
8. migration or replay behavior.

## 4. RFC record

```yaml
SpecChangeRequest:
  scr_id: string
  title: string
  affected_documents: []
  change_kind: major | minor | patch | errata
  rationale: string
  compatibility_impact: string
  replay_impact: string
  security_impact: string
  migration_plan: string
  decision: proposed | accepted | rejected | superseded
```

## 5. Deprecation lifecycle

```text
active
-> deprecated_with_replacement
-> blocked_for_new_writes
-> replay_only
-> retired
```

Deprecated objects must remain readable for replay until a purge or retention policy says otherwise.

## 6. Authority to approve

Machine-learning model output, search results, social consensus, or interpreter output may propose changes. They cannot approve changes. Approval requires the configured governance principal or human review workflow.

## 7. License

The corpus package includes `LICENSE.md`. Code generated from the corpus may use a separate software license. Specification text and implementation source should not be conflated.

---

## Conformance note

This document is part of the v1.6 Draft 1 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
