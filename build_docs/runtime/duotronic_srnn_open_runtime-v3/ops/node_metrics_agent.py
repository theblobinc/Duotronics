#!/usr/bin/env python3
"""Read-only Xavi backend-LAN host telemetry agent.

This service intentionally exposes only bounded machine-pressure observations.
It has no mutation, shell, file-read, process-control, or public-discovery API.
Bind it to the dedicated Xavi backend LAN address, never 0.0.0.0.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

SCHEMA_VERSION = "xavi-node-metrics-v1"


def _read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as handle:
            for line in handle:
                key, _, raw = line.partition(":")
                if not _:
                    continue
                parts = raw.strip().split()
                if not parts:
                    continue
                try:
                    value = int(parts[0])
                except ValueError:
                    continue
                if len(parts) > 1 and parts[1].lower() == "kb":
                    value *= 1024
                values[key] = value
    except OSError:
        pass
    return values


def _read_uptime() -> float | None:
    try:
        return round(float(open("/proc/uptime", "r", encoding="utf-8").read().split()[0]), 2)
    except (OSError, ValueError, IndexError):
        return None


def _gpu_metrics() -> list[dict[str, Any]]:
    query = (
        "name,memory.total,memory.free,memory.used,utilization.gpu,"
        "utilization.memory,temperature.gpu,power.draw"
    )
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                f"--query-gpu={query}",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if proc.returncode != 0:
        return []

    rows: list[dict[str, Any]] = []
    for index, line in enumerate(proc.stdout.splitlines()):
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 8:
            continue

        def number(value: str) -> float | None:
            if value in {"", "N/A", "[Not Supported]"}:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        rows.append(
            {
                "index": index,
                "name": parts[0],
                "memory_total_mib": number(parts[1]),
                "memory_free_mib": number(parts[2]),
                "memory_used_mib": number(parts[3]),
                "utilization_gpu_percent": number(parts[4]),
                "utilization_memory_percent": number(parts[5]),
                "temperature_c": number(parts[6]),
                "power_draw_w": number(parts[7]),
            }
        )
    return rows


def collect_metrics(node_id: str) -> dict[str, Any]:
    logical = int(os.cpu_count() or 0)
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        load1 = load5 = load15 = 0.0
    mem = _read_meminfo()
    total = int(mem.get("MemTotal", 0))
    available = int(mem.get("MemAvailable", mem.get("MemFree", 0)))
    used = max(total - available, 0) if total else 0
    return {
        "schema_version": SCHEMA_VERSION,
        "observer": "xavi-node-metrics.local",
        "offline_only": True,
        "read_only": True,
        "node_id": str(node_id),
        "hostname": socket.gethostname(),
        "observed_at_ms": int(time.time() * 1000),
        "uptime_seconds": _read_uptime(),
        "cpu": {
            "logical_threads": logical,
            "load1": round(float(load1), 3),
            "load5": round(float(load5), 3),
            "load15": round(float(load15), 3),
            "load1_per_thread": round(float(load1) / logical, 5) if logical else None,
        },
        "memory": {
            "total_bytes": total,
            "available_bytes": available,
            "used_bytes": used,
            "used_ratio": round(used / total, 6) if total else None,
        },
        "gpus": _gpu_metrics(),
        "source": "procfs+nvidia-smi",
    }


class MetricsHandler(BaseHTTPRequestHandler):
    server_version = "XaviNodeMetrics/1"

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/health":
            self._send(
                200,
                {
                    "schema_version": SCHEMA_VERSION,
                    "ok": True,
                    "node_id": self.server.node_id,
                    "offline_only": True,
                    "read_only": True,
                },
            )
            return
        if self.path == "/v1/metrics":
            self._send(200, collect_metrics(self.server.node_id))
            return
        self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        self._send(405, {"ok": False, "error": "read_only"})

    def do_PUT(self) -> None:  # noqa: N802
        self._send(405, {"ok": False, "error": "read_only"})

    def do_DELETE(self) -> None:  # noqa: N802
        self._send(405, {"ok": False, "error": "read_only"})

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep the agent quiet; systemd records lifecycle/errors.
        return


class MetricsServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], node_id: str):
        super().__init__(address, MetricsHandler)
        self.node_id = node_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Xavi private-LAN read-only node metrics agent")
    parser.add_argument("--host", required=True, help="Dedicated private LAN address; 0.0.0.0 is refused")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--node-id", required=True)
    args = parser.parse_args()
    if args.host in {"0.0.0.0", "::", ""}:
        raise SystemExit("refusing wildcard bind; use the dedicated Xavi LAN address")
    if not (1024 <= int(args.port) <= 65535):
        raise SystemExit("port must be unprivileged and <= 65535")
    server = MetricsServer((args.host, int(args.port)), args.node_id)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
