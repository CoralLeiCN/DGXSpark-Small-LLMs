# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=nvcr.io/nvidia/pytorch:26.02-py3
FROM ${BASE_IMAGE}

ARG SGLANG_VERSION=0.5.15.post1
ARG SGLANG_EXCLUDE_NEWER=2026-07-15T00:00:00Z

ENV DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/root/.cache/huggingface \
    UV_HTTP_RETRIES=10 \
    UV_HTTP_TIMEOUT=120 \
    UV_LINK_MODE=copy \
    CUDA_HOME=/usr/local/cuda

WORKDIR /opt/dgxspark

# Reuse the cached NGC base and then satisfy SGLang's exact Torch contract.
# The CUDA 13 index supplies matching ARM64 wheels without rebuilding Torch.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install \
        --system \
        --break-system-packages \
        --prerelease=if-necessary-or-explicit \
        --exclude-newer "${SGLANG_EXCLUDE_NEWER}" \
        --index-strategy unsafe-best-match \
        --extra-index-url https://download.pytorch.org/whl/cu130 \
        "click>=8,<8.3.0" \
        "flash-attn-4==4.0.0b15" \
        "torch==2.11.0" \
        "torchvision==0.26.0" \
        "torchaudio==2.11.0" \
        "wheel>=0.23,<1" \
        "sglang==${SGLANG_VERSION}" \
    && python3 -c "import sglang, torch; print('sglang', sglang.__version__); print('torch', torch.__version__)"

COPY start.sh /opt/dgxspark/start.sh
RUN chmod 0755 /opt/dgxspark/start.sh

EXPOSE 30000
ENTRYPOINT ["/opt/dgxspark/start.sh"]
