"""Regressions for missing metrics and stale model labels in make start."""

import os
import subprocess

import pytest
import yaml

from inferpack import cli, docker, monitoring
from inferpack.manifest import discover_manifests, load_manifest


def publishers(port):
    return [{
        "Service": "sglang",
        "Publishers": [
            {"URL": address, "TargetPort": 30000, "PublishedPort": port, "Protocol": "tcp"}
            for address in ("0.0.0.0", "::")
        ],
    }]


def register(monkeypatch, root, model, port, environment="dev"):
    manifest = load_manifest(model)
    target = manifest.engine("sglang").target("dgx-spark")
    monkeypatch.setattr(docker, "compose_ps", lambda selected: publishers(port))
    monitoring.register_model(root, manifest, "sglang", target, environment)
    return root / "monitoring/prometheus/targets/local-auto.yml"


def test_switching_models_and_ports_preserves_other_services(monkeypatch, tmp_path):
    gemma = "gemma-4-26b-a4b-it"
    qwen = "qwen3.8-27b-fp8"
    embed = "qwen3-embedding-8b"
    register(monkeypatch, tmp_path, gemma, 30000)
    register(monkeypatch, tmp_path, embed, 31002)
    register(monkeypatch, tmp_path, qwen, 30000)
    # Repeated starts are idempotent; a port/environment change removes old labels.
    register(monkeypatch, tmp_path, qwen, 30000)
    registry = register(monkeypatch, tmp_path, embed, 32002, "prod")
    groups = yaml.safe_load(registry.read_text())
    assert len(groups) == 2
    assert {group["targets"][0]: group["labels"] for group in groups} == {
        "host.docker.internal:30000": {
            "environment": "dev", "model": qwen, "engine": "sglang", "hardware": "dgx-spark",
        },
        "host.docker.internal:32002": {
            "environment": "prod", "model": embed, "engine": "sglang", "hardware": "dgx-spark",
        },
    }
    assert registry.stat().st_mode & 0o777 == 0o644


@pytest.mark.parametrize("failure", ["manual-duplicate", "bad-registry", "write-failure", "no-container"])
def test_registration_failures_do_not_overwrite_history(monkeypatch, tmp_path, failure):
    registry = register(monkeypatch, tmp_path, "gemma-4-26b-a4b-it", 30000)
    manual = registry.parent / "remote.yml"
    manual.write_text(yaml.safe_dump([{
        "targets": ["prod-spark:30000"], "labels": {"environment": "prod"},
    }]))
    if failure == "manual-duplicate":
        manual.write_text("- targets: [host.docker.internal:30000]\n")
    elif failure == "bad-registry":
        registry.write_text("invalid: [\n")
    elif failure == "write-failure":
        def fail_replace(*args):
            raise OSError("simulated write failure")
        monkeypatch.setattr(monitoring.os, "replace", fail_replace)
    original, remote = registry.read_bytes(), manual.read_bytes()
    manifest = load_manifest("qwen3.8-27b-fp8")
    monkeypatch.setattr(
        docker, "compose_ps", lambda target: [] if failure == "no-container" else publishers(30000),
    )
    with pytest.raises((RuntimeError, OSError)):
        monitoring.register_model(
            tmp_path, manifest, "sglang", manifest.engine("sglang").target("dgx-spark"), "dev",
        )
    assert registry.read_bytes() == original
    assert manual.read_bytes() == remote
    assert not list(registry.parent.glob("*.tmp"))


@pytest.mark.parametrize("failed_stage", [None, "monitoring", "preflight", "build", "up"])
def test_start_registers_only_after_successful_deployment(monkeypatch, failed_stage):
    calls = []

    def stage(name):
        calls.append(name)
        if failed_stage == name:
            raise RuntimeError(f"simulated {name} failure")

    def compose(target, arguments, **kwargs):
        stage(arguments[0])
        if arguments[0] == "up":
            assert kwargs["environment"] == {"INFERPACK_ENABLE_METRICS": "1"}

    def registered(root, manifest, engine, target, environment):
        assert manifest.identifier == "qwen3-embedding-8b"
        assert environment == "prod"
        stage("register")

    monkeypatch.setattr(monitoring, "start_stack", lambda root: stage("monitoring"))
    monkeypatch.setattr(cli, "_preflight", lambda *args, **kwargs: stage("preflight"))
    monkeypatch.setattr(docker, "compose", compose)
    monkeypatch.setattr(monitoring, "register_model", registered)
    result = cli.main([
        "start", "qwen3-embedding-8b", "--target", "dgx-spark", "--environment", "prod",
    ])
    expected = ["monitoring", "preflight", "build", "up", "register"]
    assert result == (1 if failed_stage else 0)
    assert calls == (expected[:expected.index(failed_stage) + 1] if failed_stage else expected)


@pytest.mark.parametrize("manifest", discover_manifests(), ids=lambda manifest: manifest.identifier)
@pytest.mark.parametrize("force_metrics,extras,enabled", [
    ("1", "", True),
    ("1", "--max-total-tokens 1024", True),
    ("1", "--enable-metrics --enable-mfu-metrics --max-total-tokens 1024", True),
    ("0", "", False),
    ("0", "--enable-metrics", True),
    ("0", "--enable-metrics --enable-mfu-metrics", True),
])
def test_every_pack_enables_mfu_with_metrics_without_losing_extras(
    tmp_path, manifest, force_metrics, extras, enabled,
):
    target = manifest.engine("sglang").target("dgx-spark")
    commands = tmp_path / "commands"
    # Capture each launcher invocation without starting an engine or preparing weights.
    for executable in ("python3", "uv"):
        stub = tmp_path / executable
        stub.write_text('#!/bin/bash\nprintf "%s\\n" "$@" >> "$RECORDED_ARGS"\n')
        stub.chmod(0o755)
    subprocess.run(
        ["bash", str(target.directory / "start.sh")], check=True, capture_output=True,
        env={
            **os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "RECORDED_ARGS": str(commands), "INFERPACK_ENABLE_METRICS": force_metrics,
            "SGLANG_EXTRA_ARGS": extras, "MEM_FRACTION_STATIC": "0.5",
        },
    )
    arguments = commands.read_text().splitlines()
    assert arguments.count("--enable-metrics") == int(enabled)
    assert arguments.count("--enable-mfu-metrics") == int(enabled)
    if "--max-total-tokens" in extras:
        assert arguments[arguments.index("--max-total-tokens") + 1] == "1024"


def test_compose_passes_metrics_override_without_replacing_other_environment(monkeypatch):
    monkeypatch.setenv("SGLANG_PORT", "32000")
    seen = {}

    def run(command, **kwargs):
        seen.update(kwargs["env"])
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    target = load_manifest("qwen3-embedding-8b").engine("sglang").target("dgx-spark")
    docker.compose(target, ["up", "-d"], environment={"INFERPACK_ENABLE_METRICS": "1"})
    assert seen["SGLANG_PORT"] == "32000"
    assert seen["INFERPACK_ENABLE_METRICS"] == "1"
