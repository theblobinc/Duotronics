# Duotronic Runtime Recurrence Complete Integration Document

**Status:** Research specification draft  
**Version:** runtime-recurrence-integration@v1.0  
**Document kind:** Complete integration document  
**Primary purpose:** Provide a single end-to-end Draft 3 explanation of temporal recurrence, WG-RNN memory, cognition governance, and MCP runtime integration.  
**Draft:** v1.6 Draft 3  
**Generated:** 2026-04-30T17:40:00Z

---

## 1. Governing idea

The runtime must not treat time, absence, memory decay, or cognition adaptation as private implementation details. In v1.6 Draft 3 each of these is a witness-bearing event that can be replayed, audited, and policy-gated.

The implementation path is:

```text
raw event or expected tick
-> TemporalWitness or AbsenceWitness
-> L1 candidate witness
-> L2/WG-RNN MemoryUpdateRecord
-> L2M slot update or lookup
-> gate values and policy clamps
-> optional L3 MetaDiagnostics
-> optional L4 proposal
-> optional L5 policy decision
-> replay package record
```

## 2. Temporal recurrence contract

Every recurrent tick must have one of:

1. a positive observation witness;
2. an explicit absence witness;
3. a policy-block witness;
4. a transport-failure witness;
5. a replay-only synthetic tick witness.

Silent gaps are prohibited in normal runtime mode. If the runtime cannot emit a full witness during failure, it must emit a degraded gap witness as soon as control returns.

## 3. L2 and L2M split

L2 is short-horizon continuity. L2M is associative memory. The two layers must not share an unexamined decay curve.

Reference cadence:

| Layer | Reference cadence | State kind |
|---|---:|---|
| L2 | 100-500 ms | continuity, recent gates, recurrent state |
| L2M | 5-30 s | stable associative slots and lookup facts |
| L3 | 100-1000 accepted witnesses | bounded meta-parameter proposal |
| L4 | maintenance window or policy event | architecture/profile proposal |
| L5 | continuous policy shield | veto, approval, clamp, review |

## 4. Gate and decay lifecycle

A memory slot lifecycle is:

```text
candidate_write
-> active_slot
-> stable_slot or quarantine_slot
-> promotion_request or decay_request
-> policy gate
-> retained, decayed, merged, split, demoted, purged, or tombstoned
```

Every lifecycle edge must have a witness record.

## 5. Cognition constraints

L3 improves cognition by reducing unbounded adaptation, not by adding unreviewed intelligence. L3 may propose parameter updates but must remain inside policy clamps. L4 owns structural proposals. L5 owns promotion, veto, rollback, and review escalation.

## 6. MCP integration

The MCP server is a runtime observation and action interface. Draft 3 treats it as a witness source. Tool manifest snapshots, policy explanations, self-tests, capability reports, git status, service catalogs, audit logs, and selected cognition queries may become `MCPRuntimeObservationWitness` records.

Current verified MCP meta-tools include:

```text
mcp_tool_manifest
mcp_capability_report
mcp_self_test
policy_explain
```

Target recurrence tools such as `write_witness`, `propose_decay`, and `query_slot_lifecycle_stats` remain backlog items until implemented and verified.

## 7. Current SRNN implementation alignment

The current SRNN implementation already moved toward Draft 3 through identity-oracle auto-registration, live recurrent witness overlays, stale evidence tests, root-bounded mutation tools, and stdio principal policy. Draft 3 documents these as implementation inputs but does not make any particular code file normative.

## 8. Required observability metrics

Implementations should report:

- silent gap ratio;
- explicit absence count;
- write/promotion/quarantine/decay counts;
- quarantine age distribution;
- promotion latency;
- replay divergence;
- gate clamp frequency;
- L3 delta distribution;
- L4 proposal acceptance/rejection;
- L5 veto and review count.

## Draft 4 carry-forward update - 2026-05-08

This document is retained in the v1.6 Draft 4 corpus as part of the full Draft 3
carry-forward. Draft 4 adds newer SRNN Server runtime observations rather than
removing this baseline. For current Draft 4 interpretation, read:

- `README_v1_6_draft_4.md`
- `duotronic_draft4_srnn_source_refresh_2026_05_08.md`
- `duotronic_srnn_federated_runtime_stack_profile_v1_0.md`
- `duotronic_srnn_gpu_worker_llama_server_runtime_profile_v1_0.md`
- `runtime/llama_server_runtime_readiness_contract_v1_0.md`

Draft 4 updates the runtime boundary with the current SRNN compose stack,
per-node `wg-rnn` service, GPU-worker llama-server large-model path, runtime
model manifest/smoke/bench endpoints, memlock diagnostics, and Agent Lab/MCP
backup-log witness handling. This update does not claim live production
certification; it records the source-observed contract and follow-up validation
requirements.
