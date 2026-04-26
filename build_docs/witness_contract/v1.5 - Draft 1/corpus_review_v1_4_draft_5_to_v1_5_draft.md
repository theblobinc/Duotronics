# Corpus Review: v1.4 Draft 5 to v1.5 Draft

**Status:** Internal corpus review and update rationale  
**Version:** corpus-review-v1.4-draft-5-to-v1.5-draft  
**Document kind:** Review-to-spec integration note  
**Primary purpose:** Record how v1.5 extends the v1.4 Draft 5 corpus into a distributed, federated, self-governing recurrent network.

---

## 1. Review driver

v1.4 Draft 5 completed the self-informing single-system governance stack.

v1.5 adds a distributed cluster layer:

```text
many Duotronic nodes
-> DBP v2 S2 full-duplex streams
-> resource availability witnesses
-> cluster decision contexts
-> policy-gated task delegation
-> task outcome witnesses
-> recurrent and lookup feedback
```

---

## 2. Major v1.5 additions

1. Resource availability witness class.
2. Task queue witness.
3. Distributed task delegation action payload.
4. Task outcome witness.
5. Node federation protocol.
6. DBP inter-node full-duplex profile.
7. Container deployment and node lifecycle guide.
8. Cluster-wide learning mode policy.
9. Node admission and revocation policy.
10. Cluster conformance fixtures.

---

## 3. Hard constraints preserved

v1.5 preserves all v1.4 Draft 5 constraints:

1. raw inputs are evidence only;
2. canonicalization before authority;
3. policy before runtime use;
4. replay identity for promoted or authority-bearing behavior;
5. purge and human review remain governance inputs;
6. planners cannot self-promote profiles;
7. raw model outputs are evidence only.

v1.5 adds the distributed equivalent:

```text
raw metrics are evidence only
connected nodes are candidates only
DBP Open/S1 frames have no authority
stale resource witnesses have zero scheduling authority
```

---

## 4. First prototype path

1. Start coordinator container.
2. Start one Xeon worker container.
3. Complete NodeHello/NodeAccept over DBP S2.
4. Publish resource witness every 5 seconds.
5. Delegate a no-op task.
6. Emit TaskOutcomeWitness.
7. Add remaining Xeon workers.
8. Add GPU worker.
9. Demonstrate GPU-specific scheduling.
10. Demonstrate stale-node invalidation and reassignment.
11. Run v1.5 conformance fixtures.
