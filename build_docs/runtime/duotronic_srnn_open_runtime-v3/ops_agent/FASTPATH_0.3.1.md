# Xavi Ops MCP fast path 0.3.1

This package removes blocking bookkeeping from the MCP request critical path while preserving fail-closed mutation coordination.

Key changes:
- FastAPI MCP and host Ops POST handlers are synchronous functions so FastAPI runs blocking OS/network work in its worker pool rather than blocking Uvicorn's event loop.
- Runtime `tools/list` uses a persisted stale-while-revalidate cache. Stale schemas are returned immediately and refreshed in the background.
- Ledger capture is queued and sanitized/written by a daemon worker. A full queue drops telemetry rather than blocking an operational request.
- Collaboration awareness is throttled, refreshed in background workers, and returned as a compact cached summary.
- Coordination event recording is asynchronous; mutation preflight remains synchronous/fail-closed and coordination finish remains synchronous with a bounded timeout.
- `run_fixed`, host Ops `run_cmd`, and synchronous bounded helpers use disk-backed temporary output with a hard response cap instead of unbounded `capture_output=True`.
- `host_status` is a 3-second cached lightweight snapshot (`podman ps`, `ss -H -ltn`, `df`) with 5-second fail-soft component deadlines.
- Runtime health probes use actual curl deadlines rather than potentially holding the Ops event loop for a minute.

Not included intentionally:
- No generic raw shell was enabled.
- No blanket passwordless sudo or root execution was added.
- No negative niceness was forced.
- No persistent interactive shell was added (avoids cross-request cwd/env/state leaks).

Long operations should use `bounded_job_start` and be polled with `bounded_job_status` / `bounded_job_output`.
