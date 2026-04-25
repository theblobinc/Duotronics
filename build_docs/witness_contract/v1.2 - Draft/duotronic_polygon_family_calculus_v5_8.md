# Duotronic Polygon Family Calculus (DPFC v5.8)

**Status:** Research specification draft  
**Version:** 5.8-standalone-revision  
**Supersedes:** DPFC v4.7/v4.8 research drafts  
**Document kind:** Normative core plus research appendices  
**Primary purpose:** Define a rigorous, testable, family-native Duotronic numeral and witness calculus while keeping speculative physics analogies separate from the arithmetic core.

> Drafting note. This document is written in a one-based Duotronic style. Public claim labels, checklist labels, and section labels begin at 1. External systems such as DBP wire cells, IEEE formats, conventional arithmetic, and physics literature may still contain ordinary zero-valued quantities where their own standards require them. The Duotronic rule is not that zero is forbidden everywhere; the rule is that native public Duotronic labels and document claim classes do not begin at zero.

---

## Revision 5.6 expansion summary

> **Status tag:** reference

The v5.8 revision keeps all v5.4 material and expands the document toward an internal source specification. The main additions are source architecture scaffolding, an absence-zero-origin rationale, a full ontology map, related-concept comparisons, a formal theorem registry, a normalizer profile language, a deeper geometry/group-action chapter, expanded conformance-harness guidance, migration/versioning rules, and a corpus-map appendix.

The v5.8 additions do not mutate the DPFC arithmetic core. They make the core easier to review, implement, falsify, and extend. In particular, the new material reinforces four boundaries:

1. DPFC defines mathematical and representational objects; the Witness Contract defines runtime trust.
2. Absence, ordinary zero, origin role, invalidity, witness history, display geometry, and transport encoding are distinct concepts.
3. Geometry may define witness structure and canonicalization, but does not prove arithmetic without a bridge.
4. Research profiles such as EDO, signal-derived witnesses, and physical analogies remain bounded unless promoted by explicit conformance tests.


---

## Document status tag key

> **Status tag:** reference

Every major section carries exactly one **primary** status tag so humans and tools can distinguish the normative core from examples, experiments, future work, and analogies. If a section touches more than one concern, it may add a separate `Related tags:` line, but machine parsers MUST treat `Status tag` as the single primary classification.

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding semantics for the active specification. | Conforming implementations must follow it. |
| `reference` | Examples, algorithms, fixtures, schemas, or implementation aids. | Useful for implementation, but not itself a new semantic rule unless cited by a normative section. |
| `research` | Experimental diagnostic, metric, benchmark, or pruning method. | Must remain opt-in until benchmarked and promoted. |
| `future` | Named work not completed in this document. | Must not be treated as live semantics. |
| `analogy` | Outside-field comparison or motivation. | Must not be promoted into proof, runtime authority, or external-domain claim. |

## 1. Executive summary

> **Status tag:** reference

DPFC v5.8 defines the Duotronic Polygon Family Calculus as a layered mathematical and implementation specification. It preserves the presence-first Duotronic stance:

1. realized native values begin at one;
2. structural absence is not encoded as a native numeral;
3. ordinary zero remains available at explicit export boundaries;
4. witness construction, canonical identity, transport encoding, and physics analogy remain separate layers.

The goal is not to abolish standard arithmetic. The goal is to prevent one overloaded token from meaning absence, origin, default, measured nothing, inactive memory, invalid payload, and real numeric zero at the same time.

The v5.x line establishes seven core refinements.

1. It separates **definition**, **theorem**, **implementation invariant**, **benchmark evidence**, **analogy**, and **external-domain claim** into one-based claim classes C1 through C6.
2. It gives a precise bijective positional evaluation for finite family numerals.
3. It separates the **core magnitude semantics** from **family geometry**, **witness history**, **transport encoding**, and **physics analogy**.
4. It introduces **retention diagnostics** as a non-normative research layer for measuring which declared invariants survive canonicalization, conversion, transport, and replay.
5. It embeds the minimum adapter vocabulary, Witness8 row contract, DBP boundary contract, and WSB2 sparse-row contract needed to read the document without relying on external Duotronic source documents.
6. It adds a stronger falsification and pruning discipline: families and profiles that do not pass declared tests remain experimental, not normative.
7. It clarifies that DPFC core addition is **realized-step addition**, not ordinary zero-based addition under the nonnegative export map.

The v5.8 revision additionally polishes the source-spec layer: single-primary status tags replace hybrid tags, revision summaries separate core refinements from revision-specific additions, and corpus-map entries now declare whether they are existing, draft-needed, or future work.

DPFC v5.8 should be read as a family-parametric representational layer over a shared positive core. It can be implemented, tested, serialized, converted, transported, and replayed. It is not a completed physical theory, and it does not claim that polygon diagrams, QCD symmetry diagrams, or virtual-particle language prove Duotronic arithmetic.

---

## 2. Design stance and non-claims

> **Status tag:** normative

### 2.1 Design stance

The core stance is presence-first.

A realized Duotronic magnitude is a positive thing. A native numeral family names realized magnitudes using a finite nonempty chain of family symbols. No native digit is reserved for absence. Absence belongs to structural state, not to the family digit alphabet.

DPFC v5.8 distinguishes:

1. **structural absence**, meaning no object is present at a position;
2. **origin role**, represented in the signed scalar line by the native label `1`;
3. **least realized magnitude**, represented abstractly by \(\mu_1\);
4. **ordinary exported zero**, available only after applying an explicit export bridge;
5. **token-free transport absence**, such as an all-inactive witness row in a transport profile;
6. **invalid or rejected payload**, which is neither absence nor numeric zero;
7. **canonical family identity**, which is the versioned normal form used for equality, hashing, signing, storage, conversion, and replay;
8. **witness history**, which may contain richer construction data than canonical identity;
9. **display geometry**, which may help rendering, debugging, orbit reduction, or canonicalization, but does not itself prove arithmetic.

### 2.2 Non-claims

DPFC v5.8 does not claim that:

1. standard arithmetic is wrong;
2. ordinary zero should be removed from mathematics;
3. all programming languages should use one-based indexing internally;
4. polygon witnesses are required for every application;
5. a hexagonal physics diagram proves `hex6` arithmetic;
6. the Eightfold Way, QCD confinement, or virtual-particle phenomenology proves DPFC;
7. DPFC-Continuous, DPFC-Geometric-Successor, or any physics-profile theory is completed by this document;
8. canonical witness identity is the same as raw witness history;
9. transport encodings define the arithmetic core;
10. retention diagnostics prove external physical coherence.

The positive claim is narrower and stronger:

> When a system benefits from separating absence, origin, realization, witness construction, canonical identity, and external export, DPFC gives a disciplined way to make those distinctions explicit.

---

## 3. Claim classes

> **Status tag:** normative

DPFC documents use one-based claim classes. These labels are documentation and review labels, not runtime layers.

| Claim class | Name | Meaning | Required support |
|---|---|---|---|
| C1 | Definition | A term, object, family, map, schema, or profile is defined. | Internal consistency and unambiguous notation. |
| C2 | Theorem candidate | A mathematical property is asserted from definitions. | Proof, proof sketch, named assumptions, and exact preservation statement. |
| C3 | Implementation invariant | A behavior is required of conforming implementations. | Deterministic tests, reference vectors, and failure behavior. |
| C4 | Benchmark-supported claim | A design choice improves a measurable task. | Baselines, measurements, and reproducibility. |
| C5 | Analogy or research heuristic | An outside field suggests a useful pattern. | Clear boundary language and no proof inflation. |
| C6 | External-domain claim | DPFC is claimed to model a physical, biological, or social system. | Domain-specific evidence outside DPFC itself. |

A runtime, paper, implementation, or reviewer MUST NOT treat a C5 analogy as C2 proof or C3 implementation authority.

---

## 4. Core terminology

> **Status tag:** normative

### 4.1 Structural position

A structural position is an address in a grid, stream, table, frame, state map, registry, memory, or tensor-like object. A structural position can be empty. A structural position is not itself a realized magnitude.

### 4.2 Realized magnitude

A realized magnitude is an element of the abstract positive core:

\[
\mathbb{U}^{+}=\{\mu_1,\mu_2,\mu_3,\ldots\}.
\]

The element \(\mu_1\) is the least realized magnitude. It is not absence. It is not ordinary exported zero. It is the first realized value in the core magnitude order.

### 4.3 Native family numeral

A native family numeral is a finite nonempty chain over a declared family digit alphabet. If \(F\) is a family with digit alphabet \(\Delta_F\), then:

\[
\mathbb{M}^{+}_F = \Delta_F^+.
\]

The superscript plus means nonempty finite words. Empty words do not denote native magnitudes.

### 4.4 Witness

A witness is a construction record explaining how a family object is realized. A witness may include:

1. polygon data;
2. reflection data;
3. path words;
4. orbit identifiers;
5. sector identifiers;
6. chamber identifiers;
7. rendering hints;
8. degeneracy metadata;
9. provenance;
10. transport metadata;
11. normalization confidence.

The witness is allowed to be richer than the canonical family numeral.

### 4.5 Canonical family object

A canonical family object is the normalized identity-bearing representation of a family numeral under its declared serializer, schema version, and normalizer.

A canonical family object is suitable for:

1. equality checks;
2. hashing;
3. signing;
4. storage;
5. conversion;
6. replay;
7. witness lookup;
8. migration comparison.

Display glyphs are not canonical identity unless a family explicitly declares them as canonical identity fields, which is discouraged.

### 4.6 Export boundary

An export boundary is a declared map from Duotronic objects to a non-Duotronic environment. Export boundaries may intentionally discard witness history, family identity, semantic state, or absence distinctions, but any such loss must be declared.

### 4.7 Structural absence

Structural absence means that no object is present at a structural position. It is not a native magnitude. It is not \(\mu_1\). It is not ordinary exported zero.

### 4.8 Token-free absence

Token-free absence is a transport-level representation of no semantic payload, usually by an all-inactive row or bitmap. Token-free absence is not numeric zero.

### 4.9 Invalid payload

An invalid payload is a present but malformed, unsupported, unauthenticated, ambiguous, or rejected payload. Invalid payload is not absence and not numeric zero.

---

## 5. The core magnitude calculus

> **Status tag:** normative

### 5.1 Core domain

The core magnitude domain is the well-ordered positive domain:

\[
\mathbb{U}^{+}=\{\mu_1,\mu_2,\mu_3,\ldots\}.
\]

The order is:

\[
\mu_1 < \mu_2 < \mu_3 < \cdots.
\]

### 5.2 Core successor

Define:

\[
\operatorname{usucc}(\mu_n)=\mu_{n+1}.
\]

The function \(\operatorname{usucc}\) is total over \(\mathbb{U}^{+}\).

### 5.3 Core realized-step addition

The operation \(\oplus_u\) is the **core realized-step addition**. It is called "addition" only in the internal Duotronic sense that one realized magnitude is advanced by the realized step count carried by another realized magnitude.

\[
\mu_m \oplus_u \mu_1 = \operatorname{usucc}(\mu_m),
\]

\[
\mu_m \oplus_u \operatorname{usucc}(\mu_n)=\operatorname{usucc}(\mu_m\oplus_u\mu_n).
\]

Equivalently, under the positive index map \(\iota(\mu_n)=n\),

\[
\iota(\mu_m\oplus_u\mu_n)=m+n.
\]

The element \(\mu_1\) is not an additive identity for \(\oplus_u\). It is the least realized addend, and adding it advances by one successor step.

There is no native additive identity inside \(\mathbb{U}^{+}\), because the domain contains realized positive magnitudes only. If an additive identity is required, it belongs to an explicit export domain or scalar-role bridge, not to a native magnitude digit.

Implementation language SHOULD use one of these internal names when ambiguity matters:

1. `core_realized_step_add`;
2. `positive_index_add`;
3. `uplus_realized`;
4. `duotronic_core_add`.

Implementation language SHOULD NOT describe \(\oplus_u\) as ordinary zero-based addition unless it also states the active export bridge.

### 5.4 Core multiplication

Core multiplication is repeated core realized-step addition:

\[
\mu_m\otimes_u\mu_1=\mu_m,
\]

\[
\mu_m\otimes_u\operatorname{usucc}(\mu_n)=(\mu_m\otimes_u\mu_n)\oplus_u\mu_m.
\]

Thus \(\mu_1\) acts as the multiplicative identity in the positive magnitude core.

### 5.5 Positive index interpretation

For computational interoperability, define the positive index map:

\[
\iota(\mu_n)=n.
\]

Under \(\iota\), the core operations correspond to ordinary positive-index arithmetic:

\[
\iota(\mu_m\oplus_u\mu_n)=\iota(\mu_m)+\iota(\mu_n),
\]

\[
\iota(\mu_m\otimes_u\mu_n)=\iota(\mu_m)\cdot\iota(\mu_n).
\]

The positive index map is the correct bridge when the implementation wants operation preservation.

### 5.6 Nonnegative export interpretation

A conventional nonnegative export can be obtained by:

\[
E_{\mathbb{U}}(\mu_n)=n-1.
\]

The inverse import is:

\[
I_{\mathbb{U}}(k)=\mu_{k+1}.
\]

This bridge does not say that \(\mu_1\) is secretly ordinary zero. It says that ordinary zero appears at an explicit boundary when a positive realized core is exported into a conventional nonnegative domain.

The nonnegative export map \(E_{\mathbb{U}}\) is intentionally not an addition-preserving homomorphism for \(\oplus_u\):

\[
E_{\mathbb{U}}(\mu_m\oplus_u\mu_n)=E_{\mathbb{U}}(\mu_m)+E_{\mathbb{U}}(\mu_n)+1.
\]

It is also not a multiplication-preserving homomorphism for \(\otimes_u\):

\[
E_{\mathbb{U}}(\mu_m\otimes_u\mu_n)=(E_{\mathbb{U}}(\mu_m)+1)(E_{\mathbb{U}}(\mu_n)+1)-1.
\]

### 5.7 Export algebra boundary rule

Any implementation that exports into ordinary nonnegative arithmetic MUST choose one of two policies.

#### Policy 1: index-preserving policy

Operate through \(\iota\), where \(\oplus_u\) and \(\otimes_u\) correspond to ordinary positive-index addition and multiplication.

#### Policy 2: nonnegative-role policy

Operate through \(E_{\mathbb{U}}\), where ordinary zero is available but Duotronic core operations acquire the explicit affine correction shown above.

A document, schema, test, adapter, runtime, or proof MUST state which export policy it uses. Silent switching between these policies is a conformance failure.

---

## 6. The signed gapped scalar line

> **Status tag:** normative

### 6.1 Scalar domain

The signed scalar line is:

\[
\Lambda=\{\ldots,-4,-3,-2,1,2,3,4,\ldots\}.
\]

The labels `0` and `-1` are omitted from the native scalar line. The order is:

\[
\cdots < -4 < -3 < -2 < 1 < 2 < 3 < 4 < \cdots.
\]

### 6.2 Scalar roles

The scalar labels carry role aliases.

| Role | Native label | Meaning |
|---|---:|---|
| origin | `1` | center role of the signed scalar line |
| positive unit neighbor | `2` | first positive step from origin |
| negative unit neighbor | `-2` | first negative step from origin |

The origin role is not a magnitude digit. It is a scalar-coordinate role.

### 6.3 Scalar successor and predecessor

The scalar successor and predecessor are adjacency operations:

\[
\operatorname{ssucc}(-2)=1,\qquad \operatorname{ssucc}(1)=2,
\]

\[
\operatorname{spred}(2)=1,\qquad \operatorname{spred}(1)=-2.
\]

Away from the gap, they continue by ordinary adjacency along the two branches.

### 6.4 Native scalar distance

The scalar line has a graph-step distance:

\[
d_{\Lambda}(a,b)=\text{least number of scalar successor/predecessor steps from }a\text{ to }b.
\]

Examples:

\[
d_{\Lambda}(1,2)=1,
\]

\[
d_{\Lambda}(1,-2)=1,
\]

\[
d_{\Lambda}(-2,2)=2.
\]

### 6.5 Translation by core magnitude

Every core magnitude \(\mu_n\) induces right and left scalar translation.

Right translation:

\[
T_+(s,\mu_1)=\operatorname{ssucc}(s),
\]

\[
T_+(s,\operatorname{usucc}(\mu_n))=\operatorname{ssucc}(T_+(s,\mu_n)).
\]

Left translation:

\[
T_-(s,\mu_1)=\operatorname{spred}(s),
\]

\[
T_-(s,\operatorname{usucc}(\mu_n))=\operatorname{spred}(T_-(s,\mu_n)).
\]

### 6.6 Translation-distance theorem candidate

For every scalar \(s\in\Lambda\) and every core magnitude \(\mu_n\):

\[
d_{\Lambda}(s,T_+(s,\mu_n))=n,
\]

\[
d_{\Lambda}(s,T_-(s,\mu_n))=n.
\]

This is a C2 theorem candidate with a direct induction proof over \(n\).

---

## 7. The Duotronic grid

> **Status tag:** normative

For dimension \(d\geq 1\), define:

\[
\mathbb{D}^{d}=\Lambda^d.
\]

The native origin point is:

\[
(1,1,\ldots,1).
\]

A Duotronic grid position may be empty or occupied. Occupancy is not encoded by using a coordinate value as a sentinel. It is a separate structural state.

Grid translation is componentwise. If \(x=(x_1,\ldots,x_d)\), then a rightward translation along coordinate \(j\) by \(\mu_n\) is:

\[
T_{+,j}(x,\mu_n)=(x_1,\ldots,T_+(x_j,\mu_n),\ldots,x_d).
\]

---

## 8. Numeral families

> **Status tag:** normative

### 8.1 Family declaration

A DPFC family is a declared tuple:

\[
F=(\mathrm{id},b_F,\Delta_F,\prec_F,\operatorname{fsucc}_F,\Phi_F,\mathrm{render}_F,\mathrm{witness}_F,\mathrm{degeneracy}_F,\mathrm{geometry}_F,\mathrm{serializer}_F,\mathrm{normalizer}_F).
\]

Where:

| Field | Meaning |
|---|---|
| \(\mathrm{id}\) | stable family identifier |
| \(b_F\) | family bijective modulus |
| \(\Delta_F\) | ordered native digit alphabet |
| \(\prec_F\) | digit order |
| \(\operatorname{fsucc}_F\) | native family successor |
| \(\Phi_F\) | family-to-core bridge |
| \(\mathrm{render}_F\) | display policy |
| \(\mathrm{witness}_F\) | witness schema |
| \(\mathrm{degeneracy}_F\) | equivalence and witness-history policy |
| \(\mathrm{geometry}_F\) | geometric generator and scope |
| \(\mathrm{serializer}_F\) | canonical storage form |
| \(\mathrm{normalizer}_F\) | validation and canonicalization profile |

### 8.2 Family alphabet

Let:

\[
\Delta_F=(\delta^{(F)}_1,\delta^{(F)}_2,\ldots,\delta^{(F)}_{b_F}).
\]

No \(\delta^{(F)}_i\) denotes absence. The first family digit denotes the least realized magnitude in that family.

### 8.3 Family numeral language

The family numeral domain is:

\[
\mathbb{M}^{+}_F=\Delta_F^+.
\]

Every valid native family numeral is a finite nonempty word:

\[
M=\delta^{(F)}_{i_1}\delta^{(F)}_{i_2}\cdots\delta^{(F)}_{i_k}.
\]

### 8.4 Family validity requirements

A family is valid only if:

1. \(b_F\geq1\);
2. \(\Delta_F\) contains exactly \(b_F\) distinct native digit symbols;
3. the digit order is deterministic;
4. the family language is exactly nonempty finite words over \(\Delta_F\), unless a stricter language is explicitly declared and proven bijective to a declared subset;
5. the family-to-core bridge is total for all valid family numerals;
6. the inverse core-to-family bridge is total for all \(\mu_n\in\mathbb{U}^{+}\);
7. the successor law commutes with core successor;
8. canonical serialization is deterministic and versioned.

---

## 9. Bijective positional evaluation

> **Status tag:** normative

### 9.1 Digit ordinal map

Define the ordinal digit value:

\[
\operatorname{ord}_F(\delta^{(F)}_i)=i,
\qquad 1\leq i\leq b_F.
\]

### 9.2 Family index value

For a word \(M=\delta^{(F)}_{i_1}\cdots\delta^{(F)}_{i_k}\), define:

\[
\operatorname{val}_F(M)=\sum_{j=1}^{k} i_j b_F^{k-j}.
\]

This is the ordinary bijective-base positional value. It maps the first digit to one, the last primitive digit to \(b_F\), and the first two-digit numeral \(\delta_1\delta_1\) to \(b_F+1\).

### 9.3 Family-to-core bridge

Define:

\[
\Phi_F(M)=\mu_{\operatorname{val}_F(M)}.
\]

This bridge is bijective from \(\mathbb{M}^{+}_F\) to \(\mathbb{U}^{+}\), provided the family language is exactly all nonempty finite words over its finite ordered alphabet.

### 9.4 Inverse encoding from core to family

For \(\mu_n\), compute the unique family word with bijective base \(b_F\).

Let \(q=n\). Repeatedly compute:

1. \(r=((q-1)\bmod b_F)+1\);
2. prepend \(\delta^{(F)}_r\);
3. replace \(q\) with \((q-r)/b_F\);
4. stop when \(q\) is no longer positive.

The result is \(\Phi_F^{-1}(\mu_n)\).

### 9.5 Canonical representation theorem candidate

For every valid finite family \(F\) and every \(\mu_n\in\mathbb{U}^{+}\), there is exactly one \(M\in\mathbb{M}^{+}_F\) such that:

\[
\Phi_F(M)=\mu_n.
\]

This theorem is inherited from bijective positional notation and is formalized in Appendix A.

---

## 10. Family successor and arithmetic

> **Status tag:** normative

### 10.1 Successor law

The family successor is the bijective carry successor over the declared one-based digit order.

For any possibly empty prefix \(X\) and any non-maximal final digit \(\delta^{(F)}_i\) with \(1\leq i<b_F\):

\[
\operatorname{fsucc}_F(X\delta^{(F)}_i)=X\delta^{(F)}_{i+1}.
\]

This rule covers the ordinary multi-digit non-carry case. For example, in `hex6`:

```text
h1 h4 -> h1 h5
```

For maximal final digits, carry recursively. If \(X\) is nonempty:

\[
\operatorname{fsucc}_F(X\delta^{(F)}_{b_F})=\operatorname{fsucc}_F(X)\delta^{(F)}_1.
\]

The one-digit carry boundary is:

\[
\operatorname{fsucc}_F(\delta^{(F)}_{b_F})=\delta^{(F)}_1\delta^{(F)}_1.
\]

Equivalently, \(\operatorname{fsucc}_F\) is the unique word-level operation that maps the bijective positional value \(n\) to \(n+1\):

\[
\operatorname{val}_F(\operatorname{fsucc}_F(M))=\operatorname{val}_F(M)+1.
\]

### 10.2 Successor bridge theorem candidate

For every \(M\in\mathbb{M}^{+}_F\):

\[
\Phi_F(\operatorname{fsucc}_F(M))=\operatorname{usucc}(\Phi_F(M)).
\]

This is the primary family-coherence theorem. Implementations must test it for all short words up to a configured length and by property-based sampling for larger words.

### 10.3 Induced family realized-step addition

Family realized-step addition is defined by the core bridge:

\[
M\oplus_F N=\Phi_F^{-1}(\Phi_F(M)\oplus_u\Phi_F(N)).
\]

The recursive presentation is:

\[
M\oplus_F\delta^{(F)}_1=\operatorname{fsucc}_F(M),
\]

\[
M\oplus_F\operatorname{fsucc}_F(N)=\operatorname{fsucc}_F(M\oplus_F N).
\]

This is not ordinary zero-based addition unless the chosen export boundary states the affine correction.

### 10.4 Induced family multiplication

Family multiplication is defined by the core bridge:

\[
M\otimes_F N=\Phi_F^{-1}(\Phi_F(M)\otimes_u\Phi_F(N)).
\]

The recursive presentation is:

\[
M\otimes_F\delta^{(F)}_1=M,
\]

\[
M\otimes_F\operatorname{fsucc}_F(N)=(M\otimes_F N)\oplus_F M.
\]

---

## 11. Inter-family conversion

> **Status tag:** normative

For families \(F\) and \(G\), define:

\[
\Psi_{F\to G}=\Phi_G^{-1}\circ\Phi_F.
\]

This converts a family numeral into the unique target-family numeral with the same core magnitude.

The conversion pipeline is:

1. parse the source surface form;
2. validate the source family declaration;
3. normalize the source object;
4. evaluate \(\Phi_F\);
5. encode by \(\Phi_G^{-1}\);
6. serialize under the target family serializer;
7. record any loss of family-local witness history.

Family conversion must preserve core magnitude. It need not preserve family identity, raw path word, display glyph, or witness construction history unless the target profile declares a metadata-preservation channel.

---

## 12. Geometry schema

> **Status tag:** normative

### 12.1 Geometry kinds

A family geometry schema must declare one of these kinds:

1. `polygon_progression`;
2. `reflection_family`;
3. `path_orbit_family`;
4. `net_family`;
5. `custom_declared_family`.

### 12.2 Required geometry fields

A geometry schema must include:

1. `kind`;
2. `dimension_scope`;
3. `generator_data`;
4. `canonicalization_policy`;
5. `degeneracy_policy`;
6. `rendering_policy`;
7. `version`.

### 12.3 Geometry is not proof of arithmetic

Geometry may justify witness shape, family naming, rendering, orbit reduction, path equivalence, and degeneracy treatment. It does not by itself prove a successor law.

A family's arithmetic law is valid only if:

1. the family-to-core bridge is defined;
2. the bridge is bijective;
3. the successor bridge theorem holds;
4. the induced arithmetic preserves core magnitude as declared.

A visual rendering is not a proof.

---

## 13. Witness schema and degeneracy

> **Status tag:** normative

### 13.1 Witness record

A witness record may contain:

1. `family_id`;
2. `schema_version`;
3. `primitive_digit_witness`;
4. `composition_rule`;
5. `raw_path`;
6. `canonical_path`;
7. `orbit_id`;
8. `sector_id`;
9. `chamber_id`;
10. `degeneracy_class`;
11. `provenance`;
12. `normalization_confidence`.

### 13.2 Degeneracy relation

A family may declare an equivalence relation \(\sim_F\) over witnesses. If \(w_1\sim_F w_2\), then canonicalization must map both witnesses to family objects with the same core magnitude:

\[
\Phi_F(\operatorname{canon}_F(w_1))=\Phi_F(\operatorname{canon}_F(w_2)).
\]

### 13.3 Canonical representative

If multiple witnesses represent the same family object, the family must declare either:

1. a deterministic canonical representative rule;
2. a rule that preserves all witness histories as metadata while selecting one canonical identity;
3. a rejection policy for ambiguous witnesses.

A common rule for path families is lexicographically smallest admissible reduced path under a schema-pinned generator order.

---

## 14. Worked family: `hex6`

> **Status tag:** reference

The `hex6` family is a simple polygon-progression reference family.

\[
\Delta_{\mathrm{hex6}}=(h_1,h_2,h_3,h_4,h_5,h_6),
\qquad b_{\mathrm{hex6}}=6.
\]

The successor chain is:

\[
h_1\to h_2\to h_3\to h_4\to h_5\to h_6\to h_1h_1.
\]

The bridge is:

\[
\Phi_{\mathrm{hex6}}(h_{i_1}\cdots h_{i_k})=\mu_{\sum_{j=1}^{k} i_j6^{k-j}}.
\]

`hex6` is useful as a reference family because it is simple, finite, visual, and easy to test. It should not be overread as a physics claim. Hexagonal diagrams in physics may motivate visualization, but they do not validate the `hex6` successor law.

---

## 15. Worked family: `refl3`

> **Status tag:** reference

The `refl3` family is a reflection-derived reference family.

\[
\Delta_{\mathrm{refl3}}=(r_1,r_2,r_3),
\qquad b_{\mathrm{refl3}}=3.
\]

The intended geometry is a two-mirror sixty-degree arrangement with positive-sector canonical reduction. A raw six-sector dihedral picture is reduced into a three-sector fundamental representation.

A witness may contain:

1. `sector_id`;
2. `path_word`;
3. `orbit_id`;
4. `canonical_path_word`;
5. `geometry_registry_version`.

The arithmetic successor remains bijective base three:

\[
r_1\to r_2\to r_3\to r_1r_1.
\]

The important research point is that geometry changes witness identity and canonicalization, but not the core successor law.

A future DPFC-Geometric-Successor profile may allow geometric walks to define successor directly, but that is not part of the v5.8 core.

---

## 16. Canonical serialization

> **Status tag:** normative

### 16.1 Storage form

The default canonical storage form is:

```text
family:<family_id> schema_version:<schema_id> digits:<i1 i2 ... ik>
```

The digits are one-based ordinal positions in the declared family alphabet.

Example:

```text
family:hex6 schema_version:dpfc-family@v5.8 digits:1 4 6
```

### 16.2 Identity fields

Canonical identity includes:

1. family identifier;
2. family schema version;
3. ordered digit ordinals;
4. serializer version;
5. normalizer version when a normalizer affects storage identity.

Display glyphs are not canonical identity.

### 16.3 Version boundary rule

Objects with different schema versions do not compare equal as canonical storage objects unless a declared migration bridge explicitly proves equality.

### 16.4 Canonical storage object

A canonical storage object SHOULD have this shape:

```json
{
  "family_id": "hex6",
  "family_schema_version": "dpfc-family@v5.8",
  "serializer_version": "canonical-storage@v1",
  "normalizer_version": "hex6-normalizer@v1",
  "digit_ordinals": [1, 4, 6],
  "canonical_storage": "family:hex6 schema_version:dpfc-family@v5.8 digits:1 4 6"
}
```

---

## 17. Normalization and automata

> **Status tag:** normative

A family may declare a normalizer. If it does, the normalizer must specify:

1. accepted input language;
2. rejection behavior;
3. deterministic canonicalization function;
4. normalizer version;
5. whether the normalizer is finite-state, bounded symbolic, or algorithmic;
6. whether witness reduction occurs before or after surface normalization;
7. whether normalization can produce low-confidence success;
8. whether ambiguous inputs are rejected or preserved as audit artifacts.

Finite-state normalizers are preferred when the input language is regular. Path and reflection families may require bounded symbolic reducers rather than pure finite-state machinery.

A normalizer MUST NOT silently change family identity, schema version, digit order, or geometry interpretation.

---

## 18. Standalone implementation adapters

> **Status tag:** normative

This section embeds the minimum adapter vocabulary needed to read DPFC v5.8 without relying on external source documents.

### 18.1 Witness8 row

A `Witness8` row is an implementation-oriented semantic row with eight ordered features:

1. `value_norm`;
2. `n_sides_norm`;
3. `center_on`;
4. `activation_density`;
5. `kind_flag`;
6. `band_position`;
7. `parity`;
8. `degeneracy`.

A `Witness8` row is not the mathematical core. It is a profile-dependent transport or implementation object.

DPFC defines adapters:

\[
\operatorname{Encode8}_F:\mathbb{M}^{+}_F\to\mathrm{Witness8}_P,
\]

\[
\operatorname{Decode8}_F:\mathrm{Witness8}_P\to\mathbb{M}^{+}_F\cup\{\mathsf{absent},\mathsf{invalid},\mathsf{lossy}\}.
\]

The adapter must declare:

1. numeric normalization bounds;
2. family-to-`kind_flag` mapping;
3. side-count normalization;
4. how numeric zero is represented as a present value if supported;
5. how token-free absence is detected;
6. how invalid rows are reported;
7. whether decoding is exact or lossy.

### 18.2 Witness8 row state outcomes

A decoder MUST output one of:

1. `decoded_exact`;
2. `decoded_lossy`;
3. `token_free_absent`;
4. `present_invalid`;
5. `unsupported_family`;
6. `ambiguous`;
7. `profile_mismatch`.

### 18.3 Token-free absence rule

An all-inactive row under the active profile represents token-free absence:

```text
[0, 0, 0, 0, 0, 0, 0, 0]
```

Expected semantic result:

```text
semantic_state = absent
numeric_zero = not inferred
trusted_for_family_core = false
```

### 18.4 Explicit numeric-zero rule

If a profile supports ordinary numeric zero at an export boundary, it must encode numeric zero as a present row, not as token-free absence.

A profile-specific present numeric-zero row MUST contain enough active information to distinguish it from absence.

### 18.5 DBP boundary

DBP is a byte or frame transport boundary. It is not a numeral family.

A minimal DBP-like frame model contains:

1. frame shape;
2. profile identifier;
3. payload length;
4. structural fields;
5. semantic payload region;
6. integrity field such as CRC or authenticated tag;
7. optional encryption metadata;
8. optional sequence number;
9. optional replay protection field.

DPFC values may be transported by DBP only after passing through a profile-defined semantic encoding.

The receiver order is:

1. validate DBP frame shape;
2. validate structural fields;
3. validate CRC or security mode;
4. decrypt authenticated payload if applicable;
5. decode WSB2 or semantic witness rows;
6. apply Witness8 validation;
7. canonicalize into DPFC normal form;
8. allow lookup, replay, or family conversion only after canonicalization succeeds.

Structural DBP fields must not be witness-encoded. This is a boundary invariant.

### 18.6 WSB2 sparse-row boundary

WSB2 is a sparse semantic bitmap or row profile for compact witness-like payloads. It is not a numeral family.

A minimal WSB2 row model contains:

1. active bitmask;
2. row width;
3. profile identifier;
4. semantic lane definitions;
5. optional compressed values;
6. optional row checksum;
7. optional row provenance tag.

WSB2 rows may carry `Witness8`-compatible semantic features only under an active profile. An inactive lane is not numeric zero unless the profile explicitly states that the lane is present and zero-valued.

### 18.7 Adapter boundary invariant

Transport, row encoding, and sparse representation do not redefine DPFC arithmetic.

The order is:

```text
transport validation
-> row/profile decode
-> semantic validation
-> DPFC canonicalization
-> trusted family operation
```

Any implementation that performs trusted family operation before canonicalization is non-conformant.

---

## 19. QCD and Eightfold Way as research analogies

> **Status tag:** analogy

The STAR Collaboration's measurement of spin correlation between quarks during QCD confinement is useful to DPFC as a methodological analogy. The paper studies an upstream hidden correlation through downstream observable hadron-pair spin correlations after confinement and hadronization.

Its key value for DPFC is not particle physics validation. Its value is the research pattern:

1. infer upstream structure from downstream observables;
2. compare near-related cases to far-related or shuffled baselines;
3. measure how much correlation survives a transformation;
4. avoid treating visualization alone as proof.

The Eightfold Way likewise suggests a useful symbolic pattern: visible state diagrams can be organized by deeper symmetry relations.

For DPFC, the practical takeaway is to study:

1. orbit classes;
2. degeneracy;
3. canonical representatives;
4. retained invariants;
5. baseline-adjusted retention;
6. loss declarations.

The takeaway is not that a hexagon image proves a six-digit family.

---

## 20. Retention diagnostics research layer

> **Status tag:** research

### 20.1 Status

Retention diagnostics are C4 research instruments, not core arithmetic definitions.

A retention diagnostic MUST NOT weaken:

1. canonicalization requirements;
2. transport validation;
3. family bridge requirements;
4. schema version checks;
5. replay identity checks;
6. absence/numeric-zero separation.

### 20.2 Invariant extractor

Let \(I_K\) be an invariant extractor for invariant kind \(K\).

Examples:

1. core magnitude;
2. family identifier;
3. canonical storage hash;
4. orbit identifier;
5. sector identifier;
6. reduced path identifier;
7. provenance class;
8. semantic state;
9. transport hash;
10. replay hash;
11. export policy;
12. normalizer version.

### 20.3 Transformation

Let \(T\) be a transformation such as:

1. canonicalization;
2. family conversion;
3. Witness8 encoding;
4. Witness8 decoding;
5. DBP transport;
6. WSB2 sparse transport;
7. lookup;
8. replay under a pinned schema;
9. migration;
10. export.

### 20.4 Similarity function

Each invariant kind \(K\) MUST declare a similarity function:

\[
\operatorname{sim}_K(a,b)\in[0,1].
\]

Allowed similarity families include:

1. `exact_equal`;
2. `hash_equal`;
3. `set_equal`;
4. `ordered_sequence_equal`;
5. `tolerance_numeric`;
6. `class_equivalent`;
7. `expected_loss_declared`;
8. `prohibited_gain_detector`.

The similarity function MUST be deterministic under the active schema and profile.

### 20.5 Retention score

Define:

\[
R_K(w,T)=\operatorname{sim}_K(I_K(w),I_K(T(w))).
\]

### 20.6 Loss score

\[
L_K(w,T)=1-R_K(w,T).
\]

### 20.7 Baseline-adjusted retention

Let \(B_K\) be a baseline retention score measured on shuffled, malformed, schema-mismatched, long-separated, transport-invalid, or unrelated witnesses.

Then:

\[
\operatorname{BAR}_K(w,T)=R_K(w,T)-B_K.
\]

A normalized lift form is:

\[
\operatorname{NRL}_K(w,T)=\frac{R_K(w,T)-B_K}{1-B_K+\epsilon}.
\]

Retention reports without baselines are diagnostic hints, not research results.

### 20.8 RetentionMetricSpec

Every reported retention metric MUST have a `RetentionMetricSpec`.

```json
{
  "metric_id": "core-magnitude-through-conversion@v1",
  "invariant_kind": "core_magnitude",
  "extractor_id": "core-index-extractor@v1",
  "similarity_id": "exact_equal@v1",
  "transformation": "family_conversion",
  "source_profile": "hex6",
  "target_profile": "refl3",
  "preservation_class": "must_preserve",
  "baseline_suite": [
    "shuffled_pair",
    "schema_mismatch",
    "malformed_source",
    "unsupported_family"
  ],
  "pass_rule": {
    "min_retention": 1.0,
    "max_baseline": 0.05,
    "min_normalized_lift": 0.95
  },
  "failure_action": "reject_conversion_or_keep_experimental"
}
```

### 20.9 Required retention fields

A retention report MUST include:

1. `metric_id`;
2. `invariant_kind`;
3. `extractor_id`;
4. `similarity_id`;
5. `transformation`;
6. `source_schema_version`;
7. `target_schema_version`;
8. `normalizer_version`;
9. `baseline_suite`;
10. `retention_score`;
11. `baseline_score`;
12. `baseline_adjusted_retention`;
13. `normalized_retention_lift`;
14. `preservation_class`;
15. `pass_rule`;
16. `failure_action`.

### 20.10 Metric elasticity prohibition

A retention metric is non-conformant if:

1. the extractor is not versioned;
2. the similarity function is not declared;
3. the baseline is omitted;
4. the pass rule is not declared;
5. the preservation class is not declared;
6. failures have no policy action;
7. the metric is reinterpreted after seeing results;
8. expected loss is reported as failure;
9. prohibited gain is ignored;
10. the metric is used as proof of a C6 external-domain claim.

---

## 21. Preservation classes

> **Status tag:** research

Every invariant should be classified.

| Preservation class | Meaning | Example |
|---|---|---|
| `must_preserve` | loss is a conformance failure | core magnitude through family conversion |
| `should_preserve` | loss is a warning | canonical path under replay |
| `metadata_only` | loss does not change canonical identity | raw witness history |
| `expected_loss` | transformation is designed to discard it | source family ID after conversion |
| `prohibited_gain` | invariant must not appear from nowhere | silent reinterpretation of absent as present |

This prevents false alarms. For example, family conversion should preserve core magnitude but may intentionally lose source-family identity.

---

## 22. Boundary table

> **Status tag:** normative

| Boundary | Must preserve | May lose | Must reject or flag |
|---|---|---|---|
| surface parse to canonical object | family ID, schema, digits | whitespace, display glyphs | malformed digit symbols |
| witness to canonical family object | core magnitude, declared equivalence | raw path orientation | ambiguous unhandled witness |
| family conversion | core magnitude | source family identity | missing bridge |
| Witness8 encoding | profile-declared fields | rich witness history | unsupported family |
| DBP transport | bytes under integrity scope | non-carried metadata | invalid frame/security failure |
| WSB2 sparse row | active semantic lanes | inactive lanes | absent/zero collapse |
| lookup | normal-form key identity | raw bundle ordering | canonicalization failure as success |
| export to nonnegative domain | declared export value | native family identity | silent operation-preservation assumption |

---

## 23. Conformance requirements

> **Status tag:** normative

### 23.1 Core conformance

A DPFC v5.8 implementation conforms at the core layer if it implements:

1. \(\mathbb{U}^{+}\);
2. \(\operatorname{usucc}\);
3. \(\oplus_u\) as core realized-step addition;
4. \(\otimes_u\);
5. \(\Lambda\);
6. scalar successor and predecessor;
7. scalar translation and distance;
8. positive index map \(\iota\);
9. nonnegative export map \(E_{\mathbb{U}}\);
10. export algebra boundary policies.

### 23.2 Family conformance

Each family declares:

1. identifier;
2. schema version;
3. alphabet;
4. bijective modulus;
5. digit order;
6. positional bridge;
7. successor;
8. witness schema;
9. geometry schema;
10. degeneracy schema;
11. serializer;
12. normalizer policy.

### 23.3 Serialization conformance

Canonical storage must be deterministic, versioned, and independent of display glyphs.

### 23.4 Conversion conformance

Inter-family conversion must be exactly:

\[
\Psi_{F\to G}=\Phi_G^{-1}\circ\Phi_F.
\]

Shortcuts are allowed only if they are proven equivalent.

### 23.5 Transport conformance

Transport profiles must not reinterpret DBP structural fields as witnesses, and must not allow failed transport validation to enter trusted DPFC state.

### 23.6 Retention conformance

Retention metrics must use `RetentionMetricSpec` objects with versioned extractors, declared similarity functions, baseline suites, pass rules, and failure actions.

### 23.7 Higher meta/runtime conformance

A higher-order or meta runtime MAY consume canonical DPFC family objects, canonical witness metadata, and declared preservation classes as inputs to a separate trust layer.

Such a meta layer MUST NOT redefine:

1. DPFC arithmetic on \(\mathbb{U}^{+}\);
2. family bridge laws;
3. successor semantics;
4. conversion semantics beyond declared expected loss;
5. export-boundary algebra.

If a meta layer emits higher-order witnesses or meta-object assertions over DPFC objects, it MUST preserve or explicitly declare loss for:

1. canonical family identity;
2. core magnitude;
3. family schema version;
4. export policy declaration;
5. the distinction between canonical identity and witness history.

Meta-object normalization over DPFC-derived objects MUST be deterministic and replay-stable. A meta assertion MAY summarize or classify a family object, but it MUST NOT silently overwrite the underlying canonical object.

---

## 24. Test matrix

> **Status tag:** reference

| Test group | Required tests |
|---|---|
| family parser | valid and malformed declarations |
| bijective bridge | encode/decode for small values and randomized values |
| successor | bridge commutation property |
| arithmetic | addition and multiplication against positive index evaluation |
| export boundary | nonnegative affine correction tests |
| conversion | round-trip core magnitude preservation |
| serialization | stable hashes and schema-version inequality |
| witness | degeneracy equivalence and canonical representative |
| reflection | path reduction and orbit stability |
| Witness8 adapter | absence, explicit numeric zero, invalid row behavior |
| DBP boundary | frame validation before semantic trust |
| WSB2 boundary | sparse inactive lane not equal to numeric zero |
| retention | real-pair versus shuffled baseline |
| retention spec | extractor, similarity, baseline, pass rule, failure action present |
| meta runtime boundary | canonical family identity preservation, witness-history separation, deterministic meta-object normalization |

---

## 25. Failure and pruning catalogue

> **Status tag:** reference

A family, profile, adapter, metric, or geometry layer should remain experimental or be deprecated if:

1. the bridge is not bijective;
2. successor does not commute with core successor;
3. canonicalization is not replay-stable;
4. geometry does not affect any declared invariant and serves only as decoration;
5. display glyphs leak into storage identity;
6. absence and numeric zero collapse;
7. conversion silently loses must-preserve invariants;
8. transport validation can be bypassed;
9. retention metrics cannot beat shuffled baselines;
10. implementation complexity exceeds measured utility;
11. export policy is not stated;
12. \(\oplus_u\) is treated as ordinary zero-based addition without correction;
13. retention metric pass rules are invented after observing results;
14. expected loss creates false conformance failure;
15. prohibited gain is ignored.

---

## 26. Research roadmap

> **Status tag:** future

### 26.1 DPFC-Discrete

Complete the finite family machinery, canonical serialization, conversion, conformance vectors, and adapter tests.

### 26.2 DPFC-Geometric-Successor

Investigate families where successor is a declared geometric walk rather than a plain bijective digit successor. This requires new proofs.

### 26.3 DPFC-Continuous

Investigate fractional magnitudes, smooth or quasi-smooth embeddings around the gapped scalar line, and field-like exported structures. This is future work.

### 26.4 DPFC-Retention

Develop benchmark datasets for retention diagnostics, including baseline-adjusted retention and conversion loss reports.

### 26.5 DPFC-Physical-Profile

Treat physics language as a separate C6 profile. Do not promote it without domain-specific definitions, predictions, and empirical comparison.

---

## 27. Reference JSON family declaration

> **Status tag:** reference

```json
{
  "family_id": "hex6",
  "schema_version": "dpfc-family@v5.8",
  "modulus": 6,
  "alphabet": ["h1", "h2", "h3", "h4", "h5", "h6"],
  "digit_order": "listed",
  "bridge": "bijective-positional-v1",
  "successor": "bijective-carry-v1",
  "geometry": {
    "kind": "polygon_progression",
    "dimension_scope": [2],
    "generator_data": {
      "side_count": 6
    },
    "version": "hex6-geometry@v1"
  },
  "witness": {
    "primitive_form": "canonical-side-count",
    "composition_rule": "digit-chain",
    "canonicalization_rule": "identity"
  },
  "degeneracy": {
    "allowed": false
  },
  "serializer": {
    "canonical_shape": "family:<id> schema_version:<version> digits:<ordinals>",
    "display_is_identity": false,
    "version": "canonical-storage@v1"
  },
  "normalizer": {
    "exists": true,
    "version": "hex6-normalizer@v1",
    "accepted_language": "nonempty listed digit tokens"
  },
  "export_policy": {
    "positive_index_map": "iota(mu_n)=n",
    "nonnegative_export": "E_U(mu_n)=n-1",
    "operation_preservation": "iota_only"
  }
}
```

---

## 28. Reference algorithms

> **Status tag:** reference

### 28.1 Core-to-family encoding

```text
encode_core_to_family(n, family):
    require n >= 1
    require family.modulus >= 1
    q = n
    out = empty list
    while q > 0:
        r = ((q - 1) mod family.modulus) + 1
        prepend family.digit[r] to out
        q = (q - r) / family.modulus
    return out
```

### 28.2 Family-to-core evaluation

```text
evaluate_family_word(word, family):
    require word is nonempty
    value = 0 in the exported implementation domain
    for each digit in word from left to right:
        ordinal = family.ordinal(digit)
        require 1 <= ordinal <= family.modulus
        value = value * family.modulus + ordinal
    return mu_value
```

The algorithm uses ordinary implementation integers internally. The mathematical value returned is the core magnitude indexed by the computed value.

### 28.3 Core realized-step addition by index

```text
core_realized_step_add(mu_m, mu_n):
    m = iota(mu_m)
    n = iota(mu_n)
    return mu_(m + n)
```

### 28.4 Nonnegative export correction

```text
exported_nonnegative_add_result(mu_m, mu_n):
    a = E_U(mu_m)
    b = E_U(mu_n)
    return a + b + 1
```

---

## 29. Final statement

> **Status tag:** reference

DPFC v5.8 is a disciplined, one-based, family-native calculus for realized magnitudes, scalar roles, witness geometry, canonical identity, and inter-family conversion.

It is intentionally modular:

1. the arithmetic core remains small;
2. the witness layer is richer;
3. the transport adapter is explicit;
4. the physics analogy is carefully bounded;
5. the research layer is measurable and falsifiable;
6. the export boundary is explicit;
7. realized-step addition is not confused with ordinary zero-based addition.

The v5.8 guiding rule is:

> Keep the core mathematically simple, keep witnesses identity-rich, keep transport subordinate to validation, keep analogies labeled, keep export policies explicit, and cut any family or metric that fails its tests.

---

# Appendix A - formal proof layer

> **Status tag:** reference

## A.1 Proof-layer assumptions

The following assumptions are active for C2 theorem candidates in the DPFC v5.8 core.

### A.1.1 Finite ordered alphabet assumption

Each valid finite family \(F\) has a finite digit alphabet:

\[
\Delta_F=(\delta^{(F)}_1,\ldots,\delta^{(F)}_{b_F})
\]

with \(b_F\geq1\), all symbols distinct, and deterministic digit order.

### A.1.2 Nonempty word assumption

The native family language is:

\[
\mathbb{M}^{+}_F=\Delta_F^+.
\]

Empty words are not native magnitudes.

### A.1.3 Positional evaluation assumption

For \(M=\delta^{(F)}_{i_1}\cdots\delta^{(F)}_{i_k}\),

\[
\operatorname{val}_F(M)=\sum_{j=1}^{k} i_j b_F^{k-j}.
\]

### A.1.4 Core bridge assumption

\[
\Phi_F(M)=\mu_{\operatorname{val}_F(M)}.
\]

### A.1.5 Core successor assumption

\[
\operatorname{usucc}(\mu_n)=\mu_{n+1}.
\]

### A.1.6 Core realized-step addition assumption

\[
\iota(\mu_m\oplus_u\mu_n)=m+n.
\]

### A.1.7 Core multiplication assumption

\[
\iota(\mu_m\otimes_u\mu_n)=m\cdot n.
\]

## A.2 Lemma A1 - bijective remainder lemma

For every integer \(q\geq1\) and every \(b\geq1\), the value:

\[
r=((q-1)\bmod b)+1
\]

is the unique integer in \(\{1,\ldots,b\}\) such that \(q-r\) is divisible by \(b\).

### Proof sketch

Because \((q-1)\bmod b\in\{0,\ldots,b-1\}\), adding one gives \(r\in\{1,\ldots,b\}\). Also, \(q-1-(r-1)\) is divisible by \(b\), hence \(q-r\) is divisible by \(b\). Uniqueness follows from uniqueness of the ordinary modular remainder.

## A.3 Lemma A2 - termination of inverse encoding

For every \(n\geq1\), the inverse encoding algorithm terminates.

### Proof sketch

At each step, \(q\) is replaced by:

\[
q'=(q-r)/b.
\]

Because \(1\leq r\leq b\) and \(r\leq q\) at active steps, \(q'\) is a nonnegative integer strictly smaller than \(q\). Therefore the process terminates.

## A.4 Lemma A3 - value reconstruction

The inverse encoding algorithm applied to \(n\) returns a word \(M\) such that:

\[
\operatorname{val}_F(M)=n.
\]

### Proof sketch

The algorithm repeatedly extracts the unique bijective-base remainder and quotient. Reconstructing the positional expansion from the extracted digits yields the original integer \(n\).

## A.5 Lemma A4 - uniqueness of bijective expansion

If two words \(M,N\in\Delta_F^+\) satisfy:

\[
\operatorname{val}_F(M)=\operatorname{val}_F(N),
\]

then \(M=N\).

### Proof sketch

Apply the unique remainder lemma to the shared value. The final digit of each word must be the same unique remainder. Removing that digit and dividing by \(b_F\) gives the same quotient. Induct on the quotient length.

## A.6 Theorem A1 - canonical representation theorem

For every valid finite family \(F\) and every \(\mu_n\in\mathbb{U}^{+}\), there is exactly one \(M\in\mathbb{M}^{+}_F\) such that:

\[
\Phi_F(M)=\mu_n.
\]

### Exact preservation statement

The bridge \(\Phi_F\) is a bijection between \(\mathbb{M}^{+}_F\) and \(\mathbb{U}^{+}\).

### Proof sketch

Existence follows from Lemmas A2 and A3. Uniqueness follows from Lemma A4.

## A.7 Theorem A2 - successor bridge theorem

For every \(M\in\mathbb{M}^{+}_F\):

\[
\Phi_F(\operatorname{fsucc}_F(M))=\operatorname{usucc}(\Phi_F(M)).
\]

### Exact preservation statement

Family successor preserves the core successor relation.

### Proof sketch

Let \(\operatorname{val}_F(M)=n\). The bijective successor algorithm maps the unique word for \(n\) to the unique word for \(n+1\). Therefore:

\[
\Phi_F(\operatorname{fsucc}_F(M))=\mu_{n+1}=\operatorname{usucc}(\mu_n)=\operatorname{usucc}(\Phi_F(M)).
\]

## A.8 Theorem A3 - family realized-step addition preservation

For all \(M,N\in\mathbb{M}^{+}_F\):

\[
\Phi_F(M\oplus_F N)=\Phi_F(M)\oplus_u\Phi_F(N).
\]

### Exact preservation statement

Family realized-step addition preserves positive-index addition through \(\Phi_F\).

### Proof sketch

By definition:

\[
M\oplus_F N=\Phi_F^{-1}(\Phi_F(M)\oplus_u\Phi_F(N)).
\]

Apply \(\Phi_F\) to both sides.

## A.9 Theorem A4 - family multiplication preservation

For all \(M,N\in\mathbb{M}^{+}_F\):

\[
\Phi_F(M\otimes_F N)=\Phi_F(M)\otimes_u\Phi_F(N).
\]

### Exact preservation statement

Family multiplication preserves positive-index multiplication through \(\Phi_F\).

### Proof sketch

By definition:

\[
M\otimes_F N=\Phi_F^{-1}(\Phi_F(M)\otimes_u\Phi_F(N)).
\]

Apply \(\Phi_F\) to both sides.

## A.10 Theorem A5 - nonnegative export correction theorem

For all \(\mu_m,\mu_n\in\mathbb{U}^{+}\):

\[
E_{\mathbb{U}}(\mu_m\oplus_u\mu_n)=E_{\mathbb{U}}(\mu_m)+E_{\mathbb{U}}(\mu_n)+1.
\]

### Exact preservation statement

The nonnegative export map preserves realized-step addition only with an affine correction term.

### Proof sketch

\[
E_{\mathbb{U}}(\mu_m\oplus_u\mu_n)
=
E_{\mathbb{U}}(\mu_{m+n})
=
m+n-1.
\]

Also:

\[
E_{\mathbb{U}}(\mu_m)+E_{\mathbb{U}}(\mu_n)+1
=
(m-1)+(n-1)+1
=
m+n-1.
\]

Therefore the correction formula holds.

---

# Appendix B - worked conversion examples

> **Status tag:** reference

## B.1 `hex6` value sequence

| Family numeral | Positional value | Core image |
|---|---:|---|
| `h1` | 1 | \(\mu_1\) |
| `h2` | 2 | \(\mu_2\) |
| `h3` | 3 | \(\mu_3\) |
| `h4` | 4 | \(\mu_4\) |
| `h5` | 5 | \(\mu_5\) |
| `h6` | 6 | \(\mu_6\) |
| `h1 h1` | 7 | \(\mu_7\) |
| `h1 h2` | 8 | \(\mu_8\) |
| `h1 h3` | 9 | \(\mu_9\) |
| `h1 h4` | 10 | \(\mu_{10}\) |

## B.2 `refl3` value sequence

| Family numeral | Positional value | Core image |
|---|---:|---|
| `r1` | 1 | \(\mu_1\) |
| `r2` | 2 | \(\mu_2\) |
| `r3` | 3 | \(\mu_3\) |
| `r1 r1` | 4 | \(\mu_4\) |
| `r1 r2` | 5 | \(\mu_5\) |
| `r1 r3` | 6 | \(\mu_6\) |
| `r2 r1` | 7 | \(\mu_7\) |
| `r2 r2` | 8 | \(\mu_8\) |
| `r2 r3` | 9 | \(\mu_9\) |
| `r3 r1` | 10 | \(\mu_{10}\) |

## B.3 Example conversion

Convert `hex6:h1 h4` to `refl3`.

`hex6:h1 h4` has value:

\[
1\cdot6+4=10.
\]

The `refl3` encoding of ten is `r3 r1`, because:

\[
3\cdot3+1=10.
\]

Therefore:

\[
\Psi_{\mathrm{hex6}\to\mathrm{refl3}}(h_1h_4)=r_3r_1.
\]

The core magnitude is preserved. The source family identity is not preserved except as metadata.

## B.4 Export-boundary example

Let:

\[
M=h_2,\qquad N=h_3.
\]

Then:

\[
\Phi_{\mathrm{hex6}}(M)=\mu_2,
\]

\[
\Phi_{\mathrm{hex6}}(N)=\mu_3.
\]

Core realized-step addition gives:

\[
\mu_2\oplus_u\mu_3=\mu_5.
\]

Positive index export gives:

\[
\iota(\mu_5)=5.
\]

Nonnegative export gives:

\[
E_{\mathbb{U}}(\mu_5)=4.
\]

But:

\[
E_{\mathbb{U}}(\mu_2)+E_{\mathbb{U}}(\mu_3)=1+2=3.
\]

So the correction is required:

\[
1+2+1=4.
\]

This example is a required test vector.

---

# Appendix C - geometry usefulness tests

> **Status tag:** research
> **Related tags:** reference

A geometry-bearing family should not be accepted merely because it renders nicely. It should answer at least one of these questions positively.

## C.1 Canonicalization usefulness

Does geometry affect canonicalization in a deterministic way? For example, does orbit reduction or path reduction select a canonical representative that would otherwise remain ambiguous?

## C.2 Compression usefulness

Does geometry allow a shorter or more regular encoding than a flat symbolic representation after counting codebook cost?

## C.3 Error-detection usefulness

Can invalid geometry reveal malformed witness construction, impossible path words, inconsistent sector identifiers, or impossible side counts?

## C.4 Cognitive/debug usefulness

Does the rendering help human operators or AI systems detect state, drift, family mismatch, or degeneracy faster than an ordinary tuple?

## C.5 Algorithmic usefulness

Does geometry support a canonical traversal, search, clustering, or retrieval strategy used by SRNN or another runtime?

## C.6 Baseline requirement

Every usefulness claim should be compared to a non-geometric baseline. If geometry does not beat the baseline or provide a clearly documented human/debugging value, the family should be labeled display-only or experimental.

---

# Appendix D - status labels for families

> **Status tag:** normative

A family declaration should carry a status.

| Status | Meaning |
|---|---|
| `sketch` | informal idea, not yet testable |
| `experimental` | schema exists, tests incomplete |
| `research-valid` | passes local tests but not normative |
| `normative-reference` | approved as a reference family |
| `deprecated` | retained for history or migration only |
| `rejected` | failed core conformance or utility criteria |

A family should not be called normative merely because it has a clean visual rendering.

---

# Appendix E - claim registry template

> **Status tag:** reference

```yaml
claim_id: DPFC-C2-BRIDGE-SUCCESSOR-001
claim_class: C2
title: Family successor commutes with core successor.
statement: For every valid family F and numeral M, Phi_F(fsucc_F(M)) = usucc(Phi_F(M)).
layer: DPFC core
depends_on:
  - finite ordered alphabet
  - bijective positional evaluation
  - declared successor law
proof_status: proof-sketch-present
implementation_tests:
  - exhaustive short-word successor test
  - randomized property-based successor test
failure_action:
  - mark family invalid
  - block family promotion
  - require schema migration if repaired
```

```yaml
claim_id: DPFC-C2-EXPORT-CORRECTION-001
claim_class: C2
title: Nonnegative export requires affine correction for core realized-step addition.
statement: E_U(mu_m plus_u mu_n) = E_U(mu_m) + E_U(mu_n) + 1.
layer: DPFC export boundary
depends_on:
  - core realized-step addition
  - E_U(mu_n)=n-1
proof_status: proof-present
implementation_tests:
  - export_add_mu2_mu3_equals_4
  - export_add_randomized_correction
failure_action:
  - block adapter conformance
  - require export policy declaration
```

---

# Appendix F - adapter failure cases

> **Status tag:** reference

## F.1 Token-free absence collapse

Failure: an all-inactive Witness8 row is decoded as numeric zero.

Correction: all-inactive row decodes to semantic absence. Numeric zero must use a present row when supported by the profile.

## F.2 Family ID loss

Failure: `kind_flag` is decoded but not stored in the canonical object.

Correction: family identity is part of canonical or metadata identity according to profile.

## F.3 Geometry mismatch

Failure: a row claims a reflection family but lacks orbit or sector fields required by the registry.

Correction: reject or downgrade to generic symbolic form according to policy.

## F.4 Transport-before-semantics violation

Failure: a receiver decodes witness rows before CRC/security validation.

Correction: block semantic decoding until transport validation succeeds.

## F.5 Export-policy silence

Failure: a bridge exports \(\mu_n\) to \(n-1\) and then treats \(\oplus_u\) as ordinary addition.

Correction: declare either positive-index operation preservation or nonnegative affine correction.

## F.6 Retention metric elasticity

Failure: a retention metric changes similarity function after observing results.

Correction: version the metric, freeze extractor and similarity function before evaluation, and report baselines.

---

# Appendix G - reviewer checklist

> **Status tag:** reference

A reviewer should ask:

1. Are all native public document labels one-based?
2. Are zero, absence, origin, invalidity, and numeric zero separated?
3. Is each family bridge bijective?
4. Does successor commute with the core successor?
5. Is \(\oplus_u\) clearly labeled as realized-step addition?
6. Is the export algebra boundary explicit?
7. Is canonical identity independent of display glyphs?
8. Are geometry claims tested against baselines?
9. Is DBP treated as a transport boundary rather than mathematical source of truth?
10. Are WSB2 inactive lanes separated from numeric zero?
11. Are physics analogies labeled C5 rather than C6?
12. Are speculative future profiles prevented from mutating the normative core?
13. Is there a clear rejection path for bad families?
14. Are retention metrics declared through `RetentionMetricSpec`?
15. Do retention reports include baselines, pass rules, and failure actions?


# Appendix H - executable fixture pack and core reference implementation

> **Status tag:** reference

This appendix gives machine-readable fixtures and a minimal reference implementation for the DPFC core. It is intentionally small. Its purpose is to expose ambiguity early and to ensure that examples in the prose can be tested directly.

The reference boundary in this appendix ends at canonical family objects, conversion, export, and witness-side distinctions. A separate higher meta/runtime layer MAY consume those outputs, but it MUST do so without redefining DPFC arithmetic and MUST preserve the normative separations declared in Sections 23.1 through 23.7.

## H.1 Fixture naming rules

> **Status tag:** reference

Fixture identifiers use one-based public labels. Host-language arrays, JSON lists, byte offsets, and external standards may still use their own indexing internally.

Every fixture includes:

1. `fixture_id`;
2. `claim_class`;
3. `status_tag`;
4. `given`;
5. `operation`;
6. `expected`;
7. `failure_action`.

## H.2 YAML fixture pack

> **Status tag:** reference

```yaml
fixture_pack: dpfc-v5.8-core-fixtures
schema_version: dpfc-fixtures@v1
fixtures:
  - fixture_id: DPFC-FIXTURE-1-HEX6-EVALUATE-H1H4
    claim_class: C3
    status_tag: reference
    given:
      family_id: hex6
      modulus: 6
      alphabet: [h1, h2, h3, h4, h5, h6]
      word: [h1, h4]
    operation: evaluate_family_word
    expected:
      positional_value: 10
      core_magnitude: mu_10
      canonical_storage: "family:hex6 schema_version:dpfc-family@v5.8 digits:1 4"
    failure_action: block_hex6_conformance

  - fixture_id: DPFC-FIXTURE-2-HEX6-SUCCESSOR-NON-CARRY
    claim_class: C3
    status_tag: reference
    given:
      family_id: hex6
      word: [h1, h4]
    operation: family_successor
    expected:
      successor_word: [h1, h5]
      source_positional_value: 10
      successor_positional_value: 11
      successor_core_magnitude: mu_11
    failure_action: block_successor_conformance

  - fixture_id: DPFC-FIXTURE-3-HEX6-SUCCESSOR-CARRY
    claim_class: C3
    status_tag: reference
    given:
      family_id: hex6
      word: [h1, h6]
    operation: family_successor
    expected:
      successor_word: [h2, h1]
      source_positional_value: 12
      successor_positional_value: 13
      successor_core_magnitude: mu_13
    failure_action: block_successor_conformance

  - fixture_id: DPFC-FIXTURE-4-REFL3-ENCODE-10
    claim_class: C3
    status_tag: reference
    given:
      family_id: refl3
      modulus: 3
      alphabet: [r1, r2, r3]
      core_magnitude: mu_10
    operation: encode_core_to_family
    expected:
      word: [r3, r1]
      positional_value: 10
      canonical_storage: "family:refl3 schema_version:dpfc-family@v5.8 digits:3 1"
    failure_action: block_refl3_conformance

  - fixture_id: DPFC-FIXTURE-5-FAMILY-CONVERSION-HEX6-TO-REFL3
    claim_class: C3
    status_tag: reference
    given:
      source_family_id: hex6
      source_word: [h1, h4]
      target_family_id: refl3
    operation: family_conversion
    expected:
      source_core_magnitude: mu_10
      target_word: [r3, r1]
      target_core_magnitude: mu_10
      must_preserve: [core_magnitude]
      expected_loss: [source_family_identity_unless_metadata_channel_enabled]
    failure_action: reject_conversion_or_keep_family_experimental

  - fixture_id: DPFC-FIXTURE-6-EXPORT-POLICY-MISMATCH
    claim_class: C3
    status_tag: reference
    given:
      left_core_magnitude: mu_2
      right_core_magnitude: mu_3
      nonnegative_export:
        E_U_mu_2: 1
        E_U_mu_3: 2
    operation: exported_nonnegative_add_without_correction
    expected:
      incorrect_downstream_result: 3
      correct_exported_result: 4
      required_correction: 1
      failure_code: export_policy_mismatch
      trusted_arithmetic_use: false
    failure_action: block_adapter_conformance

  - fixture_id: DPFC-FIXTURE-7-WITNESS8-TOKEN-FREE-ABSENCE
    claim_class: C3
    status_tag: reference
    given:
      witness8_row: [0, 0, 0, 0, 0, 0, 0, 0]
      active_profile: witness8-minsafe@v1
    operation: decode_witness8
    expected:
      decode_status: token_free_absent
      presence_status: structurally_absent
      numeric_zero_inferred: false
      trusted_for_family_core: false
    failure_action: reject_profile_or_decoder

  - fixture_id: DPFC-FIXTURE-8-FAILED-DBP-FRAME
    claim_class: C3
    status_tag: reference
    given:
      frame:
        shape_valid: true
        profile_id: dbp-minsafe@v1
        integrity_check: failed
        payload_kind: witness8
    operation: dbp_ingress
    expected:
      semantic_decode_allowed: false
      normal_form_key_constructed: false
      trusted_memory_write: false
      audit_state: rejected_untrusted_optional
      failure_code: transport_integrity_failed
    failure_action: block_semantic_use
```

## H.3 JSON fixture subset

> **Status tag:** reference

```json
{
  "fixture_pack": "dpfc-v5.8-core-fixtures",
  "schema_version": "dpfc-fixtures@v1",
  "fixtures": [
    {
      "fixture_id": "DPFC-FIXTURE-1-HEX6-EVALUATE-H1H4",
      "claim_class": "C3",
      "status_tag": "reference",
      "given": {
        "family_id": "hex6",
        "modulus": 6,
        "alphabet": ["h1", "h2", "h3", "h4", "h5", "h6"],
        "word": ["h1", "h4"]
      },
      "operation": "evaluate_family_word",
      "expected": {
        "positional_value": 10,
        "core_magnitude": "mu_10",
        "canonical_storage": "family:hex6 schema_version:dpfc-family@v5.8 digits:1 4"
      },
      "failure_action": "block_hex6_conformance"
    },
    {
      "fixture_id": "DPFC-FIXTURE-2-HEX6-SUCCESSOR-NON-CARRY",
      "claim_class": "C3",
      "status_tag": "reference",
      "given": {
        "family_id": "hex6",
        "word": ["h1", "h4"]
      },
      "operation": "family_successor",
      "expected": {
        "successor_word": ["h1", "h5"],
        "source_positional_value": 10,
        "successor_positional_value": 11,
        "successor_core_magnitude": "mu_11"
      },
      "failure_action": "block_successor_conformance"
    },
    {
      "fixture_id": "DPFC-FIXTURE-5-FAMILY-CONVERSION-HEX6-TO-REFL3",
      "claim_class": "C3",
      "status_tag": "reference",
      "given": {
        "source_family_id": "hex6",
        "source_word": ["h1", "h4"],
        "target_family_id": "refl3"
      },
      "operation": "family_conversion",
      "expected": {
        "source_core_magnitude": "mu_10",
        "target_word": ["r3", "r1"],
        "target_core_magnitude": "mu_10",
        "must_preserve": ["core_magnitude"],
        "expected_loss": ["source_family_identity_unless_metadata_channel_enabled"]
      },
      "failure_action": "reject_conversion_or_keep_family_experimental"
    }
  ]
}
```

## H.4 Python reference implementation

> **Status tag:** reference

The appendix reference module is the DPFC core boundary only. A conforming meta runtime may wrap these objects in higher-order witnesses, replay bundles, or meta-object assertions, but such logic belongs in a separate module and test surface.

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Family:
    family_id: str
    schema_version: str
    alphabet: tuple[str, ...]

    @property
    def modulus(self) -> int:
        return len(self.alphabet)

    def ordinal(self, digit: str) -> int:
        try:
            return self.alphabet.index(digit) + 1
        except ValueError as exc:
            raise ValueError(f"unknown digit {digit!r} for family {self.family_id}") from exc

    def digit(self, ordinal: int) -> str:
        if ordinal < 1 or ordinal > self.modulus:
            raise ValueError(f"ordinal {ordinal} outside 1..{self.modulus}")
        return self.alphabet[ordinal - 1]


HEX6 = Family("hex6", "dpfc-family@v5.8", ("h1", "h2", "h3", "h4", "h5", "h6"))
REFL3 = Family("refl3", "dpfc-family@v5.8", ("r1", "r2", "r3"))


def evaluate_family_word(word: list[str], family: Family) -> int:
    if not word:
        raise ValueError("native family numerals must be nonempty")
    value = 0
    for digit in word:
        value = value * family.modulus + family.ordinal(digit)
    return value


def encode_core_to_family(n: int, family: Family) -> list[str]:
    if n < 1:
        raise ValueError("core magnitude index must be at least one")
    q = n
    out: list[str] = []
    while q > 0:
        r = ((q - 1) % family.modulus) + 1
        out.insert(0, family.digit(r))
        q = (q - r) // family.modulus
    return out


def family_successor(word: list[str], family: Family) -> list[str]:
    if not word:
        raise ValueError("native family numerals must be nonempty")
    out = list(word)
    pos = len(out) - 1
    while pos >= 0:
        ordinal = family.ordinal(out[pos])
        if ordinal < family.modulus:
            out[pos] = family.digit(ordinal + 1)
            return out
        out[pos] = family.digit(1)
        pos -= 1
    return [family.digit(1)] + out


def canonical_storage(word: list[str], family: Family) -> str:
    ordinals = " ".join(str(family.ordinal(digit)) for digit in word)
    return f"family:{family.family_id} schema_version:{family.schema_version} digits:{ordinals}"


def convert_family(word: list[str], source: Family, target: Family) -> list[str]:
    core_index = evaluate_family_word(word, source)
    return encode_core_to_family(core_index, target)


def nonnegative_export(core_index: int) -> int:
    if core_index < 1:
        raise ValueError("core index must be positive")
    return core_index - 1


def exported_nonnegative_add_with_correction(left_index: int, right_index: int) -> int:
    return nonnegative_export(left_index) + nonnegative_export(right_index) + 1


def decode_witness8(row: Any, *, profile_declares_numeric_zero: bool = False) -> dict[str, Any]:
    if isinstance(row, Mapping):
        values = [
            row.get("value_norm", 0),
            row.get("n_sides_norm", 0),
            row.get("center_on", 0),
            row.get("activation_density", 0),
            row.get("kind_flag", 0),
            row.get("band_position", 0),
            row.get("parity", 0),
            row.get("degeneracy", 0),
        ]
    else:
        values = list(row)
    if len(values) != 8:
        return {"decode_status": "present_invalid", "trusted_for_lookup": False}
    if all(v == 0 for v in values):
        return {"decode_status": "token_free_absent", "presence_status": "structurally_absent", "numeric_zero_inferred": False}
    if profile_declares_numeric_zero and values[0] == 0:
        return {"decode_status": "decoded_exact", "presence_status": "present_zero_value", "numeric_zero_inferred": True}
    return {"decode_status": "decoded_lossy", "presence_status": "present_nonzero_value"}


def validate_dbp_frame(frame: Mapping[str, Any]) -> dict[str, Any]:
    if not frame.get("shape_valid", False):
        return {"semantic_decode_allowed": False, "failure_code": "frame_shape_invalid"}
    if frame.get("integrity_check") != "passed":
        return {"semantic_decode_allowed": False, "normal_form_key_constructed": False, "trusted_memory_write": False, "failure_code": "transport_integrity_failed"}
    return {"semantic_decode_allowed": True, "failure_code": None}


def run_reference_self_test() -> None:
    assert evaluate_family_word(["h1", "h4"], HEX6) == 10
    assert family_successor(["h1", "h4"], HEX6) == ["h1", "h5"]
    assert family_successor(["h6"], HEX6) == ["h1", "h1"]
    assert family_successor(["h1", "h6"], HEX6) == ["h2", "h1"]
    assert encode_core_to_family(10, REFL3) == ["r3", "r1"]
    assert convert_family(["h1", "h4"], HEX6, REFL3) == ["r3", "r1"]
    assert exported_nonnegative_add_with_correction(2, 3) == 4
    assert decode_witness8([0, 0, 0, 0, 0, 0, 0, 0])["decode_status"] == "token_free_absent"
    failed = validate_dbp_frame({"shape_valid": True, "integrity_check": "failed"})
    assert failed["semantic_decode_allowed"] is False


if __name__ == "__main__":
    run_reference_self_test()
    print("DPFC v5.8 reference self-test passed")
```


# Appendix K - EDO, temperament, and circle-family profiles

> **Status tag:** research
> **Related tags:** reference

This appendix imports the useful parts of the acoustics, harmony, temperament, Fourier, and 31-EDO source document as a bounded DPFC research/reference profile. It does not change the DPFC core. It gives DPFC a concrete worked example of a finite, modular, geometric, temperament-aware family whose conversion behavior is sometimes exact, sometimes approximate, and sometimes intentionally lossy.

## K.1 Import boundary

> **Status tag:** research
> **Related tags:** reference

The acoustics source document is useful because it links vibration, spectra, roughness, tuning systems, equal divisions of the octave, 31-EDO, and circle-of-diesis geometry. DPFC imports the following ideas as reference/research material:

1. equal-step families;
2. modular pitch-class spaces;
3. ratio-to-step approximation;
4. temperament error budgets;
5. circle geometries with different generators;
6. enharmonic separation as family-local identity;
7. comma tempering as declared equivalence;
8. timbre/spectrum as a reason families may differ.

DPFC does not import the following as core truth:

1. `31-EDO` as the universal Duotronic family;
2. musical consonance as mathematical truth;
3. movable musical zero as native DPFC public labeling;
4. Fourier analysis as mandatory canonical witness representation;
5. any music-theory naming scheme as required DPFC ontology.

## K.2 External-zero boundary for EDO systems

> **Status tag:** normative

EDO theory conventionally uses pitch class `0` as a movable root, tonic, or reference. DPFC may use that convention only inside an explicitly marked external/reference domain.

For a DPFC-native wrapper around an EDO with `N` steps, define one-based native step labels:

```text
e1, e2, ..., eN
```

and an external EDO step bridge:

```text
external_step(e_i) = i - 1
native_label(k) = e_(k + 1)       for 0 <= k < N
```

Thus, the external EDO pitch class `0` maps to the native DPFC label `e1`. The external zero is a reference position, not native structural absence.

## K.3 EDOFamilyProfile

> **Status tag:** reference

```yaml
EDOFamilyProfile:
  profile_id: edo-family-profile@v1
  family_id: edo31
  status_tag: research
  kind: equal_temperament_family
  period: octave
  step_count: 31
  external_step_domain: "0..30 modulo 31"
  native_label_domain: "e1..e31"
  step_ratio: "2^(1/31)"
  step_cents: 38.7096774194
  notation:
    edostep: "k\\31"
    ratio: "p/q"
  canonical_geometry:
    - circle_of_diesis
    - circle_of_fifths_31
  approximation_bridge: ratio_to_nearest_step
  temperament_policy: declared_error_budget
```

## K.4 EDOstep notation

> **Status tag:** reference

`k\N` means `k` equal steps in `N`-EDO. It is not the same as the ratio `k/N`.

Examples:

```text
10\31 = ten steps of 31-EDO
18\31 = eighteen steps of 31-EDO
3/2   = frequency ratio, not an EDO step count
```

A parser MUST distinguish backslash EDOstep notation from slash ratio notation.

## K.5 Modular pitch-class family

> **Status tag:** reference

For `N`-EDO, the external pitch-class operation is modular addition:

```text
transpose(k, t, N) = (k + t) mod N
```

This is external modular pitch-class arithmetic. It is not the DPFC positive-core addition operator. If a DPFC family wraps an EDO, the wrapper must declare the import/export bridge.

## K.6 Circle-of-diesis geometry

> **Status tag:** research
> **Related tags:** reference

In 31-EDO, the circle of diesis arranges external pitch classes in successor order:

```text
0 -> 1 -> 2 -> ... -> 30 -> 0
```

The DPFC-native wrapper renders this as:

```text
e1 -> e2 -> e3 -> ... -> e31 -> e1
```

The circle-of-diesis geometry is useful for:

1. local adjacency;
2. micro-step successor;
3. enharmonic proximity;
4. one-diesis voice-leading;
5. chord-shape visualization.

## K.7 Circle-of-fifths generator in 31-EDO

> **Status tag:** research
> **Related tags:** reference

31-EDO approximates a fifth by external step `18\31`. A generator circle may therefore use:

```text
generator = +18 mod 31
```

Since `gcd(18,31)=1`, repeated fifth-generation visits every pitch class before returning to the start. This is a concrete example of a DPFC family having multiple useful geometries:

1. successor geometry: `+1`;
2. harmonic-generator geometry: `+18`;
3. spelling geometry: enharmonic separation;
4. chord-shape geometry: arcs between notes.

## K.8 Ratio approximation bridge

> **Status tag:** reference

To approximate a just ratio `r` in `N`-EDO:

\[
k=\operatorname{round}(N\log_2 r).
\]

The EDO approximation is:

\[
2^{k/N}.
\]

The error in cents is:

\[
\epsilon=\frac{1200k}{N}-1200\log_2 r.
\]

This bridge is approximate unless the ratio happens to land exactly on an EDO step.

## K.9 TemperamentErrorBudget

> **Status tag:** research
> **Related tags:** reference

```yaml
TemperamentErrorBudget:
  budget_id: edo31-meantone-budget@v1
  family_id: edo31
  unit: cents
  exact_preserve:
    - octave_periodicity
  approximate_preserve:
    - ratio: "5/4"
      target_name: major_third
      nearest_step: "10\\31"
      max_abs_error_cents: 1.0
    - ratio: "7/4"
      target_name: harmonic_seventh
      nearest_step: "25\\31"
      max_abs_error_cents: 2.0
  weaker_preserve:
    - ratio: "3/2"
      target_name: perfect_fifth
      nearest_step: "18\\31"
      note: fifth is flatter than 12-EDO but consistent with meantone character
  expected_loss:
    - pure_ratio_identity
    - automatic_enharmonic_equivalence
```

## K.10 EnharmonicSeparationPolicy

> **Status tag:** research
> **Related tags:** reference

In 12-EDO, C-sharp and D-flat are often collapsed. In 31-EDO, they may be separated.

A common external mapping is:

```text
C  = 0
C# = 2
Db = 3
D  = 5
```

DPFC interpretation:

```yaml
EnharmonicSeparationPolicy:
  source_family: edo31
  target_family: edo12
  separated_in_source:
    C_sharp: 2
    D_flat: 3
  collapsed_in_target:
    C_sharp_or_D_flat: 1
  expected_loss:
    - spelling_identity
    - harmonic_function_hint
    - voice_leading_microstate
```

A normalizer MUST NOT collapse enharmonic distinctions unless the active family/profile declares that collapse.

## K.11 CommaTemperingPolicy

> **Status tag:** research
> **Related tags:** reference

31-EDO can be viewed as a meantone-like system that tempers out the syntonic comma. A reference mapping may use:

```text
2 maps to 31 steps
3 maps to 49 steps
5 maps to 72 steps
```

The syntonic comma is:

\[
81/80 = 3^4/(2^4\cdot 5).
\]

Mapped to steps:

```text
4*49 - 4*31 - 72 = 0
```

This is an example of a declared equivalence relation: the family intentionally treats a small just-ratio difference as a closed tempered identity.

## K.12 Conversion classes for temperament profiles

> **Status tag:** reference

A temperament-aware conversion result should classify each invariant:

| Conversion class | Meaning |
|---|---|
| `exact_preserve` | invariant is preserved exactly |
| `approximate_preserve` | invariant is approximated within declared error |
| `weaker_preserve` | usable but less accurate than an alternative family |
| `expected_loss` | loss is intended and documented |
| `invalid` | conversion not allowed under the active profile |

## K.13 EDO fixtures

> **Status tag:** reference

```yaml
fixture_pack: dpfc-v5.8-edo31-fixtures
schema_version: dpfc-edo-fixtures@v1
fixtures:
  - fixture_id: DPFC-EDO31-FIXTURE-1-MAJOR-THIRD
    claim_class: C4
    status_tag: research
    given:
      family_id: edo31
      ratio: "5/4"
      edo_steps: 31
    operation: approximate_ratio
    expected:
      nearest_step: "10\\31"
      cents: 387.096774
      just_cents: 386.313714
      error_cents_approx: 0.78306
      preservation_class: approximate_preserve
    failure_action: keep_profile_experimental

  - fixture_id: DPFC-EDO31-FIXTURE-2-HARMONIC-SEVENTH
    claim_class: C4
    status_tag: research
    given:
      family_id: edo31
      ratio: "7/4"
      edo_steps: 31
    operation: approximate_ratio
    expected:
      nearest_step: "25\\31"
      cents: 967.741935
      just_cents: 968.825906
      error_cents_approx: -1.08397
      preservation_class: approximate_preserve
    failure_action: keep_profile_experimental

  - fixture_id: DPFC-EDO31-FIXTURE-3-TRANSPOSITION
    claim_class: C3
    status_tag: reference
    given:
      chord_external_steps: [0, 11, 18]
      transposition: 5
      modulus: 31
    operation: transpose_mod_n
    expected:
      transposed_chord_external_steps: [5, 16, 23]
      preserved: [internal_step_distances, family_id, modulus]
      expected_loss: [absolute_root_unless_metadata_preserved]
    failure_action: reject_edo_transposition_profile

  - fixture_id: DPFC-EDO31-FIXTURE-4-ENHARMONIC-SEPARATION
    claim_class: C4
    status_tag: research
    given:
      source_family: edo31
      C_sharp_external_step: 2
      D_flat_external_step: 3
    operation: compare_pitch_classes
    expected:
      equal_in_edo31: false
      distance_in_diesis: 1
      collapse_allowed_without_policy: false
    failure_action: reject_normalizer

  - fixture_id: DPFC-EDO31-FIXTURE-5-FIFTH-GENERATOR-COVERS-ALL
    claim_class: C2
    status_tag: reference
    given:
      modulus: 31
      generator: 18
    operation: generator_cycle
    expected:
      gcd_generator_modulus: 1
      cycle_length: 31
      visits_all_pitch_classes: true
    failure_action: reject_generator_geometry
```

## K.14 EDO reference implementation

> **Status tag:** reference

```python
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd, log2


@dataclass(frozen=True)
class EDOFamily:
    family_id: str
    steps: int

    def external_step_to_native_label(self, step: int) -> str:
        return f"e{(step % self.steps) + 1}"

    def native_label_to_external_step(self, label: str) -> int:
        if not label.startswith("e"):
            raise ValueError("native EDO labels must look like e1, e2, ...")
        index = int(label[1:])
        if index < 1 or index > self.steps:
            raise ValueError("native EDO label outside family range")
        return index - 1


EDO31 = EDOFamily("edo31", 31)


def cents_of_step(k: int, edo: EDOFamily = EDO31) -> float:
    return 1200.0 * k / edo.steps


def cents_of_ratio(ratio: str) -> float:
    return 1200.0 * log2(float(Fraction(ratio)))


def approximate_ratio(ratio: str, edo: EDOFamily = EDO31) -> dict[str, float | int | str]:
    just = cents_of_ratio(ratio)
    step = round(edo.steps * log2(float(Fraction(ratio))))
    edo_cents = cents_of_step(step, edo)
    return {
        "nearest_step": step,
        "edostep": f"{step}\\{edo.steps}",
        "cents": edo_cents,
        "just_cents": just,
        "error_cents": edo_cents - just,
    }


def transpose_mod_n(values: list[int], transposition: int, modulus: int) -> list[int]:
    return [(value + transposition) % modulus for value in values]


def internal_step_distances(values: list[int], modulus: int) -> list[int]:
    ordered = list(values)
    return [((ordered[(i + 1) % len(ordered)] - ordered[i]) % modulus) for i in range(len(ordered))]


def generator_cycle(generator: int, modulus: int) -> list[int]:
    out: list[int] = []
    value = 0
    while value not in out:
        out.append(value)
        value = (value + generator) % modulus
    return out


def run_edo_self_test() -> None:
    major_third = approximate_ratio("5/4")
    assert major_third["nearest_step"] == 10
    harmonic_seventh = approximate_ratio("7/4")
    assert harmonic_seventh["nearest_step"] == 25
    assert transpose_mod_n([0, 11, 18], 5, 31) == [5, 16, 23]
    assert internal_step_distances([0, 11, 18], 31) == [11, 7, 13]
    assert EDO31.external_step_to_native_label(0) == "e1"
    assert EDO31.native_label_to_external_step("e1") == 0
    assert gcd(18, 31) == 1
    assert len(generator_cycle(18, 31)) == 31


if __name__ == "__main__":
    run_edo_self_test()
    print("DPFC EDO appendix self-test passed")
```



---

# Appendix L - Duotronic source architecture from the DPFC side

> **Status tag:** reference

DPFC is the mathematical and representational half of Duotronic witness-bearing computation. The Witness Contract is the runtime trust and safety half. DPFC answers the question:

> What kind of object is a family-native Duotronic value?

The Witness Contract answers the question:

> When is a witness fact trusted enough to affect memory, recurrence, policy, transport, or architecture?

This appendix makes the boundary explicit so future implementers do not blur mathematical identity with runtime trust.

## L.1 DPFC responsibilities

> **Status tag:** normative

DPFC owns these source-spec responsibilities:

1. realized positive core magnitudes;
2. the signed gapped scalar line;
3. family-native numeral declarations;
4. bijective positional evaluation;
5. family-to-core bridges;
6. inter-family conversion;
7. family successor and induced arithmetic;
8. family witness and degeneracy declarations;
9. canonical family storage;
10. export-boundary policies;
11. family conformance tests;
12. family-specific proof obligations.

DPFC does not decide when a raw runtime observation is trusted. That authority belongs to the Witness Contract and the policy shield.

## L.2 Witness Contract responsibilities visible to DPFC

> **Status tag:** reference

The Witness Contract owns:

1. validation before trust;
2. canonicalization-before-lookup;
3. transport-before-semantics;
4. lookup memory;
5. recurrent state;
6. event-time control;
7. architectural promotion;
8. policy shielding;
9. retention diagnostics;
10. migration and replay acceptance.

DPFC may expose canonical objects, adapters, and invariants to this runtime layer, but DPFC does not by itself grant runtime authority.

## L.3 Source-spec stack

> **Status tag:** reference

A full Duotronic implementation can be read as a stack:

```text
Duotronic Source Architecture
├── DPFC core
│   ├── positive core magnitudes
│   ├── gapped scalar line
│   ├── finite family numerals
│   ├── family conversion
│   └── export policies
├── Family registry
│   ├── family declarations
│   ├── witness schemas
│   ├── normalizer bindings
│   └── geometry registries
├── Witness Contract
│   ├── L1 extraction
│   ├── L2 recurrence
│   ├── L2M lookup memory
│   ├── L3 event-time control
│   ├── L4 architectural proposals
│   └── L5 policy shield
├── Transport profiles
│   ├── Witness8
│   ├── DBP
│   └── WSB2
├── Diagnostics
│   ├── retention metrics
│   ├── baselines
│   ├── replay checks
│   └── telemetry
└── Research profiles
    ├── EDO and temperament
    ├── spectral witnesses
    ├── QCD analogy
    └── physical-domain profiles
```

The stack is intentionally layered. A lower layer can provide objects and evidence; a higher trust layer decides whether those objects and evidence become authoritative state.

## L.4 Four separations that must never collapse

> **Status tag:** normative

DPFC v5.8 treats these separations as architectural invariants:

1. absence versus numeric zero;
2. raw witness construction versus canonical family identity;
3. transport encoding versus semantic object;
4. analogy or research profile versus proof or conformance.

Any implementation, paper, code generator, or AI agent that collapses these separations is non-conformant with the source architecture.

---

# Appendix M - The absence-zero-origin problem

> **Status tag:** normative

The absence-zero-origin problem is the central reason DPFC exists. Ordinary systems often overload a single value, often zero or a zero-like sentinel, to mean many different things. DPFC rejects that overloading in its native public model.

## M.1 Why ordinary systems overload zero

> **Status tag:** reference

Many host systems use zero because it is computationally convenient:

1. arrays often begin at index zero;
2. memory is often initialized with zero bytes;
3. null pointers are often represented by a zero address;
4. protocol fields may use zero as a default;
5. floating-point formats include positive and negative zero;
6. databases and APIs often use zero-like sentinels for absent data;
7. pitch-class and modular systems often use zero as a reference class.

DPFC does not claim these systems are wrong inside their own domains. It claims that importing this habit into native witness-bearing representation causes semantic collapse.

## M.2 The concepts that must remain distinct

> **Status tag:** normative

DPFC distinguishes at least these concepts:

| Concept | Meaning | Example failure if collapsed |
|---|---|---|
| structural absence | no object is present | absent row decoded as numeric value |
| token-free absence | an inactive transport row | all-inactive Witness8 row treated as numeric zero |
| numeric zero | a real conventional value | present zero discarded as absence |
| invalid payload | malformed object | invalid data enters trusted memory |
| unknown present value | slot exists but value unknown | unknown value treated as empty |
| least realized magnitude | first positive core object | \(\mu_1\) treated as additive identity |
| origin role | coordinate center or reference role | scalar origin confused with magnitude digit |
| display geometry | visual witness layout | rendering treated as arithmetic proof |
| canonical identity | versioned normal family object | raw surface form hashed as identity |
| exported conventional arithmetic | host-domain arithmetic | nonnegative export treated as operation-preserving without correction |

## M.3 Native one-based labels

> **Status tag:** normative

Native public DPFC labels begin at one because a native public family digit denotes a realized position in a finite ordered alphabet. The first digit is a real digit, not absence. The least core magnitude is \(\mu_1\), not empty state.

This does not prohibit ordinary zero in external domains. Instead it forces every zero-bearing external domain to declare an import/export bridge.

## M.4 Where ordinary zero remains legal

> **Status tag:** reference

Ordinary zero may appear in:

1. host-language array indices;
2. byte offsets;
3. DBP wire cells;
4. IEEE floating-point values;
5. conventional nonnegative integers;
6. modular external systems such as EDO pitch classes;
7. CRC fields and cryptographic encodings;
8. debug renderings;
9. physical measurements;
10. exported arithmetic domains.

The rule is not “zero is banned.” The rule is “zero must not be silently reused as native absence, origin, invalidity, and value at the same time.”

## M.5 Worked failure examples

> **Status tag:** reference

### M.5.1 Database failure

A database stores `0` for an unknown measurement. A later process treats `0` as a real measured value. The system can no longer distinguish missing evidence from evidence of zero.

DPFC correction: store semantic state separately from exported value.

### M.5.2 Tensor failure

A sparse tensor uses all-zero rows for inactive lanes. A model later interprets all-zero rows as a real feature vector. The inactive lane enters training as meaningful evidence.

DPFC correction: token-free absence is structural absence under the active transport profile, not numeric zero.

### M.5.3 Packet failure

A DBP frame fails integrity validation but contains plausible semantic values. A receiver decodes the semantic payload anyway.

DPFC/Witness correction: transport validation precedes semantic interpretation.

### M.5.4 Arithmetic export failure

A DPFC implementation exports \(\mu_2\) and \(\mu_3\) to ordinary nonnegative values and adds them without correction. It obtains `1 + 2 = 3`, but the DPFC realized-step addition corresponds to exported value `4` under the declared nonnegative export.

DPFC correction: the export policy must declare whether it preserves positive indices or conventional nonnegative roles.

---

# Appendix N - Duotronic glossary and ontology map

> **Status tag:** reference

This glossary is intentionally redundant with the core text. It exists so implementers, reviewers, and AI agents can look up terms without inferring them from scattered sections.

## N.1 Absence terms

> **Status tag:** reference

| Term | Meaning |
|---|---|
| structural absence | no semantic object exists at a position |
| token-free absence | profile-defined inactive representation, often an all-inactive transport row |
| empty semantic state | declared state meaning no payload is present |
| inactive lane | transport or sparse-row lane that carries no semantic witness |
| rejected untrusted payload | data retained for audit but excluded from trust |
| unknown | a position exists, but its value is not known |
| invalid | a payload is malformed or policy-rejected |

## N.2 Value terms

> **Status tag:** reference

| Term | Meaning |
|---|---|
| realized magnitude | positive core object \(\mu_n\) |
| least realized magnitude | \(\mu_1\), the first core magnitude |
| native family numeral | nonempty word over a declared family alphabet |
| ordinary exported zero | conventional zero obtained at an export boundary |
| origin role | scalar-coordinate center role, not a family digit |
| positive index | ordinary index \(n\) corresponding to \(\mu_n\) |
| nonnegative export | boundary map \(E_{\mathbb U}(\mu_n)=n-1\) |

## N.3 Witness terms

> **Status tag:** reference

| Term | Meaning |
|---|---|
| raw witness | uncanonicalized construction evidence |
| witness history | provenance or construction metadata that may not define canonical identity |
| canonical family object | normalized versioned family object |
| canonical storage object | deterministic storage form suitable for hashing and replay |
| normal-form key | runtime lookup key after canonicalization |
| witness signature | extracted local evidence, often from L1 |
| derived witness | inferred witness not directly observed |

## N.4 Ontology map

> **Status tag:** reference

```text
StructuralPosition
├── structurally_absent
└── present
    ├── unknown
    ├── invalid
    ├── conditional
    └── realized
        ├── raw_witness
        │   ├── surface_form
        │   ├── witness_history
        │   └── geometry_hint
        └── canonical_witness
            ├── DPFC_family_object
            ├── core_magnitude
            ├── export_boundary_image
            └── transport_encoding
```

## N.5 Source object map

> **Status tag:** reference

```text
DPFCFamilyObject
├── family_id
├── schema_version
├── digit_word
├── core_magnitude
├── canonical_storage
├── witness_schema
├── geometry_schema
├── degeneracy_policy
├── normalizer_policy
└── export_policy
```

---

# Appendix O - Related concepts and boundaries

> **Status tag:** reference

DPFC combines known mathematical and engineering ideas under a strict absence/canonicalization discipline. The comparisons below help readers understand what DPFC is and is not.

## O.1 Nullable and optional values

> **Status tag:** reference

Nullable types, `Option<T>`, and `Maybe<T>` separate presence from value. DPFC shares that instinct but extends it into family numerals, witness history, canonical storage, transport encoding, export arithmetic, and runtime trust.

DPFC is not merely an optional type. It is a family-parametric value and witness calculus.

## O.2 SQL NULL

> **Status tag:** reference

SQL `NULL` distinguishes unknown or missing values from ordinary values, but SQL systems often mix `NULL`, `0`, empty string, default row, and invalid state inconsistently across applications. DPFC requires each of these distinctions to be declared at the family or boundary level.

## O.3 IEEE NaN and signed zero

> **Status tag:** reference

IEEE floating-point formats distinguish NaN, infinities, positive zero, and negative zero. DPFC may transport through IEEE values, but DPFC canonical identity must not be defined by accidental floating-point representation unless a transport profile declares it and validates it.

## O.4 Sentinel values

> **Status tag:** reference

Sentinel values are convenient but dangerous. DPFC treats sentinel-like transport rows, such as token-free absence, as profile-specific structural states rather than native numeric values.

## O.5 Tagged unions

> **Status tag:** reference

Tagged unions are close in spirit to DPFC semantic states. DPFC adds family-to-core bridges, witness history, geometry, and export-boundary algebra.

## O.6 Canonical serialization and content-addressed storage

> **Status tag:** reference

DPFC canonical storage is similar to canonical serialization used in hashing, signing, and content-addressed storage. The difference is that DPFC also carries family identity, digit ordinal semantics, witness rules, and export policies.

## O.7 CRDTs and event sourcing

> **Status tag:** reference

CRDTs and event-sourced systems care about replay, convergence, and causality. DPFC itself does not define convergence, but its canonical storage and schema-version discipline are compatible with event-sourced and replayed witness systems.

## O.8 Bijective numeration

> **Status tag:** reference

DPFC family numerals use bijective positional notation. This means native words are nonempty and digits begin at one. The novelty is not the bijective notation alone; it is the integration with witnesses, geometry, canonical storage, and runtime trust.

## O.9 Modular pitch-class spaces

> **Status tag:** reference

EDO and pitch-class systems are useful external-domain examples of modular families. They naturally use external zero-reference classes, so DPFC wraps them with explicit native labels and import/export bridges.

## O.10 Proof-carrying data

> **Status tag:** reference

DPFC witnesses can be read as partial proof-carrying data: the object is accompanied by construction or normalization evidence. However, witness evidence is not automatically proof. It becomes authoritative only after validation and canonicalization.

---

# Appendix P - DPFC theorem registry

> **Status tag:** normative

The theorem registry records proof obligations and conformance implications. A theorem candidate may appear in the prose before it is fully formalized. Its registry entry states assumptions, proof status, tests, and failure action.

## P.1 Theorem registry table

> **Status tag:** reference

| Theorem ID | Name | Claim class | Proof status | Failure action |
|---|---|---|---|---|
| DPFC-T1 | Bijective representation | C2 | proof sketch | mark family invalid |
| DPFC-T2 | Successor bridge preservation | C2 | proof sketch | block family promotion |
| DPFC-T3 | Family conversion preserves core magnitude | C2/C3 | proof sketch + tests | reject conversion |
| DPFC-T4 | Nonnegative export requires affine correction | C2/C3 | proof sketch + fixtures | block adapter conformance |
| DPFC-T5 | Canonical serialization preserves replay identity | C3 | tests required | reject serializer |
| DPFC-T6 | Geometry cannot prove arithmetic without a bridge | C1/C3 | definitional | block proof inflation |
| DPFC-T7 | Token-free absence cannot decode as numeric zero | C3 | fixtures required | reject profile |

## P.2 DPFC-T1: bijective representation

> **Status tag:** normative

Statement:

> Every positive core magnitude has exactly one family numeral in every valid finite DPFC family.

Assumptions:

1. finite ordered alphabet;
2. nonempty word language;
3. bijective positional evaluation;
4. deterministic inverse encoding.

Implementation tests:

1. exhaustive small values;
2. randomized large values;
3. invalid digit rejection;
4. empty word rejection.

Failure action: mark the family invalid.

## P.3 DPFC-T2: successor bridge preservation

> **Status tag:** normative

Statement:

> For every valid family \(F\) and numeral \(M\), \(\Phi_F(\operatorname{fsucc}_F(M))=\operatorname{usucc}(\Phi_F(M))\).

Tests:

1. non-carry successor, such as `h1 h4 -> h1 h5`;
2. one-digit carry, such as `h6 -> h1 h1`;
3. recursive carry, such as `h1 h6 -> h2 h1`;
4. randomized encode-successor-evaluate tests.

Failure action: block family promotion.

## P.4 DPFC-T3: family conversion preserves core magnitude

> **Status tag:** normative

Statement:

> \(\Phi_G(\Psi_{F\to G}(M))=\Phi_F(M)\).

Expected losses may include source-family identity, spelling identity, geometry view, or witness history. These losses are valid only if declared by the conversion profile.

## P.5 DPFC-T4: nonnegative export requires affine correction

> **Status tag:** normative

Statement:

> Under \(E_{\mathbb U}(\mu_n)=n-1\), realized-step addition is not preserved as ordinary nonnegative addition without correction.

Correction:

\[
E_{\mathbb U}(\mu_m\oplus_u\mu_n)=E_{\mathbb U}(\mu_m)+E_{\mathbb U}(\mu_n)+1.
\]

Failure action: block trusted arithmetic use across that export boundary.

## P.6 DPFC-T5: canonical serialization preserves replay identity

> **Status tag:** normative

Canonical storage must be deterministic under pinned schema, serializer, normalizer, and family registry versions. Display glyphs and whitespace must not alter canonical identity unless a display profile explicitly becomes canonical, which the core profile does not allow.

## P.7 DPFC-T6: geometry cannot prove arithmetic without a bridge

> **Status tag:** normative

Geometry may define canonicalization, witness history, orbit reduction, display, and degeneracy. It does not define arithmetic unless the family declares a bridge and successor theorem.

## P.8 DPFC-T7: token-free absence cannot decode as numeric zero

> **Status tag:** normative

A transport profile may declare an all-inactive row as token-free absence. It must not be decoded as numeric zero. A real numeric zero requires a present value representation under a declared external or adapter profile.

---

# Appendix Q - Normalizer profile language

> **Status tag:** normative

Normalizers are central to family trust. A normalizer converts accepted raw input into canonical form or rejects it. Normalizers must be versioned and deterministic.

## Q.1 Required normalizer fields

> **Status tag:** normative

```yaml
normalizer_id: string
normalizer_version: string
input_schema: string
output_schema: string
accepted_language: string
rejected_language: string
deterministic_ordering: string
ambiguity_policy: reject | select_canonical | preserve_metadata
low_confidence_policy: reject | generic_bypass | conditional
canonical_selection_rule: string
failure_codes: [string]
version_affects_identity: true
```

## Q.2 Normalizer classes

> **Status tag:** reference

| Class | Use |
|---|---|
| identity normalizer | surface form is already canonical |
| finite-state normalizer | regular token languages |
| bounded symbolic reducer | finite symbolic expressions |
| path reducer | path words and group-like reductions |
| orbit reducer | geometry/orbit canonical representatives |
| lossy adapter normalizer | boundary profiles with declared expected loss |

## Q.3 Normalizer invariants

> **Status tag:** normative

A normalizer MUST NOT:

1. silently switch family identity;
2. silently switch schema version;
3. alter digit order without migration;
4. allow display glyphs to leak into storage identity;
5. collapse absence into numeric zero;
6. convert invalid input into valid output without failure metadata;
7. change canonical identity without a migration plan.

## Q.4 Example normalizer profile

> **Status tag:** reference

```yaml
normalizer_id: refl3-path-normalizer
normalizer_version: refl3-path-normalizer@v1
input_schema: refl3-raw-path@v1
output_schema: dpfc-family@v5.8
accepted_language: finite mirror-generator words over [a,b]
rejected_language: unknown generators, unregistered sector ids, malformed path metadata
deterministic_ordering: generator_order_then_lexicographic
ambiguity_policy: select_canonical
low_confidence_policy: family_bypass
canonical_selection_rule: lexicographically_smallest_reduced_path
failure_codes:
  - unknown_generator
  - invalid_sector
  - ambiguous_orbit
version_affects_identity: true
```

---

# Appendix R - Geometry, orbits, sectors, and degeneracy

> **Status tag:** normative
> **Related tags:** reference

DPFC is a polygon family calculus, but geometry remains disciplined. Geometry is witness structure, not automatic arithmetic proof.

## R.1 Geometry roles

> **Status tag:** normative

A geometry profile may define:

1. display layout;
2. witness construction;
3. orbit equivalence;
4. sector or chamber membership;
5. path reduction;
6. canonical representative selection;
7. error detection;
8. compression or indexing;
9. debugging views;
10. family-local invariants.

A geometry profile does not define arithmetic unless paired with a valid bridge and successor law.

## R.2 Group-action vocabulary

> **Status tag:** reference

| Term | Meaning |
|---|---|
| generator | primitive operation such as rotation, reflection, or step |
| relation | equation between generator words |
| orbit | set reachable under group or monoid action |
| stabilizer | operations that leave an object fixed |
| representative | selected canonical member of an orbit |
| reduced word | normalized generator word |
| sector | coarse region of geometry |
| chamber | finer canonical region used for reduction |

## R.3 Orbit reduction contract

> **Status tag:** normative

An orbit-reducing family must declare:

1. generator set;
2. admissible words;
3. equivalence relation;
4. reduction order;
5. representative selection;
6. ambiguity policy;
7. witness-history preservation;
8. replay identity fields.

## R.4 Geometry usefulness tests

> **Status tag:** research

A geometry profile should be tested for:

1. canonicalization usefulness;
2. compression usefulness;
3. error-detection usefulness;
4. debugging usefulness;
5. algorithmic usefulness;
6. retention-metric usefulness;
7. baseline improvement over non-geometric representation.

If geometry fails all usefulness tests, the family should be marked display-only or experimental.

## R.5 Example geometry registry entry

> **Status tag:** reference

```yaml
geometry_id: circle-of-diesis-edo31
geometry_version: circle-of-diesis@v1
family_id: edo31
kind: cyclic_modular_geometry
external_modulus: 31
native_label_policy: external_step_k_maps_to_e_{k+1}
generator_views:
  - view_id: successor_geometry
    generator_external_steps: 1
    purpose: local adjacency
  - view_id: fifth_generator_geometry
    generator_external_steps: 18
    purpose: harmonic generation and spelling
canonicalization_policy:
  octave_equivalence: external_mod_31
  spelling_identity: preserve_if_family_local
  collapse_policy: reject_unless_expected_loss
```

---

# Appendix S - Expanded EDO and temperament family profile

> **Status tag:** research
> **Related tags:** reference

The EDO profile is an external-domain research/reference profile. It is useful because it gives DPFC a finite, modular, geometric, approximate, and notation-rich family. It does not become the universal DPFC model.

## S.1 External pitch-class domain

> **Status tag:** reference

An EDO system divides an octave into \(N\) equal logarithmic steps. External pitch classes are usually represented modulo \(N\):

\[
k\in\mathbb Z/N\mathbb Z.
\]

This external domain often uses zero naturally. DPFC wraps it with explicit native labels:

\[
\operatorname{native}(k)=e_{k+1}.
\]

## S.2 EDOstep notation

> **Status tag:** reference

`k\N` denotes `k` steps of an `N`-EDO system. It is not the ratio `k/N`. For example, `10\31` denotes ten steps in 31-EDO.

## S.3 Frequency and cents bridges

> **Status tag:** reference

Ratio to cents:

\[
\operatorname{cents}(p/q)=1200\log_2(p/q).
\]

EDO step to cents:

\[
\operatorname{stepCents}(k,N)=1200k/N.
\]

Nearest EDO step:

\[
\operatorname{nearestStep}_N(p/q)=\operatorname{round}(N\log_2(p/q)).
\]

Error:

\[
\operatorname{errorCents}=1200k/N-1200\log_2(p/q).
\]

## S.4 31-EDO worked interval table

> **Status tag:** reference

| Interval idea | Just ratio | 31-EDO step | Approx cents | Use in DPFC |
|---|---:|---:|---:|---|
| diesis | external step | `1\31` | 38.71 | successor micro-step |
| chromatic semitone | profile-dependent | `2\31` | 77.42 | sharp-like shift |
| diatonic semitone | profile-dependent | `3\31` | 116.13 | flat-like/scale shift |
| whole tone | profile-dependent | `5\31` | 193.55 | meantone step |
| minor third-like | profile-dependent | `8\31` or `9\31` | 309.68 / 348.39 | chord family variants |
| major third | `5/4` | `10\31` | 387.10 | approximate preserve |
| fourth | `4/3` | `13\31` | 503.23 | approximate preserve |
| fifth | `3/2` | `18\31` | 696.77 | generator geometry |
| harmonic seventh | `7/4` | `25\31` | 967.74 | 7-limit profile |

## S.5 Enharmonic separation policy

> **Status tag:** research

In 12-EDO, spellings such as C# and Db often collapse. In 31-EDO, they may remain distinct, such as external steps `2` and `3` under one common mapping. A DPFC normalizer must not collapse these unless the target profile declares expected loss.

```yaml
enharmonic_policy:
  source_family: edo31
  target_family: edo12
  source_distinctions:
    C_sharp_external_step: 2
    D_flat_external_step: 3
  target_collapse: true
  expected_loss:
    - spelling_identity
    - voice_leading_microstate
    - harmonic_function_hint
  collapse_allowed_without_policy: false
```

## S.6 Chord profiles

> **Status tag:** research

31-EDO chord profiles can act as witness patterns:

| External steps | Informal interpretation | Preserved under transposition |
|---|---|---|
| `[0, 11, 18]` | supermajor-like | internal step distances |
| `[0, 10, 18]` | major-like | internal step distances |
| `[0, 9, 18]` | neutral-third-like | internal step distances |
| `[0, 8, 18]` | minor-like | internal step distances |

The absolute root may be expected loss under transposition; the internal interval pattern may be must-preserve.

---

# Appendix T - Conformance harness plan

> **Status tag:** reference

A DPFC implementation should be verified by a conformance harness, not only by prose review.

## T.1 Test pack structure

> **Status tag:** reference

```text
conformance/
├── dpfc-core/
├── families/
├── successor/
├── conversion/
├── export-boundaries/
├── canonical-storage/
├── witness8-adapters/
├── dbp-boundaries/
├── wsb2-boundaries/
├── retention/
├── replay/
├── migration/
└── policy-shield/
```

## T.2 Required test groups

> **Status tag:** normative

A serious DPFC implementation must test:

1. core magnitude encoding;
2. scalar-line translation;
3. family parser validity;
4. bijective evaluation;
5. inverse encoding;
6. successor bridge preservation;
7. family conversion preservation;
8. export-boundary correction;
9. canonical storage stability;
10. witness degeneracy handling;
11. geometry usefulness cases;
12. transport adapter boundaries;
13. token-free absence versus numeric zero;
14. retention metric baseline discipline.

## T.3 Golden traces

> **Status tag:** reference

A golden trace records:

1. input family object;
2. raw witness;
3. canonical storage;
4. core magnitude;
5. export image;
6. transport encoding;
7. expected losses;
8. retention outputs;
9. failure codes;
10. replay version pins.

## T.4 Release gates

> **Status tag:** normative

A release must not promote a family or adapter if:

1. successor bridge tests fail;
2. conversion fails to preserve core magnitude;
3. token-free absence decodes as numeric zero;
4. export algebra is ambiguous;
5. canonical storage changes without migration;
6. geometry is claimed as arithmetic proof;
7. retention metrics lack baselines.

---

# Appendix U - Migration and versioning guide

> **Status tag:** normative
> **Related tags:** reference

Long-lived Duotronic systems require explicit migration. Schema drift is a trust failure unless controlled.

## U.1 Semantic change

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
10. export arithmetic.

Semantic changes require migration and replay checks.

## U.2 Storage-only change

> **Status tag:** reference

A storage-only change changes representation without changing canonical meaning. It still requires deterministic migration tests, but may not require a family version bump if canonical identity is preserved by a declared serializer bridge.

## U.3 Display-only change

> **Status tag:** reference

A display-only change alters rendering but not canonical identity. Display-only changes must not affect hashes, lookup keys, or conversion behavior.

## U.4 Migration plan fields

> **Status tag:** normative

```yaml
migration_id: string
source_schema: string
target_schema: string
affected_families: [string]
affected_normalizers: [string]
must_preserve: [string]
expected_loss: [string]
replay_trace_set: [string]
rollback_plan: string
promotion_boundary: sequence_boundary_only
approval_required: true
```

## U.5 Deprecation and pruning

> **Status tag:** reference

A family or profile can be deprecated when:

1. it fails conformance;
2. it is superseded by a clearer profile;
3. it has no remaining runtime use;
4. it is too costly for measured utility;
5. it causes repeated ambiguity;
6. its analogy language causes proof inflation.

---

# Appendix V - Source corpus map from the DPFC perspective

> **Status tag:** reference

## V.1 Core documents

> **Status tag:** reference

1. Duotronic Source Architecture Overview;
2. Duotronic Polygon Family Calculus;
3. Duotronic Witness Contract;
4. Duotronic Schema Registry;
5. Duotronic Family Registry;
6. Witness8 Profile;
7. DBP Profile;
8. WSB2 Profile;
9. Retention Diagnostics Profile;
10. Policy Shield Guide;
11. Migration and Replay Guide;
12. EDO and Signal Witness Research Profiles;
13. Public/Internal Language Guide.

## V.2 Reading order

> **Status tag:** reference

A new implementer should read:

1. Source Architecture Overview;
2. DPFC Executive Summary;
3. Absence-Zero-Origin Problem;
4. Core Magnitude Calculus;
5. Numeral Families;
6. Inter-Family Conversion;
7. Witness Contract Executive Summary;
8. Normal-Form-Before-Trust;
9. Transport-Before-Semantics;
10. Conformance Harness.


## V.3 Corpus status matrix

> **Status tag:** reference

| Document | Corpus status | Role |
|---|---|---|
| Duotronic Source Architecture Overview | existing | entry point and reading map |
| Duotronic Polygon Family Calculus | existing | mathematical and representational core |
| Duotronic Witness Contract | existing | runtime trust and safety contract |
| Duotronic Schema Registry | draft-needed | canonical identifiers and version matrix |
| Duotronic Family Registry | draft-needed | family declarations, geometry, and normalizers |
| Witness8 Profile | draft-needed | implementation witness-row profile |
| DBP Profile | draft-needed | transport-frame boundary profile |
| WSB2 Profile | draft-needed | sparse-row transport profile |
| Retention Diagnostics Profile | draft-needed | metric specs, baselines, and pass rules |
| Policy Shield Guide | draft-needed | L5 decision tables and bypass policies |
| Migration and Replay Guide | draft-needed | schema migration, replay, rollback, and promotion |
| EDO and Signal Witness Research Profiles | future | bounded research/reference profiles |
| Public/Internal Language Guide | future | naming guidance and external-facing wording |

`existing` means the document is present in the current corpus. `draft-needed` means the role is identified and should become a standalone source document. `future` means the topic is useful but should not be treated as active implementation authority.

---



---

# Appendix Y - Polygon Lab Canonicalization and Geometry Evidence

> **Status tag:** reference

Polygon Lab v4 supplies executable evidence for DPFC's geometry and canonicalization layers. The relevant code-derived objects include `PolygonFamilySpec`, `PolygonConfig`, `CanonicalRecord`, `canonicalize`, `orbit_of`, `enumerate_canonical_catalog`, and `build_operator_adjacency`.

```yaml
code_derived_objects:
  polygon_lab_v4:
    dataclasses: [PolygonFamilySpec, PolygonConfig, CanonicalRecord, VariantFamily, ThetaSpec, RunSpec, BenchmarkSpec, BenchmarkSuiteSpec, GateReport, BenchmarkResult]
    functions: [canonical_json, sha256_id, canonicalize, orbit_of, enumerate_canonical_catalog, build_operator_adjacency, engine_compute, evaluate_gates, build_comparison_artifact]
    adapters: [InProcessToyAdapter, SubprocessJSONAdapter]
  engine_lab_v5:
    dataclasses: [BenchmarkSpec, GateReport, BenchmarkSuiteSpec, ThetaSpec, VariantFamily, RunSpec, EngineExportAdapter]
    parsers: [parse_lammps_log, parse_gpaw_info, parse_gpaw_json, parse_gpaw_log, parse_gpaw_txt]
    functions: [file_digest, evaluate_gates_v5, benchmark_specs_v5, build_variant_family, build_thetas, source_artifacts_for_benchmark, build_run_spec, validate_artifact_schema, run_suite, compare_baseline]
```

## Y.1 DPFC import boundary

> **Status tag:** normative

The lab canonicalization code may inform DPFC family registry profiles, geometry profiles, and conformance fixtures. It MUST NOT redefine DPFC core arithmetic, family successor, bridge preservation, scalar-line semantics, or export-boundary algebra.
