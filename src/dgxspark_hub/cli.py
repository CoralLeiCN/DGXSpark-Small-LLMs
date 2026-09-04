from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import docker
from .manifest import ManifestError, ModelManifest, load_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dgxspark",
        description="Build and operate model-specific DGX Spark containers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in (
        "build",
        "serve",
        "deploy",
        "stop",
        "logs",
        "status",
        "validate",
        "validate-responses",
    ):
        subparser = subparsers.add_parser(command)
        _add_model_arguments(subparser)
        if command == "logs":
            subparser.add_argument(
                "--no-follow",
                action="store_true",
                help="Print current logs and exit instead of following them.",
            )
        if command in {"validate", "validate-responses"}:
            subparser.add_argument(
                "--timeout",
                type=float,
                default=300.0,
                help="Request timeout in seconds (default: 300).",
            )

    preflight = subparsers.add_parser("preflight")
    _add_model_arguments(preflight)
    preflight.add_argument(
        "--skip-gpu-check",
        action="store_true",
        help="Do not start the base image to verify CUDA access.",
    )
    return parser


def _add_model_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("model", help="Model id in <provider>/<model> form.")
    parser.add_argument(
        "--engine",
        choices=("sglang", "vllm"),
        default="sglang",
        help="Inference engine (default: sglang).",
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = load_manifest(args.model)
        engine = manifest.engine(args.engine)

        if args.command == "build":
            docker.compose(engine, ["build"])
        elif args.command == "serve":
            docker.compose(engine, ["up", "-d", "--no-build"])
        elif args.command == "deploy":
            _preflight(manifest, args.engine, skip_gpu_check=False)
            docker.compose(engine, ["build"])
            docker.compose(engine, ["up", "-d", "--no-build"])
        elif args.command == "stop":
            docker.compose(engine, ["down"])
        elif args.command == "logs":
            command = ["logs"]
            if not args.no_follow:
                command.extend(["--follow", "--tail", "100"])
            docker.compose(engine, command)
        elif args.command == "status":
            docker.compose(engine, ["ps"])
        elif args.command == "validate":
            _validate(
                manifest,
                _effective_port(engine.name, engine.port),
                args.timeout,
            )
        elif args.command == "validate-responses":
            _validate_responses(
                manifest,
                _effective_port(engine.name, engine.port),
                args.timeout,
            )
        elif args.command == "preflight":
            _preflight(manifest, args.engine, args.skip_gpu_check)
        return 0
    except (docker.DockerError, ManifestError, OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _preflight(
    manifest: ModelManifest, engine_name: str, skip_gpu_check: bool
) -> None:
    engine = manifest.engine(engine_name)
    failures: list[str] = []
    warnings: list[str] = []

    machine = platform.machine().lower()
    if machine not in {"aarch64", "arm64"}:
        warnings.append(f"host architecture is {machine}, not DGX Spark ARM64")

    available, detail = docker.docker_available()
    if available:
        print(f"[ok] Docker server {detail}")
    else:
        failures.append(f"Docker unavailable: {detail}")

    if shutil.which("uv"):
        print("[ok] uv is installed")
    else:
        failures.append("uv is not installed")

    cache_dir = Path(
        os.environ.get("HF_CACHE_DIR", Path.home() / ".cache" / "huggingface")
    ).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    free_gib = shutil.disk_usage(cache_dir).free / 1024**3
    print(f"[ok] Hugging Face cache: {cache_dir} ({free_gib:.1f} GiB free)")
    if free_gib < 40:
        warnings.append(
            "less than 40 GiB is free for image layers and model weights"
        )

    base_image = engine.base_image
    if engine.base_image_env:
        base_image = os.environ.get(engine.base_image_env, base_image)

    if base_image:
        if docker.image_exists(base_image):
            print(f"[ok] cached base image: {base_image}")
            if not skip_gpu_check:
                gpu_ok, gpu_detail = docker.gpu_available(base_image)
                if gpu_ok:
                    print(f"[ok] Docker GPU access: {gpu_detail}")
                else:
                    failures.append(f"Docker GPU check failed: {gpu_detail}")
        else:
            warnings.append(
                f"base image {base_image} is not cached and will be downloaded"
            )

    if os.environ.get("HF_TOKEN"):
        print("[ok] HF_TOKEN is set")
    else:
        warnings.append(
            "HF_TOKEN is not set; this public model may still download without it"
        )

    for warning in warnings:
        print(f"[warning] {warning}")
    if failures:
        raise RuntimeError("; ".join(failures))


def _effective_port(engine_name: str, default: int) -> int:
    variable = f"{engine_name.upper()}_PORT"
    raw_port = os.environ.get(variable)
    if raw_port is None:
        return default
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError(f"{variable} must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"{variable} must be between 1 and 65535")
    return port


def _validate(manifest: ModelManifest, port: int, timeout: float) -> None:
    if manifest.validation_endpoint == "/v1/responses":
        _validate_responses(manifest, port, timeout)
        return

    _validate_chat(manifest, port, timeout)


def _validate_chat(manifest: ModelManifest, port: int, timeout: float) -> None:
    url = f"http://127.0.0.1:{port}{manifest.validation_endpoint}"
    body = {
        "model": manifest.served_name,
        "messages": [{"role": "user", "content": manifest.validation_prompt}],
        "max_tokens": manifest.validation_max_tokens,
        "temperature": 0.6,
        "top_p": 0.95,
    }
    payload = _post_json(url, body, timeout)

    try:
        choice = payload["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""
        reasoning = message.get("reasoning_content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unexpected response: {json.dumps(payload)}") from exc

    if not isinstance(content, str) or not content.strip():
        finish_reason = choice.get("finish_reason", "unknown")
        completion_tokens = payload.get("usage", {}).get(
            "completion_tokens", "unknown"
        )
        raise RuntimeError(
            "validation returned no final content "
            f"(finish_reason={finish_reason}, "
            f"completion_tokens={completion_tokens})"
        )

    if reasoning:
        print(f"Reasoning:\n{reasoning.strip()}\n")
    print(f"Response:\n{content.strip()}")


def _validate_responses(manifest: ModelManifest, port: int, timeout: float) -> None:
    url = f"http://127.0.0.1:{port}/v1/responses"
    body = {
        "model": manifest.served_name,
        "input": manifest.validation_prompt,
        "max_output_tokens": manifest.validation_max_tokens,
        "temperature": 0.6,
        "top_p": 0.95,
        "store": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    payload = _post_json(url, body, timeout)

    status = payload.get("status")
    if status != "completed":
        raise RuntimeError(
            "Responses API validation did not complete "
            f"(status={status or 'unknown'}): {json.dumps(payload)}"
        )

    text_parts: list[str] = []
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        text_parts.append(output_text.strip())

    output = payload.get("output")
    if not text_parts and isinstance(output, list):
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "output_text":
                    continue
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())

    if not text_parts:
        raise RuntimeError(
            f"Responses API validation returned no output text: {json.dumps(payload)}"
        )

    response_id = payload.get("id", "unknown")
    response_text = "\n".join(text_parts)
    print(f"Response ID: {response_id}")
    print(f"Status: {status}")
    print(f"Response:\n{response_text}")


def _post_json(url: str, body: dict[str, object], timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"validation returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach {url}: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected response: {json.dumps(payload)}")
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
