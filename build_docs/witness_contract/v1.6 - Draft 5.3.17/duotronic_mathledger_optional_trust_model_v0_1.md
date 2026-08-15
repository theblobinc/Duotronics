# Duotronic Optional Distributed Ledger Trust Model v0.1

**Status:** Future / optional research profile  
**Purpose:** Explore decentralized trust for high-value mathematical records without making it mandatory for v1.6.

---

## 1. Motivation

Central PostgreSQL plus policy engine is sufficient for Draft 2 implementation. Some future deployments may want non-repudiation or distributed finality for theorem-status records.

---

## 2. Ledger-eligible events

Only these event types are candidates:

1. theorem promotion;
2. proof checker acceptance;
3. proof artifact registration;
4. policy snapshot approval;
5. corpus release manifest;
6. purge attestation;
7. high-value human review decision.

---

## 3. Non-goals

The ledger must not store:

1. private raw evidence;
2. secrets;
3. large proof payloads;
4. copyrighted source documents;
5. raw social feeds;
6. raw video/audio payloads.

It stores hashes, signatures, and references.

---

## 4. State machine

```text
Proposal
-> EvidenceHashBundle
-> PolicyApproval
-> LedgerCommitCandidate
-> FinalizedLedgerAnchor
```

---

## 5. Draft 2 position

This is not required for v1.6. It is preserved as a future profile.
