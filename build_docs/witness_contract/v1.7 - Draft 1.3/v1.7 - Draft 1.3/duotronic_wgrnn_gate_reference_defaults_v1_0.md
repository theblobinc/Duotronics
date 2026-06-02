# Duotronic WG-RNN Gate Reference Defaults

**Status:** Research specification draft  
**Version:** wgrnn-gate-defaults@v1.0  
**Document kind:** Reference profile  
**Primary purpose:** Provide non-normative starting thresholds for write, promotion, quarantine, and decay behavior.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Status

This document is reference, not normative. Its numeric values are starting points for experiments and must be tuned by domain-specific fixtures.

## 2. Reference thresholds

```yaml
WGRNNGateReferenceDefaults:
  write_threshold:
    l2m_slot_creation_cosine_similarity: 0.65
    note: Create or update candidate L2M slot if semantic fit and policy allow.
  promote_threshold:
    similarity_or_support: 0.85
    consistent_witness_count: 3
    note: For runtime memory only; not sufficient for mathematical theorem promotion.
  quarantine_threshold:
    conflict_score: 0.40
    policy_violation: true
    stale_ephemeral_evidence: block_promotion
  l3_meta_control:
    max_delta_per_parameter_per_cycle: 0.02
    max_updates_per_1000_witnesses: 10
  decay:
    per_slot_decay: true
    global_decay_allowed: false
```

## 3. Domain-specific warnings

For mathematical proof witnesses, similarity is not proof. Promotion to theorem requires proof authority, checker identity, trusted proof artifact, policy approval, and replayable verification.

For ephemeral media or game-state witnesses, stale evidence should usually block promotion or reduce authority.

For stable canonical facts, age alone should not accelerate decay.

## 4. Required telemetry

Implementations using these defaults should record:

- gate values before and after clamps;
- reason for clamp;
- threshold profile ID;
- slot lifecycle action;
- replay outcome after promotion;
- quarantine cause.
