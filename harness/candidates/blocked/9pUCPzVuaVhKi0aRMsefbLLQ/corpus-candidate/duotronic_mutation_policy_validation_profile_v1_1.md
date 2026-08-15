# Mutation Policy and Validation Profile v1.1

Status: observed plus normative source-governance profile.

## Mutation levels

```yaml
MutationLevel:
  DENY: no automated mutation allowed
  REVIEW_REQUIRED: manual review required
  AUTO_ALLOWED: automatic mutation allowed for bounded types
  GENERATED: regenerable artifacts only
```

## Mutation types

```yaml
MutationType:
  REFACTOR
  BUGFIX
  FEATURE
  DOCS
  DEPS
  CODEGEN
  SECURITY
```

## Source classes

| Path class | Default level |
|---|---|
| Oracle witness core | DENY |
| Math canon core | DENY or REVIEW_REQUIRED |
| DBP envelope identity | DENY or REVIEW_REQUIRED |
| Policy engine | REVIEW_REQUIRED |
| Replay package logic | REVIEW_REQUIRED |
| Proof witness/checker logic | REVIEW_REQUIRED |
| SDK generated clients | GENERATED |
| Documentation | AUTO_ALLOWED or REVIEW_REQUIRED |

## Validation suite coverage

Observed Draft 2 phase 3 validation suite covers:

- SDK structure;
- formal model artifacts;
- threat model sections;
- mutation policy;
- proof interchange;
- OpenAPI export;
- Duotronic core conformance;
- Python SDK tests.

## Commit `44ec052` validation update

Python SDK tests should run from the SDK root with source-layout import support.

Required runner behavior:

```text
cwd = sdk/duotronic-python
pytest tests/test_client.py -v --tb=short --import-mode=importlib
PYTHONPATH = sdk/duotronic-python/src
```

## Generated docs rule

Generated documentation bundles may be auto-created. Merging them into the normative corpus requires review if they modify canonical math status, promotion thresholds, security requirements, policy defaults, replay identity rules, or MCP tool authority.

