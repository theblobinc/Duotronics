"""Run every reference-impl module's self-test in series.

Used by CI as a pre-flight; if any module's self-test fails, the
conformance run is meaningless because the SUT is broken.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from duotronic_ref import (
    canonicalizer,
    dbp,
    dpfc,
    normalizer,
    policy_shield,
    replay,
    retention,
    spectral,
    witness8,
    wsb2,
)


MODULES = (
    ("dpfc", dpfc.run_reference_self_test),
    ("witness8", witness8.run_reference_self_test),
    ("dbp", dbp.run_reference_self_test),
    ("wsb2", wsb2.run_reference_self_test),
    ("normalizer", normalizer.run_reference_self_test),
    ("canonicalizer", canonicalizer.run_reference_self_test),
    ("spectral", spectral.run_spectral_edo_self_test),
    ("replay", replay.run_reference_self_test),
    ("retention", retention.run_reference_self_test),
    ("policy_shield", policy_shield.run_reference_self_test),
)


def main() -> int:
    failures = []
    for name, fn in MODULES:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {name}: {exc}")
            failures.append(name)
    if failures:
        print(f"FAILED self-tests: {failures}")
        return 1
    print("All reference self-tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
