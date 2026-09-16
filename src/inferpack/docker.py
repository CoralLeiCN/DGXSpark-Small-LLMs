"""Docker operations for inference packs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

from .manifest import HardwareTarget


class DockerError(RuntimeError):
    """Raised when Docker or Docker Compose cannot perform an operation."""


def compose(
    target: HardwareTarget,
    arguments: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = False,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        "docker",
        "compose",
        "--project-name",
        project_name(
            target.directory.resolve().relative_to(target.repository.resolve()).as_posix(),
            target.repository,
        ),
        "--project-directory",
        str(target.directory),
        "-f",
        str(target.compose_file),
        *arguments,
    ]
    return run(
        command,
        cwd=target.directory,
        check=check,
        capture_output=capture_output,
        environment=environment,
    )


def compose_file(
    path: Path,
    arguments: Sequence[str],
    *,
    repository: Path,
    project: str,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            "docker",
            "compose",
            "--project-name",
            project_name(project, repository),
            "--project-directory",
            str(path.parent),
            "-f",
            str(path),
            *arguments,
        ],
        cwd=repository,
    )


def project_name(label: str, repository: Path) -> str:
    """Return a stable Compose project name scoped to one checkout."""
    normalized = re.sub(r"[^a-z0-9_-]+", "-", label.lower()).strip("-_")
    identity = f"{repository.resolve()}\0{label}".encode()
    suffix = hashlib.sha256(identity).hexdigest()[:12]
    return f"{normalized[:40]}-{suffix}"


def compose_ps(target: HardwareTarget, *, include_all: bool = False) -> list[dict]:
    arguments = ["ps", "--format", "json", "--no-trunc"]
    arguments.extend(["--all"] if include_all else ["--status", "running"])
    result = compose(target, arguments, check=False, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise DockerError(
            f"Cannot list containers for {target.compose_file}: "
            f"{detail or f'Docker Compose exited with code {result.returncode}'}"
        )

    output = result.stdout.strip()
    if not output:
        return []
    try:
        # Older Compose releases emit an array; current releases use JSON Lines.
        containers = (
            json.loads(output)
            if output.startswith("[")
            else [json.loads(line) for line in output.splitlines() if line.strip()]
        )
    except json.JSONDecodeError as exc:
        raise DockerError(
            f"Invalid Docker Compose JSON for {target.compose_file}"
        ) from exc
    if not isinstance(containers, list) or any(
        not isinstance(container, dict)
        or any(
            not isinstance(container.get(field), str)
            for field in ("ID", "Name", "Service", "State")
        )
        for container in containers
    ):
        raise DockerError(
            f"Unexpected Docker Compose output for {target.compose_file}"
        )
    if not containers:
        return []

    # A project-name override can make different packs query the same project.
    # Only attribute containers created from this pack's directory and config.
    owned = run(
        [
            "docker",
            "container",
            "ls",
            "--all",
            "--no-trunc",
            "--filter",
            f"label=com.docker.compose.project.working_dir={target.directory.resolve()}",
            "--filter",
            f"label=com.docker.compose.project.config_files={target.compose_file.resolve()}",
            "--format",
            "{{.ID}}",
        ],
        capture_output=True,
    )
    owned_ids = set(owned.stdout.splitlines())
    return [container for container in containers if container["ID"] in owned_ids]


def published_port(
    target: HardwareTarget,
    service: str,
    *,
    containers: Sequence[dict] | None = None,
) -> int:
    if containers is None:
        containers = compose_ps(target)
    publishers = [
        publisher
        for container in containers
        if container["Service"] == service
        for publisher in container.get("Publishers") or []
        if publisher.get("Protocol") == "tcp" and publisher.get("PublishedPort")
    ]
    ports = {int(publisher["PublishedPort"]) for publisher in publishers}
    if len(ports) != 1:
        raise DockerError(
            f"Expected one published port for {service!r} in {target.compose_file}, "
            f"found {sorted(ports)}"
        )
    return ports.pop()


def running_compose_container_ids(compose_file: Path) -> list[str]:
    """Find running containers by ownership without loading Compose environment files."""
    compose_file = compose_file.resolve()
    result = run(
        [
            "docker",
            "container",
            "ls",
            "--no-trunc",
            "--filter",
            f"label=com.docker.compose.project.working_dir={compose_file.parent}",
            "--filter",
            f"label=com.docker.compose.project.config_files={compose_file}",
            "--format",
            "{{.ID}}",
        ],
        capture_output=True,
    )
    return result.stdout.split()


def image_exists(image: str) -> bool:
    result = run(
        ["docker", "image", "inspect", image],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def docker_available() -> tuple[bool, str]:
    if shutil.which("docker") is None:
        return False, "docker is not installed"
    result = run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return False, detail or "Docker daemon is unavailable"
    return True, result.stdout.strip()


def gpu_available(image: str) -> tuple[bool, str]:
    result = run(
        [
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            image,
            "python3",
            "-c",
            (
                "import torch; "
                "assert torch.cuda.is_available(), 'CUDA is unavailable'; "
                "print(torch.cuda.get_device_name(0))"
            ),
        ],
        check=False,
        capture_output=True,
    )
    detail = (result.stdout if result.returncode == 0 else result.stderr).strip()
    return result.returncode == 0, detail


def runtime_environment() -> dict[str, str]:
    return os.environ.copy()


def run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = False,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env={**runtime_environment(), **(environment or {})},
            check=check,
            text=True,
            capture_output=capture_output,
        )
    except FileNotFoundError as exc:
        raise DockerError(f"Command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise DockerError(
            f"Command failed with exit code {exc.returncode}: {' '.join(command)}"
        ) from exc
