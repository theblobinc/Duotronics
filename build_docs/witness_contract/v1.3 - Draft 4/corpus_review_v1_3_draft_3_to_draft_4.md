# Corpus Review: v1.3 Draft 3 to Draft 4

## Structure review

Draft 3 is structurally sound. It has two root-level core documents and a `refs/` folder for companion documents and research profiles. Draft 4 keeps that shape.

## What the new material adds

The new material formalizes the pronic-centered visual axiom. The key insight is the distinction between:

1. quaternions as an external rotation/orientation tool;
2. pronic-centered polygon families as the Duotronic geometry generator.

That distinction prevents the reader from thinking Duotronics is "just quaternion math." It also gives the visual axiom a proper DPFC-compatible home.

## Where the material belongs

The pronic-centered profile belongs in:

1. DPFC, as a short boundary note because it defines a geometry family that must bridge into the positive core;
2. Witness Contract, as a geometry-witness section because generated polygons must still be validated, canonicalized, replay-pinned, and policy-gated;
3. Source Architecture Overview, as a corpus map entry;
4. Corpus Index;
5. a standalone research profile.

It does not belong in every companion source spec.

## Main mathematical additions

Draft 4 adds:

1. pronic shell law: `P_n = n(n + 1)`;
2. shell membership for even outer vertex counts;
3. center-dot presence law;
4. ring bridge to DPFC core;
5. divisor-based polygon chain selection;
6. optional star-polygon stride extension;
7. optional quaternion orientation reducer;
8. fixtures and a minimal reference implementation.

## Boundary statement

Pronic shells generate center-aware polygon witnesses. Quaternions can rotate or normalize them. DPFC bridges and serializes them. The Witness Contract decides whether they are trusted.
