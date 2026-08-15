# Witness Runtime Benchmark Plan v1.0

Status: required RC benchmark plan.

## Metrics

| Metric | Target |
|---|---:|
| witness envelope creation p50 | <= 25 ms |
| witness envelope creation p95 | <= 100 ms |
| request signature verify p95 | <= 50 ms |
| response signature generate p95 | <= 50 ms |
| memory update record write p95 | <= 100 ms |
| live overlay query p95 | <= 250 ms |
| replay package manifest hash p95 | <= 500 ms for small package |
| Firehose UI event render p95 | <= 100 ms client-side |

## Benchmark witness

```yaml
BenchmarkWitness:
  benchmark_id: string
  commit: string
  environment: string
  dataset_ref: string
  metric: string
  p50_ms: number
  p95_ms: number
  p99_ms: number
  sample_count: integer
  passed: boolean
```

