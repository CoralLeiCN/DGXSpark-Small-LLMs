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

The initial target is **Gemma 4 26B A4B**, labelled `dev`, on host port 30000.
It is distinct from the smaller Gemma E4B recipe. Its target `.env` must contain:

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
  rg '^sglang:(generation_tokens_total|prompt_tokens_total|gen_throughput)'
```

Prometheus reaches the published model port through `host.docker.internal`,
mapped to the Docker host gateway on Linux. If monitoring moves to another
machine, replace that hostname in the target file with the Spark's reachable
LAN address. `localhost` inside Prometheus refers to its own container.

To add a real prod service, create another YAML file under
`monitoring/prometheus/targets/` using its distinct, reachable endpoint:

```yaml
- targets: [your-prod-spark:30000]
  labels:
    environment: prod
    model: gemma-4-26b-a4b-it
    engine: sglang
    hardware: dgx-spark
```

The target files are watched automatically. List each endpoint only once to
avoid counting the same workload twice. If another model takes over the same
port, update the target's `model` label. Dev/prod are metric labels, not Docker
image tags. No placeholder prod endpoint is scraped by default.

## Dashboard and interpretation

Grafana provisions the Prometheus data source and **InferPack / Inference
overview** dashboard from the files in `grafana/`. Use the Environment and Model
filters to inspect dev, prod, or both. Edit the tracked JSON to change the
provisioned dashboard; Grafana refreshes the file periodically.

Panels show scrape status, output tokens since restart, estimated input/output
tokens during the selected range, throughput, running/queued requests, and mean
latencies. Scrape status reports `/metrics` reachability, not model readiness.
Generation panels apply to text-generation services; embedding services do not
produce text output tokens.

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

With Gemma ready and both monitoring services running, run from the repository
root (this sends three short inference requests and takes about a minute):

```bash
INFERPACK_MONITORING_TESTS=1 uv run --python 3.12 --env-file monitoring/.env pytest \
  monitoring/tests \
  models/gemma-4-26b-a4b-it/sglang/targets/dgx-spark/tests/test_monitoring.py -v -s
```

The test compares API token usage with the exporter, checks a positive rate
through Prometheus and Grafana, and evaluates every provisioned dashboard panel.
It also checks that the running panels match the repository. Credentials are
loaded from the local `.env`. The query regression test uses the pinned
Prometheus image to check mixed streaming/non-streaming traffic and idle latency.
Set `SGLANG_TEST_URL`, `PROMETHEUS_TEST_URL`, or
`GRAFANA_TEST_URL` if testing endpoints other than the default host ports;
Grafana's default test URL follows its bind address and configured port.

## Storage and operation

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
