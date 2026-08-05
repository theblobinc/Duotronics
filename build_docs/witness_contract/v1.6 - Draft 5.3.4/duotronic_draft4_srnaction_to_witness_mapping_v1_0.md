# Draft 4 SRNN Action to Witness Mapping v1.0

Status: Draft 4 mapping profile.
Generated: 2026-05-08

## Purpose

This mapping links newer SRNN runtime actions to Duotronic witness records.

| SRNN action | Witness record | Required evidence |
|---|---|---|
| Compose service configured | RuntimeServiceWitness | profile, node, config digest |
| WG-RNN loop started | RecurrentRuntimeWitness | node id, loop count, backends |
| Ollama proxy routed model | ModelDelegationWitness | backend URL, model inventory |
| GPU worker model manifest read | RuntimeModelObservation | model key, path, exists, size |
| Llama-server command built | LlamaServerRuntimeWitness | effective command |
| Llama-server health ready | RuntimeReadinessWitness | probe URL, status, logs |
| Smoke completion | ModelSmokeWitness | prompt digest, latency, output digest |
| Benchmark run | ModelBenchmarkWitness | ttft, decode rate, tokens, config |
| Auto mutation backup | AgentLabBackupWitness | backup id, file count, archive size |
| Failed runtime start | RuntimeFailureWitness | error, command, log tail, cleanup |

## Boundary rule

No action becomes authoritative by being logged. Authority requires the action,
its witness record, policy status, and conformance status to agree.
