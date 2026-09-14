# 2026-09-14T23:37:29Z — All eleven dashboard panels verified

Run ID: `RUN-0013`

- Status: resolved
- Phase: metrics validation
- Related turns: [live MFU validation](2026-09-14T23-30-13Z-mfu-live-validation.md)
- Host/GPU: DGX Spark GB10; the sequential runner had already stopped Gemma
- Model: google/gemma-4-26B-A4B-it, revision `4d7ae4984b7db7de8f8457170b3f1a419ee76d52`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`
- Monitoring: Prometheus `3.13.3`, Grafana `13.2.1`, temporary loopback instances

## Initial Observation

A supplementary uv Python 3.12 check queried all tracked dashboard expressions
through Grafana at the current time after the sequential runner had replaced
Gemma's scrape target with Nemotron. The first assertion failed:

```text
AssertionError: Scrape status (1 = reachable)
```

The query was `up{job="sglang",environment=~"dev",model=~"gemma-4-26b-a4b-it"}`
through `/api/datasources/proxy/uid/prometheus/api/v1/query`. Grafana credentials
came from a temporary local file and are omitted here. The target had been
removed from service discovery, so the current-time series was absent.
This was a validation-timing error, not a Gemma health failure.

## Fix And Verification

Repeated all eleven tracked panel expressions at timestamp `1789428984.439`,
the recorded Gemma live-validation query time from RUN-0012, using the query
API's `time` parameter. Substituted `dev`, the Gemma model label, a two-minute
rate window, and a fifteen-minute selected range. Every panel returned data
with finite values through Grafana, including the new TFLOPS panel.

The uv Python 3.12 check reads `monitoring/grafana/dashboards/inference.json`
and asserts nonempty finite query results rather than maintaining separate
copies of the expressions. Its result is retained at
`/tmp/inferpack-mfu-all/gemma-all-panels.json`. No serving or dashboard change
was needed, and no additional inference was run during this follow-up.

## Lesson

When validating a sequential benchmark after its endpoint has been removed,
evaluate dashboard expressions at the recorded run timestamp. A current-time
instant query does not recover a removed target's earlier scrape status.
