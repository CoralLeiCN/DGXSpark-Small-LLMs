# InferPack Spec

Status: draft

This spec describes the architecture for hardware-targeted inference packs.

## Goal

Build and maintain ready-to-run inference packs for single-node or single-GPU
hardware targets, with each model able to define independent vLLM or SGLang
environments for each supported hardware class. The currently implemented
hardware target is NVIDIA DGX Spark.

The repository should make it easy to:

- add a model without creating a provider namespace hierarchy
- add a concrete hardware target only where that model and engine are supported
- choose vLLM or SGLang
- build, start, stop, inspect, and validate a selected deployment pack
- keep incompatible model, engine, architecture, and hardware runtimes isolated

The catalog includes generation and embedding models. The pack format remains
model-type neutral so other qualified inference workloads can be added without
renaming the project or CLI.
Manifests describe `task` and `modalities` for non-generative packs. Existing
language-model manifests default to `text-generation` and `[text]`. Embedding
packs declare `embedding` (one vector, `/v1/embeddings`) or
`multi-vector-embedding` (token vectors, `/encode`), with `validation.input` and
positive `validation.dimensions`. Validation checks finite, normalized vectors
of the declared dimension; model-local service tests establish numerical and
retrieval correctness. Generation packs continue to use `validation.prompt`
and `validation.max_tokens`. Incompatible task/endpoint pairs are rejected.

## Supported Inference Engines

The supported serving engines are:

- vLLM
- SGLang

Other engines require a new technical evaluation and an explicit project-scope
decision. An individual model target must not introduce another engine on its
own.

## Non-goals

The repository does not try to support every inference engine or deployment
platform. The following remain out of scope:

- TensorRT-LLM
- NVIDIA NIM
- Ollama
- llama.cpp
- Kubernetes
- multi-node orchestration
- a custom model-serving web UI (Grafana monitoring is supported)
- a global Python environment that directly serves every model
- implicit hardware-target selection based only on detected GPU names

## Deployment Identity

Model serving is container-first. There is no universal serving environment:
CPU architecture, CUDA, PyTorch, engine, tokenizer, quantization, attention
backend, memory topology, and launch settings can differ across models and
hardware.

An **inference pack** is a versioned serving environment configured and
validated for one deployment identity:

```text
model + engine + hardware target
```

Examples:

```text
nvidia-nemotron-3-nano-30b-a3b-nvfp4 + sglang + dgx-spark
gemma-4-e4b-it + sglang + dgx-spark
example-model + vllm + rtx-4080-16gb
```

Every implemented deployment identity owns its Dockerfile, Compose file,
startup script, environment defaults, and service tests. Do not assume that a
container or launch configuration qualified on DGX Spark also works on a
discrete RTX GPU.

## Model And Hardware Identifiers

Model IDs are globally unique lowercase slugs. They may contain letters,
numbers, dots, underscores, and hyphens, and must begin with a letter or number.
They do not contain a provider path component.

Provider remains explicit metadata in the manifest. The upstream source
repository retains its canonical namespace, such as
`google/gemma-4-E4B-it`. Include a provider or brand in the local slug when it
improves recognition or avoids a collision, not because the directory layout
requires it.

Hardware target IDs describe reproducible hardware classes. Prefer precise
slugs such as `dgx-spark` or `rtx-4080-16gb` over ambiguous names such as
`4080`. A target directory is created only when a concrete recipe is being
implemented; the repository does not materialize the full model-engine-hardware
cross product.

## Repository Layout

```text
inferpack/
|-- README.md
|-- pyproject.toml
|-- uv.lock
|-- monitoring/
|   |-- compose.yaml
|   |-- .env.example
|   |-- README.md
|   |-- prometheus/
|   |   |-- prometheus.yml
|   |   `-- targets/
|   `-- grafana/
|       |-- provisioning/
|       `-- dashboards/
|-- docs/
|   |-- README.md
|   |-- SPEC.md
|   `-- experiments/
|       |-- README.md
|       `-- <model>/<engine>/<hardware>/
|           |-- README.md
|           `-- <timestamp>-<slug>.md
|-- scripts/
|   |-- build
|   |-- serve
|   |-- deploy
|   |-- stop
|   |-- logs
|   |-- status
|   |-- services
|   |-- validate
|   `-- validate-responses
|-- src/
|   `-- inferpack/
|       |-- __init__.py
|       |-- cli.py
|       |-- manifest.py
|       `-- docker.py
`-- models/
    `-- <model>/
        |-- manifest.yaml
        |-- README.md
        |-- vllm/
        |   `-- targets/
        |       `-- <hardware>/
        |           |-- Dockerfile
        |           |-- compose.yaml
        |           |-- start.sh
        |           |-- .env.example
        |           `-- tests/
        `-- sglang/
            `-- targets/
                `-- <hardware>/
                    |-- Dockerfile
                    |-- compose.yaml
                    |-- start.sh
                    |-- .env.example
                    `-- tests/
```

## Component Responsibilities

### `scripts/`

Top-level scripts are thin user-facing wrappers around the Python 3.12 CLI:

```bash
uv run --python 3.12 infer <command> "$@"
```

### `src/inferpack/`

The shared package owns repository-level behavior:

- parse command-line arguments
- discover and validate model manifests
- resolve a model, engine, and hardware target
- validate declared host constraints during preflight
- invoke Docker Compose from the selected target directory
- perform basic API validation

It must not import vLLM or SGLang or own model-specific launch flags.

### `models/<model>/`

A model folder owns stable model-level information:

- globally unique identity and provider metadata
- upstream repository and served name
- API validation settings
- human-readable model notes
- implemented vLLM and/or SGLang target packs

### `models/<model>/<engine>/targets/<hardware>/`

This is the deployable serving environment. It owns:

- base image and pinned runtime versions
- CPU/GPU-architecture-compatible dependencies
- model- and hardware-specific launch flags and defaults
- exposed ports, volumes, and GPU reservation
- service health settings
- target-specific service tests

Duplication between hardware targets is acceptable when it preserves a clear
compatibility boundary. Extract shared model-engine files only after real
targets demonstrate that they are identical and can remain so.

### `docs/experiments/`

Every deployment identity has an indexed, append-only journal at:

```text
docs/experiments/<model>/<engine>/<hardware>/
```

Each experiment turn has one immutable UTC-timestamped Markdown file and a
stable target-local sequential ID such as `RUN-0001`. Later diagnosis or
verification goes in a new linked turn with the next ID. Model READMEs describe
the stable recipe; journals preserve the observed investigation history for a
specific hardware target.

## Manifest Schema

Each model manifest lives at:

```text
models/<model>/manifest.yaml
```

Example:

```yaml
id: gemma-4-e4b-it
name: Gemma 4 E4B IT
provider: google

model:
  source: huggingface
  repo: google/gemma-4-E4B-it
  served_name: gemma-4-e4b-it

engines:
  sglang:
    targets:
      dgx-spark:
        status: experimental
        image: dgxspark/gemma-4-e4b-it-sglang:0.1.0
        base_image: lmsysorg/sglang:dev-qwen38-27b-dflash2
        base_image_env: SGLANG_BASE_IMAGE
        compose: sglang/targets/dgx-spark/compose.yaml
        port: 30000
        host:
          architectures: [aarch64, arm64]

validation:
  endpoint: /v1/chat/completions
  prompt: Reply with exactly this text and nothing else: ready
  max_tokens: 128
```

Engine and target presence means the pack exists. Unsupported engines and
hardware targets are omitted rather than represented by disabled placeholders.
Qualification status belongs to the target because support observed on one
hardware class says nothing about another.

`host.architectures` declares the host CPU architectures supported by that
target. Preflight rejects a selected target when the current host architecture
does not match. Additional target constraints, such as minimum device memory or
GPU compute capability, should be added when corresponding detection is
implemented and validated.

## Command Model

The user explicitly selects the hardware recipe:

```bash
scripts/models
scripts/services
scripts/services --all
scripts/preflight <model> --engine sglang --target <hardware>
scripts/build <model> --engine sglang --target <hardware>
scripts/serve <model> --engine sglang --target <hardware>
scripts/deploy <model> --engine sglang --target <hardware>
scripts/logs <model> --engine sglang --target <hardware>
scripts/status <model> --engine sglang --target <hardware>
scripts/validate <model> --engine sglang --target <hardware>
scripts/validate-responses <model> --engine sglang --target <hardware>
scripts/stop <model> --engine sglang --target <hardware>
```

For example:

```bash
scripts/build gemma-4-e4b-it --engine sglang --target dgx-spark
```

resolves to the Compose pack under:

```text
models/gemma-4-e4b-it/sglang/targets/dgx-spark/
```

`infer models` prints one row per implemented model, engine, and hardware
target, including provider, target-level status, and served name.

`infer services` discovers every pack in the repository and queries its Compose
project on the current Docker daemon. It prints one row per running container,
including model, engine, hardware target, service, container name, state, health,
and actual port bindings. It needs no model or target arguments. `--all` also
includes stopped containers; packs with no containers have no rows. This is a
read-only snapshot of the repository's Compose projects, not a host-wide Docker
inventory or an API readiness check. Project selection follows the same Compose
configuration and environment as the lifecycle commands. Before attributing a
container to a pack, its Compose working-directory and configuration-file labels
must match that pack's current directory and single Compose file. Container IDs
are deduplicated, so a shared `COMPOSE_PROJECT_NAME` cannot list one container
under several models. Containers with missing or different ownership labels,
including those created from a previous recipe path, are omitted.

## Shared Monitoring

`monitoring/` owns one Docker Compose deployment of Prometheus and Grafana,
independent of the model packs. Dev and prod share this stack; Prometheus scrape
target labels (`environment`, `model`, `engine`, `hardware`) identify workloads.
These labels are dashboard filters, not access-control or resource-isolation
boundaries. Docker image tags pin monitoring software versions, not environments.

Prometheus discovers explicit endpoints from files in `monitoring/prometheus/targets/`.
The initial target is Gemma 4 26B A4B on the local DGX Spark, labelled `dev`.
Each endpoint is listed once. A separate prod service needs a distinct endpoint;
changing an environment label creates a new time series. Scraping model host
ports allows the monitoring host to move without changing inference pack networks.
Model-specific flags, including `--enable-metrics`, remain in each target pack.

Both monitoring services use pinned official images, persistent Docker volumes,
and restart policies. Prometheus retains 30 days of samples by default. Grafana
provisions its data source and dashboard from tracked files; credentials stay in
an ignored local `.env`. Published monitoring ports bind to loopback by default.
`GRAFANA_BIND_ADDRESS` overrides Grafana independently for remote browser access;
the deployed Spark uses its Tailscale IPv4 address for Grafana while Prometheus
stays on loopback. Clients need access to the same tailnet.
Grafana login remains required. A browser on another machine uses the Spark's
Tailscale address, not its own `localhost` (unless using an SSH tunnel).
Both environments share retention, storage, and monitoring outages. Historical
samples survive model restarts; counters reset, and `rate`/`increase` account for
observed resets. Collection gaps cannot be reconstructed. This stack includes
metrics and dashboards; alert routing is not configured.

## Runtime Assumptions

- Serving runs in containers with Docker and NVIDIA container runtime support.
- The host uses `uv` and Python 3.12 only for lightweight repository tooling.
- Models may require credentials, so `.env` files remain local and uncommitted.
- Model downloads persist in a host Hugging Face cache and are not baked into
  the image.
- vLLM and SGLang versions may differ by model and target.
- Some model and hardware combinations may support only one engine.
- OpenAI-compatible endpoints are preferred where the selected engine supports
  them.
- Responses API is the primary application and validation path when available;
  Chat Completions remains the compatibility path otherwise.
- Official SGLang or NVIDIA framework images are preferred over unrelated
  third-party serving images.
- Exact cached base-image tags may be reused when compatible, but cache reuse
  must not override model- or target-specific compatibility.

## Tradeoffs

### Explicit target directories

Target directories add a hierarchy level and may duplicate files, but they make
architecture, memory, base-image, and qualification boundaries visible and
reviewable.

### Flat model catalog

Globally unique model slugs remove repetitive provider nesting and make CLI
commands shorter. The tradeoff is that uniqueness is enforced across the whole
catalog; provider metadata and upstream repository IDs remain available for
provenance.

### Explicit target selection

Requiring `--target` adds one CLI argument, but prevents a detected GPU or a
default from silently choosing a recipe with different compatibility and memory
assumptions.

### Per-pack containers

Independent containers increase duplication, but keep dependency and hardware
incompatibilities isolated.

### Minimal shared tooling

Keeping orchestration thin avoids coupling the host package to serving
dependencies. Manifest fields should expand only as implemented targets expose
requirements that shared preflight or discovery must understand.

## Open Questions

- Should model images remain local-only or eventually be pushed to a registry?
- Should downloaded weights use a shared system cache such as `/data/models`?
- Should `serve` use attached or detached mode by default?
- Which capability checks beyond host architecture should become mandatory
  before adding the first discrete-GPU target?
