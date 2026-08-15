# Xavi Developer Ops MCP fast path 0.3.3

## Development mode

The Developer/Ops MCP is intentionally privileged during active development. `XAVI_DEV_MCP_UNRESTRICTED` defaults to enabled (`1`). In this mode, coordination remains available for peer awareness, task context, events, and WG-RNN learning, but coordination leases/conflicts do not veto Ops mutations.

The privileged network boundary remains authenticated with `XAVI_OPS_API_KEY`. Unrestricted development mode bypasses internal coordination/security gates; it does not make the host-mutation endpoint public.

## Fast path

- Runtime MCP schemas use an in-memory stale-while-revalidate cache plus `data/cache/runtime_mcp_tools.json` as the persisted cold-start cache.
- Ledger, collaboration-awareness, and coordination-event bookkeeping use bounded background queues instead of the request critical path.
- Host status has a 3-second TTL cache.
- Fixed subprocess execution captures stdout/stderr through bounded temporary files.
- Runtime health and model inventory use short local HTTP deadlines.

## Runtime liveness

`/health` is a lightweight async liveness route. It returns startup snapshot metadata and model/module counts rather than full registries. Full model inventory is exposed separately at `/v1/models/registry`; expensive diagnostics remain under `/health/deep`.

Native `/mcp` and the compatibility MCP call surface isolate mixed synchronous DB/WG-RNN/autonomy work from Uvicorn's main event loop using worker-thread event loops. Operational `runtime.health`, `runtime.models`, and `runtime.modules` probes do not create training trajectories or collaboration-awareness queries.

## Runtime lifecycle

Runtime lifecycle ownership is separated from MCP adapter services. `xavi-duotronic-runtime.service` launches the rootless Podman runtime so conmon/rootlessport live in the runtime service cgroup rather than an adapter cgroup. Developer Ops runtime restart calls use:

`systemctl --user restart xavi-duotronic-runtime.service`

This prevents an MCP adapter reload from terminating runtime process supervision or port forwarding.

## Verification

Run:

```bash
.venv/bin/python tests/test_fastpath_smoke_standalone.py
.venv/bin/python -m pytest -q tests/test_ops_mcp_contracts.py
```

The standalone smoke suite also performs an authenticated live `tools/list` probe when the local adapter and Ops key are available.
