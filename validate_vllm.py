#!/usr/bin/env python3
"""Send a small OpenAI-compatible request to a local vLLM server."""

from __future__ import annotations

import os
import sys

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
PROMPT = "Reply with exactly: vLLM service is healthy"


def one_line(value: str) -> str:
    return " ".join(value.split())


def main() -> int:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=32,
            temperature=0,
        )
    except Exception as exc:
        print(f"vLLM validation failed for {MODEL} at {BASE_URL}: {one_line(str(exc))}", file=sys.stderr)
        return 1

    content = response.choices[0].message.content or ""
    print(f"vLLM validation succeeded for {MODEL} at {BASE_URL}: {one_line(content)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
