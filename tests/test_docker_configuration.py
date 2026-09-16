from dataclasses import replace
import subprocess

from inferpack import docker
from inferpack.manifest import load_manifest


def test_compose_project_is_stable_and_checkout_scoped(monkeypatch, tmp_path):
    target = load_manifest("gemma-4-e4b-it").engine("sglang").target("dgx-spark")
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(docker, "run", run)
    docker.compose(target, ["ps"])
    docker.compose(target, ["ps"])

    other_root = tmp_path / "other-checkout"
    other_target = replace(
        target,
        repository=other_root,
        directory=other_root / target.directory.relative_to(target.repository),
        compose_file=other_root / target.compose_file.relative_to(target.repository),
    )
    docker.compose(other_target, ["ps"])

    names = [command[command.index("--project-name") + 1] for command in commands]
    assert names[0] == names[1]
    assert names[0] != names[2]


def test_runtime_environment_does_not_override_target_dotenv(monkeypatch):
    monkeypatch.delenv("HF_CACHE_DIR", raising=False)
    assert "HF_CACHE_DIR" not in docker.runtime_environment()

    monkeypatch.setenv("HF_CACHE_DIR", "/exported/cache")
    assert docker.runtime_environment()["HF_CACHE_DIR"] == "/exported/cache"


def test_published_port_uses_running_compose_service(monkeypatch):
    target = load_manifest("qwen3-embedding-8b").engine("sglang").target("dgx-spark")
    monkeypatch.setattr(
        docker,
        "compose_ps",
        lambda selected: [{
            "Service": "sglang",
            "Publishers": [{
                "Protocol": "tcp",
                "PublishedPort": 31002,
                "TargetPort": 30000,
                "URL": "0.0.0.0",
            }],
        }],
    )
    assert docker.published_port(target, "sglang") == 31002
