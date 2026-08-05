# Corpus Index - v1.6 Draft 5.2.1

Active entry points:

- `START_HERE.md`
- `README.md`
- `DRAFT5_2_1_LEAN_PROOF_AUTHORITY_UPDATE_REPORT_v1_0.md`
- `kernel/lean_proof_authority_contract_v1_0.md`
- `kernel/logical_observer_kernel_contract_v1_0.md`
- `EVIDENCE_LANGUAGE_OPERATING_SYSTEM_PRIMER_v1_0.md`

Lean proof authority files:

- `lean-toolchain`
- `lakefile.lean`
- `Duotronic.lean`
- `Duotronic/All.lean`
- `Duotronic/Core.lean`
- `Duotronic/CoreMetaphysics.lean`
- `Duotronic/EvidenceSyntax.lean`
- `Duotronic/ProofAuthority.lean`
- `Duotronic/Kernel.lean`
- `executable/formal/run_lean_build.py`
- `refs/formal_toolchain/lean_toolchain_manifest_v1_0.json`

New schemas:

- `schemas/lean_compiler_witness.schema.json`
- `schemas/proof_witness.schema.json`
- `schemas/theorem_promotion_gate.schema.json`

Validation:

```bash
python3 executable/validators/validate_draft5_2_1_corpus.py
python3 executable/formal/run_lean_build.py --mode advisory --json
```

Strict theorem-promotion CI:

```bash
python3 executable/formal/run_lean_build.py --mode strict --json
```
