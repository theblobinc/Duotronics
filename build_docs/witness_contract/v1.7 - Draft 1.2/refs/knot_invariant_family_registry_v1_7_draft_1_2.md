# Knot Invariant Family Registry - v1.7 Draft 1.2

## Supported invariant families

- `crossing_count` - diagram crossing count unless explicitly promoted with minimal-crossing proof.
- `component_count` - link component count.
- `determinant` - determinant invariant with declared normalization.
- `alexander_polynomial` - Alexander polynomial with declared variable and unit normalization.
- `jones_polynomial` - Jones polynomial with declared variable and mirror/orientation convention.
- `signature` - knot or link signature with declared convention.
- `linking_number` - linking number for oriented links.
- `fundamental_group_presentation` / `wirtinger_presentation` - group presentation witness, not equality proof by itself.
- `quandle_coloring` - coloring-count or quandle invariant with declared finite quandle.
- `custom` - requires registry extension, payload schema, replay policy, and authority status.

## Semantic classes

- `invariant_computation` - computes an invariant value only.
- `invariant_comparison` - compares invariant values only.
- `complete_invariant_for_bounded_domain` - declares completeness over a bounded domain and requires proof authority.
- `proof_backed_equivalence` - contributes directly to equivalence only when a proof witness and first-class authority path bind it.

Invariant equality is never knot equivalence unless completeness, domain, and proof authority are all explicit.
