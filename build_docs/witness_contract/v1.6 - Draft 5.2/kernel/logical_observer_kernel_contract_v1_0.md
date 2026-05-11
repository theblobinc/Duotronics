# Logical Observer Kernel Contract v1.0

**Status:** Draft 5.2 additive kernel layer; completion-candidate, not frozen.  
**Applies to:** Duotronic Witness Contract v1.6 Draft 5.2.  
**Purpose:** Define the deterministic machine that executes the Draft 5.2 evidence language without silently inventing truth, authority, memory, proof, or replay validity.

## 1. Kernel boundary

Draft 5.2 already defines the language of evidence. This contract defines the observer kernel that runs that language. The kernel is normative: an implementation may realize it in any runtime, but it must preserve the witness, authority, replay, and non-collapse rules defined here.

The kernel is fail-closed. Any missing witness, missing authority, ambiguous canonical rule, replay assumption gap, non-collapse violation, or resource violation produces a typed witness instead of prose-only refusal.

## 2. Boot instruction set

A logical observer loads the corpus using the following boot sequence:

```text
BOOT_CORPUS
LOAD_MANIFEST
VERIFY_HASH_CLOSURE
RESOLVE_ACTIVE_VERSION
LOAD_SCHEMA_REGISTRY
LOAD_AUTHORITY_TABLE
ENTER_SAFE_MODE_IF_AMBIGUOUS
```

Boot succeeds only when the manifest hash closure verifies, the active rule set is resolved, the schema registry is loadable, and no compatibility ambiguity remains unresolved. Ambiguity enters safe mode and emits `CorpusRuleResolutionWitness` plus, when necessary, `KernelErrorWitness`.

## 3. Canonical resolver instruction set

The corpus carries historical Draft 2 through Draft 5.1 files. A runtime MUST NOT pick historical rules opportunistically. For every concept that might be governed by multiple files, the resolver executes:

```text
RESOLVE_RULE(concept)
SELECT_ACTIVE_CONTRACT(layer, version)
APPLY_SUPERSESSION_CHAIN
CHECK_COMPATIBILITY_EXCEPTION
REPORT_AMBIGUITY
```

Resolution order is:

1. Active Draft 5.2 evidence-language files govern the evidence language.
2. Draft 5.1 remains authoritative for NLA release, rollback, self-training, activation witness safety, truth-observer authority, and audit-only restrictions unless an active Draft 5.2 file explicitly strengthens the rule.
3. Earlier drafts are historical unless named by a supersession chain or compatibility exception.
4. Ambiguous resolution MUST deny, defer, fork, or escalate; it MUST NOT silently choose.

## 4. Observer capability instruction set

A logical observer cannot act solely by being present in the runtime. It must have a profile and bounded capability token:

```text
DECLARE_OBSERVER
CHECK_CAPABILITY
CHECK_SCOPE
CHECK_RUNTIME_MODE
CHECK_CHANNEL_AUTHORITY
CHECK_DELEGATION_CHAIN
DOWNGRADE_FORCE
DENY_OR_ESCALATE
```

Capabilities are explicit. Force, scope, runtime mode, delegation depth, resource limits, and policy references are checked before any task is executed.

## 5. Logical task instruction set

Tasks are first-class kernel objects:

```text
CREATE_TASK
TYPECHECK_TASK
PLAN_TASK
ALLOCATE_BUDGET
EXECUTE_DETERMINISTIC_STEP
EMIT_STEP_WITNESS
COMMIT_RESULT
ROLLBACK_RESULT
EXPORT_TASK_TRACE
```

A task cannot commit without a `TaskResultWitness`. Each deterministic step emits a `TaskStepWitness`. Hidden state is invalid in replayable computation.

## 6. Evidence transaction instruction set

Runtime effects are wrapped in evidence transactions:

```text
BEGIN_EVIDENCE_TX
ASSERT_PRECONDITIONS
EMIT_WITNESS
CHECK_NON_COLLAPSE
CHECK_POLICY
PERSIST_WITNESS
COMMIT_TX
ABORT_TX
```

No witness means no commit. A committed transaction MUST list emitted witnesses and persisted witnesses. An aborted transaction MUST list the reason or error witness.

## 7. Error and refusal instruction set

Errors are typed evidence:

```text
RAISE_MISSING_WITNESS
RAISE_AUTHORITY_DENIED
RAISE_NON_COLLAPSE_VIOLATION
RAISE_REPLAY_ASSUMPTION_MISSING
RAISE_INDETERMINATE_RESULT
ESCALATE_TO_HUMAN_REVIEW
```

Every denial, refusal, or escalation emits `KernelErrorWitness`.

## 8. Deterministic computation instruction set

The kernel may compute only through deterministic, replayable operations:

```text
READ_OBJECT
HASH_OBJECT
COMPARE
VALIDATE_SCHEMA
EVALUATE_PREDICATE
RUN_PURE_FUNCTION
CHECK_RESULT
RETURN_STATUS
```

The computation VM inherits the replay grammar prohibitions: no network fetch, no randomness, no wall-clock dependency, no hidden mutation, no authority replacement, and no evidence deletion.

## 9. Logical memory instruction set

Memory is not truth. The kernel distinguishes observation, cache, candidate fact, canonical fact, and authority reference:

```text
READ_MEMORY_CELL
WRITE_OBSERVATION
WRITE_CANDIDATE_FACT
PROMOTE_MEMORY_CELL
MARK_STALE
PURGE_WITH_WITNESS
SNAPSHOT_MEMORY
REPLAY_MEMORY_STATE
```

Canonical memory requires promotion evidence. Purge requires a witness. Replayable memory requires a snapshot and deterministic trace.

## 10. Conflict and adjudication instruction set

Conflicts are detected and represented; they are not collapsed:

```text
DETECT_CONFLICT
CLASSIFY_CONFLICT
OPEN_ADJUDICATION
COMPARE_AUTHORITY
COMPARE_EVIDENCE
MERGE_IF_COMPATIBLE
FORK_IF_INCOMPATIBLE
MARK_UNRESOLVED
```

An unresolved conflict remains unresolved and emits `ConflictAdjudicationWitness` plus, when needed, `KernelErrorWitness`.

## 11. Resource and safety instruction set

Observers run under explicit resource budgets:

```text
SET_RESOURCE_BUDGET
CHECK_RECURSION_DEPTH
CHECK_TIME_BUDGET
CHECK_MEMORY_BUDGET
DENY_NETWORK
DENY_RANDOMNESS
DENY_MUTATION
ENTER_QUARANTINE_MODE
```

Replay and verification modes deny network, randomness, and wall-clock access. Mutation is denied unless a transaction explicitly permits a bounded witness-emitting write.

## 12. Kernel state

```text
KernelState =
  corpus_manifest
  active_rule_set
  schema_registry
  authority_registry
  observer_registry
  task_queue
  evidence_store
  non_collapse_graph
  replay_store
  policy_engine
  audit_log
```

## 13. Kernel object model

The kernel layer adds the following normative object schemas:

```text
LogicalObserverProfile
ObserverCapabilityToken
ObserverTask
TaskFrame
TaskStepWitness
TaskResultWitness
KernelTransaction
KernelErrorWitness
CorpusRuleResolutionWitness
ConflictAdjudicationWitness
ResourceBudgetWitness
KernelState
ExecutionTrace
LogicalMemoryCell
```

## 14. Syscall table

| Syscall | Purpose | Required witness |
| --- | --- | --- |
| `observe()` | Record an observation | `EvidenceClaim` |
| `compose()` | Build compound claim | `CompoundClaimWitness` |
| `infer()` | Derive proposal from premises | `InferenceWitness` |
| `verify()` | Run deterministic verification | `VerificationResult` |
| `replay()` | Reconstruct from assumptions/grammar | `ReplayAssumptionManifest`, `VerificationResult` |
| `delegate()` | Transfer bounded authority | `AuthorityDelegationChain` |
| `promote()` | Change claim/model/status authority | `ClaimStatusTransition`, `NonCollapseTransition` |
| `compute()` | Run bounded deterministic computation | `TaskStepWitness`, `TaskResultWitness` |
| `adjudicate()` | Resolve conflict | `ConflictAdjudicationWitness` |
| `rollback()` | Undo failed transaction | `KernelTransaction` |
| `export()` | Produce replayable bundle | `ReplaySign`, `VerificationGrammar` |

## 15. Kernel execution loop

1. Receive task.
2. Resolve active corpus rules.
3. Authenticate observer.
4. Check observer capability and delegation.
5. Classify task: observe, compose, infer, verify, replay, promote, compute, adjudicate, memory, or export.
6. Typecheck against schemas.
7. Open evidence transaction.
8. Run non-collapse precheck.
9. Execute deterministic computation or logical operation.
10. Emit step witness.
11. Evaluate policy.
12. Persist witnesses.
13. Commit result, deny, defer, fork, rollback, or escalate.
14. Append replayable execution trace.

## 16. Kernel invariants

```text
K1. No effect before witness.
K2. No promotion without policy decision.
K3. No theorem/proof status without proof witness.
K4. No authority escalation by repetition.
K5. No self-trained-to-authoritative transition without gate path.
K6. No replay claim without assumptions and deterministic grammar.
K7. No hidden state in observer computation.
K8. No network, randomness, or wall-clock dependency in replay mode.
K9. Every refusal is itself a typed witness.
K10. Every ambiguity resolves to deny, defer, fork, or human escalation.
```
