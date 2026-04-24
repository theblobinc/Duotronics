# Duotronic Polygon Family Calculus (DPFC v4.6)

**Status:** Normative project paper  
**Version:** 4.6-draft  
**Supersedes:** DPFC v4.5  
**Authority:** This document is authoritative for DPFC v4.6. Earlier drafts, experiments, transcripts, critiques, and AI-generated notes may inform project history, but they are not normative for this specification.

---

## Abstract

DPFC v4.6 defines a **family-native** duotronic mathematical and numeral ontology.

This document should be read primarily as a **normative specification and design framework** for multi-family zeroless numeration, not as a claim to replace all prior arithmetic or numeration theory. Its main contribution is architectural: it combines family-indexed bijective numeral modules, optional geometry-linked witness semantics, cross-family conversion, and versioned machine-oriented schemas over a shared positive arithmetic core.

The project does not commit to one mandatory bijective modulus such as 10. Instead, it treats **polygon families**, **reflection-derived positive numeral families**, and other declared geometric symbol families as first-class numeral modules. Each family may carry its own:

- native digit alphabet
- native bijective modulus
- native successor and carry law
- canonical order
- witness and degeneracy rules
- rendering profile
- conversion bridge into the shared duotronic core

The duotronic core remains realized-state-first. Primitive native symbols are reserved for realized magnitudes and realized scalar positions. There is no native zero digit in any numeral family. The signed scalar line is gapped and origin-labeled at `1`:

$$
\Lambda = \{\ldots,-4,-3,-2,1,2,3,4,\ldots\}.
$$

The immediate scalar neighbors of the origin are `-2` and `2`.

DPFC v4.6 consists of two layers:

1. a **duotronic core**: abstract realized magnitudes, signed gapped scalars, and duotronic grids
2. a **family layer**: multiple compatible positive polygon-native bijective numeral modules

This paper defines the core ontology, the family schema, native arithmetic inside each family, inter-family congruence and translation, two worked families, proof sketches for bridge preservation, canonical serialization, schema versioning policy, conformance requirements, test vectors, and a positioning statement that situates DPFC relative to existing numeration-system literatures while keeping its focus on implementation-grade formalization.

---

## 1. Why this revision exists

Earlier drafts explored a fixed bijective-10 system. That is no longer treated as the project's final shape.

The present direction is broader:

- there are many meaningful polygon families
- there are many meaningful reflection-derived positive numeral families
- different families can support different natural bijective moduli
- those families can still participate in one connected duotronic mathematics

So DPFC v4.6 does **not** ask:

> which single bijective base should rule everything?

It asks instead:

> how can multiple polygon-native bijective families coexist inside one realized-state mathematical ontology?

That is the central shift of the current project.


### 1.1 Position relative to existing numeration-system work

DPFC does not arise in an empty theoretical space. Zeroless positional notation, abstract numeration systems on ordered languages, automata-based arithmetic, signed-digit frameworks, and negative-base representations are all established areas of mathematics and theoretical computer science. DPFC therefore should not be read as the first appearance of zeroless or family-indexed numeration in the abstract.

What distinguishes DPFC is the combination of:

- family-indexed bijective numeral modules
- optional geometry-linked witness semantics
- a shared positive arithmetic core
- a signed gapped scalar ontology
- canonical machine serialization with schema versioning
- explicit inter-family conversion rules

### 1.2 Contribution boundary and genre

This document is a **normative specification first**. It defines how to declare a family, how to bridge it into the core, how to serialize it canonically, and how to test conformance. A conventional research paper built on DPFC may use this document as its formal reference, but stronger claims about novelty, empirical usability, or geometry-dependent arithmetic require separate argument and validation.

In particular, DPFC v4.6 should be understood as a family-parameterized representational layer over a shared positive arithmetic core, together with optional geometry-tracking semantics. It is not presented as a proof that standard arithmetic is false or obsolete.

---

## 2. Design stance

DPFC v4.6 adopts the following design stance.

1. **Realized-state priority.** Native symbols denote realized magnitudes or realized scalar positions. Null is not a native numeral value.
2. **No native zero digit.** No numeral family is required to allocate one of its primitive digit symbols to a zero digit.
3. **Family plurality.** There is no globally mandatory bijective modulus. Different native families may carry different moduli.
4. **Core congruence.** Distinct native families are still comparable because they map into a shared duotronic core magnitude semantics.
5. **Signed gapped scalar ontology.** The native scalar line is not centered on `0`; it is centered on the origin label `1`, with `-2` and `2` as immediate neighbors.
6. **Families are positive-only.** Numeral families represent positive realized magnitudes only. Polarity and sign belong to the scalar ontology, not to family digit alphabets.
7. **Geometry matters.** Polygon or reflection family choice is not merely decorative. It governs the native alphabet, carry law, witness rules, degeneracy rules, and representation profile of a numeral family.
8. **External numeral systems are secondary.** Decimal, binary, hexadecimal, and other conventional systems may be used at interfaces, but they are not the source of truth for native DPFC semantics.
9. **Cosmic orientation.** The project is not framed as a ledger or bookkeeping notation. It is framed as a language for realized magnitudes, displacement, and structured geometry.

### 2.1 What “duotronic” means

The term **duotronic** refers to two structural dualities that define the calculus:

1. the two-branch scalar ontology (positive and negative branches around the origin label `1`)
2. the dual-layer architecture of the system (core magnitude semantics plus family-native numeral realization)

---

## 3. The duotronic core

DPFC v4.6 separates **core mathematical ontology** from **family-specific numeral realization**.

### 3.1 Core realized magnitudes

The core realized magnitude domain is a well-ordered positive domain:

$$
\mathbb{U}^{+} = \{\mu_1, \mu_2, \mu_3, \ldots\}.
$$

This domain is family-independent.

Interpretation:

- `\mu_1` is the least realized magnitude
- `\mu_{n+1}` is the successor of `\mu_n`
- every native numeral family must map its realized numerals into this domain

**Clarification.** $\mathbb{U}^{+}$ is the abstract, dimensionless order of realized presence. It does not possess intrinsic side-count or intrinsic polygon shape. Side-count and visible shape arise only upon selecting a family projection.

### 3.2 Core magnitude successor

Define the core successor:

$$
\operatorname{usucc}(\mu_n)=\mu_{n+1}.
$$

### 3.3 Core magnitude order

The order on $\mathbb{U}^{+}$ is:

$$
\mu_1 < \mu_2 < \mu_3 < \cdots
$$

This is the shared order used for inter-family comparison.

### 3.4 Core arithmetic

Define core addition recursively:

$$
\mu_m \oplus_u \mu_1 = \operatorname{usucc}(\mu_m)
$$

$$
\mu_m \oplus_u \operatorname{usucc}(\mu_n) = \operatorname{usucc}(\mu_m \oplus_u \mu_n).
$$

Define core multiplication recursively:

$$
\mu_m \otimes_u \mu_1 = \mu_m
$$

$$
\mu_m \otimes_u \operatorname{usucc}(\mu_n) = (\mu_m \otimes_u \mu_n) \oplus_u \mu_m.
$$

These laws make the core the shared positive arithmetic target of all family numeral systems.

### 3.5 Induced family arithmetic principle

Family arithmetic is not independently invented and then compared to the core afterward. It is **induced by the core through the bridge**.

For any family $F$, the intended semantics are:

$$
M \oplus_F N = \Phi_F^{-1}(\Phi_F(M) \oplus_u \Phi_F(N))
$$

$$
M \otimes_F N = \Phi_F^{-1}(\Phi_F(M) \otimes_u \Phi_F(N)).
$$

The recursive family definitions in later sections are therefore not alternative laws. They are native presentations of the core-induced laws.

---

## 4. The signed gapped scalar line

The native scalar domain is:

$$
\Lambda = \{\ldots,-4,-3,-2,1,2,3,4,\ldots\}.
$$

The order is:

$$
\cdots < -4 < -3 < -2 < 1 < 2 < 3 < 4 < \cdots
$$

### 4.1 Core scalar roles

To reduce label confusion, the system distinguishes **role names** from **serialized labels**.

- **origin**: serialized as `1`
- **unit**: serialized as `2`
- **anti-unit**: serialized as `-2`

These role names are pedagogical aliases only. The normative labels remain `1`, `2`, and `-2`.

**Important clarification.** DPFC rejects a **zero digit** and rejects centering the scalar line on `0`, but it does **not** remove the zero-role entirely. The zero-role is realized by the origin label `1` in the scalar ontology.

### 4.2 Core scalar properties

1. `1` is the native origin label.
2. `2` is the first positive scalar unit label.
3. `-2` is the first negative scalar unit label.
4. The labels `0` and `-1` are excluded from $\Lambda$.

### 4.3 Scalar successor and predecessor

Define scalar successor and predecessor as adjacency on $\Lambda$:

$$
\operatorname{ssucc}(-2)=1, \qquad \operatorname{ssucc}(1)=2
$$

$$
\operatorname{spred}(2)=1, \qquad \operatorname{spred}(1)=-2
$$

and similarly along the whole line.

Both are total on $\Lambda$.

### 4.4 Native step metric

The native scalar line carries a graph-step metric induced by adjacency.

Define the native distance:

$$
d_\Lambda(a,b)=\text{the least number of successor/predecessor steps joining }a\text{ to }b.
$$

Examples:

$$
d_\Lambda(1,2)=1
$$

$$
d_\Lambda(1,-2)=1
$$

$$
d_\Lambda(-2,2)=2.
$$

This native step metric is part of what distinguishes the gapped scalar ontology from ordinary integer labeling.

### 4.5 Core scalar translation by magnitude

Every core magnitude $\mu_n$ defines rightward and leftward translations on $\Lambda$.

Rightward translation:

$$
T_{+}(s,\mu_1)=\operatorname{ssucc}(s)
$$

$$
T_{+}(s,\operatorname{usucc}(\mu_n)) = \operatorname{ssucc}(T_{+}(s,\mu_n)).
$$

Leftward translation:

$$
T_{-}(s,\mu_1)=\operatorname{spred}(s)
$$

$$
T_{-}(s,\operatorname{usucc}(\mu_n)) = \operatorname{spred}(T_{-}(s,\mu_n)).
$$

So:

$$
T_{+}(1,\mu_1)=2
$$

$$
T_{-}(1,\mu_1)=-2.
$$

### 4.6 Translation-distance lemma

For every scalar $s$ and every core magnitude $\mu_n$:

$$
d_\Lambda(s, T_{+}(s,\mu_n)) = n
$$

and

$$
d_\Lambda(s, T_{-}(s,\mu_n)) = n.
$$

So the native metric is not decorative. It measures exactly the displacement induced by core magnitude translation.

---

## 5. The duotronic grid

The duotronic grid in dimension $n$ is:

$$
\mathbb{D}^{n} = \Lambda^{n}.
$$

So a point in the grid is an $n$-tuple:

$$
(x_1,x_2,\ldots,x_n)
\qquad \text{with each } x_i \in \Lambda.
$$

### 5.1 Grid properties

1. The native origin point is:
   $$
   (1,1,\ldots,1).
   $$
2. There are no grid coordinates equal to `0` or `-1`.
3. The immediate scalar neighbors of each axis-origin coordinate are `-2` and `2`.
4. Translation is defined componentwise by $T_{+}$ and $T_{-}$.

---

## 6. Numeral families

The numeral layer of DPFC v4.6 is family-based.

A **numeral family** is a declared positive-magnitude profile:

$$
F = (\mathrm{name},\ b_F,\ \Delta_F,\ \prec_F,\ \operatorname{fsucc}_F,\ \Phi_F,\ \mathrm{render}_F,\ \mathrm{witness}_F,\ \mathrm{degeneracy}_F,\ \mathrm{geometry}_F)
$$

where:

- $\mathrm{name}$ is the family identifier
- $b_F$ is the family's bijective modulus
- $\Delta_F$ is the ordered native digit alphabet
- $\prec_F$ is the digit order
- $\operatorname{fsucc}_F$ is the family successor/carry law
- $\Phi_F$ is the family-to-core magnitude map
- $\mathrm{render}_F$ is the rendering policy
- $\mathrm{witness}_F$ is the family witness schema
- $\mathrm{degeneracy}_F$ is the family degeneracy schema
- $\mathrm{geometry}_F$ is the family geometry schema

### 6.1 Family magnitude domain

For each family $F$, the native positive numeral domain is:

$$
\mathbb{M}^{+}_F = \{\text{finite nonempty chains over } \Delta_F\}.
$$

Each $\mathbb{M}^{+}_F$ is a full native numeral language for that family.

### 6.2 Family digit completeness axiom

For each family $F$, the $b_F$ primitive digits of $\Delta_F$ denote the first $b_F$ realized magnitudes of that family.

No family digit denotes native zero.

### 6.3 Family scope restriction

Numeral families are **positive magnitude alphabets only**. They do not carry native negative signs or polarity markers. Sign and branch belong exclusively to the scalar domain $\Lambda$.

---

## 7. Family schema requirements

To prevent the family calculus from collapsing into an under-specified zoo, DPFC v4.6 requires every family to satisfy a concrete schema.

### 7.1 Geometry schema

$\mathrm{geometry}_F$ must declare:

- `kind`: one of
  - `polygon_progression`
  - `reflection_family`
  - `net_family`
  - `custom_declared_family`
- `dimension_scope`: a positive integer or a finite set of supported dimensions
- `generator_data`: the data needed to reconstruct the family geometry

Examples of valid `generator_data`:

- ordered polygon side-count list
- Coxeter-style diagram data
- reflection-group generator list
- net/degeneration recipe
- other profile-declared structured data

### 7.2 Witness schema

$\mathrm{witness}_F$ must declare how a family digit or numeral is geometrically realized.

At minimum it must specify:

- primitive digit witness form
- admissible composition rule for multi-digit numerals
- canonicalization rule for equivalent witnesses

### 7.3 Degeneracy schema

$\mathrm{degeneracy}_F$ must specify whether multiple distinct witnesses may realize the same family numeral.

At minimum it must declare:

- whether degeneracy is allowed
- if allowed, the equivalence relation on witnesses
- whether one canonical witness is selected
- whether all witnesses must be preserved as metadata

### 7.4 Implementation note

A family declaration is intended to be machine-validatable. Appendix B provides concrete JSON-shaped examples for worked family profiles.

---

## 8. Family-native successor, order, and arithmetic

Each family defines its own internal numeral laws.

### 8.1 Family successor

Let:

$$
\Delta_F = (\delta^{(F)}_1,\delta^{(F)}_2,\ldots,\delta^{(F)}_{b_F}).
$$

Then the family successor satisfies:

$$
\operatorname{fsucc}_F(\delta^{(F)}_i)=\delta^{(F)}_{i+1}
\qquad \text{for } 1 \le i < b_F
$$

and for a nonempty numeral prefix $X$:

$$
\operatorname{fsucc}_F(X\delta^{(F)}_{b_F}) = \operatorname{fsucc}_F(X)\delta^{(F)}_1.
$$

The one-digit carry boundary case is:

$$
\operatorname{fsucc}_F(\delta^{(F)}_{b_F}) = \delta^{(F)}_1\delta^{(F)}_1.
$$

### 8.2 Family order

Each family numeral domain is ordered by:

1. shorter length is smaller
2. equal length compares lexicographically by the declared digit order $\prec_F$

### 8.3 Family addition

For each family $F$, define native family addition recursively:

$$
M \oplus_F \delta^{(F)}_1 = \operatorname{fsucc}_F(M)
$$

$$
M \oplus_F \operatorname{fsucc}_F(N) = \operatorname{fsucc}_F(M \oplus_F N).
$$

This defines total addition on $\mathbb{M}^{+}_F \times \mathbb{M}^{+}_F$.

There is no additive identity inside $\mathbb{M}^{+}_F$.

**Clarification.** These recursive presentations are the native, family-specific form of the core-induced arithmetic defined in Section 3.5.

### 8.4 Family multiplication

For each family $F$, define multiplication by repeated family addition:

$$
M \otimes_F \delta^{(F)}_1 = M
$$

$$
M \otimes_F \operatorname{fsucc}_F(N) = (M \otimes_F N) \oplus_F M.
$$

So the least family digit acts as multiplicative identity.

**Clarification.** These recursive presentations are the native, family-specific form of the core-induced arithmetic defined in Section 3.5.

---

## 9. Family-to-core congruence

Each family numeral domain maps into the shared core realized magnitudes.

For each family $F$, define a bijection:

$$
\Phi_F : \mathbb{M}^{+}_F \to \mathbb{U}^{+}
$$

such that:

1. the least family digit maps to the least core magnitude:
   $$
   \Phi_F(\delta^{(F)}_1)=\mu_1
   $$
2. family successor commutes with core successor:
   $$
   \Phi_F(\operatorname{fsucc}_F(M)) = \operatorname{usucc}(\Phi_F(M))
   $$

This is the key coherence law of DPFC v4.6.

### 9.1 Consequences

Because of this law:

- every family numeral denotes a unique core magnitude
- families can be compared without privileging one family's digits over another
- addition and multiplication are preserved across families via the core

### 9.2 Inter-family conversion

For families $F$ and $G$, define conversion:

$$
\Psi_{F\to G} = \Phi_G^{-1} \circ \Phi_F.
$$

This converts a numeral in family $F$ into the unique numeral in family $G$ with the same core realized magnitude.

### 9.3 Isomorphism theorem

For every family $F$:

$$
\Phi_F : (\mathbb{M}^{+}_F, \oplus_F, \otimes_F) \to (\mathbb{U}^{+}, \oplus_u, \otimes_u)
$$

is an arithmetic isomorphism.

This theorem is not a concession. It is the formal statement of DPFC coherence.

### 9.4 Proof sketch

Addition preservation is proved by induction on the second argument.

Base case:

$$
\Phi_F(M \oplus_F \delta^{(F)}_1)
=
\Phi_F(\operatorname{fsucc}_F(M))
=
\operatorname{usucc}(\Phi_F(M))
=
\Phi_F(M) \oplus_u \mu_1.
$$

Inductive step:

if
$$
\Phi_F(M \oplus_F N)=\Phi_F(M)\oplus_u\Phi_F(N),
$$

then

$$
\Phi_F(M \oplus_F \operatorname{fsucc}_F(N))
=
\Phi_F(\operatorname{fsucc}_F(M \oplus_F N))
=
\operatorname{usucc}(\Phi_F(M \oplus_F N))
$$

which equals

$$
\operatorname{usucc}(\Phi_F(M)\oplus_u\Phi_F(N))
=
\Phi_F(M)\oplus_u\Phi_F(\operatorname{fsucc}_F(N)).
$$

Multiplication preservation follows by induction on the second argument.

Base case:

$$
\Phi_F(M \otimes_F \delta^{(F)}_1)
=
\Phi_F(M)
=
\Phi_F(M) \otimes_u \mu_1.
$$

Inductive step:

if
$$
\Phi_F(M \otimes_F N)=\Phi_F(M)\otimes_u\Phi_F(N),
$$

then

$$
\Phi_F(M \otimes_F \operatorname{fsucc}_F(N))
=
\Phi_F((M \otimes_F N) \oplus_F M)
$$

which equals

$$
\Phi_F(M \otimes_F N) \oplus_u \Phi_F(M)
=
(\Phi_F(M) \otimes_u \Phi_F(N)) \oplus_u \Phi_F(M)
$$

and therefore

$$
\Phi_F(M \otimes_F \operatorname{fsucc}_F(N))
=
\Phi_F(M) \otimes_u \Phi_F(\operatorname{fsucc}_F(N)).
$$

---


### 9.5 Canonical representation theorem

For every valid family $F$ and every core magnitude $\mu_n \in \mathbb{U}^{+}$, there exists exactly one family numeral $M \in \mathbb{M}^{+}_F$ such that:

$$
\Phi_F(M)=\mu_n.
$$

**Proof sketch.** This is immediate from the requirement that $\Phi_F$ be a bijection from $\mathbb{M}^{+}_F$ onto $\mathbb{U}^{+}$.

### 9.6 Decidability of validation and inter-family conversion

Given:

- a finite family declaration satisfying the schema requirements of Section 7
- a finite candidate numeral over that family alphabet

the following tasks are decidable:

1. family declaration validation
2. numeral well-formedness
3. canonical storage serialization
4. bridge evaluation by $\Phi_F$
5. inter-family conversion by $\Psi_{F\to G}$

**Proof sketch.** Every family declaration and numeral in the present calculus is finite data. Family order, successor, rendering, witness canonicalization, and degeneracy rules are required to be explicitly declared. The bridge map $\Phi_F$ is total and bijective by conformance. Therefore validation, serialization, and conversion reduce to finite symbolic procedures.

## 10. Core-coupled scalar embedding

The signed scalar line is not owned by any single numeral family.

Instead, every family numeral reaches the scalar line through the shared core magnitude domain.

Define positive-branch embedding:

$$
\rho(\mu_1)=2
$$

$$
\rho(\operatorname{usucc}(\mu_n)) = \operatorname{ssucc}(\rho(\mu_n)).
$$

Define negative-branch embedding:

$$
\lambda(\mu_1)=-2
$$

$$
\lambda(\operatorname{usucc}(\mu_n)) = \operatorname{spred}(\lambda(\mu_n)).
$$

So for any family numeral $M \in \mathbb{M}^{+}_F$:

- its positive scalar realization is
  $$
  \rho(\Phi_F(M))
  $$
- its negative scalar realization is
  $$
  \lambda(\Phi_F(M)).
  $$

This means scalar embedding is family-independent after semantic resolution.

---

## 11. Scalar arithmetic

The scalar layer remains shared.

### 11.1 Transport maps

Define the transport maps:

$$
E(1)=0
$$

$$
E(n)=n-1 \qquad \text{for } n\ge 2
$$

$$
E(n)=n+1 \qquad \text{for } n\le -2.
$$

Its inverse is:

$$
I(0)=1
$$

$$
I(k)=k+1 \qquad \text{for } k\ge 1
$$

$$
I(k)=k-1 \qquad \text{for } k\le -1.
$$

These maps are normative for scalar arithmetic. They make the scalar layer an explicitly transported arithmetic over the gapped label line.

### 11.2 Scalar addition and subtraction

Define scalar addition by transport:

$$
a \oplus_s b = I(E(a)+E(b)).
$$

Define scalar subtraction by transport:

$$
a \ominus_s b = I(E(a)-E(b)).
$$

Derived corollaries:

For every scalar $s$:

$$
s \oplus_s 1 = s = 1 \oplus_s s
$$

and

$$
s \ominus_s 1 = s.
$$

If $b = \rho(\mu_n)$, then:

$$
s \oplus_s b = T_{+}(s,\mu_n)
$$

and

$$
s \ominus_s b = T_{-}(s,\mu_n).
$$

If $b = \lambda(\mu_n)$, then:

$$
s \oplus_s b = T_{-}(s,\mu_n)
$$

and

$$
s \ominus_s b = T_{+}(s,\mu_n).
$$

So the branch-sensitive translation rules are corollaries of the transported definition rather than independent ad hoc laws.

### 11.3 Scalar multiplication

Define scalar multiplication by transport:

$$
a \otimes_s b = I(E(a)\cdot E(b)).
$$

Derived corollaries:

The scalar label `1` is the additive origin and multiplicative absorber:

$$
1 \otimes_s s = 1 = s \otimes_s 1.
$$

The scalar label `2` is the positive multiplicative unit:

$$
2 \otimes_s s = s = s \otimes_s 2.
$$

The scalar label `-2` is the negative multiplicative unit:

$$
(-2) \otimes_s \rho(\mu_n)=\lambda(\mu_n)
$$

$$
(-2) \otimes_s \lambda(\mu_n)=\rho(\mu_n).
$$

For non-origin scalars, multiplication therefore reduces to:

1. transport to the ordinary signed displacement line by $E$
2. multiply there
3. return by $I$

Examples:

$$
2 \otimes_s (-2) = -2
$$

$$
(-2) \otimes_s 2 = -2
$$

$$
(-2) \otimes_s (-2) = 2
$$

$$
3 \otimes_s (-2) = -3.
$$

---
## 12. Reference family classes

DPFC v4.6 does not freeze one mandatory family, but it does define reference family classes.

### 12.1 Base-6 reference family

A base-6 family is any declared family with:

$$
b_F = 6.
$$

This may be appropriate for hexagon-centered or sixfold-symmetry constructions.

### 12.2 Base-10 reference family

A base-10 family is any declared family with:

$$
b_F = 10.
$$

This may be appropriate for decagonal or ten-symbol human-facing profiles.

### 12.3 Base-12 reference family

A base-12 family is any declared family with:

$$
b_F = 12.
$$

This may be appropriate for dodecagonal or twelvefold-structured profiles.

### 12.4 Higher or alternate family modules

Nothing in DPFC v4.6 forbids base-3, base-8, base-20, mixed-radix, or other family-native profiles, so long as:

- the family schema is declared
- the family successor and order are coherent
- the family-to-core map $\Phi_F$ is total and bijective

---

## 13. Geometric family motivation

DPFC v4.6 is motivated by the observation that geometry naturally appears in **families**, not in one universal polygon alphabet.

A family may be generated by:

- direct polygon progression
- reflection configurations
- degeneration from larger uniform objects
- higher-dimensional boundary or net structure
- other declared geometric rules

Because of this, the numeral system should not be frozen prematurely at one base merely because one family is convenient.

The correct architectural move is:

- one duotronic core
- many family-native numeral modules
- explicit bridges between them

That is the defining design idea of DPFC v4.6.

### 13.1 Why choose one family over another?

A family choice may be driven by:

- symmetry fit to a target geometry
- compactness of representation
- human readability
- visual tiling affinity
- error-detection or redundancy properties
- native compatibility with a specific geometric or computational process

So a project may choose a hex6 family for hexagonal tilings, a decagon10 family for human-facing interfaces, and a dodec12 family for twelvefold symmetry work, while preserving shared semantic magnitude through the core.

---

## 14. Degeneracy and congruence

Different geometric constructions may lead to the same family numeral or to numerals in different families that represent the same core magnitude.

DPFC v4.6 therefore distinguishes:

1. **family identity**: the exact numeral object inside one family
2. **construction witness**: the geometric or reflection witness that produced that numeral
3. **core congruence**: equality after mapping into $\mathbb{U}^{+}$

### 14.1 Core congruence relation

For numerals $M \in \mathbb{M}^{+}_F$ and $N \in \mathbb{M}^{+}_G$, define:

$$
M \cong N
\quad \Longleftrightarrow \quad
\Phi_F(M)=\Phi_G(N).
$$

This is the main inter-family equivalence notion.

### 14.2 Generic witness degeneracy example

A family may permit two distinct construction witnesses that both canonicalize to the same family digit.

For example, in a reflection-derived family, two different seat-point realizations may generate the same canonical digit witness after symmetry reduction. In that case:

- the **family numeral** is one object
- the **witness metadata** preserves both construction histories
- the **core magnitude** remains unchanged

This is how DPFC handles degeneracy without collapsing geometry into mere decoration.

**Witness transparency rule.** If $w_1 \sim w_2$ under a family's degeneracy relation, then:

$$
\Phi_F(\operatorname{canon}(w_1))=\Phi_F(\operatorname{canon}(w_2)).
$$

So degeneracy is semantically transparent to the bridge.

---

## 15. A worked concrete family: hex6

To show that the bridge and conversions are operational rather than merely philosophical, DPFC v4.6 includes one fully worked reference family.

### 15.1 Family declaration

Let the family be:

$$
F_{\mathrm{hex6}} = (\mathrm{hex6}, 6, \Delta_{\mathrm{hex6}}, \prec_{\mathrm{hex6}}, \operatorname{fsucc}_{\mathrm{hex6}}, \Phi_{\mathrm{hex6}}, \mathrm{render}, \mathrm{witness}, \mathrm{degeneracy}, \mathrm{geometry})
$$

with digit alphabet:

$$
\Delta_{\mathrm{hex6}} = (h_1,h_2,h_3,h_4,h_5,h_6).
$$

Plain-text render tokens:

```text
h1, h2, h3, h4, h5, h6
```

### 15.2 Geometry and witness summary

- `geometry.kind = polygon_progression`
- `geometry.dimension_scope = [2]`
- `geometry.generator_data.side_counts = [3,4,5,6,7,8]`

Primitive digit witnesses are declared as simple canonical side-count witnesses:

| Digit | Witness |
|---|---|
| $h_1$ | triangle witness |
| $h_2$ | square witness |
| $h_3$ | pentagon witness |
| $h_4$ | hexagon witness |
| $h_5$ | heptagon witness |
| $h_6$ | octagon witness |

The canonicalization rule is identity on primitive witnesses. Degeneracy is disabled for hex6.

### 15.3 Successor examples

$$
\operatorname{fsucc}_{\mathrm{hex6}}(h_1)=h_2
$$

$$
\operatorname{fsucc}_{\mathrm{hex6}}(h_5)=h_6
$$

$$
\operatorname{fsucc}_{\mathrm{hex6}}(h_6)=h_1h_1
$$

$$
\operatorname{fsucc}_{\mathrm{hex6}}(h_1h_6)=h_2h_1
$$

### 15.4 First 12 magnitudes

| Core magnitude | hex6 numeral |
|---|---|
| $\mu_1$ | $h_1$ |
| $\mu_2$ | $h_2$ |
| $\mu_3$ | $h_3$ |
| $\mu_4$ | $h_4$ |
| $\mu_5$ | $h_5$ |
| $\mu_6$ | $h_6$ |
| $\mu_7$ | $h_1h_1$ |
| $\mu_8$ | $h_1h_2$ |
| $\mu_9$ | $h_1h_3$ |
| $\mu_{10}$ | $h_1h_4$ |
| $\mu_{11}$ | $h_1h_5$ |
| $\mu_{12}$ | $h_1h_6$ |

This defines $\Phi_{\mathrm{hex6}}$ on the first 12 values and extends recursively by the bridge law.

### 15.5 Family addition example

Compute:

$$
h_3 \oplus_{\mathrm{hex6}} h_5.
$$

Since $h_5 = \operatorname{fsucc}_{\mathrm{hex6}}(h_4)$, repeated successor gives:

$$
h_3 \to h_4 \to h_5 \to h_6 \to h_1h_1 \to h_1h_2.
$$

So:

$$
h_3 \oplus_{\mathrm{hex6}} h_5 = h_1h_2.
$$

Mapping to the core:

$$
\Phi_{\mathrm{hex6}}(h_3)=\mu_3
$$

$$
\Phi_{\mathrm{hex6}}(h_5)=\mu_5
$$

$$
\Phi_{\mathrm{hex6}}(h_1h_2)=\mu_8.
$$

This matches:

$$
\mu_3 \oplus_u \mu_5 = \mu_8.
$$

### 15.6 Family multiplication example

Compute:

$$
h_2 \otimes_{\mathrm{hex6}} h_3.
$$

This means repeated addition of $h_2$ three times:

$$
h_2 \oplus_{\mathrm{hex6}} h_2 = h_4
$$

$$
h_4 \oplus_{\mathrm{hex6}} h_2 = h_6.
$$

So:

$$
h_2 \otimes_{\mathrm{hex6}} h_3 = h_6.
$$

Mapping to the core:

$$
\Phi_{\mathrm{hex6}}(h_2)=\mu_2, \qquad \Phi_{\mathrm{hex6}}(h_3)=\mu_3, \qquad \Phi_{\mathrm{hex6}}(h_6)=\mu_6.
$$

This matches:

$$
\mu_2 \otimes_u \mu_3 = \mu_6.
$$

---

## 16. A worked reflection-derived family: refl3

To show that the family calculus is not merely "different bases with new names," DPFC v4.6 includes a minimal reflection-derived family with explicit witness and degeneracy behavior.

### 16.1 Family declaration

Let the family be:

$$
F_{\mathrm{refl3}} = (\mathrm{refl3}, 3, \Delta_{\mathrm{refl3}}, \prec_{\mathrm{refl3}}, \operatorname{fsucc}_{\mathrm{refl3}}, \Phi_{\mathrm{refl3}}, \mathrm{render}, \mathrm{witness}, \mathrm{degeneracy}, \mathrm{geometry})
$$

with digit alphabet:

$$
\Delta_{\mathrm{refl3}} = (r_1,r_2,r_3).
$$

Plain-text render tokens:

```text
r1, r2, r3
```

### 16.2 Geometry schema

- `geometry.kind = reflection_family`
- `geometry.dimension_scope = [2]`
- `geometry.generator_data.mirrors = 2`
- `geometry.generator_data.angle_degrees = 60`
- `geometry.generator_data.fundamental_sectors = 3`

**Clarification.** A raw two-mirror 60° reflection arrangement normally produces a six-sector dihedral picture. This family deliberately employs a **canonical positive-sector reduction** that collapses the standard six-sector dihedral picture into a 3-sector fundamental domain for the purposes of numeral representation. The exact reflection action is defined by the `generator_data` and canonicalization rule, not by the unreduced dihedral picture alone.

### 16.3 Witness schema

Each primitive digit is realized by a canonical sector witness:

| Digit | Canonical witness |
|---|---|
| $r_1$ | sector-1 |
| $r_2$ | sector-2 |
| $r_3$ | sector-3 |

A witness record consists of:

- `sector_id`
- `path_word`
- `orbit_id`

### 16.4 Degeneracy schema

Degeneracy is enabled for refl3.

Two witnesses are equivalent iff:

1. they lie in the same orbit under the declared reflection action
2. their canonicalized sector is the same

For example, the following two witnesses both canonicalize to $r_2$:

```text
w_a = { sector_id: 2, path_word: [s1, s2], orbit_id: "o7" }
w_b = { sector_id: 2, path_word: [s2, s1, s2], orbit_id: "o7" }
```

Canonicalization sends both to the same digit:

```text
canon(w_a) = family:refl3 schema_version:dpfc-family@v4.6 digits:2
canon(w_b) = family:refl3 schema_version:dpfc-family@v4.6 digits:2
```

Even though the path words differ, the degeneracy relation identifies them as witnesses of the same primitive digit $r_2$.

### 16.5 Successor and arithmetic

The numeral law remains bijective base-3:

$$
\operatorname{fsucc}_{\mathrm{refl3}}(r_1)=r_2, \qquad \operatorname{fsucc}_{\mathrm{refl3}}(r_2)=r_3, \qquad \operatorname{fsucc}_{\mathrm{refl3}}(r_3)=r_1r_1.
$$

This shows an important distinction:

- the **arithmetic law** is governed by the family modulus and bridge coherence
- the **geometric semantics** are governed by witness structure and degeneracy behavior

So geometry matters in DPFC even when the successor law remains bijective at the numeral level.

**Current limitation.** In refl3, geometry changes witness structure and canonicalization behavior, but it does not yet alter the successor law itself. A future family may allow geometry to affect successor more directly through a geometric walk rule rather than a plain next-digit law.

### 16.6 First six magnitudes

| Core magnitude | refl3 numeral |
|---|---|
| $\mu_1$ | $r_1$ |
| $\mu_2$ | $r_2$ |
| $\mu_3$ | $r_3$ |
| $\mu_4$ | $r_1r_1$ |
| $\mu_5$ | $r_1r_2$ |
| $\mu_6$ | $r_1r_3$ |

---

## 17. Inter-family example: hex6 to dec10

Let a decagon10 family $F_{\mathrm{dec10}}$ have digits:

$$
\Delta_{\mathrm{dec10}}=(d_1,d_2,\ldots,d_{10})
$$

with glyph display tokens:

```text
d1, d2, d3, d4, d5, d6, d7, d8, d9, d10
```

and the first ten core magnitudes mapped directly:

| Core magnitude | dec10 numeral |
|---|---|
| $\mu_1$ | $d_1$ |
| $\mu_2$ | $d_2$ |
| $\mu_3$ | $d_3$ |
| $\mu_4$ | $d_4$ |
| $\mu_5$ | $d_5$ |
| $\mu_6$ | $d_6$ |
| $\mu_7$ | $d_7$ |
| $\mu_8$ | $d_8$ |
| $\mu_9$ | $d_9$ |
| $\mu_{10}$ | $d_{10}$ |

Then:

$$
\Psi_{\mathrm{hex6}\to\mathrm{dec10}}(h_1h_2)=d_8
$$

because both denote $\mu_8$.

So the worked addition example converts as:

$$
h_3 \oplus_{\mathrm{hex6}} h_5 = h_1h_2
$$

and therefore, in dec10 rendering,

$$
\Psi_{\mathrm{hex6}\to\mathrm{dec10}}(h_3 \oplus_{\mathrm{hex6}} h_5)=d_8.
$$

---

## 18. Serialization

### 18.1 Canonical storage serialization

For storage, hashing, signing, and equality checks, DPFC v4.6 adopts **ordinal family serialization** as the canonical form.

Canonical machine shape:

```text
family:<family_id> schema_version:<schema_id> digits:<i1 i2 ... ik>
```

where each `ij` is the ordinal position of the family digit inside $\Delta_F$.

Example:

```text
family:hex6 schema_version:dpfc-family@v4.6 digits:1 4 6
```

This means the numeral consists of the first, fourth, and sixth digits of the hex6 family.

The canonical hash/signature input must include the schema version together with the family ID and ordinal digits.

When hashing or signing, implementations must hash the exact UTF-8 bytes of the canonical storage string.


### 18.2 Display serialization

A family may additionally define a glyph-token rendering for human use.

Example:

```text
family:hex6 glyphs:h1 h4 h6
```

Display serialization is **display-only**. It is not the canonical storage form.

### 18.3 Scalar serialization

The scalar domain serializes with native labels:

```text
..., -4, -3, -2, 1, 2, 3, 4, ...
```

---

## 19. Conformance requirements

An implementation conforms to DPFC v4.6 if and only if it satisfies all of the following.

### 19.1 Core conformance

It implements the shared core magnitude domain $\mathbb{U}^{+}$, the scalar domain $\Lambda$, scalar successor/predecessor, scalar translation, and the duotronic grid exactly as defined.

### 19.2 Family schema conformance

Every supported numeral family must declare:

- family name
- schema version
- modulus $b_F$
- ordered digit alphabet $\Delta_F$
- family successor
- family order
- family-to-core map $\Phi_F$
- rendering policy
- witness schema
- degeneracy schema
- geometry schema

### 19.3 Family arithmetic conformance

For every supported family $F$, its family addition and multiplication must match Sections 8.3 and 8.4.

### 19.4 Bridge conformance

For every supported family $F$, the bridge law must hold:

$$
\Phi_F(\operatorname{fsucc}_F(M)) = \operatorname{usucc}(\Phi_F(M)).
$$

### 19.5 Inter-family conversion conformance

If an implementation claims to convert between families, it must do so via $\Psi_{F\to G}$ exactly.

### 19.6 Scalar coupling conformance

If an implementation couples numerals to scalars, it must embed them through the shared core and not through ad hoc family-specific shortcuts.

### 19.7 Boundary note

DPFC deliberately leaves performance metrics, hash table budgets, caching strategies, and runtime resource policies to the implementation layer. The present document defines mathematical and serialization semantics, not execution budgets.

### 19.8 Schema versioning policy

The `schema_version` field exists to preserve canonical meaning across revision boundaries.

Versioning rules:

1. If a family changes in any way that can alter:
   - digit ordering
   - canonical serialization
   - witness canonicalization
   - degeneracy equivalence
   - the bridge map $\Phi_F$
   then the `schema_version` **must** change.
2. Canonical strings from an older schema version remain valid **as historical objects of that version**.
3. An implementation may provide migration maps between schema versions, but migration is external to canonical identity.
4. If a new schema version preserves the exact same bridge semantics and canonical serialization, it may declare itself backward-compatible, but it must still carry its explicit version label.

This policy prevents silent semantic drift.

---


### 19.9 Recommended validation artifacts

A reference implementation or conformance harness should ideally expose at least the following artifacts:

- parser and validator for family declarations
- canonical storage serializer
- bridge evaluator for $\Phi_F$
- inter-family converter for $\Psi_{F\to G}$
- property-based tests for bridge preservation
- round-trip serialization tests
- malformed family and malformed numeral rejection tests

These artifacts are recommended for reproducibility and interoperability, even though the present document does not mandate a particular programming language or runtime.

## 20. Future profiles

DPFC v4.6 is a **discrete, gapped, realized-state calculus**.

It does not yet define a continuous analysis profile. Future work may separate at least three lines of development:

### 20.1 DPFC-Discrete

The present profile family:

- gapped scalar lattice
- family-native bijective numerals
- finite successor arithmetic
- duotronic grid structure

### 20.2 DPFC-Continuous

A future profile may address:

- fractional magnitudes
- smooth structure over or around the gapped scalar line
- derivative and limit concepts
- continuous or quasi-continuous geometry
- field-like extensions

### 20.3 DPFC-Geometric-Successor

A future profile may allow geometry to alter the successor law directly, for example by:

- geometric walk rules
- vertex-circuit successor
- mirror-step successor
- topology-sensitive carry behavior

This track is explicitly named because current families such as refl3 use geometry to affect witnesses and degeneracy, but not yet the successor law itself.

---

## 21. Positioning relative to prior work

DPFC v4.6 should be understood as a family-parameterized representational framework over a shared positive arithmetic core.

It is therefore related in broad spirit to existing literatures on:

- zeroless positional notation
- abstract numeration systems on ordered languages
- automata-oriented arithmetic in nonstandard numeration systems
- signed-digit frameworks
- negative-base and alternate-base representations

DPFC does **not** claim to invent zeroless numeration, alternate radices, or ordered-string encodings in the abstract. Its distinctive contribution is architectural: it combines

- family-indexed bijective numeral systems
- optional geometry-linked witness semantics
- a shared positive core with explicit bridge laws
- a gapped scalar ontology
- canonical machine serialization with version control
- inter-family conversion and conformance rules

### 21.1 Relation to standard arithmetic

DPFC is not best read as a replacement for standard arithmetic. It is best read as a family-parameterized representational layer over a shared positive arithmetic core, with optional geometry-tracking semantics.

The scalar layer is deliberately transported through the explicit maps $E$ and $I$ introduced in Section 11. This means the paper does not hide the relation to ordinary signed arithmetic. Instead, it makes that relation explicit and treats it as part of the framework's coherence story.

### 21.2 Current limits of the geometry claim

In the present worked families, geometry affects:

- native digit choice
- witness structure
- canonicalization
- degeneracy rules
- representation profile

It does **not yet** force a genuinely geometry-dependent successor law in the examples supplied here. That stronger claim is reserved for the future DPFC-Geometric-Successor track.

### 21.3 Genre note

This document remains a **normative specification first**. A conventional mathematics or theory paper based on DPFC should use this document as a formal reference and separately supply:

- stronger novelty claims where justified
- additional theorem development
- reference implementations and property-based testing
- any empirical or benchmark evidence relevant to usability or performance

---
## 22. Philosophical statement

DPFC v4.6 is not just a new notation. It is an ontological and organizational decision about how to structure numeral families and realized magnitudes.

It refuses three reductions:

1. the reduction of all numeral families to one arbitrary base
2. the reduction of native symbols to bookkeeping-era conventions
3. the reduction of geometric variety to a single human-friendly alphabet

Its positive thesis is:

- realized magnitudes should have native symbols
- different geometric families may realize those magnitudes differently
- family diversity is not a defect but a structural feature
- one can still obtain coherence by mapping those families into a shared core

This philosophical stance does not, by itself, prove a new foundational arithmetic. What it does provide is a disciplined way to organize multi-family zeroless numeration, witness semantics, and cross-family conversion inside one coherent calculus.

---

## 23. Final statement

DPFC v4.6 is a duotronic mathematical and numeral ontology with:

- a shared core realized magnitude domain
- a shared signed gapped scalar line
- a duotronic grid
- multiple positive polygon-native or reflection-derived numeral families
- family-native bijective moduli
- explicit family-to-core congruence maps
- explicit inter-family conversion maps
- no mandatory native zero digit
- no requirement that one family or one base dominate all others

This is the intended foundation:

**a duotronic polygon family calculus in which many native positive numeral families coexist inside one realized-state mathematical ontology.**

---

## Appendix A: Compact axiom sheet

### Core magnitude domain

$$
\mathbb{U}^{+}=\{\mu_1,\mu_2,\mu_3,\ldots\}
$$

$$
\operatorname{usucc}(\mu_n)=\mu_{n+1}
$$

### Core arithmetic

$$
\mu_m \oplus_u \mu_1 = \operatorname{usucc}(\mu_m)
$$

$$
\mu_m \oplus_u \operatorname{usucc}(\mu_n)=\operatorname{usucc}(\mu_m \oplus_u \mu_n)
$$

$$
\mu_m \otimes_u \mu_1 = \mu_m
$$

$$
\mu_m \otimes_u \operatorname{usucc}(\mu_n)=(\mu_m \otimes_u \mu_n)\oplus_u \mu_m
$$

### Scalar domain

$$
\Lambda=\{\ldots,-4,-3,-2,1,2,3,4,\ldots\}
$$

$$
\operatorname{ssucc}(-2)=1, \qquad \operatorname{ssucc}(1)=2
$$

$$
\operatorname{spred}(2)=1, \qquad \operatorname{spred}(1)=-2
$$

### Scalar translation

$$
T_{+}(s,\mu_1)=\operatorname{ssucc}(s)
$$

$$
T_{+}(s,\operatorname{usucc}(\mu_n))=\operatorname{ssucc}(T_{+}(s,\mu_n))
$$

$$
T_{-}(s,\mu_1)=\operatorname{spred}(s)
$$

$$
T_{-}(s,\operatorname{usucc}(\mu_n))=\operatorname{spred}(T_{-}(s,\mu_n))
$$

### Family schema

$$
F=(\mathrm{name},b_F,\Delta_F,\prec_F,\operatorname{fsucc}_F,\Phi_F,\mathrm{render}_F,\mathrm{witness}_F,\mathrm{degeneracy}_F,\mathrm{geometry}_F)
$$

### Family domain

$$
\mathbb{M}^{+}_F = \{\text{finite nonempty chains over } \Delta_F\}
$$

### Family successor

$$
\operatorname{fsucc}_F(\delta^{(F)}_i)=\delta^{(F)}_{i+1}\quad (1\le i < b_F)
$$

$$
\operatorname{fsucc}_F(X\delta^{(F)}_{b_F}) = \operatorname{fsucc}_F(X)\delta^{(F)}_1
$$

$$
\operatorname{fsucc}_F(\delta^{(F)}_{b_F}) = \delta^{(F)}_1\delta^{(F)}_1
$$

### Family addition

$$
M \oplus_F \delta^{(F)}_1 = \operatorname{fsucc}_F(M)
$$

$$
M \oplus_F \operatorname{fsucc}_F(N)=\operatorname{fsucc}_F(M\oplus_F N)
$$

### Family multiplication

$$
M \otimes_F \delta^{(F)}_1=M
$$

$$
M \otimes_F \operatorname{fsucc}_F(N)=(M\otimes_F N)\oplus_F M
$$

### Bridge law

$$
\Phi_F(\delta^{(F)}_1)=\mu_1
$$

$$
\Phi_F(\operatorname{fsucc}_F(M))=\operatorname{usucc}(\Phi_F(M))
$$

### Inter-family conversion

$$
\Psi_{F\to G}=\Phi_G^{-1}\circ\Phi_F
$$

### Core congruence

$$
M\cong N \Longleftrightarrow \Phi_F(M)=\Phi_G(N)
$$

---

## Appendix B: Example family declarations (JSON-shaped)

### B.1 hex6 declaration

```json
{
  "schema_version": "dpfc-family@v4.6",
  "name": "hex6",
  "modulus": 6,
  "digits": ["h1", "h2", "h3", "h4", "h5", "h6"],
  "order": [1, 2, 3, 4, 5, 6],
  "geometry": {
    "kind": "polygon_progression",
    "dimension_scope": [2],
    "generator_data": {
      "side_counts": [3, 4, 5, 6, 7, 8]
    }
  },
  "witness": {
    "primitive_form": "side_count_polygon",
    "composition_rule": "digit_chain",
    "canonicalization": "identity"
  },
  "degeneracy": {
    "allowed": false
  },
  "render": {
    "canonical_storage": "ordinal",
    "display_tokens": ["h1", "h2", "h3", "h4", "h5", "h6"]
  }
}
```

### B.2 refl3 declaration

```json
{
  "schema_version": "dpfc-family@v4.6",
  "name": "refl3",
  "modulus": 3,
  "digits": ["r1", "r2", "r3"],
  "order": [1, 2, 3],
  "geometry": {
    "kind": "reflection_family",
    "dimension_scope": [2],
    "generator_data": {
      "mirrors": 2,
      "angle_degrees": 60,
      "fundamental_sectors": 3,
      "reduction_mode": "positive-sector-canonical-reduction"
    }
  },
  "witness": {
    "primitive_form": "sector_orbit_witness",
    "composition_rule": "digit_chain",
    "canonicalization": "reduce_to_sector_orbit_representative"
  },
  "degeneracy": {
    "allowed": true,
    "equivalence": "same_orbit_and_same_canonical_sector",
    "canonical_selection": "lexicographically_smallest_path_word",
    "preserve_all_witnesses": true
  },
  "render": {
    "canonical_storage": "ordinal",
    "display_tokens": ["r1", "r2", "r3"]
  }
}
```

---

## Appendix C: Canonical conformance vectors

These vectors are normative examples for serializer and bridge conformance.

### C.1 hex6 storage string

```text
family:hex6 schema_version:dpfc-family@v4.6 digits:1 2
```

This is the canonical storage form for $h_1h_2$.

### C.2 refl3 canonical witness result

Both of the following witnesses must canonicalize to the same storage string:

```text
w_a = { sector_id: 2, path_word: [s1, s2], orbit_id: "o7" }
w_b = { sector_id: 2, path_word: [s2, s1, s2], orbit_id: "o7" }
```

Canonical result:

```text
family:refl3 schema_version:dpfc-family@v4.6 digits:2
```

### C.3 cross-family conversion vector

The hex6 numeral

```text
family:hex6 schema_version:dpfc-family@v4.6 digits:1 2
```

denotes $\mu_8$ and converts into the dec10 numeral

```text
family:dec10 schema_version:dpfc-family@v4.6 digits:8
```

(assuming a compatible dec10 family declared under the same schema version).

### C.4 negative version test

The following two canonical strings must **not** compare equal as canonical storage objects:

```text
family:hex6 schema_version:dpfc-family@v4.5 digits:1 2
family:hex6 schema_version:dpfc-family@v4.6 digits:1 2
```

Even when the digit sequence is textually identical, differing schema versions make them distinct canonical objects unless an external migration layer explicitly bridges them.

### C.5 example SHA-256 digests

If an implementation chooses SHA-256 for canonical string hashing, then hashing the exact UTF-8 bytes of the following canonical storage strings yields:

| Canonical string | SHA-256 |
|---|---|
| `family:hex6 schema_version:dpfc-family@v4.6 digits:1 2` | `17733707bf33c1e47c5236589f70870b7bde6dc9d4fe9c4fa6aa65de2f91a646` |
| `family:refl3 schema_version:dpfc-family@v4.6 digits:2` | `b68e95571e9794cd3341e9d948379dd5ebc87ec46ed687b308d511b8fad50a17` |
| `family:dec10 schema_version:dpfc-family@v4.6 digits:8` | `e05d8257915236178a99075ee8a97e06ff00b8ebad98e07c198db230e64fbe20` |

## Appendix D: Reference pseudocode

This appendix is informative. It gives one straightforward implementation pattern for bridge evaluation and inter-family conversion.

### D.1 Evaluate a family numeral into the core index

```text
function phi_index(family F, digits [d1..dk]):
    # digits are ordinal positions 1..b_F
    n = 0
    for each ordinal digit r in digits:
        n = n * F.modulus + r
    return n
```

This returns the core index `n` such that the numeral denotes `$\mu_n$`.

### D.2 Encode a core index into a family numeral

```text
function encode_index(family F, n):
    # assumes n >= 1
    digits = []
    while n > 0:
        n = n - 1
        r = (n mod F.modulus) + 1
        prepend r to digits
        n = floor(n / F.modulus)
    return digits
```

This is the standard bijective-base encoding algorithm parameterized by the family modulus.

### D.3 Inter-family conversion

```text
function convert(F, G, digits_F):
    n = phi_index(F, digits_F)
    return encode_index(G, n)
```

### D.4 Canonical storage serialization

```text
function canonical_storage(F, digits):
    return "family:" + F.name +
           " schema_version:" + F.schema_version +
           " digits:" + join(digits, " ")
```

### D.5 Validator outline

```text
function validate_family(F):
    require F.schema_version exists
    require F.modulus >= 2
    require length(F.digits) == F.modulus
    require F.order is a permutation of [1..F.modulus]
    require geometry, witness, degeneracy, render all exist
    require bridge law is declared
    return valid
```
