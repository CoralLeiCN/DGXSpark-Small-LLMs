import json
import subprocess

import pytest

from inferpack import cli, docker
from inferpack.manifest import discover_manifests


@pytest.mark.parametrize("include_all", [False, True])
@pytest.mark.parametrize("json_lines", [False, True])
@pytest.mark.parametrize(
    "ownership", ["current", "old-directory", "other-config", "missing"]
)
def test_shared_project_lists_only_the_owning_pack(
    monkeypatch, capsys, include_all, json_lines, ownership
):
    manifests = discover_manifests()
    owner = manifests[-1]
    engine = next(iter(owner.engines.values()))
    target = next(iter(engine.targets.values()))
    monkeypatch.setattr(cli, "discover_manifests", lambda: manifests)
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "shared-project")

    container = {
        "ID": "a" * 64,
        "Name": "shared-project-sglang-1",
        "Service": "sglang",
        "State": "exited" if include_all else "running",
        "Health": "",
        "Publishers": None,
    }
    # All projects return the same container, plus an unrelated one. A repeated
    # result must not produce a second row, even for the correct owner.
    containers = [
        container,
        container,
        dict(container, ID="b" * 64, Name="unrelated-sglang-1"),
    ]
    labels = {
        container["ID"]: {
            "com.docker.compose.project.working_dir": str(target.directory),
            "com.docker.compose.project.config_files": str(target.compose_file),
        },
        "b" * 64: {
            "com.docker.compose.project.working_dir": "/unrelated",
            "com.docker.compose.project.config_files": "/unrelated/compose.yaml",
        },
    }
    owner_labels = labels[container["ID"]]
    if ownership == "old-directory":
        owner_labels["com.docker.compose.project.working_dir"] = "/old-recipe"
    elif ownership == "other-config":
        owner_labels["com.docker.compose.project.config_files"] = "/other/compose.yaml"
    elif ownership == "missing":
        owner_labels.clear()

    def run(command, **kwargs):
        if command[:2] == ["docker", "compose"]:
            assert "--no-trunc" in command
            status = ["--all"] if include_all else ["--status", "running"]
            assert command[-len(status):] == status
            output = (
                "\n".join(json.dumps(item) for item in containers)
                if json_lines
                else json.dumps(containers)
            )
        else:
            assert command[:3] == ["docker", "container", "ls"]
            assert "--all" in command
            assert "--no-trunc" in command
            filters = [
                command[index + 1].removeprefix("label=").split("=", 1)
                for index, argument in enumerate(command)
                if argument == "--filter"
            ]
            output = "\n".join(
                identifier
                for identifier, values in labels.items()
                if all(values.get(key) == value for key, value in filters)
            )
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(docker, "run", run)

    assert cli.main(["services", *(["--all"] if include_all else [])]) == 0
    lines = capsys.readouterr().out.splitlines()
    if ownership != "current":
        assert lines == [
            "No service containers found."
            if include_all
            else "No running services found."
        ]
        return
    assert len(lines) == 2
    assert lines[1].split() == [
        owner.identifier,
        engine.name,
        target.name,
        "sglang",
        container["Name"],
        container["State"],
        "-",
        "-",
    ]
