# MCP Runtime Observation Log 2026-04-30 Draft 3

**Status:** Research specification draft  
**Version:** mcp-runtime-observation@2026-04-30-draft-3  
**Document kind:** Runtime observation log  
**Primary purpose:** Record live MCP observations used for v1.6 Draft 3 corpus updates.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Observation summary

Live MCP observations showed a 127-tool server named `xavi-agent-lab` with groups for Xavi, repo, ops, browser, and meta tools. Capability reporting showed DNS rebinding protection, allowed host/origin lists, configured auth keys, Docker availability, and a configured base directory under `/var/www/xavi/srnn_server`.

## 2. Self-test summary

The MCP self-test reported success with zero errors. Observed checks included principal scopes, path availability, git head/status, Docker containers, compose configuration, database checks, fallback API manager/tier0 stats, and Playwright import.

## 3. Runtime caveats

The current `cognition_loops` call returned an error indicating a missing `step` column in one path. Draft 3 therefore reinforces the rule that snapshot step must be derived from JSON state where needed and not assumed as a physical column.

## 4. Minecraft mode

Minecraft mode was observed as disabled, while the bridge path existed and the hint instructed enabling `MINECRAFT_MODE=http_bridge` or `local_sidecar`. Minecraft action tools therefore remain verified as manifest/policy capabilities but not necessarily active runtime side effects.

## 5. Policy examples

Observed policy behavior included:

- `minecraft_ingest_multimodal_witness`: `db_write`, requires `mcp:write`, no approval required.
- `minecraft_collect_blocks`: `external_action`, requires `mcp:minecraft-action`, approval required.

## 6. Draft 3 impact

The corpus now requires every MCP observation used for runtime decisions to be wrapped as an observation witness with tool name, observed result, principal scope, runtime mode, and policy metadata.
