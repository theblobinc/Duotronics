# Pronic-Centered Polygon Families as a Duotronic Visual Axiom Profile v1.0

**Status:** Research profile paper  
**Version:** research-pronic-centered-polygon-families@v1.0  
**Document kind:** Bounded geometry/witness-family research profile, not DPFC arithmetic core  
**Primary purpose:** Formalize the Duotronic visual axiom based on one center dot, even outer vertex counts, pronic shell boundaries, center-presence flags, deterministic polygon chain selection, and optional quaternion orientation reduction.

> Drafting note. This document follows the one-based Duotronic style for public headings, claim labels, and fixture labels. External geometry, host-language arrays, quaternion algebra, and ordinary exported arithmetic may still use ordinary zero where their own standards require it. The Duotronic rule is not that zero is forbidden; the rule is that absence, origin, invalidity, numeric zero, center presence, witness history, canonical identity, and geometric rendering must not be silently collapsed.

---

## Document status tag key

> **Status tag:** reference

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this research profile. | Conforming experimental implementations must follow it. |
| `reference` | Examples, algorithms, fixtures, schemas, or implementation aids. | Useful for implementation, but not a new DPFC core rule. |
| `research` | Experimental geometry family, benchmark, reducer, or witness profile. | Must remain opt-in until benchmarked and promoted. |
| `future` | Named work not completed in this document. | Must not be treated as live authority. |
| `analogy` | Outside-field comparison or motivation. | Must not be treated as proof or runtime authority. |

## 1. Research boundary

> **Status tag:** research

This profile formalizes a Duotronic geometry family generated from:

1. a single center dot representing least realized presence;
2. even outer vertex counts;
3. pronic shell boundaries;
4. a center-present/center-absent structural flag;
5. deterministic polygon chain selection;
6. optional quaternion or angle-sort orientation reduction.

The profile does not claim that:

1. quaternion algebra proves Duotronics;
2. polygon rendering proves DPFC arithmetic;
3. pronic shells prove chemistry, atoms, molecules, or physics;
4. the center dot is ordinary numeric zero;
5. geometric beauty is sufficient for canonical identity;
6. every generated polygon family is automatically useful.

The intended claim is narrower:

> Pronic-centered polygon generation is a coherent Duotronic geometry/witness family profile. It may provide canonical polygon witnesses, shell-indexed visual forms, geometry reducers, and molecule/atom-like research fixtures without mutating DPFC arithmetic.

## 2. Before concept and after concept

> **Status tag:** reference

The earlier observation was a quaternion/Platonic resonance:

```text
1 center / identity
2 axis pair
4 tetrahedral-looking structure
6 octahedral / hexagonal-looking structure
8 cubic-looking structure
10 decagonal / 4D extension hint
12 dodecagonal / icosahedral-looking structure
```

That observation is useful, but it can be overread. The corrected interpretation is:

| Stage | Interpretation | Corpus status |
|---|---|---|
| Before concept | Quaternions and small symmetry groups explain why some numbers such as 4, 6, 8, and 12 feel geometrically natural. | `analogy` |
| After concept | The visual axiom is a broader pronic-centered polygon generator using one center, even outer vertex counts, shell boundaries, and deterministic chain selection. | `research` / `reference` |

The after concept is stronger because it is not limited to quaternion-friendly polyhedra. It can describe arbitrary even outer vertex rings and inscribed polygons selected from those rings.

## 3. Quaternion layer

> **Status tag:** analogy

Quaternions are useful external geometry tools. A quaternion has the form:

\[
q=a+bi+cj+dk.
\]

A vector may be represented as a pure quaternion:

\[
v=xi+yj+zk.
\]

A unit quaternion rotation has the sandwich form:

\[
v' = qv\bar{q}.
\]

This profile may use quaternions for:

1. orientation normalization;
2. canonical pose selection;
3. interpolation between orientations;
4. molecule-like geometry alignment;
5. rotation-invariant witness comparison.

But quaternions are optional. A simpler 2D profile can canonicalize a polygon by sorting vertices by angle and choosing the lexicographically smallest rotation. The quaternion layer is a reducer or renderer tool, not the family generator and not DPFC arithmetic.

## 4. Pronic shell law

> **Status tag:** reference

The pronic numbers are:

\[
P_n=n(n+1).
\]

They are twice the triangular numbers:

\[
P_n=2T_n,
\qquad
T_n=\frac{n(n+1)}{2}.
\]

The pronic-centered polygon profile uses these as shell boundaries for even outer vertex counts.

Shell \(n\) contains the even vertex counts:

\[
2(T_{n-1}+1),\ 2(T_{n-1}+2),\ \ldots,\ 2T_n.
\]

The maximum outer vertex count in shell \(n\) is:

\[
2T_n=P_n=n(n+1).
\]

So shell \(n\) contains exactly \(n\) even vertex-count options.

| Shell | Even outer vertex counts | Boundary |
|---:|---|---:|
| L1 | 2 | 2 |
| L2 | 4, 6 | 6 |
| L3 | 8, 10, 12 | 12 |
| L4 | 14, 16, 18, 20 | 20 |
| L5 | 22, 24, 26, 28, 30 | 30 |

This gives a one-based, shell-based, presence-first geometry ladder.

## 5. Center-dot presence law

> **Status tag:** reference

Let \(v\) be the number of outer vertices. The outer vertex count is either absent or even:

\[
v\in\{0,2,4,6,8,\ldots\}.
\]

Let \(c\) be the center structural flag:

\[
c\in\{\texttt{center\_absent},\texttt{center\_present}\}.
\]

Define:

\[
\epsilon(\texttt{center\_absent})=0,
\]

\[
\epsilon(\texttt{center\_present})=1.
\]

The occupied site count under exported arithmetic is:

\[
A(v,c)=v+\epsilon(c).
\]

The minimum realized configuration is the single-dot configuration:

\[
(v=0,c=\texttt{center\_present}).
\]

This configuration maps to the least realized magnitude:

\[
\mu_1.
\]

It is not absence and not ordinary numeric zero.

## 6. Center policy

> **Status tag:** normative

The center flag is structural state. It is not a native digit, not absence, and not exported zero.

A profile may choose one of three center policies:

| Policy | Meaning | Canonicalization effect |
|---|---|---|
| `free_center_flag` | center present and center absent are distinct canonical forms when outer vertices exist | preserves both states |
| `parity_center_policy` | center is present or absent according to a declared parity rule | deterministic derived center state |
| `degenerate_center_merge` | center variants may be equivalent under a declared degeneracy relation | stores loss report or degeneracy class |

The recommended default is `free_center_flag`, because it preserves information and lets later profiles decide whether to merge states.

If a parity rule is used, it MUST be declared. For example:

```yaml
center_presence_policy:
  mode: parity_center_policy
  even_occupied_total_prefers: center_absent
  odd_occupied_total_prefers: center_present
```

A runtime MUST NOT silently infer center absence from numeric zero.

## 7. Canonical outer-ring index

> **Status tag:** reference

For \(v>0\), define the half-count:

\[
m=\frac{v}{2}.
\]

The shell index \(L(v)\) is the least \(n\) such that:

\[
v\leq P_n=n(n+1).
\]

Equivalently:

\[
L(v)=\left\lceil \frac{-1+\sqrt{1+4v}}{2}\right\rceil.
\]

Because \(v\) is even, this shell index exactly matches the pronic boundary table.

The within-shell ordinal is:

\[
O(v)=m-T_{L(v)-1}.
\]

So:

\[
1\leq O(v)\leq L(v).
\]

This gives a deterministic shell address:

\[
\operatorname{shelladdr}(v)=(L(v),O(v)).
\]

## 8. Shape chain selection

> **Status tag:** reference

Given an outer ring with \(v\) vertices, an \(s\)-sided polygon may be selected when:

\[
s\mid v.
\]

Let:

\[
d=\frac{v}{s}.
\]

For start offset \(a\), define the selected vertex chain:

\[
C_{s,a}(v)=\{a+(\ell-1)d \pmod v\mid 1\leq \ell\leq s\}.
\]

This selects \(s\) evenly spaced vertices from a \(v\)-vertex ring.

Examples:

| Outer count \(v\) | Side count \(s\) | Step \(d=v/s\) | Shape |
|---:|---:|---:|---|
| 6 | 3 | 2 | triangle |
| 8 | 4 | 2 | square |
| 10 | 5 | 2 | pentagon |
| 12 | 3 | 4 | triangle |
| 12 | 4 | 3 | square |
| 12 | 6 | 2 | hexagon |

This makes the "different chains produce different shapes" insight deterministic.

## 9. Star polygon extension

> **Status tag:** research

A star polygon profile may choose a stride \(r\) that is not the simple regular-polygon stride \(v/s\). A chain is valid when the selected cycle has the desired period.

A simple cycle condition is:

\[
\operatorname{period}(v,r)=\frac{v}{\gcd(v,r)}.
\]

A stride \(r\) produces an \(s\)-cycle when:

\[
\frac{v}{\gcd(v,r)}=s.
\]

This allows star and skip-chain witnesses while preserving deterministic canonicalization.

## 10. DPFC bridge

> **Status tag:** normative

A pronic-centered polygon object is not valid as a DPFC family object until it has a deterministic bridge into the positive core.

Let a canonical profile object be:

\[
X=(v,c,\sigma),
\]

where:

1. \(v\) is the outer vertex count;
2. \(c\) is the center flag;
3. \(\sigma\) is optional shape metadata such as side count, stride, offset, or reducer identity.

The minimum object is:

\[
X_1=(0,\texttt{center\_present},\varnothing).
\]

A simple reference index for the center/ring part is:

\[
\operatorname{idx}_{ring}(0,\texttt{center\_present})=1.
\]

For \(v=2m\) with \(m\geq 1\):

\[
\operatorname{idx}_{ring}(v,\texttt{center\_absent})=2m,
\]

\[
\operatorname{idx}_{ring}(v,\texttt{center\_present})=2m+1.
\]

So:

| Object | Index | Core image |
|---|---:|---|
| center only | 1 | \(\mu_1\) |
| 2 outer, center absent | 2 | \(\mu_2\) |
| 2 outer, center present | 3 | \(\mu_3\) |
| 4 outer, center absent | 4 | \(\mu_4\) |
| 4 outer, center present | 5 | \(\mu_5\) |

This is only the reference ring bridge. If shape metadata \(\sigma\) is part of canonical identity, the profile must declare a pairing or enumeration function that remains deterministic, injective over canonical objects, and replay-stable.

## 11. Shape metadata and identity

> **Status tag:** normative

A profile MUST declare whether shape metadata is canonical identity or witness metadata.

| Mode | Meaning |
|---|---|
| `ring_identity_only` | \((v,c)\) defines canonical identity; shapes are witness/render metadata. |
| `shape_identity` | \((v,c,s,a,r)\) or equivalent shape fields define canonical identity. |
| `degenerate_shape_class` | multiple shape selections map to one canonical identity with a declared degeneracy class. |

The default research mode is `ring_identity_only`, because it keeps the DPFC bridge simple while still allowing rich polygon witnesses.

A profile that uses `shape_identity` must provide:

1. finite field domains at each ring;
2. deterministic ordering of shape choices;
3. canonical rotation/reflection reduction;
4. replay-stable serializer;
5. conformance fixtures for equivalent shapes.

## 12. Canonicalization

> **Status tag:** reference

A 2D polygon witness may be canonicalized by:

1. validating the ring count \(v\);
2. validating the center flag;
3. validating side count or stride;
4. selecting the vertex chain;
5. sorting vertices cyclically;
6. rotating the cyclic list to lexicographically smallest order;
7. applying reflection policy;
8. recording shell address;
9. serializing the canonical object.

Reference canonical storage:

```text
family:pronic_centered_polygon schema_version:pcp@v1 outer_vertices:<v> center:<present|absent> shell:<L> shell_ordinal:<O> shape_mode:<mode>
```

## 13. Quaternion reducer option

> **Status tag:** analogy

A 3D or molecule-like rendering may use quaternions as an orientation reducer.

Reference reducer path:

```text
polygon witness -> embed in 2D/3D -> choose canonical frame -> compute orientation quaternion -> normalize pose -> serialize orientation-independent witness
```

The quaternion reducer may store:

```yaml
orientation_reducer:
  kind: quaternion_pose_reducer
  unit_quaternion: [w, x, y, z]
  rotation_formula: v_prime = q v q_conjugate
  sign_policy: choose_short_path_or_lexicographic_positive
```

The reducer is optional. A profile may instead use angle sorting or graph canonicalization. Quaternion math is not the pronic generator.

## 14. Molecular and atomic research boundary

> **Status tag:** normative

This profile may be used to build molecule-like or atom-like polygon witnesses. It may represent:

1. center dot as nucleus-like center;
2. outer vertices as shell positions;
3. selected chains as bond-like or orbital-like geometry;
4. rotations as pose normalization;
5. symmetry classes as degeneracy classes.

It MUST NOT claim chemical or physical correctness without external domain validation.

The correct claim is:

> Pronic-centered polygon families provide a deterministic geometry/witness language for molecule-like and atom-like research fixtures.

not:

> Pronic-centered polygon families prove atomic or molecular physics.

## 15. Family declaration sketch

> **Status tag:** reference

```yaml
family_id: pronic_centered_polygon
status: research
kind: polygon_progression
schema_version: pcp@v1
native_center_label: c1
center_label_meaning: least_present_center_not_zero
outer_vertex_counts: even_nonnegative
shell_boundary_rule: P_n = n(n + 1)
minimum_realized_configuration:
  outer_vertices: 0
  center: present
  core_image: mu_1
center_presence_policy:
  mode: free_center_flag
shape_selection:
  regular_polygon_rule: s divides v
  chain_rule: C_{s,a}(v) = {a + (ell - 1)(v/s) mod v | 1 <= ell <= s}
  star_polygon_extension: optional_stride_profile
identity_mode: ring_identity_only
canonicalization:
  rotation_policy: lexicographically_smallest_cyclic_order
  reflection_policy: declared_per_family
  quaternion_reducer: optional
non_claims:
  - not_dpfc_arithmetic_proof
  - not_physics_proof
  - not_required_for_all_polygon_families
```

## 16. Witness schema

> **Status tag:** reference

```yaml
PronicCenteredPolygonWitness:
  family_id: pronic_centered_polygon
  schema_version: pcp@v1
  outer_vertices: integer
  center: present | absent
  shell_index: integer
  shell_ordinal: integer
  occupied_site_count: integer
  shape:
    mode: none | regular_polygon | star_polygon
    side_count: integer | null
    stride: integer | null
    start_offset: integer | null
    vertex_chain: list[integer] | null
  canonicalization:
    cyclic_order_policy: lexicographic_min
    reflection_policy: preserve | quotient | reject
    orientation_reducer: none | quaternion | angle_sort
  bridge:
    identity_mode: ring_identity_only | shape_identity | degenerate_shape_class
    core_index: integer
    core_image: string
  non_claims:
    chemistry_validated: false
    physics_validated: false
```

## 17. Fixtures

> **Status tag:** reference

```yaml
fixture_pack: pronic-centered-polygon-v1-fixtures
fixtures:
  - fixture_id: PCP-FIXTURE-1-SINGLE-DOT-MINIMUM
    given:
      outer_vertices: 0
      center: present
    operation: bridge_to_core
    expected:
      occupied_site_count: 1
      core_index: 1
      core_image: mu_1
      absence: false

  - fixture_id: PCP-FIXTURE-2-SHELL-THREE-CONTAINS-8-10-12
    given:
      shell_index: 3
    operation: enumerate_shell
    expected:
      even_outer_vertex_counts: [8, 10, 12]
      pronic_boundary: 12
      shell_size: 3

  - fixture_id: PCP-FIXTURE-3-TRIANGLE-FROM-SIX-RING
    given:
      outer_vertices: 6
      side_count: 3
      start_offset: 1
    operation: select_regular_polygon_chain
    expected:
      step: 2
      vertex_chain: [1, 3, 5]
      shape: triangle

  - fixture_id: PCP-FIXTURE-4-SQUARE-FROM-EIGHT-RING
    given:
      outer_vertices: 8
      side_count: 4
      start_offset: 1
    operation: select_regular_polygon_chain
    expected:
      step: 2
      vertex_chain: [1, 3, 5, 7]
      shape: square

  - fixture_id: PCP-FIXTURE-5-CENTER-FLAG-IS-STRUCTURAL
    given:
      outer_vertices: 4
      center: absent
    operation: classify_center
    expected:
      center_is_numeric_zero: false
      center_is_absence: false
      center_is_structural_flag: true

  - fixture_id: PCP-FIXTURE-6-QUATERNION-REDUCER-OPTIONAL
    given:
      reducer: quaternion_pose_reducer
      rotation_formula: v_prime = q v q_conjugate
    operation: validate_reducer_role
    expected:
      reducer_is_generator: false
      reducer_is_optional_orientation_tool: true
      dpfc_arithmetic_changed: false
```

## 18. Minimal reference implementation

> **Status tag:** reference

```python
from dataclasses import dataclass
from math import ceil, gcd, sqrt


@dataclass(frozen=True)
class PCPObject:
    outer_vertices: int
    center_present: bool


def pronic(n: int) -> int:
    if n < 1:
        raise ValueError("shell labels are one-based")
    return n * (n + 1)


def triangular(n: int) -> int:
    if n < 0:
        raise ValueError("triangular helper received negative input")
    return n * (n + 1) // 2


def shell_index(v: int) -> int:
    if v <= 0 or v % 2 != 0:
        raise ValueError("outer vertex count must be positive and even")
    return ceil((-1 + sqrt(1 + 4 * v)) / 2)


def shell_ordinal(v: int) -> int:
    L = shell_index(v)
    return v // 2 - triangular(L - 1)


def occupied_site_count(obj: PCPObject) -> int:
    return obj.outer_vertices + (1 if obj.center_present else 0)


def ring_core_index(obj: PCPObject) -> int:
    v = obj.outer_vertices
    if v == 0:
        if obj.center_present:
            return 1
        raise ValueError("empty object is absence, not a realized PCP object")
    if v < 0 or v % 2 != 0:
        raise ValueError("outer vertex count must be even")
    m = v // 2
    return 2 * m + (1 if obj.center_present else 0)


def select_regular_polygon_chain(v: int, sides: int, start_offset: int = 1):
    if v <= 0 or sides <= 0:
        raise ValueError("vertex and side counts must be positive")
    if v % sides != 0:
        raise ValueError("side count must divide outer vertex count")
    step = v // sides
    return [((start_offset - 1 + (ell - 1) * step) % v) + 1 for ell in range(1, sides + 1)]


def star_period(v: int, stride: int) -> int:
    if v <= 0 or stride <= 0:
        raise ValueError("v and stride must be positive")
    return v // gcd(v, stride)


if __name__ == "__main__":
    assert pronic(3) == 12
    assert [2 * k for k in range(triangular(2) + 1, triangular(3) + 1)] == [8, 10, 12]
    assert ring_core_index(PCPObject(0, True)) == 1
    assert ring_core_index(PCPObject(2, False)) == 2
    assert ring_core_index(PCPObject(2, True)) == 3
    assert select_regular_polygon_chain(6, 3, 1) == [1, 3, 5]
    assert select_regular_polygon_chain(8, 4, 1) == [1, 3, 5, 7]
    assert shell_index(12) == 3
    assert shell_ordinal(12) == 3
```

## 19. Promotion path

> **Status tag:** future

This profile may be promoted from research to reference after:

1. fixture pack passes;
2. bridge and canonicalizer are implemented;
3. center presence remains distinct from numeric zero and absence;
4. ring identity and shape identity modes are tested;
5. quaternion reducer is optional and correctly bounded;
6. molecule/atom-like claims remain research-only unless externally validated;
7. replay-stable canonical storage is demonstrated.

## 20. Final boundary statement

> **Status tag:** normative

The pronic-centered visual axiom is a Duotronic geometry-family generator. It may generate center-aware polygon witnesses, shell-indexed visual forms, and canonical geometry fixtures. It does not prove DPFC arithmetic, chemistry, quantum physics, or quaternion theory. Quaternions may rotate or normalize geometry; pronic shells generate the family; DPFC bridges and serializes; the Witness Contract decides trust.

---

## v1.4 compatibility note

This profile is carried forward as bounded research material. It may inform witness extraction, fixtures, diagnostics, or profile candidates, but it does not gain runtime authority under v1.4 unless staged through the Profile Synthesis Registry, replayed, tested, and approved by the Policy Shield.

