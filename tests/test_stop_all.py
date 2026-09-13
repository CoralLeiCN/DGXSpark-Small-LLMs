import subprocess

import pytest

from inferpack import cli, docker
from inferpack.manifest import ManifestError, discover_manifests, repository_root


@pytest.mark.parametrize("scenario", ["running", "empty", "stop-failure", "list-failure"])
def test_stop_all_scopes_shutdown_and_continues_after_failures(monkeypatch, capsys, scenario):
    packs = [
        target.compose_file.resolve()
        for manifest in discover_manifests()
        for engine in manifest.engines.values()
        for target in engine.targets.values()
    ]
    monitoring = repository_root() / "monitoring/compose.yaml"

    def container(path, *, running=True):
        return {
            "running": running,
            "com.docker.compose.project.working_dir": str(path.parent),
            "com.docker.compose.project.config_files": str(path),
        }

    containers = {
        "model-a": container(packs[0]),
        "model-b": container(packs[-1]),
        "prometheus": container(monitoring),
        "grafana": container(monitoring),
        "already-stopped": container(packs[0], running=False),
        "other-checkout": container(packs[0]),
        "other-config": container(packs[0]),
        "unlabelled": {"running": True},
    }
    containers["other-checkout"]["com.docker.compose.project.working_dir"] = "/other"
    containers["other-config"]["com.docker.compose.project.config_files"] = "/other.yaml"
    if scenario == "empty":
        for values in containers.values():
            values["running"] = False
    stopped = []
    queried = []
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "shared-project")
    monkeypatch.delenv("GRAFANA_ADMIN_PASSWORD", raising=False)

    def run(command, **kwargs):
        if command[:3] == ["docker", "container", "ls"]:
            assert "--all" not in command
            filters = dict(
                command[index + 1].removeprefix("label=").split("=", 1)
                for index, argument in enumerate(command)
                if argument == "--filter"
            )
            path = filters["com.docker.compose.project.config_files"]
            queried.append(path)
            if scenario == "list-failure" and path == str(packs[0]):
                raise docker.DockerError("simulated listing failure")
            matching = [
                identifier for identifier, values in containers.items()
                if values["running"] and all(values.get(key) == value for key, value in filters.items())
            ]
            # Duplicate results must never cause duplicate shutdown attempts.
            return subprocess.CompletedProcess(command, 0, "\n".join(matching * 2), "")
        assert command[:3] == ["docker", "container", "stop"]
        assert len(command) == 4
        stopped.append(command[3])
        if scenario == "stop-failure" and command[3] == "model-a":
            raise docker.DockerError("simulated stop failure")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(docker, "run", run)
    assert cli.main(["stop-all"]) == (1 if scenario.endswith("failure") else 0)
    assert queried == [str(path) for path in [*packs, monitoring]]
    expected = ["model-a", "model-b", "prometheus", "grafana"]
    if scenario == "empty":
        expected = []
    elif scenario == "list-failure":
        expected.remove("model-a")
    assert stopped == expected
    output = capsys.readouterr()
    assert ("simulated" in output.err) == scenario.endswith("failure")


def test_stop_all_still_stops_monitoring_when_manifests_are_invalid(monkeypatch, capsys):
    def discover():
        raise ManifestError("invalid manifest")

    monkeypatch.setattr(cli, "discover_manifests", discover)
    queried = []

    def running(compose_file):
        queried.append(compose_file)
        return ["prometheus", "grafana"]

    monkeypatch.setattr(docker, "running_compose_container_ids", running)
    stopped = []
    monkeypatch.setattr(docker, "run", lambda command: stopped.append(command))
    assert cli.main(["stop-all"]) == 1
    assert queried == [repository_root() / "monitoring/compose.yaml"]
    assert stopped == [
        ["docker", "container", "stop", "prometheus"],
        ["docker", "container", "stop", "grafana"],
    ]
    assert "invalid manifest" in capsys.readouterr().err
