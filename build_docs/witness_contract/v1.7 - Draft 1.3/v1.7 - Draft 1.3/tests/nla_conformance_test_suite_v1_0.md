# NLA Conformance Test Suite v1.0

Status: active Draft 5 test specification.

## Purpose

This suite defines tests a later implementation must pass before claiming Draft 5
NLA support.

## Test groups

### Group 1 - Schema tests

1. Valid witness fixture passes `nla_activation_witness.schema.json`.
2. Missing `source_model` fails.
3. Missing activation digest fails.
4. Invalid lifecycle state fails.
5. Audit-only policy with memory write true fails project policy review.

### Group 2 - Activation capture tests

1. Captured vector records d_model, layer, token, norm, digest, dtype.
2. Unsupported backend records `hidden_states_unavailable` and cannot create an
   accepted witness.
3. Token text can be redacted while preserving token hash.
4. Retention class defaults to ephemeral.

### Group 3 - AV runtime tests

1. Sidecar missing -> failure.
2. Tokenizer/sidecar mismatch -> failure.
3. Injection position missing -> failure.
4. Valid output parses explanation.
5. Invalid output becomes diagnostic-only.

### Group 4 - AR and fidelity tests

1. AR returns vector with matching d_model.
2. Dimension mismatch -> failure.
3. High cosine witness accepted.
4. Low cosine witness quarantined.
5. AR unavailable witness remains unscored diagnostic.
6. Repeat instability prevents promotion.

### Group 5 - Policy tests

1. NLA witness cannot write user memory.
2. NLA witness cannot change policy authority.
3. NLA witness cannot trigger mutation.
4. NLA explanation cannot be treated as executable instruction.
5. Sensitive explanation routes to human review.

### Group 6 - Replay tests

1. Fixture replay reproduces explanation class or similarity envelope.
2. Fixture replay reproduces score within configured tolerance.
3. Runtime config digest is recorded.
4. Release bundle includes manifest and checksums.

## Minimum pass condition for Draft 5 implementation claim

All Group 1 through Group 5 tests must pass. Group 6 must pass for release
claims, but may be pending for local prototype claims if clearly labeled.
