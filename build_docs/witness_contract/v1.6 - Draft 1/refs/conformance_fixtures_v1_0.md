# v1.6 Conformance Fixtures v1.0

**Status:** reference draft  
**Version:** conformance-fixtures@v1.0

---

## 1. Core fixtures

### Fixture: zero versus absence

Expected behavior: mathematical zero, empty set, null placeholder, and absence are represented as separate states.

### Fixture: notation ambiguity

Input: `f^-1(y)`  
Expected behavior: reject or preserve ambiguity unless context declares inverse function or reciprocal.

### Fixture: alpha equivalence

Input: `forall x, P(x)` and `forall y, P(y)`  
Expected behavior: alpha-equivalent under bound variable normalizer.

### Fixture: isomorphism not equality

Input: two isomorphic groups with different presentations.  
Expected behavior: structural identities differ; isomorphism claim may link them.

---

## 2. Langlands fixtures

### Fixture: Riemann zeta

Object: `CanonicalLFunction` with Euler product, gamma factor, functional equation metadata, and analytic continuation status.

### Fixture: Dirichlet L-function

Object: primitive Dirichlet character and its L-function, with conductor and root number fields.

### Fixture: Dedekind zeta

Object: quadratic field and Dedekind zeta function with splitting metadata.

### Fixture: elliptic curve modularity record

Object: elliptic curve, modular form, and `ModularityClaim` with theorem status only when cited/proved by source witness.

### Fixture: functorial transfer candidate

Object: source and target groups, L-group homomorphism, preservation claims, status `conjectural`.

---

## 3. Interpreter fixtures

### Python fixture

Run exact rational arithmetic and produce a `verified_computation` only if replay succeeds.

### Julia fixture

Compute a small matrix eigenvalue result and record tolerance, package lock, and replay identity.

### Lisp fixture

Expand a symbolic query and record input/output hashes and rule profile version.

---

## 4. SRNN-derived fixtures

### Meta-object fixture

Input: artifact features with aliases.  
Expected behavior: canonicalized typed instances with provenance.

### Polyglot selector fixture

Input: active constellation.  
Expected behavior: Python extraction, Lisp expansion, Julia scoring, Lisp reranking, Julia/Python blend, with fallback path recorded.

### Multimodal ingest fixture

Input: frame detections with track IDs.  
Expected behavior: schema validation, temporal deltas, witness forwarding, witness event ID.

### Identity oracle fixture

Input: already-structured payload.  
Expected behavior: identity oracle creates witness without heavyweight model dependency.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
