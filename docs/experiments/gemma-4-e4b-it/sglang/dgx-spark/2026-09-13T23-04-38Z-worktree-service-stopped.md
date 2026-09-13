# 2026-09-13T23:04:38Z — Worktree-owned Gemma stopped after main-checkout stop-all missed it

Run ID: `RUN-0007`

- Status: workaround (service stopped; known shutdown cleanup traceback remains)
- Phase: container shutdown
- Related turns: [benchmark startup](2026-09-13T22-00-25Z-gemma-started-for-aiperf.md),
  [prior shutdown traceback](2026-09-05T23-09-10Z-shutdown-cleanup-traceback.md)
- Repo revision: `0d0acca2289c8d0475ba3c8dab76b366e4f150da`, dirty with
  benchmark documentation, runner, and journals
- Host/GPU: DGX Spark, Linux aarch64
- Container: `dgxspark-gemma-4-e4b-it-sglang-1`, image
  `dgxspark/gemma-4-e4b-it-sglang:0.1.0`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`, as recorded at startup
- Model: `google/gemma-4-E4B-it`, revision
  `ee0ef6023621cff504d758262d4e04895a5af4a2`, BF16

## Command And Observation

The user reported `infer stop-all` printing `Stopped 0 container(s)` from the
main checkout. Direct inspection found Gemma still healthy on port 30000:

```bash
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'
docker inspect dgxspark-gemma-4-e4b-it-sglang-1 \
  --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
```

The Compose working-directory and config-file labels pointed to this Codex
worktree's Gemma target directory. `running_compose_container_ids` matches both
resolved paths exactly. The main checkout's paths differ, so that CLI scope
does not include this container. This follows the documented ownership policy;
it is not evidence that Docker failed to stop a selected container.

## Fix And Shutdown Error

Completed the user's attempted shutdown by stopping the identified container:

```bash
docker stop --timeout 120 dgxspark-gemma-4-e4b-it-sglang-1
```

SGLang drained all requests, then repeated the known development-runtime cleanup
warnings and traceback:

```text
23:04:08 Gracefully exiting... Remaining number of requests 0.
WARNING: destroy_process_group() was not called before program exit
23:04:11 ERROR: Traceback (most recent call last):
SystemExit: 0
asyncio.exceptions.CancelledError
```

No runtime patch was attempted. Added a concrete Git-worktree explanation and
ownership-inspection guidance to the root README; the checkout-scoped shutdown
policy remains unchanged.

## Verification

```bash
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'
docker inspect dgxspark-gemma-4-e4b-it-sglang-1 \
  --format '{{.State.Status}} {{.State.ExitCode}}'
ss -ltn '( sport = :30000 )'
```

Docker listed no running containers. Gemma was `exited` with exit code `0`.
The socket listing showed no listener on port 30000. The stopped container,
images, cached weights, and benchmark artifacts were retained.

## Lesson And Next Step

Distinguish checkout-scoped service discovery from the Docker host's full
inventory. Inspect Compose ownership labels when a main checkout cannot see
worktree-launched services. Verify container state and port closure after a
shutdown traceback. No remaining action for stopping this service.
