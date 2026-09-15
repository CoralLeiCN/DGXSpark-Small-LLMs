"""Evaluate the actual dashboard PromQL against mixed stream-mode samples."""

import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml


pytestmark = pytest.mark.skipif(
    os.environ.get("INFERPACK_MONITORING_TESTS") != "1",
    reason="Set INFERPACK_MONITORING_TESTS=1 to run promtool in Docker.",
)


def test_mixed_stream_modes_and_idle_latency(tmp_path: Path) -> None:
    monitoring = Path(__file__).resolve().parents[1]
    dashboard = json.loads((monitoring / "grafana/dashboards/inference.json").read_text())
    model = "gemma-4-26b-a4b-it"
    labels = f'environment="dev",instance="host.docker.internal:30000",model="{model}"'
    inputs = []
    for metric, active, idle in (
        ("generation_tokens_total", "0+60x5 300+0x8", "30+0x13"),
        ("prompt_tokens_total", "0+120x5 600+0x8", "100+0x13"),
        ("time_to_first_token_seconds_sum", "0+120x5 600+0x8", "20+0x13"),
        ("time_to_first_token_seconds_count", "0+60x5 300+0x8", "10+0x13"),
        ("inter_token_latency_seconds_sum", "0+3x5 15+0x8", "1+0x13"),
        ("inter_token_latency_seconds_count", "0+60x5 300+0x8", "10+0x13"),
    ):
        for streaming, values in (("false", active), ("true", idle)):
            inputs.append({
                "series": f'sglang:{metric}{{{labels},job="sglang",is_streaming="{streaming}"}}',
                "values": values,
            })

    expected = {
        "Output tokens since engine restart": 330,
        "Output throughput": 1,
        "Input throughput": 2,
        "Time to first token (mean)": 2,
        "Inter-token latency (mean)": 0.05,
    }
    checks = []
    for panel in dashboard["panels"]:
        if panel["title"] not in expected:
            continue
        expression = (
            panel["targets"][0]["expr"]
            .replace("$environment", "dev")
            .replace("$model", model)
            .replace("$__rate_interval", "2m")
        )
        checks.append({
            "expr": expression,
            "eval_time": "5m",
            "exp_samples": [{"labels": "{" + labels + "}", "value": expected[panel["title"]]}],
        })
        if "latency" in panel["title"] or "first token" in panel["title"]:
            checks.append({"expr": expression, "eval_time": "12m", "exp_samples": []})
    assert len(checks) == 7
    fixture = {"evaluation_interval": "1m", "tests": [{
        "interval": "1m", "input_series": inputs, "promql_expr_test": checks,
    }]}
    (tmp_path / "queries.yml").write_text(yaml.safe_dump(fixture))
    image = yaml.safe_load((monitoring / "compose.yaml").read_text())["services"]["prometheus"]["image"]
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--user", "0:0",
         "-v", f"{tmp_path}:/tests:ro", "--entrypoint", "promtool", image,
         "test", "rules", "/tests/queries.yml"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cached_input_zero_requires_completed_request_evidence(tmp_path: Path) -> None:
    monitoring = Path(__file__).resolve().parents[1]
    dashboard = json.loads((monitoring / "grafana/dashboards/inference.json").read_text())
    panels = {panel["id"]: panel for panel in dashboard["panels"]}
    labels = 'environment="dev",instance="spark:30000",job="sglang",model="example"'
    count_series = {
        "series": f'sglang:uncached_prompt_tokens_histogram_count{{{labels}}}',
        "values": "0+1x5",
    }
    checks = []
    for panel_id, expected_labels in (
        (12, '{environment="dev",instance="spark:30000",model="example"}'),
        (13, "{}"),
    ):
        expression = (
            panels[panel_id]["targets"][0]["expr"]
            .replace("$environment", "dev")
            .replace("$model", "example")
            .replace("$__range", "5m")
        )
        checks.append({
            "expr": expression,
            "eval_time": "5m",
            "exp_samples": [{"labels": expected_labels, "value": 0}],
        })
        checks.append({
            "expr": expression.replace('model=~"example"', 'model=~"absent"'),
            "eval_time": "5m",
            "exp_samples": [],
        })
    fixture = {"evaluation_interval": "1m", "tests": [{
        "interval": "1m", "input_series": [count_series],
        "promql_expr_test": checks,
    }]}
    (tmp_path / "cached-input.yml").write_text(yaml.safe_dump(fixture))
    image = yaml.safe_load((monitoring / "compose.yaml").read_text())["services"]["prometheus"]["image"]
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--user", "0:0",
         "-v", f"{tmp_path}:/tests:ro", "--entrypoint", "promtool", image,
         "test", "rules", "/tests/cached-input.yml"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_estimated_tflops_preserves_ranks_filters_and_counter_resets(tmp_path: Path) -> None:
    monitoring = Path(__file__).resolve().parents[1]
    dashboard = json.loads((monitoring / "grafana/dashboards/inference.json").read_text())
    panel = next(p for p in dashboard["panels"] if p["title"] == "Estimated model TFLOPS per GPU")
    expression = (
        panel["targets"][0]["expr"]
        .replace("$environment", "dev")
        .replace("$model", "example")
        .replace("$__rate_interval", "3m")
    )
    labels = 'environment="dev",instance="spark:30000",job="sglang",model="example"'
    metric = "sglang:estimated_flops_per_gpu_total"
    # Rank zero resets at 3m; rank one stays monotonic. Both become idle at 5m.
    inputs = [
        {"series": f'{metric}{{{labels},tp_rank="0"}}',
         "values": "0 120000000000000 240000000000000 120000000000000 240000000000000 360000000000000+0x7"},
        {"series": f'{metric}{{{labels},tp_rank="1"}}',
         "values": "0+240000000000000x5 1200000000000000+0x6"},
    ]
    for excluded in (labels.replace('"dev"', '"prod"'), labels.replace('"example"', '"another-model"')):
        inputs.append({"series": f'{metric}{{{excluded},tp_rank="0"}}', "values": "0+600000000000000x12"})
    samples = lambda values: [
        {"labels": "{" + labels + f',tp_rank="{rank}"' + "}", "value": value}
        for rank, value in enumerate(values)
    ]
    fixture = {"evaluation_interval": "1m", "tests": [{
        "interval": "1m", "input_series": inputs,
        "promql_expr_test": [
            {"expr": expression, "eval_time": "4m", "exp_samples": samples([2, 4])},
            {"expr": expression, "eval_time": "12m", "exp_samples": samples([0, 0])},
            {"expr": expression.replace('"example"', '"absent"'), "eval_time": "4m", "exp_samples": []},
        ],
    }]}
    (tmp_path / "mfu.yml").write_text(yaml.safe_dump(fixture))
    image = yaml.safe_load((monitoring / "compose.yaml").read_text())["services"]["prometheus"]["image"]
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--user", "0:0",
         "-v", f"{tmp_path}:/tests:ro", "--entrypoint", "promtool", image,
         "test", "rules", "/tests/mfu.yml"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
