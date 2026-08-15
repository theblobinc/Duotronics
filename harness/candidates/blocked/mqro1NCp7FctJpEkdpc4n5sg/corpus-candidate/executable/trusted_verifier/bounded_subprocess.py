#!/usr/bin/env python3
"""Small dependency-free bounded subprocess runner for verifier containers."""

from __future__ import annotations

import hashlib
import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Result:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    output_limit_exceeded: bool
    stdout_shake256_512: str
    stderr_shake256_512: str


def run_bounded(
    command: list[str], *, cwd: str | Path | None, env: dict[str, str], timeout: float,
    stdout_limit: int = 1024 * 1024, stderr_limit: int = 1024 * 1024,
    combined_limit: int = 2 * 1024 * 1024,
) -> Result:
    process = subprocess.Popen(
        command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True,
    )
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    digests = {"stdout": hashlib.shake_256(), "stderr": hashlib.shake_256()}
    limits = {"stdout": stdout_limit, "stderr": stderr_limit}
    total = 0; timed_out = False; exceeded = False
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True; break
            events = selector.select(min(0.1, remaining))
            if not events and process.poll() is not None:
                break
            for key, _ in events:
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj); continue
                stream = key.data; digests[stream].update(chunk); total += len(chunk)
                allowed = limits[stream] - len(buffers[stream])
                if allowed > 0:
                    buffers[stream].extend(chunk[:allowed])
                if len(chunk) > allowed or total > combined_limit:
                    exceeded = True; break
            if exceeded:
                break
        if timed_out or exceeded:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)
    finally:
        selector.close(); process.stdout.close(); process.stderr.close()
    return Result(
        process.returncode, buffers["stdout"].decode("utf-8", "replace"),
        buffers["stderr"].decode("utf-8", "replace"), timed_out, exceeded,
        digests["stdout"].hexdigest(64), digests["stderr"].hexdigest(64),
    )

