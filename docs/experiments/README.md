# Inference Experiment Journals

These journals turn failed Docker and model-serving experiments into reusable
guidance for building reliable inference services. They preserve what happened,
why it happened, what changed, and how the result was verified.

## Journal Location

Each deployable `model + engine + hardware target` pack owns an indexed
directory:

```text
docs/experiments/<model>/<engine>/<hardware>/
|-- README.md
`-- <YYYY-MM-DDTHH-MM-SSZ>-<short-slug>.md
```

The path mirrors the deployment recipe under `models/`. For example:

```text
models/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/targets/dgx-spark/
docs/experiments/nvidia-nemotron-3-nano-30b-a3b-nvfp4/sglang/dgx-spark/
```

The target journal's `README.md` links to its deployment recipe and lists every
turn in chronological order with its status and outcome. Link the model README
back to that index.

## One File Per Turn

A turn is one bounded experiment attempt or follow-up investigation performed
with a particular command, configuration, and environment. Store the entire
turn in one dedicated file. If later work retries the command, changes the
configuration, revises the diagnosis, or verifies a fix, create another turn
file and link it to the earlier file.

Use UTC in the heading and a filesystem-safe UTC timestamp in the filename:

```text
Heading:  2026-09-03T21:18:43Z
Filename: 2026-09-03T21-18-43Z-flashinfer-jit-oom.md
```

Treat a completed turn file as immutable apart from correcting a typo or
redacting a secret. Do not fold later knowledge into the earlier account. The
directory is append-only: add new turn files and index rows over time.

Every turn also receives a target-local sequential ID. Use `RUN-` followed by
four digits, beginning with `RUN-0001`. Put the ID immediately below the title,
assign the next unused number even when the preceding run is unresolved, and
never reuse or renumber an ID. The target index must state the number of recorded
runs and the next ID to assign.

## What To Record

Create a turn file whenever an observed run fails during:

- image pull or build
- container creation or runtime setup
- GPU discovery or allocation
- vLLM or SGLang startup
- dependency import, kernel compilation, or model loading
- readiness and health checks
- completion, chat, tool-calling, or other inference validation

Also create a new turn file for a retry, diagnosis, workaround, or successful
verification that materially advances an earlier failure. A routine successful
run does not need a record. If work stops before the cause or fix is known, end
the turn with `Status: open`; a future turn links back and continues the work.

Do not reconstruct or invent experiments that were not observed.

## Investigation Workflow

1. Read the target index and assign its next run ID.
2. Create the turn file when a failure is observed.
3. Capture the command, useful error excerpt, and relevant logs.
4. Record enough environment detail to reproduce the compatibility boundary.
5. Separate the observed symptom from the suspected or confirmed root cause.
6. Document the diagnostic commands and evidence that support the diagnosis.
7. Describe the exact configuration, image, dependency, or code change attempted.
8. Re-run the failing step, then validate the running API when possible.
9. Extract a lesson that can prevent the same class of failure elsewhere.
10. Add the ID and turn to the target index, then advance its counters.

Prefer exact versions, image tags or digests, model revisions, and configuration
values over descriptions such as "latest" or "default." Note whether the repo
had uncommitted changes when that fact affects reproducibility.

Redact Hugging Face tokens, registry credentials, private URLs, user data, and
other secrets from commands and logs. Keep error excerpts as short as possible
without removing the evidence needed for diagnosis.

## Turn File Template

````markdown
# YYYY-MM-DDTHH:MM:SSZ — Short experiment outcome

Run ID: `RUN-NNNN`

- Status: open | resolved | workaround
- Phase: preflight | image pull | build | container startup | engine startup | model load | health check | inference
- Related turns: [Earlier observation](earlier-turn.md), or `none`
- Repo revision: commit SHA, plus `dirty` when relevant
- Host/GPU: hardware target and details relevant to the failure
- Container: exact image tag or digest
- Engine: vLLM or SGLang and exact version
- Model: repository ID, revision, and quantization

## Command

```bash
# Use placeholders for all secrets.
command that reproduced the outcome
```

## Error Or Observation

```text
The smallest log excerpt that preserves the outcome and its context.
```

## Diagnosis

- Symptom: what was directly observed
- Root cause: confirmed cause, or current hypothesis when status is open
- Evidence: diagnostic commands, log details, and eliminated alternatives

## Fix Or Change

Describe the exact change or attempted change and why it addresses the cause.
Link relevant recipe files or commits when available.

## Verification

```bash
command used to re-run the failed step
command used to validate the inference API
```

Record the observed result. If verification reveals a distinct failure or is
performed in a later turn, create and link another turn file.

## Lesson

State the reusable compatibility check, configuration rule, or diagnostic method
that should inform future inference services.

## Next Step

State the next experiment, remaining risk, or `None` when the chain is resolved.
````

## Target Index Template

```markdown
# Model Name — Engine — Hardware Target Experiment Journal

Deployment recipe: [`models/<model>/<engine>/targets/<hardware>/`](...)

Runs recorded: 1

Next run ID: `RUN-0002`

| Run ID | Time (UTC) | Status | Outcome |
| --- | --- | --- | --- |
| `RUN-0001` | 2026-09-03T21:18:43Z | open | [FlashInfer JIT OOM](2026-09-03T21-18-43Z-flashinfer-jit-oom.md) |
```
