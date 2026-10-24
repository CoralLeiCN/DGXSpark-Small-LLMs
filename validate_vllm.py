#!/usr/bin/env python3
"""Send a small OpenAI-compatible request to a local vLLM server."""

from __future__ import annotations

import os
import sys
import time

try:
    from openai import OpenAI
except ImportError:
    print(
        "Missing dependency: openai. Install project dependencies with `uv sync`.",
        file=sys.stderr,
    )
    raise SystemExit(2)


BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")
MODEL = os.getenv("VLLM_MODEL", "model")
TIMEOUT_SECONDS = float(os.getenv("VLLM_VALIDATE_TIMEOUT_SECONDS", "600"))
INTERVAL_SECONDS = float(os.getenv("VLLM_VALIDATE_INTERVAL_SECONDS", "10"))
PROMPT = "Reply with exactly: vLLM service is healthy"


def one_line(value: str) -> str:
    return " ".join(value.split())


def main() -> int:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    deadline = time.monotonic() + TIMEOUT_SECONDS
    attempt = 0

    while True:
        attempt += 1
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": PROMPT}],
                max_tokens=32,
                temperature=0,
            )
            break
        except Exception as exc:
            message = one_line(str(exc))
            status_code = getattr(exc, "status_code", None)
            retryable = status_code is None or status_code in {408, 409, 429, 500, 502, 503, 504}

            if not retryable or time.monotonic() >= deadline:
                print(
                    f"vLLM validation failed for {MODEL} at {BASE_URL} after {attempt} attempt(s): {message}",
                    file=sys.stderr,
                )
                print(
                    "Check that `docker compose --profile nano up -d` or "
                    "`docker compose --profile super up -d` is running, and that "
                    "`VLLM_MODEL` matches the served model name.",
                    file=sys.stderr,
                )
                return 1

            remaining = max(0, int(deadline - time.monotonic()))
            print(
                f"Waiting for vLLM at {BASE_URL} ({remaining}s left): {message}",
                file=sys.stderr,
            )
            time.sleep(INTERVAL_SECONDS)

    content = response.choices[0].message.content or ""
    print(f"vLLM validation succeeded for {MODEL} at {BASE_URL}: {one_line(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
