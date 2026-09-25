# Shared inference monitoring

One Prometheus container collects SGLang metrics and one Grafana container
displays them. Dev and prod share storage, retention, and availability;
`environment` labels separate dashboard views, not permissions. No GPU is needed
for monitoring. Keep this stack running to collect history while model services
start and stop.

Qualified on DGX Spark with Prometheus 3.13.3, Grafana 13.2.1, and the Gemma
SGLang development build on 2026-09-09: all ten dashboard queries passed, and
349 generated tokens matched the exporter counter increase exactly. See the
[validation journal](../docs/experiments/gemma-4-26b-a4b-it/sglang/dgx-spark/2026-09-09T22-19-44Z-shared-monitoring-qualified.md).

## Start

Run these commands from the repository root. Docker Compose loads
`monitoring/.env`; exported shell variables take precedence.

```bash
cp -n monitoring/.env.example monitoring/.env
# Set a unique GRAFANA_ADMIN_PASSWORD in monitoring/.env before proceeding.
docker compose -f monitoring/compose.yaml up -d
docker compose -f monitoring/compose.yaml ps
```

Once the password is configured, you can start this stack and a model with one
command from the repository root:

```bash
make start MODEL=gemma-4-26b-a4b-it
```

`make start` calls `infer start`, which waits for monitoring to become healthy,
then runs preflight, builds, and starts the selected model in the background.
It enables metrics and registers the actual published inference port automatically.
Override `ENGINE=sglang`, `TARGET=dgx-spark`, or `MONITORING_ENVIRONMENT=dev` as
needed; the environment can be `dev` or `prod`. It reuses the shared monitoring
stack, which stays running if model deployment fails or the model is stopped.
The existing one-time Grafana password setup is still required.

The initial deployment has a generated password in the ignored local `.env`.
Login as `admin` using that password. This variable initializes a new Grafana
database; editing it later does not change an existing account's password.

- [Grafana dashboard](http://localhost:3000/d/inference-overview)
- [Prometheus targets](http://localhost:9090/targets)

Ports bind to loopback by default. For direct remote Grafana access, set
`GRAFANA_BIND_ADDRESS` to the host's Tailscale IPv4 address in `monitoring/.env`
and recreate only Grafana:

```bash
docker compose -f monitoring/compose.yaml up -d --no-deps grafana
```

This publishes Grafana only on that address, with login required. Prometheus
remains bound to `MONITORING_BIND_ADDRESS`. The deployed Spark uses
`GRAFANA_BIND_ADDRESS=100.127.217.100`: open
[Grafana over Tailscale](http://100.127.217.100:3000/d/inference-overview).
The client must be connected to the same tailnet with access to this host.
This is the host's current address; update it if its network changes.

Alternatively, keep both services on loopback and use an SSH tunnel:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 user@your-spark
```

Then open the localhost URLs on that machine. `MONITORING_BIND_ADDRESS` also
controls Prometheus, which has no authentication in this recipe; use the
Grafana-specific override when only the dashboard needs remote access.

## Connect model services

For local services, use `make start MODEL=<model>`. All six SGLang packs honor
the start command's `INFERPACK_ENABLE_METRICS=1` setting, even when their `.env`
has an empty `SGLANG_EXTRA_ARGS`. Other extra launch arguments are preserved.
No per-model scrape configuration is required.

After Docker successfully starts the model container, the CLI reads its actual
published port, including `.env` and exported `SGLANG_PORT` overrides, and writes
`prometheus/targets/local-auto.yml`. This ignored file is updated atomically and
is readable by the Prometheus container. Repeated starts do not add duplicates.
A different model using the same endpoint replaces the old labels; moving a pack
to a new port or environment removes that pack's old entry. Entries for other
ports remain. This does not stop an existing model to free an occupied port:
stop it explicitly before starting a replacement. Failed builds or container
starts do not relabel its endpoint.

The model continues loading in the background. Prometheus discovers target
changes within its 15-second refresh interval and begins collecting when
`/metrics` becomes available. Registration is not a model-readiness check.
Stopped targets remain visible as unreachable until replaced or removed; history
stays in Prometheus. Starts performed with direct `infer serve` or `infer deploy`
do not update the registry. The registry belongs to the checkout running
`make start`; operate monitoring and models from the same checkout.

For example, start the two embedding services on their default distinct ports:

```bash
make start MODEL=tomoro-colqwen3-embed-4b  # port 30001
make start MODEL=qwen3-embedding-8b       # port 30002
```

For a manually managed service started with `infer serve` or `infer deploy`,
enable metrics in its target `.env` and add an explicit target file as below:

```dotenv
SGLANG_EXTRA_ARGS="--enable-metrics"
```

Apply the setting to its existing built image:

```bash
uv run --python 3.12 infer serve gemma-4-26b-a4b-it --engine sglang --target dgx-spark
```

Changing container configuration recreates the service and reloads the model.
After startup and warmup, verify inference and metrics:

```bash
uv run --python 3.12 infer validate gemma-4-26b-a4b-it --engine sglang --target dgx-spark --timeout 600
curl -fsS http://localhost:30000/metrics |
  rg '^sglang:(generation_tokens_total|prompt_tokens_total|cached_tokens_total|gen_throughput)'
```

Prometheus reaches the published model port through `host.docker.internal`,
mapped to the Docker host gateway on Linux. If monitoring moves to another
machine, replace that hostname in the target file with the Spark's reachable
LAN address. `localhost` inside Prometheus refers to its own container.

To add a manually managed remote prod service, create another YAML file under
`monitoring/prometheus/targets/` using its distinct, reachable endpoint:

```yaml
- targets: [your-prod-spark:30000]
  labels:
    environment: prod
    model: gemma-4-26b-a4b-it
    engine: sglang
    hardware: dgx-spark
```

The target files are watched automatically. Keep manual endpoints in separate
files and list each endpoint only once. If a manual file already lists an endpoint
being registered automatically, `make start` reports the conflicting file rather
than double-counting it; remove that manual entry and rerun. The old tracked
`gemma-dev.yml` target has been removed in favor of automatic registration.
For manually managed endpoints, update the model label when changing models.
Dev/prod are metric labels, not Docker image tags. No placeholder endpoints are
scraped by default.

## Dashboard and interpretation

Grafana provisions the Prometheus data source and **InferPack / Inference
overview** dashboard from the files in `grafana/`. Use the Environment and Model
filters to inspect dev, prod, or both. Edit the tracked JSON to change the
provisioned dashboard; Grafana refreshes the file periodically.

Panels show scrape status, output tokens since restart, estimated input/output
tokens during the selected range, cached input tokens since restart and during
the selected range, throughput, running/queued requests, and mean latencies.
Scrape status reports `/metrics` reachability, not model readiness.
Generation panels apply to text-generation services; embedding services do not
produce text output tokens.

Cached-input panels sum `sglang:cached_tokens_total` across its `cache_source`
labels, such as device, host, and storage. The counter is emitted by SGLang
`0.5.15.post1`; the other pinned builds need a live `/metrics` check. SGLang
creates a cached-token series only after a hit. In the checked `0.5.14` and
`0.5.15.post1` sources, the uncached-prompt histogram is observed for every
completed request and accompanies the cached counter. The panels use that
histogram as evidence to show **0** when no cache-hit series exists after
requests have completed. **No data** means the exporter has not yet supplied
that evidence, a new cache-hit series has fewer than two scrapes for the
selected-range estimate, or the build does not expose the histogram. A zero on an
unchecked build needs validation that it exports both metric families.

The raw counter includes activity before Prometheus connected and resets on
engine restart; the selected-range panel estimates changes from collected
samples and needs at least two histogram scrapes to show zero. The
`--enable-cache-report` flag controls per-request API
`usage.prompt_tokens_details.cached_tokens`, not this Prometheus counter.
Neither cached-input panel separates reasoning tokens from generation tokens.

**Estimated model TFLOPS per GPU** uses the SGLang counter:

```promql
rate(sglang:estimated_flops_per_gpu_total{job="sglang"}[1m]) / 1e12
```

The panel keeps each scheduler series separate and applies the Environment and
Model filters. It averages over wall time, including idle time, and requires
at least two scrapes. An absent counter displays no data. Both `--enable-metrics`
and `--enable-mfu-metrics` are required. All six DGX Spark packs add the latter
automatically when metrics are enabled, including through `make start`. Existing
extra arguments are preserved, and an explicit MFU flag is not duplicated.
Direct launches with metrics disabled do not turn on MFU collection.

The flag, counter name, and scheduler collection paths were checked in each
cached image: SGLang `0.5.15.post1` for Nemotron and
`0.0.0.dev1+g5f55db35e` for both Gemmas, Qwen3.8, and both embedding packs.
Overriding a pack's SGLang version or base image requires rechecking compatibility.

All six packs passed sequential live validation on GB10 with their recipe defaults
and metrics enabled: readiness, configured inference validation, increasing FLOP
counters, and positive rates through Prometheus and the Grafana data source. Both
embedding packs also passed their live service and numerical reference tests.

| Model | Live validation | Evidence |
| --- | --- | --- |
| `qwen3-embedding-8b` | Passed | [RUN-0003](../docs/experiments/qwen3-embedding-8b/sglang/dgx-spark/2026-09-14T23-20-51Z-mfu-live-validation.md) |
| `tomoro-colqwen3-embed-4b` | Passed | [RUN-0007](../docs/experiments/tomoro-colqwen3-embed-4b/sglang/dgx-spark/2026-09-14T23-24-32Z-mfu-live-validation.md) |
| `gemma-4-e4b-it` | Passed | [RUN-0008](../docs/experiments/gemma-4-e4b-it/sglang/dgx-spark/2026-09-14T23-27-13Z-mfu-live-validation.md) |
| `gemma-4-26b-a4b-it` | Passed | [RUN-0012](../docs/experiments/gemma-4-26b-a4b-it/sglang/dgx-spark/2026-09-14T23-30-13Z-mfu-live-validation.md) |
| `nvidia-nemotron-3-nano-30b-a3b-nvfp4` | Passed | [RUN-0011](../docs/experiments/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/dgx-spark/2026-09-14T23-42-50Z-mfu-live-validation.md) |
| `qwen3.8-27b-fp8` | Passed | [RUN-0024](../docs/experiments/qwen3.8-27b-fp8/sglang/dgx-spark/2026-09-14T23-46-12Z-mfu-live-validation.md) |

The 11 previously provisioned dashboard panel queries returned finite data for
Gemma 4 26B at its
[recorded validation time](../docs/experiments/gemma-4-26b-a4b-it/sglang/dgx-spark/2026-09-14T23-37-29Z-all-dashboard-panels.md).
The two cached-input panels were added later and have not yet been live-validated.
Qwen3.8 additionally passed an earlier check with native MTP enabled. These checks
validate telemetry plumbing; their rates are not sustained benchmark results.

This is an approximate model-operation rate, not measured GPU arithmetic throughput
or a percentage of peak. These estimators use an attention/MLP formula;
MoE routing, hybrid GDN/Mamba layers, vision, and MTP draft/verification work are
not fully represented. Embedding requests contribute prefill estimates rather
than output-token throughput. Pooling and custom embedding projections are
outside the generic estimate. Compare identical workloads and runtime versions.

For a future benchmark, start the desired pack with
`make start MODEL=<model-slug>`; this rebuilds it, enables both metrics flags,
and registers its actual API port with Prometheus. Wait for readiness, send
the appropriate generation or embedding workload, and allow at least two
scrapes before reading the TFLOPS panel. AIPerf runners can collect client-side
GPU telemetry and, when configured, benchmark-window server metrics in their
own artifacts; Prometheus records this counter independently while the
monitoring stack is running.

The qualified Gemma runtime exports `sglang:inter_token_latency_seconds` for
token intervals. The dashboard uses that histogram; it does not assume the
`time_per_output_token_seconds` name exists in every SGLang build.

- Raw token counters reset on engine restart and include tokens counted before
  Prometheus connected. They are not all-time durable totals.
- `rate` and `increase` use sampled counter changes and handle observed resets.
  Range totals are estimates and may be fractional. Missing collection history
  cannot be recovered; at least two samples are needed to calculate a rate.
- Throughput is aggregate service output across requests and includes idle time
  in its averaging window. It differs from a single request's decode speed.
- Idle latency panels can be empty because no observations were recorded.
- Token counters and rates combine streaming and non-streaming requests per
  service. Latency means combine histogram sums and observation counts, excluding
  services with no observations in the window rather than displaying undefined values.
- Changing target labels starts new time series; earlier samples retain their
  original labels.

## Repeat the live validation

Run the non-live suite with importlib mode so identically named tests in
different model packs can be collected together:

```bash
uv run --python 3.12 pytest --import-mode=importlib -q
INFERPACK_MONITORING_TESTS=1 uv run --python 3.12 pytest monitoring/tests -q
```

The query tests check cached-input zeros and absent data, TFLOPS conversion,
separate scheduler ranks, model and environment filtering, counter resets, idle
zeros, and absent metrics, alongside throughput and latency checks. They use the
pinned Prometheus image.

With Gemma ready and both monitoring services running, run from the repository
root (this sends three short inference requests and takes about a minute):

```bash
INFERPACK_MONITORING_TESTS=1 uv run --python 3.12 --env-file monitoring/.env pytest \
  monitoring/tests \
  models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/tests/test_monitoring.py -v -s
```

The test compares API token usage with the exporter, checks a positive rate
through Prometheus and Grafana, and evaluates every provisioned dashboard panel.
It accepts missing cached-input samples when the histogram evidence is absent.
It also checks that the running panels match the repository. Credentials are
loaded from the local `.env`. The query regression test uses the pinned
Prometheus image to check mixed streaming/non-streaming traffic and idle latency.
Set `SGLANG_TEST_URL`, `PROMETHEUS_TEST_URL`, or
`GRAFANA_TEST_URL` if testing endpoints other than the default host ports;
Grafana's default test URL follows its bind address and configured port.

## Storage and operation

Run `make stop-all` (or `uv run --python 3.12 infer stop-all`) from the repository
root to stop all running model containers and both monitoring services owned by
this checkout on the current Docker daemon. It releases their GPU and memory
resources while preserving stopped containers, images, caches, networks, and
monitoring volumes. Shutdown uses Compose ownership labels, so it does not need
the Grafana password or load `.env` files. Containers from other checkout paths
are outside its scope. It attempts remaining services after a failure and returns
an error if any shutdown failed. Restart with `make start MODEL=<model>`.

In the validated embedding images, SGLang drains requests and then kills its own
process. The uv launcher reports exit 137 even after zero requests remain;
both embedding checks completed without an OOM. See the
[shutdown diagnosis](../docs/experiments/qwen3-embedding-8b/sglang/dgx-spark/2026-09-14T23-25-34Z-shutdown-self-kill.md)
for the observed signal timing and upstream code path.

Prometheus retains 30 days by default (`PROMETHEUS_RETENTION`). Named volumes
`prometheus-data` and `grafana-data`, scoped to `inferpack-monitoring`, persist
across container recreation. Both services restart unless explicitly stopped.

```bash
docker compose -f monitoring/compose.yaml logs --tail 100
docker compose -f monitoring/compose.yaml stop
docker compose -f monitoring/compose.yaml up -d
```

`down` removes containers and the network while keeping named volumes. `down -v`
deletes monitoring history and Grafana's database. It is not needed for upgrades.
To upgrade, change the pinned images in `compose.yaml`, pull, and recreate the
stack. Monitoring upgrades affect both environments. Alert routing is not set up.

## Sources

- [Prometheus file service discovery](https://prometheus.io/docs/guides/file-sd/)
- [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [SGLang metrics](https://github.com/sgl-project/sglang/blob/main/docs_new/docs/references/production_metrics.mdx)
