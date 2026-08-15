#!/usr/bin/env python3
"""Deterministic reference evaluator for positive-baseline polygonal cells."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EVALUATOR_VERSION = "positive-baseline-reference/1.0"
KNOWN_PROFILES = {"core-acyclic-1.2", "positive-baseline-1", "even-payload-1"}
KNOWN_OPERATORS = {"global-scaled-weighted-sum", "child-scaled-weighted-sum"}


class EvaluationError(ValueError):
    """Deterministic refusal with a stable error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CellResult:
    cell_id: str
    payload: int
    codeword: int
    baseline: int
    assertion_log: tuple[str, ...]


def _exact_int(value: Any, label: str) -> int:
    if type(value) is not int:
        raise EvaluationError("domain_violation", f"{label} must be an exact integer")
    return value


def _shake256_512_json(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.shake_256(canonical.encode("utf-8")).hexdigest(64)


def bijective_encode(n: int, alphabet: list[str]) -> tuple[str, ...]:
    _exact_int(n, "n")
    if n <= 0:
        raise EvaluationError("domain_violation", "bijective numerals represent positive integers")
    if not alphabet or len(alphabet) != len(set(alphabet)) or any(not isinstance(s, str) or not s for s in alphabet):
        raise EvaluationError("alphabet_invalid", "alphabet must contain unique nonempty symbols")
    base = len(alphabet)
    result: list[str] = []
    while n:
        n, remainder = divmod(n - 1, base)
        result.append(alphabet[remainder])
    return tuple(reversed(result))


def bijective_decode(symbols: list[str] | tuple[str, ...], alphabet: list[str]) -> int:
    if not symbols:
        raise EvaluationError("domain_violation", "empty sequence is not a positive bijective numeral")
    if not alphabet or len(alphabet) != len(set(alphabet)) or any(not isinstance(s, str) or not s for s in alphabet):
        raise EvaluationError("alphabet_invalid", "alphabet must contain unique nonempty symbols")
    digits = {symbol: index + 1 for index, symbol in enumerate(alphabet)}
    value = 0
    for symbol in symbols:
        if symbol not in digits:
            raise EvaluationError("alphabet_invalid", f"symbol is not in alphabet: {symbol!r}")
        value = len(alphabet) * value + digits[symbol]
    return value


def encode_baseline(payload: int, baseline: int = 1) -> int:
    return _exact_int(payload, "payload") + _exact_int(baseline, "baseline")


def decode_baseline(codeword: int, baseline: int = 1) -> int:
    return _exact_int(codeword, "codeword") - _exact_int(baseline, "baseline")


def evaluate_graph(package: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(package, dict):
        raise EvaluationError("schema_validation_failed", "graph package must be an object")
    root_id = package.get("root_cell_id")
    rows = package.get("cells")
    if not isinstance(root_id, str) or not root_id:
        raise EvaluationError("schema_validation_failed", "root_cell_id is required")
    if not isinstance(rows, list) or not rows:
        raise EvaluationError("schema_validation_failed", "cells must be a nonempty array")

    cells: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("cell_id"), str) or not row["cell_id"]:
            raise EvaluationError("schema_validation_failed", "every cell requires a nonempty cell_id")
        if row["cell_id"] in cells:
            raise EvaluationError("duplicate_cell_id", f"duplicate cell_id: {row['cell_id']}")
        cells[row["cell_id"]] = row
    if root_id not in cells:
        raise EvaluationError("unresolved_child", f"root cell does not exist: {root_id}")

    root_policy = cells[root_id].get("numeric_policy", {})
    max_nodes = _exact_int(root_policy.get("max_nodes"), "root numeric_policy.max_nodes")
    max_depth = _exact_int(root_policy.get("max_depth"), "root numeric_policy.max_depth")
    if max_nodes < 1 or max_depth < 1 or len(cells) > max_nodes:
        raise EvaluationError("resource_budget_exceeded", "graph exceeds declared node or depth budget")

    active: set[str] = set()
    memo: dict[str, CellResult] = {}

    def evaluate(cell_id: str, depth: int) -> CellResult:
        if depth > max_depth:
            raise EvaluationError("resource_budget_exceeded", "graph exceeds max_depth")
        if cell_id in active:
            raise EvaluationError("cycle_detected", f"cycle includes cell: {cell_id}")
        if cell_id in memo:
            return memo[cell_id]
        if cell_id not in cells:
            raise EvaluationError("unresolved_child", f"child cell does not exist: {cell_id}")

        cell = cells[cell_id]
        required = {"schema_version", "profiles", "payload_domain", "operator", "coefficient", "baseline", "sockets", "children", "status", "numeric_policy"}
        missing = sorted(required - set(cell))
        if missing:
            raise EvaluationError("schema_validation_failed", f"{cell_id} missing fields: {missing}")
        if cell["schema_version"] != "positive_baseline_cell/v1":
            raise EvaluationError("schema_validation_failed", f"{cell_id} has unsupported schema_version")
        profiles = cell["profiles"]
        if not isinstance(profiles, list) or not profiles:
            raise EvaluationError("unknown_profile", f"{cell_id} must declare profiles")
        unknown_profiles = set(profiles) - KNOWN_PROFILES
        if unknown_profiles:
            raise EvaluationError("unknown_profile", f"{cell_id} requires unknown profiles: {sorted(unknown_profiles)}")
        if "core-acyclic-1.2" not in profiles:
            raise EvaluationError("unknown_profile", f"{cell_id} lacks core-acyclic-1.2")
        if cell["operator"] not in KNOWN_OPERATORS:
            raise EvaluationError("unknown_operator", f"{cell_id} has unknown operator: {cell['operator']!r}")
        if cell["status"] != "VALID":
            raise EvaluationError("status_not_valid", f"{cell_id} status is {cell['status']!r}")

        coefficient = _exact_int(cell["coefficient"], f"{cell_id}.coefficient")
        baseline = _exact_int(cell["baseline"], f"{cell_id}.baseline")
        if baseline < 0 or ("positive-baseline-1" in profiles and baseline < 1):
            raise EvaluationError("domain_violation", f"{cell_id} baseline violates declared profile")
        domain = cell["payload_domain"]
        if not isinstance(domain, dict) or domain.get("kind") != "integer":
            raise EvaluationError("domain_violation", f"{cell_id} supports only the exact integer domain")
        minimum = _exact_int(domain.get("minimum"), f"{cell_id}.payload_domain.minimum")
        maximum = domain.get("maximum")
        if maximum is not None:
            maximum = _exact_int(maximum, f"{cell_id}.payload_domain.maximum")
            if maximum < minimum:
                raise EvaluationError("domain_violation", f"{cell_id} domain maximum is below minimum")

        sockets = cell["sockets"]
        child_ids = cell["children"]
        if not isinstance(sockets, list) or not isinstance(child_ids, list) or any(not isinstance(c, str) or not c for c in child_ids):
            raise EvaluationError("schema_validation_failed", f"{cell_id} sockets/children are malformed")
        direct_weights = cell.get("direct_weights", [1] * len(sockets))
        child_weights = cell.get("child_weights", [1] * len(child_ids))
        if not isinstance(direct_weights, list) or len(direct_weights) != len(sockets):
            raise EvaluationError("weight_arity_mismatch", f"{cell_id} requires one direct weight per socket")
        if not isinstance(child_weights, list) or len(child_weights) != len(child_ids):
            raise EvaluationError("weight_arity_mismatch", f"{cell_id} requires one child weight per child")
        direct_weights = [_exact_int(v, f"{cell_id}.direct_weight") for v in direct_weights]
        child_weights = [_exact_int(v, f"{cell_id}.child_weight") for v in child_weights]

        direct_values: list[int] = []
        for index, value in enumerate(sockets):
            if value is None:
                continue
            direct_values.append(_exact_int(value, f"{cell_id}.socket[{index}]"))

        active.add(cell_id)
        try:
            child_results = [evaluate(child_id, depth + 1) for child_id in child_ids]
        finally:
            active.remove(cell_id)

        even_profile = "even-payload-1" in profiles
        assertions = ["schema_version", "known_profiles", "known_operator", "status_valid", "acyclic_boundary_decode"]
        if even_profile:
            if domain.get("multiple_of") != 2:
                raise EvaluationError("even_payload_violation", f"{cell_id} even profile requires payload_domain.multiple_of = 2")
            for index, value in enumerate(sockets):
                if value is not None and value % 2:
                    raise EvaluationError("even_payload_violation", f"{cell_id}.socket[{index}] is odd")
            for child_result in child_results:
                if child_result.payload % 2:
                    raise EvaluationError("even_payload_violation", f"{cell_id} child {child_result.cell_id} decoded payload is odd")
            assertions.append("even_inputs_and_children")

        direct_total = sum(weight * value for weight, value in zip(direct_weights, sockets) if value is not None)
        child_total = sum(weight * result.payload for weight, result in zip(child_weights, child_results))
        if cell["operator"] == "global-scaled-weighted-sum":
            payload = coefficient * (direct_total + child_total)
        else:
            payload = direct_total + coefficient * child_total

        if payload < minimum or (maximum is not None and payload > maximum):
            raise EvaluationError("domain_violation", f"{cell_id} output {payload} is outside the declared domain")
        if even_profile and payload % 2:
            raise EvaluationError("even_payload_violation", f"{cell_id} output is odd")
        if even_profile:
            assertions.append("even_output")
        codeword = encode_baseline(payload, baseline)
        if "payload" in cell and _exact_int(cell["payload"], f"{cell_id}.payload") != payload:
            raise EvaluationError("derived_value_mismatch", f"{cell_id} stored payload does not match evaluation")
        if "codeword" in cell and _exact_int(cell["codeword"], f"{cell_id}.codeword") != codeword:
            raise EvaluationError("derived_value_mismatch", f"{cell_id} stored codeword does not equal payload + baseline")
        assertions.extend(["payload_domain", "derived_payload", "derived_codeword"])
        result = CellResult(cell_id, payload, codeword, baseline, tuple(assertions))
        memo[cell_id] = result
        return result

    root = evaluate(root_id, 1)
    return {
        "schema_version": "positive_baseline_result/v1",
        "root_cell_id": root.cell_id,
        "payload": root.payload,
        "codeword": root.codeword,
        "baseline": root.baseline,
        "status": "VALID",
        "input_shake256_512": _shake256_512_json(package),
        "evaluator_version": EVALUATOR_VERSION,
        "assertion_log": list(root.assertion_log),
        "child_result_count": max(0, len(memo) - 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args(argv)
    try:
        package = json.loads(args.package.read_text(encoding="utf-8"))
        print(json.dumps(evaluate_graph(package), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, EvaluationError) as error:
        code = error.code if isinstance(error, EvaluationError) else "input_error"
        print(json.dumps({"status": "INVALID", "error_code": code, "message": str(error)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
