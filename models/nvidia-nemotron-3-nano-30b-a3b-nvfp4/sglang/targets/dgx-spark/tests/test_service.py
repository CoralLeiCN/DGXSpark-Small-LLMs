from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from inferpack.manifest import load_manifest


ENGINE_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[6]


class TestNemotronSGLangService:
    def test_safe_runtime_defaults(self) -> None:
        environment = os.environ.copy()
        environment.pop("HF_HUB_DISABLE_IMPLICIT_TOKEN", None)
        environment.pop("GPU_MEMORY_BUDGET_GIB", None)
        environment.pop("MEM_FRACTION_STATIC", None)
        environment.pop("MAX_JOBS", None)
        environment["HF_CACHE_DIR"] = "/tmp/hf-cache"

        result = subprocess.run(
            [
                "docker",
                "compose",
                "--project-directory",
                str(ENGINE_DIR),
                "-f",
                str(ENGINE_DIR / "compose.yaml"),
                "config",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            env=environment,
            text=True,
        )
        config = json.loads(result.stdout)

        assert (
            config["services"]["sglang"]["environment"][
                "HF_HUB_DISABLE_IMPLICIT_TOKEN"
            ]
            == "1"
        )
        assert (
            config["services"]["sglang"]["environment"][
                "GPU_MEMORY_BUDGET_GIB"
            ]
            == "60"
        )
        assert (
            config["services"]["sglang"]["environment"]["MEM_FRACTION_STATIC"]
            == ""
        )
        assert (
            config["services"]["sglang"]["environment"]["MAX_JOBS"] == "4"
        )

    def test_reasoning_model_has_sufficient_validation_budget(self) -> None:
        manifest = load_manifest(
            "nvidia-nemotron-3-nano-30b-a3b-nvfp4",
            root=REPOSITORY_ROOT,
        )

        assert manifest.validation_max_tokens == 512
