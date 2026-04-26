# Duotronic Representation Bridge Contract v1.1

**Status:** Source-spec baseline candidate  
**Version:** representation-bridge-contract@v1.1  
**Supersedes:** representation-bridge-contract@v1.0  
**Document kind:** Normative bridge contract plus reference examples  
**Primary purpose:** Define how a source representation is validated, normalized, mapped into a canonical Duotronic object or DPFC core object, optionally converted into a target representation, and evaluated for preservation, expected loss, replay stability, and policy authority.

---

## 1. Scope

This contract governs bridges between:

1. DPFC families;
2. external numeric systems;
3. symbolic numerals;
4. glyphic scripts;
5. natural-language semantic witnesses;
6. graph, matrix, tensor, or geometry objects;
7. transport rows and protocol frames;
8. search/social source records;
9. learned profile candidates;
10. model-generated intermediate forms.

A bridge does not make a source trustworthy. It specifies how a source can be transformed if it has already passed the required validation and canonicalization stages.

---

## 2. Bridge rule

A bridge must never be an informal shortcut.

The required path is:

```text
source surface or object
-> source profile validation
-> source canonicalization
-> bridge function
-> target canonicalization
-> preservation/loss report
-> replay identity
-> policy gate
```

A direct `source-looking-object -> target-looking-object` shortcut is nonconforming if it bypasses validation, normalizer identity, bridge versioning, preservation claims, or expected-loss reporting.

---

## 3. Bridge profile schema

```yaml
RepresentationBridgeProfile:
  bridge_id: string
  bridge_version: string
  status: candidate | research_valid | sandbox_runtime | reference | normative | deprecated | rejected
  owner_document: string

  source_representation:
    profile_id: string
    schema_id: string
    kind: numeral | polygon | glyphic | language | graph | matrix | tensor | transport | external_numeric | social_source | search_source | model_output | custom
    modality: text | image | audio | video | mixed | structured

  target_representation:
    profile_id: string
    schema_id: string
    kind: numeral | polygon | glyphic | language | graph | matrix | tensor | transport | external_numeric | canonical_object | dpfc_core | custom

  validation:
    parser_id: string
    required_fields: []
    invalid_states: []
    ambiguity_policy: reject | preserve_uncertainty | audit_only | profile_specific
    absence_policy: string
    zero_policy: string

  canonicalization:
    source_normalizer_id: string
    target_normalizer_id: string | null
    source_identity_fields: []
    target_identity_fields: []
    display_only_fields: []
    replay_identity_fields: []

  bridge:
    source_to_core: string | null
    core_to_target: string | null
    source_to_canonical_object: string | null
    canonical_object_to_target: string | null
    inverse_bridge: string | null
    totality: total | partial | lossy | research_only
    deterministic: true | false

  preservation:
    must_preserve: []
    should_preserve: []
    expected_loss: []
    prohibited_loss: []

  policy:
    minimum_runtime_mode: audit_only | sandbox | restricted | normal
    required_policy_gate: string
    failure_modes: []

  conformance:
    fixture_pack_id: string
    property_tests: []
    round_trip_tests: []
    replay_tests: []
    failure_tests: []
```

---

## 4. Bridge result schema

```yaml
BridgeResult:
  bridge_result_id: string
  bridge_profile_id: string
  source_canonical_hash: string
  target_canonical_hash: string | null
  core_identity_hash: string | null
  status: canonical_success | lossy_success | audit_only | rejected | bypass_required | replay_mismatch
  preserved_invariants: []
  expected_loss_observed: []
  unexpected_loss_observed: []
  ambiguity_preserved: []
  policy_decision: promote | allow | audit_only | degrade | bypass | reject | rollback
  replay_record_id: string
```

A bridge result must be stored if it influences runtime state, lookup memory, recurrence, profile promotion, migration, or policy.

---

## 5. Loss classes

| Loss class | Meaning | Default behavior |
|---|---|---|
| `display_loss` | Rendering detail removed | Allowed only if declared |
| `provenance_loss` | Source lineage reduced | Usually audit-only or reject |
| `semantic_loss` | Meaning not preserved | Reject unless explicitly lossy export |
| `identity_loss` | Canonical equality cannot be preserved | Reject for authoritative path |
| `confidence_loss` | Uncertainty collapsed | Reject or preserve uncertainty |
| `history_loss` | Construction path lost | Allowed for pure values, not for evidence claims |
| `modality_loss` | Image/audio/video reduced to text | Allowed only with source payload hash retained |

---

## 6. Common bridge classes

### 6.1 DPFC family-to-family

```text
family A -> core magnitude -> family B
```

Normally lossless if both families are valid total encodings of the same core range.

### 6.2 External numeric import/export

```text
external integer/float -> declared import policy -> DPFC or external numeric object
```

Requires explicit zero and range policy.

### 6.3 Symbolic numeral adapter

```text
surface string -> symbolic parse -> canonical symbolic object -> numeric bridge
```

Roman numerals are the reference example.

### 6.4 Glyphic visual-semantic bridge

```text
image region -> visual canonical identity -> sign cluster -> candidate reading
```

The visual layer may be canonical even when reading remains unresolved.

### 6.5 Natural-language claim bridge

```text
text span -> normalized claim witness -> evidence/contradiction graph
```

A normalized claim is not a true claim.

### 6.6 Search/social source bridge

```text
platform item -> source evidence record -> claim/source/propagation witnesses
```

Platform metrics may inform diagnostics but are not proof.

---

## 7. Conformance tests

A bridge profile must include tests for:

1. valid source examples;
2. invalid source examples;
3. ambiguous examples;
4. round-trip where an inverse exists;
5. expected-loss cases;
6. prohibited-loss cases;
7. replay determinism;
8. normalizer version pinning;
9. absence/zero separation;
10. source-to-target preservation;
11. target canonical hash stability;
12. policy failure behavior.

---

## 8. Non-claims

This contract does not claim that every representation can be bridged losslessly. It defines how to declare and test bridges when bridging is possible or useful.


---

## 9. Partial bridge usage

> **Status tag:** normative

A partial bridge is a bridge whose source domain is smaller than the set of valid source-profile objects.

Partial bridges are allowed, but they carry restricted authority by default.

### 9.1 Required declarations

A partial bridge must declare:

1. `bridge_domain_rule`;
2. `non_bridgeable_cases`;
3. `domain_test_fixtures`;
4. `failure_status_for_out_of_domain_input`;
5. `policy_modes_allowed`;
6. whether out-of-domain input is rejected, preserved as unbridged canonical object, or routed to audit-only.

### 9.2 Runtime authority

Default policy:

| Bridge totality | Default allowed mode | Authority |
|---|---|---|
| `total` | restricted or normal if tests pass | may support runtime authority |
| `partial` | audit_only or sandbox | may not support normal authority unless L5 grants explicit exception |
| `lossy` | audit_only or restricted | must declare expected loss |
| `research_only` | audit_only | no runtime authority |

A partial bridge may be used in normal runtime only if:

1. the input is proven inside the declared bridge domain;
2. the `BridgeResult` records the domain proof;
3. out-of-domain behavior is tested;
4. L5 policy explicitly permits the bridge for the target runtime path.

### 9.3 BridgeResult requirement

Every partial bridge use must emit:

```yaml
BridgeResult:
  status: canonical_success | lossy_success | audit_only | rejected | bypass_required
  bridge_totality: partial
  domain_check:
    in_domain: true | false
    rule_id: string
    evidence_ref: string
  non_bridgeable_reason: string | null
```

If `in_domain` is false, the result must be `rejected`, `audit_only`, or `bypass_required`.
