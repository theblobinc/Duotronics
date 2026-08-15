# Docker Compose Federated Stack Observation - 2026-05-08

Status: source observation.
Generated: 2026-05-08

## Observed stack shape

The SRNN compose file describes a unified federated node stack. Node-specific
behavior is controlled through compose profiles and env files.

Observed profile categories include:

- core storage;
- Ollama and Ollama GPU;
- Redis;
- SearXNG;
- Hovod and Hovod workers;
- SRNN and SRNN GPU;
- GPU worker;
- Ollama proxy and remote proxy;
- LibreChat;
- Agent Lab;
- video-dl;
- Stable Diffusion stubs/full backends;
- WG-RNN per-node recurrent cognition loop.

## Draft 4 contract impact

Draft 4 treats compose profile selection as a source of node-role evidence. The
same compose file can describe multiple roles, so conformance must bind node
identity, profile set, and runtime health together.
