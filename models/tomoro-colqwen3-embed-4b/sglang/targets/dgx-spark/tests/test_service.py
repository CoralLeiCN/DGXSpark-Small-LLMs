"""Host checks; set INFERPACK_LIVE_TESTS=1 for running-service validation."""
import os
from pathlib import Path

import pytest

from inferpack.cli import _check_embedding_vectors, _post_json, _validate, _validate_responses
from inferpack.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[6]
MODEL = "tomoro-colqwen3-embed-4b"


def test_manifest_selects_token_embeddings():
    manifest = load_manifest(MODEL, ROOT)
    assert manifest.task == "multi-vector-embedding"
    assert manifest.modalities == ("text", "image")
    with pytest.raises(ValueError, match="text-generation"):
        _validate_responses(manifest, 30000, 1)


@pytest.mark.parametrize("vectors", [[], [[0.0] * 320], [[float("nan")] * 320], [[1.0]], [[True] * 320]])
def test_invalid_vectors_are_rejected(vectors):
    with pytest.raises(RuntimeError):
        _check_embedding_vectors(vectors, 320)


def test_embedding_validation_uses_native_payload(monkeypatch):
    def post(url, body, timeout):
        assert url.endswith("/encode")
        assert set(body) == {"text"}
        return {"embedding": [[1.0] + [0.0] * 319] * 3}
    monkeypatch.setattr("inferpack.cli._post_json", post)
    _validate(load_manifest(MODEL, ROOT), 30000, 1)


@pytest.mark.skipif(os.environ.get("INFERPACK_LIVE_TESTS") != "1", reason="requires running Tomoro service")
def test_live_text_embeddings_and_batch_isolation():
    manifest = load_manifest(MODEL, ROOT)
    port = int(os.environ.get("SGLANG_PORT", "30000"))
    _validate(manifest, port, 300)
    url = f"http://127.0.0.1:{port}/encode"
    texts = ["Paris is the capital of France.", "A much shorter query."]
    singles = [_post_json(url, {"text": t}, 300)["embedding"] for t in texts]
    import json
    import urllib.request
    request = urllib.request.Request(url, data=json.dumps({"text": texts}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        batch = json.load(response)
    assert len(batch) == 2
    assert len(singles[0]) != len(singles[1])
    for single, item in zip(singles, batch):
        vectors = item["embedding"]
        _check_embedding_vectors(vectors, 320)
        assert len(vectors) == len(single)
        # Batch composition must preserve each token's embedding.
        for left, right in zip(single, vectors):
            assert sum(a * b for a, b in zip(left, right)) > 0.99
