# Release Notes — Duotronic v1.6 Draft 3 Completed

Status: release notes.

## Summary

Draft 3 Completed is the consolidated documentation pass after the SRNN server source refresh. It keeps the Draft 3 corpus, updates the runtime recurrence profile, and folds in the newest backend implementation observations.

## Included source refreshes

### SRNN commit `44ec052`

Observed update:

- Python SDK tests in `tests/test_duotronic_draft2_phase3_suite.py` now run from `sdk/duotronic-python`.
- Test command uses `tests/test_client.py`, `--import-mode=importlib`, and a `PYTHONPATH` pointing at `sdk/duotronic-python/src`.
- Failure output now captures both stdout and stderr for better diagnostics.
- Worktree directories appeared as gitlinks in the commit, showing the need for generated-doc rules that avoid accidentally committing active worktrees.

### WGRNN Firehose working tree

Observed local working tree status includes modified and new files in:

```text
packages/wgrnn_firehose/
  controller.php
  css/wgrnn-firehose.css
  js/main.js
  js/constants.js
  js/utils.js
  js/mixins/
```

Draft 3 Completed treats this as an active UI/runtime observation package. It is documented as working-tree state, not a finalized release claim.

### Previous Draft 2 and Draft 3 implementation baseline

Included from prior review:

- SDK packages for Python and JavaScript/TypeScript.
- TLA+ task delegation and policy formal model.
- Lean 4 core proof framework.
- OpenAPI export and API route surface.
- Cognition step migration and snapshot compatibility.
- Proof interchange fixtures.
- Mutation policy defaults.
- SDK STRIDE threat model.
- Direct MCP mutation tools with auto backup/git sync and audit redaction.
- Stdio principal mapping.
- Allowed host-root enforcement.
- Live recurrent witness overlay.
- Stale evidence quarantine/degrade rules.

## Release boundary

This corpus is documentation and integration guidance. It does not certify that all tests pass, that all Lean proofs are complete, or that unresolved mathematical conjectures have been proven.

