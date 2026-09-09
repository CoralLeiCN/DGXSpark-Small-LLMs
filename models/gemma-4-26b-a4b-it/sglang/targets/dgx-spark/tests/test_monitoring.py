"""Opt-in integration test for Gemma and the shared monitoring containers."""

from __future__ import annotations

import base64
import json
import math
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("INFERPACK_MONITORING_TESTS") != "1",
    reason="Set INFERPACK_MONITORING_TESTS=1 with Gemma and monitoring running.",
)

MODEL = "gemma-4-26b-a4b-it"
SELECTOR = '{job="sglang",environment="dev",model="gemma-4-26b-a4b-it"}'


def test_gemma_metrics_reach_grafana() -> None:
    """Compare real API usage with counters and query every provisioned panel."""
    model_url = os.environ.get("SGLANG_TEST_URL", "http://127.0.0.1:30000")
    prometheus_url = os.environ.get("PROMETHEUS_TEST_URL", "http://127.0.0.1:9090")
    bind = os.environ.get("GRAFANA_BIND_ADDRESS") or os.environ.get(
        "MONITORING_BIND_ADDRESS", "127.0.0.1"
    )
    if bind == "0.0.0.0":
        bind = "127.0.0.1"
    grafana_url = os.environ.get(
        "GRAFANA_TEST_URL", f"http://{bind}:{os.environ.get('GRAFANA_PORT', '3000')}"
    )
    password = os.environ.get("GRAFANA_ADMIN_PASSWORD")
    if not password:
        pytest.fail("Load monitoring/.env with uv --env-file before running this test.")
    user = os.environ.get("GRAFANA_ADMIN_USER", "admin")
    authorization = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    def request(url: str, payload: dict | None = None, *, auth: bool = False):
        headers = {"Authorization": authorization} if auth else {}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.load(response)

    def query(expression: str, *, through_grafana: bool = False):
        base = (
            f"{grafana_url}/api/datasources/proxy/uid/prometheus"
            if through_grafana
            else prometheus_url
        )
        result = request(
            f"{base}/api/v1/query?{urllib.parse.urlencode({'query': expression})}",
            auth=through_grafana,
        )
        assert result["status"] == "success"
        return result["data"]["result"]

    def counter() -> float:
        with urllib.request.urlopen(f"{model_url}/metrics", timeout=15) as response:
            lines = response.read().decode().splitlines()
        samples = [
            float(line.split()[-1])
            for line in lines
            if line.startswith("sglang:generation_tokens_total{")
        ]
        assert samples, "SGLang must expose its generated-token counter."
        return sum(samples)

    assert request(f"{grafana_url}/api/health")["database"] == "ok"
    remote = request(f"{grafana_url}/api/dashboards/uid/inference-overview", auth=True)
    assert remote["meta"]["provisioned"]
    dashboard = remote["dashboard"]
    root = Path(__file__).resolve().parents[6]
    tracked = json.loads((root / "monitoring/grafana/dashboards/inference.json").read_text())
    assert dashboard["panels"] == tracked["panels"], "Grafana must serve the reviewed panels."
    assert {v["name"] for v in dashboard["templating"]["list"]} == {"environment", "model"}
    up = query("up" + SELECTOR)
    assert up and all(float(sample["value"][1]) == 1 for sample in up)
    models = request(f"{model_url}/v1/models")
    assert MODEL in {model["id"] for model in models["data"]}

    # Let Prometheus capture a baseline before generating the test traffic.
    time.sleep(20)
    before = counter()
    output_tokens = 0
    for topic in ("the sky is blue", "leaves change color", "the Moon has phases"):
        response = request(
            f"{model_url}/v1/chat/completions",
            {
                "model": MODEL,
                "messages": [{"role": "user", "content": f"In about 100 words explain why {topic}."}],
                "max_tokens": 160,
                "temperature": 0,
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )
        assert response["choices"][0]["message"]["content"].strip()
        assert response["usage"]["completion_tokens"] > 0
        output_tokens += response["usage"]["completion_tokens"]

    # Allow the next scrape and any delayed exporter accounting to finish.
    time.sleep(20)
    delta = counter() - before
    assert delta >= output_tokens, "Exporter must count all API output tokens."
    expression = f"sum(rate(sglang:generation_tokens_total{SELECTOR}[2m]))"
    for through_grafana in (False, True):
        rate = query(expression, through_grafana=through_grafana)
        assert rate and float(rate[0]["value"][1]) > 0

    for panel in dashboard["panels"]:
        for target in panel["targets"]:
            expression = (
                target["expr"]
                .replace("$environment", "dev")
                .replace("$model", MODEL)
                .replace("$__rate_interval", "2m")
                .replace("$__range", "15m")
            )
            results = query(expression, through_grafana=True)
            assert results, f"No data for {panel['title']}"
            assert all(math.isfinite(float(sample["value"][1])) for sample in results), panel["title"]

    print(f"API output tokens: {output_tokens}; counter increase: {delta:g}; all panels passed.")
