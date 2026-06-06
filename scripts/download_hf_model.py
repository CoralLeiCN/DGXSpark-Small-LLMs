#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "huggingface-hub[hf-xet]>=1.1.0",
# ]
# ///
"""Download a Hugging Face model into the cache used by docker-compose."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


DEFAULT_REPO_ID = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4"


def default_hub_cache() -> Path:
    if value := os.getenv("HUGGINGFACE_HUB_CACHE"):
        return Path(value).expanduser()
    if value := os.getenv("HF_HOME"):
        return Path(value).expanduser() / "hub"
    if value := os.getenv("HF_CACHE_DIR"):
        return Path(value).expanduser() / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download or resume a Hugging Face model snapshot with progress bars.",
    )
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help=f"Hugging Face repo id to download. Default: {DEFAULT_REPO_ID}",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Git revision, branch, or tag to download. Default: main",
    )
    parser.add_argument(
        "--hub-cache-dir",
        type=Path,
        default=default_hub_cache(),
        help="Hugging Face hub cache directory. Defaults to the cache mounted into Docker.",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("HF_TOKEN"),
        help="Hugging Face token. Defaults to HF_TOKEN from the environment.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Concurrent download workers. Default: 8",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Redownload files even if cached.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Only inspect existing cache files; do not contact Hugging Face.",
    )
    return parser.parse_args()


def find_incomplete_files(cache_dir: Path, repo_id: str) -> list[Path]:
    repo_cache_dir = cache_dir / f"models--{repo_id.replace('/', '--')}"
    if not repo_cache_dir.exists():
        return []
    return sorted(repo_cache_dir.rglob("*.incomplete"))


def validate_safetensor_shards(snapshot_dir: Path) -> int:
    index_path = snapshot_dir / "model.safetensors.index.json"
    if not index_path.exists():
        print(f"No model.safetensors.index.json found at {snapshot_dir}")
        return 0

    index = json.loads(index_path.read_text())
    expected_files = sorted(set(index.get("weight_map", {}).values()))
    missing = [name for name in expected_files if not (snapshot_dir / name).exists()]

    print("\nExpected safetensor shards:")
    for name in expected_files:
        status = "present" if name not in missing else "MISSING"
        print(f"  {status:7} {name}")

    if metadata := index.get("metadata"):
        total_size = metadata.get("total_size")
        if isinstance(total_size, int):
            print(f"\nIndexed weight size: {total_size / (1024**3):.2f} GiB")

    if missing:
        print("\nDownload is incomplete; missing shard files remain.", file=sys.stderr)
        return 1

    print("\nDownload is complete for the indexed safetensor shards.")
    return 0


def print_incomplete_files(cache_dir: Path, repo_id: str) -> None:
    incomplete_files = find_incomplete_files(cache_dir, repo_id)
    if not incomplete_files:
        print("No .incomplete files found in the model cache.")
        return

    print("\nIncomplete cache files:")
    for path in incomplete_files:
        size = path.stat().st_size if path.exists() else 0
        print(f"  {size / (1024**3):.2f} GiB  {path}")


def main() -> int:
    args = parse_args()
    cache_dir = args.hub_cache_dir.expanduser().resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Repo:        {args.repo_id}")
    print(f"Revision:    {args.revision}")
    print(f"Hub cache:   {cache_dir}")
    print(f"Token:       {'set' if args.token else 'not set'}")
    print(f"Workers:     {args.max_workers}")
    print("\nStarting Hugging Face snapshot download. Existing partial files will be resumed when possible.\n")

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Missing huggingface_hub. Run this script with `uv run scripts/download_hf_model.py`.", file=sys.stderr)
        return 2

    try:
        snapshot_path = snapshot_download(
            repo_id=args.repo_id,
            revision=args.revision,
            cache_dir=cache_dir,
            token=args.token,
            max_workers=args.max_workers,
            force_download=args.force_download,
            local_files_only=args.local_files_only,
        )
    except Exception as exc:
        print(f"\nDownload failed: {exc}", file=sys.stderr)
        print_incomplete_files(cache_dir, args.repo_id)
        return 1

    snapshot_dir = Path(snapshot_path)
    print(f"\nSnapshot path: {snapshot_dir}")
    print(f"Cache size:    {shutil.disk_usage(cache_dir).used / (1024**3):.2f} GiB used on filesystem")
    print_incomplete_files(cache_dir, args.repo_id)
    return validate_safetensor_shards(snapshot_dir)


if __name__ == "__main__":
    raise SystemExit(main())
