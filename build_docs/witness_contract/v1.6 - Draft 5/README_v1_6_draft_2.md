# Duotronic v1.6 Draft 2 Corpus

**Status:** implementation-ready draft corpus  
**Version:** v1.6-draft-2  
**Generated:** 2026-04-30  
**Document kind:** full active corpus update, preserving v1.5 Draft 2 carry-forward coverage and v1.6 Draft 1 implementation material  
**Primary purpose:** Promote v1.6 from an implementation-ready architecture draft to a more complete production-specification draft grounded in current Duotronics repository material, current `srnn_server` backend state, and live MCP server tooling observations.

---

## 1. Executive summary

v1.6 Draft 2 keeps the full v1.6 Draft 1 corpus and applies the next hardening pass.

Draft 2 adds:

1. formal semantics and verification planning;
2. a STRIDE-style threat model;
3. proof interchange and proof-carrying computation rules;
4. standards alignment for OpenAPI, problem details, hash/signature formats, and proof artifacts;
5. human-review state machines and quorum rules;
6. live MCP server tooling integration;
7. MCP capability and self-test observation records;
8. SRNN current-backend review notes;
9. direct host-mutation MCP tool security rules;
10. cognition-loop schema migration note;
11. Minecraft/Mineflayer MCP action profile upgrade;
12. multimodal witness runtime profile upgrade;
13. production release checklist;
14. updated manifest and reading guide.

Draft 2 does not remove v1.5 material. It preserves the v1.5 Draft 2 carry-forward surface, the v1.6 Draft 1 implementation-ready additions, and adds new documents under this active Draft 2 folder.

---

## 2. Authority model

The active source path for this draft is:

```text
build_docs/witness_contract/v1.6 - Draft 2/
```

This corpus supersedes v1.6 Draft 1 for draft-review purposes. It does not delete prior material. Draft 1 materials retained in this folder are historical and compatibility references unless the Draft 2 reading guide marks them active.

---

## 3. Current backend observations incorporated

Draft 2 incorporates observations from the live Xavi.app MCP endpoint and the current `srnn_server` repository state:

1. MCP server name: `xavi-agent-lab`.
2. MCP tool count observed: `127`.
3. MCP tool families include Xavi data tools, repo tools, ops tools, browser tools, meta tools, social tools, cognition/witness tools, backup tools, and Minecraft/Mineflayer tools.
4. MCP principal scopes observed for the ChatGPT user include `mcp:read`, `mcp:write`, `mcp:ops-request`, and `mcp:minecraft-action`.
5. Transport protection includes DNS rebinding protection and an allowlist for localhost and `mcp.xavi.app`.
6. Docker is installed; Playwright package import is available but the capability report says Playwright browser install is not currently active.
7. Current SRNN git head observed by MCP self-test: `3b52b6a`.
8. Minecraft mode observed as `disabled`, with the bridge file present at the configured bridge path.
9. Direct mutation tools exist and require explicit governance: `write_file_system` and `execute_system_command`.
10. A schema mismatch was observed for cognition loop listing: the tool returned `column "step" does not exist`, which Draft 2 treats as a migration note rather than expected runtime behavior.

---

## 4. Primary Draft 2 entry points

Start here:

1. `v1_6_draft_2_reading_guide.md`
2. `RELEASE_NOTES_v1_6_draft_2.md`
3. `corpus_review_v1_6_draft_1_to_v1_6_draft_2.md`
4. `IMPLEMENTATION_READINESS_GAP_CLOSURE_v1_6_draft_2.md`
5. `duotronic_mcp_server_tooling_integration_v1_0.md`
6. `duotronic_srnn_backend_current_state_review_2026_04_30.md`
7. `duotronic_formal_semantics_and_verification_v1_0.md`
8. `duotronic_stridethreat_model_v1_0.md`
9. `duotronic_proof_interchange_and_certificates_v1_0.md`
10. `duotronic_human_review_state_machine_v1_0.md`

---

## 5. Non-claim

Draft 2 canonizes object forms, witness forms, bridge semantics, backend contracts, interpreter evidence, and review processes. It does not claim to prove unresolved mathematical conjectures, including open Langlands conjectures. It records conjectures, evidence, computational experiments, proof witnesses, and theorem statuses under explicit authority scopes.
