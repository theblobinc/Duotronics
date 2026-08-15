# Positive-Baseline Polygonal Witness Integration Profile v1.0

**Imported specification:** `Duotronic_Positive_Baseline_Polygonal_Computation_v1.2.md`  
**Witness Contract generation:** v1.6 Draft 5.3.1  
**Status:** optional normative computation profile

## Purpose

This profile maps positive-baseline polygonal computation into the language of evidence. It does not make arithmetic output authoritative and does not treat a visual diagram as an executable record.

## Typed distinctions

| Object | Witness category | Non-collapse rule |
|---|---|---|
| Decoded payload `V` | computational value | not a codeword, status, or physical signal |
| Normalized codeword `P = V + tau` | representation | not a changed payload |
| Physical sample `y = b + gV + eta` | measurement | not a normalized codeword without calibration |
| `ABSENT` socket | structural state | not numeric zero |
| `UNKNOWN`, `INVALID`, `FAULT` | status | not numeric zero |
| Cell result | computational evidence | not theorem, fact, proof, or authority |

## Canonical rules

1. A record declares its required profiles, operator, coefficient, baseline, payload domain, socket order, sockets, children, status, and numeric policy.
2. Unknown required profiles or operators are rejected.
3. A parent consumes `child.payload`, equivalently `child.codeword - child.baseline`; it never consumes the raw child codeword as payload.
4. Stored derived `payload` and `codeword` are recomputed and compared.
5. `even-payload-1` requires exact Python/JSON integers (not Boolean, float, NaN, or infinity), even present socket values, even decoded child payloads, integer weights/coefficient, and an even output.
6. `core-acyclic-1.2` rejects back-edges and unresolved child identifiers.
7. `positive-baseline-1` requires `baseline >= 1` and `codeword = payload + baseline`.
8. Physical-channel claims additionally require calibration evidence; they cannot be inferred from normalized values alone.
9. Arithmetic identity at codeword `tau` is transported structure, not the proposition `tau = 0` in ordinary arithmetic.
10. Pronic and six-socket mappings are optional declared profiles, not inherent properties of hexagonal geometry.

## Evidence emission

A conforming evaluator emits:

- canonical input-record SHAKE256-512;
- evaluator profile and version;
- ordered child result references;
- decoded payload;
- local codeword and baseline;
- status;
- operator identifier;
- domain assertions performed; and
- deterministic error details on refusal.

The output may support a claim with status `computed`. Promotion beyond computation follows the normal Draft 5.3.1 authority path.

## Reference implementation

`executable/runtime/positive_baseline.py` implements the core acyclic profiles. `schemas/positive_baseline_cell_v1.schema.json` performs syntactic checks, while the evaluator performs graph, operator, parity, derived-value, and resource checks that JSON Schema cannot establish alone.
