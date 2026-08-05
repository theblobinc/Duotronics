#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "executable/runtime/positive_baseline.py"
SPEC = importlib.util.spec_from_file_location("positive_baseline", MODULE_PATH)
pb = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = pb
SPEC.loader.exec_module(pb)


def cell(cell_id, sockets, children=(), baseline=1, payload=None, codeword=None):
    value = {
        "schema_version": "positive_baseline_cell/v1",
        "cell_id": cell_id,
        "cell_type": "hex-cell",
        "profiles": ["core-acyclic-1.2", "positive-baseline-1", "even-payload-1"],
        "payload_domain": {"kind": "integer", "minimum": 0, "multiple_of": 2},
        "operator": "global-scaled-weighted-sum",
        "coefficient": 1,
        "baseline": baseline,
        "sockets": list(sockets),
        "children": list(children),
        "status": "VALID",
        "numeric_policy": {"overflow": "reject", "max_nodes": 100, "max_depth": 20}
    }
    if payload is not None:
        value["payload"] = payload
    if codeword is not None:
        value["codeword"] = codeword
    return value


class PositiveBaselineTests(unittest.TestCase):
    def test_bijective_roundtrip(self):
        alphabet = list("123456789A")
        expected = {1: "1", 10: "A", 11: "11", 20: "1A", 42: "42", 100: "9A", 101: "A1"}
        for number, numeral in expected.items():
            encoded = pb.bijective_encode(number, alphabet)
            self.assertEqual("".join(encoded), numeral)
            self.assertEqual(pb.bijective_decode(encoded, alphabet), number)

    def test_child_baseline_removed_at_parent_boundary(self):
        child = cell("child", [8, 4, 8, 4, 10, 8], payload=42, codeword=43)
        parent = cell("parent", [6, 14, 22, 30], ["child"], payload=114, codeword=115)
        result = pb.evaluate_graph({"root_cell_id": "parent", "cells": [parent, child]})
        self.assertEqual((result["payload"], result["codeword"]), (114, 115))
        self.assertNotEqual(result["codeword"], 116)

    def test_mixed_child_baseline_is_decoded(self):
        child = cell("child", [8, 4, 8, 4, 10, 8], baseline=7, payload=42, codeword=49)
        parent = cell("parent", [6, 14, 22, 30], ["child"], payload=114, codeword=115)
        result = pb.evaluate_graph({"root_cell_id": "parent", "cells": [parent, child]})
        self.assertEqual(result["payload"], 114)

    def test_absent_socket_is_not_zero_sentinel(self):
        record = cell("root", [None, 0, 4], payload=4, codeword=5)
        result = pb.evaluate_graph({"root_cell_id": "root", "cells": [record]})
        self.assertEqual(result["payload"], 4)

    def test_odd_input_rejected_at_boundary(self):
        record = cell("root", [2, 3])
        with self.assertRaisesRegex(pb.EvaluationError, r"socket\[1\] is odd"):
            pb.evaluate_graph({"root_cell_id": "root", "cells": [record]})

    def test_cycle_rejected(self):
        first = cell("a", [], ["b"])
        second = cell("b", [], ["a"])
        with self.assertRaisesRegex(pb.EvaluationError, "cycle"):
            pb.evaluate_graph({"root_cell_id": "a", "cells": [first, second]})

    def test_derived_codeword_mismatch_rejected(self):
        record = cell("root", [4], payload=4, codeword=4)
        with self.assertRaisesRegex(pb.EvaluationError, "stored codeword"):
            pb.evaluate_graph({"root_cell_id": "root", "cells": [record]})

    def test_unknown_operator_rejected(self):
        record = cell("root", [4])
        record["operator"] = "implicit-add"
        with self.assertRaisesRegex(pb.EvaluationError, "unknown operator"):
            pb.evaluate_graph({"root_cell_id": "root", "cells": [record]})


if __name__ == "__main__":
    unittest.main()
