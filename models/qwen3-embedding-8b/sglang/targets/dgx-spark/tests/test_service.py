"""Set INFERPACK_LIVE_TESTS=1 to validate the running service."""
import math
import os
from pathlib import Path

import pytest
from inferpack.cli import _check_embedding_vectors, _post_json, _validate
from inferpack.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[6]
MODEL = "qwen3-embedding-8b"
TEXTS = [
    "Instruct: Retrieve a passage that answers the question.\nQuery: What is the capital of France?",
    "Paris is the capital of France.",
    "Bananas are yellow fruit grown in warm climates.",
]


def test_manifest_uses_dense_embeddings(monkeypatch):
    manifest = load_manifest(MODEL, ROOT)
    assert manifest.task == "embedding"
    assert manifest.modalities == ("text",)
    def post(url, body, timeout):
        assert url.endswith("/v1/embeddings")
        assert body == {"model": MODEL, "input": manifest.validation_prompt, "encoding_format": "float"}
        return {"data": [{"index": 0, "embedding": [1.0] + [0.0] * 4095}]}
    monkeypatch.setattr("inferpack.cli._post_json", post)
    _validate(manifest, 30002, 1)


@pytest.mark.skipif(os.environ.get("INFERPACK_LIVE_TESTS") != "1", reason="requires Qwen embedding service")
def test_live_batch_retrieval_and_dimensions():
    port = int(os.environ.get("SGLANG_PORT", "30002"))
    url = f"http://127.0.0.1:{port}/v1/embeddings"
    def embed(inputs, dimensions=None):
        body = {"model": MODEL, "input": inputs, "encoding_format": "float"}
        if dimensions is not None:
            body["dimensions"] = dimensions
        payload = _post_json(url, body, 300)
        expected = len(inputs) if isinstance(inputs, list) else 1
        assert [item["index"] for item in payload["data"]] == list(range(expected))
        assert payload["usage"]["prompt_tokens"] > 0
        vectors = [item["embedding"] for item in payload["data"]]
        _check_embedding_vectors(vectors, dimensions or 4096)
        return vectors
    vectors = embed(TEXTS)
    scores = [sum(a * b for a, b in zip(vectors[0], v)) for v in vectors[1:]]
    print(f"relevant={scores[0]:.6f}, unrelated={scores[1]:.6f}")
    assert scores[0] > scores[1] + 0.2
    for text, expected in zip(TEXTS, vectors):
        single = embed(text)[0]
        assert sum(a * b for a, b in zip(single, expected)) > 0.99
    reduced = embed(TEXTS, 1024)
    for full, short in zip(vectors, reduced):
        norm = math.sqrt(sum(x * x for x in full[:1024]))
        assert sum(a / norm * b for a, b in zip(full[:1024], short)) > 0.99
