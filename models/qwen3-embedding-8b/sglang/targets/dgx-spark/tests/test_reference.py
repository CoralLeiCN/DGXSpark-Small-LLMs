"""Run in the serving container with INFERPACK_REFERENCE_TESTS=1."""
import os
import pytest

pytestmark = pytest.mark.skipif(os.environ.get("INFERPACK_REFERENCE_TESTS") != "1", reason="requires container and extra GPU memory")


def test_last_token_embeddings_match_transformers():
    import json
    import urllib.request
    import torch
    from transformers import AutoModel, AutoTokenizer

    repo = "Qwen/Qwen3-Embedding-8B"
    revision = "1d8ad4ca9b3dd8059ad90a75d4983776a23d44af"
    texts = [
        "Instruct: Retrieve a passage that answers the question.\nQuery: What is the capital of France?",
        "Paris is the capital of France.",
        "Bananas are yellow fruit grown in warm climates.",
    ]
    tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision, padding_side="left", local_files_only=True)
    model = AutoModel.from_pretrained(repo, revision=revision, dtype=torch.bfloat16, attn_implementation="sdpa", local_files_only=True).to("cuda").eval()
    inputs = tokenizer(texts, padding=True, return_tensors="pt").to("cuda")
    with torch.inference_mode():
        hidden = model(**inputs).last_hidden_state[:, -1].float()
        expected = torch.nn.functional.normalize(hidden, dim=-1)
    body = {"model": "qwen3-embedding-8b", "input": texts, "encoding_format": "float"}
    request = urllib.request.Request("http://127.0.0.1:30000/v1/embeddings", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)["data"]
    actual = torch.tensor([item["embedding"] for item in data], device="cuda")
    assert actual.shape == expected.shape == (3, 4096)
    cosine = torch.nn.functional.cosine_similarity(actual, expected, dim=-1)
    print(f"reference cosine: {cosine.tolist()}")
    assert cosine.min().item() > 0.99
