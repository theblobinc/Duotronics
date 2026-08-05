# Duotronic v1.6 Draft 5.2 — SRNN Server Implementation Guide

**Status:** Planning document for future implementation  
**Repository:** `/home/runner/work/srnn_server/srnn_server`  
**Audience:** Future implementors, especially ChatGPT 5.5 / Copilot agents carrying out Draft 5.2  
**Purpose:** Describe, in concrete repository terms, what Draft 5.2 will require across code, schemas, persistence, APIs, MCP tooling, formal models, and tests.

---

## 1. Executive intent

Draft 5.2 is not a small extension to Draft 5.1. It changes the center of gravity of the Duotronic runtime from:

- witness records,
- authority gates,
- replay bundles,
- and proof/non-proof separation

into a more explicit **formal language of evidence** with four enforced layers:

1. **Syntax of Evidence**
2. **Pragmatics of Authority**
3. **Semiotics of Replay**
4. **Metaphysics of Non-Collapse**

In this repository, that means Draft 5.2 should be implemented as a **cross-cutting upgrade** over the existing Draft 5.1 substrate, not as a new isolated subsystem.

The current codebase already contains the right foundations:

- `srnn/duotronic/dbp_envelope.py`
- `srnn/duotronic/policy_engine.py`
- `srnn/duotronic/replay_package.py`
- `srnn/duotronic/math_canon.py`
- `srnn/duotronic/proof_witness.py`
- `srnn/cognition/truth_observer_registry.py`
- `srnn/cognition/nla_policy_enforcement.py`
- `srnn/cognition/nla_training_witness.py`
- `srnn/cognition/nla_release_evidence_bundle.py`
- Duotronic API routes in `api/routes/duotronic_v2.py`
- existing conformance tests in `tests/test_duotronic_v1_6_conformance.py`, `tests/test_duotronic_v1_6_tier2_conformance.py`, and NLA integration tests

Draft 5.2 should therefore be treated as a **semantic unification pass** over existing runtime structures.

---

## 2. Current baseline in this repository

### 2.1 What already exists

The repository already enforces several Draft 5.2-adjacent ideas:

#### DBP / object envelope
- `srnn/duotronic/dbp_envelope.py` already provides:
  - canonical identity hash,
  - payload hash,
  - authority scope,
  - runtime mode,
  - policy decision reference,
  - replay identity reference.

#### Policy
- `srnn/duotronic/policy_engine.py` already models:
  - principals,
  - action kinds,
  - runtime modes,
  - obligations,
  - explicit policy decisions,
  - default-deny behavior.

#### Replay
- `srnn/duotronic/replay_package.py` already models:
  - replay packages,
  - artifact manifests,
  - schema/runtime manifests,
  - expected results,
  - verification status.

#### Math claims / non-collapse
- `srnn/duotronic/math_canon.py` already enforces:
  - structured claim lifecycle,
  - status transitions,
  - proof-authority gating,
  - prohibition on auto-promoting computation to theorem.

#### Proof witnesses
- `srnn/duotronic/proof_witness.py` already separates:
  - proof witness,
  - conjecture witness,
  - computation-to-theorem profiles,
  - proof authority completeness.

#### Truth observers / NLA authority
- `srnn/cognition/truth_observer_registry.py` already models:
  - observer capabilities,
  - activation capture modes,
  - NLA training/inference permissions,
  - fallback modes,
  - compatibility profiles.

- `srnn/cognition/nla_policy_enforcement.py`, `nla_training_witness.py`, `nla_release_evidence_bundle.py`, and `nla_persistence.py` already encode:
  - self-training witness records,
  - promotion gates,
  - release evidence bundles,
  - policy restrictions,
  - persistence tables.

### 2.2 What is still missing

The current runtime does **not** yet have a first-class implementation of:

- compositional claims,
- inference witnesses,
- replay assumption manifests,
- verification grammar,
- pragmatic force markers,
- delegated authority chains,
- non-collapse constraints as a reusable policy primitive,
- deep-time replay conformance,
- schema-level locks for forbidden epistemic transitions,
- or formal evidence grammar objects exposed through APIs and storage.

That is the real Draft 5.2 gap.

---

## 3. Design goal for Draft 5.2 in SRNN server

The implementation goal should be:

> make every claim, transition, inference, authority statement, and replay package in SRNN/Duotronic expressible in one explicit evidence language

That language should be visible in:

- DBP envelopes,
- policy decisions,
- math claims,
- proof witnesses,
- observer authority records,
- replay bundles,
- database tables,
- API request/response shapes,
- MCP/admin tools,
- and formal model files.

Draft 5.2 should **not** replace Draft 5.1’s safety posture. It should make that posture explicit, composable, and replayable.

---

## 4. High-level implementation strategy

Draft 5.2 should be implemented in seven coordinated workstreams:

1. **New schemas and formal document corpus**
2. **Core Python datamodel additions**
3. **Policy engine upgrades**
4. **Replay system upgrades**
5. **Persistence and migration changes**
6. **API and MCP/tooling changes**
7. **Formal-model and conformance-test expansion**

The work should be done in this order because each later stage depends on the earlier semantic definitions.

---

## 5. Required new artifacts

The following artifacts should be added exactly or near-exactly as named in the Draft 5.2 specification.

### 5.1 New authority and theory contracts

Recommended location: a new Draft 5.2 docs subtree under `docs/duotronic/` or equivalent runtime-spec area.

- `authority/syntax_of_evidence_contract_v1_0.md`
- `authority/pragmatics_of_authority_contract_v1_0.md`
- `authority/semiotics_of_replay_contract_v1_0.md`
- `authority/metaphysics_of_non_collapse_contract_v1_0.md`

These should become the normative source for future runtime code.

### 5.2 New runtime contracts

- `runtime/evidence_grammar_runtime_contract_v1_0.md`
- `runtime/replay_assumption_runtime_contract_v1_0.md`
- `runtime/compound_claim_resolver_v1_0.md`
- `runtime/inference_engine_runtime_contract_v1_0.md`

These should map semantics to code paths in this repository.

### 5.3 New schemas

- `schemas/composition_policy.schema.json`
- `schemas/inference_witness.schema.json`
- `schemas/replay_assumption_manifest.schema.json`
- `schemas/verification_grammar.schema.json`

These should be machine-readable and referenced by both tests and runtime validation code.

### 5.4 New formal models

- `formal/lean4/DuotronicCoreMetaphysics.lean`
- `formal/lean4/DuotronicEvidenceSyntax.lean`
- `formal/tlaplus/NonCollapseAxioms.tla`

These should live alongside the existing formal model directories:

- `/home/runner/work/srnn_server/srnn_server/formal_models/lean4/`
- `/home/runner/work/srnn_server/srnn_server/formal_models/tlaplus/`

### 5.5 New validation suites

- `validation/evidence_language_acceptance_matrix_v1_0.md`
- `tests/evidence_language_conformance_suite_v1_0.md`
- `tests/deep_time_replay_test_v1_0.md`

In code terms, the actual executable coverage should likely become new pytest modules under:

- `/home/runner/work/srnn_server/srnn_server/tests/`

---

## 6. Core Python modules that must change

The most important implementation work is in Python runtime datamodels.

### 6.1 `srnn/duotronic/dbp_envelope.py`

#### Why it must change
Draft 5.2 explicitly treats the DBP envelope as a visible, structured carrier of evidence semantics, not merely a transport wrapper.

#### Required changes
- Extend the envelope to represent evidence-language metadata more explicitly.
- Add fields or nested sections for:
  - syntax metadata,
  - pragmatic metadata,
  - replay assumptions,
  - verification grammar references,
  - non-collapse classification markers.
- Preserve backwards compatibility with current envelope readers.
- Decide whether to:
  - expand the current flat envelope structure, or
  - introduce a nested `evidence_section` / `replay_section` / `pragmatic_section`.

#### Important constraint
Do not break:
- `wrap_object()`
- `decode_payload()`
- current `canonical_identity_hash` / `payload_hash` semantics

#### Follow-up work
- Update all callers that assume the current minimal shape.
- Add round-trip tests for new envelope fields.

### 6.2 `srnn/duotronic/policy_engine.py`

#### Why it must change
Draft 5.2 makes policy responsible not just for allow/deny, but for:

- composition approval,
- inference approval,
- pragmatic force handling,
- authority delegation verification,
- and non-collapse enforcement.

#### Required changes
- Introduce new rule concepts:
  - `CompositionPolicy`
  - `PragmaticConstraint`
  - `NonCollapseConstraint`
  - inference authorization rules
- Extend `PolicyDecisionRequest` to carry:
  - illocutionary force markers,
  - intended audience,
  - minimum interpretation assumptions,
  - composition/inference context,
  - delegation-chain reference,
  - deep-time replay intent.
- Extend `PolicyDecision` to capture:
  - force indicator,
  - pragmatic rationale,
  - composition/inference approval basis,
  - replay-assumption obligations.
- Add explicit evaluation paths for:
  - compound claim creation,
  - inference witness creation,
  - temporal scope extension,
  - delegated authority claims.

#### Important constraint
Draft 5.2 must preserve fail-closed behavior:
- missing pragmatic context should not silently upgrade authority
- missing replay assumptions should block deep-time claims
- missing non-collapse guarantees should deny promotion where required

### 6.3 `srnn/duotronic/replay_package.py`

#### Why it must change
Draft 5.2 changes replay from “artifact verification package” into “self-describing replay language package.”

#### Required changes
- Add `ReplayAssumptionManifest` support.
- Add `VerificationGrammar` support.
- Add optional `ReplaySign` support for iconic/indexical markers.
- Distinguish:
  - normal replay package,
  - deep-time replay package.
- Extend verification so a package can be checked using:
  - assumptions,
  - grammar,
  - DBP envelope structure,
  - without relying on external docs.

#### New dataclasses likely needed
- `ReplayAssumption`
- `ReplayAssumptionManifest`
- `VerificationGrammar`
- `ReplaySign`
- `ReplayExtensionWitness`

#### Important constraint
Current `ReplayPackage` callers and tests are lightweight. Upgrading this module will require coordinated changes to:
- `api/routes/duotronic_v2.py`
- `srnn/duotronic/admin_cli.py`
- any replay verification helpers
- tier-2 conformance tests

### 6.4 `srnn/duotronic/math_canon.py`

#### Why it must change
Draft 5.2 introduces explicit evidence syntax and no-collapse semantics across claim composition and inference.

#### Required changes
- Keep current math claim lifecycle.
- Add support for:
  - atomic claim identity class,
  - compound claims,
  - inference relationships,
  - temporal scope witnesses,
  - explicit chain transition witnesses.
- Represent compositional relationships without weakening the current rule that theorem status cannot come from computation alone.
- Add schema-level or runtime-level guards so forbidden transitions remain impossible.

#### Likely new dataclasses
- `CompoundClaimWitness`
- `InferenceWitness`
- `TemporalScopeWitness`
- `AuthorityDelegationChain`
- enriched `MathClaimStatusTransition`

#### Important constraint
Existing semantics in `MathClaimStatus` and `can_advance_to()` should remain the non-collapse anchor, not be bypassed by compound-claim logic.

### 6.5 `srnn/duotronic/proof_witness.py`

#### Why it must change
Draft 5.2 formalizes the distinction between:
- proof,
- computational support,
- conjecture,
- theorem,
- inference.

#### Required changes
- Ensure `InferenceWitness` cannot masquerade as `ProofWitness`.
- Add explicit relationships from inference witnesses to proof witnesses.
- Support inference rules that may propose promotion but never self-promote to theorem.
- Allow proof witnesses to participate as premises in compound claims or implication claims.

### 6.6 `srnn/cognition/truth_observer_registry.py`

#### Why it must change
Draft 5.2 specifically requires pragmatic context extension of observer authority.

#### Required changes
- Extend observer authority metadata with:
  - pragmatic context,
  - audience scope,
  - channel authority,
  - declared force capabilities,
  - replay assumption coverage.
- Add data structures corresponding to:
  - `TruthObserverActivationAuthority` expansion
  - pragmatic applicability records
  - delegation-aware observer authority

#### Important constraint
The current `TruthObserverActivationProfile` is flat and capability-oriented. Draft 5.2 will require it to become partly semantic/policy aware.

### 6.7 `srnn/cognition/nla_policy_enforcement.py`

#### Why it must change
Draft 5.2 introduces new no-collapse rules directly relevant to NLA:
- self-trained must never collapse into authoritative,
- audit-only must never escalate by repetition,
- explanation must not be confused with fact,
- observation must not be confused with proof.

#### Required changes
- Add explicit Draft 5.2 non-collapse checks.
- Add pragmatic-mode checks for NLA outputs.
- Ensure self-training witnesses cannot acquire authoritative force unless all layered checks pass.
- Extend enforcement messages so the blocked reason is evidence-language aware.

### 6.8 `srnn/cognition/nla_training_witness.py`

#### Why it must change
Current promotion gates are Draft 5.1-style authority gates. Draft 5.2 requires those gates to be described and enforced in the new language of evidence.

#### Required changes
- Add linkage from each promotion event to:
  - pragmatic context,
  - replay assumptions,
  - non-collapse classification,
  - inference/proposal force markers.
- Ensure every state transition can carry a formal witness rather than only an internal gate result.
- Add a stronger distinction between:
  - measured fidelity,
  - accepted-for-audit status,
  - release candidacy,
  - authoritative deployment.

### 6.9 `srnn/cognition/nla_release_evidence_bundle.py`

#### Why it must change
Release bundles need to become self-describing enough for Draft 5.2 replay.

#### Required changes
- Add replay assumption manifest inclusion.
- Add verification grammar inclusion.
- Add optional replay signs for deep-time packages.
- Distinguish “bundle is complete for release review” from “bundle is interpretable across deep time.”

### 6.10 `api/routes/duotronic_v2.py`

#### Why it must change
The current routes expose basic policy, replay, interpreter, Langlands, proof, and admin flows. Draft 5.2 will require first-class evidence-language APIs.

#### Required changes
- Add endpoints for:
  - compound claim submission
  - inference witness creation
  - authority delegation chain registration
  - replay assumption manifest creation and retrieval
  - verification grammar registration and validation
  - temporal scope extension requests
  - deep-time replay verification
- Upgrade existing policy and replay endpoints so they understand the new fields.
- Fix current replay route drift so the route shape matches the actual `ReplayPackage` model before layering Draft 5.2 on top.

#### Important note
The current replay endpoints around `/replay/packages` look partially stubbed and should be normalized before deeper changes.

---

## 7. New modules that should likely be added

Draft 5.2 is large enough that it should not all be forced into existing files.

Recommended new Python modules under `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/`:

- `evidence_syntax.py`
  - claim grammar objects
  - operator definitions
  - formation validation

- `compound_claims.py`
  - compound claim assembly
  - compatibility checking
  - evidence bundle union logic

- `inference_engine.py`
  - evidence-preserving inference rules
  - inference witness generation
  - temporal propagation

- `pragmatics.py`
  - force indicators
  - audience declarations
  - addressivity
  - delegated authority chain validation

- `replay_assumptions.py`
  - replay assumption manifest structures
  - manifest validation

- `verification_grammar.py`
  - grammar definition
  - deterministic interpreter/validator

- `non_collapse.py`
  - primitive-state definitions
  - exclusion matrix
  - forbidden transition helpers

- `replay_signs.py`
  - optional generation of iconic/indexical replay signs

Recommended new support modules under `/home/runner/work/srnn_server/srnn_server/srnn/cognition/`:

- `evidence_runtime.py`
  - cognition-facing helpers for emitting formal evidence objects

- `pragmatic_authority.py`
  - observer/runtime pragmatic context helpers

---

## 8. Persistence and migration changes

Draft 5.2 is not only in-memory. It needs durable storage.

### 8.1 New tables likely required

The exact database backend varies in this repo, but the following logical tables are needed:

- `srnn_composition_policies`
- `srnn_compound_claim_witnesses`
- `srnn_inference_witnesses`
- `srnn_temporal_scope_witnesses`
- `srnn_authority_delegation_chains`
- `srnn_replay_assumption_manifests`
- `srnn_verification_grammars`
- `srnn_replay_signs`
- `srnn_non_collapse_events` or equivalent audit table
- `srnn_claim_operator_edges` for DAG-style claim relationships

### 8.2 Existing tables that likely need expansion

- `srnn_nla_training_witnesses`
- `srnn_nla_promotion_audit_trail`
- `srnn_nla_release_evidence_bundles`
- `srnn_truth_observer_registry`

Potential added columns:
- pragmatic context JSON
- force indicator
- replay assumption manifest ref
- verification grammar ref
- non-collapse class
- audience declaration
- deep-time survival class

### 8.3 Migration files

Draft 5.2 should use additive migrations under the repository’s existing DB migration area.

Expected work:
- add new migrations for new tables
- add indexes on:
  - claim refs,
  - policy decision refs,
  - replay identity refs,
  - delegation-chain refs,
  - canonical identity hashes
- preserve old readers through null-default columns or compatibility views

---

## 9. Schema and validation changes

Draft 5.2 needs schema-level enforcement, not only Python checks.

### 9.1 New JSON schemas

The following are mandatory from the specification:

- `composition_policy.schema.json`
- `inference_witness.schema.json`
- `replay_assumption_manifest.schema.json`
- `verification_grammar.schema.json`

### 9.2 Additional schemas that should also exist

To avoid ambiguity, Draft 5.2 should also define:

- `compound_claim_witness.schema.json`
- `temporal_scope_witness.schema.json`
- `authority_delegation_chain.schema.json`
- `replay_sign.schema.json`
- `non_collapse_state.schema.json`

### 9.3 Schema-level non-collapse enforcement

Draft 5.2 explicitly expects schema locks on forbidden transitions. In practice this should mean:

- required state markers for primitive categories
- mutually exclusive fields where appropriate
- explicit prohibition on representing proof and computational evidence as the same semantic class
- explicit prohibition on treating absent, null, empty, unknown, invalid, and zero as interchangeable encodings

Where JSON Schema cannot express the full rule, the remaining rule should be enforced in Python validation plus tests.

---

## 10. Syntax of evidence workstream

This is the first pillar and likely the hardest to get right.

### 10.1 Required runtime capabilities

The system must be able to represent:

- atomic claims,
- conjunctions,
- disjunctions,
- implications,
- temporal claims,
- claim DAGs,
- operator-specific formation rules.

### 10.2 Concrete repository changes

- Add a grammar datamodel in `srnn/duotronic/evidence_syntax.py`
- Add composition validators that check:
  - `authority_scope` compatibility
  - `runtime_mode` compatibility
  - evidence-bundle merge validity
  - policy approval requirement
- Add operator-specific rule checks:
  - `And`
  - `Or`
  - `Implies`
  - `TemporalSince`

### 10.3 Changes to current code assumptions

Right now many claims in the repo are effectively atomic. Draft 5.2 will require:

- references between claims to be first-class,
- witness status transitions to become graph-aware,
- policy to understand composition as an action kind,
- replay to preserve premise/conclusion structure.

### 10.4 Tests required

- compound-claim formation passes only when scopes are compatible
- incompatible scopes fail closed
- composed claims produce new witness IDs and policy decision refs
- conjunction elimination does not mutate premise claims
- modus ponens yields proposal/inference witness, not automatic theorem
- temporal propagation requires replay evidence

---

## 11. Pragmatics of authority workstream

This pillar is about the force of a claim, not just its content.

### 11.1 Required runtime capabilities

The system must represent:

- who can say something,
- in which scope,
- on which channel,
- to which audience,
- with what illocutionary force,
- under what delegation chain,
- and whether repetition changes nothing.

### 11.2 Concrete repository changes

- Extend policy request and observer authority models with:
  - `pragmatic_context`
  - `intended_audience`
  - `minimum_assumptions`
  - `force_indicator`
  - `channel_authority`
  - `delegation_chain_ref`

- Add a delegated authority chain structure and validator.
- Add a `PragmaticConstraint` rule class inside policy evaluation.
- Record pragmatic effectiveness in runtime applicability or witness records.

### 11.3 Current modules directly affected

- `srnn/duotronic/policy_engine.py`
- `srnn/cognition/truth_observer_registry.py`
- `srnn/cognition/nla_policy_enforcement.py`
- any witness emission path that currently stores `authority_scope` and `runtime_mode` only

### 11.4 Tests required

- `audit_only` outputs cannot escalate by repetition
- missing audience declaration blocks deep-time-intended claims
- force markers are preserved in policy decisions
- delegation chains cannot exceed authorized scope
- channel authority cannot override semantic or proof constraints

---

## 12. Semiotics of replay workstream

This pillar upgrades replay into a self-describing verification system.

### 12.1 Required runtime capabilities

The runtime must support:

- replay assumption manifests,
- verification grammars,
- optional replay signs,
- future-reader verification without external docs.

### 12.2 Concrete repository changes

- Extend `ReplayPackage` so it can include:
  - replay assumptions
  - verification grammar
  - replay signs
  - deep-time conformance marker

- Add a deterministic verification-grammar interpreter or validator.
- Add package builders that can emit minimal replay packages and deep-time replay packages.
- Add API routes for storing and verifying these structures.

### 12.3 Important design decision

Do **not** hide the verification grammar inside prose-only docs. It must exist as machine-checked structured data, with optional human-facing Markdown around it.

### 12.4 Tests required

- a claim can be verified from package + assumptions + grammar alone
- a missing required assumption causes failure
- a package marked deep-time-ready fails if replay signs are required but absent
- manifest hash remains stable when semantically unchanged
- verification grammar execution is deterministic

---

## 13. Metaphysics of non-collapse workstream

This pillar is the most philosophically explicit but should become highly practical in code.

### 13.1 Primitive distinctions that must be modeled

At minimum:

- zero
- absence
- unknown
- invalid
- empty
- null
- computational_evidence
- theorem
- conjectural
- self_trained
- authoritative

The exact internal type system can differ, but these categories must not be silently merged.

### 13.2 Concrete repository changes

- Add a central primitive-state model under `srnn/duotronic/non_collapse.py`
- Add reusable validators for:
  - storage values,
  - claim transitions,
  - NLA authority transitions,
  - replay interpretation,
  - proof/computation separation

- Add `NonCollapseConstraint` to the policy engine.
- Add no-collapse checks to:
  - `math_canon.py`
  - `proof_witness.py`
  - `nla_policy_enforcement.py`
  - replay verification logic

### 13.3 Formal model work

Add Lean/TLA+ models that prove or at least specify:

- pairwise mutual exclusion where intended
- forbidden transition rules
- external witness requirement for trust-state changes
- layered verification requirement

### 13.4 Tests required

- attempted collapse of `computational_evidence -> theorem` without proof witness fails hard
- attempted collapse of `self_trained -> authoritative` without full gate path fails hard
- absent/null/empty/zero are preserved across serialization
- invalid cannot be reinterpreted as unknown
- theorem cannot be inferred from replayed computation alone

---

## 14. API work required

The Draft 5.2 implementation will need new or expanded API surfaces.

### 14.1 Existing routes to upgrade

`/home/runner/work/srnn_server/srnn_server/api/routes/duotronic_v2.py`

Upgrade:
- `/policy/decide`
- `/replay/packages`
- `/replay/verify/{package_id}`
- `/interpreter/run`

because these flows will need new evidence-language payloads.

### 14.2 New endpoints likely needed

- `POST /evidence/claims/compound`
- `POST /evidence/inferences`
- `POST /evidence/temporal-scope/extend`
- `POST /authority/delegations`
- `POST /replay/assumptions`
- `POST /replay/verification-grammars`
- `POST /replay/deep-time/verify`
- `GET /evidence/claims/{claim_id}/graph`
- `GET /authority/delegations/{chain_id}`

### 14.3 API contract rules

Every new endpoint should return:

- DBP envelope refs where applicable
- policy decision refs
- replay identity refs
- explicit witness IDs
- no-collapse classification where relevant

---

## 15. MCP, admin, and tooling work

Draft 5.2 will be difficult to operate without tooling.

### 15.1 MCP/admin tooling likely needed

The repo already has admin and MCP-adjacent surfaces. Draft 5.2 should add tools for:

- compound claim inspection
- inference DAG browsing
- replay assumption manifest generation
- verification grammar linting
- authority delegation inspection
- non-collapse audit reporting
- deep-time replay test execution

### 15.2 Likely affected modules

- `srnn/duotronic/admin_cli.py`
- `srnn/agent_lab/_mcp_tools.py`
- `srnn/meta_objects/api/mcp_tools.py`
- any future Duotronic MCP tool registry

### 15.3 Important implementation note

If tooling is omitted, future implementors will be forced to debug Draft 5.2 through raw JSON and DB rows, which will slow adoption and increase semantic drift.

---

## 16. Formal models and proof artifacts

The repository already has a formal-model direction; Draft 5.2 should extend it.

### 16.1 Lean 4

New files should likely be added under:

- `/home/runner/work/srnn_server/srnn_server/formal_models/lean4/`

Needed topics:
- primitive-state distinctions
- non-collapse axioms
- evidence syntax formation rules
- preservation of distinct statuses through transitions

### 16.2 TLA+

New files should likely be added under:

- `/home/runner/work/srnn_server/srnn_server/formal_models/tlaplus/`

Needed topics:
- claim graph state transitions
- delegation chain boundedness
- inference witness creation rules
- layered verification requirements

### 16.3 Scope discipline

The formal files do not need to prove the whole repository correct. They do need to formalize the parts Draft 5.2 declares as non-negotiable.

---

## 17. Test plan for Draft 5.2

Draft 5.2 should extend, not replace, the existing conformance approach.

### 17.1 Existing test files that will likely need updates

- `/home/runner/work/srnn_server/srnn_server/tests/test_duotronic_v1_6_conformance.py`
- `/home/runner/work/srnn_server/srnn_server/tests/test_duotronic_v1_6_tier2_conformance.py`
- `/home/runner/work/srnn_server/srnn_server/tests/test_nla_implementation.py`
- `/home/runner/work/srnn_server/srnn_server/tests/test_nla_integration_contract.py`
- any policy and witness lifecycle tests touching authority transitions

### 17.2 New test modules likely needed

- `tests/test_duotronic_evidence_syntax.py`
- `tests/test_duotronic_compound_claims.py`
- `tests/test_duotronic_inference_witnesses.py`
- `tests/test_duotronic_pragmatic_constraints.py`
- `tests/test_duotronic_replay_assumptions.py`
- `tests/test_duotronic_verification_grammar.py`
- `tests/test_duotronic_non_collapse.py`
- `tests/test_deep_time_replay.py`

### 17.3 Minimum acceptance coverage

The new tests should prove:

- claim composition rules are enforced
- inference is evidence-preserving and witness-generating
- policy treats pragmatic force separately from semantic content
- replay packages are self-describing
- non-collapse rules are hard failures, not warnings
- NLA and math promotion logic still respect Draft 5.1 safety boundaries

---

## 18. Migration and compatibility strategy

Draft 5.2 should be introduced without breaking Draft 5.1 behavior abruptly.

### 18.1 Backward compatibility rules

- Existing Draft 5.1 witnesses must remain parseable.
- Existing DBP envelopes must remain decodable.
- Existing replay packages must remain verifiable in legacy mode.
- Existing NLA promotion flows must continue to function, then gain Draft 5.2 annotations.

### 18.2 Recommended rollout phases

#### Phase A — corpus and schema groundwork
- write new Draft 5.2 docs
- define schemas
- define formal model stubs

#### Phase B — datamodel introduction
- add new Python dataclasses
- add validators
- keep features dormant or optional

#### Phase C — policy and replay upgrade
- upgrade policy engine and replay package
- add API fields and routes

#### Phase D — persistence and tests
- add migrations
- add persistence
- add conformance tests

#### Phase E — full runtime integration
- wire NLA, math, observer, and admin/tooling paths

#### Phase F — deep-time replay hardening
- enforce replay assumptions
- enable verification grammar execution
- add deep-time packages and tests

---

## 19. Risks and likely implementation traps

### 19.1 Overloading existing dataclasses

Do not stuff all Draft 5.2 semantics into existing classes without introducing clearer substructures. That will create flat, ambiguous objects and make replay harder.

### 19.2 Confusing policy approval with proof

Draft 5.2 increases policy’s role, but policy still does not make something true. This distinction must remain hard and visible.

### 19.3 Allowing inference to bypass status ladders

Inference witnesses may justify proposals, but they must not silently skip:
- proof-authority requirements
- theorem gates
- replay requirements

### 19.4 Treating replay assumptions as comments

Replay assumptions must be structured, versioned, validated data, not prose blobs.

### 19.5 Failing to keep no-collapse semantics centralized

If non-collapse rules are scattered ad hoc through the codebase, later changes will drift. They need one central reusable implementation.

### 19.6 Breaking current route/test assumptions

Some current Duotronic API code appears lighter or more stub-like than the datamodels beneath it. Draft 5.2 should normalize these mismatches early.

---

## 20. File-by-file implementation map

### Existing files to modify

- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/dbp_envelope.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/policy_engine.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/replay_package.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/math_canon.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/proof_witness.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/cognition/truth_observer_registry.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/cognition/nla_policy_enforcement.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/cognition/nla_training_witness.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/cognition/nla_release_evidence_bundle.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/cognition/nla_persistence.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/cognition/wgrnn_memory_service.py`
- `/home/runner/work/srnn_server/srnn_server/api/routes/duotronic_v2.py`

### New files or modules likely to add

- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/evidence_syntax.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/compound_claims.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/inference_engine.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/pragmatics.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/replay_assumptions.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/verification_grammar.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/non_collapse.py`
- `/home/runner/work/srnn_server/srnn_server/srnn/duotronic/replay_signs.py`
- formal model files under `/home/runner/work/srnn_server/srnn_server/formal_models/`
- new pytest files under `/home/runner/work/srnn_server/srnn_server/tests/`

### New documentation/corpus files likely to add

- Draft 5.2 authority, runtime, schema, formal, validation, and rollout docs listed earlier in this guide

---

## 21. Recommended execution order for future implementation

When ChatGPT 5.5 or another implementor carries out Draft 5.2, the safest order is:

1. Normalize Draft 5.1 runtime/document naming and route-model mismatches
2. Add Draft 5.2 normative docs and JSON schemas
3. Add new dataclasses for syntax/pragmatics/replay/non-collapse
4. Add central validators
5. Upgrade policy engine
6. Upgrade replay package
7. Upgrade math/proof/NLA integration points
8. Add persistence and migrations
9. Add and expand tests
10. Add formal-model files
11. Add admin/MCP/deep-time tooling

This sequence keeps the repository testable throughout the migration.

---

## 22. Final summary

Draft 5.2 will require substantial but coherent changes. The repository already contains most of the conceptual substrate Draft 5.2 needs:

- DBP envelopes,
- policy decisions,
- replay packages,
- math claim lifecycles,
- proof witnesses,
- truth observer capability records,
- NLA authority gates,
- and conformance tests.

What Draft 5.2 adds is the missing unifying layer:

- a formal syntax for claim composition,
- a pragmatic model for authority and force,
- a self-describing replay language,
- and an explicit metaphysics of non-collapse enforced across runtime, policy, storage, and formal models.

The implementation should therefore be treated as a **unification and formalization program**, not a bolt-on feature.

If implemented carefully, Draft 5.2 will make SRNN server and Duotronics much more internally consistent, much easier to audit, and much more suitable for long-horizon verified replay.

## Draft 5.2 completion-candidate hardening addendum

The completed corpus adds the missing operational detail required for implementation review. Active Draft 5.2 runtimes MUST preserve the following objects as first-class records and MUST NOT collapse them into prose-only metadata:

- `evidence_claim/v1`
- `composition_policy/v1`
- `compound_claim_witness/v1`
- `inference_witness/v1`
- `claim_status_transition/v1`
- `pragmatic_context/v1`
- `policy_decision_evidence_extension/v1`
- `authority_delegation_chain/v1`
- `non_collapse_state/v1`
- `non_collapse_transition/v1`
- `replay_assumption_manifest/v1`
- `replay_sign/v1`
- `verification_grammar/v1`
- `verification_result/v1`

A runtime that cannot emit the required witness object MUST deny, defer, or escalate the operation rather than silently promoting authority, truth status, replay status, model status, or proof status.
