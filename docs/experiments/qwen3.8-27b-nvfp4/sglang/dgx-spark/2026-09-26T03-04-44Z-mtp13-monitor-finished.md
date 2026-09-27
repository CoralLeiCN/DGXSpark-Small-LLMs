# 2026-09-26T03:04:44Z — NVFP4 MTP=1/3: final monitor and shutdown check

Run ID: `RUN-0023`

- Status: resolved
- Phase: inference / benchmark / lifecycle
- Repo revision: `89611e1`, dirty with experiment documentation
- Host/GPU: DGX Spark, NVIDIA GB10, driver `580.173.02`, aarch64
- Image: `sha256:110ad45e7872397f337ea5714e6c97c400852938a9b8f258bcc27cab07182b0c`
- Engine: SGLang `0.0.0.dev1+g5f55db35e`; AIPerf `0.12.0`, Python 3.12
- Model: `nvidia/Qwen3.8-27B-NVFP4`, revision `482ca0f3832238542f8f5295dde86b5f22711d80`
- Artifacts: [2026-09-26T00-12-44Z-mtp1-mtp3](/home/coral/inference-artifacts/qwen3.8-27b-nvfp4/sglang/dgx-spark/2026-09-26T00-12-44Z-mtp1-mtp3/)
- Related turns: [MTP=2 launch](2026-09-25T20-24-59Z-mtp2-c72-round.md); see this target index for the MTP=1/3 launch and subsequent events.

## Observed final check

```json
{
  "checked_at_utc": "2026-09-26T03:04:44Z",
  "check_interval_minutes": 30,
  "suite_status": {
    "at_utc": "2026-09-26T03:03:11Z",
    "phase": "finished",
    "outcomes": [
      {
        "mtp": 3,
        "status": "completed"
      },
      {
        "mtp": 1,
        "status": "completed"
      }
    ],
    "all_experiment_services_stopped": true
  },
  "benchmark_service": {
    "Result": "success",
    "ExecMainStatus": "0",
    "ActiveState": "inactive",
    "SubState": "dead"
  },
  "containers": {
    "3": {
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
      "StartedAt": "2026-09-26T00:13:01.321507579Z",
      "FinishedAt": "2026-09-26T01:37:03.690600912Z",
      "Health": {
        "Status": "unhealthy",
        "FailingStreak": 1,
        "Log": [
          {
            "Start": "2026-09-26T02:34:38.933619568+01:00",
            "End": "2026-09-26T02:34:39.988763422+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T02:35:09.989638094+01:00",
            "End": "2026-09-26T02:35:11.084077307+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T02:35:41.085468736+01:00",
            "End": "2026-09-26T02:35:42.151479272+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T02:36:12.163461189+01:00",
            "End": "2026-09-26T02:36:13.230824986+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T02:36:43.231902076+01:00",
            "End": "2026-09-26T02:36:43.278900599+01:00",
            "ExitCode": 7,
            "Output": ""
          }
        ]
      }
    },
    "1": {
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
      "StartedAt": "2026-09-26T01:37:04.15849188Z",
      "FinishedAt": "2026-09-26T03:03:10.897782241Z",
      "Health": {
        "Status": "unhealthy",
        "FailingStreak": 0,
        "Log": [
          {
            "Start": "2026-09-26T04:00:48.377999906+01:00",
            "End": "2026-09-26T04:00:49.439860978+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T04:01:19.440696994+01:00",
            "End": "2026-09-26T04:01:20.494770341+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T04:01:50.495750935+01:00",
            "End": "2026-09-26T04:01:51.548182154+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T04:02:21.549982467+01:00",
            "End": "2026-09-26T04:02:22.620409958+01:00",
            "ExitCode": 0,
            "Output": ""
          },
          {
            "Start": "2026-09-26T04:02:52.622173296+01:00",
            "End": "2026-09-26T04:02:53.667747296+01:00",
            "ExitCode": 0,
            "Output": ""
          }
        ]
      }
    }
  },
  "completed_concurrencies": {
    "3": [
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
    ],
    "1": [
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

The independent 30-minute monitor inspected the suite status, expected per-concurrency trial summaries, and Docker states. It stopped its timer after confirming that both experiment containers were stopped. `monitor-checks.jsonl` preserves every check. Incomplete or failed trials are not successful results.
