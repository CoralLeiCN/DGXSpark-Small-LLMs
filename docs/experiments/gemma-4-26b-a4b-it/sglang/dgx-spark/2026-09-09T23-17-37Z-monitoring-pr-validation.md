# 2026-09-09T23:17:37Z — Monitoring PR validation passes with mixed stream modes

Run ID: `RUN-0011`

- Status: resolved
- Phase: inference and monitoring validation
- Related turns: [Mixed stream aggregation failure](2026-09-09T23-13-53Z-mixed-stream-monitoring.md)
- Repo revision: `c52d96f` plus this journal entry; merged `origin/main` (`c7fa5eb`)
- Host/GPU: DGX Spark, NVIDIA GB10, ARM64
- Container: `dgxspark/gemma-4-26b-a4b-it-sglang:0.1.0`
- Engine: existing SGLang `0.0.0.dev1+g5f55db35e`
- Model: `google/gemma-4-26B-A4B-it`, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`, BF16
- Monitoring: Prometheus 3.13.3, Grafana 13.2.1

## Command

```bash
INFERPACK_MONITORING_TESTS=1 uv run --python 3.12 --env-file monitoring/.env pytest monitoring/tests models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/tests/test_monitoring.py -v -s --tb=short
uv run --python 3.12 pytest --import-mode=importlib -q
docker compose -f monitoring/compose.yaml run --rm --no-deps --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml
```

## Error Or Observation

```text
API output tokens: 374; counter increase: 374; all panels passed.
2 passed in 56.33s
26 passed, 6 skipped in 0.19s
SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax
```

## Diagnosis

The earlier NaN came from dividing individual idle stream-mode histograms while
another mode was active. The exported data itself was valid. Combining sums and
counts before division removes this ambiguity without inventing a zero latency.

## Fix Or Change

Token counter/rate panels aggregate stream modes per environment/model/instance.
Latency panels divide grouped histogram sums/counts and omit zero-count windows.
Added a model-target live pytest and a PromQL regression test under monitoring.
The regression test evaluates actual dashboard expressions with the pinned
Prometheus engine: five active-service expectations and two empty idle-latency
expectations. The live test queries Grafana over its Tailscale address and checks
that all served panels match the reviewed repository JSON.

## Verification

All seven synthetic query expectations passed, covering an active non-streaming
series alongside an idle streaming series, service totals, weighted mean latency,
and fully idle windows. The live test generated 374 tokens and observed exactly
374 additional output tokens; Prometheus and Grafana both returned positive rates
and all ten dashboard panels returned finite values. The model was not restarted.
The combined branch's ordinary pytest suite passed with six opt-in tests skipped;
the two monitoring tests were also explicitly enabled and passed as above.
Promtool and Git whitespace validation passed. Credentials remained local.

## Lesson

Exercise mixed exporter labels and idle periods with deterministic query tests,
then validate the same dashboard expressions against real inference traffic.
A fresh single-mode deployment is insufficient to establish aggregation behavior.

## Next Step

Create and merge the reviewed PR, then stop inference and monitoring as requested.
