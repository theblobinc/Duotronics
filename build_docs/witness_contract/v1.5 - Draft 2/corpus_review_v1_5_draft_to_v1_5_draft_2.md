# Corpus Review: v1.5 Draft to v1.5 Draft 2

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.5-draft-to-v1.5-draft-2  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record the addition of the Witness-Gated Recurrent Cell research profile to the v1.5 distributed Duotronic corpus.

---

## 1. Review driver

v1.5 added distributed cluster operation: resource witnesses, DBP inter-node profiles, node federation, and task delegation.

Draft 2 adds the next recurrent-memory layer:

```text
Witness-Gated Recurrent Cell
```

The WG-RNN uses canonical witness features as memory-control signals.

---

## 2. New source spec

Added:

```text
refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md
```

---

## 3. Core addition

WG-RNN separates:

1. fast recurrent computation;
2. persistent witness memory;
3. witness-derived gates;
4. hard policy clamps;
5. replayable memory updates;
6. slot promotion;
7. purge-aware memory cascade.

---

## 4. New rule

```text
Fast recurrent state is computation.
Persistent memory authority requires witness features, replay, and policy.
```

---

## 5. Research status

WG-RNN v1.0 is a research profile.

Promotion to normative behavior requires fixture evidence, replay traces, retention diagnostics, purge tests, contradiction tests, and policy approval.
