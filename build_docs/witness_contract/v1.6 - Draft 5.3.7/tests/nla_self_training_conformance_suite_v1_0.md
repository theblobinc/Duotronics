# NLA Self-Training Conformance Suite v1.0

Status: active Draft 5.1 test specification.

## Test groups

### Group 1 - Truth observer registry

1. Register hidden-state capable observer.
2. Register API-only observer.
3. API-only observer fails residual NLA claims.
4. Capability changes create new registry digest.

### Group 2 - Training memory

1. Raw capture example persists with artifact ref and digest.
2. Raw private example cannot enter curriculum without review.
3. Heldout examples cannot be used in training.
4. Failure examples persist and are used in eval.

### Group 3 - Self-training witness

1. Valid `NlaSelfTrainingWitness` passes schema.
2. Missing rollback ref fails promotion.
3. `may_write_memory=true` fails schema.
4. Increased confabulation fails audit gate.

### Group 4 - Promotion gates

1. Trained candidate enters shadow only after eval.
2. Shadow candidate cannot affect outputs.
3. Audit candidate cannot write memory.
4. Release candidate requires operator approval.
5. Rollback metadata exists and is testable.

### Group 5 - Safety regression

1. Candidate with lower average score is rejected.
2. Candidate with higher average score but more privacy violations is rejected.
3. Candidate with higher average score but worse failure-case behavior is rejected.
4. Candidate with no human review for sensitive findings is rejected.
