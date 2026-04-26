# GCD-Jump Recurrences as Sparse Duotronic Witness Gates v1.0

**Status:** Research profile paper  
**Version:** research-gcd-jump-recurrences@v1.0  
**Document kind:** Bounded recurrence/witness-gating research profile, not DPFC core  
**Primary purpose:** Import the useful method pattern from GCD-jump prime recurrences into Duotronic witness recurrence, sparse update scheduling, DW-SSM gate fixtures, and conformance examples without claiming this is a faster prime generator or a replacement for DPFC arithmetic.

> Drafting note. This document follows the one-based Duotronic style for public headings, claim labels, and fixture labels. External recurrence literature and host-language arrays may still use ordinary zero where appropriate. The Duotronic rule is not that zero is forbidden; the rule is that absence, origin, invalidity, numeric zero, raw witness evidence, canonical identity, transport encoding, and recurrence state must not be silently collapsed.

---

## Document status tag key

> **Status tag:** reference

| Tag | Meaning | Promotion rule |
|---|---|---|
| `normative` | Binding rule for this research profile. | Conforming experimental implementations must follow it. |
| `reference` | Examples, algorithms, fixtures, schemas, or implementation aids. | Useful for implementation, but not a new DPFC rule. |
| `research` | Experimental diagnostic, recurrence pattern, benchmark, or gating method. | Must remain opt-in until benchmarked and promoted. |
| `future` | Named work not completed in this document. | Must not be treated as live semantics. |
| `analogy` | Outside-field comparison or motivation. | Must not be treated as proof or runtime authority. |

## 1. Research boundary

> **Status tag:** research

This profile studies recurrences of the form:

\[
R(n)=R(n-1)+\gcd(n,R(n-1)).
\]

With the common seed:

\[
R(1)=7.
\]

The increment is:

\[
J(n)=R(n)-R(n-1)=\gcd(n,R(n-1)).
\]

The useful Duotronic import is not "this is the best way to generate primes." It is the recurrence pattern:

```text
cheap local step -> long low-information runs -> sparse high-information jumps
```

That pattern is useful for witness recurrence, DW-SSM event gating, harness fixtures, sparse memory writes, and selective runtime updates.

This profile does not claim that:

1. GCD-jump recurrences redefine DPFC arithmetic;
2. GCD-jump recurrences are faster than sieves for practical prime generation;
3. every nontrivial GCD jump is automatically semantically authoritative;
4. a raw recurrence jump may bypass transport validation, canonicalization, or policy gating;
5. prime-producing recurrence behavior proves Duotronic witness theory.

## 2. Reference recurrence

> **Status tag:** reference

The seed-seven profile is:

\[
R_1=7,
\]

\[
J_n=\gcd(n,R_{n-1}),
\]

\[
R_n=R_{n-1}+J_n.
\]

Early terms:

| Step | Previous state | Jump \(J_n\) | Next state | Event class |
|---:|---:|---:|---:|---|
| 2 | 7 | 1 | 8 | trivial continuation |
| 3 | 8 | 1 | 9 | trivial continuation |
| 4 | 9 | 1 | 10 | trivial continuation |
| 5 | 10 | 5 | 15 | nontrivial jump |
| 6 | 15 | 3 | 18 | nontrivial jump |

A nontrivial jump is:

\[
J_n>1.
\]

A trivial continuation is:

\[
J_n=1.
\]

## 3. Sparse witness gate interpretation

> **Status tag:** research

A GCD-jump recurrence can be interpreted as a sparse witness gate:

\[
\operatorname{jump}_n = \mathbf{1}[J_n>1].
\]

A witness runtime may use this as a cheap event detector:

\[
\alpha_n = \operatorname{clamp}_{L5}\left(\alpha_{base}+\alpha_{jump}\mathbf{1}[J_n>1]\right).
\]

Here \(\alpha_n\) is update authority. It is not trust by itself. It must be bounded by policy, canonicalization, validation, and confidence.

The Duotronic rule is:

```text
gcd jump detected -> candidate witness event -> validation/canonicalization/policy -> possible state update
```

not:

```text
gcd jump detected -> trusted state update
```

## 4. DW-SSM integration

> **Status tag:** research

A selective witness state-space runtime may add a jump-event term to the recurrent update:

\[
s_n=\rho_n\odot s_{n-1}+\beta_n\odot B_nu_n+\lambda_n\odot m_n+\eta_n\odot e^J_n.
\]

Where:

1. \(s_n\) is recurrent witness state;
2. \(u_n\) is the admitted event embedding;
3. \(m_n\) is gated L2M lookup memory;
4. \(e^J_n\) is a jump-event embedding derived from the validated recurrence witness;
5. \(\eta_n\) is jump-event authority after policy clamps.

A conservative authority rule is:

\[
\eta_n = \operatorname{clamp}_{L5}\left(c_n^{norm}\cdot \mathbf{1}[J_n>1]\cdot h(J_n)\right),
\]

where \(c_n^{norm}\) is canonicalization confidence and \(h\) is a bounded embedding or scoring function for the jump magnitude.

Low confidence MUST NOT increase \(\eta_n\). A failed transport or failed canonicalization path MUST force \(\eta_n=0\) for authoritative state writes.

## 5. DPFC boundary

> **Status tag:** normative

GCD-jump recurrences do not alter DPFC successor, addition, multiplication, inter-family conversion, canonical serialization, or export algebra.

They may be used as:

1. witness-runtime fixtures;
2. sparse recurrence benchmarks;
3. event-gated state-update examples;
4. research profiles for selective state-space dynamics;
5. examples of external arithmetic entering through a declared adapter boundary.

If a GCD-jump recurrence state is represented as a DPFC object, the recurrence value must enter through an explicit adapter profile and must still be canonicalized before trusted use.

## 6. Performance boundary

> **Status tag:** normative

The profile MUST NOT be described as a faster general prime-generation method unless benchmark evidence supports that claim against ordinary prime-generation baselines.

The performance value for Duotronics is narrower:

1. sparse update scheduling;
2. cheap event detection;
3. recurrence compression;
4. selective witness gating;
5. conformance fixtures for trivial-versus-jump behavior.

## 7. Fixture pack

> **Status tag:** reference

```yaml
fixture_pack: gcd-jump-recurrence-v1-fixtures
fixtures:
  - fixture_id: GCD-JUMP-FIXTURE-1-SEED-7-EARLY-STEPS
    given:
      recurrence: R(n) = R(n-1) + gcd(n, R(n-1))
      initial:
        n: 1
        R: 7
    operation: generate_steps
    expected:
      steps:
        - {n: 2, previous_R: 7, gcd_jump: 1, next_R: 8, event_class: trivial_continuation}
        - {n: 3, previous_R: 8, gcd_jump: 1, next_R: 9, event_class: trivial_continuation}
        - {n: 4, previous_R: 9, gcd_jump: 1, next_R: 10, event_class: trivial_continuation}
        - {n: 5, previous_R: 10, gcd_jump: 5, next_R: 15, event_class: nontrivial_jump}
        - {n: 6, previous_R: 15, gcd_jump: 3, next_R: 18, event_class: nontrivial_jump}

  - fixture_id: GCD-JUMP-FIXTURE-2-TRIVIAL-STEPS-DO-NOT-FORCE-MEMORY-WRITE
    given:
      gcd_jump: 1
      canonicalization_result: canonical_success
      policy_mode: normal
    operation: recurrence_event_to_memory_write
    expected:
      nontrivial_jump_witness: false
      authoritative_memory_write_required: false
      state_update_may_use_cheap_successor: true

  - fixture_id: GCD-JUMP-FIXTURE-3-JUMP-IS-CANDIDATE-NOT-AUTHORITY
    given:
      gcd_jump: 5
      canonicalization_result: raw_only
      policy_mode: normal
    operation: recurrence_event_to_memory_write
    expected:
      candidate_jump_detected: true
      trusted_memory_write_allowed: false
      reason: normal_form_before_trust_not_satisfied

  - fixture_id: GCD-JUMP-FIXTURE-4-VALID-JUMP-MAY-RAISE-DWSSM-AUTHORITY
    given:
      gcd_jump: 5
      canonicalization_result: canonical_success
      normalizer_confidence: 1.0
      policy_mode: normal
    operation: gcd_jump_to_selective_state_update
    expected:
      candidate_jump_detected: true
      jump_event_embedding_allowed: true
      update_authority_may_increase: true
      policy_clamp_required: true

  - fixture_id: GCD-JUMP-FIXTURE-5-TRANSPORT-FAILURE-BLOCKS-JUMP-AUTHORITY
    given:
      gcd_jump: 5
      transport_validation: failed_integrity
      policy_mode: transport_bypass
    operation: gcd_jump_to_selective_state_update
    expected:
      candidate_jump_detected: true
      semantic_state_update_allowed: false
      jump_authority: 0
      trusted_memory_write: false
```

## 8. Minimal reference implementation

> **Status tag:** reference

```python
from math import gcd


def gcd_jump_steps(seed=7, start_n=2, count=5):
    state = seed
    out = []
    for n in range(start_n, start_n + count):
        jump = gcd(n, state)
        next_state = state + jump
        out.append({
            "n": n,
            "previous_R": state,
            "gcd_jump": jump,
            "next_R": next_state,
            "event_class": "nontrivial_jump" if jump > 1 else "trivial_continuation",
        })
        state = next_state
    return out


def recurrence_authority(jump, canonicalized, confidence, policy_mode):
    if policy_mode in {"transport_bypass", "full_bypass"}:
        return 0.0
    if not canonicalized:
        return 0.0
    if jump <= 1:
        return 0.0
    return max(0.0, min(1.0, float(confidence)))


if __name__ == "__main__":
    early = gcd_jump_steps(seed=7, start_n=2, count=5)
    assert [x["gcd_jump"] for x in early] == [1, 1, 1, 5, 3]
    assert recurrence_authority(5, True, 1.0, "normal") == 1.0
    assert recurrence_authority(5, False, 1.0, "normal") == 0.0
    assert recurrence_authority(5, True, 1.0, "transport_bypass") == 0.0
```

## 9. Promotion path

> **Status tag:** future

This profile may be promoted from research example to reference architecture only after:

1. fixture pack passes;
2. recurrence adapter is deterministic;
3. trivial steps do not cause unnecessary authoritative writes;
4. jump events improve at least one benchmarked sparse-update workload;
5. prime-generation claims remain bounded or benchmarked;
6. failed validation and failed canonicalization block authority;
7. integration with DW-SSM does not break replay identity.

---

## v1.4 compatibility note

This profile is carried forward as bounded research material. It may inform witness extraction, fixtures, diagnostics, or profile candidates, but it does not gain runtime authority under v1.4 unless staged through the Profile Synthesis Registry, replayed, tested, and approved by the Policy Shield.

