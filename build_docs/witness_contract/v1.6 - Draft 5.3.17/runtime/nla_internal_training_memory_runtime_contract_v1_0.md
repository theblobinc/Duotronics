# NLA Internal Training Memory Runtime Contract v1.0

Status: active Draft 5.1 runtime contract.

## Purpose

This contract defines persistence for WG-RNN NLA training memory cells.

## Required tables or equivalent stores

```sql
srnn_nla_training_examples
srnn_nla_failure_examples
srnn_nla_curriculum_manifests
srnn_nla_training_runs
srnn_nla_model_lineage
srnn_nla_eval_results
```

## Runtime rules

1. Raw activation vectors are artifact refs, not inline DB blobs by default.
2. Every example must carry privacy class and retention class.
3. Curriculum promotion must be append-only.
4. Failure examples must be preserved for regression testing.
5. Heldout examples must not be used for training.
6. Expired examples must not enter new training runs.
7. Training runs must store source manifest hashes.
