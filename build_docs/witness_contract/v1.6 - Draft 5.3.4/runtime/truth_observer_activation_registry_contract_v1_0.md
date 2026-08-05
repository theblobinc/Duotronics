# Truth Observer Activation Registry Runtime Contract v1.0

Status: active Draft 5.1 runtime contract.

## Purpose

The runtime must maintain a registry of AI models and tools that act as truth
observers for WG-RNN.

## Registry record

```yaml
TruthObserverRegistryRecord:
  observer_id: string
  display_name: string
  model_id: string
  backend: string
  endpoint_ref: string | null
  capability_digest: sha256
  activation_profile_ref: string
  evidence_authority_class: E0 | E1 | E2 | E3 | E4 | E5
  nla_adapter_refs: list
  status: disabled | shadow | audit | active | deprecated
  registered_at: timestamp
  updated_at: timestamp
```

## Runtime obligations

1. Return observer capability status.
2. Fail closed for unavailable activation capture.
3. Record backend capability changes.
4. Bind every NLA witness to an observer id.
5. Bind every training example to an activation space id.
6. Preserve historical profiles for replay.
