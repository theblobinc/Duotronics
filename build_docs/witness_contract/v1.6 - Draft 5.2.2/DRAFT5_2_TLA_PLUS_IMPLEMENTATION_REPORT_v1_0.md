# Draft 5.2 TLA+ Implementation Report v1.0

Status: TLA+ implementation added; Lean toolchain intentionally not added.

This update implements a TLA+-only formal execution surface for Draft 5.2. It upgrades the existing TLA stubs into bounded TLC-ready specifications and adds configs, a runner, and a manifest. The integration is deliberately scoped to TLA+ and does not add Lake, Lean build files, or a Lean compiler workflow.

## Added or upgraded files

- `formal/tlaplus/EvidenceClaimGraph.tla`
- `formal/tlaplus/EvidenceClaimGraph.cfg`
- `formal/tlaplus/TaskDelegationAndPolicyCoreSpec.tla`
- `formal/tlaplus/TaskDelegationAndPolicyCoreSpec.cfg`
- `formal/tlaplus/NonCollapseRuntime.tla`
- `formal/tlaplus/NonCollapseRuntime.cfg`
- `formal/tlaplus/LogicalObserverKernel.tla`
- `formal/tlaplus/LogicalObserverKernel.cfg`
- `executable/formal/run_tla_model_check.py`
- `refs/formal_toolchain/tla_toolchain_manifest_v1_0.json`

## Scope

The TLA+ surface covers:

1. evidence claim composition and proof-gated theorem promotion;
2. task delegation and policy-gated completion;
3. non-collapse runtime transitions with external/proof/authority witness classes;
4. logical observer kernel task execution with no-effect-before-witness and no-commit-without-result-witness invariants.

## Commands

Advisory mode performs portable static checks and runs TLC if `tla2tools.jar` is available:

```bash
python executable/formal/run_tla_model_check.py --mode advisory
```

Strict mode requires TLC:

```bash
python executable/formal/run_tla_model_check.py --mode strict
```

TLC is resolved through either:

1. `TLA2TOOLS_JAR`; or
2. `tools/tla2tools.jar` under the corpus root.

## Local validation note

The package validator invokes advisory TLA+ checks. In an environment without `tla2tools.jar`, this confirms manifest/config/static consistency and reports advisory pass. Full TLC model checking is available in strict mode once TLC is provided.
