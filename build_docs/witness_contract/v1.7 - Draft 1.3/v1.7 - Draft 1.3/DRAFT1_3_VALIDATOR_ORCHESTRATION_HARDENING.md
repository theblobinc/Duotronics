# Draft 1.3 Validator Orchestration Hardening

The active validator now supports per-stage progress records, per-stage timeout warnings, partial report emission on timeout/failure, and explicit skip flags:

- `--skip-inherited`
- `--skip-lean`
- `--skip-tla`

Subprocesses for inherited validators and formal runners use sanitized environments. Toolchain timeouts are reported under `toolchain_warnings`; corpus failures remain under `corpus_errors`.
