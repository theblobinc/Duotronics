# Duotronic Program Charter v1.0

**Status:** Internal program-level charter
**Version:** program-charter@v1.0
**Document kind:** Top-level scope, framing, and authority statement for the Duotronic program
**Primary purpose:** Establish, in one place, what Duotronics is *as a program* (not just as a polygon workbook), what the v1.5 Draft 2 corpus is for, and how the legacy chapter material relates to the active witness-runtime and distributed-systems specification.

---

## 1. What Duotronics is

Duotronics is a **witness-runtime and distributed-systems program**.

The full program scope is:

1. a presence-first witness calculus that distinguishes absence, zero, unknown, invalid, origin, and canonical identity without collapsing them;
2. a runtime trust contract (the **Witness Contract**) covering evidence, witnesses, canonicalization, replay, lookup memory, recurrent state, retention, and policy gating;
3. a representational core (**DPFC**) that keeps family-native magnitude, conversion, and bridge boundaries disciplined;
4. an auto-profile learning pipeline that allows new representations to be proposed, validated, staged, and policy-gated rather than silently adopted;
5. a **distributed self-governing recurrent network** (v1.5) in which nodes auto-federate over DBP v2 S2 full-duplex transport, publish resources as canonical witnesses, and accept policy-gated task delegation;
6. a **witness-gated recurrent cell** (WG-RNN, v1.5 Draft 2) for governed persistent memory updates;
7. a research workbook track (the polygon-atomic-model chapters) which acts as a bounded research input, not as the program's runtime authority.

Duotronics is therefore not "a workbook" and not "one runtime class." It is a layered specification stack with research, normative, and reference documents, and it is intended to drive a real implementation.

## 2. Program separation rule

> **Status tag:** normative

The program separates four concerns and does not allow them to silently exchange authority:

1. **Representation** — DPFC, families, normalizers, bridges.
2. **Trust** — Witness Contract, evidence, canonicalization, replay, policy.
3. **Distribution** — Node federation, DBP cluster lanes, task delegation, resource witnesses.
4. **Memory and adaptation** — Lookup memory, recurrent witness state, WG-RNN slots, profile synthesis.

Each concern has owning documents inside this corpus. No track may rewrite another track's authority by side channel.

## 3. Active corpus

The active source corpus is `build_docs/witness_contract/v1.5 - Draft 2/` and the documents it references.

The reading entry points, in order, are:

1. `README_v1_5_draft_2.md` — corpus overview and integration summary.
2. `duotronic_program_charter_v1_0.md` — this document.
3. `v1_5_draft_2_reading_guide.md` — corpus map and reading order by role.
4. `refs/duotronic_source_architecture_overview_v1_7.md` — architecture map.
5. `duotronic_polygon_family_calculus_v5_15.md` — DPFC core.
6. `duotronic_witness_contract_v10_16.md` — runtime trust contract.
7. `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md` — distributed cluster layer.
8. `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md` — WG-RNN.
9. `refs/duotronic_glossary_v1_0.md` — terminology authority.
10. `duotronic_canonical_implementation_target_v0_1.md` — canonical implementation target status (currently TBD).

## 4. Relationship to the legacy chapter material

The HTML chapter exports at the repository root (`Duotronics - Chapter 1-17.html`, `Chapter 18.html`, `Chapter 19.html`, `Chapter 20-21.html`, `Chapter 22.html`, `Chapter 23.html`) and the `Duotronics - ai prep instructions.html` document are **research workbook material**.

They retain value as:

- early formal definitions of polygon objects, lattice states, and operator templates;
- catalog generation, expansion, and operator/witness recipes;
- prior reasoning about variant management and validation gates.

They do **not** define the active runtime or trust semantics for the program. Where chapter material conflicts with the v1.5 Draft 2 corpus, the corpus controls.

The chapter material is treated as:

| Chapter material | Status in v1.5 corpus |
|---|---|
| Chapter 1–17 foundation | research input; informs polygon family research profile |
| Chapter 18 catalog pipeline | research input; informs catalog/fixture lineage in `duotronic_lab_evidence_registry` |
| Chapter 19 expansion protocol | research input; partially superseded by Schema Registry, Migration Guide, and Profile Synthesis Registry |
| Chapter 20–21 operator/witness workbook | research input; superseded by the Witness Contract, Normalizer Profiles, and Retention Diagnostics |
| Chapter 22, Chapter 23 | research input; subject matter folded into bounded research profiles |

A future revision may republish surviving chapter content as one or more bounded research profiles under `refs/research_profiles/`.

## 5. Authority of this charter

This charter does not redefine DPFC, the Witness Contract, the distributed addendum, or the WG-RNN contract. It records which documents own which concerns, declares the active corpus, and frames the legacy material.

If this charter conflicts with an owning document on a subsystem question, the owning document controls.

If this charter conflicts with the repository-level `README.md` or `ROADMAP.md` on program scope, this charter controls. The repository-level documents are expected to be re-baselined to match.

## 6. Implementation-target status

The program is **specification-led**. As of v1.5 Draft 2, the canonical implementation target (language, repository location, runtime, deployment substrate) is not yet decided.

See `duotronic_canonical_implementation_target_v0_1.md` for:

1. the current candidate implementation surfaces;
2. the criteria that will be used to decide;
3. the deferred decisions that block production-grade promotion.

Until that decision is recorded, all references in the corpus to "your implementation repo," "the canonical implementation," or similar phrasing should be read as deferred to the canonical-target document.

## 7. Stability and change management

Changes that affect program scope (this charter), runtime trust semantics (Witness Contract), or representation core (DPFC) require:

1. a corpus review note in `build_docs/witness_contract/v1.5 - Draft 2/`;
2. updated supersedes lines in the affected owning document;
3. updated entries in the corpus index and reading guide;
4. preserved ownership boundaries in section 4 of the source architecture overview.

Changes inside a single owning document that do not alter its public interface do not require a charter update.
