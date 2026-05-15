# Corpus alignment

This runtime is aligned with these corpus ideas:

- witness before assertion
- WG-RNN memory lifecycle: candidate write, quarantine, promote, no-op
- NLA as L2n diagnostic evidence, not policy authority
- separation of model output, semantic validity, proof, policy, and memory
- replay identity refs on memory updates
- audit events for important transitions
- MCP/tool surface for agent operation

## NLA data flow

```text
WG-RNN or model execution event
  -> activation capture
  -> activation vector digest
  -> AV explanation
  -> AR reconstruction and fidelity score
  -> NaturalLanguageActivationWitness
  -> Base evidence object
  -> optional memory/write/promotion only after gates
```

The default `.env.example` keeps NLA audit-only. This intentionally demonstrates non-collapse: a good explanation does not automatically write memory.

## Corpus-built runtime behavior

The `corpus_agent.py` module scans mounted markdown files, extracts headings and summaries, persists them to PostgreSQL, and emits an implementation build plan. This is not a magical proof of conformance; it is a safe agentic scaffold generator that can help a repo agent decide which runtime capabilities to wire next.
