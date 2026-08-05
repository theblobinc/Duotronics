# Evidence Language Operating System Primer v1.0

## Purpose

This primer explains how Draft 5.2 acts as an operating system for truthful behavior. It is not a software kernel. It is a normative execution layer for AI, runtime tools, replay systems, policy engines, and reviewers.

## Kernel objects

The kernel objects are:

- `EvidenceClaim`: first-class atomic claim.
- `CompoundClaimWitness`: explicit composition of claims.
- `InferenceWitness`: explicit inference from premises to conclusion.
- `PragmaticContext`: who is speaking, to whom, through which channel, with what force.
- `PolicyDecisionEvidenceExtension`: policy decision with evidence-language force semantics.
- `AuthorityDelegationChain`: delegated authority path and limits.
- `NonCollapseState`: primitive state identity.
- `NonCollapseTransition`: explicit attempted or approved state transition.
- `ReplayAssumptionManifest`: assumptions required for replay.
- `VerificationGrammar`: deterministic replay-check language.
- `VerificationResult`: output of deterministic verification.
- `ReplaySign`: replay self-description marker.

## Execution loop

1. Parse the requested operation into claim/action form.
2. Determine whether the operation creates, composes, infers, promotes, replays, delegates, or verifies.
3. Select the required schema set.
4. Evaluate pragmatic authority before accepting force.
5. Evaluate non-collapse before changing status.
6. Emit witness objects before runtime effects.
7. Persist witness objects before promotion.
8. Refuse or escalate when a required witness, assumption, proof, or authority chain is missing.

## Truth discipline

Draft 5.2 does not let policy approval become truth. Policy approval may authorize an assertion, release, or runtime action. It does not prove a theorem, establish a fact, or create activation-backed truth unless the corresponding witness class exists.

## Replay discipline

Deep-time replay is only valid when replay assumptions are explicit, required assumptions are satisfied, the verification grammar is deterministic, and verification results are recorded. A replay package without assumptions is not deep-time replay; it is at most a local reconstruction attempt.

## Non-collapse discipline

Every attempted transition across primitive categories must be represented. If the transition crosses a forbidden pair, it must be denied, escalated, or accompanied by the required external/proof witness. Silent collapse is never valid.

## Logical observer kernel

Draft 5.2 now has an explicit logical observer kernel layer. The evidence language is the instruction language; the observer kernel is the deterministic machine that executes it. The kernel adds `LogicalObserverProfile`, `ObserverCapabilityToken`, `ObserverTask`, `TaskFrame`, `TaskStepWitness`, `TaskResultWitness`, `KernelTransaction`, `KernelErrorWitness`, `CorpusRuleResolutionWitness`, `ConflictAdjudicationWitness`, `ResourceBudgetWitness`, `KernelState`, `ExecutionTrace`, and `LogicalMemoryCell`.

The kernel boot sequence verifies the manifest hash closure, resolves the active rule set, loads schemas and authority tables, and enters safe mode if canonical rule resolution is ambiguous. Every effect is inside an evidence transaction, every step emits a witness, and every refusal is itself typed evidence.
