# NLA Memory Cell Implementation Requirements v1.0

Status: active Draft 5.1 implementation requirement.

Draft 5.1 requires internal NLA memory cells to separate raw capture, candidate
explanations, reconstruction metrics, curated curriculum, failure examples, and
model lineage.

```yaml
required_cells:
  nla_raw_capture_cell: activation refs, hashes, model/layer/token metadata
  nla_candidate_explanation_cell: AV outputs, teacher notes, parser state
  nla_reconstruction_cell: AR metrics, cosine, MSE, stability
  nla_curriculum_cell: accepted training pairs and heldout examples
  nla_failure_cell: rejected, confabulated, unsupported, or low-fidelity examples
  nla_model_lineage_cell: adapter versions, eval scores, rollback refs
```

Raw vectors must remain artifact referenced and retention bounded. No memory cell
may directly write user memory or policy authority.
