# Corpus review — v1.5 Draft 2 consistency pass

**Status:** Internal review note
**Version:** corpus-review@v1.5-draft-2-consistency-pass
**Document kind:** Change log for an editorial / consistency pass over the v1.5 Draft 2 corpus and the repository-level documents.
**Primary purpose:** Record what changed during the consistency pass that aligned the v1.5 Draft 2 corpus and the repository-level documents with the broader Duotronic witness-runtime and distributed-systems program scope.

---

## 1. Scope of this pass

This pass did not introduce new theory, did not redefine DPFC, did not redefine the Witness Contract, and did not change runtime semantics anywhere.

It addressed:

1. program-level framing (no top-level statement of program scope existed);
2. canonical-implementation-target ambiguity (corpus implied a target without naming one);
3. v1.4-vs-v1.5 drift inside documents that were carried forward into the v1.5 Draft 2 folder;
4. carry-forward phrasing inside the Witness Contract;
5. repository-level `README.md` and `ROADMAP.md` which still framed Duotronics as a polygon workbook with a binary→quantum→hardware spine.
6. a follow-up framing cleanup that removed the last places where carried-forward reference documents still described v1.4 as if it were the active corpus release.

## 2. New documents

| Document | Path | Role |
|---|---|---|
| Program charter v1.0 | `duotronic_program_charter_v1_0.md` | Top-level program scope, separation rule, relationship to legacy chapter material |
| Canonical implementation target v0.1 | `duotronic_canonical_implementation_target_v0_1.md` | Open-decision status note (target is TBD) |
| Reading guide | `v1_5_draft_2_reading_guide.md` | Corpus map and reading order by role |
| This note | `corpus_review_v1_5_draft_2_consistency_pass.md` | Change log for the pass |

## 3. Existing documents edited

### 3.1 `refs/duotronic_source_architecture_overview_v1_7.md`

- Header `Primary purpose` updated from "v1.4 Duotronic source-spec stack" to "v1.5 Duotronic source-spec stack" and extended to mention the distributed cluster layer and WG-RNN.
- Added an inline versioning note explaining why the file kept its `v1.7-source-overview` identifier when carried forward into v1.5 Draft 2 (architecture map and ownership boundaries remained valid).
- Section 1 heading changed from "What Duotronics is in v1.4" to "What Duotronics is" and a paragraph added to point to the distributed cluster addendum and WG-RNN contract for the v1.5 layers.
- Section 6 phrasing changed from "A minimal v1.4 implementation should include" to "A minimal Duotronic implementation (v1.4 single-node baseline) should include," preserving its single-node baseline scope while acknowledging the v1.5 layers above it.

### 3.2 `duotronic_witness_contract_v10_16.md`

- Replaced the carry-forward sentence "v10.12 extends the contract to support automatic profile learning…" with a non-stale phrasing: "Beginning with v10.12 and carried forward through v10.16, the contract supports automatic profile learning…"

### 3.3 `v1_5_draft_2_next_steps.md`

- Replaced the implementation-direction line "Copy the skeleton to your implementation repo" with a deferred reference to `duotronic_canonical_implementation_target_v0_1.md` and explicitly framed the WG-RNN PyTorch skeleton as a research prototype until a target is recorded.

### 3.4 `README_v1_5_draft_2.md`

- Added a `## 0. Program-level entry points` section pointing to the program charter, reading guide, canonical-target note, source architecture overview, and glossary, before the existing Draft 2 release notes.

### 3.5 `refs/duotronic_lab_integrated_source_corpus_index_v1_13.md`

- Header `Primary purpose` updated from "List the v1.4 Draft corpus" to "List the active v1.5 Draft 2 corpus (v1.4 Draft 5 baseline plus the v1.5 distributed cluster layer and the v1.5 Draft 2 WG-RNN research profile)."
- Cross-reference block added pointing to program charter, reading guide, and canonical-target note.
- Core-documents list extended to include program charter, reading guide, and canonical-target note.
- Follow-up framing cleanup renamed `New v1.4 source specs` to `Carried-forward profile-learning source specs`, renamed `v1.4 scope statement` to `Carried-forward profile-learning scope statement`, and clarified that bounded research profiles promote through the carried-forward registry/policy path used by the active corpus.

### 3.5a `refs/duotronic_glossary_v1_0.md`

- Follow-up framing cleanup changed `This glossary defines terms used across the v1.4 Draft 2 corpus` to language that identifies the glossary as the terminology layer for the active v1.5 Draft 2 corpus and its carried-forward baseline documents.
- Follow-up framing cleanup changed `The canonical v1.4 Draft 2 status ladder is` to language that identifies the status ladder as the carried-forward ladder used by the v1.5 Draft 2 corpus.

### 3.5b `duotronic_witness_contract_v10_16.md`

- Follow-up framing cleanup changed `two v1.4 learning overlays` to `two carried-forward profile-learning overlays` in the runtime-layer description.

### 3.5c carried-forward reference specs

- Follow-up framing cleanup renamed `v1.4 new registered classes` in `refs/duotronic_schema_registry_v1_10.md` to `Carried-forward profile-learning registered classes`.
- Follow-up framing cleanup renamed `v1.4 lab classes` in `refs/duotronic_lab_evidence_registry_v1_7.md` to `Carried-forward lab classes`.
- Follow-up framing cleanup renamed `v1.4 metric classes` in `refs/duotronic_retention_diagnostics_v1_4.md` to `Carried-forward metric classes`.

### 3.6 Repository-level `README.md`

- Replaced workbook-style framing with a witness-runtime + distributed-systems program description.
- Documented the seven concerns of the program (witness calculus, DPFC, distributed cluster, auto-profile learning, WG-RNN, governance, polygon research workbook).
- Pointed active readers to the v1.5 Draft 2 entry points.
- Reclassified the chapter HTML/ODT exports as research input only.
- Added a status section noting that the canonical implementation target is undecided and that prototypes run as research prototypes until that decision is recorded.

### 3.7 Repository-level `ROADMAP.md`

- Replaced the binary-engine → quantum → cross-backend → hardware sequence with corpus-aligned phases A–F and a long-horizon research track L.
- Phase A: specification finalization (active corpus).
- Phase B: conformance harness.
- Phase C: WG-RNN research prototype.
- Phase D: distributed cluster prototype.
- Phase E: canonical-implementation-target decision.
- Phase F: production-grade runtime.
- Track L: polygon workbook, quantum-compatible representation, cross-backend portability, hardware acceleration.

## 4. Documents intentionally not changed

The following were reviewed and left unchanged because they are internally consistent with the v1.5 Draft 2 framing:

- `duotronic_polygon_family_calculus_v5_15.md` (DPFC) — version-stable, its scope is representation-only.
- `duotronic_v1_5_distributed_self_governing_recurrent_network_addendum.md` — already self-describes as v1.5 distributed addendum.
- `refs/duotronic_witness_gated_recurrent_cell_contract_v1_0.md` — owns its scope cleanly.
- `refs/duotronic_glossary_v1_0.md` — terminology entries are stable.
- All `refs/` documents not listed in section 3 above.

## 5. Authority and follow-up

This note is editorial and does not redefine any owning document.

The follow-up framing cleanup recorded above was also editorial only. It did not change runtime semantics, normative behavior, object schemas, or promotion rules.

Follow-up items that were noticed but not actioned in this pass:

1. Source architecture overview should eventually be renumbered (`v1.7` → `v1.8` or higher) when the next material rewrite happens; for now the inline versioning note is sufficient.
2. Corpus index v1.13 should be incremented when the next batch of edits lands.
3. When the canonical implementation target is decided, append `## 8. Decision record` to `duotronic_canonical_implementation_target_v0_1.md` and add a corresponding follow-up review note.
4. The `harness/` directory at the repository top level and the `harness/` references inside the v1.5 Draft 2 corpus should be reconciled when the conformance harness moves to its final home.
5. Surviving chapter content, if any is needed by the runtime corpus, should be republished as bounded research profiles under `refs/research_profiles/` rather than being read directly from the chapter HTML/ODT exports.
