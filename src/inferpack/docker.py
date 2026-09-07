"""Docker operations for inference packs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from .manifest import HardwareTarget


class DockerError(RuntimeError):
    """Raised when Docker or Docker Compose cannot perform an operation."""


def compose(
    target: HardwareTarget,
    arguments: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        "docker",
        "compose",
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
    )


def compose_ps(target: HardwareTarget, *, include_all: bool = False) -> list[dict]:
    arguments = ["ps", "--format", "json"]
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
            for field in ("Name", "Service", "State")
        )
        for container in containers
    ):
        raise DockerError(
            f"Unexpected Docker Compose output for {target.compose_file}"
        )
    return containers


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
    environment = os.environ.copy()
    environment.setdefault(
        "HF_CACHE_DIR", str(Path.home() / ".cache" / "huggingface")
    )
    return environment


def run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=runtime_environment(),
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
