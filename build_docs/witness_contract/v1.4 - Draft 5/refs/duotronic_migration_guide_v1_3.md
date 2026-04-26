# Duotronic Migration Guide v1.3

**Status:** Source-spec baseline candidate  
**Version:** migration-guide@v1.3  
**Document kind:** Normative migration and replay guide plus reference workflows  
**Primary purpose:** Define how Duotronic schemas, families, learned profiles, normalizers, bridges, transports, source profiles, retention metrics, policy profiles, and distributed node protocols change safely over time.


## Document status tag key

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this source document. | Must be followed by conforming implementations. |
| `reference` | Schema, example, implementation aid, explanation, or diagnostic guidance. | Useful for implementation; not new semantic authority unless cited by a normative rule. |
| `research` | Experimental candidate, benchmark, learned profile, or metric. | Must remain opt-in until promoted. |
| `future` | Planned work not active in this draft. | Must not be treated as live behavior. |
| `analogy` | Outside-domain comparison or motivation. | Must not be treated as proof. |


## 1. Scope

Migration governs semantic changes to:

1. canonical identity;
2. family interpretation;
3. profile object space;
4. learned profile status;
5. normalizer output;
6. bridge behavior;
7. transport/source validation;
8. evidence bundle structure;
9. model witness schema;
10. retention metric meaning;
11. policy action;
12. replay identity;
13. distributed node protocol behavior.

---

## 2. Semantic-change rule

A change is semantic if it can alter:

1. family value;
2. core magnitude;
3. canonical identity;
4. witness equivalence;
5. profile validity;
6. absence interpretation;
7. numeric-zero interpretation;
8. invalid-state interpretation;
9. source reliability interpretation;
10. bridge preservation;
11. expected-loss declarations;
12. replay output;
13. policy action;
14. ML gating behavior.

Semantic changes require migration and replay checks.

---

## 3. Migration plan schema

```yaml
MigrationPlan:
  migration_id: string
  source_version: string
  target_version: string
  affected_layers: []
  affected_schemas: []
  affected_profiles: []
  affected_bridges: []
  affected_normalizers: []
  affected_policy_modes: []
  must_preserve: []
  expected_loss: []
  incompatible_cases: []
  sentinel_cases: []
  replay_trace_set: string
  shadow_run_required: true
  rollback_plan: string
  promotion_boundary: sequence_boundary_only | maintenance_window | manual_review
  approval_required: true
```

---

## 4. Learned profile migration

Learned profile migration is required when:

1. discovered symbol inventory changes;
2. segmentation rule changes;
3. canonical identity fields change;
4. normalizer output changes;
5. bridge output changes;
6. ambiguity policy changes;
7. expected loss changes;
8. runtime mode changes;
9. source requirements change;
10. profile moves between status levels.

Candidate profiles may be replaced freely while audit-only. Sandbox or higher profiles require migration records.

---

## 5. Replay identity

Replay identity must pin:

1. schema versions;
2. profile versions;
3. normalizer versions;
4. bridge versions;
5. policy snapshot;
6. model versions where model output is part of profile creation;
7. node protocol version;
8. evidence bundle hashes;
9. fixture pack IDs;
10. retrieval/source profiles;
11. random seeds or non-determinism declarations.

---

## 6. Rollback

A rollback plan must identify:

1. prior profile status;
2. prior schema versions;
3. prior normalizer and bridge versions;
4. affected lookup memory records;
5. affected recurrent state;
6. affected model gates;
7. affected search/social source diagnostics;
8. invalidated profile candidates;
9. replacement policy mode.

---

## 7. Non-claims

Migration preserves runtime safety and replayability. It does not prove a profile is externally true.
