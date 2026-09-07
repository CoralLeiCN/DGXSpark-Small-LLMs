"""Run inside the model container against a healthy service.

INFERPACK_REFERENCE_TESTS=1 uv run --no-project --python /opt/sglang/bin/python
  python -m pytest /opt/inferpack/tests/test_reference.py -v -s
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("INFERPACK_REFERENCE_TESTS") != "1",
    reason="requires container dependencies, GPU memory, and running service",
)


def test_text_and_image_match_reference():
    import base64
    import io
    import json
    import urllib.request
    import torch
    from PIL import Image, ImageDraw
    from transformers import AutoModel, AutoProcessor
    from huggingface_hub import snapshot_download

    snapshot = snapshot_download("TomoroAI/tomoro-colqwen3-embed-4b", revision="13517a29e8c5e408f7f2684337ed407df3acb212", local_files_only=True)
    processor = AutoProcessor.from_pretrained(snapshot, trust_remote_code=True)
    reference = AutoModel.from_pretrained(snapshot, trust_remote_code=True, dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda").eval()
    picture = Image.new("RGB", (256, 256), "white")
    ImageDraw.Draw(picture).text((20, 80), "PARIS\nCapital of France", fill="black", font_size=20)
    cases = [processor.process_texts(["What is the capital of France?"]), processor.process_images([picture])]
    raw = io.BytesIO()
    picture.save(raw, format="PNG")
    image_data = "data:image/png;base64," + base64.b64encode(raw.getvalue()).decode()
    for index, inputs in enumerate(cases):
        text = processor.tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=False)
        if index == 1:
            text = processor.visual_prompt_prefix + processor.visual_prompt_suffix
        body = {"text": text}
        if index == 1:
            body["image_data"] = image_data
        request = urllib.request.Request("http://127.0.0.1:30000/encode", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=300) as response:
            actual = torch.tensor(json.load(response)["embedding"], device="cuda", dtype=torch.float32)
        with torch.inference_mode():
            expected = reference(**inputs.to("cuda")).embeddings[0].float()
        assert actual.shape == expected.shape
        cosine = torch.nn.functional.cosine_similarity(actual, expected, dim=-1)
        print(f"{'image' if index else 'text'}: shape={tuple(actual.shape)}, mean_cosine={cosine.mean().item():.6f}, min_cosine={cosine.min().item():.6f}")
        assert torch.isfinite(actual).all()
        assert cosine.mean().item() > 0.99
        assert cosine.min().item() > 0.95
