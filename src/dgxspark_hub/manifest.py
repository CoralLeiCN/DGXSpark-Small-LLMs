from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ManifestError(ValueError):
    """Raised when a model manifest is missing or invalid."""


@dataclass(frozen=True)
class Engine:
    name: str
    directory: Path
    compose_file: Path
    port: int
    base_image: str | None
    base_image_env: str | None


@dataclass(frozen=True)
class ModelManifest:
    identifier: str
    model_repo: str
    served_name: str
    validation_endpoint: str
    validation_prompt: str
    validation_max_tokens: int
    path: Path
    engines: dict[str, Engine]

    def engine(self, name: str) -> Engine:
        try:
            return self.engines[name]
        except KeyError as exc:
            choices = ", ".join(sorted(self.engines)) or "none"
            raise ManifestError(
                f"Engine {name!r} is not enabled for {self.identifier}; enabled: {choices}"
            ) from exc


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_manifest(identifier: str, root: Path | None = None) -> ModelManifest:
    root = root or repository_root()
    parts = identifier.split("/")
    if len(parts) != 2 or any(not part for part in parts):
        raise ManifestError("Model must use the form <provider>/<model>")

    path = root / "models" / parts[0] / parts[1] / "manifest.yaml"
    if not path.is_file():
        raise ManifestError(f"Model manifest not found: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError(f"Manifest must be a mapping: {path}")

    manifest_id = _required_string(data, "id")
    if manifest_id != identifier:
        raise ManifestError(
            f"Manifest id {manifest_id!r} does not match requested model {identifier!r}"
        )

    model = _required_mapping(data, "model")
    validation = _required_mapping(data, "validation")
    engines_data = _required_mapping(data, "engines")
    engines: dict[str, Engine] = {}

    for name, raw_engine in engines_data.items():
        if not isinstance(raw_engine, dict) or not raw_engine.get("enabled", False):
            continue
        compose = _required_string(raw_engine, "compose")
        compose_file = path.parent / compose
        if not compose_file.is_file():
            raise ManifestError(f"Compose file not found: {compose_file}")
        engines[name] = Engine(
            name=name,
            directory=compose_file.parent,
            compose_file=compose_file,
            port=_required_int(raw_engine, "port"),
            base_image=_optional_string(raw_engine, "base_image"),
            base_image_env=_optional_string(raw_engine, "base_image_env"),
        )

    if not engines:
        raise ManifestError(f"No engines are enabled in {path}")

    return ModelManifest(
        identifier=manifest_id,
        model_repo=_required_string(model, "repo"),
        served_name=_required_string(model, "served_name"),
        validation_endpoint=_required_string(validation, "endpoint"),
        validation_prompt=_required_string(validation, "prompt"),
        validation_max_tokens=_optional_positive_int(
            validation, "max_tokens", default=128
        ),
        path=path,
        engines=engines,
    )


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ManifestError(f"Manifest field {key!r} must be a mapping")
    return value


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"Manifest field {key!r} must be a non-empty string")
    return value


def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ManifestError(f"Manifest field {key!r} must be a non-empty string")
    return value


def _required_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ManifestError(f"Manifest field {key!r} must be an integer")
    return value


def _optional_positive_int(
    data: dict[str, Any], key: str, *, default: int
) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ManifestError(f"Manifest field {key!r} must be a positive integer")
    return value
