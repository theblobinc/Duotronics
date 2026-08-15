# DPFC to Mathematical Canon Bridge v1.0

**Status:** normative clarification  
**Version:** dpfc-canon-bridge@v1.0

## 1. Purpose

DPFC remains part of v1.6, but it is no longer the whole mathematical core. It supplies presence-first representation discipline inside the broader Mathematical Canon.

## 2. Mapping table

| DPFC concept | v1.6 Mathematical Canon mapping |
|---|---|
| Realized magnitude | `CanonicalMathObject(object_kind=realized_magnitude)` |
| Native family word | `MathFamilyDeclaration` plus `CanonicalMathObject` instance |
| Family value | Canonical interpretation under family profile |
| Canonical family identity | `canonical_identity_hash` inside DBP v2 envelope |
| Witness history | `EvidenceBundle`, `CandidateWitness`, `CanonicalWitnessFact` |
| Bridge profile | `RepresentationBridgeWitness` or `MathBridgeWitness` |
| Export zero policy | Boundary policy inside `MathFamilyDeclaration` |
| Learned profile | `ProfileCandidate` gated by Profile Synthesis Registry |

## 3. Presence/absence preservation

The DPFC distinction between presence, absence, zero, invalid, unknown, origin, and inactive transport remains normative for all mathematical families. External mathematical systems may contain zero objects, empty sets, zero morphisms, null spaces, and origin points, but those must not be collapsed into structural absence.

## 4. Canonization rule

```text
DPFC family object
-> MathFamilyDeclaration
-> DBP v2 envelope
-> CanonicalMathObject
-> optional bridge to external integer, algebraic object, geometric object, or Langlands object
```

## 5. Polygon-family research status

Polygon-family calculus remains a research and representational domain. It may produce canonical objects when declared, validated, and normalized. It does not define arithmetic truth for unrelated domains such as algebraic geometry, topology, or Langlands representation theory.

---

## Conformance note

This document is part of the v1.6 Draft 2 implementation-readiness pass. It closes gaps identified after the first full v1.6 corpus package: API shape, durable schema, policy execution, security, deployment, replay, migration, admin tooling, and live SRNN/MCP introspection.

Unless explicitly marked `reference` or `research`, normative rules in this file bind conforming v1.6 prototypes.
