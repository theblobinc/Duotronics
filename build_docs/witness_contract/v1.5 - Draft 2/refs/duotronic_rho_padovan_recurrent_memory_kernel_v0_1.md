# Duotronic Rho-Padovan Recurrent Memory Kernel v0.1

**Status:** Research profile specification  
**Version:** rho-padovan-memory-kernel@v0.1  
**Document kind:** Bounded experimental recurrent-memory kernel contract  
**Primary purpose:** Define a plastic-ratio / Padovan recurrence option for branch-local witness memory, diagnostics, and ranking experiments without changing canonical chronology or granting authority to raw recurrence math.

---

## 1. Scope

This profile adds an optional recurrent-memory kernel to v1.5 Draft 2.

It covers:

1. plastic-ratio constants and inverse ladder values;
2. rho-ladder EMA updates;
3. damped Padovan delayed memory updates;
4. hybrid one-step plus delayed callback memory;
5. trace diagnostics that compare baseline EMA behavior with the rho kernel;
6. feature-flagged use in branch-local, ranking, or canonical-shadow contexts.

It does not replace DPFC, WG-RNN, Phi/Psi recurrence, the Policy Shield, canonical chronology, or any canonical witness fact.

---

## 2. Research status

The rho kernel is a research profile.

It may be used for:

1. branch-local worker loops;
2. ranking diagnostics;
3. canonical-shadow diagnostics;
4. replay experiments;
5. fixture generation.

It must not be enabled as canonical memory behavior until replay parity, ranking stability, retention diagnostics, and operator approval are present.

---

## 3. Constants

```text
rho = 1.324717957244746
rho^3 = rho + 1
rho^-1 = 0.7548776662466927
rho^-2 = 0.5698402909980532
rho^-3 = 0.4301597090019468
rho^-4 = 0.3247179572447460
```

The inverse ladder is interpreted as:

| Tier | Value | Intended use |
|---|---:|---|
| `long` | `rho^-1` | persistent callback residue |
| `medium` | `rho^-2` | ordinary witness smoothing |
| `short` | `rho^-3` | delayed Padovan carry normalization |
| `fast` | `rho^-4` | novelty or fast-decay threshold |

Implementations must keep these constants in one module and import them rather than duplicating literals across the runtime.

---

## 4. Memory modes

### 4.1 Rho-ladder EMA

```text
mass_t[k] = lambda_k * mass_(t-1)[k] + delta_t[k]
```

`lambda_k` must be selected from the rho ladder or from a policy-approved family mapping that does not exceed `rho^-1`.

### 4.2 Damped Padovan delayed recurrence

```text
carry_t = alpha * rho^-3 * (m_(t-2) + m_(t-3))
m_t = carry_t + delta_t
```

`alpha` must satisfy `0 <= alpha <= 1`. This delayed path intentionally skips `t-1`; it is for callback motifs that reappear after a gap.

### 4.3 Hybrid rho-Padovan update

```text
ema_part_t = lambda_k * m_(t-1)
padovan_part_t = beta_k * rho^-3 * (m_(t-2) + m_(t-3))
m_t = ema_part_t + padovan_part_t + delta_t
```

The hybrid mode must satisfy:

```text
0 <= lambda_k <= rho^-1
0 <= beta_k <= 1 - lambda_k
```

---

## 5. Feature flags

The profile defines these implementation flags:

```text
SRNN_ENABLE_RHO_KERNEL=false
SRNN_RHO_KERNEL_SCOPE=worker
SRNN_RHO_MEMORY_MODE=hybrid
SRNN_RHO_ALPHA=0.85
SRNN_RHO_BETA=0.25
SRNN_RHO_TRACE_DEPTH=3
SRNN_RHO_DIAGNOSTICS=true
SRNN_RHO_PERSIST_FIELDS=false
```

Allowed scopes are `off`, `worker`, `ranking`, `canonical_shadow`, and `canonical`.

`canonical` must be rejected unless replay parity, ranking stability, and diagnostics gates have passed. The rho kernel is experimental memory support, not the source of canonical chain truth.

---

## 6. Object classes

The profile adds these schema classes:

1. `RhoKernelConfig`;
2. `RhoPadovanTrace`;
3. `RhoMemoryStepInput`;
4. `RhoMemoryStepResult`;
5. `RhoKernelDiagnostics`;
6. `RhoKernelReplayIdentity`.

All persisted results must record the memory mode, alpha, beta, decay tier, selected family, replay identity, and whether the step was authoritative, diagnostic-only, or rejected.

---

## 7. Runtime rule

Rho memory may influence candidate ranking or branch-local recall only through explicit diagnostics unless policy grants a stronger scope.

The required flow is:

```text
canonical witness features
-> policy scope check
-> rho kernel step
-> diagnostics / branch-local memory trace
-> ranking or candidate support
-> policy clamp before any authoritative effect
```

Raw source records, model output, node metrics, or transport payloads must not update rho memory without the same witness and policy gates used by WG-RNN.

---

## 8. Harness mirror

The v1.5 Draft 2 harness mirrors the executable subset with:

```text
op: evaluate_rho_memory_kernel
```

The initial fixture proves that hybrid mode uses a bounded rho-ladder decay, includes delayed Padovan carry, and remains diagnostic-only under worker scope.
