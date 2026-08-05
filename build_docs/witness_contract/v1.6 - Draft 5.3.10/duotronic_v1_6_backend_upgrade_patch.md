# v1.6 Backend Upgrade Patch

**Status:** normative patch document  
**Applies to:** all v1.6 Draft 2 documents  
**Purpose:** One patch that upgrades all retained v1.5 Draft 2 files to the new backend and mathematical canon without dropping source coverage.

## 1. Universal backend substitution

Any v1.5 text that says the canonical implementation target is undecided is now read with this v1.6 binding:

- Python/FastAPI is the current transition implementation.
- PostgreSQL is the planned canonical transactional store.
- Milvus is semantic/vector retrieval only.
- Redis is ephemeral coordination/cache/pubsub/meta-object exchange.
- Rust is the major final control-plane candidate.
- Lisp/SBCL is the symbolic specialist runtime through JSON-RPC.
- Julia is the math-kernel runtime.
- PHP is legacy/transitional and cannot own new backend authority.

## 2. Universal math substitution

Any v1.5 text that frames DPFC as the representational core is retained, but v1.6 adds the Mathematical Canon above it. DPFC is one canonical representation discipline; it is not the exclusive representation for all mathematics.

## 3. Universal witness substitution

Any v1.5 witness path now admits these additional witness kinds:

```yaml
MathObjectWitness:
  domain_id: string
  object_kind: string
  canonical_identity_hash: string
  source_profile_id: string
  normalizer_id: string
  replay_identity_ref: string
  status: candidate | canonicalized | audit_only | rejected

MathematicalClaimWitness:
  claim_kind: definition | theorem | conjecture | lemma | corollary | example | counterexample | computation | analogy
  truth_status: formal_proof_verified | literature_supported | computationally_supported | conjectural | disproven | unknown | analogy_only
  evidence_refs: []
  proof_witness_refs: []
  interpreter_run_refs: []
  policy_decision_id: string

InterpreterRunWitness:
  runtime: python | julia | lisp | other
  runtime_version: string
  input_artifact_ref: string
  output_artifact_ref: string
  stdout_hash: string
  stderr_hash: string
  dependency_lock_ref: string
  replay_identity_ref: string
  authority_scope: computation_support | proof_checker_result | example_generation | counterexample_search | benchmark
```

## 4. SRNN-specific substitution

Any v1.5 runtime queue, task, oracle, or node witness now records the SRNN v1.6 fields when available:

```yaml
SRNNBackendWitnessFields:
  loop_id: string
  node_id: string
  oracle_job_id: string
  input_artifact_ref: string
  output_artifact_ref: string
  replay_identity_ref: string
  witness_event_id: string
  temporal_meta_objects: []
  source_clock: event_time | ingestion_time | replay_time | external_clock
  binding_confidence: number
```

## 5. Interpreter authority rule

Code can support a claim but cannot become proof by itself unless the interpreter run is explicitly a proof-checker run and its proof authority profile accepts that checker, version, dependencies, and input artifact.
