# 2026-09-20T16:47:13Z — Benchmark artifacts preserved outside Git and worktrees

Run ID: `RUN-0010`

- Status: resolved.
- Phase: artifact preservation; no new inference run or service change.
- Related turns: [Full sweep, RUN-0007](2026-09-20T12-47-55Z-aiperf-full-c1-c72.md), [performance report, RUN-0008](2026-09-20T16-28-58Z-concurrency-performance-report.md), [TFLOPS assessment, RUN-0009](2026-09-20T16-33-51Z-tflops-concurrency-assessment.md).
- Model/engine/hardware: Qwen3.8 27B NVFP4, SGLang, DGX Spark.
- User requirement: retain all AIPerf and SGLang run metrics in a dedicated directory without requiring Git commits.

## Destination and contents

The verified archive is at:

```text
/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/
├── README.md
├── archive-2026-09-20-manifest.json
├── archive-2026-09-20-sha256.txt
├── nvfp4-admission72-full-20260920-21dGW0/
├── nvfp4-c72-effective33-targeted-20260920-TPefwN/
├── nvfp4-c72-effective33-20260920-Zn2fpj/
└── reports/
```

All files in the three source experiment directories were copied unchanged,
including AIPerf raw request records, aggregate JSON/CSV, generated inputs, GPU
telemetry, SGLang raw samples and summaries, warmup/profiling summaries, phase
manifests, experiment metadata, event timestamps and console logs. The partial
initial attempt remains partial; no historical results were reconstructed.

| Experiment | Preserved benchmark files | Bytes |
| --- | ---: | ---: |
| Full c1–c72 sweep | 202 | 969,409,914 |
| Earlier completed c72 profile, admission 33 | 22 | 31,495,350 |
| Interrupted initial sweep | 8 | 5,114,769 |

The archive also includes 13 report/journal files: the nine earlier turn entries
and four generated report assets. In total, **245 source files comprising
1,006,548,386 bytes** were copied and verified, plus newly generated archive
index, manifest and checksum files. The current preservation entry was written
after the archive was finalized and is not part of that dated snapshot.

The raw-artifact source was:

```text
/home/coral/.codex/worktrees/8174/DGXSpark-Small-LLMs/models/qwen3.8-27b-nvfp4/sglang/targets/dgx-spark/artifacts/
```

Report copies came from the main checkout's target journal. Originals remain in
place. Copied report contents and source metadata retain their historical paths;
the same experiment names identify the preserved directories in the new archive.

## Verification

The collection was staged locally, hashed against the source files with SHA-256,
installed at the dedicated destination, and verified again there. The manifest
records each source path, destination-relative path, byte count and hash.
Recheck all preserved files and the manifest using:

```bash
cd "$HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark"
sha256sum --check --quiet archive-2026-09-20-sha256.txt
```

All 245 copied files passed the source/destination integrity check. This is an
independent directory on the same host and filesystem; repository/worktree
cleanup does not remove it. It is not an off-host backup or a Prometheus export.
The saved SGLang samples are the AIPerf server-metrics exports already collected
during each experiment.

## Future output location

The NVFP4 benchmark runner in the main checkout now defaults to a unique
`<experiment-tag>-<suffix>/` directory under
`$HOME/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/`.
`QWEN_NVFP4_BENCHMARK_ROOT` still overrides the complete output directory and
existing directories are never overwritten. Bash syntax validation and the help
command passed; no new model benchmark was needed for this path change.

Older worktree copies of the runner retain their previous default until updated;
their existing `QWEN_NVFP4_BENCHMARK_ROOT` override can select the external path.
The dated import manifest does not automatically include future runs.

## Lesson

Store raw benchmark evidence outside disposable code checkouts, retain the
experiment names and phase boundaries, and verify copies before relying on the
new location. Keep concise findings and archive references in the repository.
