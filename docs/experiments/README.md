# Inference Experiment Journals

These journals preserve substantive model-serving failures, qualifications,
performance results, and investigations. Each entry should add reproducible
evidence or a useful finding: what happened, why, what changed, and how the
result was verified. Routine operational events belong in experiment artifacts.

Every performance experiment also follows the shared
[benchmarking rules](../BENCHMARKING.md), across all models and engines. Record
the selected sampling/trial protocol, resolved per-concurrency counts, separate
warmup, available telemetry, artifact directory, and any justified exception.
Historical journals preserve the protocol actually used; do not rewrite them
to imply compliance with a later policy.

## Final Reports

Keep consolidated final reports in
`docs/reports/<model>/<engine>/<hardware>/<YYYY-MM-DD>-<topic>.md` and list them in
the [reports index](../reports/README.md). Link the report from the model README
and target journal index. Maintain report clarifications and table additions in
that document; preserve the dated journal entries as evidence. New experiment
observations still belong in new journal entries and should be cited by the report.

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
retained turn in chronological order with its status and outcome. Link the model README
back to that index.

## One File Per Turn

A turn is one bounded experiment attempt or follow-up investigation that meets
the inclusion criteria below. It is not each shell command, chat message, poll,
or lifecycle event. Keep related diagnostics, corrected commands, retries, and
verification within the same investigation in one file before completing it.
Later work that adds a substantive configuration result, diagnosis, or fix
verification gets a new linked turn; a repeated check alone does not.

Use UTC in the heading and a filesystem-safe UTC timestamp in the filename:

```text
Heading:  2026-09-30T12:00:00Z
Filename: 2026-09-30T12-00-00Z-engine-startup-failure.md
```

Treat a completed turn file as immutable apart from correcting a typo or
redacting a secret. Do not fold later knowledge into the earlier account. The
directory is append-only during normal experiment work. The historical cleanup
exception below applies when the user requests cleanup.

Every turn also receives a target-local sequential ID. Use `RUN-` followed by
four digits, beginning with `RUN-0001`. Put the ID immediately below the title,
assign the next unused number even when the preceding run is unresolved, and
never reuse or renumber an ID. The target index must state the number of retained
run files (`Runs recorded`) and the next ID to assign. Preserve the next-ID
counter during cleanup instead of deriving it from the retained file count.
Gaps after deletion are normal and do not require an ID retirement registry.

## What To Record

Create a turn file when the work adds at least one of:

- A substantive failure or unresolved blocker in the intended serving or
  benchmark workflow, with evidence that can inform reproduction or diagnosis.
- A first qualification of a deployment pack or a materially changed runtime,
  model, configuration, or validation capability.
- An intentional performance experiment and its results, including negative,
  failed, or inconclusive trials, under the shared benchmarking rules.
- A new diagnosis, workaround, verified fix, or analysis that materially changes
  the interpretation of an earlier result.

Substantive failures include observed problems during:

- image pull or build
- container creation or runtime setup
- GPU discovery or allocation
- vLLM or SGLang startup
- dependency import, kernel compilation, or model loading
- readiness and health checks
- completion, chat, tool-calling, or other inference validation
- benchmark execution, artifact collection, or service shutdown

Do not suppress an unresolved failure because its cause is unknown. Record it
before ending the work session with `Status: open`; a future substantive turn
links back and continues the work. A recurrence deserves a new entry when it
adds evidence, changes the compatibility boundary, or blocks the experiment.

### Events that do not need a separate entry

- Routine successful starts, API smoke checks on an unchanged configuration,
  progress polls, normal shutdown, and monitor/timer completion. Summarize useful
  lifecycle evidence in the experiment's completion entry and link raw artifacts.
- Expected readiness failures while startup is progressing within its allowed
  window, or probes failing during intentional shutdown. Unexpected timeouts,
  crashes, failed cleanup, and failures after readiness still qualify.
- Repeated known sandbox, Docker-socket, GPU-access, or network restrictions
  resolved by using the established execution context. Keep a brief note in the
  relevant experiment if needed; record a new entry only for a new limitation
  or unresolved blocker that materially affects the work.
- Diagnostic-command typos, incorrect `uv` invocation, guessed source paths,
  and mistaken JSON-field assumptions corrected during the same investigation.
  Preserve a tooling issue in the substantive entry if it affected results;
  actual recipe or runner defects and invalidated measurements still qualify.
- Price lookups, rental comparisons, and general operational notes. Put useful
  material in the relevant model documentation with its original source dates.
- Reformatting existing results or repeating an existing explanation without a
  new finding. Update the relevant guide or maintained report rather than
  assigning a run ID; completed journal entries remain immutable.
- Re-verifying a fix already documented in [resolved issues](../RESOLVED_ISSUES.md)
  on an unchanged configuration. Add a new turn only for a regression, a new
  compatibility boundary, or other material evidence.

Raw evidence can include all these events without turning each into a journal
file. Keep full Docker state JSON, health histories, and monitor snapshots in
the artifact directory; include only the excerpt needed to explain a finding.
Automated runners and monitors must apply the same inclusion criteria. Successful
shutdown and monitor completion should update their artifact status, not each
generate a separate `RUN` entry. Unexpected failures remain journal-worthy.

Do not reconstruct or invent experiments that were not observed.

## Historical Cleanup

When the user requests cleanup, delete trivial entries and consolidate
superseded troubleshooting in [resolved issues](../RESOLVED_ISSUES.md). Verify
each claimed fix against current code, configuration, and available verification
evidence; a historical `resolved` status alone is insufficient. Distinguish
implemented fixes from operational workarounds and partial recoveries.

Keep one concise account of each issue: symptom, implemented remedy, source
links, original observation/verification dates, outcome, and remaining limits.
Do not reproduce command-by-command histories or full state dumps. Preserve
benchmark evidence, unresolved failures, and qualifications with independent
findings. A narrowed experiment does not establish that its original failure is
fixed. Do not change historical protocols or move later findings into earlier
turns. Non-experiment material belongs in the relevant maintained documentation.

Delete superseded files, remove their index rows, update retained counts, and
repair incoming links to the maintained document or surviving evidence. Remove
obsolete prose references as well as links. No compatibility stubs, redirects,
retirement tables, or duplicate cleanup histories are required. Leave next-ID
counters unchanged and retained runs unrenumbered. Cleanup is documentation
maintenance and does not receive a run ID.

## Investigation Workflow

1. Read the target index and [resolved issues](../RESOLVED_ISSUES.md), check the
   current implementation, and apply the inclusion criteria. Assign the next run
   ID only when a new substantive turn is warranted.
2. Create one file for the bounded investigation or experiment.
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

Record the observed result. Keep verification within this investigation here;
if later work reveals a distinct substantive failure or materially advances
the result, create and link another turn file.

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
| `RUN-0001` | 2026-09-30T12:00:00Z | open | [Engine startup failure](2026-09-30T12-00-00Z-engine-startup-failure.md) |
```
