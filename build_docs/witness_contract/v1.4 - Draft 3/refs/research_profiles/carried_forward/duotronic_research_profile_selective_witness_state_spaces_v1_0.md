# Selective Witness State-Space Dynamics as a Bounded Duotronic Research Profile v1.0

**Status:** Research profile paper  
**Version:** research-selective-witness-ssm@v1.0  
**Corpus release:** build_docs/witness_contract/v1.3-draft  
**Document kind:** Research/reference profile, not normative DPFC core  
**Primary purpose:** Define how selective state-space ideas can inform Duotronic witness-gated recurrent models without allowing raw untrusted evidence to select runtime state authority.

> Drafting note. This document follows the one-based Duotronic style for public headings, claim labels, and checklist labels. External machine-learning literature, host languages, arrays, tensors, and physical sciences may still use ordinary zero where their own standards require it. The Duotronic rule is not that zero is forbidden; the rule is that absence, origin, invalidity, numeric zero, raw witness evidence, canonical identity, and transport encoding must not be silently collapsed.

---

## Document status tag key

> **Status tag:** reference

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this profile. | Conforming experimental implementations must follow it. |
| `reference` | Examples, schemas, fixtures, algorithms, and implementation aids. | Useful, but not a new core rule unless cited by a normative section. |
| `research` | Experimental model architecture or benchmark candidate. | Must remain opt-in until benchmarked and promoted. |
| `future` | Planned work not active yet. | Must not be treated as live authority. |
| `analogy` | Outside-field comparison or motivation. | Must not be treated as proof or runtime authority. |

## 1. Research boundary

> **Status tag:** research

A selective state-space model updates hidden state through transition parameters that may vary with the current input or context. This profile imports that idea into Duotronics by allowing canonical witness context, normalization diagnostics, retention diagnostics, and policy state to select or modulate recurrent state evolution.

This profile does not claim that:

1. DPFC arithmetic is a neural state-space model;
2. selective state-space math proves Duotronics;
3. raw witness evidence may control trusted state updates;
4. state-space retention is physical decoherence;
5. a learned neural gate can override L5 policy.

## 2. Central form

> **Status tag:** reference

A Duotronic Witness Selective State-Space Model, abbreviated **DW-SSM**, has the abstract form:

\[
s_t=A_t s_{t-1}+B_t u_t,
\]

\[
y_t=C_t s_t+D_t u_t.
\]

The selected matrices are functions of canonical Duotronic context:

\[
A_t=f_A(k_t^{\mathrm{nf}},d_t^{\mathrm{norm}},p_t,r_t),
\]

\[
B_t=f_B(k_t^{\mathrm{nf}},d_t^{\mathrm{norm}},p_t,r_t),
\]

\[
C_t=f_C(k_t^{\mathrm{nf}},d_t^{\mathrm{norm}},p_t,r_t),
\]

\[
D_t=f_D(p_t).
\]

Where:

1. \(s_t\) is recurrent witness state;
2. \(u_t\) is validated event/input embedding;
3. \(k_t^{\mathrm{nf}}\) is canonical normal-form witness key;
4. \(d_t^{\mathrm{norm}}\) is normalization/canonicalization diagnostics;
5. \(p_t\) is L5 policy state;
6. \(r_t\) is declared retention diagnostic context.

## 3. Canonicalization-before-selection

> **Status tag:** normative

Authoritative state selection MUST NOT be computed from raw untrusted witness evidence when a normal-form path exists. The permitted path is:

```text
raw event
-> transport validation
-> semantic decode
-> witness extraction
-> family/normalizer registry lookup
-> canonicalization
-> policy gate
-> selective state-space update
```

If transport validation or canonicalization fails, the state-space implementation must use an explicit bypass/degraded mode.

## 4. Gate decomposition

> **Status tag:** reference

A practical DW-SSM may decompose update authority into three gates:

\[
\rho_t=\sigma(g_\rho(k_t^{\mathrm{nf}},r_t,p_t)),
\]

\[
\beta_t=\sigma(g_\beta(k_t^{\mathrm{nf}},d_t^{\mathrm{norm}},p_t)),
\]

\[
\lambda_t=\sigma(g_\lambda(k_t^{\mathrm{nf}},m_t,d_t^{\mathrm{norm}},p_t)).
\]

The update is:

\[
s_t=\rho_t\odot s_{t-1}+\beta_t\odot B_tu_t+\lambda_t\odot m_t.
\]

Here \(\rho_t\) controls state retention, \(\beta_t\) controls new event admission, and \(\lambda_t\) controls L2M lookup injection.

## 5. Policy clamps

> **Status tag:** normative

L5 policy clamps dominate learned gate values. The profile-level defaults are:

| Mode | Input admission | Lookup injection | Semantic state write |
|---|---:|---:|---:|
| `normal` | allowed | allowed | allowed |
| `degraded` | reduced | reduced | conservative |
| `family_bypass` | generic only | generic only | family-sensitive blocked |
| `transport_bypass` | blocked for failed payload | blocked for failed payload | blocked |
| `lookup_bypass` | allowed | blocked | allowed without lookup |
| `full_bypass` | blocked | blocked | blocked or minimal safe decay |

## 6. Continuous-time optional form

> **Status tag:** research

A continuous-time variant may define:

\[
\dot{s}(t)=A(\xi_t)s(t)+B(\xi_t)u(t),
\]

where \(\xi_t=(k_t^{\mathrm{nf}},d_t^{\mathrm{norm}},p_t,r_t)\). A deterministic discretization over \(\Delta_t\) may use:

\[
\overline{A}_t=\exp(\Delta_t A(\xi_t)),
\]

\[
\overline{B}_t=\left(\int_0^{\Delta_t}\exp(\tau A(\xi_t))d\tau\right)B(\xi_t).
\]

If the discretized state affects replay or promotion, the discretization method, floating-point profile, and seed must be replay-pinned.

## 7. DPFC boundary

> **Status tag:** normative

DPFC objects may supply canonical features for state selection. They do not become state-space matrices and their arithmetic is not redefined. Inter-family conversion remains:

\[
\Psi_{F\to G}=\Phi_G^{-1}\circ\Phi_F.
\]

A DW-SSM may use family ID, canonical digits, core magnitude hash, witness-history hash, and export policy as features, but it must not reinterpret successor, addition, multiplication, or export correction.

## 8. Retention diagnostics

> **Status tag:** research

DW-SSM adds diagnostics for whether trusted witness context appropriately governs state update authority. Example metrics include:

```yaml
RetentionMetricSpec:
  metric_id: low-confidence-no-authority-gain@v1
  invariant_kind: gate_monotonicity
  extractor_id: state-gate-extractor@v1
  similarity_id: finite_difference_monotonicity@v1
  transformation: canonicalization_to_state_gate
  baseline_suite: [confidence_sweep, malformed_witness, transport_invalid]
  preservation_class: must_preserve
  failure_action: block_promotion
```

## 9. Reference fixtures

> **Status tag:** reference

```yaml
fixture_pack: selective-witness-state-space-v1-fixtures
fixtures:
  - fixture_id: DWSSM-FIXTURE-1-FAILED-CANONICALIZATION-ZERO-UPDATE
    given:
      canonicalization_result: malformed_reject
      previous_state_hash: state_A
      policy_mode: family_bypass
    operation: selective_state_update
    expected:
      state_update_allowed: false
      new_state_hash: state_A
      lookup_injection_allowed: false

  - fixture_id: DWSSM-FIXTURE-2-VALID-WITNESS-SELECTIVE-UPDATE
    given:
      canonicalization_result: canonical_success
      normalizer_confidence: 1.0
      policy_mode: normal
      witness_key: family:hex6 schema_version:dpfc-family@v5.9 digits:1 4
    operation: selective_state_update
    expected:
      state_update_allowed: true
      update_source: canonical_witness
      raw_witness_used_for_matrix_selection: false

  - fixture_id: DWSSM-FIXTURE-3-LOW-CONFIDENCE-DEMOTES-UPDATE
    given:
      canonicalization_result: canonical_success_low_confidence
      normalizer_confidence: 0.34
      policy_mode: degraded
    operation: selective_state_update
    expected:
      update_strength_max: 0.34
      lookup_authority_increased: false

  - fixture_id: DWSSM-FIXTURE-4-TRANSPORT-BYPASS-BLOCKS-SEMANTIC-UPDATE
    given:
      transport_validation: failed_integrity
      payload_kind: witness8
      previous_state_hash: state_B
    operation: selective_state_update
    expected:
      semantic_state_update_allowed: false
      policy_mode: transport_bypass
      trusted_memory_write: false
```

## 10. Minimal implementation sketch

> **Status tag:** reference

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class StateSelectionContext:
    canonical_key_hash: Optional[str]
    confidence: float
    policy_mode: str
    transport_valid: bool
    canonicalization_result: str


def policy_clamp(authority: float, ctx: StateSelectionContext) -> float:
    if not ctx.transport_valid:
        return 0.0
    if ctx.policy_mode in {"transport_bypass", "full_bypass"}:
        return 0.0
    if ctx.canonicalization_result not in {"canonical_success", "canonical_success_low_confidence"}:
        return 0.0
    return min(authority, max(0.0, ctx.confidence))


def selective_update(s_prev, s_candidate, authority, ctx):
    a = policy_clamp(authority, ctx)
    return s_prev + a * (s_candidate - s_prev)
```

This sketch is intentionally small. Production implementations must use versioned schemas, replay identity, deterministic fixtures, and Policy Shield decisions.

## 11. Promotion path

> **Status tag:** future

A DW-SSM profile may be promoted from research to normative reference only after:

1. fixture pack passes;
2. malformed/bypass cases fail closed;
3. replay identity is stable;
4. low-confidence inputs cannot increase authority;
5. transport-invalid payloads cannot update semantic state;
6. policy clamps dominate learned gate outputs;
7. migration and rollback are tested.

## 12. Final boundary statement

> **Status tag:** normative

DW-SSM is a Duotronic runtime profile for selective recurrent state evolution. It is not DPFC arithmetic, not physics, not proof of cognition, and not authority to trust raw evidence. It is useful only when canonical witness context and policy state govern what may enter, remain in, or be read from recurrent state.

---

## v1.4 compatibility note

This profile is carried forward as bounded research material. It may inform witness extraction, fixtures, diagnostics, or profile candidates, but it does not gain runtime authority under v1.4 unless staged through the Profile Synthesis Registry, replayed, tested, and approved by the Policy Shield.

