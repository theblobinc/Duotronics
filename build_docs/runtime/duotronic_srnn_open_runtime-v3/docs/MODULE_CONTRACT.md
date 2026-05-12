# Module Contract

Every module should declare:

```json
{
  "id": "ollama.local",
  "kind": "model_provider",
  "profile": "models",
  "endpoint": "http://ollama:11434",
  "capabilities": ["text_generation", "embeddings"],
  "evidence_outputs": ["ModelOutputWitness", "EmbeddingWitness"],
  "enabled": false
}
```

Every module invocation should produce a witness containing:

- module id and version/image digest when available
- input digest
- output digest
- status
- runtime/corpus reference
- declared force (`observe`, `propose`, `verify`, `prove`, `generate`, `refuse`)
- non-collapse notes

A module cannot promote its own output to truth, theorem, or production authority.
