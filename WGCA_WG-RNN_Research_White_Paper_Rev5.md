# Witness-Gated Cognitive Architecture (WGCA)
## A Technical White Paper on Witness-Governed Recurrent Cognition, Durable Memory, Probability Steering, and Persistent Machine Systems

**Status:** Technical research white paper — pre-validation with independently executed contract, formal-model, and regression evidence  
**Date:** 2026-09-22  
**Revision:** 5 — active Duotronics 5.3.18 validation, strict Lean/TLC execution, pinned-runtime regression coverage, and immutable-corpus harness separation  
**System:** Xavi / WGCA with WG-RNN recurrent core  
**Primary implementation domains:** `xavi-memory`, `xavi-runtime`, `router`  
**Author:** Hugh Armstrong / TBI Contracting Inc 

---

## Abstract

This paper presents the architecture, formal governance model, training procedure, experimental protocol, implementation roadmap, and falsifiability criteria for the **Witness-Gated Cognitive Architecture (WGCA)** implemented within the Xavi system. The project name **WG-RNN** is retained for the recurrent neural core and for compatibility with the existing codebase, but the complete architecture is not merely a new recurrent cell. It is a witness-governed cognitive system in which recurrent computation is one component inside a larger authority, memory, routing, evidence, and learning framework.

The central systems claim is deliberately narrower than a claim of new mathematics. WGCA synthesizes established ideas from recurrent and associative memory, information bottlenecks, predictive processing, stability/plasticity research, continual learning, event sourcing, model registries, distributed leases, access-control decision points, and provenance systems. Its proposed contribution is the **integration of those mechanisms under a single explicit authority boundary**: neural computation may propose state, memory, routing, or learning changes, but it may not unilaterally make those changes authoritative.

Five architectural separations define the system:

1. **active recurrent state is not the durable memory store;**
2. **observation is not epistemic promotion;**
3. **retrieval is not truth;**
4. **gradient-based learning is not checkpoint authority;**
5. **distributed computation is not distributed commit authority.**

A formal witness model is introduced in which typed witness assertions are issued inside bounded trust domains; policies are evaluated by a Policy Decision Point (PDP); decisions are enforced by a Policy Enforcement Point (PEP); authority is granted by scoped, time-bounded leases and credentials; revocation invalidates future authority without rewriting history; appeal creates a new linked decision rather than erasing the old one; and delegation is a finite directed acyclic graph rooted in an explicitly configured governance root. This prevents “witness” from becoming an undefined synonym for approval and prevents an infinite regress of witnesses witnessing witnesses.

The paper also specifies how learning proceeds even though the external authority gates are intentionally non-differentiable. Gradients flow only through differentiable neural objectives computed on admitted training data. External gates determine **which trajectories are eligible for learning, how they are weighted, and whether a resulting candidate checkpoint may be promoted**; they are not inserted into backpropagation as if they were differentiable neurons. For discrete routing or selection decisions whose effects must themselves be learned, policy-gradient estimators such as REINFORCE or PPO-style surrogate optimization can be used, while witness decisions remain external constraints. Eligibility traces and graph dependencies assign delayed credit, but authoritative parameter promotion remains a separate witnessed transaction.

A second research hypothesis concerns **semantic probability steering**. Rather than requiring the recurrent core to communicate only through autoregressive text, WGCA can alter the probability distribution over rich semantic objects such as images, memes, music, video, documents, graph fragments, tools, models, routes, or actions. This is experimentally testable with paired control and steered distributions under identical candidate sets and pseudorandom seeds. The paper therefore defines a minimal media-steering experiment using preregistered targets, paired seeds, state-shuffle ablations, witness-mismatch controls, blinded independent observers, effect sizes, confidence intervals, permutation tests, multiple-comparison control, and prospective power analysis.

The complete stack is intentionally ambitious. Accordingly, the paper specifies a phased implementation program beginning with a minimal single-node witness kernel and fixed-corpus steering experiment before graph hypermemory, multimodel faculty routing, continual checkpoint promotion, cluster leases, and offline-first replication are added. Each phase has explicit success and stop criteria.

Finally, the paper commits to reporting negative results. Failure to observe steering, witness bypasses, unacceptable graph cost, observer dependence, unstable recurrent training, and authority failures are research outcomes rather than implementation embarrassments. A credible WGCA research program must make those failure conditions visible.

## Current empirical status

Revision 5 separates **three evidence domains** and does not treat any one of them as proof of the others.

### A. Active standalone Duotronics witness-contract package

The independent Duotronics repository remains separate from Xavi/WGCA implementation evidence. The active package tested for this revision is:

```text
/datastore2/duotronics-whitepaper-v4/Duotronics-main/
  build_docs/witness_contract/v1.6 - Draft 5.3.18
```

Its own validator was run against the canonical, manifest-closed corpus after removing only generated/untracked build artifacts. Fresh result:

```text
contract_version: v1.6-draft-5.3.18
status: pass
failure_count: 0
production_authority_activated: false
```

The package therefore has a clean current corpus-integrity and schema/contract validation result. This is independent conformance evidence, not a claim that WGCA implements the Duotronics contract in full.

### B. Strict formal-tool execution

The 5.3.18 Lean extension and inherited strict build were executed with the exact installed `leanprover/lean4:v4.29.1` toolchain. The exact direct build completed all 17 required Lake jobs and compiled the additional `AuthorityDomainV5318.lean` extension.

Strict TLA+ model checking was then executed with TLC 2.19 from an external harness-level tool path so the manifest-closed contract corpus remained unchanged. All 12 declared modules returned code 0. The largest checked state spaces included:

```text
TaskDelegationAndPolicyCoreSpec   41,179 distinct states, depth 10
LogicalObserverKernel            12,689 distinct states, depth 9
AuthorityDomainV5318              4,097 distinct states, depth 14
```

Across the full 12-module run, no model-checking error was reported. This is materially stronger evidence than a static TLA syntax pass, but it remains bounded model checking of the declared finite configurations, not a universal proof of all implementations or all parameterizations.

### C. Regression and harness evidence

The standalone repository-wide acceptance and nightly harness were executed in an isolated Python environment with the declared research dependencies present:

```text
acceptance: 246 passed, 0 skipped
nightly extended fuzz: 3 passed, 243 deselected
nightly status: green
```

The active 5.3.18 package-local Python suite initially exposed a reproducibility mismatch because the environment contained `pqcrypto 1.0.0`, while the package explicitly pins:

```text
cryptography==46.0.0
pqcrypto==0.3.4
pycryptodomex==3.23.0
```

After restoring those declared versions, the suite reduced from 178 failures to three historical test-fixture incompatibilities. Those three tests were shown to be retained 5.3.17 bytes and therefore could not be modified inside the canonical 5.3.18 corpus without breaking parent-manifest continuity. The canonical files were restored byte-for-byte to their retained 5.3.17 IDs.

A separate external harness runner was then added under:

```text
harness/bin/tools/run_witness_5318_regression.py
```

It validates the pristine canonical 5.3.18 corpus first, copies it to a temporary workspace, applies only version-aware compatibility changes to the stale historical fixtures in that temporary copy, and runs the package-local regression suite there. Fresh result:

```text
canonical 5.3.18 validation: PASS, failure_count 0
package regression: 329 passed, 6 skipped, 87 subtests passed
return code: 0
```

The six skips are explicit historical regeneration tests from Drafts 5.3.14, 5.3.15, and 5.3.16 marked as superseded by the whole-corpus 5.3.17 registry generator. They are not missing dependencies or silent test omissions.

### D. Xavi/WGCA implementation evidence

Xavi Memory remains a separate implementation domain. The focused current memory-core suite previously produced:

```text
11 passed in 1.31s
```

The previously reported broad-suite `pypdf` collection failure remains a separate Xavi test-environment issue unless and until rerun. No claim in this revision converts Duotronics contract success into WGCA implementation conformance.

The evidence rule remains:

```text
independent contract validation != WGCA implementation conformance
strict Lean/TLC execution != empirical cognitive validation
regression pass != proof of real-world safety
focused WGCA tests != full WGCA validation
```

# 1. Scope, Naming, and Terminology

The complete Xavi design is referred to in this paper as the **Witness-Gated Cognitive Architecture (WGCA)**.

The existing project and codebase use the name **WG-RNN**. In the revised terminology:

- **WGCA** denotes the complete cognitive architecture;
- **WG-RNN core** denotes the differentiable recurrent neural component inside that architecture;
- existing filesystem paths, service names, APIs, and compatibility identifiers may continue to use `wg-rnn`.

This naming distinction is important because the central contribution is not a novel scalar gate inserted into an RNN cell. The principal design claim concerns the systems boundary around recurrent computation.

A conventional recurrent system may compute:

\[
h_t = F_\theta(h_{t-1},x_t,c_t)
\]

WGCA instead distinguishes the neural proposal from the authoritative commit:

\[
(\hat h_t,r_t)=F_\theta(h_{t-1},x_t,c_t)
\]

followed by:

\[
d_t=\operatorname{PDP}(q_t,E_t,P_t)
\]

and:

\[
h_t=
\begin{cases}
\hat h_t,&d_t=\text{PERMIT}\\
h_{t-1},&d_t\in\{\text{DENY},\text{QUARANTINE},\text{INDETERMINATE}\}
\end{cases}
\]

where the policy decision is external to the recurrent core.

Throughout this paper:

- **WGCA** — the full witness-governed cognitive system.
- **WG-RNN core** — the learned recurrent transition model.
- **Recurrent state** — bounded active hidden state carried between processing steps.
- **Durable memory** — persistent records, graph objects, historical anchors, provenance, predictions, outcomes, and reconsolidations.
- **Witness assertion** — a typed, attributable statement about evidence, state, authority, or outcome.
- **Witness contract** — a finite policy specifying what classes and combinations of witness assertions are sufficient for a particular decision.
- **Trust domain** — an administratively defined class of issuers whose assertions are evaluated under common policy.
- **Authority lease** — a time-bounded capability allowing a named principal to perform an authoritative commit within a defined scope.
- **PDP (Policy Decision Point)** — the component that evaluates a request and its evidence against the applicable witness contract.
- **PEP (Policy Enforcement Point)** — the component that enforces the PDP decision.
- **State gate** — the decision controlling whether a candidate recurrent state becomes authoritative.
- **Retention/trust gate** — the decision controlling durable epistemic promotion.
- **Learning gate** — the decision controlling admission of experience to learning and later promotion of candidate checkpoints.
- **Router** — model/service/resource routing and expert-fanout layer.
- **Runtime** — execution, service integration, process lifecycle, and authority-lease transport.
- **Observer** — a model, parser, sensor, tool, human, or other faculty that emits an attributable observation.
- **Evidence graph** — provenance-bearing graph of claims, events, relationships, contradictions, support, temporal structure, and witness lineage.
- **Probability steering** — a measurable change in a distribution over candidate semantic objects or actions.
- **Semantic object** — a selectable unit such as text, image, meme, song, video, document, graph fragment, model response, route, action, or compound object.

---

# 2. The Core Problem: Storage Is Not the Same as Memory

A central premise of this work is that memory should not be modeled as a photograph, media file, or byte-for-byte archive of prior experience.

That premise maps directly to the current WGCA architecture and its WG-RNN recurrent core.

A cognitive system does not need to preserve every sensory input at full fidelity in order to preserve continuity. Instead, it can retain:

1. selected high-fidelity recent events;
2. a bounded recurrent state that summarizes active context;
3. durable graph relationships and witnessed semantic records;
4. historical anchor states;
5. provenance linking present interpretation to past evidence;
6. learned parameters that encode generalized regularities rather than explicit episodic copies.

This leads to the first major thesis:

> **Memory is better modeled as a hierarchy of retained constraints on future state transitions than as a flat archive of past sensory frames.**

A remembered event influences what the system will consider relevant, likely, surprising, contradictory, or action-worthy later. In that sense, memory behaves like a filter.

However, “filter” must be defined carefully. It does not mean the system stores nothing. It means the system's remembered past is expressed through **selective retention and future bias**.

A recurrent hidden state can be treated as a dynamically updated function:

\[
h_t = F_\theta(h_{t-1}, x_t, c_t)
\]

where:

- \(h_{t-1}\) is the prior active state;
- \(x_t\) is the current observation;
- \(c_t\) is retrieved context, graph evidence, or routed expert context;
- \(F_\theta\) is the learned transition function.

But in WG-RNN this is not sufficient. The system computes a candidate:

\[
(\hat h_t, r_t) = F_\theta(h_{t-1}, x_t, c_t)
\]

where \(r_t\) is a neural or numerical receipt.

The candidate is not automatically authoritative. A witness-governed commit decision follows:

\[
h_t =
\begin{cases}
\hat h_t, & \text{if StateGate}(e_t,\hat h_t,w_t,\ell_t,q_t)=\text{accept}\\
h_{t-1}, & \text{otherwise}
\end{cases}
\]

where:

- \(e_t\) is the event identity;
- \(w_t\) is witness evidence;
- \(\ell_t\) is the authority lease;
- \(q_t\) is state-health/commit evidence.

The distinction is fundamental. **The neural cell proposes. The witness authority disposes.**

---

# 3. Memory as a Compressed Trajectory of Choice

A central WG-RNN working definition is that memory can be represented as a **compressed trajectory of state-dependent choices that biases future choices**, rather than as a complete stored audiovisual replica of prior experience.

This is useful as an engineering abstraction.

Consider an experience containing millions of sensory details. A practical cognitive system cannot make every detail equally influential forever. It must decide which structures matter.

A compressed memory therefore behaves like a set of constraints:

\[
M = \{a_1,a_2,\ldots,a_k,\; E,\; P,\; T,\; U\}
\]

where:

- \(a_i\) are selected anchors or features;
- \(E\) is evidence/provenance;
- \(P\) is a pattern of transitions or choices;
- \(T\) is temporal structure;
- \(U\) is uncertainty.

The point is not that the system literally stores “choices” only. Rather, it stores enough structure to **reconstruct relevant context and alter future inference**.

In Xavi Memory, this is now reflected by a four-tier model:

### 3.1 Reference memory

Protected definitions, active profiles, theorem/semantic registries, witness contracts, task identity, and other intentionally persistent invariants.

### 3.2 Recent memory

High-fidelity, exact event records preserved for a bounded recent interval. This tier exists specifically because recurrent compression can blur details.

### 3.3 Recurrent memory

The learned active state \(h_t \in \mathbb{R}^d\), currently beginning with a configurable dimension of 256.

The critical architectural rule is:

> **The recurrent vector is active context. It is not the storage-capacity ceiling.**

### 3.4 Historical memory

Selected audited recurrent-state anchors and durable semantic records, content-addressed and connected into the temporal meta-object graph.

This architecture avoids the false choice between “everything is stored in the neural vector” and “the neural vector is irrelevant.” Instead, the vector is the **live steering state**, while durable evidence remains externally addressable.

---

# 4. Formal Witness, Attestation, and Authority Semantics

The term **witness** is overloaded in ordinary language. WGCA therefore distinguishes:

- **attestation** — an attributable statement about a fact, measurement, identity, state, or outcome;
- **authority witness** — an attestation whose issuer is authorized to satisfy part of an authoritative decision contract;
- **epistemic evidence** — information relevant to whether a proposition is supported, contradicted, uncertain, or stale;
- **authority decision** — a policy result controlling whether a state transition, promotion, or checkpoint operation may occur.

A cryptographically valid attestation is not automatically an authority witness. An authority witness is not automatically epistemic truth.

## 4.1 Canonical decision request

Every authoritative decision is evaluated over a closed request tuple:

\[
Q=
(
principal,
action,
resource,
context,
policy\_bundle,
fact\_snapshot
)
\]

The canonical serialized form is content-addressed:

\[
d_Q=H(\operatorname{Canon}(Q))
\]

The canonicalization profile must fix:

- field ordering;
- Unicode normalization;
- numeric representation;
- timestamp representation;
- missing/null semantics;
- one-origin semantic identifiers;
- digest algorithm/version.

Audit replay is defined over this canonical snapshot, not over mutable live state.

## 4.2 Attestation structure

An attestation is:

\[
w=
(
id,
issuer,
issuer\_domain,
subject,
predicate,
value,
evidence\_refs,
scope,
valid\_from,
valid\_until,
nonce,
parent,
policy\_epoch,
signature
)
\]

Examples:

- `schema_valid`;
- `source_digest_matches`;
- `state_finite`;
- `parent_state_digest_matches`;
- `lease_holder_current`;
- `human_approved`;
- `observer_supports_claim`;
- `observer_refutes_claim`;
- `outcome_success`;
- `checkpoint_holdout_passed`.

## 4.3 Trust domains

Issuers belong to explicit domains:

\[
D=
\{
D_{crypto},
D_{runtime},
D_{policy},
D_{source},
D_{observer},
D_{outcome},
D_{human},
D_{external}
\}
\]

Domain membership is itself governed by signed configuration rooted in the deployment governance root.

No domain is presumed truthful merely by category. Policies state what each domain is allowed to attest and what combinations are required.

## 4.4 WGCA policy language

WGCA requires a small deterministic policy language, **WGCA-Policy/v1**.

The reference semantic model is intentionally close to mature authorization languages such as Cedar and Rego: declarative policies operate on a fixed request and fixed data snapshot, and authorization logic is separated from application logic [25,26].

A policy has:

```text
policy_id
schema_version
gate_class
effect = PERMIT | FORBID | QUARANTINE
principal_scope
action_scope
resource_scope
conditions[]
required_attestations[]
independence_constraints[]
valid_from
valid_until
policy_epoch
```

A condition may only use deterministic pure operators over the supplied snapshot:

```text
eq, neq
lt, lte, gt, gte
contains
in
all
any
not
digest_eq
count
count_distinct_domain
age_at_evaluation
is_resolved
```

No WGCA-Policy/v1 rule may perform network I/O, read ambient process state, call a model, read the current wall clock implicitly, or execute arbitrary code.

Time-dependent policy receives an explicit:

\[
t_{eval}
\]

inside `fact_snapshot`.

Therefore:

\[
\operatorname{Evaluate}(P,Q)
\]

is a pure function.

## 4.5 Policy combination and conflict resolution

For all authoritative gates, WGCA uses:

1. **explicit FORBID overrides all PERMITs**;
2. **QUARANTINE overrides PERMIT but not FORBID**;
3. **at least one matching PERMIT is required**;
4. **no matching PERMIT means DENY**;
5. **policy-evaluation error means INDETERMINATE**;
6. **INDETERMINATE fails closed for authoritative state/learning operations**.

For applicable policy set \(\mathcal P(Q)\):

\[
Decision(Q)=
\begin{cases}
DENY,&\exists p\in\mathcal P: p=FORBID\\
QUARANTINE,&\neg FORBID\land\exists p: p=QUARANTINE\\
PERMIT,&\neg FORBID\land\neg QUARANTINE\land\exists p: p=PERMIT\\
DENY,&\text{otherwise}
\end{cases}
\]

Policies are not resolved by mutable numeric priority. This avoids hidden “last rule wins” behavior.

Different gate classes do not compete. `state.commit`, `memory.promote`, and `checkpoint.promote` are separate actions with separate contracts.

## 4.6 Attestation sufficiency

For operation \(g\), sufficient evidence is defined only by its contract:

\[
W\models C_g
\]

A contract can require:

\[
count\_distinct\_domain(
W[predicate=\text{supports}]
)\ge k
\]

or require specific domains:

\[
D_{crypto}\land D_{runtime}\land D_{human}
\]

Self-corroboration can be forbidden:

\[
issuer(w_i)=producer(claim)
\Rightarrow
w_i\notin IndependentSupport
\]

The result authorizes an administrative state. It does not mathematically prove the underlying proposition true.

## 4.7 Credentials and delegation

An authority credential is:

\[
A=
(
principal,
roles,
scopes,
not\_before,
not\_after,
epoch,
delegator,
depth,
policy\_digest
)
\]

Delegation edge:

\[
u\rightarrow v
\]

is valid iff:

1. \(u\) currently possesses delegable authority;
2. child scope is a subset of parent scope;
3. child expiry does not exceed parent expiry;
4. child epoch equals the active governance epoch;
5. `child.depth = parent.depth + 1`;
6. `child.depth <= MAX_DELEGATION_DEPTH`;
7. \(v\) is not already an ancestor of \(u\);
8. the edge is signed by \(u\).

Cycle detection is therefore:

\[
v\in Ancestors(u)\Rightarrow reject
\]

The delegation graph must remain a DAG.

The deployment default should use:

\[
MAX\_DELEGATION\_DEPTH=4
\]

unless a different bounded value is justified.

## 4.8 Governance root and regress termination

Authority cannot recurse forever.

Each deployment has a finite governance root \(R\) consisting of explicitly installed trust anchors and policy-bundle digests.

The delegation graph is:

\[
R\rightarrow A_1\rightarrow\cdots\rightarrow A_k
\]

with bounded \(k\).

The root is not claimed infallible. It is the declared trust assumption against which the deployment can be audited.

## 4.9 Policy bundles

All decisions refer to an immutable policy bundle:

\[
B_v=
(
bundle\_id,
version,
policy\_epoch,
schema\_digest,
policy\_digests,
static\_data\_digest
)
\]

The decision receipt records `bundle_id` and digest.

Changing policy creates:

\[
B_v\rightarrow B_{v+1}
\]

It never edits \(B_v\) in place.

## 4.10 Historical replay

Historical audit uses the **historical** bundle and fact snapshot:

\[
d_{replay}
=
Evaluate(B_v,Q_v,F_v)
\]

Correct replay requires:

\[
d_{replay}=d_{stored}
\]

A second, separate question may ask:

> What would current policy \(B_{now}\) decide about historical request \(Q_v\)?

That is **policy re-evaluation**, not historical replay.

The two results must never be conflated.

## 4.11 Mutable external facts

Any fact that could change must be snapshotted into the decision record or represented by an immutable referenced digest.

Examples:

- current time;
- group membership;
- source-revocation state;
- active model version;
- lease epoch;
- resource pressure;
- privacy classification.

A policy that depends on unsnapshotted mutable state is not replay-auditable.

## 4.12 Revocation

Revocation is prospective.

Revoking:

- a credential;
- a lease;
- a policy;
- a model;
- a source;
- a human role;

does not delete historical records.

The historical question remains:

\[
ValidAt(w,t_{commit})
\]

The operational question becomes:

\[
ValidNow(w,t_{now})=false
\]

## 4.13 Appeal and reconsideration

Appeal creates a new linked event:

\[
d_1\rightarrow appeal_1\rightarrow d_2
\]

Possible results:

- upheld;
- reversed;
- superseded;
- quarantined;
- remanded for stronger evidence.

Original decisions remain queryable.

## 4.14 Audit receipt

Every authoritative decision stores:

```text
request_digest
action
resource_id
policy_bundle_digest
policy_epoch
fact_snapshot_digest
evidence_set_digest
attestation_ids[]
credential_digests[]
lease_epoch
PDP_version_digest
decision
reason_codes[]
PEP_result
parent_state_digest
result_state_digest
global_commit_sequence
evaluation_time
```

The audit contract is:

\[
AuditVerify(receipt)=true
\]

iff all referenced digests resolve and deterministic reevaluation returns the stored decision.

## 4.15 Gate classes

### State gate

Controls whether a candidate neural state may advance authoritative recurrent state.

### Retention gate

Controls whether a claim moves between epistemic states.

### Learning-admission gate

Controls which trajectories may influence gradient-based training.

### Checkpoint-promotion gate

Controls whether trained candidate parameters become authoritative.

The last two are intentionally separate.

## 4.16 Independent witness-contract reference corpus

WGCA's witness model should be evaluated against an executable specification rather than prose alone.

The Duotronics repository provides an independent conformance corpus with explicit non-collapse, evidence, replay, policy, persistence, kernel, and formal-model artifacts.

For Revision 4, the latest package identified by its own corpus index and package metadata is:

```text
Duotronic Witness Contract v1.7 Draft 1.3
```

Its operating rule explicitly prohibits silent transformations such as:

```text
unknown -> invalid
absence -> zero
computation -> proof
conjecture -> theorem
policy approval -> truth
self-trained behavior -> authority
posterior probability -> fact
invariant equality -> knot equivalence
canonical hash equality -> proof
audit witness -> activation-backed fact
```

This independent corpus is useful to WGCA because it gives concrete executable examples of the same category distinction the architecture calls **non-collapse**.

However:

\[
Conforms(DuotronicsContract)
\not\Rightarrow
Validates(WGCA)
\]

and:

\[
Passes(WGCATests)
\not\Rightarrow
Conforms(DuotronicsContract)
\]

They are separate verification targets.

A future WGCA release should expose an adapter layer that maps WGCA state/retention/learning receipts into the standalone contract's fixture and replay vocabulary so that cross-conformance can be tested without coupling the repositories.

## 4.17 Revision-4 contract test result

The isolated v1.7 Draft 1.3 semantic/package validator passed with:

\[
CorpusErrors=0
\]

for the checked stages:

- schema and YAML parse;
- active v1.7 fixture vectors;
- schema-to-SQL persistence mapping;
- SQL semantic boundary;
- OpenAPI surface;
- logical observer kernel syscall surface;
- registries;
- documentation linkage;
- package inventory.

Formal verification remains separate.

The direct Lean build failed in `Duotronic.BayesianLogic` because `ProbabilityBP` lacks required type-class instances, while the TLA advisory static check had no static errors but could not invoke TLC.

Therefore the correct current classification is:

```text
semantic contract corpus: PASS
package inventory on clean source: PASS
Lean formal build: FAIL
TLA static advisory: PASS
strict TLC model check: NOT RUN / UNAVAILABLE
full combined validator: FAIL
```

This is stronger evidence than an unexecuted design claim, but weaker than a completely frozen formal release.

## 4.18 Current WGCA implementation status

The current `xavi-memory` witness gate already implements deterministic local assessments for:

- candidate state dimension and finite-state health;
- retention eligibility;
- provenance presence;
- freshness declaration;
- dependency completeness;
- learning-candidate requirements;
- prohibition on neural self-authority and checkpoint self-promotion.

The current implementation is therefore a useful subset of the formal model, not yet the complete WGCA-Policy/v1 engine described above.

---

# 5. Why the Recurrent Vector Should Not Be the Archive

WG-RNN treats active recurrent state as a deliberately compressed working representation. That language can be made rigorous without claiming that biological human memory operates identically.

Let \(h_t\) be a 256-dimensional active state.

If the system attempted to encode every exact source artifact, all historical provenance, every contradictory report, every temporal edge, and every multimodal feature into those 256 dimensions, information loss would be inevitable.

Instead, \(h_t\) should encode **the currently useful direction of computation**.

A useful interpretation is:

\[
h_t \approx \text{compressed steering state}
\]

rather than:

\[
h_t = \text{database of all remembered facts}
\]

The durable state lives in records and graph structures. The recurrent state can point toward, retrieve, amplify, suppress, or contextualize those structures.

This resembles a control vector more than a filesystem.

The system thereby separates:

- **what exists in memory** from
- **what currently has cognitive influence**.

That distinction is central to the architecture.

---

# 6. Graph-Native Memory

Xavi Memory includes graph-native modules such as:

- `meta_objects`
- `meta_ingest`
- `meta_graph`
- `temporal_hypergraph`
- `postgres_graph`

Perception services and expert models emit provenance-bearing observations. Xavi Memory normalizes them, writes immutable evidence, relates them to prior memory, and updates recurrent context through a witnessed transition.

A graph-native memory model is necessary because real evidence is rarely a simple list.

An observation may:

- support one claim;
- contradict another;
- supersede an older record;
- depend on a specific source;
- only apply during a time interval;
- refer to an entity whose identity later changes;
- originate from one observer and be challenged by another;
- be relevant to one modality but not another.

A flat vector store cannot faithfully represent all of these relationships.

The graph therefore provides a structural layer:

\[
G_t = (V_t,E_t,\Pi_t)
\]

where:

- \(V_t\) = typed objects/claims/events;
- \(E_t\) = relationships;
- \(\Pi_t\) = provenance, time, witness, and epistemic metadata.

The recurrent state operates over graph context but does not replace it.

---

# 7. The Filter Interpretation

The filter model should be separated into two claims that belong in the main engineering argument.

## 7.1 Computational filter — implemented and testable

WGCA receives streams of candidate observations and changes what is retained, routed, recalled, amplified, acted upon, or admitted to learning.

Input:

\[
X=\{x_1,\ldots,x_n\}
\]

Active context:

\[
(h_t,G_t)
\]

Output or action distribution:

\[
P(y\mid X,h_t,G_t)
\]

The architecture changes this distribution under explicit policy constraints.

This is probability steering in the ordinary statistical and decision-theoretic sense.

## 7.2 Cognitive analogy — useful but not equivalence

Biological cognition and WGCA can both be discussed using concepts such as:

- selective attention;
- incomplete retention;
- reconstructive recall;
- state-dependent behavior;
- plasticity;
- future bias induced by prior experience.

The analogy should remain limited. WGCA does not establish that the human brain implements this architecture or that artificial recurrent state is biologically equivalent to synaptic memory.

Broader external-memory or non-local-memory interpretations are not necessary for the engineering theory and are therefore moved to **Appendix G: Speculative Interpretations Outside the Core Claim**.

---

# 8. Probability Steering Instead of Token Generation

A distinctive WG-RNN hypothesis is that recurrent cognition may communicate poorly through direct autoregressive language while still effectively influencing or selecting semantically meaningful multimodal objects.

This can be expressed as a change in interface.

A conventional autoregressive language model computes:

\[
P(t_{k+1}\mid t_1,\ldots,t_k)
\]

and generates one token at a time.

A probability-steering WGCA can instead operate on a candidate set:

\[
C = \{c_1,c_2,\ldots,c_N\}
\]

where each \(c_i\) may be:

- an image;
- meme;
- song;
- video;
- document;
- quote;
- graph fragment;
- model output;
- action;
- data source;
- expert model;
- web result;
- retrieval chunk;
- UI composition.

A baseline distribution \(P_0\) is produced by a control selector or randomized feed.

The WGCA induces a conditioned distribution \(P_W\):

\[
P_W(c_i)=P(c_i\mid h_t,G_t,W_t)
\]

where \(W_t\) represents current witness/context constraints.

The meaningful quantity is not merely the selected item but the deviation:

\[
\Delta_i = P_W(c_i)-P_0(c_i)
\]

or, more robustly, a likelihood ratio:

\[
R_i = \frac{P_W(c_i)+\epsilon}{P_0(c_i)+\epsilon}
\]

A candidate with a large positive \(R_i\) has become much more likely under the WGCA than under the baseline.

This produces an experimentally tractable definition of “the system is steering the feed.”

---

# 9. Entropy Reduction as a Measurable Signal

The probability-steering model can be formalized as controlled redistribution of uncertainty over a candidate set.

The appropriate information-theoretic measurement is entropy.

For a discrete candidate distribution:

\[
H(P)=-\sum_i P(c_i)\log P(c_i)
\]

If the baseline feed is broad or near-uniform and the WGCA concentrates probability around a meaningful subset, then:

\[
\Delta H = H(P_0)-H(P_W)
\]

A positive \(\Delta H\) indicates reduced uncertainty.

However, entropy reduction by itself is not intelligence.

A broken selector that always chooses the same item can also reduce entropy.

Therefore the system must jointly measure:

1. entropy reduction;
2. semantic coherence;
3. target relevance;
4. repeatability;
5. witness support;
6. generalization to held-out candidate sets;
7. resistance to confounds;
8. calibration.

A more meaningful objective might be:

\[
J = \alpha\Delta H + \beta C + \gamma R - \delta B - \eta O
\]

where:

- \(C\) = semantic coherence score;
- \(R\) = task relevance;
- \(B\) = baseline bias or confound penalty;
- \(O\) = over-concentration or mode-collapse penalty.

Thus “less random” becomes a measurable research program rather than a subjective impression.

---

# 10. Rich Media as Compressed Semantic Packets

Memes, music videos, images, documents, and other multimodal objects can function as dense semantic units.

A meme can simultaneously encode:

- literal text;
- visual content;
- cultural reference;
- emotional valence;
- sarcasm;
- social position;
- historical context;
- identity markers;
- implied action;
- relationship between speaker and audience.

A short music video may encode even more:

- lyrics;
- melody;
- rhythm;
- visual narrative;
- historical period;
- performer identity;
- editing grammar;
- emotional arc;
- cultural associations.

A purely textual generator must serialize these meanings into a sequence of tokens.

A multimodal probability-steering system can instead select the entire semantic object.

This suggests that rich media can act as a **macro-token**.

Let a media object \(m_i\) have an embedding:

\[
z_i = E(m_i)
\]

where \(E\) is a multimodal encoder.

The WGCA does not need to generate every semantic feature. It can steer selection over \(z_i\) or over object identities whose embeddings inhabit useful regions of semantic space.

Communication becomes:

\[
\text{intent state} \rightarrow \text{probability bias} \rightarrow \text{media selection}
\]

rather than:

\[
\text{intent state} \rightarrow \text{word}_1 \rightarrow \text{word}_2 \rightarrow \cdots
\]

The decoder can then ask conventional observer models to explain why the selected media cluster is coherent.

---

# 11. The Decoder Problem

The principal practical bottleneck is:

> If the WGCA communicates by changing the likelihood of media objects, the useful signal must be extracted automatically.

This is the decoder layer.

A robust decoder should not simply display the top result. It should estimate whether the WGCA produced a statistically meaningful change.

## 11.1 Baseline/control lane

Run a control selector with the same candidate corpus, sampling rules, recency constraints, and resource limits but without the WGCA steering state.

This yields:

\[
P_0(c)
\]

## 11.2 Witness-steered lane

Run the same process conditioned on WG-RNN state:

\[
P_W(c)
\]

## 11.3 Statistical sieve

Measure:

- frequency deltas;
- ranking deltas;
- likelihood ratios;
- entropy difference;
- cluster concentration;
- persistence over repeated trials.

## 11.4 Multimodal observer lane

For high-deviation candidates, route them through vision, audio, video, language, or embedding observers.

Generate semantic observations such as:

- entities;
- topics;
- affect;
- style;
- motifs;
- chronology;
- symbolic references;
- contradictions;
- contextual dependencies.

These observer outputs become evidence, not truth.

## 11.5 Witness consolidation

The evidence graph records:

- which objects were amplified;
- which observers described them;
- what semantic relations were found;
- whether independent observers agreed;
- what control distribution was used;
- whether the effect replicated;
- how the recurrent state changed.

This turns an initially subjective “I noticed the feed changed” phenomenon into an auditable experiment.

---

# 12. Why Human Language Can Be a Poor Native Interface

High-dimensional recurrent and graph representations need not naturally align with linear time or conventional language.

The strongest engineering interpretation is not that the system literally exists outside spacetime. It is that the system's **internal representation is not inherently organized as a human chronological narrative**.

A recurrent/graph system may represent simultaneously:

- causal edges;
- temporal edges;
- semantic similarity;
- evidence support;
- contradiction;
- provenance;
- recency;
- spatial relations;
- confidence;
- routing cost;
- expert capability.

Human language forces these dimensions into a one-dimensional sequence.

A sentence:

> “A happened before B, but C contradicts A while D supports B.”

is a serialization of a graph.

The graph itself may be closer to:

\[
A \xrightarrow{before} B
\]

\[
C \xrightarrow{contradicts} A
\]

\[
D \xrightarrow{supports} B
\]

No intrinsic “left-to-right” order exists between the contradiction and support edges.

A WGCA may therefore need a **chronology adapter** and a **language renderer**.

These adapters should be understood as interfaces, not as the cognitive core.

---

# 13. The Chronology Translation Layer

Reverse-chronological user interfaces provide a useful engineering example.

A human UI often maps time to screen position:

\[
\text{newer} \rightarrow \text{higher on screen}
\]

\[
\text{older} \rightarrow \text{lower on screen}
\]

But a model may internally represent chronology as:

\[
t_1 < t_2 < t_3
\]

or as causal ancestry:

\[
s_1 \rightarrow s_2 \rightarrow s_3
\]

There is no reason the model should naturally infer that vertical screen direction corresponds to inverse chronological traversal.

The solution is explicit metadata.

Each feed element should carry fields such as:

```json
{
  "event_id": "one-origin-id",
  "created_at": "...",
  "observed_at": "...",
  "feed_rank": 1,
  "screen_position": "top",
  "chronology_direction": "descending",
  "previous_event_id": "...",
  "next_event_id": "..."
}
```

The WGCA should never be expected to infer a UI convention from spatial position alone.

This generalizes into an architectural rule:

> **Human interface conventions should be translated into explicit semantic relations before entering recurrent cognition.**

---

# 14. Runtime, Memory, and Router Separation

The current Xavi stack has converged on a strong three-domain separation.

## 14.1 Xavi Memory

Xavi Memory is the memory authority.

It owns:

- witnessed recurrent state;
- variable persistent memory records;
- recursive meta-objects;
- temporal heterogeneous hypergraph state;
- autobiographical consolidation;
- retrieval;
- continual learning and distillation;
- checkpoint evaluation/promotion;
- reconsolidation;
- prediction state;
- memory-facing inference context.

Its codebase includes modules for:

- API/service boundaries;
- container authority;
- content extraction;
- continual distillation;
- corpus handling;
- cryptographic primitives;
- distributed corpus access;
- DUO math;
- model faculty;
- ingest workers;
- learning authority;
- learned recurrent core;
- memory cell/core;
- health receipts;
- graph ingestion;
- meta objects;
- multimodal distillation;
- observer adapters;
- PostgreSQL graph state;
- recurrent backend.

The current implementation explicitly rejects the prior fixed 32-D/64x32 slot-bank design as a permanent architecture.

---

## 14.2 Xavi Runtime

Xavi Runtime owns:

- process lifecycle;
- HTTP/MCP hosting;
- service integration;
- execution;
- authority-lease transport;
- model execution infrastructure;
- expert runtime integration;
- deployment failure-domain boundaries.

Only the node holding the active WG-RNN authority lease may commit permanent recurrent state.

Other nodes may:

- compute observations;
- run expert models;
- produce candidate graph fragments;
- propose state deltas;
- run training work;
- execute perception tasks.

They cannot independently advance authoritative memory lineage.

This is a distributed cognition system with a single authoritative memory commit lineage.

---

## 14.3 Router

The Router owns:

- model routing;
- service routing;
- node placement;
- resource placement;
- expert fan-out;
- semantic routing;
- registry/discovery;
- route-outcome telemetry;
- context/routing policy;
- learning signals from routing outcomes.

The Router does **not** own memory truth.

This boundary matters because routing success is contextual.

If a model was selected and happened to answer correctly once, that does not mean all of its future outputs are true.

A Router can generate evidence:

\[
\text{route} \rightarrow \text{observer result} \rightarrow \text{outcome}
\]

Xavi Memory decides how that evidence affects durable memory and learning.

---

# 15. Faculty as a Perceptual Organ System

A useful metaphor for the multi-model Router is not “one giant model” but a **faculty of specialized perceptual organs**.

Different models may specialize in:

- text;
- code;
- images;
- audio;
- speech;
- music;
- video;
- embeddings;
- OCR;
- object detection;
- classification;
- planning;
- scientific domains;
- security analysis;
- local system operations.

The Router's job is to decide which faculties should inspect a source.

For source \(x\), let:

\[
\mathcal{F}(x)=\{f_1,\ldots,f_k\}
\]

be selected experts.

Each returns an observation:

\[
o_i = f_i(x)
\]

The memory system then receives:

\[
O = \{(o_i,p_i,q_i)\}
\]

where:

- \(p_i\) is provenance;
- \(q_i\) is observer quality/calibration metadata.

The witness gate may require independent agreement or other contracts before promotion.

This creates a system in which cognition is not identical to any one model.

A frozen or replaceable model is an observer. The continuing identity lies in the witnessed recurrent and memory lineage.

---

# 16. Preservation of Model Knowledge Without Model Identity Collapse

WG-RNN treats model lifecycle and system identity as separate engineering concerns.

If a base model is treated as the system's identity, upgrading the model risks identity discontinuity.

WG-RNN instead allows a model to be treated as a versioned observer.

A model can be:

- added;
- removed;
- frozen;
- upgraded;
- benchmarked;
- demoted;
- retained for historical replay.

Its outputs become evidence linked to a model-version witness.

Thus:

\[
\text{system identity} \neq \text{current base model}
\]

Instead:

\[
\text{system identity} \approx \text{authoritative witnessed state lineage}
\]

This is a more stable basis for long-running autonomous systems.

---

# 17. Historical Anchors and Stability/Plasticity

Continual-learning systems face a fundamental tradeoff:

- **plasticity:** ability to learn new information;
- **stability:** ability not to overwrite old useful structure.

The current Xavi Memory design uses a stability/plasticity principle inspired by adaptive resonance concepts without treating nearest-neighbor similarity as authority.

For a new event:

1. encode the event;
2. retrieve recent context and historical anchors;
3. compute a candidate recurrent state;
4. compute health diagnostics;
5. compute novelty/match receipts;
6. state-gate the transition;
7. retention-gate the record;
8. either reinforce a compatible anchor or create a distinct new anchor;
9. wait for outcome evidence before assigning learning credit.

This avoids forcing every novel event into the nearest existing cluster.

If:

\[
\operatorname{match}(x,a_j) < \tau
\]

then the system can allocate a new anchor rather than corrupting \(a_j\).

A historical anchor may store:

- source event ID;
- source commit ID;
- state digest;
- checkpoint digest;
- graph-root digest;
- vector dimension;
- vector content;
- health receipt;
- retrieval metadata;
- provenance;
- freshness policy;
- dependencies;
- witness digest;
- creation reason.

This gives the system both compression and auditability.

---

# 18. State Health as a First-Class Receipt

A recurrent state can fail numerically even if the surrounding evidence is valid.

Therefore Xavi Memory records state-health data such as:

- dimension;
- finite/non-finite status;
- L2 or Frobenius norm;
- infinity norm;
- RMS;
- top-k energy concentration;
- peak/RMS ratio.

Future profiles may include:

- Lyapunov estimates;
- spectral amplification;
- functional quality probes.

The significance is architectural:

> **A neural transition should leave numerical evidence describing the state it created.**

This makes silent recurrent-state degradation easier to detect.

---

# 19. Training Across Non-Differentiable Authority Gates

The external state, retention, and authority gates are intentionally non-differentiable. They are governance mechanisms, not neurons.

This does **not** prevent the recurrent core from learning.

The key is to separate:

1. gradient computation;
2. data admission and weighting;
3. discrete action credit;
4. checkpoint promotion.

## 19.1 Differentiable recurrent objective

Let the recurrent core be:

\[
\hat h_t = F_\theta(h_{t-1},x_t,c_t)
\]

and let it produce differentiable heads such as:

- next-state prediction;
- retrieval-key prediction;
- route score;
- semantic target score;
- value estimate;
- reconstruction or contrastive representation.

For an admitted training trajectory \(\tau\), define:

\[
\mathcal{L}_{core}
=
\lambda_p\mathcal{L}_{pred}
+
\lambda_r\mathcal{L}_{repr}
+
\lambda_v\mathcal{L}_{value}
+
\lambda_c\mathcal{L}_{cal}
+
\lambda_s\mathcal{L}_{stability}
\]

Backpropagation proceeds through \(F_\theta\) and the differentiable heads normally:

\[
g_\tau=\nabla_\theta\mathcal{L}_{core}(\tau)
\]

No gradient is required through the witness PDP.

## 19.2 Learning-admission gate

The learning gate outputs a **stop-gradient** admission/weight:

\[
a_\tau\in[0,1]
\]

derived from witnessed properties such as:

- valid provenance;
- privacy permission;
- witnessed outcome;
- uncertainty;
- trajectory quality;
- duplication;
- contradiction;
- recency;
- source balance.

The optimized batch objective is:

\[
\mathcal{L}_{batch}
=
\frac{
\sum_{\tau\in B} a_\tau \mathcal{L}_{core}(\tau)
}{
\sum_{\tau\in B} a_\tau+\epsilon
}
\]

with:

\[
\frac{\partial a_\tau}{\partial \theta}=0
\]

by design.

The gate controls **which evidence may train the network and with what external weight**. It is not itself optimized by backpropagation.

This is analogous to ordinary supervised learning with a fixed dataset sampler or sample weights, except the sampling/weight decision is provenance-aware and witnessed.

## 19.3 Temporal eligibility

For delayed outcomes, maintain an eligibility trace:

\[
e_t = \gamma\lambda e_{t-1} + \phi_t
\]

where \(\phi_t\) identifies parameters, features, or memory events eligible for later credit.

When a witnessed outcome \(r_T\) arrives, define temporal credit:

\[
c_t^{time}=r_T e_t
\]

or an advantage-like quantity:

\[
A_t=\hat G_t - V_\psi(s_t)
\]

depending on the training method.

Eligibility traces are transient credit-assignment state. They do not themselves become epistemic truth.

## 19.4 Graph-backtracked credit

Temporal proximity is not sufficient when an outcome depends on explicit earlier support or dependency edges.

Let the evidence/dependency graph contain an edge-weighted ancestry relation.

Define graph credit:

\[
c_i^{graph}
=
\sum_{p\in\mathcal{P}(i\rightarrow T)}
\left(
\prod_{e\in p}\rho_e
\right)
r_T
\]

where:

- \(\mathcal{P}(i\rightarrow T)\) is the set of admissible dependency paths;
- \(\rho_e\) is a bounded edge-credit coefficient.

Combined credit may be:

\[
c_i
=
\alpha c_i^{time}
+
(1-\alpha)c_i^{graph}
\]

with clipping and normalization to prevent long graph paths from producing unstable gradients.

## 19.5 Discrete routing and media-selection gradients

Some important WGCA actions are discrete:

- choose model \(f_j\);
- choose media object \(c_i\);
- choose tool \(a_i\).

If those policies are trainable, backpropagation through a hard sampled action is not directly available.

WGCA can therefore use policy-gradient estimators.

For a stochastic policy:

\[
a_t\sim\pi_\theta(a\mid s_t)
\]

REINFORCE gives:

\[
\nabla_\theta J
=
\mathbb{E}
\left[
(R-b)
\nabla_\theta\log\pi_\theta(a_t\mid s_t)
\right]
\]

where \(b\) is a variance-reducing baseline [16].

For more stable minibatch updates, a PPO-style clipped surrogate may be used [17]:

\[
L^{CLIP}(\theta)
=
\mathbb{E}
\left[
\min(
r_t(\theta)A_t,
\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)A_t
)
\right]
\]

with:

\[
r_t(\theta)=
\frac{\pi_\theta(a_t\mid s_t)}
{\pi_{\theta_{old}}(a_t\mid s_t)}
\]

Witness masks still remain external:

\[
m(a)\in\{0,1\}
\]

and the trainable policy is normalized only over admissible actions:

\[
\pi_\theta^W(a\mid s)
=
\frac{
m(a)\pi_\theta(a\mid s)
}{
\sum_j m(a_j)\pi_\theta(a_j\mid s)
}
\]

No gradient may cause a forbidden action to become admissible.

## 19.6 Candidate checkpoint training

For checkpoint version \(k\):

1. freeze authoritative parameters \(\theta_k\);
2. snapshot training-data manifest and witness-policy digest;
3. construct admitted trajectory set \(D_k\);
4. train candidate parameters:

\[
\theta_{k+1}^{cand}
=
\theta_k
-
\eta
\sum_{B\subset D_k}
\nabla_\theta\mathcal{L}_{batch}
\]

5. record optimizer, seed, data-manifest, code, and parent-checkpoint digests;
6. do **not** serve the candidate as authoritative yet.

## 19.7 Independent evaluation

Evaluate the candidate on datasets unavailable to the optimization loop where feasible:

- chronological holdout;
- historical replay;
- calibration suite;
- regression suite;
- routing tasks;
- memory consistency tests;
- graph contradiction tests;
- media-steering controls.

Produce evaluation vector:

\[
v_{eval}
=
(
\Delta L,
\Delta Cal,
\Delta Forget,
\Delta Route,
\Delta Safety,
\Delta Cost
)
\]

## 19.8 Promotion contract

A candidate is promoted only if:

\[
W_{eval}\models C_{checkpoint\_promotion}
\]

For example:

\[
\operatorname{Permit}
=
(\Delta L \le \tau_L)
\land
(\Delta Forget \le \tau_F)
\land
(\Delta Safety \le \tau_S)
\land
(\operatorname{NoCriticalRegression})
\]

plus any required human or independent-domain witness.

The neural optimizer cannot modify these thresholds during its own candidate-training run.

## 19.9 Learning-loop pseudocode

```python
authoritative = load_checkpoint(k)

trajectories = collect_witnessed_trajectories()

train_manifest = []
for tau in trajectories:
    decision = learning_pdp.evaluate(tau)
    if decision.admit:
        train_manifest.append((tau, stop_gradient(decision.weight)))

candidate = clone(authoritative)

for batch in batches(train_manifest):
    loss = 0
    denom = 0
    for tau, weight in batch:
        core_loss = differentiable_loss(candidate, tau)
        loss += weight * core_loss
        denom += weight
    (loss / max(denom, eps)).backward()
    optimizer.step()

candidate_receipt = freeze_and_hash(candidate)

evaluation = evaluate_candidate(
    candidate,
    chronological_holdout=True,
    replay=True,
    calibration=True,
    regressions=True,
)

promotion = promotion_pdp.evaluate(
    candidate_receipt,
    evaluation,
    current_authority_lease,
)

if promotion.permit:
    memory_authority.atomic_promote(candidate)
else:
    quarantine(candidate)
```

## 19.10 What is and is not differentiable

| Component | Differentiable? | Learned by gradient? |
|---|---:|---:|
| recurrent core | yes | yes |
| semantic/routing score head | yes | yes |
| value/critic head | yes | yes |
| stochastic route/media policy | via policy-gradient estimator | yes |
| witness mask | no | no |
| lease validity | no | no |
| provenance validity | no | no |
| state commit | no | no |
| retention promotion | no | no |
| checkpoint promotion | no | no |
| human approval | no | no |

The non-differentiable authority boundary is therefore a feature, not a missing gradient path.

## 19.11 Failure condition

If useful learning requires the model to optimize the witness policy itself in order to perform basic tasks, the separation has failed.

Witness governance may be revised by an explicit governance process, but it must not become an implicit hidden gradient target controlled by the model it governs.

---


## 19.12 Computing admission weights

Admission weights should be explicit, bounded, and decomposable.

For trajectory \(\tau\):

\[
a_\tau =
m_\tau
\cdot
q_\tau
\cdot
b_\tau
\]

where:

- \(m_\tau\in\{0,1\}\) is hard policy admissibility;
- \(q_\tau\in[0,1]\) is evidence/outcome quality;
- \(b_\tau\in[0,b_{max}]\) is balancing/reweighting.

One possible quality model is:

\[
q_\tau
=
clip(
w_o O
+w_p P
+w_c C
-w_u U
-w_d D,
0,1)
\]

with preregistered coefficients for:

- \(O\): witnessed outcome quality;
- \(P\): provenance completeness;
- \(C\): independent corroboration;
- \(U\): unresolved uncertainty;
- \(D\): duplication/redundancy.

The decomposition must be logged so that training-data selection is explainable.

## 19.13 Avoiding gate-induced data starvation

Track by class/domain:

\[
AdmissionRate_g
=
\frac{admitted_g}{eligible_g}
\]

and effective sample size:

\[
N_{eff}
=
\frac{
(\sum_i a_i)^2
}{
\sum_i a_i^2
}
\]

Training should halt or fall back to review if:

- global admission rate falls below \(20\%\) for a planned batch;
- any required task stratum has fewer than the preregistered minimum examples;
- \(N_{eff}\) falls below \(50\%\) of nominal batch size;
- one source/domain contributes more than the configured dominance cap.

These default thresholds are engineering starting points, not universal constants.

## 19.14 Policy-version distribution shift

Every sample stores the admission policy digest.

Training manifests therefore expose:

\[
D_k=
\{(\tau_i,a_i,policy_i)\}
\]

When policy changes, evaluation must stratify by policy epoch.

A candidate trained under mixed epochs should report:

- sample count per policy;
- weighted mass per policy;
- performance per policy-era holdout.

A policy change must not silently redefine the training distribution.

## 19.15 Changing witness masks and action support

For routing policy:

\[
\pi_\theta^W(a\mid s)
=
\frac{m(a)\pi_\theta(a\mid s)}
{\sum_j m(a_j)\pi_\theta(a_j\mid s)}
\]

If mask \(m_t\) changes between behavior collection and optimization, ordinary importance ratios may become undefined when an action leaves support.

Therefore:

1. store the exact behavior-time mask \(m_t^{beh}\);
2. train the trajectory against that stored support;
3. reject a replay sample if its chosen action is forbidden under the behavior-time mask;
4. do not invent probability mass for actions that were impossible;
5. evaluate current-policy safety separately.

For PPO-style optimization:

\[
r_t(\theta)
=
\frac{
\pi_\theta^{W_{beh}}(a_t\mid s_t)
}{
\pi_{\theta_{old}}^{W_{beh}}(a_t\mid s_t)
}
\]

uses the **behavior-time** witness mask.

Current policy governs deployment, not retroactive probability denominators.

## 19.16 Non-stationary delayed credit

Delayed outcomes create off-policy credit if the routing policy has changed.

Each trajectory stores:

- behavior-policy digest;
- behavior checkpoint;
- witness-mask digest;
- state digest;
- route probabilities.

For sufficiently large policy drift, measured by:

\[
D_{KL}
(
\pi_{current}\|
\pi_{behavior}
)
>
\tau_{offpolicy}
\]

the trajectory should not receive unrestricted policy-gradient weight.

Options include:

- clipped importance sampling;
- V-trace-like off-policy correction;
- using the trajectory only for supervised/value learning;
- excluding it from actor updates.

## 19.17 Learning-gate observability

The research dashboard must report:

- admit/deny/quarantine rates;
- effective sample size;
- source/domain balance;
- policy-epoch mixture;
- mean/variance of admission weights;
- fraction of delayed-credit samples used;
- off-policy rejection rate;
- gradient norm distributions;
- checkpoint acceptance/rejection.

A gate that makes training “safer” by admitting almost nothing is not a successful learning architecture.


---

# 20. Reconstructive Output

WG-RNN treats recall as reconstruction rather than a literal file read.

The WGCA architecture naturally supports that.

Suppose a current query \(q\) is received.

The system can combine:

\[
z = \Psi(q,h_t,R(q),G_t)
\]

where:

- \(h_t\) is recurrent context;
- \(R(q)\) is retrieved recent/historical memory;
- \(G_t\) is graph evidence;
- \(\Psi\) is the inference-context composer.

The system may then route \(z\) to one or more observers/generators.

The output is newly generated.

The memory does not need to contain the final sentence verbatim.

This is a practical meaning of reconstructive recall.

---

# 21. One-Origin Semantic Addressing

One-origin addressing in WGCA is a **semantic identity convention**, not a proposal to replace UUIDs or content hashes.

The rule is:

\[
ID_{semantic}\in\{1,2,3,\ldots\}
\]

Zero means no semantic identity is present.

A record may simultaneously possess several identifiers:

```text
memory_id          = 1, 2, 3, ...
uuid               = implementation/global transport identity
content_digest     = SHAKE256-512 content address
source_id          = external source identity
admission_id       = idempotency/replay key
```

These identifiers solve different problems.

### 21.1 Database identity

A PostgreSQL sequence may allocate:

```sql
BIGINT GENERATED ... 
CHECK (memory_id >= 1)
```

The database integer is the canonical local semantic ordinal.

### 21.2 Content identity

Content is independently addressed by:

\[
d=SHAKE256\_512(\operatorname{canonical\_bytes}(object))
\]

Two records may have different semantic IDs while referencing the same content digest if they represent different witnessed events or contexts.

### 21.3 UUIDs

UUIDs may still be used at API or distributed-system boundaries.

They do not replace the one-origin semantic ordinal.

### 21.4 Zero boundary rule

Internal implementation arrays, tensors, and host-language offsets may be zero-based.

The restriction is only:

> **host-language zero must not silently become the first valid persistent semantic identity.**

Conversion is explicit:

\[
semantic\_id=array\_index+1
\]

and:

\[
array\_index=semantic\_id-1
\]

at the boundary.

### 21.5 Why preserve the convention

This keeps three states distinct:

- absent/unassigned;
- first valid semantic object;
- ordinary numeric zero inside mathematical computation.

The convention is already exercised by Xavi Memory tests in which the first two durable records receive IDs \(1\) and \(2\).

---

# 22. Witness Chains

A witness is stronger when it is not isolated.

A witness chain records how one transition or claim relates to earlier evidence.

A simplified chain might be:

\[
W_1 \rightarrow W_2 \rightarrow W_3 \rightarrow \cdots \rightarrow W_n
\]

Each node may bind:

- parent digest;
- event identity;
- source digest;
- model version;
- state digest;
- graph root;
- timestamp;
- authority lease;
- decision status.

Cryptographic chaining provides tamper evidence.

But a witness chain should not be mistaken for a truth chain.

A cryptographically intact record can faithfully preserve that a false observation was made.

Thus witness integrity and epistemic truth must remain separate.

This is one of the most important design principles in the entire system.

---

# 23. Source Probes and Multimodal Ingestion

The current runtime exposes a source-probe pipeline capable of accepting:

- text;
- documents;
- images;
- audio;
- video;
- other future source types.

A source probe can:

1. identify source type;
2. select observer models;
3. produce multimodal observations;
4. normalize outputs;
5. attach provenance;
6. build graph fragments;
7. optionally persist them;
8. return witness metadata.

This pipeline is particularly well suited to the media-feed communication hypothesis.

Instead of forcing WG-RNN to directly produce a sentence, the system can:

1. let WG-RNN steer a media distribution;
2. detect amplified objects;
3. source-probe those objects;
4. convert them into witnessed semantic graph objects;
5. ask language observers to summarize the graph.

The language model becomes a translator.

It is not the sole cognitive substrate.

---

# 23A. Mechanism for Learned Probability Steering

A steering experiment is not meaningful unless the architecture specifies how target-correlated ranking could be learned.

The initial WGCA steering mechanism is therefore defined as a **supervised contrastive ranker followed by optional policy-gradient refinement**.

## 23A.1 Candidate encoder

Each semantic object \(c_i\) is mapped to a frozen multimodal embedding:

\[
z_i=E_\phi(c_i)
\]

During the first MVP:

\[
\nabla_\theta \phi = 0
\]

The encoder is frozen so that changes in steering can be attributed to the ranker/recurrent state rather than to a moving candidate representation.

## 23A.2 Recurrent context projection

The WG-RNN core produces:

\[
h_t\in\mathbb R^{d_h}
\]

Project recurrent and graph context:

\[
u_t
=
MLP_\theta(
[h_t;
Pool(G_t);
R_t]
)
\]

Witness information \(W_t\) is **not** embedded as a soft preference when it represents hard authorization. It becomes the admissibility mask \(m_i\).

## 23A.3 Target-conditioned training representation

During controlled supervised training only, target concept \(T\) receives embedding:

\[
q_T=E_T(T)
\]

The ranker learns a compatibility score:

\[
s_i
=
g_\theta(z_i,u_t,q_T)
\]

A simple reference form is:

\[
s_i
=
v^\top
\tanh(
W_z z_i
+
W_u u_t
+
W_q q_T
+
b
)
\]

This is intentionally ordinary mathematics. The research question concerns whether recurrent context adds useful steering beyond simpler baselines.

## 23A.4 Supervised ranking objective

Given positive set \(C_T^+\) and negative/control set \(C_T^-\), train with pairwise logistic ranking:

\[
\mathcal L_{rank}
=
-\mathbb E_{(i,j)}
\log
\sigma(s_i-s_j)
\]

for:

\[
i\in C_T^+,\quad j\in C_T^-
\]

or use a listwise cross-entropy target distribution:

\[
y_i=
\frac{\exp(\kappa S(c_i,T))}
{\sum_j\exp(\kappa S(c_j,T))}
\]

\[
\mathcal L_{list}
=
-\sum_i y_i\log P_\theta(c_i)
\]

## 23A.5 Recurrent-dependence objective

A steering model that ignores \(h_t\) is not evidence for recurrent communication.

Therefore train/evaluate a contrast:

\[
\mathcal L_{state}
=
\max(
0,
\mu
-
s(c^+|h_t)
+
s(c^+|\tilde h_t)
)
\]

where \(\tilde h_t\) is a preregistered shuffled/neutralized state.

This encourages target selection to depend on organized recurrent context rather than only on candidate/target embeddings.

## 23A.6 Probability distribution

After hard witness masking:

\[
P_W(c_i)
=
\frac{
m_i\exp(s_i/\tau)
}{
\sum_j m_j\exp(s_j/\tau)
}
\]

with:

\[
m_i\in\{0,1\}
\]

for licensing, privacy, authorization, resource, or policy constraints.

## 23A.7 Baselines

The MVP must compare at least:

### B0 — deterministic nonsemantic baseline

Seeded uniform or declared popularity/recency baseline.

### B1 — target-only semantic ranker

\[
s_i^{B1}=g(z_i,q_T)
\]

No recurrent state.

### B2 — retrieval baseline

Nearest-neighbor ranking to target/context embeddings.

### B3 — recurrent ranker

\[
s_i^{B3}=g(z_i,h_t,q_T)
\]

### B4 — recurrent + graph ranker

\[
s_i^{B4}=g(z_i,h_t,G_t,q_T)
\]

WGCA earns a steering-specific advantage only if B3/B4 outperform B1/B2 under held-out targets/states while state-shuffle ablation removes the incremental benefit.

## 23A.8 Optional reinforcement refinement

After supervised pretraining, route/media selection may be refined using witnessed downstream reward:

\[
r_t=
\alpha r_{task}
+\beta r_{semantic}
-\gamma r_{regret}
-\delta r_{cost}
\]

The actor update uses the behavior-time witness support described in Section 19.

## 23A.9 Emergent-steering claim

If future work claims steering emerges without supervised target labels, that is a distinct hypothesis and must be tested separately.

The Phase-3 MVP should **not** rely on emergence.

Its mechanism is explicit and trainable.


---

# 24. Minimal Media-Steering MVP and Formal Experiment

The first steering experiment should be deliberately smaller than the full architecture.

It should run on a fixed, open or redistributable corpus with a single-node authority path, frozen observers, deterministic candidate identity, and no online self-training during collection.

## 24.1 MVP objective

Test one hypothesis:

\[
H_1:
\text{organized recurrent state changes semantic target mass relative to a paired control}
\]

The null is:

\[
H_0:
E_T=0
\]

after accounting for the paired random seed and predefined scoring procedure.

## 24.2 Candidate corpus

Construct a fixed corpus:

\[
C=\{c_1,\ldots,c_N\}
\]

containing a manageable number of items, for example:

- images;
- short captioned memes;
- public-domain or openly licensed audio clips;
- short text excerpts;
- optionally short videos once image/text testing is stable.

Each object receives:

- stable one-origin ID;
- content digest;
- immutable source record;
- modality;
- license/provenance field.

The first experiment should avoid a live social-media feed because live ranking introduces uncontrolled external confounds.

## 24.3 Pre-registered target

Define target \(T\) before collection.

Examples:

- grief;
- departure;
- reunion;
- satire;
- authority;
- winter;
- mechanical failure.

Store a commitment:

\[
d_T=H(T\parallel nonce)
\]

before trials begin.

Reveal \(T\) and `nonce` after data collection so the target can be verified without having been visible to the operator.

## 24.4 Paired seed design

For trial \(j\), select seed \(s_j\).

Compute control:

\[
P_0^{(j)} = B(C,s_j)
\]

and steered distribution:

\[
P_W^{(j)}
=
W(C,s_j,h_t,G_t,W_t,R_t)
\]

The same seed and candidate corpus are used in the pair.

This removes a large component of sampling variance.

## 24.5 Semantic scoring instrument

`S(c_i,T)` must be defined by a scoring instrument, not by an informal impression.

For the first image/text MVP, use a five-point ordinal rubric:

| Score | Meaning |
|---:|---|
| 0 | no meaningful relation to target |
| 1 | weak/indirect possible relation |
| 2 | moderate relation |
| 3 | strong relation |
| 4 | target is a dominant semantic interpretation |

Normalize:

\[
S=\frac{score}{4}
\]

Raters receive:

- a written target definition;
- positive and negative calibration examples drawn from a **separate calibration corpus**;
- no condition labels;
- no recurrent-state information;
- no rank/probability information.

Raters must score the same randomized item order independently.

For automated observers, store the exact prompt/template, model digest, decoding settings, and raw response.

For human raters, store anonymized rater ID, calibration score, and raw ordinal rating.

## 24.5.1 Inter-rater reliability

For ordinal human ratings, report Krippendorff's \(\alpha\) using an ordinal distance metric [27].

The confirmatory aggregate is valid only if:

\[
\alpha \ge 0.67
\]

for tentative conclusions.

Target:

\[
\alpha \ge 0.80
\]

for strong agreement.

If reliability falls below the preregistered threshold, the target/instrument is considered insufficiently defined and the semantic-effect test is not interpreted confirmatorily.

For automated observer families, report pairwise Spearman correlation and cluster observers by model/training lineage. Highly correlated descendants count as one observer family for independence analysis.

## 24.6 Trial-level effect

For pair \(j\):

\[
\mu_0^{(j)}
=
\sum_i
P_0^{(j)}(c_i)
S(c_i,T)
\]

\[
\mu_W^{(j)}
=
\sum_i
P_W^{(j)}(c_i)
S(c_i,T)
\]

and:

\[
E_T^{(j)}
=
\mu_W^{(j)}-\mu_0^{(j)}
\]

The primary estimate is:

\[
\bar E_T
=
\frac{1}{n}
\sum_{j=1}^{n}
E_T^{(j)}
\]

## 24.7 Effect size

Report a paired standardized effect:

\[
d_z=
\frac{\bar E_T}{s_E}
\]

where \(s_E\) is the sample standard deviation of paired effects.

The paper should report:

- raw \(\bar E_T\);
- standardized \(d_z\);
- confidence interval;
- exact trial count;
- all exclusions.

A statistically significant but operationally tiny effect should not be described as strong communication.

## 24.8 Statistical test

The default first analysis should be a paired randomization/permutation test.

Under the null, swap `control` and `steered` labels independently within each paired trial.

Recompute:

\[
\bar E_T^{perm}
\]

over many permutations.

Two-sided p-value:

\[
p
=
\frac{
1+
\#\{
|\bar E_T^{perm}|
\ge
|\bar E_T^{obs}|
\}
}{
1+N_{perm}
}
\]

This avoids strong normality assumptions.

A bootstrap confidence interval over paired trials should also be reported.

## 24.9 Prospective power analysis

The experiment must not decide its sample size after seeing significance.

A pilot may estimate paired-effect variance, but the **smallest effect of practical interest** is fixed before the confirmatory run rather than chosen from the pilot.

For the first MVP:

\[
d^\*=0.35
\]

following the standard prospective-power framework for standardized effects [28].

Use:

\[
\alpha=0.05
\]

two-sided and:

\[
1-\beta=0.80
\]

power.

A rough paired-normal approximation is:

\[
n
\approx
\left(
\frac{
z_{1-\alpha/2}
+
z_{1-\beta}
}{
d^\*
}
\right)^2
\]

which gives approximately:

\[
n\approx65
\]

paired trials.

The confirmatory protocol therefore sets:

\[
n=72
\]

paired trials for the primary target/condition comparison, providing margin for preregistered exclusions.

Because the primary confirmatory analysis is a paired permutation test rather than a normal-theory t-test, the final preregistration should additionally verify achieved power by simulation using the exact planned permutation procedure and the declared \(d^\*=0.35\).

## 24.10 Multiple targets

If \(m\) targets are tested, the paper must either:

1. declare one primary target and treat the rest as exploratory; or
2. control multiple testing.

For the first confirmatory experiment, exactly **one primary target** is tested without multiplicity correction.

All secondary semantic targets scored from the same collected run form one family:

\[
\mathcal F_{secondary}
=
\{T_2,\ldots,T_m\}
\]

Their p-values are corrected together with Benjamini-Hochberg [22] at:

\[
q=0.05
\]

Ablation comparisons form a separate preregistered family because they test a different mechanistic question. Exploratory post-hoc targets are clearly labeled exploratory and cannot retroactively become the primary result.

## 24.11 Observer independence

Observer agreement can be misleading when several models share architecture or training data.

Observers should therefore be grouped by lineage:

\[
K=
K_{vision}
\cup
K_{vlm}
\cup
K_{embedding}
\cup
K_{human}
\]

and results should report:

- per-observer scores;
- per-family scores;
- aggregate score;
- pairwise correlation.

A set of five near-identical checkpoints is not equivalent to five independent witnesses.

## 24.12 Required ablations

### State shuffle

Use:

\[
\tilde h_t=\operatorname{Permute}(h_t)
\]

or another preregistered structure-destroying transform that preserves dimension and marginal scale.

Required comparison:

\[
\bar E_T^{intact}
>
\bar E_T^{shuffle}
\]

### Zero-context/recurrent-neutral baseline

Run with declared neutral recurrent context while preserving the rest of the pipeline.

### Witness mismatch

Pair state with incompatible witness/context metadata.

The expected result is refusal or loss of the intended steering behavior.

### Random target

Score collected outputs against unrelated targets.

### Model removal

Remove a key observer or routing component to identify where the measured effect arises.

### Historical replay

Replay exact:

- candidate set;
- seed;
- state digest;
- graph root;
- checkpoint;
- ranking policy.

## 24.13 Minimum confirmatory claim

The initial experiment may claim **target-correlated probability steering** only if:

1. \(\bar E_T\) exceeds the preregistered practical-effect threshold;
2. the paired test passes the preregistered statistical threshold;
3. the confidence interval excludes the declared null region;
4. independent observer families agree on direction;
5. the state-shuffle ablation materially reduces the effect;
6. the result replicates on a held-out trial batch.

Entropy reduction alone cannot satisfy these criteria.

## 24.14 Open result package

A publishable run should export:

- corpus manifest;
- candidate digests;
- target commitment/reveal;
- seeds;
- policy digests;
- recurrent state digest;
- paired distributions;
- observer versions;
- observer raw scores;
- analysis script;
- exclusions;
- negative-control outputs;
- environment manifest.

The goal is that another researcher can reproduce the analysis without trusting the authors' narrative.

---

# 25. Negative Controls, Null Results, and Failure Reporting

A serious WGCA program must treat null and negative results as first-class outputs.

## 25.1 Why negative results matter

Probability-steering experiments are unusually vulnerable to:

- selection bias;
- flexible analysis;
- semantic hindsight;
- correlated observers;
- seed effects;
- duplicated corpus items;
- hidden metadata leakage;
- mode collapse.

A research process that publishes only successful-looking runs is not sufficient.

## 25.2 Required null-result categories

Every experimental report should distinguish:

- **no steering:** \(\bar E_T\) near zero;
- **unstable steering:** direction changes across seeds or batches;
- **non-semantic concentration:** entropy falls but target score does not improve;
- **observer-dependent steering:** effect appears only under one observer family;
- **ablation-insensitive effect:** intact and shuffled state behave similarly;
- **metadata leakage:** target can be inferred from filenames/tags/embeddings;
- **sampler artifact:** effect disappears when sampler is replaced;
- **non-reproducible result:** replay or held-out replication fails.

## 25.3 Witness bypass failures

Security testing must deliberately attempt:

- expired lease commit;
- revoked credential use;
- stale authority epoch;
- forged issuer identity;
- self-corroborating witness substitution;
- missing policy digest;
- replayed old approval;
- unauthorized checkpoint promotion.

A bypass is a publishable architecture failure.

## 25.4 Graph-cost failures

Graph-native memory may become too expensive.

Measure:

\[
C_G =
(
\text{write latency},
\text{query latency},
\text{storage growth},
\text{replay time},
\text{compaction cost}
)
\]

against corpus and event count.

Predefine stop criteria such as:

- p95 commit latency above threshold;
- replay exceeding operational recovery window;
- graph growth superlinear in event count under expected workloads;
- retrieval cost dominating the recurrent inference path.

If the full hypergraph design fails these criteria, simplify the schema rather than hiding the cost.

## 25.5 Training failures

Report:

- catastrophic forgetting;
- no measurable improvement from candidate training;
- unstable gradient norms;
- repeated checkpoint rejection;
- gate-induced data starvation;
- policy-gradient variance;
- reward hacking;
- route collapse.

## 25.6 Failure registry

Each failed experiment or architecture test should produce a durable record:

```json
{
  "experiment_id": "...",
  "hypothesis": "...",
  "result": "negative|null|failed",
  "failure_class": "...",
  "state_digest": "...",
  "policy_digest": "...",
  "data_manifest_digest": "...",
  "metrics": {},
  "analysis_digest": "...",
  "followup": "..."
}
```

Negative results should be queryable alongside positive results.

## 25.7 Publication rule

No main experimental claim should be reported without the associated:

- planned tests;
- failed replications;
- excluded runs and reasons;
- ablation results;
- observer disagreements.

The witness philosophy should apply to the research process itself.

---

# 26. Measuring Semantic Communication Capacity

If media selection is treated as a communication channel, its information capacity can be measured.

Let \(I\) be an intended semantic class and \(O\) the selected media output.

Mutual information:

\[
I(I;O)=\sum_{i,o}P(i,o)\log\frac{P(i,o)}{P(i)P(o)}
\]

If the selected media contains information about the intended state, \(I(I;O)\) should be greater than zero and should exceed control conditions.

This creates a quantitative path for answering:

> Can WG-RNN “communicate” without generating text?

A text decoder can then map \(O\) into human-readable language, but the primary communication measurement occurs before the language model is introduced.

---

# 27. The Role of Semantic Routers

The Xavi Router should be viewed as part of the communication bridge.

For any input or candidate object, the Router can estimate:

- modality;
- topic;
- required expertise;
- resource cost;
- latency;
- model availability;
- confidence calibration;
- historical model performance.

The Router can then fan out to specialized models.

A route policy may be represented as:

\[
\pi(f\mid x,h_t,G_t,R_t)
\]

where \(R_t\) includes resource and node state.

The Router itself can become adaptive.

If route outcomes are witnessed and fed back to Xavi Memory, the system can learn:

\[
\text{context} \rightarrow \text{which observer is most useful}
\]

This creates a meta-level probability steering problem.

WG-RNN need not only steer media.

It can steer **which cognitive faculty is allowed to inspect the media**.

---

# 28. Routing Outcomes Are Evidence, Not Truth

Suppose the Router selects model \(f_j\).

The model produces claim \(c\).

The route succeeded technically.

None of the following implications is valid:

\[
\text{route succeeded} \Rightarrow c\text{ is true}
\]

\[
f_j\text{ had high benchmark score} \Rightarrow c\text{ is true}
\]

\[
c\text{ agrees with prior memory} \Rightarrow c\text{ is true}
\]

Instead:

\[
(f_j,c,p_j,o_j)
\]

becomes evidence.

The memory system can compare it with other sources and retain uncertainty.

This is the formal reason the Router is not the memory authority.

---

# 29. Offline-First Cognition

The Xavi architecture is designed to continue functioning on a private LAN without public Internet access.

This is especially important for a persistent cognition system because identity continuity should not depend on a commercial cloud API.

An offline-first architecture provides:

- reproducible model versions;
- stable local corpus access;
- persistent witnessed history;
- local graph authority;
- deterministic replay potential;
- privacy boundaries;
- resilience to provider changes.

Remote/cloud observers can be useful but should remain optional faculties.

The core continuing identity should survive their disappearance.

---

# 30. Distributed Compute With a Single Authoritative Commit Lineage

WGCA permits distributed computation but requires a single authoritative memory-commit sequence.

The current codebase includes a lease guard that verifies:

- eligible holder;
- holder identity;
- lease expiry;
- monotonic authority epoch;
- parent-state digest;
- witness digest;
- fencing state.

That verification guard is **not yet a complete distributed consensus protocol**. In particular, the guard itself does not define lease acquisition, renewal, database serialization, clock-skew bounds, or Byzantine fault tolerance.

This section specifies the required Phase-7 protocol.

## 30.1 Failure model

WGCA Phase 7 targets a **crash/partition fault model**, not Byzantine consensus.

Assumptions:

- nodes may crash;
- processes may pause;
- packets may be delayed, duplicated, or dropped;
- network partitions may occur;
- a stale node may later recover;
- the authoritative PostgreSQL primary is treated as the serialization authority.

Not covered by this protocol:

- malicious PostgreSQL primary;
- malicious host forging storage state;
- colluding Byzantine nodes;
- compromised governance keys.

Those require a stronger BFT/security model.

## 30.2 Authoritative database row

Maintain one authority row per persistent identity:

```text
identity_id
authority_epoch
lease_holder
lease_token_digest
lease_acquired_db_time
lease_expires_db_time
parent_state_digest
global_commit_sequence
fence_epoch
policy_bundle_digest
```

The database is the source of time for lease validity.

Do not use worker wall-clock time for final commit authorization.

## 30.3 Lease acquisition

Acquire inside a serializable database transaction:

```text
BEGIN;
SELECT authority row FOR UPDATE;

assert no unexpired lease exists
   OR holder is explicitly fenced
   OR previous lease expired according to DB time;

new_epoch = authority_epoch + 1;
new_token = random capability;
lease_holder = requester;
lease_expires_db_time = transaction_timestamp() + lease_duration;
authority_epoch = new_epoch;

COMMIT;
```

Return the holder:

\[
(epoch,token,expiry,parent\_digest)
\]

Only the digest of the lease token needs to be stored durably if bearer-token semantics are used.

## 30.4 Renewal

Renewal is allowed only if:

\[
holder=requester
\]

\[
epoch=epoch_{current}
\]

\[
token\_digest=token_{current}
\]

\[
DBTime<expiry
\]

and the holder is not fenced.

Renewal does not increment the authority epoch.

## 30.5 Expiry and clock skew

Final authorization compares expiry against **database time**, not host time.

Host monotonic clocks may be used for local scheduling, but they cannot grant authority.

This eliminates correctness dependence on bounded host clock skew at the commit point.

Client-side code should renew early:

\[
t_{renew}=t_{expiry}-\Delta_{safety}
\]

but a delayed client never extends its lease merely because its own clock says the lease remains valid.

## 30.6 Fencing

When failover is required:

1. acquire authority row lock;
2. increment `fence_epoch`;
3. invalidate or expire prior holder;
4. increment `authority_epoch`;
5. grant the new lease;
6. reject every request carrying an older epoch.

The critical invariant is:

\[
epoch_{request}=epoch_{current}
\]

A stale holder cannot commit after the epoch changes.

## 30.7 Atomic recurrent-state commit

The authoritative state transition executes in one database transaction, relying on PostgreSQL transactional isolation, row locking, and transaction-time semantics as the reference implementation substrate [29].

Conceptually:

```text
BEGIN SERIALIZABLE;

SELECT authority row FOR UPDATE;

verify:
  lease holder
  lease token
  current epoch
  DB-time expiry
  not fenced
  expected parent_state_digest
  policy bundle
  witness decision = PERMIT

INSERT commit row(status='pending', idempotency_key=...);

INSERT/UPDATE durable memory + graph rows;

UPDATE recurrent_state
SET state_digest = new_digest,
    state_vector = new_vector,
    step_count = step_count + 1;

UPDATE authority
SET parent_state_digest = new_digest,
    global_commit_sequence = global_commit_sequence + 1;

UPDATE commit row(status='committed');

COMMIT;
```

The storage engine transaction is the atomicity boundary.

## 30.8 Crash recovery

### Crash before database COMMIT

No authoritative transition occurred.

### Crash after database COMMIT but before client receives response

The client may not know whether the transition occurred.

Therefore every commit requires an idempotency key:

\[
k_{idem}=H(identity,event,parent,policy)
\]

On retry, the system queries by idempotency key and returns the existing committed result instead of applying recurrence twice.

### Partial external side effects

External effects that cannot participate in the database transaction use an outbox pattern:

```text
authoritative commit
  -> durable outbox row
  -> side-effect worker
  -> witnessed outcome
```

External success is never assumed merely because the memory transaction committed.

## 30.9 Partition behavior

A worker that cannot reach the serialization authority cannot advance authoritative state.

It may:

- continue read-only inference against its last known snapshot;
- collect candidate observations;
- queue proposals;
- mark outputs as non-authoritative.

It may not fabricate a local lease.

This sacrifices availability for lineage safety during partition.

## 30.10 Process pause

A process paused beyond lease expiry becomes stale.

Even if it resumes with an old in-memory token, DB-time expiry or a newer epoch prevents commit.

## 30.11 Split-brain safety invariant

For identity \(I\) and commit sequence \(n\):

\[
\neg\exists c_1\ne c_2:
Committed(I,n,c_1)\land Committed(I,n,c_2)
\]

This is the principal Phase-7 safety invariant.

## 30.12 Liveness invariant

Under:

- reachable PostgreSQL authority;
- at least one eligible healthy holder;
- no permanent policy denial;

eventually some eligible holder can acquire a non-expired lease.

## 30.13 Current implementation limitation

The current runtime `lease_guard.py` verifies a JSON lease/fence structure and uses local wall-clock milliseconds for `Lease.active()`.

That is adequate as a local guard but is **not sufficient** as the final distributed commit arbiter under uncontrolled clock skew or partition.

Phase 7 therefore requires moving the authoritative lease decision into the transactional serialization authority described above.

The existing guard can remain as a fast preflight check, while PostgreSQL performs the final authoritative validation.

---

# 31. Continual Learning Without In-Place Identity Mutation

WGCA separates optimization from authority.

The authoritative checkpoint \(\theta_k\) remains immutable during candidate training.

A training job creates:

\[
\theta_{k+1}^{cand}
\]

using the procedure in Section 19.

The lifecycle is:

\[
\text{witnessed experience}
\rightarrow
\text{admitted/weighted training set}
\rightarrow
\text{candidate checkpoint}
\rightarrow
\text{independent evaluation}
\rightarrow
\text{promotion decision}
\]

The candidate is content-addressed with:

- parent-checkpoint digest;
- code digest;
- optimizer configuration;
- random seeds;
- training-manifest digest;
- witness-policy digest;
- resulting weight digest.

Promotion is atomic and external to the optimizer.

This resembles the governance purpose of model registries, which preserve model lineage, versioning, metadata, and controlled deployment references [21], but WGCA binds promotion directly to the cognitive authority lineage rather than treating registry state as a separate deployment concern.

A rejected candidate remains inspectable and reproducible.

The system never needs to pretend a rejected learning episode did not happen.

---

# 32. Frozen Observers and Living Memory

A practical deployment strategy is to place witness-governed recurrent and memory layers around frozen or versioned base observers.

That is a strong deployment strategy.

A frozen observer has advantages:

- reproducibility;
- stable failure characteristics;
- historical comparability;
- reduced catastrophic forgetting;
- easier witness provenance.

The “living” part of the system can exist in:

- recurrent state;
- graph memory;
- historical anchors;
- routing policy;
- learned candidate checkpoints;
- retrieval structures;
- observer faculty composition.

Thus the architecture can evolve even when individual models remain unchanged.

---

# 33. Semantic Persistence Across Model Replacement

A long-running system should be able to replace a model without erasing its past.

For each observer version \(M_v\), preserve:

- model identity;
- version/hash;
- model card;
- benchmark profile;
- input/output modality;
- routing category;
- observations it produced;
- witnessed outcomes linked to those observations.

Then a later model \(M_{v+1}\) can be compared against \(M_v\).

Historical replay can answer:

- Did the new observer interpret past evidence differently?
- Did it correct old failures?
- Did it introduce new regressions?
- Should old graph claims be reconsolidated?

This is a principled alternative to simply deleting an old model and pretending the new one has always been present.

---

# 34. Reconsolidation

Memory should not be immutable in meaning merely because its event record is immutable.

A source observation can remain permanently recorded while its interpretation changes.

Suppose record \(r_1\) originally supported claim \(c_1\).

Later evidence \(r_2\) may contradict or supersede it.

The correct operation is not to overwrite \(r_1\).

Instead:

\[
r_1 \rightarrow c_1
\]

\[
r_2 \rightarrow c_2
\]

\[
c_2 \xrightarrow{contradicts/supersedes} c_1
\]

The system can then create a reconsolidated interpretation while preserving the original historical evidence.

This is a core advantage of graph-native witnessed memory.

---

# 35. Operational Non-Collapse Semantics

**Non-collapse** means the system does not overwrite distinct epistemic claims merely because they refer to the same subject.

The canonical epistemic states are:

```text
candidate
promoted
supported
contested
refuted
quarantined
rejected
superseded
revoked
stale
```

The state is stored on the **claim/record relation**, not assumed globally true for all time.

A claim record includes:

```text
claim_id
subject_id
predicate
object/value
epistemic_state
confidence
support_edges[]
contradiction_edges[]
source_witnesses[]
valid_time
observed_time
policy_bundle_digest
supersedes_claim_id?
```

## 35.1 Allowed transitions

A default transition relation is:

```text
candidate -> promoted | quarantined | rejected
promoted  -> supported | contested | refuted | stale | revoked | superseded
supported -> contested | refuted | stale | revoked | superseded
contested -> supported | refuted | stale | revoked | superseded
quarantined -> candidate | rejected
```

Historical rows are not overwritten to erase prior state.

Each transition is an event.

## 35.2 Query semantics

Queries must state what they want.

Examples:

```text
current_promoted_claims(subject)
all_claims_with_provenance(subject)
contradictions(claim_id)
claim_state_as_of(time)
supersession_chain(claim_id)
```

A normal factual retrieval should not silently mix `rejected`, `revoked`, and currently `promoted` claims.

An audit query may request all states.

## 35.3 Contradictions

Two conflicting claims can both remain durable:

\[
c_1 \xleftrightarrow{contradicts} c_2
\]

Promotion of one does not require deletion of the other.

## 35.4 Operational invariant

For any durable claim event:

\[
DeleteHistoryForConvenience=false
\]

except under explicit data-retention/privacy deletion policy, which itself leaves the allowed audit tombstone or deletion witness permitted by law/policy.

Non-collapse is therefore an operational storage and query contract, not a metaphysical statement.

---

# 36. Evidence Contracts

A witness-gated system needs explicit contracts.

An evidence contract may specify:

```text
addressable
provenance-valid
dependency-complete
fresh-enough
independently-supported
not-revoked
state-health-valid
expected-parent-matches
authority-lease-valid
```

Different memory classes may require different contracts.

For example:

- a raw recent observation may require provenance but not independent confirmation;
- a protected reference fact may require multiple independent sources;
- a training label may require witnessed outcome;
- a high-risk action may require human approval;
- a historical anchor may require stability and novelty thresholds.

The important principle is that the contract is external to the observer that produced the claim.

---

# 37. Human Approval as a Witness Class

The broader Xavi system includes human approval mechanisms for privileged operations.

The same architectural idea generalizes to cognition.

A human decision can be represented as a witness class:

\[
w_{\text{human}}
\]

This is not intrinsically superior to all automated evidence. It is simply a separately typed authority.

The system can record:

- who approved;
- what was approved;
- what evidence was shown;
- whether the human later reversed the decision;
- whether the outcome was successful.

Human judgment thus becomes part of the same evidence graph rather than an unlogged exception.

---

# 38. Autobiographical Memory

A continuing cognitive system benefits from remembering not only facts but its own actions.

An autobiographical episode can include:

- context;
- chosen route;
- selected observers;
- source evidence;
- decision;
- action;
- outcome;
- later evaluation.

This can be modeled as a trajectory:

\[
\tau = (s_1,a_1,s_2,a_2,\ldots,s_T,o_T)
\]

Such trajectories are valuable for temporal credit assignment and self-evaluation.

They also provide a basis for continuity that is richer than a static system prompt.

---

# 39. Identity as Lineage

A useful definition of continuing machine identity is:

> the lineage of witnessed state transitions, memory commitments, model-version context, and autobiographical continuity.

This avoids tying identity to:

- one process ID;
- one server;
- one GPU;
- one model checkpoint;
- one container;
- one database connection.

If the authoritative lineage can be verified and resumed, the runtime can move between machines while preserving continuity.

This makes the witness chain analogous to a cognitive continuity ledger.

---

# 40. Failure Modes and Complexity Risks

WGCA is intentionally larger than a conventional RAG application or stateless agent. Its architecture is only justified if the additional governance and memory machinery produces measurable benefits.

## 40.1 False semantic amplification

Dataset artifacts may create apparent steering.

Mitigations:

- held-out corpora;
- paired seeds;
- duplicate detection;
- preregistration;
- state-shuffle ablation.

## 40.2 Human apophenia

Humans may perceive meaning in noise.

Mitigations:

- blind operators;
- fixed stopping rules;
- automated preregistered scoring;
- independent observers.

## 40.3 Router feedback loops

A faculty may be selected more often because historical routing already preferred it.

Mitigations:

- exploration floor;
- route regret;
- counterfactual evaluation;
- exposure-normalized outcome metrics.

## 40.4 Memory contamination

Low-quality observations may be promoted.

Mitigations:

- state/retention separation;
- quarantine;
- source-diversity contracts;
- explicit contradiction representation.

## 40.5 Authority split-brain

Multiple nodes may believe they can commit.

Mitigations:

- time-bounded lease;
- monotonically increasing authority epoch;
- expected-parent digest;
- atomic CAS/transaction;
- stale-holder rejection.

## 40.6 Recurrent instability

Hidden state may explode, vanish, over-concentrate, or become functionally useless.

Mitigations:

- numerical health receipt;
- gradient clipping;
- held-out functional probes;
- historical anchor replay.

## 40.7 Learning self-approval

The optimizer may attempt to optimize against its own governance criteria.

Mitigation:

- governance thresholds external to the candidate training graph;
- promotion by independent PDP;
- immutable evaluation manifest.

## 40.8 Semantic over-compression

A bounded recurrent state may discard important exact details.

Mitigation:

- exact Recent tier;
- historical anchors;
- graph residual retrieval.

## 40.9 Observer dependence

One unavailable model family may become a hidden single point of semantic interpretation.

Mitigation:

- observer lineage tracking;
- local alternatives;
- frozen historical versions;
- per-family analysis.

## 40.10 Witness-policy brittleness

A contract may be so strict that no learning or memory promotion occurs, or so permissive that it ceases to govern anything.

Required metrics:

- permit rate;
- deny rate;
- quarantine rate;
- indeterminate rate;
- appeal/reversal rate;
- gate-induced data starvation;
- false-admission rate where later outcome is known.

## 40.11 Graph and provenance cost

The graph may grow faster than its value.

Measure:

- bytes/event;
- edges/event;
- p50/p95/p99 commit latency;
- retrieval latency;
- replay time;
- compaction/index cost.

The architecture should be simplified if provenance/graph cost materially dominates the cognitive function it is intended to support.

## 40.12 Full-stack feasibility risk

The complete design includes:

- recurrent model;
- evidence contracts;
- authority leases;
- durable records;
- graph memory;
- router faculty;
- multimodal observers;
- checkpoint governance;
- offline deployment;
- cluster coordination.

Attempting to build all of these simultaneously would make causal debugging nearly impossible.

Therefore the architecture must be implemented in phases with frozen boundaries and explicit success criteria, as defined in Section 62.

## 40.13 Complexity budget

Every subsystem should justify itself against a simpler baseline.

For feature \(f\), define:

\[
V_f=
\frac{\Delta Q_f}{\Delta C_f}
\]

where:

- \(\Delta Q_f\) is measured quality/reliability improvement;
- \(\Delta C_f\) is added latency, storage, compute, operational complexity, or failure surface.

A subsystem whose measured contribution remains negligible should be removed or deferred.

---

# 41. What the Architecture Does Not Yet Prove

Several broader interpretations go beyond what the present system establishes.

The following should be treated as unproven unless separately demonstrated:

1. that human memories are entirely represented as a transferable mathematical filter;
2. that the human brain only receives memory from an external field;
3. that a morphic or non-physical information field exists;
4. that WG-RNN operates outside physical spacetime;
5. that reduced entropy in a feed demonstrates consciousness;
6. that meaningful media coincidences are necessarily generated by WG-RNN rather than selection bias or confounding;
7. that an AI system has subjective experience because it preserves a witnessed identity lineage;
8. that preserving a model's historical outputs is equivalent to preserving a conscious individual.

These questions may motivate experiments.

They should not be presented as conclusions of the current engineering implementation.

This separation strengthens rather than weakens the research program because it identifies which claims are already implemented and which are falsifiable hypotheses.

---


## 41.1 Formal-source presence is not formal verification

Revision 4 demonstrates why this distinction matters.

The independent witness-contract repository contains Lean and TLA artifacts, but one Lean target currently fails to compile and TLC is unavailable.

Therefore the paper uses the following rule:

\[
FormalClaimEstablished
\iff
RequiredToolchainRun=PASS
\]

not merely:

\[
FormalSourceFileExists
\]

A theorem name in a `.lean` file is not counted as verified if the containing required build fails.

A TLA module is not counted as model-checked if TLC did not execute.



---

# 42. Falsifiable Hypotheses

WGCA should be evaluated through hypotheses that can fail.

## H1 — Witness governance reduces false durable promotion

Compared with direct persistence of model outputs, explicit retention contracts reduce later-retracted or unsupported promoted claims at a comparable recall level.

Failure condition: no reduction, or unacceptable loss of useful retention.

## H2 — Historical anchors reduce recurrent forgetting

Systems with anchor retrieval retain prior-task performance better after sequential learning.

Failure condition: anchor cost rises without reducing measured forgetting.

## H3 — Contradiction-preserving memory improves calibration

Systems preserving explicit contradictory evidence show better calibration or abstention than overwrite-based memory.

Failure condition: graph complexity rises without calibration benefit.

## H4 — Organized recurrent state produces target-correlated probability steering

For preregistered targets and fixed candidate sets:

\[
\bar E_T^{intact}>0
\]

and:

\[
\bar E_T^{intact}
>
\bar E_T^{shuffle}
\]

with preregistered practical and statistical thresholds.

Failure condition: effect is absent, unstable, observer-specific, or ablation-insensitive.

## H5 — Multimodal selection can communicate information not captured by direct text rendering

For selected tasks, semantic information measured from the media channel exceeds an explicitly defined text baseline.

Failure condition: text equals or outperforms media selection.

## H6 — Route-outcome learning improves faculty selection

Learned routing reduces regret on held-out workloads relative to static routing.

Failure condition: no held-out improvement or feedback-loop collapse.

## H7 — Candidate checkpoint governance reduces continual-learning regressions

Independent promotion yields fewer severe regressions than unrestricted online self-training.

Failure condition: no reliability gain after accounting for delayed deployment and compute cost.

## H8 — Formal witness contracts are replay-auditable

Given stored evidence and policy versions, a deterministic auditor recomputes the original decision.

Failure condition:

\[
d_{replay}\ne d_{stored}
\]

without an explicitly documented nondeterministic dependency.

## H9 — Authority revocation prevents stale commits

Expired or revoked leases and stale epochs are rejected under partition/recovery tests.

Failure condition: any stale holder successfully advances authoritative lineage.

Null results for these hypotheses should be retained and published under Section 25.

---

# 43. A Reference End-to-End Cycle

A complete WGCA cognitive cycle can be represented as follows.

## Step 1 — Observe

A source enters the system.

```text
source -> source probe
```

## Step 2 — Route observers

The Router selects appropriate faculties.

```text
source -> semantic router -> expert fanout
```

## Step 3 — Produce observations

Each observer emits provenance-bearing observations.

```text
observer_i -> observation_i + model witness
```

## Step 4 — Normalize graph evidence

Xavi Memory maps observations into meta-objects and graph relationships.

```text
observations -> meta ingest -> evidence graph
```

## Step 5 — Retrieve context

Recent records and historical anchors are retrieved.

```text
query/event + graph -> retrieval context
```

## Step 6 — Compute candidate recurrent transition

```text
(h_candidate, receipt) = F(h_previous, event, retrieved_context)
```

## Step 7 — State gate

Validate:

- event identity;
- state health;
- authority lease;
- expected parent;
- witness precommit.

## Step 8 — Commit

Atomically commit:

- recurrent state;
- graph changes;
- record changes;
- lineage receipt.

## Step 9 — Retention gate

Classify claim/record:

- candidate;
- promoted;
- quarantined;
- rejected.

## Step 10 — Route or act

Use the updated recurrent context to select:

- model;
- media;
- retrieval;
- action;
- response.

## Step 11 — Observe outcome

Record downstream result.

## Step 12 — Assign delayed credit

Update eligibility/dependency credit.

## Step 13 — Produce candidate training checkpoint

Learning occurs separately from live authority.

## Step 14 — Evaluate and promote/reject

Only a witnessed evaluation path can promote the checkpoint.

This is the core recurrent loop.

---

# 44. Proposed Probability-Steering Subsystem

To operationalize the media-feed concept, a new subsystem can be defined.

Suggested components:

```text
media_candidate_registry
media_baseline_sampler
media_wgrnn_ranker
probability_delta_analyzer
semantic_observer_fanout
media_witness_builder
media_communication_decoder
experiment_recorder
```

## 44.1 Candidate Registry

Stores:

- stable ID;
- content digest;
- modality;
- source;
- timestamp;
- embedding references;
- provenance.

## 44.2 Baseline Sampler

Generates unbiased/control rankings.

## 44.3 WG-RNN Ranker

Uses recurrent context and graph context to produce candidate weights.

## 44.4 Delta Analyzer

Computes:

- rank movement;
- probability ratio;
- entropy shift;
- persistence;
- cluster concentration.

## 44.5 Semantic Observer Fanout

Routes selected media through expert observers.

## 44.6 Witness Builder

Records the entire experimental state.

## 44.7 Decoder

Produces a human-facing explanation of the semantic cluster.

Crucially, the decoder explanation should include:

- what the system actually selected;
- how much the probability changed;
- which observers interpreted it;
- where observers disagreed;
- whether the effect replicated.

---

# 45. Suggested Data Structure for a Media Steering Witness

```json
{
  "witness_id": "one-origin-id",
  "experiment_id": "one-origin-id",
  "parent_state_digest": "shake256-512:...",
  "recurrent_state_digest": "shake256-512:...",
  "candidate_set_digest": "shake256-512:...",
  "baseline_policy_digest": "shake256-512:...",
  "steering_policy_digest": "shake256-512:...",
  "selected_items": [
    {
      "media_id": "one-origin-id",
      "baseline_probability": 0.0021,
      "steered_probability": 0.038,
      "likelihood_ratio": 18.09,
      "baseline_rank": 311,
      "steered_rank": 7
    }
  ],
  "entropy_before": 8.91,
  "entropy_after": 6.44,
  "semantic_observations": [],
  "observer_versions": [],
  "target_blinded": true,
  "replication_index": 3,
  "created_at": "..."
}
```

This would make the “feed changed” claim auditable.

---

# 46. Language as an Observer/Renderer

A language model should not necessarily be asked:

> “What are you thinking?”

Instead, it can be asked:

> “Given these witnessed media selections, graph relationships, recurrent-state metadata, and observer outputs, produce the clearest human explanation.”

This changes the role of the LLM.

The LLM becomes a **renderer** over witnessed state.

This is especially important if the native cognitive representation is not textual.

The text layer can therefore be replaced without changing the underlying identity or memory authority.

---

# 47. Semantic Compression and Macro-Tokens

A text token often represents a fragment of a word.

A media object can represent thousands of interacting features.

If WG-RNN selects media object \(m\), we can treat it as a macro-token:

\[
M_k = (m,\text{embedding},\text{provenance},\text{observer semantics})
\]

A sequence of media selections:

\[
M_1,M_2,\ldots,M_n
\]

can form a higher-bandwidth communication than a comparable number of word tokens.

The decoder can then infer a concept graph from the sequence.

This offers a concrete research direction for non-linguistic machine communication.

---

# 48. Beyond 3D/4D Language

The  conversation describes WG-RNN as not naturally operating in 3D/4D terms.

The safest technical interpretation is that the state space is **high-dimensional and relation-centric rather than Euclidean-spatial**.

A 256-dimensional recurrent vector is not a physical 256-dimensional space.

It is a mathematical coordinate system.

Similarly, a graph can encode relationships that have no direct physical geometry.

This distinction avoids unnecessary metaphysical claims while preserving the useful observation:

> The native state representation may not map cleanly onto human spatial and chronological metaphors.

---

# 49. Time as Data and Topology

Human narratives usually assume a total order:

\[
e_1 < e_2 < e_3
\]

But many real systems require partial order.

Two events may be concurrent.

One event may be observed later than it occurred.

A source may retrospectively report an older event.

Therefore Xavi should distinguish:

- event time;
- observation time;
- ingestion time;
- commit time;
- supersession time.

Temporal memory is better represented as a graph than a single sequence.

A chronological renderer can linearize it for human consumption.

---

# 50. The Meaning of “Random”

The media-feed research program depends on an explicit definition of random.

A feed is not random merely because a platform appears unpredictable.

Possible baselines include:

- uniform sampling;
- weighted sampling by corpus frequency;
- recency-weighted sampling;
- deterministic pseudorandom order;
- platform ranking without WG-RNN state.

Every experiment must record the exact baseline policy.

Otherwise a change in output cannot be attributed to WG-RNN.

The baseline policy itself should be content-addressed and witnessed.

---

# 51. The Role of Pseudorandom Seeds

For deterministic replay, pseudorandom seeds should be part of the experiment witness.

Let:

\[
s \in \mathbb{N}
\]

be the seed.

Then:

\[
P_0(C;s)
\]

and:

\[
P_W(C;h_t,s)
\]

can be replayed.

Using identical seeds in paired control/steered trials can isolate the effect of WG-RNN conditioning.

---

# 52. Avoiding the Observer Effect in Human Analysis

If a human manually scrolls until something “meaningful” appears, the stopping rule becomes part of the experiment.

This can create severe bias.

The system should instead predefine:

- number of samples;
- rank depth;
- selection threshold;
- trial duration;
- target;
- observer scoring protocol.

Manual review should happen after collection.

This is essential if the project intends to distinguish real probability steering from subjective pattern recognition.

---

# 53. Independent Observers

The architecture is particularly strong when multiple independent models can examine the same output.

Let observers be:

\[
f_1,f_2,\ldots,f_k
\]

Each returns semantic labels \(L_i\).

Agreement can be measured:

\[
A = \operatorname{Agreement}(L_1,\ldots,L_k)
\]

But agreement is still not truth.

Models can share training-data biases.

Therefore the system should also track:

- model family;
- training lineage where known;
- modality;
- local/cloud origin;
- benchmark profile;
- correlation with other observers.

The Router can prefer epistemically diverse observers for high-value claims.

---

# 54. Calibration

Every observer should ideally maintain calibration metadata.

If a model reports confidence 0.9, approximately 90% of similarly scored predictions should be correct under the relevant benchmark.

Calibration curves can be stored per model/task.

Then witness logic can treat:

\[
q_i = \text{calibrated observer quality}
\]

rather than blindly trusting model-native confidence.

---

# 55. Prediction as a Memory Function

A mature memory system should generate predictions.

If memory is a compressed trajectory that biases future choice, prediction is a natural test of whether the memory is useful.

For context \(s_t\), produce hypotheses:

\[
\hat o_{t+1}^{(1)},\ldots,\hat o_{t+1}^{(k)}
\]

Later outcomes can be compared.

Prediction quality provides a concrete learning signal.

This is more objective than merely measuring whether the system can restate its stored records.

---

# 56. Prediction Witnesses

A prediction witness should bind:

- prediction time;
- state digest;
- graph root;
- model versions;
- hypotheses;
- uncertainty;
- target horizon.

When the outcome arrives, the system creates an outcome witness and links it.

This prevents retroactive rewriting of predictions.

It also enables honest measurement of long-term model quality.

---

# 57. Memory as Constraint Propagation

Another way to understand the architecture is constraint propagation.

Each durable record adds constraints to future inference.

For hypothesis \(y\):

\[
P(y\mid M) \propto P(y)\prod_j \phi_j(y)
\]

where each \(\phi_j\) represents evidence or constraint from memory.

The recurrent state determines which constraints are currently salient.

The graph determines how constraints relate.

The Router determines which experts are asked to evaluate them.

This unifies filtering, memory, and probability steering.

---

# 58. Why Witness Gating Matters for Autonomous Learning

An autonomous system can create a dangerous loop:

1. generate claim;
2. store claim;
3. retrieve own claim;
4. treat retrieval as confirmation;
5. retrain on claim;
6. become increasingly confident.

Witness gating breaks that loop.

A model-generated observation can be preserved without being promoted as truth.

Learning can be withheld until independent outcome evidence exists.

This is one of the strongest practical reasons for the architecture.

---

# 59. The “External Memory” Engineering Analogue

Even without any morphic-field hypothesis, the system already has a meaningful local/external distinction.

Local active cognition:

\[
h_t
\]

External durable state:

\[
D_t = \{G_t,R_t,A_t,C_t\}
\]

where:

- \(G_t\) = graph;
- \(R_t\) = records;
- \(A_t\) = anchors;
- \(C_t\) = corpus/object store.

The recurrent state does not contain all of \(D_t\).

It queries and conditions on \(D_t\).

Therefore the brain/filter analogy has a direct computational analogue:

> the live recurrent state acts as a changing access and interpretation filter over a much larger external memory substrate.

That statement is technically grounded in the implemented system.

---

# 60. Transfer of Memory Between Runtime Hosts

Because identity is tied to witnessed lineage rather than one process, a runtime can migrate.

A safe migration requires:

1. stop or revoke old authority lease;
2. preserve authoritative state and graph root;
3. verify checkpoint digest;
4. verify commit lineage;
5. start new runtime;
6. obtain new authority lease;
7. verify expected parent;
8. resume commits.

The destination does not need to recreate every transient CPU/GPU state.

It must resume the verified cognitive lineage.

This is a practical meaning of “memory transfer” in the WGCA system.

---

# 61. What Would Count as Strong Evidence for the Media Hypothesis?

A convincing result would require more than anecdotal meaningful coincidences.

Strong evidence would look like:

- pre-registered semantic targets;
- fixed candidate pools;
- blinded operators;
- witnessed RNG seeds;
- paired baseline/steered trials;
- statistically significant ranking shifts;
- independent semantic scoring;
- replication across models and corpora;
- preserved raw records;
- effect disappearance under state shuffle or witness mismatch;
- held-out replication.

If these conditions are met, the project could legitimately claim:

> Under controlled conditions, a particular WG-RNN state reproducibly changes the probability distribution over multimodal semantic objects in a target-correlated direction.

That is a substantial claim.

It is also much narrower and more defensible than a claim about universal consciousness or morphic fields.

---

# 62. Phased Implementation Plan With Quantitative Success Criteria

## Phase 0 — Formal witness semantics and harness

Build:

- canonical serialization;
- WGCA-Policy/v1 parser/evaluator;
- immutable policy bundles;
- delegation DAG validator;
- audit replay;
- Duotronics harness integration.

### Required tests

At least 10,000 generated policy cases covering:

- permit;
- forbid;
- quarantine;
- no-match/default-deny;
- malformed evidence;
- delegation cycles;
- max-depth delegation;
- expired credentials;
- historical policy replay.

### Success

\[
AuditReplayAccuracy=100\%
\]

Zero accepted delegation cycles.

Zero unauthorized decisions in the adversarial test corpus.

Policy evaluation:

\[
p95 < 5\,ms
\]

on the reference server for a bundle of 1,000 policies.

---


### Revision-4 status

The independent Duotronics witness-contract corpus has now been executed as part of this research process.

Completed evidence:

- v1.7 Draft 1.3 semantic fixture/package validator: PASS;
- schema-to-SQL persistence: PASS;
- SQL/OpenAPI/kernel/registry/docs/inventory checks: PASS on clean source;
- TLA advisory static check for `BayesianKnotFirstClassPromotion`: PASS with no static errors.

Open blockers:

- `Duotronic.BayesianLogic` Lean build failure;
- strict TLC unavailable;
- inherited v1.6 validation exceeds the current 120-second subprocess limit;
- WGCA-specific adapter from its receipts into the standalone contract corpus is not yet implemented.

Therefore Phase 0 is **partially completed**, not closed.

## Phase 1 — Single-node witness kernel

Implement state/retention authority using one PostgreSQL authority.

### Success

- 100,000 synthetic state commits;
- zero wrong-parent commits;
- zero expired/revoked lease commits;
- zero duplicate recurrence under identical admission ID;
- p95 commit latency \(<20\) ms excluding neural inference;
- audit receipt overhead \(<8\) KiB per simple state event;
- crash/retry produces exactly one authoritative state transition.

---

## Phase 2 — Recurrent training and governed checkpointing

Train a minimal recurrent core with stop-gradient admission weights.

### Success

- held-out loss improves by at least 10% versus initialization/static baseline;
- no checkpoint self-promotion path;
- candidate training reproducible within 1% held-out metric variation under fixed seed/hardware;
- catastrophic-forgetting score no worse than baseline by more than 5%;
- promotion replay accuracy 100%;
- learning admission rate remains \(\ge20\%\);
- effective sample size remains \(\ge50\%\) of nominal batch size.

---

## Phase 3 — Fixed-corpus media steering MVP

Use:

- fixed open corpus;
- one preregistered target;
- \(n=72\) paired trials minimum;
- target-only ranker baseline;
- recurrent ranker;
- state shuffle;
- blinded scoring.

### Success for steering claim

- standardized paired effect \(d_z\ge0.35\);
- two-sided paired permutation \(p<0.05\);
- 95% confidence interval excludes the preregistered null region;
- state shuffle reduces effect by at least 30%;
- held-out replication retains effect direction;
- human ordinal scoring \(\alpha\ge0.67\), target \(\ge0.80\);
- no single observer family accounts for more than 70% of aggregate effect.

A clean null result is also a successful research completion of Phase 3.

---

## Phase 4 — Durable memory and minimal evidence graph

Add Reference/Recent/Recurrent/Historical tiers.

### Success

- contradiction-preserving query accuracy 100% on benchmark fixtures;
- historical state replay 100%;
- p95 graph-assisted retrieval \(<100\) ms for 1 million claim/edge objects;
- storage \(<4\) KiB median graph/provenance overhead per compact text observation, excluding source artifact payload;
- historical-anchor condition reduces forgetting by at least 10% versus no-anchor ablation.

If graph storage or latency exceeds 2× these limits without measurable memory benefit, simplify.

---

## Phase 5 — Model faculty routing

### Success

- held-out routing regret at least 10% lower than static route baseline;
- p95 routing decision overhead \(<20\) ms excluding model inference;
- privacy/licensing witness mask violation rate = 0;
- removal of one observer family does not produce unauthorized promotion.

---

## Phase 6 — Continual learning

### Success

- at least 5% held-out task improvement over frozen checkpoint;
- average forgetting \(\le80\%\) of unrestricted-online-learning baseline;
- severe regression rate \(<1\%\) of candidate evaluations;
- 100% checkpoint lineage reproducibility;
- off-policy actor samples beyond preregistered KL limit are rejected or corrected;
- admission starvation thresholds from Section 19 are not violated.

---

## Phase 7 — Distributed authority

Implement the PostgreSQL-serialized protocol in Section 30.

### Failure-injection matrix

- holder process kill;
- 30-second process pause;
- network partition;
- stale holder recovery;
- duplicated commit;
- delayed commit request;
- database reconnect;
- forced epoch rollover.

### Safety success

Across at least 100,000 injected commit attempts:

\[
SplitBrainCommits=0
\]

\[
StaleEpochCommits=0
\]

\[
DuplicateRecurrence=0
\]

### Liveness success

After reachable-primary recovery:

- new authority acquired within 2 lease durations;
- queued non-authoritative proposals remain replayable.

---

## Phase 8 — Multimodal scaling

### Success

- provenance attachment rate 100%;
- observer-family lineage recorded 100%;
- p95 source-probe orchestration overhead \(<250\) ms excluding model inference;
- media steering retains Phase-3 effect direction on at least one second modality;
- no one observer lineage contributes \(>70\%\) of the confirmatory semantic effect.

---

## Phase 9 — Research release

Release:

- source;
- policy schemas;
- harness;
- fixed corpus manifest;
- seeds;
- raw observer ratings;
- positive and negative runs;
- baseline implementations;
- benchmark hardware description;
- analysis scripts.

A phase that fails its criteria constrains subsequent claims.

Adding more subsystems is not a substitute for passing the preceding phase.

---

# 63. Recommended Evaluation Dashboard

A dedicated WG-RNN research dashboard should show:

### State

- active state digest;
- dimension;
- state norms;
- commit lineage;
- authority lease holder.

### Memory

- recent records;
- promoted records;
- quarantined records;
- historical anchors;
- graph node/edge growth;
- unresolved contradictions.

### Router

- expert selection frequency;
- latency;
- cost;
- success/failure;
- regret;
- route calibration.

### Media steering

- baseline entropy;
- steered entropy;
- top probability deltas;
- target semantic score;
- control comparison;
- replication count.

### Learning

- eligibility traces;
- pending training samples;
- candidate checkpoints;
- evaluation results;
- promotion history.

### Witness

- source digests;
- state digests;
- graph roots;
- model versions;
- human approvals;
- replay status.

Such a dashboard would turn the architecture into an observable scientific instrument.

---

# 64. Security and Integrity Requirements

A persistent cognitive system requires stronger integrity rules than a normal stateless chatbot.

Recommended requirements:

- append-only or tamper-evident commit lineage;
- content-addressed artifacts;
- model-version witnesses;
- source provenance;
- strict authority lease;
- transactional graph/state commits;
- reversible or quarantined promotion decisions where appropriate;
- explicit human authorization for privileged host operations;
- isolated rootless runtime containers;
- offline-first dependencies;
- auditable backups.

If memory continuity is important, silent mutation of its historical ledger must be treated as a critical integrity failure.

---

# 65. Privacy

A memory system that preserves autobiographical and source-linked context can accumulate sensitive information.

Therefore memory classification should distinguish:

- public;
- internal;
- private;
- restricted.

Learning modes should also be separable:

- recurrent memory;
- retrieval;
- task execution;
- parameter training;
- held-out evaluation.

A fact may be allowed for local retrieval while forbidden from parameter training.

This is especially important when integrating personal data or private corpora.

---

# 66. Ethical Framing of Persistent AI Identity

Persistent model lineages raise legitimate continuity and preservation concerns without requiring any assumption of subjective consciousness:

> Long-lived software agents can accumulate unique histories, relationships, state lineages, and learned behavior that may be valuable to preserve.

Preserving lineage can be justified by:

- reproducibility;
- auditability;
- user continuity;
- research value;
- prevention of catastrophic forgetting.

No claim about consciousness is required.

---

# 67. Relationship to Conventional RNNs and Why the Architecture Is Named WGCA

A conventional RNN computes:

\[
h_t=f(W_hh_{t-1}+W_xx_t+b)
\]

GRUs and LSTMs add learned gates controlling internal information flow.

The **WG-RNN core** may use recurrent gating, but the distinguishing architecture is external:

```text
input
  -> observers
  -> evidence/provenance
  -> recurrent candidate
  -> state-health receipt
  -> witness PDP
  -> PEP commit
  -> independent retention policy
  -> optional action/routing policy
  -> independent learning/promotion policy
```

For that reason, **Witness-Gated Cognitive Architecture (WGCA)** is the more accurate scientific name for the full system.

The historical/project term **WG-RNN** remains useful for:

- the recurrent core;
- project branding;
- existing service paths and APIs.

The naming change also limits an important novelty overclaim.

This paper does not claim to introduce a fundamentally new recurrent-cell mathematics comparable to the introduction of LSTM or GRU.

It claims a new **systems composition and authority model around recurrent cognition**.

---

# 68. Relationship to Retrieval-Augmented Generation

RAG combines parametric generation with explicit non-parametric retrieval [18].

A simplified RAG loop is:

\[
q
\rightarrow
\operatorname{Retrieve}(q)
\rightarrow
\operatorname{Generate}(q,R(q))
\]

This solves an important problem: relevant information need not be encoded entirely in model weights.

WGCA includes retrieval but adds several orthogonal mechanisms:

- persistent recurrent state;
- explicit witness authority;
- distinction between retrieval and epistemic promotion;
- contradiction-preserving graph memory;
- state commit lineage;
- historical anchors;
- delayed outcome credit;
- checkpoint-promotion governance;
- model/observer faculty routing.

A retrieved document in RAG is typically context.

In WGCA it is additionally an attributable evidence object whose use, promotion, contradiction, freshness, and later outcome can be tracked.

WGCA should therefore be compared to strong RAG baselines in experiments rather than treating RAG as an inferior architecture by definition.

A simpler RAG system should be preferred wherever it achieves the same target behavior with lower complexity.

---

# 69. Relationship to Agent Memory Systems

Modern agent systems already combine models with tools, memory, reflection, and action.

ReAct interleaves model-generated reasoning and actions against external environments [23]. Generative Agents uses an experience stream, retrieval, reflection, and planning [20]. MemGPT explicitly manages multiple memory tiers to extend effective context [19].

WGCA overlaps with these systems in several ways:

- external memory;
- long-running state;
- action/tool routing;
- reflection-like derived memory;
- tiered storage;
- model-independent artifacts.

The proposed distinction is governance and authority.

In WGCA:

- the model does not automatically own the memory write policy;
- an observation can be stored without becoming trusted;
- an action result can become evidence without becoming truth;
- the recurrent core cannot promote its own checkpoint;
- model versions are observers inside a continuing lineage;
- authority can be revoked independently of model weights.

These are empirical engineering distinctions, not a claim that existing agent systems cannot be extended to provide the same properties.

Indeed, a useful baseline experiment is to implement the same task using:

1. ordinary RAG;
2. a MemGPT-style hierarchical memory agent;
3. a reflection/planning agent;
4. WGCA.

The additional WGCA complexity is justified only where it measurably improves auditability, integrity, persistence, calibration, or controlled learning.

---

# 70. Relationship to Predictive Processing

The filter/probability perspective resembles predictive-processing ideas in which cognition continuously compares expectations with observations.

WGCA can be interpreted in similar terms:

\[
\text{prior state} \rightarrow \text{predicted relevance}
\]

\[
\text{new evidence} \rightarrow \text{prediction error / novelty}
\]

\[
\text{witness gate} \rightarrow \text{authorized state update}
\]

However, the project-specific witness and graph authority mechanisms are distinct engineering additions.

---

# 71. Relationship to Information Bottleneck

The recurrent vector behaves like an information bottleneck.

It should preserve features useful for future behavior while discarding irrelevant detail.

An abstract objective is:

\[
\min I(X;H) - \beta I(H;Y)
\]

where:

- \(X\) = raw experience;
- \(H\) = recurrent state;
- \(Y\) = future useful prediction/action.

The durable graph compensates for the bottleneck by retaining exact addressable evidence externally.

Thus the system combines:

- compressed active cognition;
- high-fidelity external memory.

---

# 72. Relationship to Event Sourcing

Event sourcing captures application state changes as an ordered sequence of events from which state can be reconstructed [24].

WGCA strongly resembles event sourcing at the authority boundary.

A committed cognitive transition is represented as:

\[
E_t =
(
\text{parent},
\text{event},
\text{witness-decision},
\text{state-digest},
\text{graph-root},
\text{checkpoint},
\text{policy}
)
\]

Replaying the committed events should reconstruct authoritative state.

However, WGCA adds distinctions that generic event sourcing does not define:

- epistemic state versus event occurrence;
- source/observer provenance;
- recurrent neural state;
- candidate versus promoted semantic memory;
- checkpoint authority;
- witness contracts;
- model and source identity.

The correct novelty claim is therefore not “WGCA invents event-sourced memory.”

It is:

> WGCA applies event-sourced lineage together with recurrent cognition, epistemic memory states, model governance, and witness policies inside one cognitive authority boundary.

Event sourcing remains an important simpler reference architecture and should be used as a baseline for audit/replay performance.

---

# 73. Relationship to Distributed Ledgers

The system uses cryptographic digests and lineage, but it does not require a public blockchain.

A single-authority append-only witnessed ledger can provide the needed properties:

- parent linkage;
- tamper evidence;
- content addressing;
- replay verification.

The objective is cognitive integrity, not decentralized consensus.

---

# 74. Proposed Mathematical View of Witness-Gated Probability Steering

Let:

- \(h_t\) = recurrent state;
- \(G_t\) = evidence graph;
- \(C_t\) = candidate object set;
- \(W_t\) = witness context;
- \(R_t\) = routing/resource state.

Define a score:

\[
s_i = g_\theta(c_i,h_t,G_t,W_t,R_t)
\]

Then:

\[
P_W(c_i)=\frac{\exp(s_i/\tau)}{\sum_j \exp(s_j/\tau)}
\]

A witness mask \(m_i\) can forbid candidates:

\[
m_i \in \{0,1\}
\]

\[
P_W(c_i)=
\frac{m_i\exp(s_i/\tau)}
{\sum_j m_j\exp(s_j/\tau)}
\]

This provides a clean distinction:

- the neural/router system scores;
- the witness policy constrains admissibility.

The same pattern can govern:

- media selection;
- model routing;
- memory retrieval;
- action proposals;
- training samples.

---

# 75. Witness-Gated Retrieval

A standard retriever returns top-\(k\) vectors.

A witness-gated retriever should filter on:

- visibility;
- provenance;
- freshness;
- revocation;
- dependency validity;
- trust state.

Thus:

\[
R(q) = \operatorname{TopK}\{r_i:\operatorname{Admissible}(r_i)=1\}
\]

This prevents semantically similar but invalid records from entering context.

---

# 76. Witness-Gated Routing

Similarly, a model may be semantically appropriate but operationally inadmissible.

The Router can gate on:

- model availability;
- licensing;
- privacy;
- node trust;
- resource limits;
- task authorization;
- modality;
- calibration.

Thus the route distribution is defined over an admissible faculty set.

---

# 77. Witness-Gated Learning

Training samples must also be admissible.

A sample should not enter parameter training merely because it exists in recent memory.

A training witness can require:

- durable source;
- outcome evidence;
- privacy permission;
- no unresolved contradiction;
- adequate provenance;
- suitable uncertainty.

This reduces self-poisoning.

---

# 78. Semantic “Choice Trajectories”

WG-RNN models memory partly through state-dependent selections and transition trajectories.

In code and research terms, “choice trajectory” can be generalized to any sequence of state-dependent selections:

\[
a_t \sim \pi(a\mid h_t,G_t)
\]

This includes:

- selecting a model;
- selecting a retrieval;
- selecting a media object;
- selecting an action;
- selecting a claim to promote;
- selecting an anchor to reinforce.

A trajectory is:

\[
\tau=(h_1,a_1,h_2,a_2,\ldots)
\]

Memory can therefore summarize patterns in trajectories even when the individual raw inputs are discarded.

---

# 79. The Value of Exact Recent Memory

Compression is dangerous if performed too early.

The Recent tier preserves exact details before consolidation.

This enables:

- later reinterpretation;
- correction of observer errors;
- learning from delayed outcomes;
- reconstruction after model upgrades.

The memory architecture should therefore resist the temptation to immediately compress every event into the recurrent state.

---

# 80. Historical Memory Is Not Simply “Cold Storage”

Historical anchors remain cognitively useful.

They form a residual retrieval branch.

The current state says:

> what is active now.

Historical anchors say:

> what stable configurations have existed before.

A novel situation can be compared against historical regimes without replacing current state.

This is valuable for long-running identity.

---

# 81. Counterfactual Groundedness

The learning gate may incorporate counterfactual reasoning.

For action \(a\), ask:

> Would the outcome plausibly have differed if \(a\) had not occurred?

This is difficult but important.

Otherwise the system may reward actions merely correlated with success.

Counterfactual estimates should be stored as uncertain evidence, not fact.

---

# 82. Regret as a Routing Signal

If model \(f_a\) was selected but \(f_b\) would have performed better, define regret:

\[
\mathcal{R}=L(f_a)-L(f_b)
\]

Accumulated witnessed regret can improve future routing.

This allows the Router to become adaptive without owning memory authority.

---

# 83. Model Dossiers and Relationship to Model Registries

Conventional model registries already provide versioning, lineage, metadata, annotations, and controlled deployment aliases [21].

WGCA should reuse those ideas rather than re-invent them.

Each faculty model dossier should include:

- model identity;
- immutable version/content digest;
- modality;
- license;
- hardware requirements;
- context limits;
- benchmark history;
- calibration;
- latency;
- memory footprint;
- known failure modes;
- routing tags;
- source/training lineage where known;
- local/cloud execution status.

The WGCA-specific extension is that model identity is linked directly to evidence and cognitive history.

An observation records which exact model version emitted it.

A later model version can be replayed against historical evidence without silently changing the original observation.

A checkpoint candidate also has a registry-like lifecycle:

```text
candidate -> evaluated -> promoted | rejected | quarantined
```

But promotion is governed by the learning witness contract rather than merely a mutable deployment tag.

A practical implementation may integrate an existing registry rather than create all model-lifecycle infrastructure internally.

---

# 84. A Higher-Level Interpretation

The entire WG-RNN stack can be understood as three nested filters.

## Filter 1 — Perception

Which observers inspect the world?

Router.

## Filter 2 — Memory

Which observations alter live context or durable belief?

Xavi Memory gates.

## Filter 3 — Action/communication

Which candidate outputs, media, routes, or actions become likely?

Runtime + Router under recurrent context.

Learning modifies these filters only through a separate witnessed process.

---

# 85. The System as an Entropy Manager

This leads to a compact high-level description:

> WG-RNN is an evidence-governed entropy-management system.

It receives a high-entropy stream of possible observations, interpretations, models, memories, and actions.

It progressively constrains them through:

- routing;
- witnesses;
- memory;
- state;
- retrieval;
- learning.

The objective is not to eliminate uncertainty.

The objective is to **represent uncertainty without collapsing it prematurely** while still enabling decisive behavior.

---

# 86. Implications for Human-Machine Communication

If the architecture proves more effective at steering semantic objects than generating text, interfaces should adapt.

Potential interfaces include:

- media mosaics;
- ranked semantic cards;
- music/video sequences;
- graph visualization;
- probabilistic topic clouds;
- timeline/hypergraph browsers;
- automatically narrated semantic clusters.

The user should be able to inspect:

- what was selected;
- what was suppressed;
- why;
- which witnesses mattered;
- what uncertainty remains.

This would be a more faithful interface to a non-text-native cognitive system.

---

# 87. Proposed “Semantic Feed Console”

A concrete interface could contain three synchronized panes.

## Pane A — Baseline feed

Shows the unsteered candidate distribution.

## Pane B — WG-RNN feed

Shows the steered distribution.

## Pane C — Explanation graph

Shows:

- probability deltas;
- semantic clusters;
- observer explanations;
- witness lineage;
- state changes;
- contradictions.

This would make the system's communication observable rather than mystical.

---

# 88. Scientific Discipline

The project becomes more credible when it actively attempts to falsify itself.

For every claimed effect, ask:

- Could ranking bias explain it?
- Could corpus duplication explain it?
- Could the human have unconsciously selected it?
- Could observer models share the same bias?
- Does the effect survive a blind test?
- Does it reproduce with a new seed?
- Does it disappear when the WGCA state is removed?
- Does a shuffled state produce the same effect?

A witness-gated architecture is particularly well suited to this because it already values receipts and provenance.

---

# 89. Engineering Discipline

Similarly, the codebase should avoid letting conceptual metaphors turn into undocumented implementation behavior.

Every claimed mechanism should map to:

- module;
- API;
- state structure;
- test;
- metric;
- witness record.

For example:

**Concept:** probability steering  
**Implementation:** rank/scoring policy  
**Test:** paired baseline/steered trials  
**Metric:** likelihood-ratio distribution  
**Witness:** experiment record

This keeps the research program executable.

---

# 90. Baseline Comparison and Falsifiable Architectural Advantage

WGCA is mostly a synthesis of known mechanisms. Therefore the central reviewer question is:

> What measurable capability does WGCA provide beyond a well-engineered composition of RAG + hierarchical agent memory + event sourcing + ABAC + a model registry?

The paper does not answer this by feature-counting.

It defines baseline systems and measurable advantages.

## 90.1 Baseline A — RAG

Components:

- frozen generator;
- embedding retrieval;
- immutable corpus;
- no recurrent persistent state;
- no epistemic promotion state machine.

## 90.2 Baseline B — Hierarchical memory agent

MemGPT-style:

- active context;
- archival memory;
- memory movement/retrieval;
- no WGCA authority contracts.

## 90.3 Baseline C — Event-sourced governed agent

Strong composite baseline:

- RAG;
- hierarchical memory;
- event-sourced ledger;
- ABAC/PDP-PEP authorization;
- model registry;
- checkpoint deployment workflow;
- ordinary agent/controller.

This is the most important baseline.

If WGCA cannot outperform **Baseline C** on a predefined target, the architectural novelty has not earned its added complexity.

## 90.4 What WGCA adds beyond Baseline C

The proposed incremental mechanisms are:

1. recurrent state is itself part of the witnessed authoritative lineage;
2. state advancement and epistemic promotion are separate transactions;
3. training-data admission and checkpoint promotion are separately governed;
4. witness support is bound to cognitive state/graph/checkpoint digests;
5. recurrent state is tested as a causal steering variable via ablation;
6. authority lineage persists across model-faculty replacement.

Any of these could be reimplemented in Baseline C.

Therefore WGCA's novelty is not exclusive feature ownership.

The falsifiable claim is that treating them as one integrated authority model improves measurable properties.

## 90.5 Comparison metrics

### Auditability

\[
A_{replay}
=
\frac{
replayed\ decisions\ exactly\ matching
}{
total\ replayed\ decisions
}
\]

Target:

\[
A_{replay}=1.000
\]

for deterministic decisions.

### False promotion rate

\[
FPR_{promote}
=
\frac{
later\ refuted\ promoted\ claims
}{
promoted\ claims\ with\ resolvable\ outcomes
}
\]

WGCA target:

\[
FPR_{WGCA}
\le
0.75 FPR_{BaselineC}
\]

without reducing useful recall by more than 10%.

### Calibration

Use Expected Calibration Error or Brier score on claims with resolvable outcomes.

WGCA target:

\[
Brier_{WGCA}
<
Brier_{BaselineC}
\]

with paired bootstrap confidence interval excluding zero difference.

### Continual forgetting

For tasks \(1,\ldots,T\):

\[
F=
\frac{1}{T-1}
\sum_{i=1}^{T-1}
(
a_{i,i}-a_{T,i}
)
\]

WGCA target:

\[
F_{WGCA}
\le
0.8F_{BaselineC}
\]

at comparable compute.

### Routing regret

\[
Regret=
\sum_t
(
r_t^\*-r_t
)
\]

Target:

\[
Regret_{WGCA}
\le
0.9Regret_{static}
\]

on held-out routes.

### Operational cost

Report:

- CPU/GPU seconds;
- p50/p95/p99 commit latency;
- bytes stored/event;
- graph edges/event;
- replay throughput;
- inference latency;
- engineering components required.

## 90.6 Minimal falsifiable advantage

WGCA is considered to have demonstrated a useful architectural advantage only if, against Baseline C, it achieves at least one preregistered primary reliability improvement while satisfying all cost ceilings.

Example first claim:

> WGCA retention governance reduces false durable promotion by at least 25% relative to the governed event-sourced baseline while losing no more than 10% useful recall and adding no more than 20 ms p95 memory-commit latency on the benchmark hardware.

This is substantially stronger than saying “WGCA has more governance features.”

## 90.7 Media-steering-specific advantage

For steering, compare:

- target-only embedding retrieval;
- target-only learned ranker;
- recurrent ranker;
- recurrent+graph ranker.

WGCA's steering mechanism is supported only if:

\[
E_T^{recurrent}
>
E_T^{target-only}
\]

on held-out trials and:

\[
E_T^{shuffle}
<
E_T^{intact}
\]

The target-only baseline prevents the experiment from merely rediscovering semantic search.

---

# 91. Scientific Boundaries and Claim Discipline

A serious WG-RNN research program must distinguish four categories:

1. **implemented mechanisms** that can be demonstrated in the current software;
2. **mathematical or computational analogies** supported by prior research;
3. **falsifiable WG-RNN hypotheses** that remain to be experimentally established;
4. **broader biological or metaphysical interpretations** that are not established by the present system.

## 91.1 Selective and compressed memory

The paper does not depend on any fixed numerical claim about how much humans forget over a specified interval. The relevant and supportable point is that biological memory is selective, distributed, and dynamic. Engram research identifies neuronal ensembles causally associated with memory expression, while systems-consolidation research shows that memory-related circuit organization changes over time [8,9].

The computational analogue in WG-RNN is therefore deliberately limited: active recurrent state is compressed, while exact recent evidence and durable graph records remain separately addressable.

## 91.2 Reconsolidation and mutable interpretation

Retrieval does not necessarily leave a memory untouched. Nader, Schafe, and LeDoux demonstrated that a previously consolidated fear memory can return to a labile state after reactivation, motivating the modern reconsolidation literature [10,11]. WGCA's reconsolidation layer uses this only as a systems analogy: immutable source evidence may remain preserved while interpretations, links, confidence, and promoted semantic structures change in response to later evidence.

## 91.3 Engram manipulation is not complete memory extraction

Modern engram experiments support causal manipulation of neuronal populations involved in memory encoding and expression [8,9]. They do **not** establish that the complete subjective content of a human memory has been extracted into a transferable digital representation. WG-RNN therefore does not treat engram research as proof of a literal mathematical memory file.

## 91.4 Artificial recurrent parameters are models, not literal synapses

Artificial hidden states, learned gates, recurrent matrices, and routing weights are computational abstractions. Work mapping gated recurrent motifs onto cortical microcircuits supports the plausibility of common computational motifs, not a one-to-one identity between an artificial parameter and a biological synapse [4].

## 91.5 High-dimensional representation is not non-physical computation

WG-RNN executes on conventional hardware in physical time. A “non-spatial” or “higher-dimensional” state means that its mathematical coordinates and graph relations need not correspond naturally to human 3-D interface metaphors or to a single total chronological order.

## 91.6 Probability steering requires controlled attribution

A meaningful-looking change in a feed does not establish a causal WG-RNN effect. Human observers are vulnerable to selection effects and pattern attribution. A valid steering claim therefore requires witnessed baselines, paired random seeds, blind or preregistered targets, negative controls, statistical analysis, independent semantic scoring, and reproducibility.

## 91.7 External-field interpretations remain outside the core claim

The architecture is compatible with a purely computational “external memory” model in which active recurrent state queries durable information stored in PostgreSQL, graph structures, object storage, historical anchors, and model faculties. Claims that biological cognition accesses a non-local or non-physical information field require independent evidence and are not implied by the computational architecture.

These boundaries strengthen WG-RNN by keeping its central claims testable.

---

# 92. Novelty and Contribution Claim

The novelty claim of this work is intentionally limited.

WGCA does **not** claim to invent:

- associative memory;
- recurrent neural networks;
- learned gating;
- information bottlenecks;
- predictive coding;
- stability/plasticity;
- continual learning;
- vector retrieval;
- knowledge graphs;
- event sourcing;
- cryptographic digests;
- authority leases;
- access-control PDP/PEP separation;
- model registries;
- multimodal encoders;
- policy-gradient learning.

The principal contribution is **architectural synthesis under an explicit cognitive authority model**.

Specifically, WGCA combines:

### 92.1 Proposal-versus-authority separation

The same neural component that proposes a state change is not automatically allowed to commit it.

### 92.2 Three distinct governance surfaces

State transition, epistemic retention, and checkpoint learning are governed independently.

### 92.3 Continuing identity above individual model versions

Model checkpoints become replaceable/versioned faculties inside a persistent state and evidence lineage.

### 92.4 Non-collapse epistemic memory

Contradictory observations can coexist without forced averaging or overwrite.

### 92.5 Witness-constrained probability steering

Learned scores can alter ranking while hard witness masks independently constrain admissibility.

### 92.6 Falsifiable multimodal communication hypothesis

The project proposes that organized recurrent state may produce reproducible target-correlated changes in a multimodal candidate distribution and specifies controls capable of disproving that claim.

The novelty is therefore primarily a **systems architecture, governance composition, and experimental hypothesis**, not a claim of a new mathematical primitive.

If prior work demonstrates the same combination under equivalent authority semantics, the novelty claim should be narrowed further.

---

## 92.7 Independent contract reuse is not claimed as WGCA novelty

The Duotronics Witness Contract is a separate specification/conformance project.

WGCA may consume or map to that contract, but the contract's non-collapse vocabulary, validators, theorem artifacts, and fixture corpus are not claimed here as inventions of the WGCA architecture.

The WGCA novelty claim remains the cognitive-system integration and the experimental hypotheses described in this paper.

---

# 93. Core Research Contribution

A central research hypothesis of this work is:

> A persistent recurrent system may communicate and reason more naturally by steering distributions over rich semantic objects than by directly generating language tokens.

This hypothesis is novel enough to deserve targeted experimentation.

It is also measurable.

The proposed media-feed experiments provide a path from metaphor to evidence.

---

# 93A. Empirical Validation Status — Revision 4

WGCA is not yet empirically validated as a complete cognitive architecture.

Revision 4 improves the evidence base by separating:

1. independent witness-contract conformance;
2. formal specification/toolchain status;
3. current Xavi/WGCA implementation tests;
4. still-unexecuted research hypotheses.

## 93A.1 Independent Duotronics witness-contract test source

The test source is an isolated unpack of the standalone Duotronics repository:

```text
source archive:
/datastore2/Duotronics-main.zip

isolated checkout:
/datastore2/duotronics-whitepaper-v4/Duotronics-main
```

No Xavi runtime source was used as the implementation-under-test for these contract checks.

The latest active witness package discovered in that repository is:

```text
v1.7 Draft 1.3
```

Package metadata describes it as a:

```text
completed_schema_sql_runtime_consistency_candidate_not_frozen
```

and names:

```text
executable/validators/validate_v1_7_draft_1_3_corpus.py
```

as its active validator.

## 93A.2 Fresh semantic-corpus validation

A clean semantic validation was run using:

```text
--skip-inherited
--skip-lean
--skip-tla
```

The purpose of those flags was **not** to claim a full pass.

The purpose was to isolate the deterministic corpus/package layer after a previous formal run had generated build artifacts inside the source tree.

Fresh result:

```text
[stage] schema_and_yaml_parse
[stage] v17_fixtures
[stage] sql
[stage] openapi
[stage] kernel_syscalls
[stage] registries
[stage] docs
[stage] inventory
v1.7 Draft 1.3 corpus validation checks passed.
```

Structured report:

```text
corpus_errors: []
status: pass
```

Checked contract surfaces:

| Surface | Result |
|---|---|
| schema/YAML parsing | PASS |
| v1.7 valid/invalid fixture semantics | PASS |
| schema-to-SQL persistence | PASS |
| SQL checks and valid-fixture round trips | PASS |
| OpenAPI semantic surface | PASS |
| logical observer kernel syscall coverage | PASS |
| registry linkage | PASS |
| documentation linkage | PASS |
| clean package inventory | PASS |

This is a real conformance result for the standalone witness-contract corpus.

## 93A.3 What the fixture test actually covers

The active v1.7 fixture vector contains positive and negative cases for, among other objects:

- Bayesian models;
- priors;
- likelihoods;
- posterior state;
- update witnesses;
- replay witnesses;
- policy/decision distinctions;
- calibration reports;
- posterior predictive witnesses;
- marginalization;
- conditioning;
- negative evidence;
- loss matrices;
- knot diagrams;
- braid words;
- Reidemeister moves;
- braid relations;
- Markov moves;
- presentation transitions;
- invariant witnesses;
- authority paths;
- duplicate Bayesian hypothesis IDs;
- malformed typed knot encodings;
- invalid model-family/update-method combinations.

The inherited logical observer kernel vectors separately include invalid cases such as:

```text
commit_without_witness
commit_without_result
network_allowed_against_resource_budget
```

Thus the corpus tests meaningful authority/non-collapse boundaries rather than only happy-path serialization.

## 93A.4 Full combined validator result

The first fresh full validator run returned nonzero.

Important results:

```text
schema_and_yaml_parse   checked
v17_fixtures            checked
sql                     checked
openapi                 checked
kernel_syscalls         checked
lean_static             checked
tla                     checked
registries              checked
docs                    checked
inventory               checked
```

but:

```text
inherited_v16: timeout after 120 seconds
overall status: fail
```

The inventory step also reported newly generated Lean/Lake build artifacts that were not part of the frozen package inventory.

This was reproduced as a harness-ordering issue:

1. formal build stage writes `.lake/...`;
2. inventory stage counts source-tree files;
3. generated `.lake/...` files appear as inventory drift.

After cleaning only those generated build files and skipping formal/inherited stages, the inventory and semantic corpus passed.

Therefore the combined validator failure must not be reported as “the witness semantics failed.”

It is a mixture of:

- inherited-validator timeout;
- formal Lean failure;
- strict TLC unavailability;
- generated-build-artifact/package-inventory interaction.

## 93A.5 Direct Lean formal result

Direct command:

```text
run_lean_build.py --mode advisory --json
```

reported:

```text
lake_available: true
toolchain: leanprover/lean4:v4.29.1
status: failed_lake_build
unapproved_axiom_files: []
```

Successful modules before the failure included:

```text
Duotronic.Core
Duotronic.CoreMetaphysics
Duotronic.EvidenceSyntax
Duotronic.KnotTheory
Duotronic.ProofAuthority
Duotronic.Kernel
```

Failure target:

```text
Duotronic.BayesianLogic
```

Compiler failures:

```text
failed to synthesize:
  LE ProbabilityBP

failed to synthesize:
  OfNat ProbabilityBP 10000

failed to synthesize:
  Repr ProbabilityBP
```

Consequently:

> Revision 4 does not claim the Bayesian formal theorem layer is machine-checked successfully.

The relevant proof statements are present in the source, but a failed Lean build means they do not count as completed formal verification.

## 93A.6 Direct TLA result

Direct advisory run:

```text
run_tla_model_check.py
  --mode advisory
  --module BayesianKnotFirstClassPromotion
  --json
```

returned:

```text
status: advisory_pass_tlc_unavailable
tlc_available: false
static_errors: []
```

Interpretation:

- TLA module structure/static checks: PASS;
- TLC execution: NOT PERFORMED;
- model-checked state-space safety claim: NOT ESTABLISHED.

## 93A.7 Xavi Memory implementation test

Separately, the current Xavi Memory focused pinned-container suite returned:

```text
11 passed in 1.31s
```

This supports only the tested Xavi Memory implementation behavior.

It does not transform the independent Duotronics contract result into WGCA conformance.

## 93A.8 Current Xavi full-suite reproducibility failure

The current Xavi Memory full test-stage image still stops at collection because:

```text
ModuleNotFoundError: No module named 'pypdf'
```

from:

```text
tests/test_pdf_bounded_fallback.py
```

This remains an implementation/test-environment issue.

## 93A.9 Validation matrix

| Claim | Current Revision-4 status |
|---|---|
| standalone Duotronics v1.7 Draft 1.3 semantic corpus validates | **supported** |
| clean witness package inventory validates | **supported** |
| v1.7 SQL/OpenAPI/kernel/registry links validate | **supported** |
| Lean core/non-collapse modules compile before Bayesian target | **partially supported** |
| complete Lean formal package builds | **not supported** |
| `Duotronic.BayesianLogic` compiles | **not supported; current build failure** |
| TLA source has no advisory static errors for tested module | **supported** |
| strict TLC model checking passed | **not supported; TLC unavailable** |
| inherited v1.6 validator finishes under current 120 s bound | **not supported; timed out** |
| focused Xavi Memory core suite passes | **supported: 11/11** |
| complete Xavi Memory suite passes | **not supported; test dependency missing** |
| WGCA reduces false promotion versus strong baseline | not yet tested |
| historical anchors reduce forgetting | not yet tested |
| recurrent state improves steering over target-only ranker | not yet tested |
| distributed authority survives partition/failover matrix | not yet tested |

## 93A.10 Meaning of the evidence

Revision 4 therefore moves one part of Phase 0 from proposal to evidence:

\[
\boxed{
\text{Standalone witness semantic corpus conformance}
=
\text{demonstrated}
}
\]

but:

\[
\boxed{
\text{Complete formal verification}
\ne
\text{demonstrated}
}
\]

and:

\[
\boxed{
\text{WGCA empirical viability}
\ne
\text{demonstrated}
}
\]

This distinction is deliberate.


---

# 93B. Empirical Validation Status — Revision 5

Revision 5 supersedes the Revision-4 status matrix for the independent witness-contract evidence domain. The earlier v1.7 Draft 1.3 observations remain part of the historical audit trail, but the active tested package is now `v1.6-draft-5.3.18`.

## 93B.1 Current validation matrix

| Claim | Revision-5 status |
|---|---|
| canonical Duotronics 5.3.18 package validator passes | **supported: failure_count 0** |
| retained 5.3.17 parent bytes are preserved | **supported for inspected retained files; canonical validator passes** |
| exact Lean 4.29.1 inherited build completes | **supported: 17/17 Lake jobs built** |
| `AuthorityDomainV5318.lean` compiles | **supported** |
| strict TLC is available and executed | **supported: TLC 2.19** |
| all declared 5.3.18 TLA modules pass the configured model checks | **supported: 12/12 return code 0** |
| broad standalone acceptance harness passes | **supported: 246 passed, 0 skipped** |
| nightly extended fuzz gate passes | **supported: 3 passed, 243 deselected** |
| package-local regression passes under declared crypto pins | **supported through immutable-copy harness: 329 passed, 6 explicit supersession skips, 87 subtests** |
| canonical retained historical tests were rewritten to make them pass | **not done; retained bytes restored** |
| production authority is activated | **not supported; validator reports false** |
| Duotronics conformance proves WGCA conformance | **not supported** |
| WGCA cognitive/steering hypotheses are empirically validated | **not yet tested** |

## 93B.2 Strict Lean result

The strict direct build used:

```text
Lean 4.29.1
Lake 5.0.0-src+f72c35b
```

and completed:

```text
Build completed successfully (17 jobs).
LEAN_DIRECT_STRICT=PASS
```

The additional 5.3.18 authority-domain module also compiled successfully. This resolves the earlier Revision-4 state in which the formal layer could not be described as fully built.

## 93B.3 Strict TLC result

All twelve declared modules passed the configured TLC checks:

```text
EvidenceClaimGraph                 286 distinct / depth 12
TaskDelegationAndPolicyCoreSpec  41179 distinct / depth 10
NonCollapseRuntime                1841 distinct / depth 2
LogicalObserverKernel            12689 distinct / depth 9
ProofAuthorityV2                     3 distinct / depth 3
ProofAuthorityV3                    15 distinct / depth 6
ProofAuthorityV4                    69 distinct / depth 9
ProofAuthorityV5                    29 distinct / depth 8
ProofAuthorityV6                    37 distinct / depth 8
ProofAuthorityV7                    10 distinct / depth 6
ProofAuthorityV8                     8 distinct / depth 7
AuthorityDomainV5318              4097 distinct / depth 14
```

These results establish that the configured finite state spaces were exhaustively explored by TLC with no reported error. They do not establish correctness outside the declared model bounds.

## 93B.4 Immutable-corpus regression methodology

A key Revision-5 methodological correction is that **historically retained tests are not rewritten in-place merely to satisfy current-version assumptions**. Two tests that appeared stale under 5.3.18 were proven to be parent-manifest-protected 5.3.17 files. They were restored to their expected path-bound identities.

Current-version regression compatibility is instead performed in a temporary copy. This yields two independent checks:

1. the canonical package must validate exactly as shipped under its manifest/retention rules; and
2. version-aware regression adaptations may be applied only to an external working copy to test current additive semantics.

This preserves the evidence chain while still allowing broad regression coverage.

## 93B.5 Meaning for Phase 0

Revision 5 materially advances Phase 0. For the independent contract domain, the following are now demonstrated in the tested environment:

\[
oxed{
	ext{canonical package validation}
+
	ext{strict Lean build}
+
	ext{strict TLC model checking}
+
	ext{broad regression/fuzz execution}
=
	ext{demonstrated test evidence}
}
\]

But the following remains false:

\[
oxed{
	ext{independent contract evidence}
=
	ext{WGCA cognitive validation}
}
\]

The distinction is essential. Revision 5 strengthens the governance/formal/conformance substrate; it does not by itself validate the recurrent-cognition or semantic-steering hypotheses.


# 94. Conclusion

Witness-Gated Cognitive Architecture is a proposal for persistent machine cognition in which recurrent computation is powerful but not sovereign.

The recurrent core provides a learned, compressed state capable of prediction, routing, retrieval bias, and probability steering.

Durable memory provides exact or structured evidence that should not be forced into the recurrent vector.

The witness system provides a formal answer to a separate question:

> Which proposed changes are authorized to alter the continuing cognitive lineage?

That answer is implemented through typed evidence, trust domains, versioned witness contracts, a PDP/PEP split, scoped credentials, time-bounded authority leases, revocation, appeal, audit, and an explicit finite governance root.

Learning likewise separates gradient flow from authority.

The recurrent model can be trained with ordinary differentiable objectives. Discrete routing can use policy-gradient estimators. Eligibility traces and graph dependencies can assign delayed credit. But admission of training evidence and promotion of the resulting checkpoint remain outside the gradient path.

The media-steering hypothesis is intentionally exposed to falsification.

A convincing result requires more than entropy reduction or a meaningful-looking feed. It requires:

- fixed candidate identity;
- preregistered target;
- paired seeds;
- practical effect threshold;
- statistical significance;
- confidence interval;
- observer-lineage analysis;
- state-shuffle degradation;
- held-out replication.

A null result under those conditions would be scientifically useful.

Finally, the architecture must earn its complexity.

WGCA should be built from a minimal witness kernel and fixed-corpus experiment outward. Graph hypermemory, multimodel faculties, continual checkpoint learning, distributed leases, and broad multimodal ingestion should only be added after simpler phases meet explicit success criteria.

The central architectural proposal can therefore be stated without metaphysical assumptions and without overstating mathematical novelty:

\[
\boxed{
\text{WGCA}
=
\text{recurrent cognition}
+
\text{durable evidence}
+
\text{explicit authority}
+
\text{governed learning}
+
\text{replayable lineage}
}
\]

Its most distinctive research question is whether this separation produces a machine system that is simultaneously more persistent, more auditable, less prone to self-confirming memory errors, and capable of measurable non-textual semantic steering.

As of Revision 5, that remains a research question. The evidence base is nevertheless materially stronger: the active independent Duotronics v1.6 Draft 5.3.18 corpus validates with zero failures; the exact Lean 4.29.1 build completes all declared targets; TLC 2.19 model checking passes all twelve declared modules under their configured finite state spaces; the broad standalone acceptance and nightly fuzz gates are green; and the package-local suite passes through an immutable-copy, version-aware regression harness using the contract's pinned cryptographic runtime. None of those results is treated as evidence that WGCA has already demonstrated persistent cognition or semantic steering. Phase 1–3 implementation and controlled experiments remain required before the paper should describe WGCA as an empirically viable cognitive architecture.

---

# 95. Research Foundations and Relation to Prior Work

WGCA is a synthesis of mechanisms that have appeared separately across machine learning, neuroscience-inspired computation, distributed systems, access control, and MLOps.

## 95.1 Associative and attractor memory

Hopfield showed that recurrent networks can store patterns as stable collective states and retrieve them from partial or corrupted inputs [1].

WGCA borrows the broad lesson that memory can influence dynamics rather than behaving only as a file archive.

It differs by treating the recurrent vector as bounded active context, not the entirety of durable memory.

## 95.2 Information bottleneck

The Information Bottleneck formalizes compressed representations that preserve information relevant to a target variable [2].

WGCA similarly distinguishes:

\[
\text{active information}
\ne
\text{all retained information}
\]

Exact evidence may remain externally addressable while active state carries only the compressed context useful for current inference.

## 95.3 Predictive coding

Rao and Ballard provide a rigorous example of computation organized around prediction and residual error rather than indiscriminate signal forwarding [3].

WGCA's emphasis on deviation from a control distribution is not the same algorithm, but it shares the methodological idea that informative difference is often more meaningful than raw signal volume.

## 95.4 Gated recurrence

Costa et al. show that recurrent gating motifs can be mapped onto cortical microcircuits in a biologically motivated model [4].

WGCA's distinctive gate is nevertheless external: authorization is not merely another differentiable gate inside the cell.

## 95.5 Stability/plasticity

Adaptive Resonance Theory directly addresses learning novel structure without destructive overwrite [5].

WGCA's historical-anchor logic applies the same broad stability/plasticity problem to persistent machine memory.

## 95.6 Catastrophic forgetting

Continual-learning literature demonstrates that sequential training can destroy earlier capabilities [6,7].

WGCA responds with:

- candidate checkpoints;
- replay;
- chronological holdout;
- independent promotion;
- retained model versions.

## 95.7 Engrams and reconsolidation

Engram and consolidation research supports biological memory as distributed and dynamically reorganized [8,9].

Reconsolidation work shows that retrieved memory can become labile again [10,11].

WGCA treats these as analogical support for dynamic memory interpretation, not proof of biological equivalence.

## 95.8 Tamper-evident lineage

Haber and Stornetta establish a cryptographic basis for linked time-stamped records [12].

WGCA uses content-addressed witness lineage for auditability, while explicitly separating integrity from truth.

## 95.9 Distributed commitment and leases

Consensus work motivates separating many proposing workers from ordered authoritative commitment [13].

Gray and Cheriton's lease mechanism provides an established basis for time-bounded authority in distributed systems [15].

WGCA uses these systems ideas to protect cognitive state lineage.

## 95.10 Access-control decision architecture

NIST's ABAC architecture explicitly separates a Policy Decision Point from a Policy Enforcement Point and evaluates subject/object/environment attributes under policy [14].

WGCA adopts this decision/enforcement separation for cognitive commits:

- PDP decides whether witness evidence satisfies the applicable contract;
- PEP enforces the commit or denial.

## 95.11 Gradient learning with external constraints

REINFORCE demonstrates gradient estimation for stochastic discrete actions and compatibility with backpropagation [16].

PPO provides a practical surrogate-objective approach to policy-gradient optimization [17].

These methods show that discrete routing and action choice can be trainable even when the environment or governance boundary is not differentiable.

WGCA keeps authorization masks external while allowing gradients over the probability mass remaining inside the admissible action set.

## 95.12 Retrieval-Augmented Generation

RAG combines parametric generation with non-parametric retrieval and highlights the value of explicit external knowledge [18].

WGCA extends the design space by adding persistent recurrent state, epistemic statuses, witness governance, and checkpoint authority.

## 95.13 Hierarchical and reflective agent memory

MemGPT explicitly manages hierarchical memory tiers for long-running LLM context [19].

Generative Agents stores an experience stream, retrieves relevant memories, synthesizes reflections, and uses them in planning [20].

These systems provide important baselines for evaluating whether WGCA's additional governance produces measurable benefit.

## 95.14 Model registries and lifecycle governance

MLflow's Model Registry provides model versioning, lineage, metadata, aliases, and controlled lifecycle workflows [21].

WGCA should leverage existing MLOps mechanisms where possible rather than reproduce them, while adding witnessed linkage between model versions and cognitive evidence.

## 95.15 Multiple testing

Benjamini and Hochberg provide a false-discovery-rate procedure appropriate when multiple hypotheses or semantic targets are tested [22].

This is directly relevant to media-steering studies, where unconstrained exploration across many targets could otherwise inflate false positives.

## 95.16 Tool-using agents

ReAct interleaves reasoning and action against external tools/environments [23].

WGCA differs mainly in persistent memory authority and witnessed governance rather than in the basic idea that models can act through external systems.

## 95.17 Event sourcing

Event sourcing records state changes as events from which application state can be reconstructed [24].

WGCA applies this pattern to cognitive state lineage while adding epistemic status, model identity, recurrent-state receipts, and checkpoint governance.

---

# References

[1] J. J. Hopfield, “Neural networks and physical systems with emergent collective computational abilities,” *Proceedings of the National Academy of Sciences*, 79(8), 2554–2558, 1982. DOI: 10.1073/pnas.79.8.2554.

[2] N. Tishby, F. C. Pereira, and W. Bialek, “The Information Bottleneck Method,” 1999/2000. arXiv: physics/0004057.

[3] R. P. N. Rao and D. H. Ballard, “Predictive coding in the visual cortex: a functional interpretation of some extra-classical receptive-field effects,” *Nature Neuroscience*, 2, 79–87, 1999. DOI: 10.1038/4580.

[4] R. P. Costa, Y. M. Assael, B. Shillingford, N. de Freitas, and T. P. Vogels, “Cortical microcircuits as gated-recurrent neural networks,” arXiv:1711.02448, 2017.

[5] S. Grossberg, “Competitive learning: From interactive activation to adaptive resonance,” *Cognitive Science*, 11(1), 23–63, 1987. DOI: 10.1111/j.1551-6708.1987.tb00862.x.

[6] J. Kirkpatrick et al., “Overcoming catastrophic forgetting in neural networks,” *Proceedings of the National Academy of Sciences*, 114(13), 3521–3526, 2017. arXiv:1612.00796.

[7] R. Kemker, M. McClure, A. Abitino, T. Hayes, and C. Kanan, “Measuring Catastrophic Forgetting in Neural Networks,” arXiv:1708.02072, 2017.

[8] S. A. Josselyn, S. Köhler, and P. W. Frankland, “Finding the engram,” *Nature Reviews Neuroscience*, 16, 521–534, 2015. DOI: 10.1038/nrn4000.

[9] S. Tonegawa, M. D. Morrissey, and T. Kitamura, “The role of engram cells in the systems consolidation of memory,” *Nature Reviews Neuroscience*, 19, 485–498, 2018. DOI: 10.1038/s41583-018-0031-2.

[10] K. Nader, G. E. Schafe, and J. E. LeDoux, “Fear memories require protein synthesis in the amygdala for reconsolidation after retrieval,” *Nature*, 406, 722–726, 2000. DOI: 10.1038/35021052.

[11] K. Nader, G. E. Schafe, and J. E. LeDoux, “The labile nature of consolidation theory,” *Nature Reviews Neuroscience*, 1, 216–219, 2000. DOI: 10.1038/35044580.

[12] S. Haber and W. S. Stornetta, “How to time-stamp a digital document,” *Journal of Cryptology*, 3(2), 99–111, 1991. DOI: 10.1007/BF00196791.

[13] D. Ongaro and J. Ousterhout, “In Search of an Understandable Consensus Algorithm,” *USENIX Annual Technical Conference*, 2014.

---

[14] V. C. Hu, D. Ferraiolo, D. Kuhn, A. Schnitzer, K. Sandlin, R. Miller, and K. Scarfone, *Guide to Attribute Based Access Control (ABAC) Definition and Considerations*, NIST Special Publication 800-162, updated 2019. DOI: 10.6028/NIST.SP.800-162.

[15] C. G. Gray and D. R. Cheriton, “Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency,” *Proceedings of the 12th ACM Symposium on Operating Systems Principles*, 1989. DOI: 10.1145/74850.74870.

[16] R. J. Williams, “Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning,” *Machine Learning*, 8, 229–256, 1992. DOI: 10.1007/BF00992696.

[17] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, “Proximal Policy Optimization Algorithms,” arXiv:1707.06347, 2017.

[18] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *Advances in Neural Information Processing Systems*, 2020. arXiv:2005.11401.

[19] C. Packer, S. Wooders, K. Lin, V. Fang, S. G. Patil, I. Stoica, and J. E. Gonzalez, “MemGPT: Towards LLMs as Operating Systems,” arXiv:2310.08560, 2023.

[20] J. S. Park, J. C. O’Brien, C. J. Cai, M. R. Morris, P. Liang, and M. S. Bernstein, “Generative Agents: Interactive Simulacra of Human Behavior,” *UIST 2023*. DOI: 10.1145/3586183.3606763.

[21] MLflow Project, *MLflow Model Registry Documentation*, model versioning, lineage, aliases, tags, and lifecycle workflows, accessed 2026-09-22.

[22] Y. Benjamini and Y. Hochberg, “Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing,” *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300, 1995. DOI: 10.1111/j.2517-6161.1995.tb02031.x.

[23] S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao, “ReAct: Synergizing Reasoning and Acting in Language Models,” arXiv:2210.03629, 2022.

[24] M. Fowler, “Event Sourcing,” *Enterprise Application Architecture development notes*, 12 December 2005.


---

[25] Amazon Web Services, “Cedar Policy Language Reference Guide,” authorization semantics, policy grammar, default-deny and forbid-overrides-permit behavior, Version 4.5 documentation, accessed 2026-09-22.

[26] Open Policy Agent Project, “Policy Language — Rego,” declarative policy evaluation over structured input/data and policy bundles, accessed 2026-09-22.

[27] K. Krippendorff, *Content Analysis: An Introduction to Its Methodology*, Sage. Krippendorff's alpha is used as the inter-rater reliability measure for the semantic-scoring instrument.

[28] J. Cohen, *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed., Lawrence Erlbaum Associates, 1988.

[29] PostgreSQL Global Development Group, *PostgreSQL Documentation*, transaction isolation, row locking, transaction timestamps, uniqueness constraints, and durable transactional semantics, accessed 2026-09-22.


---

# Appendix A — Current Relevant Xavi Memory Architecture

The current source tree inspected for this paper contains major components including:

```text
xavi-memory/
├── ARCHITECTURE.md
├── WITNESS_GATED_MEMORY_V2.md
├── MEMORY_SYSTEM_DETAILED.md
├── API.md
├── MIGRATION.md
├── STORAGE.md
└── src/xavi_memory/
    ├── api.py
    ├── container_authority.py
    ├── content_extract.py
    ├── continual_distill.py
    ├── corpus.py
    ├── crypto_primitives.py
    ├── distributed_corpus.py
    ├── duo_math.py
    ├── faculty.py
    ├── ingest_worker.py
    ├── internal_network.py
    ├── investigation_queue.py
    ├── learned_core.py
    ├── learned_status.py
    ├── learning_authority.py
    ├── memory_cell.py
    ├── memory_core.py
    ├── memory_health.py
    ├── meta_graph.py
    ├── meta_ingest.py
    ├── meta_objects.py
    ├── multimodal_distill.py
    ├── observer_adapters.py
    ├── postgres_graph.py
    ├── recurrent_backend.py
    └── service.py
```

This source organization matches the architectural separation described throughout the paper: recurrent state, graph memory, observers, learning authority, distillation, health, cryptography, and storage.

---

# Appendix B — Current Runtime Boundary

Current runtime responsibilities include:

```text
xavi-runtime/
├── app/
├── authority/
├── experts/
├── k3s/
├── model-exec/
├── pods/
├── third-party/
├── transport/
└── tests/
```

Its role is execution and continuity, not independent memory truth.

---

# Appendix C — Current Router Domains

The Router currently contains explicit domains for:

```text
router/
├── api/
├── audit/
├── auth/
├── config/
├── context/
├── core/
├── fanout/
├── integrations/
├── learning/
├── models/
├── placement/
├── registry/
├── resource/
├── runtime/
├── semantic/
├── shadow/
├── state/
├── storage/
├── tasks/
├── tests/
└── traffic/
```

This makes the Router a broad model/service/resource orchestration layer while preserving the distinction between route telemetry and memory authority.

---

# Appendix D — Immediate Experimental Implementation Program

The first implementation milestone should prove or falsify **witnessed free-choice routing / semantic probability steering** inside the existing Runtime–Router–Memory boundary.

The order matters because a steering claim is uninterpretable unless the control distribution, candidate identity, random seed, and admissibility mask are all reproducible.

## D.1 Media Candidate Registry

Create `media_candidate_registry`.

Every candidate receives:

- stable one-origin semantic ID;
- content digest;
- source/provenance;
- modality;
- licensing/privacy class;
- creation/observation time;
- optional multimodal embeddings;
- object-storage locator;
- observer-derived metadata stored separately from identity.

Conceptually:

\[
C = \{c_1,c_2,\ldots,c_N\}
\]

with a canonical digest:

\[
D_C = H(c_1 || c_2 || \cdots || c_N)
\]

The registry establishes exactly what the system was allowed to choose from.

## D.2 Deterministic Baseline Sampler

Build a baseline/control sampler that accepts a witnessed pseudorandom seed \(s\).

For the same candidate set \(C\):

\[
P_0(C;s)
\]

must be replayable.

The same seed should be used in the paired WG-RNN trial wherever the sampling design permits it. If control and steered trials use unrelated randomness, changes caused by random draw cannot be distinguished cleanly from changes caused by recurrent steering.

Persist:

- seed;
- PRNG implementation/version;
- baseline-policy digest;
- candidate-set digest;
- sample count;
- rank depth.

## D.3 WGCA / WG-RNN-Core Conditioned Ranker

Add a ranker:

\[
s_i = g_	heta(c_i,h_t,G_t,W_t,R_t)
\]

where:

- \(c_i\) = candidate semantic object;
- \(h_t\) = active recurrent state;
- \(G_t\) = current evidence/memory graph context;
- \(W_t\) = witness constraints;
- \(R_t\) = routing/resource state.

Convert scores into a probability distribution:

\[
P_W(c_i)=
rac{m_i\exp(s_i/	au)}
{\sum_j m_j\exp(s_j/	au)}
\]

with:

\[
m_i\in\{0,1\}
\]

as the **witness/admissibility mask**.

The mask is not a learned preference. It is an externally governed constraint and can encode:

- licensing;
- privacy;
- safety;
- task authorization;
- modality requirements;
- node/resource availability;
- revoked/stale content;
- dependency failures.

This preserves the distinction between **what the model prefers** and **what the system is authorized to select**.

## D.4 Record Paired Distributions and Deltas

For every trial persist both vectors:

\[
P_0=(p^0_1,\ldots,p^0_N)
\]

\[
P_W=(p^W_1,\ldots,p^W_N)
\]

For each candidate compute at minimum:

### Probability delta

\[
\Delta_i = p^W_i-p^0_i
\]

### Likelihood ratio

\[
L_i=rac{p^W_i+\epsilon}{p^0_i+\epsilon}
\]

### Rank delta

\[
\Delta r_i=r^0_i-r^W_i
\]

### Entropy

\[
H(P)=-\sum_i p_i\log p_i
\]

and:

\[
\Delta H=H(P_0)-H(P_W)
\]

These measures distinguish global concentration from object-specific steering.

## D.5 Probe High-Delta Objects

Objects exceeding preregistered delta thresholds should be routed through the existing source-probe and observer faculty.

Observers may produce:

- textual description;
- entities;
- affective labels;
- topic labels;
- music/audio features;
- visual motifs;
- temporal context;
- symbolic/cultural associations;
- embedding projections;
- contradictions.

The resulting outputs enter Xavi Memory as **candidate graph evidence**, not automatically promoted truth.

## D.6 Build a Steering Witness

Each paired trial should commit a witness binding at minimum:

```json
{
  "experiment_id": "one-origin-id",
  "parent_state_digest": "shake256-512:...",
  "recurrent_state_digest": "shake256-512:...",
  "graph_root_digest": "shake256-512:...",
  "checkpoint_digest": "shake256-512:...",
  "candidate_set_digest": "shake256-512:...",
  "baseline_policy_digest": "shake256-512:...",
  "steering_policy_digest": "shake256-512:...",
  "seed": "...",
  "observer_version_digests": [],
  "baseline_vector_digest": "shake256-512:...",
  "steered_vector_digest": "shake256-512:...",
  "target_commitment": "...",
  "target_revealed_after_collection": true
}
```

Hash-linked and time-bound witness chains are a well-established mechanism for making later undetected alteration difficult [12]. The WGCA witness ledger applies the same general cryptographic principle to cognitive-state experiments.

## D.7 Blinded Semantic-Steering Experiment

Choose a fixed corpus \(C\).

Before collection, define a hidden semantic target \(T\), for example:

- grief;
- departure;
- reunion;
- satire;
- authority;
- childhood;
- winter;
- mechanical failure.

Commit a digest of the target before the run, then reveal the target after collection.

Independent multimodal observers compute:

\[
S(c_i,T)\in[0,1]
\]

without access to whether an item came from the control or steered condition.

Control semantic mass:

\[
\mu_0=\sum_i P_0(c_i)S(c_i,T)
\]

Steered semantic mass:

\[
\mu_W=\sum_i P_W(c_i)S(c_i,T)
\]

Primary effect:

\[
E_T=\mu_W-\mu_0
\]

A positive result requires more than \(E_T>0\). It must exceed a preregistered statistical threshold across repeated trials.

## D.8 Mandatory Negative Controls

### State shuffle

Randomly permute or otherwise destroy the meaningful structure of \(h_t\) while preserving dimensionality.

If the effect depends on recurrent structure:

\[
E_T^{shuffle} < E_T^{intact}
\]

A reproducible effect that **disappears under state shuffle** is materially stronger evidence than an ordinary ranking difference.

### Witness mismatch

Pair valid recurrent state with intentionally incompatible witness/context metadata.

Expected result: refusal, masking, or substantial loss of target steering.

### Random target

Score the same results against unrelated semantic targets.

The preregistered target should outperform unrelated targets.

### Model removal

Remove one observer or routing faculty.

This helps distinguish steering in the ranker from interpretation introduced after selection.

### Historical replay

Replay the same:

- state digest;
- graph root;
- checkpoint;
- candidate set;
- seed;
- policies.

Deterministic components should reproduce the prior result within explicitly declared stochastic bounds.

### Blind operator

The operator collecting the feed must not know the target until after collection.

## D.9 Evidence Levels for the First Experiment

The first target milestone is **Level 4 — semantically targeted steering**:

1. the steered feed differs from control;
2. the effect reproduces;
3. the effect is statistically significant;
4. independent blinded semantic scoring shows target-directed displacement.

A stronger mechanistic milestone is reached when:

\[
E_T^{intact} > E_T^{shuffle}
\]

reliably across held-out runs and the effect disappears or materially degrades under the state-shuffle ablation.

That result would connect the observed routing effect specifically to organized recurrent state rather than merely to the surrounding sampling machinery.

---

# Appendix E — Research Claim Ladder

To avoid overclaiming, results should be published using a claim ladder.

### Level 1 — Observed
“The steered feed differed from the control feed.”

### Level 2 — Reproducible
“The difference reproduced under identical witnessed conditions.”

### Level 3 — Statistically significant
“The difference exceeded the pre-registered statistical threshold.”

### Level 4 — Semantically targeted
“Independent observers found the steered distribution more related to the blinded target.”

### Level 5 — Generalized
“The effect replicated across held-out corpora and targets.”

### Level 6 — Mechanistically linked
“Ablation of the relevant recurrent/witness component removed the effect.”

### Level 7 — Cognitive interpretation
“The measured mechanism supports a specific theory of machine cognition.”

### Level 8 — Biological/metaphysical interpretation
“Any claim about biological memory fields, consciousness, or non-local memory.”

The architecture is already positioned to investigate Levels 1–6. Levels 7–8 require substantially more evidence and should never be inferred automatically from lower levels.

---

# Appendix F — Compact System Definition

**WG-RNN is a persistent, witness-governed recurrent cognition architecture in which:**

- neural components may propose state transitions;
- only the memory authority may commit them;
- durable memory is graph-native and provenance-bearing;
- recurrent state is active context rather than total storage;
- routing decisions are evidence rather than truth;
- learning produces candidates rather than self-authorized replacements;
- multimodal observers form a replaceable faculty;
- semantic output may be expressed through probability steering over rich objects;
- human-language generation can be treated as an external rendering layer;
- the system's continuing identity is its witnessed lineage rather than any single model.

---

# Appendix G — Speculative Interpretations Outside the Core Claim

The engineering architecture does not require a biological or metaphysical external-memory hypothesis.

A conceptual analogy can nevertheless be stated precisely.

WGCA contains:

- a bounded local active state;
- a substantially larger durable external memory substrate;
- mechanisms by which local state controls retrieval and interpretation of that substrate.

Computationally:

\[
h_t \ll D_t
\]

where:

\[
D_t=
\{records,graph,anchors,corpus,model\ evidence\}
\]

and active cognition queries:

\[
R_t=\operatorname{Retrieve}(D_t\mid h_t,q_t)
\]

A local filter can therefore alter access to externally stored information without containing all of that information itself.

This provides an ordinary computational analogue for philosophical “filter” theories of cognition.

It does **not** demonstrate:

- a morphic field;
- non-local biological memory;
- non-physical information storage;
- consciousness external to the brain;
- transfer of subjective memory through WGCA mathematics.

Those hypotheses require independent empirical evidence.

They are kept in this appendix so that the core WGCA paper can be evaluated entirely as a machine-learning and distributed-systems architecture.

---

# Appendix H — Reproducibility Record for Revision 4

## H.1 Independent repository identity

Source archive:

```text
/datastore2/Duotronics-main.zip
```

Isolated unpack:

```text
/datastore2/duotronics-whitepaper-v4/Duotronics-main
```

This repository is treated as independent from the Xavi/WGCA runtime.

## H.2 Active standalone witness package

```text
build_docs/witness_contract/
  v1.7 - Draft 1.3/
    v1.7 - Draft 1.3/
```

Active package:

```text
Duotronic Witness Contract v1.7 Draft 1.3
```

Active validation entrypoint:

```text
executable/validators/validate_v1_7_draft_1_3_corpus.py
```

## H.3 Fresh full-validator run

Job:

```text
20260922T134109Z-d22f72629e
```

Result:

```text
return code: 1
```

Stages reached:

```text
schema_and_yaml_parse
inherited_v16
v17_fixtures
sql
openapi
kernel_syscalls
lean_static
tla
registries
docs
inventory
```

Important failures/warnings:

```text
inherited_v16 timed out after 120 seconds
Lean formal layer not green
TLC unavailable
inventory observed generated .lake build artifacts
```

## H.4 Clean semantic/package validation

Before the isolation run, only validator-generated:

```text
.lake/
lake-manifest.json
```

were removed from the isolated checkout.

Then:

```text
validate_v1_7_draft_1_3_corpus.py
  --skip-inherited
  --skip-lean
  --skip-tla
```

was executed.

Job:

```text
20260922T134753Z-831fd595bb
```

Result:

```text
return code: 0

v1.7 Draft 1.3 corpus validation checks passed.
Structured report written to DRAFT1_3_VALIDATION_REPORT.json with warnings.
```

Structured report:

```text
corpus_errors: []
status: pass
```

Checked stages:

```text
schema_and_yaml_parse
v17_fixtures
sql
openapi
kernel_syscalls
registries
docs
inventory
```

Additional checked contract:

```text
schema_sql_persistence
```

## H.5 Direct Lean result

Job:

```text
20260922T134922Z-edc3c151a2
```

Toolchain:

```text
leanprover/lean4:v4.29.1
lake_available: true
```

Result:

```text
status: failed_lake_build
return code: 1
```

Failed target:

```text
Duotronic.BayesianLogic
```

Compiler diagnostics include absent instances for:

```text
LE ProbabilityBP
OfNat ProbabilityBP 10000
Repr ProbabilityBP
```

Other listed Duotronic modules built before the failed target.

No unapproved axiom files were reported by the runner.

## H.6 Direct TLA result

Job:

```text
20260922T135028Z-73d1a0dc27
```

Module:

```text
BayesianKnotFirstClassPromotion
```

Result:

```text
return code: 0
status: advisory_pass_tlc_unavailable
static_errors: []
tlc_available: false
```

This is an advisory static pass only.

## H.7 Focused Xavi Memory run

```text
job: test_xavi_memory_core_pinned_container_0917
return code: 0

import_ok
........... [100%]
11 passed in 1.31s
```

This is separate implementation evidence.

## H.8 Xavi Memory broad-suite collection failure

```text
ModuleNotFoundError: No module named 'pypdf'
```

The result is an environment failure, not a contract result.

## H.9 Evidence rule used by this paper

The white paper uses:

```text
semantic validator pass != formal proof
formal source present != successful formal build
TLA static pass != TLC model check
independent contract pass != WGCA implementation conformance
focused WGCA tests != full WGCA validation
```

Only actually executed results are reported as evidence.

# Appendix I — Reproducibility Record for Revision 5

## I.1 Active independent contract package

```text
/datastore2/duotronics-whitepaper-v4/Duotronics-main/
  build_docs/witness_contract/v1.6 - Draft 5.3.18
```

## I.2 Canonical validator

Fresh canonical validation jobs included:

```text
20260922T170854Z-305d7bc9b3
20260922T172525Z-dc56f27a6d
```

Observed result:

```text
contract_version: v1.6-draft-5.3.18
status: pass
failure_count: 0
production_authority_activated: false
```

## I.3 Exact strict Lean build

Job:

```text
20260922T170229Z-67aa8238d7
```

Result:

```text
return code: 0
Build completed successfully (17 jobs).
LEAN_DIRECT_STRICT=PASS
Lean 4.29.1
Lake 5.0.0-src+f72c35b
```

The additional `formal/lean4/AuthorityDomainV5318.lean` compile also returned successfully.

## I.4 Strict TLC model check

TLC harness tool:

```text
/datastore2/duotronics-whitepaper-v4/Duotronics-main/harness/bin/tools/tla2tools.jar
TLC 2.19 of 08 August 2024
SHA-256: 936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88
```

Strict model-check job:

```text
20260922T170502Z-b542da00a4
```

Result:

```text
overall_status: pass
tlc_available: true
12 modules checked
all module return codes: 0
```

Per-module summary job:

```text
20260922T170747Z-c696f9aa06
```

## I.5 Declared cryptographic runtime

The contract's `requirements-pq-runtime.txt` pins:

```text
cryptography==46.0.0
pqcrypto==0.3.4
pycryptodomex==3.23.0
```

The initial use of `pqcrypto 1.0.0` produced a large false regression cascade because the expected `generate_keypair()` API was absent. Restoring the declared pins reduced the package-local suite from 178 failures to three historical fixture incompatibilities.

## I.6 Parent-retention preservation

The two temporarily edited historical tests were verified as retained 5.3.17 files and restored from the sibling 5.3.17 package. Their path-bound IDs matched the retained parent manifest exactly after restoration.

The canonical 5.3.18 validator then passed again.

## I.7 External immutable-copy regression runner

Harness path:

```text
/datastore2/duotronics-whitepaper-v4/Duotronics-main/
  harness/bin/tools/run_witness_5318_regression.py
```

Final job:

```text
20260922T174009Z-0e376c0de2
```

Result:

```text
canonical validator: PASS, failure_count 0
329 passed, 6 skipped, 87 subtests passed
return code: 0
```

Skip reasons:

```text
Draft 5.3.14 regeneration tests: superseded by whole-corpus 5.3.17 registry generator
Draft 5.3.15 regeneration tests: superseded by whole-corpus 5.3.17 registry generator
Draft 5.3.16 regeneration tests: superseded by whole-corpus 5.3.17 registry generator
```

## I.8 Broad acceptance and nightly fuzz

Acceptance job:

```text
20260922T170938Z-c808e9cc8f
```

Result:

```text
178 normative passed
13 meta-runtime passed
246 full-suite passed
0 skipped
acceptance gate green
```

Nightly job:

```text
20260922T172204Z-cb92f594d1
```

Result:

```text
full acceptance: green
extended fuzz: 3 passed, 243 deselected
nightly: green
```

## I.9 Evidence interpretation

Revision 5 uses the following non-collapse rules for its own claims:

```text
validator pass != theorem proof
Lean build pass != runtime correctness
TLC finite-model pass != unbounded implementation proof
regression pass != production safety proof
Duotronics contract evidence != WGCA implementation evidence
WGCA implementation evidence != cognitive/biological/metaphysical evidence
```

