# Corpus Review - v1.6 Draft 3 to v1.6 Draft 4

Status: corpus review.
Generated: 2026-05-08

## Review goal

Draft 4 exists to correct two issues:

1. Produce a complete standalone package at least as comprehensive as Draft 3.
2. Update the corpus for the latest observed SRNN Server runtime changes.

## Baseline

The physical baseline is the uploaded `v1.6 - Draft 3.zip` archive. It contains:

- 205 files total;
- 199 Markdown files;
- 806,649 bytes of uncompressed file content;
- a full Draft 3 RC-closure body rather than a small overlay.

## Draft 4 action

Draft 4 copies the baseline into a new `v1.6 - Draft 4/` directory and then adds
new Draft 4 documents, manifest entries, validation records, runtime profiles,
source observations, and migration notes.

## Carry-forward decision

Existing Draft 1, Draft 2, and Draft 3 files are retained because they provide
historical lineage, previous review notes, old manifests, and contract continuity.
Draft 4 does not delete those files or rewrite history. Instead, Draft 4 adds
active entry points and marks the earlier material as carried forward unless a
new Draft 4 document supersedes it.

## Source-refresh decision

The key new SRNN changes are not limited to one code file. Draft 4 therefore
adds a source-refresh document plus topic-specific profiles:

- federated runtime stack;
- llama-server runtime readiness;
- GPU worker large-model runtime;
- runtime model observability;
- Agent Lab/MCP backup witness records;
- conformance plan update;
- security and memlock profile;
- migration note from Draft 3 to Draft 4.

## Validation conclusion

Draft 4 is complete as a corpus package when:

- every Draft 3 file is present;
- every Draft 4 entry point is present;
- the manifest lists all files;
- package checksums are generated;
- the ZIP contains the actual corpus files and not only scripts or overlays.

This generated package satisfies those packaging conditions.
