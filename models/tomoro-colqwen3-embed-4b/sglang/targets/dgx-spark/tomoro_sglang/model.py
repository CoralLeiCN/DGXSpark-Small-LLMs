"""Reuse SGLang Qwen3-VL with Tomoro's learned token projection.

The prepared checkpoint advertises Qwen3VLForConditionalGeneration so SGLang
uses its native multimodal processor and MRoPE handling. This package replaces
that registry entry only inside this model's container.
"""
import torch
from torch import nn
from sglang.srt.layers.pooler import EmbeddingPoolerOutput
from sglang.srt.model_loader.weight_utils import default_weight_loader
from sglang.srt.models.qwen3_vl import Qwen3VLForConditionalGeneration as Backbone


class TokenProjection(nn.Module):
    def __init__(self, hidden_size, embed_dim):
        super().__init__()
        self.projection = nn.Linear(hidden_size, embed_dim, bias=True)

    def forward(self, hidden_states, forward_batch):
        # Full prefill is required: cached prefixes would omit their vectors.
        if any(forward_batch.extend_prefix_lens_cpu):
            raise ValueError("ColQwen3 requires disabled prefix caching")
        vectors = self.projection(hidden_states)
        vectors = vectors / vectors.norm(dim=-1, keepdim=True).clamp_min(
            torch.finfo(vectors.dtype).eps
        )
        return EmbeddingPoolerOutput(
            embeddings=list(vectors.split(forward_batch.extend_seq_lens_cpu))
        )


class Qwen3VLForConditionalGeneration(Backbone):
    def __init__(self, config, quant_config=None, prefix=""):
        if config.embed_dim != 320:
            raise ValueError("This pack requires Tomoro's 320-dimensional head")
        super().__init__(config, quant_config, prefix)
        self.pooler = TokenProjection(config.text_config.hidden_size, config.embed_dim)

    def forward(self, *args, get_embedding=True, **kwargs):
        if not get_embedding:
            raise ValueError("This pack serves token embeddings only")
        return super().forward(*args, get_embedding=True, **kwargs)

    def load_weights(self, weights):
        loaded_projection = set()

        def backbone_weights():
            for name, weight in weights:
                if name.startswith("embedding_proj_layer."):
                    suffix = name.removeprefix("embedding_proj_layer.")
                    default_weight_loader(getattr(self.pooler.projection, suffix), weight)
                    loaded_projection.add(suffix)
                elif name.startswith("vlm."):
                    yield name.removeprefix("vlm."), weight
                else:
                    raise ValueError(f"Unexpected Tomoro checkpoint weight: {name}")

        super().load_weights(backbone_weights())
        if loaded_projection != {"weight", "bias"}:
            raise ValueError("Missing Tomoro projection weights")


EntryClass = Qwen3VLForConditionalGeneration
