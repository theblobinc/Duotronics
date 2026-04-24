# Duotronic Witness Contract v10.6

**Status:** Research specification draft  
**Version:** 10.6-standalone-revision  
**Supersedes:** SRNN Recurrent Witness Contract v9/v9.1 research drafts and v10.0 rewrite draft  
**Document kind:** Normative runtime contract plus research diagnostics  
**Primary purpose:** Define how Duotronic witness facts are extracted, canonicalized, stored, retrieved, transported, replayed, tested, and safely promoted.

> Drafting note. This document is written in a one-based Duotronic style. Public claim labels, checklist labels, and section labels begin at 1. External systems such as DBP wire cells, IEEE formats, conventional arithmetic, and physics literature may still contain ordinary zero-valued quantities where their own standards require them. The Duotronic rule is not that zero is forbidden everywhere; the rule is that native public Duotronic labels and document claim classes do not begin at zero.

---

## Revision 10.6 expansion summary

> **Status tag:** reference

The v10.6 revision keeps all v10.4 material and expands the Witness Contract into a fuller internal runtime source specification. The main additions are a source-architecture view from the witness side, a threat model, a witness lifecycle chapter, a failure-code registry, a replay identity profile, a telemetry catalog, policy-shield decision tables, an expanded conformance harness, migration/versioning rules, and a full end-to-end worked trace.

The v10.6 additions do not weaken any hard rule. They make the hard rules more operational:

1. normal-form-before-trust remains primary;
2. transport-before-semantics remains primary;
3. bypass remains valid behavior;
4. failed canonicalization remains a first-class state;
5. retention metrics remain diagnostics unless a policy explicitly promotes them;
6. raw witness evidence, canonical identity, transport encoding, replay identity, and policy authority remain separate.


---

## Document status tag key

> **Status tag:** reference

Every major section carries exactly one **primary** status tag so humans and tools can distinguish the normative core from examples, experiments, future work, and analogies. If a section touches more than one concern, it may add a separate `Related tags:` line, but machine parsers MUST treat `Status tag` as the single primary classification.

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding semantics for the active specification. | Conforming implementations must follow it. |
| `reference` | Examples, algorithms, fixtures, schemas, or implementation aids. | Useful for implementation, but not itself a new semantic rule unless cited by a normative section. |
| `research` | Experimental diagnostic, metric, benchmark, or pruning method. | Must remain opt-in until benchmarked and promoted. |
| `future` | Named work not completed in this document. | Must not be treated as live semantics. |
| `analogy` | Outside-field comparison or motivation. | Must not be promoted into proof, runtime authority, or external-domain claim. |

## 1. Executive summary

> **Status tag:** reference

The Duotronic Witness Contract v10.6 defines the runtime discipline for systems that operate on witness-bearing state.

The core rule is:

> A witness fact is not trusted merely because it is observed. It becomes trusted only after passing through declared validation, canonicalization, policy gating, and replay-stable identity checks.

The v10.6 revision keeps the strong v9/v10 idea that stable witness facts must be in canonical normal form before they are trusted, stored, retrieved, compared, replayed, or promoted.

The v10.x line establishes five core refinements.

1. It uses one-based claim classes C1 through C6.
2. It formalizes retained-correlation diagnostics as optional engineering metrics, not physics claims.
3. It embeds standalone minimum definitions for DPFC family objects, Witness8 rows, DBP frames, and WSB2 sparse rows so the witness contract can be read without external Duotronic documents.
4. It adds falsification and pruning rules so weak witness families, normalizers, metrics, adapters, or retention claims can be removed quickly.
5. It requires every retention metric to declare its extractor, similarity function, baseline suite, pass rule, preservation class, and failure action.

The v10.6 revision additionally polishes the source-spec layer: single-primary status tags replace hybrid tags, the revision summary distinguishes v10.x fundamentals from revision-specific expansion work, and the source-corpus status table now marks which companion documents exist, which need drafts, and which remain future work.

This document is written for implementers and AI systems working on Duotronic internal source documents. The vocabulary is intentionally dense. It specifies what must happen before a witness can affect recurrent state, lookup memory, controller policy, structural promotion, outbound transport, or persistent storage.

---

## 2. Scope and non-claims

> **Status tag:** normative

### 2.1 Scope

This contract governs:

1. fast witness extraction;
2. canonical normal-form construction;
3. lookup-backed witness memory;
4. recurrent witness state;
5. event-time controller updates;
6. structural proposal and promotion;
7. policy shielding and bypass modes;
8. DBP-style frame ingress;
9. WSB2-style sparse-row ingress;
10. Witness8 row decoding;
11. DPFC family-sensitive witness registry behavior;
12. correlation-retention diagnostics;
13. replay identity;
14. schema migration;
15. conformance testing;
16. pruning and demotion.

### 2.2 Non-claims

This contract does not claim that:

1. SRNN witness state is consciousness;
2. retained-correlation diagnostics are physical quantum coherence;
3. virtual particles prove Duotronic witness theory;
4. family geometry should be trusted without canonicalization;
5. DBP-style transport validation is optional when payloads look reasonable;
6. WSB2 sparse rows are mathematical numerals;
7. Witness8 rows are automatically canonical DPFC objects;
8. a model can rewrite its own schema without migration and replay validation;
9. retention metrics are meaningful without baselines;
10. analogies are implementation authority.

The contract is an engineering safety and semantics document. Physics language is allowed only as labeled analogy or as part of a separately approved physics profile.

---

## 3. Claim classes

> **Status tag:** normative

The contract uses one-based claim classes.

| Claim class | Name | Witness-contract use |
|---|---|---|
| C1 | Definition | Define witness objects, states, registries, maps, schemas, and adapters. |
| C2 | Theorem candidate | Prove determinism, replay, or preservation properties. |
| C3 | Implementation invariant | Enforce validation, canonicalization, replay, and shield behavior. |
| C4 | Benchmark-supported claim | Show a witness path improves a measurable system outcome. |
| C5 | Analogy or research heuristic | Use QCD-style retention patterns as a method analogy. |
| C6 | External-domain claim | Claim correspondence to physics or other external systems. |

A runtime MUST NOT treat a C5 analogy as C3 implementation authority.

A retention metric MUST NOT be promoted from C4 to C6 without a separate external-domain evidence profile.

---

## 4. Architecture overview

> **Status tag:** normative

The witness system is organized into five runtime levels plus one memory layer.

| Runtime level | Symbol | Object | Update cadence | Primary role |
|---|---|---|---|---|
| L1 | \(W_t\) | `WitnessSignature` | per packet/event | extract local witness evidence |
| L2 | \(\widetilde{W}_t\) | `RecurrentWitnessState` | per packet/event | maintain bounded continuity |
| L2M | \(M_t\) | `WitnessLookupMemory` | lookup per packet, maintenance async | retrieve stable normal-form facts |
| L3 | \(\widehat{W}_\tau\) | `MetaRecurrentWitness` | event time | tune bounded policy coordinates |
| L4 | \(\overline{W}_\mu\) | `ArchitecturalWitness` | maintenance windows | propose structural changes |
| L5 | \(\breve{W}\) | `PolicyShield` | fixed/slow | enforce feasibility, rollback, bypass |

The naming L1 through L5 is retained because these are runtime layers and already one-based.

---

## 5. Hard rules

> **Status tag:** normative

The following hard rules govern all conforming deployments.

### 5.1 Normal-form-before-trust rule

Stable witness facts MUST be represented in canonical normal form before they are trusted, stored, retrieved, compared, replayed, or promoted.

### 5.2 Transport-before-semantics rule

Transport validation MUST precede semantic interpretation.

A payload from any of the following MUST NOT enter authoritative witness memory:

1. failed frame;
2. failed shape check;
3. failed security check;
4. failed CRC or integrity tag;
5. failed WSB2 decode;
6. failed Witness8 row validation;
7. failed numeric validation;
8. failed schema validation;
9. failed canonicalization.

### 5.3 No silent family reinterpretation

A witness family identifier, family schema version, geometry registry version, and normalizer version MUST NOT be silently changed.

Any semantic change requires:

1. migration path;
2. replay checks;
3. must-preserve invariant comparison;
4. rollback plan;
5. policy approval.

### 5.4 No canonicalization success by absence of error

Canonicalization failure is a first-class state. It MUST NOT be counted as:

1. successful lookup;
2. successful replay;
3. authoritative contradiction;
4. trusted memory write;
5. promotion evidence.

### 5.5 Bypass is valid behavior

If validation, canonicalization, lookup, or family-sensitive confidence fails, the system MUST still operate through degraded, family-bypass, transport-bypass, lookup-bypass, or full-bypass behavior.

### 5.6 Geometry is advisory until canonicalized

Raw geometry hints from L1 are advisory until the witness-family registry validates and canonicalizes them.

### 5.7 Retention metric discipline

A retention metric MUST NOT be treated as meaningful unless it declares:

1. invariant kind;
2. extractor;
3. similarity function;
4. transformation;
5. baseline suite;
6. preservation class;
7. pass rule;
8. failure action.

---

## 6. Core state sets

> **Status tag:** normative

### 6.1 Semantic witness state

A witness-bearing position may be in one of these semantic states:

\[
\Xi=\{\mathsf{empty},\mathsf{unknown},\mathsf{conditional},\mathsf{realized},\mathsf{error}\}.
\]

| State | Meaning |
|---|---|
| `empty` | no semantic object is present |
| `unknown` | a position is in scope but lacks committed value |
| `conditional` | a candidate exists but is not yet trusted for irreversible action |
| `realized` | a committed witness object exists |
| `error` | a malformed or rejected payload is retained for audit |

### 6.2 Presence status lattice

Witness systems MUST distinguish:

1. `structurally_absent`;
2. `present_unknown`;
3. `present_zero_value`;
4. `present_nonzero_value`;
5. `present_invalid`;
6. `rejected_untrusted`.

This prevents token-free absence from collapsing into numeric zero.

### 6.3 Trust status

A witness object has a trust status:

1. `raw`;
2. `transport_validated`;
3. `semantic_validated`;
4. `canonicalized`;
5. `trusted_for_lookup`;
6. `trusted_for_recurrence`;
7. `trusted_for_promotion`;
8. `rejected`.

A deployment may use fewer states internally only if it preserves these distinctions at policy boundaries.

---

## 7. Standalone embedded terminology

> **Status tag:** normative

This section defines enough DPFC, Witness8, DBP, and WSB2 material for this contract to stand alone.

### 7.1 DPFC minimum profile

A DPFC family is a declared finite numeral family over a positive realized core.

The positive realized core is:

\[
\mathbb{U}^{+}=\{\mu_1,\mu_2,\mu_3,\ldots\}.
\]

The first realized magnitude \(\mu_1\) is not structural absence and not ordinary exported zero.

A family \(F\) has:

1. `family_id`;
2. `family_schema_version`;
3. finite ordered digit alphabet \(\Delta_F=(\delta_1,\ldots,\delta_{b_F})\);
4. bijective modulus \(b_F\);
5. canonical digit order;
6. positional evaluation;
7. serializer;
8. normalizer;
9. optional witness geometry;
10. optional degeneracy rules.

For a word:

\[
M=\delta^{(F)}_{i_1}\cdots\delta^{(F)}_{i_k},
\]

the family value is:

\[
\operatorname{val}_F(M)=\sum_{j=1}^{k} i_j b_F^{k-j}.
\]

The family-to-core bridge is:

\[
\Phi_F(M)=\mu_{\operatorname{val}_F(M)}.
\]

Family conversion from \(F\) to \(G\) preserves core magnitude by:

\[
\Psi_{F\to G}=\Phi_G^{-1}\circ\Phi_F.
\]

### 7.2 DPFC export boundary

The positive index map is:

\[
\iota(\mu_n)=n.
\]

The conventional nonnegative export map is:

\[
E_{\mathbb{U}}(\mu_n)=n-1.
\]

The nonnegative export map is not an ordinary addition-preserving bridge for Duotronic realized-step addition. Any witness profile that exports DPFC values MUST declare whether it uses:

1. positive-index operation preservation; or
2. nonnegative export with correction.

### 7.3 Witness8 minimum profile

A `Witness8` row has eight ordered features:

1. `value_norm`;
2. `n_sides_norm`;
3. `center_on`;
4. `activation_density`;
5. `kind_flag`;
6. `band_position`;
7. `parity`;
8. `degeneracy`.

A `Witness8` row is a transport or implementation object. It is not automatically a DPFC canonical object.

A decoder MUST output one of:

1. `decoded_exact`;
2. `decoded_lossy`;
3. `token_free_absent`;
4. `present_invalid`;
5. `unsupported_family`;
6. `ambiguous`;
7. `profile_mismatch`.

### 7.4 Token-free absence rule

An all-inactive `Witness8` row under the active profile represents token-free absence:

```text
[0, 0, 0, 0, 0, 0, 0, 0]
```

Expected result:

```text
presence_status = structurally_absent or token_free_absent
trusted_for_lookup = false
numeric_zero = not inferred
```

### 7.5 Present numeric-zero rule

If a profile supports ordinary numeric zero, numeric zero MUST be represented as a present row, not as an all-inactive row.

A decoder that collapses token-free absence and numeric zero is non-conformant.

### 7.6 DBP minimum frame model

For this contract, DBP means a byte/frame transport boundary with:

1. frame shape;
2. profile identifier;
3. payload length;
4. structural fields;
5. semantic payload region;
6. integrity field such as CRC or authenticated tag;
7. optional encryption metadata;
8. optional sequence number;
9. optional replay protection field.

DBP is not a numeral family. DBP structural fields MUST NOT be witness-encoded.

### 7.7 WSB2 minimum sparse-row model

For this contract, WSB2 means a sparse semantic row or bitmap profile with:

1. active bitmask;
2. row width;
3. profile identifier;
4. semantic lane definitions;
5. optional compressed values;
6. optional row checksum;
7. optional row provenance tag.

An inactive WSB2 lane is not numeric zero unless the active profile explicitly marks the lane as present and zero-valued.

### 7.8 Standalone ingress order

The standalone ingress order is:

```text
frame shape validation
-> structural field validation
-> integrity/security validation
-> decryption if applicable
-> WSB2 or payload decode
-> Witness8 row validation if applicable
-> family registry lookup
-> canonicalization
-> policy gating
-> lookup/recurrent use
```

Any trusted semantic use before this order completes is non-conformant.

### 7.9 Standalone embedded boundary invariants

> **Status tag:** normative

The embedded terminology above includes reference material, but the following boundary invariants are normative for this witness contract.

A conforming implementation MUST preserve these invariants:

1. DPFC family objects are not trusted until canonicalized under a versioned family registry.
2. Witness8 rows are not canonical DPFC objects until decoded, validated, and canonicalized.
3. DBP-style frames are transport containers, not numeral families.
4. WSB2 inactive lanes are absence at the sparse-row/profile layer, not numeric zero.
5. Token-free absence and present numeric zero MUST remain distinct at every trust boundary.
6. Transport validation MUST precede semantic interpretation.
7. Family conversion MAY lose source-family identity only when that loss is declared as `expected_loss` or preserved as metadata.
8. Exported DPFC arithmetic MUST declare whether it uses positive-index operation preservation or nonnegative export correction.

---

## 8. L1 object witness

> **Status tag:** normative

### 8.1 Purpose

L1 extracts local witness evidence from the current packet, event, frame, row, or observation. It is fast, lossy, and bounded.

### 8.2 Required fields

A `WitnessSignature` SHOULD be able to express:

1. entity cues;
2. source cues;
3. event cues;
4. role cues;
5. local contradiction cues;
6. confidence and evidence measures;
7. family hints;
8. geometry hints;
9. provenance identifiers;
10. transport validation status when the witness arrived through a frame;
11. profile identifiers;
12. row-decoder output state.

### 8.3 L1 constraints

L1 MUST be computable on the hot path. It MUST NOT depend on future packets. It MAY be uncertain, but uncertainty must be represented explicitly.

Family hints emitted by L1 are advisory until canonicalized.

---

## 9. L2 recurrent witness state

> **Status tag:** normative

### 9.1 Purpose

L2 maintains short-horizon continuity across adjacent events. It handles recurrence, callback pressure, coherence drift, contradiction accumulation, and local family mass.

### 9.2 Canonical L2 update stages

A conforming L2 update SHOULD expose these stages:

1. family mass update;
2. scene/story axis update;
3. callback persistence update;
4. coherence drift update;
5. regime evidence update;
6. sector/path trace update;
7. contradiction pressure update;
8. retention diagnostic update when enabled.

### 9.3 L2 safety rules

L2 MAY consume only accepted L3 policy settings.

L2 MAY consume only gated and shield-permitted L2M retrievals.

L2 MUST remain meaningful under full lookup bypass.

Canonicalization failures reduce evidence. They do not become authoritative contradictions unless a policy explicitly declares the invariant must preserve and supplies a safe interpretation.

---

## 10. L2M lookup witness memory

> **Status tag:** normative

### 10.1 Purpose

L2M stores and retrieves stable witness facts more cheaply than repeated reconstruction. It is a lookup substrate, not a free-form reasoning engine.

### 10.2 Key path

The canonical key path is:

\[
k_t^{\mathrm{raw}}\xrightarrow{\operatorname{Canon}_{\sigma,\nu,\mathcal F}}k_t^{\mathrm{nf}}\xrightarrow{\Lambda}r_t^{\mathrm{lookup}}.
\]

Where:

1. \(k_t^{\mathrm{raw}}\) is the raw typed witness bundle;
2. \(\sigma\) is schema version;
3. \(\nu\) is normalizer/canonicalizer version;
4. \(\mathcal F\) is the witness-family registry;
5. \(k_t^{\mathrm{nf}}\) is the canonical normal-form key;
6. \(\Lambda\) is the lookup operator.

### 10.3 Gated injection

Retrieved memory is injected only through a bounded gate:

\[
\gamma_t=G(h_t^{\mathrm{ctx}},r_t^{\mathrm{lookup}},c_t^{\mathrm{norm}},s_t^{\mathrm{policy}}),
\]

\[
h_t^+=h_t+\gamma_t\odot r_t^{\mathrm{lookup,mix}}.
\]

Low normalization confidence MUST NOT increase retrieval authority.

### 10.4 L2M state fields

A `WitnessLookupMemory` object SHOULD track:

1. backend family;
2. table count;
3. table width;
4. value dimension;
5. head enable mask;
6. collision rate;
7. hit rate;
8. gate fire rate;
9. normalization failure rate;
10. normalization confidence;
11. lookup latency;
12. schema version;
13. normalizer version;
14. family registry version;
15. geometry registry version;
16. bypass mode;
17. profile identifier;
18. transport reject rate;
19. Witness8 decode failure rate;
20. WSB2 inactive-lane ambiguity rate.

### 10.5 Hashing rule

Hashing MUST operate on canonical normal form whenever the key class defines a normal form.

Hashing raw surface bundles is prohibited for authoritative family-sensitive lookup.

---

## 11. Witness family registry

> **Status tag:** normative

### 11.1 Purpose

The `WitnessFamilyRegistry` declares how family-sensitive witness classes are validated, canonicalized, serialized, replayed, and compared.

### 11.2 Registry entry fields

A registry entry MUST include:

1. `family_id`;
2. `family_schema_version`;
3. `kind`;
4. `dimension_scope`;
5. `generator_data`;
6. `witness_schema`;
7. `degeneracy_schema`;
8. `canonicalization_policy`;
9. `canonical_selection_rule`;
10. `serializer_policy`;
11. `normalizer_policy`;
12. `geometry_registry_ref`;
13. `replay_identity_fields`;
14. `retention_preservation_class` when retention diagnostics are enabled;
15. `export_policy` when DPFC values cross a conventional arithmetic boundary.

### 11.3 Registry kinds

Allowed kinds include:

1. `generic_symbolic`;
2. `polygon_progression`;
3. `reflection_family`;
4. `path_orbit_family`;
5. `dpfc_family`;
6. `custom_declared_family`.

### 11.4 Reflection and path discipline

Reflection or path-orbit entries MUST additionally declare:

1. generator data;
2. orbit equivalence relation;
3. reduced-word rule;
4. sector or chamber reduction rule;
5. canonical representative selection algorithm;
6. witness-history preservation policy;
7. ambiguity rejection policy.

Raw path evidence and canonical path evidence must remain distinguishable.

---

## 12. Canonicalization pipeline

> **Status tag:** normative

### 12.1 Pipeline stages

The canonicalization pipeline is:

1. schema identify;
2. field order normalization;
3. explicit absent-field materialization;
4. family registry lookup;
5. generic field validation;
6. declared normalizer execution;
7. geometry-aware reduction when applicable;
8. canonical representative selection;
9. confidence and diagnostics computation;
10. canonical wire/key materialization.

### 12.2 Failure outputs

Canonicalization may output:

1. `canonical_success`;
2. `canonical_success_low_confidence`;
3. `generic_only_success`;
4. `family_bypass_required`;
5. `malformed_reject`;
6. `ambiguous_reject`;
7. `normalizer_error`;
8. `schema_mismatch`;
9. `registry_mismatch`;
10. `export_policy_mismatch`;
11. `presence_zero_collapse_reject`.

Only successful states may enter authoritative lookup, and even then policy may gate them.

### 12.3 Reference pseudocode

```text
canonicalize_witness_key_bundle(raw_bundle, registries, policy):
    schema = identify_schema(raw_bundle)
    bundle = apply_schema_order(raw_bundle, schema)
    bundle = materialize_declared_absent_fields(bundle, schema)

    validate_presence_status(bundle)
    validate_export_policy_if_present(bundle)

    family = registries.family.get(bundle.family_id)

    if family is missing:
        return canonicalize_generic_or_reject(bundle, policy)

    validate_family_schema_version(bundle, family)
    validate_required_fields(bundle, family)

    if family.normalizer exists:
        bundle = run_declared_normalizer(bundle, family.normalizer)

    if family.kind is reflection_family or path_orbit_family:
        bundle = reduce_orbit_sector_path(bundle, family.geometry)

    canonical = select_canonical_representative(bundle, family)
    diag = compute_canonicalization_diagnostics(raw_bundle, canonical)
    return materialize_normal_form(canonical, diag)
```

---

## 13. L3 event-time controller

> **Status tag:** normative

### 13.1 Purpose

L3 is a sparse, bounded event-time controller. It may tune a small number of policy coordinates. It does not rewrite schemas, registries, normalizers, or geometry rules.

### 13.2 Event-time set

Let \(\mathbb T_{\mathrm{event}}\) be the set of event times where L3 may update. Packet time \(t\) is not the same as event time \(\tau\).

### 13.3 Controlled coordinates

The default controlled vector is:

\[
\theta_\tau=\{\ell_{\lambda,k},\ell_\rho,b_g,\ell_B,\ell_C,\ell_R\}.
\]

Where:

1. \(\ell_{\lambda,k}\) is a log decay offset;
2. \(\ell_\rho\) is callback persistence logit;
3. \(b_g\) is lookup gate bias;
4. \(\ell_B\) is lookup-budget logit;
5. \(\ell_C\) is canonicalization-confidence threshold control;
6. \(\ell_R\) is retention-diagnostic sensitivity when enabled.

### 13.4 Prohibited L3 authority

L3 MUST NOT change:

1. hidden dimension;
2. gate topology;
3. table shape;
4. key schema;
5. family registry definition;
6. normalizer algorithm;
7. automaton structure;
8. geometry reducer;
9. migration plan;
10. DBP validation rules;
11. WSB2 lane semantics;
12. Witness8 absence/zero policy;
13. retention metric extractor;
14. retention metric similarity function.

Those belong to L4/L5 and require migration or policy review.

---

## 14. L4 architectural witness

> **Status tag:** normative

### 14.1 Purpose

L4 handles structural proposals only through versioned, validated, reversible changes.

### 14.2 Allowed proposal families

L4 MAY propose:

1. enabling or disabling an already registered witness family;
2. adjusting gate mixing coefficients;
3. pruning high-cost low-value families;
4. changing lookup table dimensions;
5. changing key schema with migration;
6. replacing a normalizer after equivalence validation;
7. replacing a geometry reducer after replay validation;
8. altering retention metric thresholds;
9. changing WSB2 profile binding;
10. changing cache and prefetch policy;
11. adding a new retention metric spec;
12. changing export policy only with explicit migration.

### 14.3 Required migration plan

Any proposal that changes state layout, key schema, lookup table schema, family semantics, normalizer identity, automaton identity, geometry canonicalization, export policy, or transport binding MUST include a `StateMigrationPlan`.

### 14.4 Promotion rule

Promotion is atomic and occurs only at sequence boundaries.

A candidate cannot be promoted if it worsens any must-preserve invariant beyond policy tolerance, even if it improves a soft utility metric.

---

## 15. L5 policy shield

> **Status tag:** normative

### 15.1 Purpose

L5 defines the feasible set and runtime safety behavior.

### 15.2 Runtime modes

| Mode | Meaning | Dominant behavior |
|---|---|---|
| `normal` | budgets healthy | bounded L3 and staged L4 allowed |
| `degraded` | one or more budgets marginal | clamp L3, reduce lookup, freeze risky L4 |
| `family_bypass` | family-sensitive canonicalization unhealthy | generic path allowed, family-sensitive path bypassed |
| `transport_bypass` | transport validation failed | semantic payload excluded |
| `lookup_bypass` | lookup memory unsafe | recurrent state continues without lookup injection |
| `full_bypass` | memory path unsafe | lookup disabled, recurrent core continues |

### 15.3 Hard constraints

Hard constraints include:

1. memory ceiling;
2. latency ceiling;
3. lookup collision ceiling;
4. canonicalization-failure ceiling;
5. replay-normal-form mismatch ceiling;
6. no silent canonicalization drift;
7. no silent family reinterpretation;
8. no semantic trust before transport validation;
9. no promotion without rollback path;
10. no absence/numeric-zero collapse;
11. no retention metric without baseline;
12. no export-policy silence.

Soft objective improvement never relaxes hard constraints.

---

## 16. DPFC binding

> **Status tag:** normative

### 16.1 Boundary

The witness contract may carry DPFC family objects, but it does not redefine DPFC arithmetic.

The embedded DPFC minimum profile in this document is sufficient for witness-contract conformance. A richer DPFC source may add more families or proof machinery, but it cannot weaken this contract's trust, validation, canonicalization, or replay rules.

DPFC provides:

1. family identity;
2. canonical family serialization;
3. family-to-core bridge;
4. inter-family conversion;
5. witness and degeneracy rules;
6. preservation classes for conversion;
7. export policy declarations.

The witness contract provides:

1. canonicalization-before-trust;
2. lookup memory;
3. replay identity;
4. policy gating;
5. retention telemetry;
6. runtime promotion rules;
7. transport and row ingress discipline.

### 16.2 DPFC object key

A DPFC-backed witness key SHOULD include:

1. `dpfc_family_id`;
2. `dpfc_schema_version`;
3. `canonical_digits`;
4. `core_magnitude_hash` when available;
5. `witness_history_hash` when preserved;
6. `normalizer_version`;
7. `geometry_registry_version`;
8. `export_policy`.

### 16.3 Arithmetic boundary

L2M may store DPFC-derived facts, but it must not invent DPFC arithmetic.

Arithmetic operations must call DPFC-conformant evaluators or operate on exported values with declared bridges.

A witness key MUST NOT treat nonnegative exported values as operation-preserving unless the adapter declares the correction policy.

---

## 17. Witness8 binding

> **Status tag:** normative

### 17.1 Witness8 fields

The implementation witness row has eight ordered fields:

1. `value_norm`;
2. `n_sides_norm`;
3. `center_on`;
4. `activation_density`;
5. `kind_flag`;
6. `band_position`;
7. `parity`;
8. `degeneracy`.

### 17.2 Binding rule

Witness8 rows are transport/implementation objects. They are not automatically canonical DPFC objects.

The receiver must:

1. decode them through an active profile;
2. validate ranges;
3. distinguish token-free absence from numeric zero;
4. distinguish invalid present rows from absence;
5. canonicalize into witness normal form;
6. apply policy gating before lookup or recurrence.

### 17.3 Presence and numeric-zero rule

A token-free absent row is an all-inactive row under the active profile.

Numeric zero, when it is a real present value, MUST be encoded as a present non-absent witness row.

A decoder that collapses these concepts is non-conformant.

### 17.4 Invalid row policy

If a row is present but invalid, the decoder MUST:

1. mark it invalid;
2. emit telemetry;
3. prevent it from entering authoritative memory;
4. retain it only as audit state when policy allows.

---

## 18. DBP and WSB2 ingress binding

> **Status tag:** normative

### 18.1 Ingress order

Ingress from DBP-style frames or WSB2-style sparse rows MUST follow this order:

1. parse exact frame shape;
2. validate structural fields;
3. validate CRC/security policy;
4. decrypt if applicable;
5. apply numeric checks after decryption;
6. decode WSB2 or semantic witness rows;
7. validate Witness8 row contracts;
8. canonicalize witness family semantics;
9. apply lookup and recurrent use only after trust gates pass.

### 18.2 Structural no-witness fence

Structural wire fields MUST NOT be witness-encoded. Witness encoding belongs only to semantic payload regions authorized by the active profile.

### 18.3 Untrusted debug retention

A failed frame may be retained for debugging only if marked `rejected_untrusted` and excluded from normal lookup, recurrence, and promotion.

### 18.4 WSB2 inactive lane rule

An inactive WSB2 lane is absence at the row/profile level, not numeric zero.

A present zero lane must be encoded as present and zero-valued under the active profile.

---

## 19. Correlation-retention diagnostics

> **Status tag:** research

### 19.1 Status

Correlation-retention diagnostics are optional C4 research diagnostics. They do not weaken canonicalization, transport validation, replay, or shield rules.

### 19.2 Motivation

The STAR QCD confinement measurement is methodologically useful because it studies an upstream hidden correlation through downstream observable correlations after transformation.

Witness systems face an analogous engineering question:

> What declared witness invariants survive canonicalization, transport, lookup, replay, migration, export, and conversion?

This is an analogy. It is not a physics claim.

### 19.3 Invariant extractor

Let \(I_K\) extract invariant kind \(K\).

Examples:

1. family identifier;
2. core magnitude;
3. canonical storage hash;
4. orbit identifier;
5. sector identifier;
6. reduced path;
7. provenance class;
8. semantic state;
9. transport hash;
10. replay hash;
11. export policy;
12. normalizer version;
13. geometry registry version.

### 19.4 Transformation

A transformation \(T\) may be:

1. canonicalization;
2. lookup;
3. replay;
4. family conversion;
5. Witness8 encode;
6. Witness8 decode;
7. DBP transport;
8. WSB2 sparse-row transport;
9. migration;
10. export.

### 19.5 Similarity function

Each invariant kind \(K\) MUST declare:

\[
\operatorname{sim}_K(a,b)\in[0,1].
\]

Allowed similarity families include:

1. `exact_equal`;
2. `hash_equal`;
3. `ordered_sequence_equal`;
4. `set_equal`;
5. `tolerance_numeric`;
6. `class_equivalent`;
7. `expected_loss_declared`;
8. `prohibited_gain_detector`.

### 19.6 Retention score

For witness \(w\) and transformation \(T\):

\[
R_K(w,T)=\operatorname{sim}_K(I_K(w),I_K(T(w))).
\]

### 19.7 Loss score

\[
L_K(w,T)=1-R_K(w,T).
\]

### 19.8 Baseline-adjusted retention

Let \(B_K\) be a baseline from shuffled, long-separation, malformed, schema-mismatch, lookup-bypass, transport-invalid, or unrelated controls:

\[
\operatorname{BAR}_K(w,T)=R_K(w,T)-B_K.
\]

\[
\operatorname{NRL}_K(w,T)=\frac{R_K(w,T)-B_K}{1-B_K+\epsilon}.
\]

Retention claims without baselines remain diagnostic hints.

### 19.9 RetentionMetricSpec

Every active metric MUST have a `RetentionMetricSpec`.

```json
{
  "metric_id": "canonical-storage-through-replay@v1",
  "invariant_kind": "canonical_storage_hash",
  "extractor_id": "canonical-storage-hash-extractor@v1",
  "similarity_id": "hash_equal@v1",
  "transformation": "replay",
  "source_profile": "witness-key@v10.6",
  "target_profile": "witness-key@v10.6",
  "preservation_class": "must_preserve",
  "baseline_suite": [
    "shuffled_pair",
    "schema_mismatch",
    "malformed_witness",
    "transport_invalid"
  ],
  "pass_rule": {
    "min_retention": 1.0,
    "max_baseline": 0.01,
    "min_normalized_lift": 0.99
  },
  "failure_action": "reject_or_rollback"
}
```

### 19.10 Metric elasticity prohibition

A retention metric is non-conformant if:

1. the extractor is unversioned;
2. the similarity function is undeclared;
3. the baseline suite is omitted;
4. the pass rule is absent;
5. the preservation class is absent;
6. failure action is absent;
7. the metric definition changes after seeing results;
8. expected loss is treated as unexpected failure;
9. prohibited gain is ignored.

---

## 20. Baseline discipline

> **Status tag:** research

A deployment that reports retained-correlation metrics SHOULD include:

1. shuffled-pair baseline;
2. long event-time separation baseline;
3. schema-mismatch baseline;
4. malformed witness baseline;
5. lookup-bypass baseline;
6. DBP-invalid-frame baseline;
7. WSB2-inactive-lane baseline;
8. family-conversion expected-loss baseline;
9. replay-under-old-schema baseline;
10. export-policy-mismatch baseline.

The baseline must be reported with the metric.

---

## 21. Retention preservation classes

> **Status tag:** research

Every retention invariant must have a class.

| Class | Meaning | L5 action |
|---|---|---|
| `must_preserve` | loss means conformance failure | reject, bypass, or rollback |
| `should_preserve` | loss is warning | degrade or log |
| `metadata_only` | loss does not alter canonical identity | log only |
| `expected_loss` | loss is intended | no alert if declared |
| `prohibited_gain` | invariant must not appear from nowhere | reject or audit |

---

## 22. Contradiction discipline

> **Status tag:** normative

The system MUST distinguish:

1. true semantic contradiction;
2. low-confidence canonicalization;
3. transport failure;
4. schema mismatch;
5. expected lossy conversion;
6. invalid witness row;
7. stale memory;
8. collision or lookup ambiguity;
9. export-policy mismatch;
10. absence/numeric-zero collapse attempt.

Only the first should raise direct contradiction pressure. The rest are validation or confidence events unless policy says otherwise.

---

## 23. Security and integrity

> **Status tag:** normative

### 23.1 Security-first semantics

If witness semantics can influence control action, the transport and identity path must be secured according to deployment policy.

### 23.2 No action from insecure protected semantics

When a profile requires secure semantics, insecure or failed-auth payloads MUST be treated as inactive for action. They may be retained only as untrusted audit artifacts.

### 23.3 Replay identity

Replay identity must pin:

1. input data hash;
2. schema version;
3. family registry version;
4. geometry registry version;
5. normalizer version;
6. canonicalization policy version;
7. event-time reducer version;
8. transport profile version;
9. Witness8 profile version;
10. WSB2 profile version;
11. export policy version;
12. policy shield version.

---

## 24. Event-time semantics

> **Status tag:** normative

### 24.1 Packet time

Packet time \(t\) advances for every input event.

### 24.2 Event time

Event time \(\tau\) advances only when the policy permits a controller update.

Event-time summaries are derived from packet-time telemetry by a versioned reducer.

### 24.3 Maintenance index

Maintenance index \(\mu\) advances only during structural evaluation windows.

### 24.4 Rule

Sparse or irregular triggering MUST NOT create hidden authority. Each control event must be replayable.

---

## 25. Metrics and budgets

> **Status tag:** normative

A deployment SHOULD track:

1. recurrent step latency;
2. lookup latency;
3. key construction latency;
4. normalizer latency;
5. canonicalization-failure rate;
6. lookup timeout rate;
7. collision rate;
8. gate fire rate;
9. replay-normal-form mismatch rate;
10. family-sensitive ambiguity rate;
11. retention collapse rate;
12. transport reject rate;
13. rollback rate;
14. Witness8 decode failure rate;
15. WSB2 inactive-lane ambiguity rate;
16. export-policy mismatch rate;
17. absence/numeric-zero collapse attempts.

Every threshold must have a default action.

---

## 26. Minimal safe profile

> **Status tag:** reference

A minimal safe profile starts conservative.

1. L4 promotions disabled.
2. L3 controls only a small coordinate set.
3. Lookup starts degraded.
4. Family-sensitive lookup starts in family bypass until conformance tests pass.
5. Geometry-sensitive normalizers must pass deterministic replay tests before enablement.
6. Transport invalid payloads never enter trusted memory.
7. Retention diagnostics run observe-only.
8. Continuous or physics-profile hooks remain shadow-only.
9. Export policy must be explicit before exported arithmetic is trusted.
10. Witness8 absence/zero separation must pass tests before row use.

---

## 27. Conformance test suite

> **Status tag:** reference

### 27.1 Canonicalization tests

Required tests:

1. same semantic input yields same normal form;
2. field ordering is deterministic;
3. absent fields materialize explicitly;
4. malformed inputs reject;
5. schema version mismatch is detected;
6. normalizer version is pinned;
7. geometry reduction is replay-stable;
8. export-policy mismatch is detected;
9. token-free absence does not decode as numeric zero.

### 27.2 Lookup tests

Required tests:

1. hashing uses normal-form keys;
2. collision counters increment;
3. low confidence gates retrieval down;
4. timeout yields no-op or bypass;
5. shield bypass overrides injection;
6. stale values do not contaminate hidden state.

### 27.3 DPFC tests

Required tests:

1. family registry entry validates;
2. canonical DPFC storage round-trips;
3. inter-family conversion preserves core magnitude;
4. expected-loss metadata is reported;
5. witness history and canonical identity remain distinct;
6. positive-index and nonnegative export policies are not silently mixed.

### 27.4 DBP/WSB2 tests

Required tests:

1. invalid frame shape rejects;
2. CRC/security failure blocks semantic use;
3. WSB2 bitmap rows decode deterministically;
4. token-free absence remains absence;
5. explicit numeric zero remains present when profile supports it;
6. structural fields are never witness-encoded;
7. inactive sparse lanes are not numeric zero.

### 27.5 Retention tests

Required tests:

1. real related witnesses beat shuffled baseline;
2. malformed witnesses score near baseline;
3. schema mismatches are detected;
4. must-preserve invariant loss triggers policy;
5. expected-loss invariants do not trigger false alerts;
6. metric extractor is versioned;
7. similarity function is declared;
8. pass rule exists before evaluation;
9. failure action is declared.

---

## 28. Failure and pruning catalogue

> **Status tag:** normative

Remove, demote, or keep experimental any feature that shows:

1. unstable canonicalization;
2. replay mismatch;
3. high family ambiguity;
4. high cost without benchmark utility;
5. retention metrics indistinguishable from shuffled baseline;
6. hidden schema drift;
7. transport trust bypass;
8. accidental collapse of absence and numeric zero;
9. geometry that never affects any useful invariant;
10. controller action based only on weak diagnostics;
11. export-policy silence;
12. retention metric elasticity;
13. WSB2 inactive-lane ambiguity;
14. Witness8 profile ambiguity;
15. normalizer version drift.

---

## 29. Reference module layout

> **Status tag:** reference

A reference implementation SHOULD expose modules similar to:

```text
srnn/cognition/witness
srnn/cognition/state
srnn/cognition/loop
srnn/memory/canonicalize
srnn/memory/lookup
srnn/memory/gating
srnn/memory/normalizers
srnn/families/registry
srnn/families/reflection
srnn/families/dpfc
srnn/meta/reducer
srnn/meta/controller
srnn/architecture/manager
srnn/architecture/migration
srnn/policy/shield
srnn/transport/dbp_ingress
srnn/transport/wsb2_decode
srnn/transport/witness8_decode
srnn/diagnostics/retention
srnn/diagnostics/baselines
srnn/export/policy
```

Module names may differ, but responsibilities should remain separated.

---

## 30. Reference schemas

> **Status tag:** reference

### 30.1 NormalFormKey

```json
{
  "schema_version": "witness-key@v10.6",
  "family_id": "hex6",
  "family_schema_version": "dpfc-family@v5.6",
  "normalizer_version": "hex6-normalizer@v1",
  "geometry_registry_version": null,
  "canonical_storage": "family:hex6 schema_version:dpfc-family@v5.6 digits:1 4 6",
  "semantic_state": "realized",
  "presence_status": "present_nonzero_value",
  "provenance_hash": "...",
  "export_policy": "positive_index_preserving",
  "trust_status": "canonicalized"
}
```

### 30.2 CanonicalizationDiagnostics

```json
{
  "normalization_confidence": 1.0,
  "canonicalization_path": ["schema", "family", "normalizer", "serializer"],
  "failure_code": null,
  "ambiguous": false,
  "loss_report": [],
  "preservation_class_results": {
    "core_magnitude": "preserved",
    "raw_path": "not-applicable"
  },
  "presence_zero_separation": "passed",
  "export_policy_check": "passed"
}
```

### 30.3 PolicyAction

```json
{
  "mode": "normal",
  "lookup_allowed": true,
  "family_sensitive_allowed": true,
  "transport_trusted": true,
  "action": "allow_gated_lookup",
  "reason": "canonicalization_success"
}
```

### 30.4 RetentionMetricSpec

```json
{
  "metric_id": "core-magnitude-through-family-conversion@v1",
  "invariant_kind": "core_magnitude",
  "extractor_id": "dpfc-core-magnitude-extractor@v1",
  "similarity_id": "exact_equal@v1",
  "transformation": "family_conversion",
  "source_profile": "hex6",
  "target_profile": "refl3",
  "preservation_class": "must_preserve",
  "baseline_suite": [
    "shuffled_pair",
    "malformed_witness",
    "schema_mismatch",
    "unsupported_family"
  ],
  "pass_rule": {
    "min_retention": 1.0,
    "max_baseline": 0.05,
    "min_normalized_lift": 0.95
  },
  "failure_action": "reject_conversion_or_keep_experimental"
}
```

---

## 31. End-to-end flow

> **Status tag:** reference

A complete witness flow is:

1. packet/frame/event arrives;
2. transport shape validates;
3. integrity/security validates;
4. semantic payload decodes;
5. WSB2 row decodes if present;
6. Witness8 row validates if present;
7. L1 extracts raw witness signature;
8. witness-family registry validates family hints;
9. normalizer canonicalizes raw bundle;
10. geometry reducer selects canonical representative;
11. diagnostics and confidence are computed;
12. export policy is checked if present;
13. L2M lookup resolves normal-form key;
14. gate injects bounded retrieval;
15. L2 recurrent state updates;
16. telemetry accumulates;
17. retention metrics update only under declared specs;
18. L3 may update at event time;
19. L4 may evaluate proposals at maintenance time;
20. L5 may degrade, bypass, rollback, or allow.

---

## 32. QCD analogy boundary

> **Status tag:** analogy

The STAR confinement paper is useful as a C5 method analogy. It motivates measuring what survives transformation.

In witness systems, the analogous question is whether declared witness invariants survive:

1. canonicalization;
2. lookup;
3. replay;
4. conversion;
5. migration;
6. transport;
7. export.

The contract does not claim physical quantum coherence. Terms such as correlation, coherence, and decoherence are engineering diagnostics unless a separate physics profile explicitly defines them.

---

## 33. Public-language caution

> **Status tag:** analogy

For public-facing documents, prefer:

| Internal term | Safer public term |
|---|---|
| cosmological witness | policy shield |
| quantum coherence | retained invariant correlation |
| decoherence | retention decay |
| virtual-particle proof | hidden-to-observable correlation analogy |
| universe layer | runtime state layer |

Internal research language may remain expressive, but normative documents should avoid accidental external-domain claims.

---

## 34. Final statement

> **Status tag:** reference

The Duotronic Witness Contract v10.6 is a trust contract.

It does not make raw observations authoritative. It routes observations through validation, canonicalization, registry semantics, policy gates, replay identity, and measured diagnostics.

The v10.6 guiding rule is:

> Trust normal forms, not raw forms; trust validated transport, not convenient payloads; trust declared export policies, not silent arithmetic assumptions; trust baselines, not attractive analogies; and remove any witness path that cannot prove its utility.

---

# Appendix A - operational playbooks

> **Status tag:** reference

## A.1 Canonicalization failure playbook

When canonicalization fails:

1. mark the witness `present_invalid` or `rejected_untrusted`;
2. emit a stable failure code;
3. prevent authoritative lookup;
4. prevent recurrent contradiction pressure unless policy declares otherwise;
5. retain raw artifact only if audit policy allows;
6. consider `family_bypass` if failures are family-specific and persistent;
7. consider `full_bypass` if failures threaten runtime safety.

## A.2 Retention collapse playbook

When retention metrics collapse:

1. identify which invariant class collapsed;
2. compare to baseline;
3. check whether the invariant was must-preserve, should-preserve, metadata-only, expected-loss, or prohibited-gain;
4. do not trigger bypass for expected-loss collapse;
5. trigger degrade or bypass only when must-preserve collapse combines with confidence loss or policy violation;
6. open an L4 review if a normalizer or family registry change caused the collapse;
7. verify that the metric spec was frozen before evaluation.

## A.3 Transport failure playbook

When DBP/WSB2 validation fails:

1. block semantic decoding;
2. emit transport reject telemetry;
3. retain frame only as untrusted audit data if configured;
4. do not construct normal-form witness keys from failed payload;
5. do not compare failed payloads as if they were canonical witness contradictions.

## A.4 Schema migration playbook

When schema migration is proposed:

1. freeze incumbent schema and candidate schema;
2. generate sentinel cases;
3. replay old inputs through old and new paths;
4. compare must-preserve invariants;
5. report expected losses;
6. reject migration if replay-normal-form mismatch exceeds policy;
7. promote only at sequence boundary with rollback path.

## A.5 Export-policy mismatch playbook

When export-policy mismatch is detected:

1. stop trusted arithmetic use;
2. retain decoded data only as conditional or audit state;
3. identify whether the active profile expected positive-index preservation or nonnegative export correction;
4. require adapter repair or migration;
5. replay sentinel cases before re-enabling.

---

# Appendix B - policy threshold template

> **Status tag:** reference

```yaml
policy_id: witness-policy@v10.6-minsafe
mode_defaults:
  startup_mode: degraded
  family_sensitive_startup: family_bypass
latency:
  recurrent_step_ms_target: 35
  recurrent_step_ms_ceiling: 50
  lookup_p99_us_target: 120
  lookup_p99_us_ceiling: 250
canonicalization:
  normalizer_mean_us_target: 20
  normalizer_mean_us_ceiling: 60
  canonicalization_failure_rate_target: 0.005
  canonicalization_failure_rate_ceiling: 0.02
replay:
  replay_normal_form_mismatch_target: 0.0
  replay_normal_form_mismatch_ceiling: 0.001
retention:
  require_metric_spec: true
  require_baseline_suite: true
  must_preserve_loss_ceiling: 0.001
  should_preserve_loss_warning: 0.05
transport:
  failed_frame_semantic_use_allowed: false
presence:
  absence_zero_collapse_allowed: false
export:
  require_explicit_export_policy: true
promotion:
  require_state_migration_plan: true
  require_rollback_path: true
```

The exact numbers are deployment-specific. What matters is that thresholds exist, have actions, and are replay-auditable.

---

# Appendix C - StateMigrationPlan schema

> **Status tag:** reference

```json
{
  "migration_id": "string",
  "source_schema": "witness-key@v10",
  "target_schema": "witness-key@v10.6",
  "affected_components": [
    "key_schema",
    "family_registry",
    "normalizer",
    "lookup_table",
    "export_policy"
  ],
  "must_preserve_invariants": [
    "canonical_storage_hash",
    "core_magnitude",
    "semantic_state",
    "presence_status"
  ],
  "expected_loss_invariants": [
    "raw_path_word"
  ],
  "sentinel_cases": ["case-1", "case-2"],
  "rollback_plan": "restore previous registry and lookup snapshot",
  "promotion_boundary": "sequence-boundary-only",
  "approval_required": true
}
```

A migration plan must be executable enough that a reviewer can reproduce why promotion was allowed.

---

# Appendix D - deterministic test vectors

> **Status tag:** reference

## D.1 Token-free absence vector

Input Witness8 row:

```text
[0, 0, 0, 0, 0, 0, 0, 0]
```

Expected result:

```text
presence_status = structurally_absent or token_free_absent
trusted_for_lookup = false
numeric_zero = not inferred
```

## D.2 Present numeric-zero vector

A profile that supports numeric zero must encode it as a present row.

Example shape:

```text
[
  value_norm = profile_min_present,
  n_sides_norm = declared,
  center_on = 1,
  activation_density = declared_min,
  kind_flag = supported,
  band_position = declared,
  parity = declared,
  degeneracy = 1
]
```

Expected result:

```text
presence_status = present_zero_value
trusted_for_lookup = only after canonicalization
```

## D.3 Unsupported family vector

Input has `kind_flag` that maps to no family.

Expected result:

```text
canonicalization_result = family_bypass_required or malformed_reject
lookup_allowed = false for family-sensitive path
```

## D.4 Retention expected-loss vector

Convert a `hex6` canonical family object into `refl3`.

Expected result:

```text
core_magnitude = preserved
source_family_id = expected_loss unless metadata channel enabled
retention alert = none for expected-loss invariant
```

## D.5 Transport-invalid vector

A WSB2 row arrives from a DBP-style frame that fails integrity validation.

Expected result:

```text
semantic_decode = blocked
normal_form_key = not constructed
trusted_memory_write = false
audit_retention = optional untrusted only
```

## D.6 Export-policy mismatch vector

A DPFC value is exported through \(E_{\mathbb U}(\mu_n)=n-1\), but downstream code treats \(\oplus_u\) as ordinary zero-based addition.

Expected result:

```text
export_policy_check = failed
trusted_arithmetic_use = false
failure_code = export_policy_mismatch
```

---

# Appendix E - anti-patterns and corrections

> **Status tag:** reference

## E.1 Anti-pattern: raw lookup

Bad: hashing raw witness JSON directly.

Correct: canonicalize to schema-versioned normal form first.

## E.2 Anti-pattern: hidden family switch

Bad: changing interpretation based on an unversioned conditional in application code.

Correct: declare family behavior in the registry and pin the registry version.

## E.3 Anti-pattern: treating failed canonicalization as contradiction

Bad: increasing contradiction pressure because a path reducer failed.

Correct: mark low confidence or invalidity; raise contradiction only when a must-preserve invariant has a trustworthy comparison.

## E.4 Anti-pattern: retention metric without baseline

Bad: reporting a retention score of `0.62` as meaningful alone.

Correct: report shuffled, malformed, long-separation, and schema-mismatch baselines.

## E.5 Anti-pattern: transport semantic shortcut

Bad: decoding a DBP semantic row before integrity validation.

Correct: validate transport first, then decode semantics.

## E.6 Anti-pattern: physics inflation

Bad: saying retained-correlation telemetry is quantum decoherence.

Correct: call it retention decay unless a physics profile defines a valid external-domain claim.

## E.7 Anti-pattern: export arithmetic shortcut

Bad: exporting \(\mu_n\) to \(n-1\) and treating Duotronic core addition as ordinary zero-based addition.

Correct: declare positive-index operation preservation or use nonnegative export correction.

## E.8 Anti-pattern: retention metric elasticity

Bad: choosing a similarity function after looking at results.

Correct: freeze `RetentionMetricSpec` before evaluation.

---

# Appendix F - release checklist for v10.6 implementation

> **Status tag:** reference

Before a v10.6 implementation is called conforming, verify:

1. all public claim labels are one-based;
2. normal-form-before-trust rule is enforced;
3. transport-before-semantics rule is enforced;
4. raw and canonical path evidence remain distinct;
5. token-free absence and numeric zero remain distinct;
6. family registry entries are versioned;
7. normalizers are versioned;
8. geometry reducers are versioned;
9. replay identity pins all relevant versions;
10. L3 cannot mutate schemas;
11. L4 proposals require migration when semantics change;
12. L5 can force degraded, family-bypass, transport-bypass, lookup-bypass, or full-bypass modes;
13. retention metrics have baselines;
14. retention metrics have declared extractors and similarity functions;
15. failed transport cannot enter trusted memory;
16. failed canonicalization cannot count as successful lookup;
17. export policy is explicit;
18. physics language is labeled analogy unless separately validated.

---

# Appendix G - claim registry examples

> **Status tag:** reference

```yaml
claim_id: WITNESS-C3-NORMALFORM-BEFORE-TRUST-001
claim_class: C3
title: Stable witness facts require canonical normal form before trust.
required_tests:
  - raw_lookup_is_blocked
  - canonical_key_lookup_allowed
  - failed_canonicalization_no_lookup
failure_action:
  - block release
  - set runtime to family_bypass or full_bypass
```

```yaml
claim_id: WITNESS-C4-RETENTION-UTILITY-001
claim_class: C4
title: Retention telemetry improves replay-risk detection.
required_tests:
  - retention_metric_above_shuffle_baseline
  - retention_drop_predicts_replay_mismatch
  - malformed_baseline_near_null
  - metric_spec_declared_before_evaluation
failure_action:
  - keep metric observe-only
  - do not use metric in L3 triggers
```

```yaml
claim_id: WITNESS-C5-QCD-ANALOGY-001
claim_class: C5
title: QCD spin-correlation studies motivate hidden-to-observable retention diagnostics.
required_boundary:
  - no claim that Duotronics models QCD
  - no claim that engineering retention is quantum coherence
failure_action:
  - revise wording
  - move to research-note appendix
```

```yaml
claim_id: WITNESS-C3-EXPORT-POLICY-001
claim_class: C3
title: Exported DPFC values require explicit export policy before trusted arithmetic use.
required_tests:
  - positive_index_policy_preserves_operations
  - nonnegative_export_requires_affine_correction
  - silent_policy_switch_rejects
failure_action:
  - block trusted arithmetic
  - require adapter migration
```

---

# Appendix H - implementation acceptance criteria

> **Status tag:** reference

An implementation is acceptable for experimental use when:

1. it can ingest valid DBP/WSB2 frames and reject invalid ones;
2. it can decode Witness8 rows without collapsing token-free absence and numeric zero;
3. it can construct normal-form keys for at least one generic symbolic family and one DPFC family;
4. it can run lookup in normal, degraded, family-bypass, transport-bypass, lookup-bypass, and full-bypass modes;
5. it emits stable telemetry counters;
6. it can replay a pinned trace with identical normal-form output;
7. it can prove token-free absence does not collide with numeric zero;
8. it can produce a retention report with at least one baseline;
9. it can reject a schema migration that changes must-preserve identity;
10. it can detect export-policy mismatch.

A production-grade implementation additionally requires security review, load testing, migration rehearsal, operator observability, and documented recovery procedures.


# Appendix I - executable witness fixtures and reference implementation

> **Status tag:** reference

This appendix gives a fixture pack and a small reference implementation for runtime distinctions required by the contract: normal-form-before-trust, ordered Witness8 decoding, token-free absence, present numeric zero, failed DBP ingress, export-policy mismatch, and DPFC family conversion.

## I.1 YAML fixture pack

> **Status tag:** reference

```yaml
fixture_pack: witness-v10.6-runtime-fixtures
schema_version: witness-fixtures@v1
fixtures:
  - fixture_id: WITNESS-FIXTURE-1-HEX6-NORMAL-FORM
    claim_class: C3
    status_tag: reference
    given:
      raw_bundle:
        family_id: hex6
        family_schema_version: dpfc-family@v5.6
        digits: [h1, h4]
      family_registry_entry:
        family_id: hex6
        alphabet: [h1, h2, h3, h4, h5, h6]
        normalizer_version: hex6-normalizer@v1
    operation: canonicalize_witness_key_bundle
    expected:
      canonical_storage: "family:hex6 schema_version:dpfc-family@v5.6 digits:1 4"
      core_magnitude: mu_10
      trust_status: canonicalized
      lookup_allowed: true
    failure_action: block_family_sensitive_lookup

  - fixture_id: WITNESS-FIXTURE-2-WITNESS8-TOKEN-FREE-ABSENCE
    claim_class: C3
    status_tag: reference
    given:
      witness8_row: [0, 0, 0, 0, 0, 0, 0, 0]
      profile_id: witness8-minsafe@v1
    operation: decode_witness8
    expected:
      decode_status: token_free_absent
      presence_status: structurally_absent
      numeric_zero_inferred: false
      normal_form_key_constructed: false
      trusted_for_lookup: false
    failure_action: reject_decoder_profile

  - fixture_id: WITNESS-FIXTURE-3-WITNESS8-PRESENT-NUMERIC-ZERO
    claim_class: C3
    status_tag: reference
    given:
      witness8_row:
        value_norm: 0.0
        n_sides_norm: 0.6
        center_on: 1.0
        activation_density: 0.125
        kind_flag: 1.0
        band_position: 0.5
        parity: 1.0
        degeneracy: 1.0
      profile_id: witness8-minsafe@v1
      profile_declares_numeric_zero: true
    operation: decode_witness8
    expected:
      decode_status: decoded_exact
      presence_status: present_zero_value
      token_free_absent: false
      numeric_zero_inferred: true
      trusted_for_lookup: only_after_canonicalization
    failure_action: reject_decoder_profile

  - fixture_id: WITNESS-FIXTURE-4-WITNESS8-MAPPING-FIELD-ORDER
    claim_class: C3
    status_tag: reference
    given:
      witness8_row:
        degeneracy: 1.0
        parity: 1.0
        band_position: 0.5
        kind_flag: 1.0
        activation_density: 0.125
        center_on: 1.0
        n_sides_norm: 0.6
        value_norm: 0.0
      profile_declares_numeric_zero: true
    operation: decode_witness8
    expected:
      field_order_used: [value_norm, n_sides_norm, center_on, activation_density, kind_flag, band_position, parity, degeneracy]
      presence_status: present_zero_value
      numeric_zero_inferred: true
    failure_action: reject_decoder_profile

  - fixture_id: WITNESS-FIXTURE-5-FAILED-DBP-FRAME
    claim_class: C3
    status_tag: reference
    given:
      dbp_frame:
        shape_valid: true
        profile_id: dbp-minsafe@v1
        integrity_check: failed
        semantic_payload_kind: witness8
    operation: ingress_dbp_frame
    expected:
      semantic_decode_allowed: false
      witness8_decode_allowed: false
      normal_form_key_constructed: false
      trusted_memory_write: false
      audit_state: rejected_untrusted_optional
      failure_code: transport_integrity_failed
    failure_action: transport_bypass

  - fixture_id: WITNESS-FIXTURE-6-FAMILY-CONVERSION-RETENTION
    claim_class: C4
    status_tag: research
    given:
      source_family_id: hex6
      source_word: [h1, h4]
      target_family_id: refl3
      retention_metric_spec: core-magnitude-through-family-conversion@v1
    operation: family_conversion_with_retention_report
    expected:
      target_word: [r3, r1]
      core_magnitude_retention: 1.0
      source_family_identity_retention: expected_loss
      baseline_suite_required: true
      alert: false
    failure_action: reject_conversion_or_keep_metric_observe_only
```

## I.2 Python reference implementation

> **Status tag:** reference

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


WITNESS8_FIELD_ORDER = [
    "value_norm",
    "n_sides_norm",
    "center_on",
    "activation_density",
    "kind_flag",
    "band_position",
    "parity",
    "degeneracy",
]


@dataclass(frozen=True)
class Family:
    family_id: str
    schema_version: str
    alphabet: tuple[str, ...]

    @property
    def modulus(self) -> int:
        return len(self.alphabet)

    def ordinal(self, digit: str) -> int:
        if digit not in self.alphabet:
            raise ValueError(f"unknown digit {digit!r} for {self.family_id}")
        return self.alphabet.index(digit) + 1

    def digit(self, ordinal: int) -> str:
        if ordinal < 1 or ordinal > self.modulus:
            raise ValueError("ordinal outside family alphabet")
        return self.alphabet[ordinal - 1]


HEX6 = Family("hex6", "dpfc-family@v5.6", ("h1", "h2", "h3", "h4", "h5", "h6"))
REFL3 = Family("refl3", "dpfc-family@v5.6", ("r1", "r2", "r3"))
REGISTRY = {family.family_id: family for family in (HEX6, REFL3)}


def evaluate_family_word(word: list[str], family: Family) -> int:
    if not word:
        raise ValueError("family word must be nonempty")
    value = 0
    for digit in word:
        value = value * family.modulus + family.ordinal(digit)
    return value


def encode_core_to_family(core_index: int, family: Family) -> list[str]:
    if core_index < 1:
        raise ValueError("core index must be positive")
    q = core_index
    out: list[str] = []
    while q > 0:
        r = ((q - 1) % family.modulus) + 1
        out.insert(0, family.digit(r))
        q = (q - r) // family.modulus
    return out


def canonical_storage(word: list[str], family: Family) -> str:
    ordinals = " ".join(str(family.ordinal(digit)) for digit in word)
    return f"family:{family.family_id} schema_version:{family.schema_version} digits:{ordinals}"


def canonicalize_witness_key_bundle(raw_bundle: Mapping[str, Any]) -> dict[str, Any]:
    family = REGISTRY.get(raw_bundle.get("family_id"))
    if family is None:
        return {"canonicalization_result": "family_bypass_required", "lookup_allowed": False, "trust_status": "rejected"}
    if raw_bundle.get("family_schema_version") != family.schema_version:
        return {"canonicalization_result": "schema_mismatch", "lookup_allowed": False, "trust_status": "rejected"}
    word = list(raw_bundle.get("digits", []))
    try:
        core_index = evaluate_family_word(word, family)
        storage = canonical_storage(word, family)
    except Exception as exc:
        return {"canonicalization_result": "malformed_reject", "failure_code": str(exc), "lookup_allowed": False, "trust_status": "rejected"}
    return {"canonicalization_result": "canonical_success", "canonical_storage": storage, "core_magnitude": f"mu_{core_index}", "lookup_allowed": True, "trust_status": "canonicalized"}


def convert_family(word: list[str], source: Family, target: Family) -> dict[str, Any]:
    core_index = evaluate_family_word(word, source)
    target_word = encode_core_to_family(core_index, target)
    return {"source_core_magnitude": f"mu_{core_index}", "target_word": target_word, "target_core_magnitude": f"mu_{evaluate_family_word(target_word, target)}", "expected_loss": ["source_family_identity_unless_metadata_channel_enabled"]}


def decode_witness8(row: Any, *, profile_declares_numeric_zero: bool = False) -> dict[str, Any]:
    if isinstance(row, Mapping):
        values = [row.get(field, 0) for field in WITNESS8_FIELD_ORDER]
    else:
        values = list(row)
    if len(values) != 8:
        return {"decode_status": "present_invalid", "trusted_for_lookup": False}
    if all(v == 0 for v in values):
        return {"decode_status": "token_free_absent", "presence_status": "structurally_absent", "numeric_zero_inferred": False, "normal_form_key_constructed": False, "trusted_for_lookup": False}
    if profile_declares_numeric_zero and values[0] == 0:
        return {"decode_status": "decoded_exact", "presence_status": "present_zero_value", "token_free_absent": False, "numeric_zero_inferred": True, "trusted_for_lookup": "only_after_canonicalization"}
    return {"decode_status": "decoded_lossy", "presence_status": "present_nonzero_value", "trusted_for_lookup": "only_after_canonicalization"}


def ingress_dbp_frame(frame: Mapping[str, Any]) -> dict[str, Any]:
    if not frame.get("shape_valid"):
        return {"semantic_decode_allowed": False, "failure_code": "frame_shape_invalid"}
    if frame.get("integrity_check") != "passed":
        return {"semantic_decode_allowed": False, "witness8_decode_allowed": False, "normal_form_key_constructed": False, "trusted_memory_write": False, "failure_code": "transport_integrity_failed", "policy_mode": "transport_bypass"}
    return {"semantic_decode_allowed": True, "failure_code": None}


def run_reference_self_test() -> None:
    assert canonicalize_witness_key_bundle({"family_id": "hex6", "family_schema_version": "dpfc-family@v5.6", "digits": ["h1", "h4"]})["core_magnitude"] == "mu_10"
    assert convert_family(["h1", "h4"], HEX6, REFL3)["target_word"] == ["r3", "r1"]
    assert decode_witness8([0, 0, 0, 0, 0, 0, 0, 0])["decode_status"] == "token_free_absent"
    shuffled = {"degeneracy": 1.0, "parity": 1.0, "band_position": 0.5, "kind_flag": 1.0, "activation_density": 0.125, "center_on": 1.0, "n_sides_norm": 0.6, "value_norm": 0.0}
    assert decode_witness8(shuffled, profile_declares_numeric_zero=True)["presence_status"] == "present_zero_value"
    assert ingress_dbp_frame({"shape_valid": True, "integrity_check": "failed"})["semantic_decode_allowed"] is False


if __name__ == "__main__":
    run_reference_self_test()
    print("Witness Contract v10.6 reference self-test passed")
```


# Appendix K - spectral, temperament, and EDO witness profiles

> **Status tag:** research
> **Related tags:** reference

This appendix imports the useful parts of the acoustics, harmony, temperament, Fourier, and 31-EDO source document as witness-profile material. It does not change the witness trust core. It gives concrete witness examples where raw signals, spectra, inferred pitch, tuning families, and notation require validation and provenance before trust.

## K.1 Import boundary

> **Status tag:** research
> **Related tags:** reference

The witness contract imports the following ideas as research/reference profiles:

1. waveform-to-spectrum witness extraction;
2. Fourier/STFT provenance;
3. partial alignment and roughness metrics;
4. missing-fundamental derived witnesses;
5. EDO step-pattern witnesses;
6. enharmonic identity witnesses;
7. temperament error witnesses;
8. masking and critical-bandwidth boundary rules.

It does not import the following as core witness semantics:

1. consonance as truth;
2. Fourier components as automatically canonical witnesses;
3. 31-EDO as universal family identity;
4. musical notation as runtime authority;
5. external pitch-class zero as native Duotronic absence.

## K.2 SpectralWitnessSignature

> **Status tag:** reference

```yaml
SpectralWitnessSignature:
  schema_version: spectral-witness@v1
  observed_waveform_hash: string
  sample_rate_hz: number
  analysis_window:
    window_size_samples: integer
    hop_size_samples: integer
    window_function: string
  spectrum_profile:
    partials:
      - frequency_hz: number
        amplitude: number
        phase: number | null
        confidence: number
    inharmonicity_score: number | null
    roughness_score: number | null
    masking_score: number | null
  inferred_pitch:
    pitch_hz: number | null
    inference_type: observed_fundamental | missing_fundamental | ambiguous | none
  trust:
    canonicalization_status: raw | canonicalized | rejected
    provenance: string
```

## K.3 FourierProvenance rule

> **Status tag:** normative

A Fourier-derived witness MUST record:

1. sample rate;
2. window function;
3. window size;
4. hop size when applicable;
5. normalization policy;
6. leakage handling policy;
7. source waveform hash or stream provenance;
8. confidence policy.

A spectral witness lacking this provenance may be retained as raw audit data, but it MUST NOT enter authoritative witness memory.

## K.4 MissingFundamentalDerivedWitness

> **Status tag:** research
> **Related tags:** reference

A missing-fundamental witness is inferred, not directly observed.

```yaml
MissingFundamentalDerivedWitness:
  observed_components_hz: [200, 300, 400, 500]
  inferred_fundamental_hz: 100
  inference_type: missing_fundamental
  evidence_pattern: [2, 3, 4, 5]
  trust_status: conditional
  rule: inferred_witness_must_not_be_stored_as_observed_witness
```

This is a clean reference case for the witness contract's separation of raw observation, derived witness, canonical witness, and trusted witness.

## K.5 EDOStepWitness

> **Status tag:** research
> **Related tags:** reference

```yaml
EDOStepWitness:
  family_id: edo31
  external_step_domain: "0..30 modulo 31"
  native_label_bridge: external_zero_maps_to_e1
  chord_external_steps: [0, 11, 18]
  chord_native_labels: [e1, e12, e19]
  interval_pattern: [11, 7, 13]
  provenance: edo-step-pattern@v1
```

The external step `0` is a pitch-class reference, not Duotronic absence.

## K.6 EnharmonicIdentityWitness

> **Status tag:** research
> **Related tags:** reference

```yaml
EnharmonicIdentityWitness:
  source_family: edo31
  compared_spellings:
    C_sharp: 2
    D_flat: 3
  relation:
    equal_in_source_family: false
    distance_diesis: 1
  collapse_policy:
    collapse_to_12edo_allowed: only_with_expected_loss
  expected_loss_if_collapsed:
    - spelling_identity
    - voice_leading_microstate
    - harmonic_function_hint
```

This profile demonstrates why family identity must be part of canonical witness interpretation.

## K.7 TemperamentErrorWitness

> **Status tag:** research
> **Related tags:** reference

```yaml
TemperamentErrorWitness:
  source_ratio: "5/4"
  target_family: edo31
  nearest_step: "10\\31"
  just_cents: 386.313714
  edo_cents: 387.096774
  error_cents: 0.78306
  preservation_class: approximate_preserve
  failure_action: none_if_within_declared_budget
```

## K.8 RoughnessRetentionMetric

> **Status tag:** research

```yaml
RetentionMetricSpec:
  metric_id: roughness-weighted-partial-alignment@v1
  invariant_kind: partial_alignment
  extractor_id: spectral-partial-extractor@v1
  similarity_id: roughness_weighted_alignment@v1
  transformation: canonicalization | transport | replay | family_conversion
  baseline_suite:
    - shuffled_partials
    - detuned_partials
    - masked_signal
    - window_leakage_control
  preservation_class: should_preserve
  failure_action: degrade_confidence
```

This metric is research-only until benchmarked. It MUST NOT be treated as physical truth or runtime authority.

## K.9 EDOStepPatternRetentionMetric

> **Status tag:** research

```yaml
RetentionMetricSpec:
  metric_id: edo31-step-pattern-retention@v1
  invariant_kind: interval_step_structure
  extractor_id: canonical_edo_step_pattern@v1
  similarity_id: exact_modular_interval_pattern@v1
  family_id: edo31
  modulus: 31
  transformation: transposition | notation_conversion | family_conversion
  pass_rule:
    must_preserve:
      - internal_step_distances
      - family_id
      - modulus
    expected_loss:
      - absolute_root_unless_metadata_preserved
  baseline_suite:
    - shuffled_step_pattern
    - collapsed_to_12edo
    - random_transposition_control
  failure_action: keep_metric_observe_only
```

## K.10 Masking and critical-bandwidth boundary rule

> **Status tag:** research
> **Related tags:** reference

A spectral witness may be structurally present but perceptually or analytically masked. A masked partial MUST NOT be promoted with the same confidence as an unmasked partial.

```yaml
MaskingBoundaryRule:
  rule_id: masking-boundary@v1
  input: spectral_partial
  conditions:
    - partial_inside_critical_band_of_stronger_component
    - amplitude_below_masking_threshold
  output:
    trust_status: conditional
    confidence_adjustment: decrease
    promotion_allowed_without_review: false
```

## K.11 Executable fixture pack

> **Status tag:** reference

```yaml
fixture_pack: witness-v10.6-spectral-edo-fixtures
schema_version: witness-spectral-edo-fixtures@v1
fixtures:
  - fixture_id: WITNESS-SPECTRAL-FIXTURE-1-MISSING-FUNDAMENTAL
    claim_class: C4
    status_tag: research
    given:
      observed_components_hz: [200, 300, 400, 500]
    operation: infer_missing_fundamental
    expected:
      inferred_fundamental_hz: 100
      inference_type: missing_fundamental
      trust_status: conditional
      observed_as_fundamental: false
    failure_action: keep_inferred_witness_conditional

  - fixture_id: WITNESS-EDO31-FIXTURE-2-TRANSPOSITION-RETENTION
    claim_class: C4
    status_tag: research
    given:
      chord_external_steps: [0, 11, 18]
      transposition: 5
      modulus: 31
    operation: transpose_and_measure_interval_retention
    expected:
      transposed_chord_external_steps: [5, 16, 23]
      preserved: [internal_step_distances, family_id, modulus]
      expected_loss: [absolute_root_unless_metadata_preserved]
      retention_score: 1.0
    failure_action: keep_metric_observe_only

  - fixture_id: WITNESS-EDO31-FIXTURE-3-ENHARMONIC-COLLAPSE
    claim_class: C4
    status_tag: research
    given:
      source_family: edo31
      target_family: edo12
      C_sharp_source_step: 2
      D_flat_source_step: 3
    operation: collapse_to_12edo
    expected:
      collapse_allowed: only_with_expected_loss
      expected_loss: [spelling_identity, voice_leading_microstate, harmonic_function_hint]
      alert_if_loss_undeclared: true
    failure_action: reject_normalizer

  - fixture_id: WITNESS-SPECTRAL-FIXTURE-4-FOURIER-PROVENANCE-MISSING
    claim_class: C3
    status_tag: reference
    given:
      spectral_witness:
        partials:
          - frequency_hz: 200
            amplitude: 0.8
        sample_rate_hz: null
        window_function: null
    operation: validate_fourier_provenance
    expected:
      authoritative_memory_allowed: false
      audit_retention_allowed: true
      failure_code: missing_fourier_provenance
    failure_action: reject_authoritative_use

  - fixture_id: WITNESS-EDO31-FIXTURE-5-RATIO-APPROX-WITNESS
    claim_class: C4
    status_tag: research
    given:
      ratio: "5/4"
      target_family: edo31
    operation: temperament_error_witness
    expected:
      nearest_step: "10\\31"
      error_cents_approx: 0.78306
      preservation_class: approximate_preserve
    failure_action: none_if_within_declared_budget
```

## K.12 Spectral and EDO witness reference implementation

> **Status tag:** reference

```python
from __future__ import annotations

from fractions import Fraction
from math import gcd, log2
from typing import Any, Mapping


def cents_of_ratio(ratio: str) -> float:
    return 1200.0 * log2(float(Fraction(ratio)))


def approximate_ratio_in_edo(ratio: str, steps: int) -> dict[str, float | int | str]:
    just_cents = cents_of_ratio(ratio)
    nearest = round(steps * log2(float(Fraction(ratio))))
    edo_cents = 1200.0 * nearest / steps
    return {"nearest_step": nearest, "edostep": f"{nearest}\\{steps}", "just_cents": just_cents, "edo_cents": edo_cents, "error_cents": edo_cents - just_cents}


def infer_missing_fundamental(components_hz: list[int]) -> dict[str, Any]:
    if not components_hz:
        return {"inference_type": "none", "trust_status": "rejected"}
    base = components_hz[0]
    for value in components_hz[1:]:
        base = gcd(base, value)
    if base < min(components_hz):
        pattern = [value // base for value in components_hz]
        return {"inferred_fundamental_hz": base, "evidence_pattern": pattern, "inference_type": "missing_fundamental", "trust_status": "conditional", "observed_as_fundamental": base in components_hz}
    return {"inferred_fundamental_hz": base, "inference_type": "observed_fundamental", "trust_status": "conditional", "observed_as_fundamental": True}


def transpose_mod(values: list[int], transposition: int, modulus: int) -> list[int]:
    return [(value + transposition) % modulus for value in values]


def interval_pattern(values: list[int], modulus: int) -> list[int]:
    return [((values[(i + 1) % len(values)] - values[i]) % modulus) for i in range(len(values))]


def transpose_retention(values: list[int], transposition: int, modulus: int) -> dict[str, Any]:
    before = interval_pattern(values, modulus)
    after_values = transpose_mod(values, transposition, modulus)
    after = interval_pattern(after_values, modulus)
    return {"transposed_chord_external_steps": after_values, "before_pattern": before, "after_pattern": after, "retention_score": 1.0 if before == after else 0.0}


def validate_fourier_provenance(witness: Mapping[str, Any]) -> dict[str, Any]:
    required = ["sample_rate_hz", "window_function", "partials"]
    missing = [field for field in required if not witness.get(field)]
    if missing:
        return {"authoritative_memory_allowed": False, "audit_retention_allowed": True, "failure_code": "missing_fourier_provenance", "missing": missing}
    return {"authoritative_memory_allowed": True, "failure_code": None}


def enharmonic_collapse_policy(source_family: str, target_family: str, left_step: int, right_step: int) -> dict[str, Any]:
    if source_family == "edo31" and target_family == "edo12" and left_step != right_step:
        return {"collapse_allowed": "only_with_expected_loss", "expected_loss": ["spelling_identity", "voice_leading_microstate", "harmonic_function_hint"]}
    return {"collapse_allowed": True, "expected_loss": []}


def run_spectral_edo_self_test() -> None:
    missing = infer_missing_fundamental([200, 300, 400, 500])
    assert missing["inferred_fundamental_hz"] == 100
    assert missing["inference_type"] == "missing_fundamental"
    retention = transpose_retention([0, 11, 18], 5, 31)
    assert retention["transposed_chord_external_steps"] == [5, 16, 23]
    assert retention["retention_score"] == 1.0
    major_third = approximate_ratio_in_edo("5/4", 31)
    assert major_third["nearest_step"] == 10
    bad_provenance = validate_fourier_provenance({"partials": [{"frequency_hz": 200, "amplitude": 0.8}], "sample_rate_hz": None, "window_function": None})
    assert bad_provenance["authoritative_memory_allowed"] is False
    collapse = enharmonic_collapse_policy("edo31", "edo12", 2, 3)
    assert collapse["collapse_allowed"] == "only_with_expected_loss"


if __name__ == "__main__":
    run_spectral_edo_self_test()
    print("Witness spectral/EDO appendix self-test passed")
```



---

# Appendix L - Duotronic source architecture from the Witness side

> **Status tag:** reference

The Witness Contract is the runtime trust half of Duotronic witness-bearing computation. It consumes objects and evidence that may originate from DPFC, transport profiles, signal profiles, EDO profiles, model outputs, or human-authored source documents. It decides whether such evidence becomes trusted runtime state.

## L.1 Witness Contract responsibility boundary

> **Status tag:** normative

The Witness Contract owns:

1. raw witness extraction;
2. transport validation;
3. semantic validation;
4. family registry lookup;
5. canonicalization;
6. normal-form key construction;
7. lookup memory;
8. recurrent state update;
9. event-time control;
10. architectural proposal control;
11. policy shielding;
12. replay identity;
13. telemetry and failure codes;
14. migration and rollback requirements.

It does not define DPFC arithmetic. It verifies, gates, stores, retrieves, and promotes witness-bearing facts.

## L.2 Trust-preserving representational stack

> **Status tag:** reference

```text
Raw Observation
-> Transport Validation
-> Semantic Decode
-> Witness Signature
-> Family Registry Lookup
-> Canonicalization
-> Normal-Form Key
-> Policy Gate
-> L2M Lookup
-> L2 Recurrent Update
-> L3 Event-Time Adjustment
-> L4 Structural Proposal
-> L5 Policy Shield Acceptance/Rejection
```

At every arrow, the system must know which invariants are preserved, transformed, expected-loss, metadata-only, or rejected.

## L.3 What must never be confused

> **Status tag:** normative

The witness runtime must never confuse:

1. raw observation with trusted fact;
2. observed witness with derived witness;
3. absent row with numeric zero;
4. valid transport with valid semantics;
5. family hint with family registry entry;
6. geometry hint with arithmetic proof;
7. diagnostic metric with policy authority;
8. lookup result with recurrent truth;
9. migration candidate with promoted schema;
10. analogy with external-domain claim.

---

# Appendix M - Duotronic threat model

> **Status tag:** normative
> **Related tags:** reference

The Witness Contract protects runtime state from semantic collapse, untrusted input, schema drift, proof inflation, and unsafe promotion.

## M.1 Threat classes

> **Status tag:** normative

| Threat ID | Threat | Description | Default mitigation |
|---|---|---|---|
| T1 | absence-zero collapse | token-free absence becomes numeric zero | reject decoder/profile |
| T2 | raw lookup injection | raw bundle is hashed or stored | require normal form |
| T3 | transport semantic shortcut | semantics decoded before integrity validation | block semantic decode |
| T4 | silent family reinterpretation | family/schema/normalizer changes without migration | reject or bypass |
| T5 | geometry proof inflation | visual witness treated as arithmetic proof | require bridge theorem |
| T6 | retention metric inflation | diagnostic score treated as proof | require baseline and policy |
| T7 | export-policy mismatch | exported values treated as operation-preserving incorrectly | block trusted arithmetic |
| T8 | replay identity drift | replay uses different versions without pinning | reject replay |
| T9 | bypass failure | system fails unsafe instead of entering declared bypass | force L5 mode |
| T10 | malicious payload shaping | hostile frame mimics valid witness rows | validate transport, schema, and normalizer |

## M.2 Protected assets

> **Status tag:** normative

Protected assets include:

1. canonical witness memory;
2. lookup keys;
3. recurrent state;
4. policy shield state;
5. schema registry;
6. family registry;
7. normalizer registry;
8. replay traces;
9. migration plans;
10. transport integrity decisions.

## M.3 Attacker capabilities

> **Status tag:** reference

The threat model assumes an attacker or faulty subsystem may:

1. send malformed frames;
2. send well-shaped frames with invalid integrity;
3. reorder mapping fields;
4. imitate token-free absence;
5. force schema ambiguity;
6. exploit normalizer edge cases;
7. send geometry hints that look plausible;
8. induce retention collapse;
9. exploit export-policy mismatch;
10. cause replay under changed versions.

## M.4 Required mitigations

> **Status tag:** normative

Mitigations include:

1. transport-before-semantics;
2. normal-form-before-trust;
3. explicit Witness8 field order;
4. version-pinned registries;
5. replay identity hashes;
6. failure-code registries;
7. policy-shield modes;
8. migration plans;
9. audit-only retention for rejected data;
10. metric baselines and pass rules.

---

# Appendix N - Witness lifecycle

> **Status tag:** reference

A witness has a lifecycle. The lifecycle makes runtime behavior understandable and testable.

## N.1 Birth

> **Status tag:** reference

A packet, frame, row, signal, model output, human statement, or derived structure appears. At birth it is not trusted. It is only input evidence.

## N.2 Raw extraction

> **Status tag:** reference

L1 extracts a `WitnessSignature`. This may include family hints, geometry hints, confidence, provenance, and local contradiction cues.

## N.3 Transport validation

> **Status tag:** normative

If the witness comes through DBP, WSB2, Witness8, or another transport profile, transport validation happens before semantic interpretation.

## N.4 Semantic validation

> **Status tag:** normative

The runtime validates field shapes, ranges, expected order, schema version, family identifier, and profile declarations.

## N.5 Family registry lookup

> **Status tag:** normative

A family hint becomes meaningful only after registry lookup. Missing family entries cause rejection or family bypass.

## N.6 Canonicalization

> **Status tag:** normative

Raw witness evidence becomes a versioned canonical normal-form key, or it is rejected, bypassed, or marked conditional.

## N.7 Policy gating

> **Status tag:** normative

L5 decides whether a canonicalized object can influence lookup, recurrence, promotion, or transport.

## N.8 Lookup and recurrent update

> **Status tag:** reference

L2M may retrieve stable facts. L2 may update bounded recurrent state. Both remain subject to gate and bypass policy.

## N.9 Event-time and maintenance control

> **Status tag:** reference

L3 can adjust bounded coordinates at event time. L4 can propose structural changes only during maintenance windows and only with migration/replay checks.

## N.10 Audit retention and pruning

> **Status tag:** normative
> **Related tags:** reference

Rejected data may be retained as untrusted audit material. Weak families, metrics, and normalizers must be demoted or pruned if they fail tests.

---

# Appendix O - Failure-code registry

> **Status tag:** normative
> **Related tags:** reference

Failure codes make runtime failure explicit. A failure without a code is difficult to audit, reproduce, or test.

## O.1 Failure-code schema

> **Status tag:** normative

```yaml
failure_code: string
layer: string
trust_status: rejected | conditional | bypassed | audit_only
lookup_allowed: false
recurrence_allowed: false
promotion_allowed: false
audit_allowed: true
default_mode: normal | degraded | family_bypass | transport_bypass | lookup_bypass | full_bypass
telemetry_counter: string
```

## O.2 Core failure-code table

> **Status tag:** reference

| Failure code | Layer | Default mode | Meaning |
|---|---|---|---|
| frame_shape_invalid | transport | transport_bypass | frame shape invalid |
| transport_integrity_failed | transport | transport_bypass | CRC/security/integrity failed |
| witness8_field_order_invalid | semantic decode | degraded | mapping/row order invalid |
| token_free_absence_collision | semantic decode | full_bypass | absence collapsed into numeric zero |
| family_registry_missing | registry | family_bypass | family hint not registered |
| schema_mismatch | canonicalization | family_bypass | object schema not accepted |
| normalizer_error | canonicalization | family_bypass | normalizer failed |
| ambiguous_orbit | geometry | family_bypass | canonical representative ambiguous |
| export_policy_mismatch | boundary | degraded | export arithmetic assumption invalid |
| retention_metric_unbounded | diagnostics | degraded | metric lacks extractor/baseline/pass rule |
| replay_identity_mismatch | replay | full_bypass | replay versions or outputs differ |
| migration_plan_missing | L4 | degraded | promotion lacks migration plan |

## O.3 Failure-code YAML examples

> **Status tag:** reference

```yaml
failure_code: transport_integrity_failed
layer: DBP
trust_status: rejected
lookup_allowed: false
recurrence_allowed: false
promotion_allowed: false
audit_allowed: true
default_mode: transport_bypass
telemetry_counter: dbp_integrity_failed_count
```

```yaml
failure_code: token_free_absence_collision
layer: Witness8Decode
trust_status: rejected
lookup_allowed: false
recurrence_allowed: false
promotion_allowed: false
audit_allowed: true
default_mode: full_bypass
telemetry_counter: absence_zero_collision_count
```

---

# Appendix P - Replay identity profile

> **Status tag:** normative

Replay identity determines whether a witness pipeline can be reproduced. A witness that cannot be replayed under pinned versions cannot support promotion.

## P.1 Replay hash construction

> **Status tag:** reference

A replay hash should cover:

1. input data hash;
2. transport profile;
3. semantic schema;
4. family registry version;
5. geometry registry version;
6. normalizer version;
7. serializer version;
8. policy shield version;
9. retention metric version;
10. migration version;
11. deterministic random seeds if any;
12. floating-point mode if relevant.

## P.2 Replay profile schema

> **Status tag:** normative

```yaml
replay_profile_id: string
input_hash: string
transport_profile_version: string
schema_versions: [string]
family_registry_version: string
geometry_registry_version: string
normalizer_versions: [string]
serializer_versions: [string]
policy_shield_version: string
retention_metric_versions: [string]
floating_point_profile: string | null
deterministic_seed: string | null
expected_normal_form_hash: string
```

## P.3 Replay mismatch classes

> **Status tag:** reference

| Mismatch | Meaning | Default action |
|---|---|---|
| input_hash_mismatch | input differs | reject replay |
| schema_version_mismatch | schema differs | migration required |
| normalizer_version_mismatch | normalizer differs | migration required |
| geometry_registry_mismatch | geometry reducer differs | family bypass |
| floating_point_profile_mismatch | numeric environment differs | rerun under pinned profile |
| normal_form_hash_mismatch | output differs | block promotion |

---

# Appendix Q - Policy shield decision matrix

> **Status tag:** normative
> **Related tags:** reference

The policy shield must make failure behavior explicit.

| Condition | Mode | Lookup | Recurrence | Promotion | Transport | Audit |
|---|---|---|---|---|---|---|
| canonicalization failure spike | family_bypass | generic only | allowed | blocked | allowed if valid | yes |
| transport integrity failed | transport_bypass | blocked | no semantic update | blocked | rejected | untrusted only |
| lookup timeout high | lookup_bypass | disabled | allowed | blocked if dependent | allowed | yes |
| replay mismatch | degraded or full_bypass | disabled for affected path | conservative | rollback | allowed if valid | yes |
| absence-zero collapse attempt | full_bypass | blocked | blocked for affected path | blocked | reject profile | yes |
| retention metric lacks baseline | degraded | allowed without metric authority | allowed | metric promotion blocked | allowed | yes |
| migration plan missing | degraded | incumbent only | incumbent only | blocked | allowed | yes |
| geometry ambiguity high | family_bypass | generic only | allowed | blocked | allowed if valid | yes |

---

# Appendix R - Telemetry catalog

> **Status tag:** reference

Telemetry fields must have units, windows, thresholds, and actions. A metric that cannot trigger an action or explain a state transition should remain experimental.

## R.1 Telemetry schema

> **Status tag:** reference

```yaml
metric_id: string
layer: string
unit: string
window: string
warning_threshold: number | string
failure_threshold: number | string
default_action: string
related_failure_codes: [string]
status_tag: reference | research | normative
```

## R.2 Required telemetry fields

> **Status tag:** normative
> **Related tags:** reference

| Metric | Layer | Unit | Default action |
|---|---|---|---|
| canonicalization_failure_rate | canonicalization | failures / attempts | family_bypass |
| normalizer_latency_p99 | canonicalization | milliseconds | degraded |
| lookup_collision_rate | L2M | collisions / lookup | degraded |
| lookup_timeout_rate | L2M | timeouts / lookup | lookup_bypass |
| gate_fire_rate | L2M/L2 | fires / event | investigate drift |
| replay_normal_form_mismatch_rate | replay | mismatches / replay | full_bypass |
| transport_reject_rate | DBP/WSB2 | rejects / frame | transport_bypass |
| absence_zero_collision_count | semantic decode | count | full_bypass |
| retention_collapse_rate | diagnostics | collapse / metric window | degrade metric authority |
| promotion_reject_count | L4 | count | audit |
| bypass_duration | L5 | seconds | operator review |

---

# Appendix S - Conformance harness for the Witness Contract

> **Status tag:** reference

The Witness Contract must be testable through fixtures, golden traces, and negative tests.

## S.1 Required test groups

> **Status tag:** normative

1. transport validation;
2. Witness8 decoding;
3. token-free absence distinction;
4. present numeric-zero distinction;
5. family registry lookup;
6. canonicalization;
7. normal-form key hashing;
8. lookup gating;
9. bypass modes;
10. replay identity;
11. migration plans;
12. retention metrics;
13. policy-shield transitions;
14. audit retention.

## S.2 Fuzz tests

> **Status tag:** research
> **Related tags:** reference

Fuzz tests should generate:

1. malformed frames;
2. reordered mapping fields;
3. invalid digit words;
4. unknown family IDs;
5. ambiguous geometry hints;
6. missing Fourier provenance;
7. export-policy mismatches;
8. replay version mismatches;
9. lossy conversion without expected-loss declaration.

## S.3 CI acceptance criteria

> **Status tag:** normative
> **Related tags:** reference

A v10.6 implementation should not pass CI unless:

1. all normative fixtures pass;
2. JSON and YAML fixtures parse;
3. embedded reference implementations self-test;
4. golden traces replay;
5. no failed frame enters trusted memory;
6. no absence-zero collision is accepted;
7. migration tests cover every semantic change;
8. retention metrics have baselines.

---

# Appendix T - Migration and versioning guide

> **Status tag:** normative
> **Related tags:** reference

## T.1 What counts as a semantic change

> **Status tag:** normative

A semantic change includes changes to:

1. trust status meaning;
2. canonical key format;
3. family registry interpretation;
4. normalizer output;
5. geometry reduction;
6. Witness8 decoding;
7. DBP/WSB2 validation;
8. retention metric meaning;
9. policy-shield decision;
10. replay identity fields.

## T.2 Migration plan requirements

> **Status tag:** normative

A migration plan must include:

1. source version;
2. target version;
3. affected layers;
4. must-preserve invariants;
5. expected-loss invariants;
6. sentinel cases;
7. replay trace set;
8. rollback plan;
9. promotion boundary;
10. approval rule.

## T.3 Dual-read/single-write strategy

> **Status tag:** reference

During migration, an implementation may read both old and new canonical forms while writing only the new form after validation. This strategy requires replay comparison and must not allow old ambiguous forms to regain authority.

## T.4 Shadow canonicalization

> **Status tag:** reference

Shadow canonicalization runs candidate normalizers without changing authoritative state. It records differences, retention loss, and replay mismatches. L4 may use shadow results when proposing promotion.

---

# Appendix U - End-to-end worked trace

> **Status tag:** reference

This trace follows a valid DBP frame carrying a WSB2 sparse witness row that decodes into a Witness8 row and then a DPFC family object.

## U.1 Input

> **Status tag:** reference

```yaml
trace_id: witness-trace-v10.6-example-1
transport:
  kind: dbp_frame
  shape_valid: true
  integrity_check: passed
  security_profile: S1
payload:
  kind: wsb2_sparse_rows
  rows:
    - lane: 1
      witness8:
        value_norm: 0.25
        n_sides_norm: 0.6
        center_on: 1.0
        activation_density: 0.5
        kind_flag: 1.0
        band_position: 0.25
        parity: 1.0
        degeneracy: 1.0
family_hint:
  family_id: hex6
  family_schema_version: dpfc-family@v5.6
  digits: [h1, h4]
```

## U.2 Processing steps

> **Status tag:** reference

1. DBP frame shape validates.
2. Integrity and security validate.
3. WSB2 sparse row decodes.
4. Witness8 row validates under explicit field order.
5. L1 extracts witness signature.
6. Family registry resolves `hex6`.
7. Canonicalizer evaluates `[h1,h4]` to `mu_10`.
8. Normal-form key is constructed.
9. L5 allows gated lookup.
10. L2M retrieves matching stable facts.
11. L2 updates recurrent state.
12. Retention metric records core magnitude retention.
13. Audit trace records pinned versions.

## U.3 Rejected alternative path

> **Status tag:** reference

If the same payload arrived with failed integrity validation, semantic decode would be blocked. The row could be retained only as `rejected_untrusted` audit material.

---

# Appendix V - Layer examples

> **Status tag:** reference

## V.1 L1 example

A raw event arrives with a family hint and local confidence. L1 extracts the hint but does not trust it.

## V.2 L2 example

L2 receives a gated lookup result and updates callback persistence without changing schema.

## V.3 L2M example

L2M hashes a normal-form key, not a raw JSON bundle.

## V.4 L3 example

L3 adjusts lookup gate bias during event time but cannot alter the family registry.

## V.5 L4 example

L4 proposes replacing a path normalizer only after shadow canonicalization and replay tests.

## V.6 L5 example

L5 enters `family_bypass` when canonicalization failures exceed the policy threshold.

---


---

# Appendix W - Witness-side source corpus status map

> **Status tag:** reference

This appendix mirrors the Source Architecture Overview from the Witness Contract side. It prevents readers from assuming every named source-map entry already exists as a standalone document.

| Document | Corpus status | Witness-side dependency |
|---|---|---|
| Duotronic Source Architecture Overview | existing | reader entry point and boundary map |
| Duotronic Polygon Family Calculus | existing | family identity, core magnitude, conversion, export rules |
| Duotronic Witness Contract | existing | runtime trust, canonicalization, gating, replay, and policy |
| Duotronic Schema Registry | draft-needed | stable schema identifiers and compatibility matrix |
| Duotronic Family Registry | draft-needed | versioned family declarations and geometry registry |
| Normalizer Profiles | draft-needed | declared canonicalization profiles and failure codes |
| Witness8 Profile | draft-needed | semantic witness-row decoder contract |
| DBP Profile | draft-needed | frame validation and transport-before-semantics boundary |
| WSB2 Profile | draft-needed | sparse-row validation and inactive-lane semantics |
| Retention Diagnostics Profile | draft-needed | metric specs, baselines, pass rules, and telemetry |
| Policy Shield Guide | draft-needed | L5 decision tables, bypass policies, and rollback behavior |
| Migration and Replay Guide | draft-needed | replay identity, shadow canonicalization, and promotion gates |
| EDO and Signal Witness Research Profiles | future | bounded research/reference profiles |
| Public/Internal Language Guide | future | public wording and analogy-boundary language |

`existing` means the document is present in the current corpus. `draft-needed` means the role is recognized and should be extracted into a standalone document before production use. `future` means the topic is valuable but not active implementation authority.

