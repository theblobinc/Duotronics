# Application Notes — Draft 3 Completed Corpus

Status: operational guidance.

## Recommended destination

```text
build_docs/witness_contract/v1.6 - Draft 3/
```

## Manifest directory rule

All manifest documents belong under:

```text
refs/manifest/
```

## Merge gate checklist

- [ ] Confirm current source commit baseline.
- [ ] Confirm local working-tree modifications.
- [ ] Confirm test status or record tests not run.
- [ ] Confirm OpenAPI export status.
- [ ] Confirm formal proof status labels stubs honestly.
- [ ] Confirm unresolved conjectures are not promoted to theorems.
- [ ] Confirm target MCP tools are not marked verified until manifest confirms them.
- [ ] Confirm generated docs do not alter source behavior.
- [ ] Confirm worktree directories are not accidentally committed.

## Suggested tests

```bash
pytest tests/test_duotronic_draft2_phase3_suite.py -q
pytest tests/test_duotronic_v1_6_conformance.py tests/test_duotronic_v1_6_tier2_conformance.py -q
python -m pytest tests/test_duotronic_openapi_export.py -q
```

