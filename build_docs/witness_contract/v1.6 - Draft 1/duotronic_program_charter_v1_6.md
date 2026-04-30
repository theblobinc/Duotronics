# Duotronic Program Charter v1.6

**Status:** normative draft  
**Version:** program-charter@v1.6  
**Document kind:** Program-level authority and scope statement  
**Primary purpose:** Define the v1.6 transition from a presence-first representational runtime into a general mathematical witness canon with Langlands integration and polyglot execution support.

---

## 1. What Duotronics is in v1.6

Duotronics v1.6 is a **witness-runtime, distributed-systems, mathematical-canon, and polyglot-computation program**.

Its scope is:

1. a general mathematical object canon;
2. witness records for claims, proofs, computations, examples, counterexamples, conjectures, and bridges;
3. Langlands integration as a first-class mathematical domain;
4. a polyglot runtime for Python, Julia, and Lisp, with room for a later Rust control plane;
5. a code interpreter plan that treats execution as evidence, not truth by default;
6. SRNN-derived recurrence, meta-object, oracle, multimodal, and task-witness patterns as implementation-facing reference architecture.

---

## 2. Core separation rule

No subsystem may silently exchange authority with another.

| Concern | Owner in v1.6 |
|---|---|
| Mathematical representation | Mathematical Canon Contract |
| Langlands objects and bridges | Langlands Canon Contract |
| Mathematical claims, proofs, conjectures | Proof and Conjecture Witness Contract |
| All-field witness coverage | All-Math Witness Contract |
| Runtime language roles | Polyglot Runtime Contract |
| Interpreter execution | Code Interpreter Plan |
| SRNN implementation learnings | SRNN Integration Addendum |
| Domain listings and fixtures | Registries under `refs/` |

---

## 3. Replacement of the older representational core

The previous family-native representational design is not discarded. Its invariant lessons are retained:

1. presence, absence, zero, invalidity, unknown, origin, transport encoding, and canonical identity are separate states;
2. every family declares object space, normalizer, serializer, bridge, fixtures, and failure states;
3. learned or computed output is not authority by itself;
4. equality and replay require pinned canonical identity.

The owning document is now `duotronic_mathematical_canon_contract_v1_0.md`.

---

## 4. Mathematical authority ladder

Mathematical records use the following status ladder:

```text
raw_expression
parsed_candidate
canonical_object
computational_result
verified_computation
literature_supported_claim
formally_verified_claim
theorem
conjecture
counterexample
rejected_or_retracted_claim
```

A conjecture can be canonical without being proven. A computational result can be reproducible without being a theorem. A theorem can be referenced without the full proof being mechanically formalized.

---

## 5. Langlands integration rule

Langlands objects are canonical mathematical objects in v1.6. Their conjectural bridges are represented as `FunctorialTransferCandidate`, `CorrespondenceClaim`, or `LFunctionEqualityClaim` records with explicit status.

Unproved parts of Langlands must never be promoted to theorem status by analogy, model agreement, numerical evidence alone, or interpreter output alone.

---

## 6. SRNN implementation feedback rule

Current SRNN server implementation patterns are accepted as implementation-facing reference input when they satisfy the v1.6 witness rules:

1. structured payloads must create witness event IDs;
2. oracle outputs must preserve replay identity;
3. multimodal ingest must validate schema before witness creation;
4. symbolic and numeric polyglot paths must have Python fallbacks;
5. external actions must remain policy-gated;
6. vector, cache, and recurrence systems may support reasoning but must not become truth by themselves.

---

## 7. Stability

This draft is specification-complete for planning and review. It is not production-final. A production v1.6 must still add:

1. implementation conformance tests;
2. formal serialization schemas;
3. migration scripts from v1.5 registries;
4. package and sandbox hardening for the interpreter;
5. Langlands fixture packs with known theorem/conjecture examples;
6. formal proof assistant bridge profiles if theorem verification is required.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
