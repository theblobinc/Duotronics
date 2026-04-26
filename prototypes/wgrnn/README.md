# Duotronic WG-RNN Research Prototype

This package is a sandboxed research prototype for the v1.5 Draft 2 Witness-Gated Recurrent Cell.

It is not the canonical Duotronic runtime and must not be treated as production behavior. The Duotronics repository remains the specification and conformance asset authority while the canonical implementation target is still undecided.

The prototype demonstrates:

1. witness-derived authority checks;
2. explicit policy clamps for write, decay, quarantine, and promotion gates;
3. slot-based persistent memory with candidate and quarantine writes;
4. `MemoryUpdateRecord` emission for every step, including no-op steps;
5. deterministic replay identity hashing that excludes wall-clock timestamps;
6. a four-event sample loop matching the v1.5 Draft 2 research fixtures.

## Quick Start

```sh
cd prototypes/wgrnn
python -m duotronic_wgrnn.runner
pytest -q
```

The prototype uses PyTorch for tensor operations, but it intentionally keeps the policy and record logic plain and inspectable.
