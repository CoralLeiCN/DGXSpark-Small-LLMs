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
