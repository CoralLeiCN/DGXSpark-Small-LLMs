"""Docker operations for inference packs."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from .manifest import Engine


class DockerError(RuntimeError):
    """Raised when Docker or Docker Compose cannot perform an operation."""


def compose(
    engine: Engine,
    arguments: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        "docker",
        "compose",
        "--project-directory",
        str(engine.directory),
        "-f",
        str(engine.compose_file),
        *arguments,
    ]
    return run(
        command,
        cwd=engine.directory,
        check=check,
        capture_output=capture_output,
    )


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
