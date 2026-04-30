# Mathematical Claim Status Ladder v1.0

**Status:** reference draft  
**Version:** math-claim-status-ladder@v1.0

---

## 1. Status values

| Status | Meaning | Promotion requirement |
|---|---|---|
| raw_statement | unparsed mathematical text | parser witness |
| parsed_statement | syntax parsed, context not fully bound | context binding |
| well_typed_statement | expression valid in ambient context | object and assumption records |
| definition | declarative meaning assignment | domain profile approval |
| example | instance satisfying declared property | validation witness |
| counterexample_candidate | possible refutation | verification witness |
| verified_counterexample | refutation accepted under assumptions | proof or computation witness |
| computational_evidence | reproducible computation supports claim | replay and error bounds |
| literature_supported | cited source supports claim | literature witness |
| proof_sketch | informal proof outline | gap annotation |
| peer_reviewed_proof | proof accepted in standard literature | citation and review witness |
| formalized_proof | proof assistant artifact exists | checker result |
| kernel_checked_theorem | trusted kernel accepted proof | pinned kernel and library hash |
| theorem | theorem status in declared authority scope | peer reviewed or formal route |
| conjecture | explicit unproven claim | conjecture witness |
| open_problem | known unresolved question | source/reference witness |
| retracted | source or review retracted claim | retraction witness |
| rejected | invalid under current schema or assumptions | rejection record |

---

## 2. Promotion prohibitions

1. `computational_evidence` may not become `theorem` by confidence score alone.
2. `literature_supported` may not become `kernel_checked_theorem` without formal artifact.
3. `conjecture` may not become `theorem` by analogy.
4. `proof_sketch` must retain gaps unless filled.
5. `theorem` status is scoped to assumptions and authority profile.

---

## 3. Demotion triggers

1. counterexample discovered;
2. assumption mismatch;
3. notation parse error;
4. proof gap found;
5. source retraction;
6. library/kernel version invalidates formal proof;
7. computation replay failure;
8. policy veto.


---

## v1.6 full-corpus upgrade note

This document is retained from the first v1.6 math-integration pass and is now part of the complete v1.6 Draft 1 corpus alongside all v1.5 Draft 2 carry-forward files.
