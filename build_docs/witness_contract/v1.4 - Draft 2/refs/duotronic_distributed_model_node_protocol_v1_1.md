# Duotronic Distributed Model Node Protocol v1.1

**Status:** Source-spec baseline candidate  
**Version:** distributed-model-node-protocol@v1.1  
**Supersedes:** distributed-model-node-protocol@v1.0  
**Document kind:** Normative distributed witness and model-node protocol plus reference topologies  
**Primary purpose:** Define how distributed machine nodes, multiple machine-learning models, local evidence stores, search adapters, and Duotronic runtime components coordinate without allowing raw model output to bypass witness validation, canonicalization, replay, or policy shielding.

---

## 1. Scope

This protocol applies to Duotronic deployments that run across more than one model, process, host, GPU worker, server, cluster, region, or organization-local machine.

A node may:

1. ingest source data;
2. call local models;
3. call remote models;
4. run search adapters;
5. decode media;
6. emit evidence bundles;
7. emit model witnesses;
8. propose candidate witnesses;
9. propose profile candidates;
10. run local replay;
11. participate in cross-node adjudication.

A node may not unilaterally promote a learned profile into global authority.

---

## 2. Node classes

| Node class | Role |
|---|---|
| intake node | collects raw evidence and creates evidence bundles |
| model node | runs inference and emits model witnesses |
| parser node | performs decoding, OCR, ASR, tokenization, or structural parsing |
| search node | retrieves and wraps search/social evidence |
| profile node | synthesizes profile candidates |
| falsifier node | searches for counterexamples and contradictions |
| replay node | reruns fixture and replay tests |
| registry node | stages profile records and schema entries |
| policy node | applies L5 policy and promotion rules |
| coordinator node | organizes cross-node adjudication without becoming semantic authority |

Nodes may be combined in one deployment, but the record types must remain separate.

---

## 3. Node witness event

```yaml
NodeWitnessEvent:
  node_event_id: string
  node_id: string
  node_role: intake | model | parser | search | profile | falsifier | replay | registry | policy | coordinator
  software_version: string
  runtime_environment_hash: string | null
  input_refs: []
  output_refs: []
  event_time: string
  deterministic: true | false
  replay_ref: string | null
  local_policy_mode: normal | degraded | audit_only | bypass | blocked
  signature_or_integrity_tag: string | null
```

Every node output that can influence witnesses, profiles, lookup memory, recurrent state, or policy must be traceable to a `NodeWitnessEvent`.

---

## 4. Model execution record

```yaml
ModelExecutionRecord:
  execution_id: string
  node_id: string
  model_id: string
  model_version: string
  model_family: llm | vision | audio | embedding | classifier | parser | search_ranker | custom
  input_evidence_ids: []
  prompt_or_task_profile_id: string | null
  inference_settings_hash: string
  output_hash: string
  output_storage_ref: string
  safety_filters_applied: []
  known_failure_modes: []
  calibration_profile_id: string | null
  replay_allowed: true | false
```

The execution record is not the same as a model witness. A model witness is the structured claim extracted from the execution output.

---

## 5. Local node policy

Every node must apply a local policy clamp before emitting outputs.

Minimum local checks:

1. source integrity available;
2. payload hash available;
3. model version available;
4. inference settings hash available;
5. output hash available;
6. privacy class respected;
7. no restricted data sent to unauthorized models;
8. local policy mode recorded;
9. failed decode recorded as failed decode, not empty content;
10. missing result recorded as missing, not zero.

---

## 6. Cluster adjudication

Cluster adjudication compares multiple node outputs.

It must track:

1. same evidence processed by different models;
2. same model run on different nodes;
3. same source retrieved by different connectors;
4. same claim extracted from different platforms;
5. same profile candidate generated from different corpora;
6. same bridge tested with different fixture packs;
7. contradictions and unresolved ambiguities.

A coordinator node may compute adjudication scores. It may not promote a profile without L5 approval.

---

## 7. Distributed profile learning

A distributed profile learning run has this shape:

```text
intake nodes collect evidence
-> model nodes emit model witnesses
-> parser nodes emit segmentation candidates
-> profile nodes synthesize candidate profiles
-> falsifier nodes generate counterexamples
-> replay nodes test fixtures
-> coordinator node writes adjudication record
-> registry node stages candidate
-> policy node approves sandbox, rejects, or requests more evidence
```

All steps must be replayable or explicitly marked as non-replayable evidence with reduced authority.

---

## 8. Conflict handling

Conflict types:

| Conflict | Meaning | Default action |
|---|---|---|
| model disagreement | models propose incompatible outputs | preserve uncertainty or audit-only |
| source conflict | sources contradict each other | create contradiction witness |
| profile conflict | new profile overlaps existing profile | require equivalence or migration plan |
| normalizer conflict | normalizer output unstable | reject or degrade |
| bridge conflict | bridge fails preservation | reject bridge |
| policy conflict | local and global policy disagree | stricter policy wins |
| replay conflict | replay cannot reproduce output | block promotion |

---

## 9. Gating ML models with Duotronic witnesses

A Duotronic witness may gate an ML model only if the witness has a policy-approved runtime mode.

Allowed gate types:

1. input routing gate;
2. model selection gate;
3. prompt/task profile gate;
4. memory retrieval gate;
5. tool access gate;
6. search expansion gate;
7. output confidence gate;
8. profile-learning gate;
9. safety review gate.

Disallowed without explicit L5 approval:

1. raw evidence directly selecting authoritative model state;
2. uncanonicalized profile candidate controlling memory writes;
3. social trend signal directly promoting a claim;
4. search rank directly overriding canonical evidence;
5. model confidence directly bypassing policy.

---

## 10. Node failure states

```text
node_unavailable
node_timeout
model_unavailable
model_version_mismatch
inference_settings_missing
output_hash_missing
privacy_policy_block
source_connector_failed
decode_failed
local_policy_bypass
global_policy_veto
replay_unavailable
```

Node failures must be explicit and must not be silently converted into absence or zero.

---

## 11. Security and governance

At minimum, distributed nodes must preserve:

1. source provenance;
2. privacy class;
3. access boundary;
4. payload hash;
5. model version;
6. node identity;
7. replay record;
8. policy decision;
9. migration impact where relevant;
10. rollback path for promoted profiles.

---

## 12. Non-claims

This protocol does not prescribe a specific networking stack, queue system, model serving framework, or database. It defines the witness and authority boundaries that such systems must preserve.


---

## 13. Non-deterministic node policy

> **Status tag:** normative

A node event marked `deterministic: false` has restricted authority.

Outputs from non-deterministic node events must not be used for:

1. replay-dependent profile promotion;
2. authoritative state updates requiring replay identity;
3. normal Family Registry promotion;
4. migration sentinel results;
5. irreversible policy decisions;
6. model-gating paths that require reproducible evidence.

They may be used for:

1. audit-only evidence;
2. sandbox experiments;
3. candidate witness generation;
4. candidate profile generation;
5. heuristic search expansion;
6. fixture discovery;
7. contradiction discovery.

A non-deterministic output may support higher authority only if it is independently reproduced by deterministic replay or by a policy-approved equivalence replay profile.

### 13.1 Required fields for non-deterministic output

```yaml
NonDeterminismRecord:
  node_event_id: string
  non_determinism_sources:
    - sampling
    - model_temperature
    - gpu_kernel
    - race_condition
    - external_api_variation
    - unknown
  replay_equivalence_profile: string | null
  allowed_use: audit_only | sandbox
  promotion_blocker: true
```
