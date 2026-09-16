# 2026-09-16T08:03:25Z — Docker inventory blocked by sandbox access

Run ID: `RUN-0009`

- Status: workaround
- Phase: preflight
- Related turns: `none`
- Repo revision: `85155a9fbfd5d9c677db9c5de528bf244294cf5d`, dirty
- Host/GPU: DGX Spark target; GPU not queried
- Container: `dgxspark/gemma-4-e4b-it-sglang:0.1.0`; runtime state not queried
- Engine: SGLang; installed version not queried
- Model: `google/gemma-4-E4B-it`; revision and dtype not queried

## Command

```bash
docker ps --filter label=com.docker.compose.project.working_dir=<checkout> \
  --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Label "com.docker.compose.project.config_files"}}'
```

## Error Or Observation

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

## Diagnosis

- Symptom: the review environment could not inspect running containers.
- Root cause: the sandbox account cannot access the host Docker socket.
- Evidence: Docker Compose configuration rendering succeeded without daemon
  access, while the daemon-backed `docker ps` command failed at the socket.

## Fix Or Change

No runtime change was attempted. Checkout-scoped project names were verified
through rendered Compose configuration and regression tests instead of a live
container inventory.

## Verification

```bash
uv run --no-sync --offline --python 3.12 pytest -q
docker compose --project-name <generated> --project-directory <target> \
  -f <target>/compose.yaml config --format json
```

The repository suite passed with 97 tests and 8 opt-in tests skipped. Compose
rendering produced distinct checkout-scoped project names and the expected
published ports. Live container ownership remains unverified in this sandbox.

## Lesson

Compose rendering verifies project identity without Docker daemon access, but a
live ownership migration audit still requires permission to read the host socket.

## Next Step

Before migrating a running deployment, inspect legacy project labels from a host
session with Docker access and stop legacy containers that still own pack ports.
