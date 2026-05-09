# Duotronic v1.6 Draft 4 Complete Corpus

Status: complete Draft 4 corpus package.
Generated: 2026-05-08
Base package: uploaded `v1.6 - Draft 3.zip`.

## Summary

v1.6 Draft 4 is a full corpus update built from the complete Draft 3 archive.
It does not replace the Draft 3 corpus with a thin overlay. It preserves the
entire Draft 3 body of files, adds Draft 4 entry points, updates the active
manifest, and folds in the current SRNN Server runtime changes observed after
the Draft 3 source-refresh pass.

Draft 4 should be read as the comprehensive successor to Draft 3. Draft 3
remains present as carried-forward history and as the source baseline for the
Draft 4 deltas.

## What Draft 4 adds

Draft 4 adds or upgrades the following implementation-facing layers:

1. **SRNN runtime source refresh through 2026-05-08.** Draft 4 incorporates the
   current SRNN Server updates around the unified federated compose stack,
   per-node WG-RNN service, GPU worker large-model runtime, llama-server manager,
   runtime model manifests, smoke/bench endpoints, memlock diagnostics, and
   model runtime test coverage.
2. **Full carry-forward completeness.** Every file from the uploaded Draft 3
   package is copied into Draft 4. Draft 4 is a complete standalone corpus, not
   a patch that requires hunting down missing files.
3. **Runtime model readiness contract.** New Draft 4 profiles define how
   llama-server runtime status, effective command reporting, binary detection,
   memlock capability, context size, CPU-MoE split, cache-type flags, and smoke
   benchmark evidence should be recorded as witness-bearing runtime state.
4. **Federated stack alignment.** Draft 4 updates the contract language to match
   the SRNN compose topology: core stores, SRNN/SRNN-GPU, GPU worker, Redis,
   Ollama/Ollama-GPU, Ollama proxy and remote proxy, Hovod, SearXNG, LibreChat,
   Agent Lab, and the `wg-rnn` recurrent cognition service.
5. **MCP/Agent Lab mutation evidence handling.** Draft 4 captures recent
   execute-system-command backup-log commits as audit evidence, while keeping
   the governance boundary clear: backup existence is evidence of a mutation
   process, not proof of semantic correctness.
6. **Validation and non-claim clarity.** Draft 4 records what was source-observed,
   what is executable, what is tested at the source level, and what still needs
   live runtime verification.

## Primary Draft 4 entry points

```text
START_HERE_v1_6_draft_4.md
README_v1_6_draft_4.md
RELEASE_NOTES_v1_6_draft_4.md
CORPUS_INDEX_v1_6_draft_4.md
corpus_review_v1_6_draft_3_to_v1_6_draft_4.md
duotronic_draft4_srnn_source_refresh_2026_05_08.md
duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md
duotronic_srnn_federated_runtime_stack_profile_v1_0.md
duotronic_draft4_runtime_model_observability_profile_v1_0.md
duotronic_draft4_agent_lab_mutation_backup_witness_profile_v1_0.md
runtime/llama_server_runtime_readiness_contract_v1_0.md
refs/manifest/MANIFEST_v1_6_draft_4_complete.md
```

## Draft 4 rule

Draft 4 is authoritative for the v1.6 Draft 4 line, but it is additive and
traceable. Files whose names still include Draft 1, Draft 2, or Draft 3 are
retained as carried-forward history or baseline documents. The active Draft 4
orientation, source refresh, release notes, and manifest are the Draft 4 entry
points listed above.

## Apply rule

Copy this directory as a complete corpus package:

```text
build_docs/witness_contract/v1.6 - Draft 4/
```

Do not apply Draft 4 by copying only the new files. Draft 4 is intended to be a
full standalone directory.
