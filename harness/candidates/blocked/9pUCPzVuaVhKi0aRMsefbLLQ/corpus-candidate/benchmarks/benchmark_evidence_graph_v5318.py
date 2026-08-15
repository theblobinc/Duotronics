#!/usr/bin/env python3
"""Deterministic microbenchmark for 5.3.18 evidence calculations.

It reports measurements; it does not establish acceptance budgets.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "validation"))
sys.path.insert(0, str(ROOT / "executable" / "runtime"))
from identity import canonical_bytes, duoid  # noqa: E402
from evidence_graph_v5318 import graph_snapshot_root  # noqa: E402


def sample(index: int) -> dict[str, object]:
    return {
        "schema_version": "benchmark_evidence/v1",
        "ordinal": index + 1,
        "gate_id": f"gate-{index % 12 + 1:02d}",
        "authority_namespace": "duotronic://authority/sandbox/witness-harness-vm",
        "stable_projection": {"ok": True, "checks": [1, 2, 3, 4]},
    }


def calculate(index: int) -> str:
    value = sample(index)
    return duoid("DUOTRONIC/BENCHMARK-EVIDENCE/v1", canonical_bytes(value))


def run_once(count: int, workers: int) -> dict[str, object]:
    started = time.perf_counter_ns()
    if workers == 1:
        identifiers = [calculate(index) for index in range(count)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            identifiers = list(pool.map(calculate, range(count)))
    identifiers_ns = time.perf_counter_ns() - started
    started = time.perf_counter_ns()
    root = graph_snapshot_root(
        identifiers,
        "duotronic://authority/sandbox/witness-harness-vm",
        identifiers[0],
    )
    graph_ns = time.perf_counter_ns() - started
    return {
        "count": count,
        "workers": workers,
        "identifier_total_ns": identifiers_ns,
        "identifier_per_object_ns": identifiers_ns // count,
        "graph_root_ns": graph_ns,
        "graph_root_id": root,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", default="1,12,100,1000")
    parser.add_argument("--workers", default="1,2,4,6")
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()
    rows = []
    for count in [int(v) for v in args.counts.split(",")]:
        for workers in [int(v) for v in args.workers.split(",")]:
            runs = [run_once(count, workers) for _ in range(args.rounds)]
            rows.append({
                "count": count,
                "workers": workers,
                "rounds": args.rounds,
                "identifier_total_ns_median": int(statistics.median(r["identifier_total_ns"] for r in runs)),
                "identifier_per_object_ns_median": int(statistics.median(r["identifier_per_object_ns"] for r in runs)),
                "graph_root_ns_median": int(statistics.median(r["graph_root_ns"] for r in runs)),
                "graph_root_id": runs[0]["graph_root_id"],
                "root_deterministic": len({r["graph_root_id"] for r in runs}) == 1,
            })
    print(json.dumps({
        "schema_version": "evidence_graph_benchmark/v1",
        "contract_version": "v1.6-draft-5.3.18",
        "non_authoritative_measurement": True,
        "rows": rows,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
