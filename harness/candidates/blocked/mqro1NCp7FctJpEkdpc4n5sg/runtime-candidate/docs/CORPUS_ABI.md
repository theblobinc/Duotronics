# Corpus ABI

A corpus bundle is loaded as a versioned candidate. Activation should be explicit and witness-backed.

Recommended layout:

```text
corpus/
  manifest.json
  corpus.lock
  schemas/
  policies/
  migrations/
  formal/
    lean4/
    tlaplus/
  conformance/
  mcp/
  adapters/
  docs/
```

Required manifest fields:

- `corpus_id`
- `version`
- `schema_version`

The runtime computes a corpus digest from the manifest and file digests. Every evidence claim and witness includes the corpus reference available when it was emitted.
