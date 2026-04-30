# Duotronic Mathematical Canon Contract v1.0

**Status:** normative draft  
**Version:** mathematical-canon@v1.0  
**Supersedes:** older family-native representational core for v1.6 planning  
**Document kind:** Mathematical representation and canonical identity contract

---

## 1. Purpose

The Mathematical Canon Contract defines how mathematical entities become canonical Duotronic objects.

The goal is not to reduce all math to one primitive. The goal is to prevent representational collapse across:

1. object and notation;
2. term and theorem;
3. conjecture and proof;
4. computation and theorem;
5. example and universal claim;
6. external convention and internal identity;
7. absence, zero, bottom, null, empty object, undefined, unknown, contradiction, and invalidity.

---

## 2. Canonical mathematical object

A `CanonicalMathObject` is the basic representation record.

```yaml
CanonicalMathObject:
  object_id: string
  object_kind: string
  domain_id: string
  ambient_context_id: string
  notation_profile_id: string
  normalizer_id: string
  serializer_id: string
  canonical_payload_ref: string
  canonical_identity_hash: string
  assumptions_ref: string
  construction_witness_ids: []
  source_witness_ids: []
  status: parsed_candidate | canonical_object | deprecated | rejected
  version: string
```

The object identity must not depend on display-only notation.

---

## 3. Ambient context

Most mathematical objects are meaningful only in context.

```yaml
AmbientContext:
  context_id: string
  base_category: set | group | ring | field | scheme | stack | vector_space | hilbert_space | manifold | topos | custom
  base_object_refs: []
  universe_policy: small | large | inaccessible_required | proof_assistant_specific | custom
  coefficient_domain_ref: string | null
  characteristic: integer | zero | positive_prime | mixed | unknown
  topology_or_sigma_algebra_ref: string | null
  assumptions: []
  notation_conventions: []
```

Examples:

- a vector space requires a base field;
- a representation requires a group and coefficient category;
- a sheaf requires a site or space;
- an L-function requires local factors and normalization choices.

---

## 4. Distinct special states

The following states are distinct and must not be silently collapsed:

| State | Meaning |
|---|---|
| zero | additive identity where declared |
| one | multiplicative identity where declared |
| empty | empty set, empty sequence, empty scheme, or declared empty object |
| null | implementation placeholder, not mathematical by default |
| undefined | expression has no value in declared context |
| unknown | value not known to system |
| contradiction | inconsistent assumptions or claims detected |
| invalid | violates schema or object rules |
| absence | no object supplied or no witness present |
| bottom | domain-theoretic or logical bottom where declared |
| origin | coordinate or geometric role, not numeric zero by default |

---

## 5. Mathematical family declaration

```yaml
MathFamilyDeclaration:
  family_id: string
  family_schema_version: string
  domain_id: string
  object_kinds: []
  notation_profiles: []
  valid_object_rule: string
  invalid_object_rule: string
  equality_rule: structural | definitional | isomorphism_class | equivalence_relation | proof_assistant_kernel | custom
  canonicalizer: string
  serializer: string
  bridge_profiles: []
  theorem_profiles: []
  computation_profiles: []
  fixture_pack_id: string
  status: candidate | research | reference | normative | deprecated | rejected
```

---

## 6. Equality modes

Mathematical equality is not single-mode.

| Equality mode | Meaning |
|---|---|
| literal | identical surface spelling |
| alpha_equivalent | bound variable names ignored |
| definitional | equal by normalization or definitional reduction |
| propositional | equality requires proof |
| isomorphic | same up to isomorphism |
| equivalent | same under declared equivalence relation |
| Morita_equivalent | same under Morita-style equivalence |
| derived_equivalent | same under derived equivalence |
| numerically_close | approximate equality under error bounds |
| conjecturally_correspondent | matched by conjectural bridge, not equality |

A canonical identity must declare its equality mode.

---

## 7. Bridge records

A mathematical bridge is a typed relationship between objects or domains.

```yaml
MathBridgeRecord:
  bridge_id: string
  bridge_kind: isomorphism | equivalence | functor | adjunction | transform | correspondence | embedding | reduction | computation | analogy
  source_object_refs: []
  target_object_refs: []
  source_domain_id: string
  target_domain_id: string
  preservation_claims: []
  expected_loss: []
  proof_status: theorem | conjecture | computational | definition | analogy | unknown
  witness_ids: []
  normalizer_id: string
  replay_identity_ref: string
```

Langlands functorial transfers use this schema with `bridge_kind: correspondence` or `functor` and `proof_status` set per case.

---

## 8. Notation profiles

A notation profile records how mathematical text, LaTeX, code, diagrams, or formal proof assistant terms map to canonical objects.

```yaml
NotationProfile:
  notation_profile_id: string
  surface_language: latex | unicode_math | ascii | python | julia | lisp | lean | coq | agda | sage | magma | diagram | custom
  parser_id: string
  grammar_version: string
  ambiguity_policy: reject | preserve_all | require_context | choose_by_policy
  binding_policy: explicit | infer_with_witness | reject_if_ambiguous
  display_only_fields: []
  canonical_fields: []
```

---

## 9. Computation object

```yaml
MathComputationWitness:
  computation_id: string
  runtime_language: python | julia | lisp | other
  interpreter_profile_id: string
  input_object_refs: []
  code_artifact_ref: string
  package_lock_ref: string
  stdout_ref: string
  stderr_ref: string
  result_object_refs: []
  numerical_error_bound_ref: string | null
  deterministic_replay: true | false
  status: raw_execution | reproducible | verified_computation | rejected
```

Interpreter output is never automatically theorem status.

---

## 10. Canonicalization pipeline

```text
raw notation / code / source claim
-> source evidence bundle
-> parse candidate
-> context binding
-> object validation
-> normal form
-> canonical math object
-> claim / proof / computation / bridge witness
-> policy and replay record
```

---

## 11. Conformance

A v1.6 mathematical domain must provide:

1. object schemas;
2. context schemas;
3. equality modes;
4. parser/normalizer profile;
5. serializer profile;
6. claim/proof statuses;
7. computation witness behavior;
8. bridge behavior;
9. fixture pack;
10. migration notes;
11. policy gates for conjectural, numerical, and formal-proof claims.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
