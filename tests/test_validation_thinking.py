"""Validate explicit thinking controls without changing existing endpoint defaults."""
from dataclasses import replace

import pytest
import yaml

from inferpack.cli import _validate_chat, _validate_responses
from inferpack.manifest import ManifestError, load_manifest


@pytest.mark.parametrize("thinking", [None, False, True])
@pytest.mark.parametrize("endpoint", ["chat", "responses"])
def test_request_thinking_toggle_and_endpoint_defaults(monkeypatch, thinking, endpoint):
    manifest = replace(load_manifest("qwen3.8-27b-fp8"), validation_enable_thinking=thinking)

    def post(url, body, timeout):
        if endpoint == "chat" and thinking is None:
            assert "chat_template_kwargs" not in body
            assert body["temperature"] == 0.6
        else:
            assert body["chat_template_kwargs"] == {"enable_thinking": thinking if thinking is not None else False}
        if endpoint == "chat":
            return {"choices": [{"message": {"content": "Ready"}}]}
        return {"status": "completed", "output_text": "Ready"}

    monkeypatch.setattr("inferpack.cli._post_json", post)
    (_validate_chat if endpoint == "chat" else _validate_responses)(manifest, 30000, 1)


@pytest.mark.parametrize("value", ["false", 0, 1, None, {}, []])
def test_manifest_rejects_non_boolean_thinking(monkeypatch, value):
    manifest = load_manifest("nvidia-nemotron-3-nano-30b-a3b-nvfp4")
    data = yaml.safe_load(manifest.path.read_text())
    data["validation"]["enable_thinking"] = value
    monkeypatch.setattr("inferpack.manifest.yaml.safe_load", lambda _: data)
    with pytest.raises(ManifestError, match="must be a boolean"):
        load_manifest(manifest.identifier)


def test_embedding_manifest_rejects_thinking_toggle(monkeypatch):
    manifest = load_manifest("qwen3-embedding-8b")
    data = yaml.safe_load(manifest.path.read_text())
    data["validation"]["enable_thinking"] = False
    monkeypatch.setattr("inferpack.manifest.yaml.safe_load", lambda _: data)
    with pytest.raises(ManifestError, match="requires text-generation"):
        load_manifest(manifest.identifier)
