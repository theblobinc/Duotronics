# Duotronic Migration Guide v1.0

**Status:** Source-spec baseline candidate  
**Version:** migration-guide@v1.0  
**Document kind:** Normative migration and replay guide plus reference workflows  
**Primary purpose:** Define how Duotronic schemas, families, normalizers, transports, retention metrics, and policy profiles change safely over time.

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

Migration governs semantic changes to canonical identity, family interpretation, normalizer output, transport validation, retention meaning, policy action, and replay identity.

## 2. Semantic-change rule

> **Status tag:** normative

A change is semantic if it can alter:

1. family value;
2. core magnitude;
3. successor behavior;
4. conversion behavior;
5. canonical identity;
6. absence/numeric-zero interpretation;
7. witness equivalence;
8. geometry canonicalization;
9. expected-loss declarations;
10. export arithmetic;
11. replay output;
12. policy action.

Semantic changes require migration and replay checks.

## 3. Migration plan schema

> **Status tag:** normative

```yaml
MigrationPlan:
  migration_id: string
  source_version: string
  target_version: string
  affected_layers: [string]
  affected_schemas: [string]
  must_preserve: [string]
  expected_loss: [string]
  incompatible_cases: [string]
  sentinel_cases: [string]
  replay_trace_set: [string]
  shadow_run_required: true
  rollback_plan: string
  promotion_boundary: sequence_boundary_only
  approval_required: true
```

## 4. Replay identity

> **Status tag:** normative

Replay identity must pin:

1. input hash;
2. transport profile version;
3. schema versions;
4. family registry version;
5. geometry registry version;
6. normalizer versions;
7. serializer versions;
8. policy shield version;
9. retention metric versions;
10. floating-point profile when relevant;
11. deterministic seed when relevant;
12. expected normal-form hash.

## 5. Migration workflow

> **Status tag:** reference

```text
proposal
-> classify change
-> write migration plan
-> build sentinel cases
-> shadow canonicalization
-> replay old traces
-> compare must-preserve invariants
-> identify expected losses
-> policy review
-> staged rollout
-> monitor telemetry
-> promote or rollback
```

## 6. Dual-read/single-write

> **Status tag:** reference

During migration, an implementation may read both old and new forms while writing only the new form after validation. Dual-read must not allow ambiguous old forms to regain authority.

## 7. Shadow canonicalization

> **Status tag:** reference

Shadow canonicalization runs candidate normalizers without changing authoritative state. It records differences, retention loss, failure codes, and replay mismatches. L4 may propose promotion only after shadow results pass policy gates.

## 8. Migration rejection conditions

> **Status tag:** normative

A migration must be rejected if:

1. must-preserve invariants fail;
2. replay normal forms mismatch beyond policy;
3. absence collapses into numeric zero;
4. transport validation is weakened silently;
5. normalizer failures are hidden;
6. expected losses are undeclared;
7. rollback plan is missing;
8. policy approval is missing.

## 9. Example migration

> **Status tag:** reference

```yaml
MigrationPlan:
  migration_id: hex6-normalizer-v1-to-v2
  source_version: simple-bijective-word-normalizer@v1
  target_version: simple-bijective-word-normalizer@v2
  affected_layers: [family_registry, normalizer_registry, replay]
  must_preserve: [core_magnitude, canonical_digit_ordinals]
  expected_loss: [legacy_display_spacing]
  sentinel_cases: [hex6_h1_h4, hex6_h6_carry, invalid_digit]
  replay_trace_set: [dpfc-core-golden-v1]
  rollback_plan: restore_v1_registry_snapshot
  promotion_boundary: sequence_boundary_only
  approval_required: true
```

## 10. Conformance checklist

> **Status tag:** normative

A migration process must:

1. classify changes;
2. write migration plans;
3. run sentinel fixtures;
4. run replay traces;
5. compare must-preserve invariants;
6. declare expected losses;
7. require policy approval;
8. maintain rollback.
