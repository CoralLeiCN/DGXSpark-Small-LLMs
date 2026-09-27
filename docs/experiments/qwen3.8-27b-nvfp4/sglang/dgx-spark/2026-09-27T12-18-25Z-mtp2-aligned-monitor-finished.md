# 2026-09-27T12:18:25Z — NVFP4 aligned MTP=2: final monitor and shutdown check

Run ID: `RUN-0032`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-27T10-59-11Z-mtp2-aligned](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-27T10-59-11Z-mtp2-aligned/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Observed final check

```json
{
  "checked_at_utc": "2026-09-27T12:18:25Z",
  "check_interval_minutes": 30,
  "suite_status": {
    "at_utc": "2026-09-27T12:18:25Z",
    "phase": "finished",
    "outcomes": [
      {
        "mtp": 2,
        "status": "completed"
      }
    ],
    "all_experiment_services_stopped": true
  },
  "benchmark_service": {
    "Result": "success",
    "ExecMainStatus": "0",
    "ActiveState": "deactivating",
    "SubState": "stop-post"
  },
  "containers": {
    "2": {
      "created": true,
      "Status": "exited",
      "Running": false,
      "Paused": false,
      "Restarting": false,
      "OOMKilled": false,
      "Dead": false,
      "Pid": 0,
      "ExitCode": 0,
      "Error": "",
      "StartedAt": "2026-09-27T11:01:08.395329165Z",
      "FinishedAt": "2026-09-27T12:18:25.031913645Z",
      "Health": {
        "Status": "unhealthy",
        "FailingStreak": 0,
        "Log": [
          {
            "Start": "2026-09-27T13:16:00.111024591+01:00",
            "End": "2026-09-27T13:16:01.162566918+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-27T13:16:31.163779952+01:00",
            "End": "2026-09-27T13:16:32.206297752+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-27T13:17:02.207476059+01:00",
            "End": "2026-09-27T13:17:03.26432424+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-27T13:17:33.265702116+01:00",
            "End": "2026-09-27T13:17:34.322192644+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-27T13:18:04.323772914+01:00",
            "End": "2026-09-27T13:18:05.40334673+01:00",
            "ExitCode": 0,
            "Output": ""
          }
        ]
      }
    }
  },
  "completed_concurrencies": {
    "2": [
      1,
      2,
      4,
      8,
      16,
      32,
      48,
      56,
      64,
      72
    ]
  },
  "all_expected_trials_verified": true,
  "all_experiment_containers_stopped": true,
  "monitor_timer_stop_exit_status": 0,
  "monitoring_finished": true,
  "outcome": "completed"
}
```

## Verification and lesson

The independent 30-minute monitor inspected the suite status, expected per-concurrency trial summaries, and Docker states. It stopped its timer after confirming that the experiment container was stopped. `monitor-checks.jsonl` preserves every check. Incomplete or failed trials are not successful results.
